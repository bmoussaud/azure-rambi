"""Main module to manage the Movie Poster Service."""
import os
import sys
import logging
import json
import redis
import requests
import uuid
import datetime
from collections import OrderedDict

import openai
import uvicorn

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi_logger.logger import log_request

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
    BlobClient,
    BlobSasPermissions,
    ContainerSasPermissions,
    ResourceTypes,
    AccountSasPermissions,
    UserDelegationKey,
    generate_account_sas,
    generate_container_sas,
    generate_blob_sas
)
from dotenv import load_dotenv
from pydantic import BaseModel

from openai import AzureOpenAI

from azure.identity import DefaultAzureCredential

openai.log = "debug"
OpenAIInstrumentor().instrument()
AIInferenceInstrumentor().instrument() 

load_dotenv()

root = logging.getLogger()
root.setLevel(logging.INFO)

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set the logging level to WARNING for the azure.core.pipeline.policies.http_logging_policy logger
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.monitor.opentelemetry.exporter').setLevel(logging.WARNING)

# Set the logging level to WARNING for the urllib3.connectionpool logger
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
logger_uvicorn = logging.getLogger('uvicorn.error')

if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger_uvicorn.info("configure_azure_monitor")
    configure_azure_monitor()


app = FastAPI()
FastAPIInstrumentor.instrument_app(app, excluded_urls="liveness,readiness")
templates = Jinja2Templates(directory="templates")

class MoviePoster(BaseModel):
    """ Class to manage the movie poster """
    title: str
    description: str | None = None
    url: str | None = None

class GenAiMovieService:
    """ Class to manage the access to OpenAI API to generate a new movie """
    def __init__(self):
        logger.info("Initializing GenAiMovieService")
        logger.info("Initializing AzureOpenAI with api_key: %s, api_version: %s, azure_endpoint: %s",
                    os.getenv("AZURE_OPENAI_API_KEY","-1"), os.getenv("OPENAI_API_VERSION","2024-08-01-preview"), os.getenv("AZURE_OPENAI_ENDPOINT"))

        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY","-1"),
            api_version=os.getenv("OPENAI_API_VERSION","2024-08-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self._use_cache = os.getenv("USE_CACHE", None) is not None
        if self._use_cache:
            logger.info("Initializing Redis client")
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"),ssl=True )
            logger.info("Redis ping: %s", self.redis_client.ping())

        logger.info("Initializing Azure Blob Storage client")
        self.blob_service_client = BlobServiceClient.from_connection_string(os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING"))
        self.container_name = "movieposters"
        logger.info("Container name: %s", self.container_name)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)


    def describe_poster(self, movie_title: str, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        logger.info("describe_poster called with %s", poster_url)
        if self._use_cache:
            cache_key = f"poster_description:{movie_title}:{poster_url}"
            logger.info("cache key %s", cache_key) 
            cached_description = self.redis_client.get(cache_key)
            if cached_description: 
                logger.info("Cache hit for %s", cache_key)
                return cached_description.decode("utf-8")
        try:
            logger.info("ask gpt4o")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": [
                        {
                            "type": "text",
                            "text": f"This is the '{movie_title}' movie poster. Describe it:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                    "url": poster_url
                            }
                        }
                    ]}
                ],
                max_tokens=2000
            )
            # Return the generated description
            description = response.choices[0].message.content
            if self._use_cache:
                logger.info("set cache for %s", cache_key)
                self.redis_client.set(cache_key, description, ex=3600)
            
            logger.info("describe_poster: %s", description)
        except Exception as e:
            logger.error("describe_poster: %s", e)
            description = f"Unable to describe the movie poster for {movie_title}: {e}"
        return description

    def store_poster(self, url: str) -> str:
        """ Store the generated poster in Azure Blob Storage and return a sas url"""
        # Upload the generated poster to Azure Blob Storage
        logger.info("Uploading poster to Azure Blob Storage")
        blob_name = f"azure-rambi-poster-{uuid.uuid4()}.png"
        logger.info("Blob name: %s", blob_name)
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(requests.get(url,timeout=100).content, overwrite=True,blob_type="BlockBlob" )
        logger.info("Uploaded poster to Azure Blob Storage: %s", blob_client.url)

        # Generate a SAS token for the blob
        sas_token = self.create_service_sas_blob(blob_client=blob_client, account_key=self.blob_service_client.credential.account_key)
        logger.info("Account SAS: %s", sas_token)
        #sas_token = self.create_user_delegation_sas_blob(blob_client=blob_client, user_delegation_key=user_delegation_key)
        # The SAS token string can be appended to the resource URL with a ? delimiter
        # or passed as the credential argument to the client constructor
        blob_url_with_sas = f"{blob_client.url}?{sas_token}"
        logger.info("Blob URL with SAS: %s", blob_url_with_sas)
        return blob_url_with_sas

    def generate_poster(self, poster_description: str) -> str:
        """ Generate a new movie poster based on the description """
        logger.info("generate_poster called with %s", poster_description)
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt="Generate a movie poster based on this description: "+poster_description,
                n=1,
                size='1024x1792'
            )
            json_response = json.loads(response.model_dump_json())
            url = json_response["data"][0]["url"]
            logger.info("generate_poster: %s", url)
            blob_url = self.store_poster(url)
            return blob_url
        except Exception as e:
            logger.error("generate_poster: %s", e)
            blob_url = "https://placehold.co/150x220/red/white?text=Image+Not+Available"
        return blob_url
<<<<<<< HEAD
    
    def create_service_sas_blob(self, blob_client: BlobClient, account_key: str):
        """Create a SAS token that's valid for one day, as an example"""
        start_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = start_time + datetime.timedelta(days=1)

        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=blob_client.container_name,
            blob_name=blob_client.blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )

        return sas_token
    
    
=======
>>>>>>> 4de239c (fix error in TMDB logic)

def custom_openapi():
    """Customize the OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Movie Poster Service",
        version="0.0.1",
        summary="The Famous Movie Poster Service OpenAPI schema",
        description="This is the OpenAPI schema for the Movie Poster Service",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get('/')
@log_request
async def racine(request: Request):
    """Function to show the environment variables."""
    logger_uvicorn.info("racine")
    return "Welcome to the Movie Poster Service"

@app.get('/env')
@log_request
async def env(request: Request):
    """Function to show the environment variables."""
    logger_uvicorn.info("env")
    sorted_env = OrderedDict(sorted(os.environ.items()))
    return templates.TemplateResponse('env.html', {"request": request, "env": sorted_env})

@app.get('/describe/{movie_title}')
@log_request
async def movie_poster_describe(request: Request, movie_title: str, url: str):
    """Function to show the movie poster description."""
    logger_uvicorn.info("movie_poster_describe")
    return GenAiMovieService().describe_poster(movie_title, url)

@app.post('/generate')
@log_request
async def movie_poster_generate(request: Request, poster: MoviePoster) -> MoviePoster:
    """Function to show the movie poster description."""
    logger.info("movie_poster_generate %s", poster.title)
    poster.url = GenAiMovieService().generate_poster(poster.description)
    return poster

@app.get('/liveness')
@log_request
async def liveness(request: Request):
    """Function to check the liveness of the service."""
    return  "liveness"

@app.get('/readiness')
@log_request
async def readiness(request: Request):
    """Function to check the readiness of the service."""
    return  "readiness"

if __name__ == '__main__':
    uvicorn.run('main:app')

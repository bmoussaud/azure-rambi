"""Main module to manage the Movie Poster Service."""
import os
import sys
import logging
import json
import redis
import base64
import requests
import io
from collections import OrderedDict

import openai
import uvicorn

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi_logger.logger import log_request

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from azure.monitor.opentelemetry import configure_azure_monitor
from PIL import Image
from azure.identity import ManagedIdentityCredential
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AzureOpenAI

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, AzureCliCredential



from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
from azure.storage.queue import QueueServiceClient


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


logging.getLogger('azure.identity').setLevel(logging.DEBUG)

if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger_uvicorn.info("configure_azure_monitor")
    configure_azure_monitor()


app = FastAPI()
FastAPIInstrumentor.instrument_app(app, excluded_urls="liveness,readiness")
templates = Jinja2Templates(directory="templates")

class MoviePoster(BaseModel):
    """ Class to manage the movie poster """
    id: str | None = None
    title: str
    description: str
    url: str | None = None
    error: str | None = None

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
        self._use_cache = False
        if self._use_cache:
            logger.info("Initializing Redis client")
            #use managed identity to connect to redis (azure-rambi-storage-contributor)
            managed_id_credential = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID_BLOB"))
            logger.info("managedIdCredential: %s", managed_id_credential)
            redis_scope = "https://redis.azure.com/.default"
            logger.info("Redis Scope: %s", redis_scope)
            token = managed_id_credential.get_token(redis_scope)
            logger.info("Token: %s", token)
            if token is None:
                logger.error("Redis client using password")
                self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"),ssl=True )
            else:
                logger.info("Redis Client using token")
                user_name = self.extract_username_from_token(token.token)
                logger.info("User name: %s", user_name)
                self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), username=user_name, password=token.token,ssl=True,decode_responses=True)
            logger.info("Redis ping: %s", self.redis_client.ping())

        sa_url = os.getenv("STORAGE_ACCOUNT_BLOB_URL")
        logger.info("Initializing Azure Blob Storage client with account_url: %s", sa_url)
        #use managed identity to connect to redis (azure-rambi-storage-contributor)
        #if (os.getenv("AZURE_CLIENT_ID_BLOB") is not None or os.getenv("AZURE_CLIENT_ID_BLOB") != ""):
        #    logger.info(f"Using Managed Identity to connect to Blob Storage [{os.getenv('AZURE_CLIENT_ID_BLOB')}]")
        #    managed_id_credential = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID_BLOB"))
        #else:
        #    logger.info("Using DefaultAzureCredential to connect to Blob Storage")
        #managed_id_credential = DefaultAzureCredential()
        managed_id_credential = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID_BLOB"))
        logger.info("** AZURE_CLIENT_ID_BLOB managedIdCredential: %s", managed_id_credential)
        
        self.blob_service_client = BlobServiceClient(account_url=sa_url, credential=managed_id_credential)
        logger.info("Blob Service Client: %s", self.blob_service_client)
        #for container in self.blob_service_client.list_containers():
        #    logger.info("==> Container name: %s", container['name'])
        self.container_client = self.blob_service_client.get_container_client("movieposters")
        logger.info("Container Client: %s", self.container_client)
        logger.info("GenAiMovieService initialized")

    def extract_username_from_token(self,token):
        """Extract the username from the token"""
        parts = token.split('.')
        base64_str = parts[1]

        if len(base64_str) % 4 == 2:
            base64_str += "=="
        elif len(base64_str) % 4 == 3:
            base64_str += "="

        json_bytes = base64.b64decode(base64_str)
        json_str = json_bytes.decode('utf-8')
        jwt = json.loads(json_str)
        logger.info("extract_username_from_token: %s", jwt)
        logger.info("extract_username_from_token oid: %s", jwt['oid'])
        return jwt['oid']

    def describe_poster(self, movie_title: str, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        logger.info("describe_poster %s called with %s", movie_title, poster_url)
        cache_key = f"poster_description:{movie_title}:{poster_url}"
        logger.info("cache_key %s", cache_key)
        if self._use_cache:
            logger.info("cache key %s", cache_key)
            cached_description = self.redis_client.get(cache_key)
            if cached_description:
                logger.info("Cache hit for %s", cache_key)
                if isinstance(cached_description, str):
                    return cached_description
                else:
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
            logger.error("describe_poster error: %s", e)
            description = f"Unable to describe the movie poster for {movie_title}: {e}"
        return description

    def store_poster(self, movie_id: str,  content) -> str:
        """ Store the generated poster in Azure Blob Storage and return a sas url"""
        # Upload the generated poster to Azure Blob Storage
        logger.info("store_poster %s", movie_id)
        blob_name = f"{movie_id}.png"
        logger.info("Blob name: %s", blob_name)
        blob_client = self.container_client.get_blob_client(blob_name)
        logger.info("uploading.....")
        blob_client.upload_blob(content, overwrite=True,blob_type="BlockBlob" )
        logger.info("Uploaded poster to Azure Blob Storage: %s", blob_client.url)
        return f"/poster/{movie_id}.png"

    def generate_poster(self, movie_id: str, poster_description: str) -> str:
        logger.info("GPT generate_poster called with %s", poster_description)
        return self.generate_poster_gpt_image(movie_id, poster_description)

    def generate_poster_dall_e(self, movie_id: str, poster_description: str) -> str:
        """ Generate a new movie poster based on the description """
        logger.info("generate_poster_dall_e called with %s", poster_description)
        
        response = self.client.images.generate( 
            model="dall-e-3",
            prompt="Generate a movie poster based on this description: " + poster_description,
            n=1,
            size='1024x1792'
        )
        json_response = json.loads(response.model_dump_json())
        url = json_response["data"][0]["url"]
        
        blob_url = self.store_poster(movie_id, requests.get(url,timeout=100).content)
        logger.info("generate_poster: %s", blob_url)
        return blob_url
    
    def generate_poster_gpt_image(self, movie_id: str, poster_description: str) -> str:
        """ Generate a new movie poster based on the description using gpt-image-1 model """
        logger.info("generate_poster_gpt_image called with %s", poster_description)
        
        response = self.client.images.generate( 
            model="gpt-image-1",
            prompt="Generate a movie poster based on this description: "+poster_description,
            n=1,
            size='1024x1536',
            quality='medium'
        )
        json_response = json.loads(response.model_dump_json())
        b64_json = json_response["data"][0]["b64_json"]
        #decode the base64 string and save it as an image


        logger.info("store the image in a temporary file")
        self.store_poster(movie_id, b64_json)
        image_data = base64.b64decode(b64_json)
        image = Image.open(io.BytesIO(image_data))
        temp_file = f"./{movie_id}.png"
        image.save(temp_file)

        logger.info("upload the image to blob storage")
        blob_url = self.store_poster(movie_id, image_data)
        logger.info("generate_poster gpt: %s", blob_url)
        return blob_url
    
    
    def extract_error_message(self, e: Exception) -> str:
        """Extract the error message from the exception"""
        error_message = None
        try:
            error_message = e.response.json().get('error', {}).get('message', str(e))
        except AttributeError:
            error_message = str(e)
        return error_message
    
    def explain_exception(self, exception: Exception) -> str:
        """Explain the exception using the GPT-4o model"""
        logger.info("explain_exception called with %s", exception)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": f"explain using one or two sentences this error : {str(exception)}"}
                ],
                max_tokens=500
            )
            explanation = response.choices[0].message.content
            logger.info("explain_exception: %s", explanation)
            return explanation
        except Exception as e:
            logger.error("explain_exception: %s", e)
            return f"Unable to explain the exception: {e}"

    # ...existing code...
    def poster(self, movie_id: str) -> bytes:
        """Retrieve the movie poster from Azure Blob Storage"""
        logger.info("poster called with %s", movie_id)
        blob_name = f"{movie_id}.png"
        blob_client = self.container_client.get_blob_client(blob_name)
        try:
            blob_data = blob_client.download_blob().readall()
            logger.info("Retrieved poster from Azure Blob Storage: %s", blob_client.url)
            return blob_data
        except Exception as e:
            logger.error("poster exception: %s", e)
            raise


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

service = GenAiMovieService()

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
    return service.describe_poster(movie_title, url)

@app.get('/store/{movie_title}')
@log_request
async def movie_poster_store(request: Request, movie_title: str, url: str):
    """Function to show the movie poster description."""
    logger_uvicorn.info("movie_poster_describe")
    return service.store_poster(10, url)

@app.post('/generate')
@log_request
async def movie_poster_generate(request: Request, poster: MoviePoster) -> MoviePoster:
    """Function to show the movie poster description."""
    try:
        logger.info("movie_poster_generate called with %s", poster)
        poster.url = service.generate_poster(poster.id, poster.description)
    except Exception as e:  
        logger.error("movie_poster_generate error: %s", e)
        error_message = service.extract_error_message(e)
        logger.error("generate_poster error_message: %s", error_message)
        poster.error = service.explain_exception(e)
        poster.url = f"https://placehold.co/1024x1792/red/white?text={error_message}"
    return poster

@app.get(
    "/poster/{movie_id}.png",
    # Set what the media type will be in the autogenerated OpenAPI specification.
    # fastapi.tiangolo.com/advanced/additional-responses/#additional-media-types-for-the-main-response
    responses = {
        200: {
            "content": {"image/png": {}}
        }
    },
    # Prevent FastAPI from adding "application/json" as an additional
    # response media type in the autogenerated OpenAPI specification.
    # https://github.com/tiangolo/fastapi/issues/3258
    # https://stackoverflow.com/questions/55873174/how-do-i-return-an-image-in-fastapi (If you already have the bytes of the image in memory)
    response_class=Response
)
def get_image(request: Request, movie_id: str):
    """Function to get the movie poster image."""
    logger.info("get_image called with %s", movie_id)
    image_bytes: bytes = service.poster(movie_id)
    headers = {'Content-Disposition': 'inline; filename="'+movie_id+'.png"'}
    logger.info("get_image headers: %s", headers)
    # media_type here sets the media type of the actual response sent to the client.
    return Response(image_bytes, headers=headers, media_type='image/png')

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
    uvicorn.run('main:app', host='0.0.0.0', port=8002)

"""Main module to manage the Movie Generate Service."""
import os
import sys
import logging
import json
import redis
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

from dotenv import load_dotenv
from pydantic import BaseModel

from openai import AzureOpenAI

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

class Movie(BaseModel):
    """ Data class for Movie """
    title: str
    plot: str
    poster_url: str
    poster_description: str = None

class GenAIMovie(Movie):
    """ Data class for GenAIMovie """
    prompt: str = None

class GenAiMovieService:
    """ Class to manage the access to OpenAI API to generate a new movie """

    def __init__(self):
        logger.info("Initializing GenAiMovieService")
        logger.info("Initializing AzureOpenAI with api_key: %s, api_version: %s, azure_endpoint: %s",
                    os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("OPENAI_API_VERSION"), os.getenv("AZURE_OPENAI_ENDPOINT"))

        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self._use_cache = os.getenv("USE_CACHE", None) is not None
        if self._use_cache: 
            logger.info("Initializing Redis client")
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"),ssl=True ) 
            logger.info("Redis ping: %s", self.redis_client.ping()) 

    def describe_poster(self, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        logger.info("describe_poster called with %s", poster_url)
        if self._use_cache: 
            cache_key = f"poster_description:{poster_url}" 
            logger.info("cache key %s", cache_key) 
            cached_description = self.redis_client.get(cache_key)
            if cached_description: 
                logger.info("Cache hit for %s", cache_key)
                return cached_description.decode("utf-8") 
            
        logger.info("ask gpt4o")
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": f"Describe the movie poster at this URL: {poster_url}"
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
        return description

    def generate_movie(self, movie1: Movie, movie2: Movie, genre: str) -> Movie:
        """ Generate a new movie based on the two movies """ 

        logger.info(
            "generate_movie called based on two movies %s and %s, genre: %s", movie1.title, movie2.title, genre)
        movie1.poster_description = self.describe_poster(movie1.poster_url)
        movie2.poster_description = self.describe_poster(movie2.poster_url)

        with open("prompts/structured_new_movie_short.txt", "r", encoding="utf-8") as file:
            prompt_template = file.read()

        prompt = prompt_template.format(
            movie1_title=movie1.title,
            movie1_plot=movie1.plot,
            movie1_description=movie1.poster_description,
            movie2_title=movie2.title,
            movie2_plot=movie2.plot,
            movie2_description=movie2.poster_description,
            genre=genre
        )

        logger.info("Prompt: %s", prompt)

        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            response_format=GenAIMovie,
            messages=[
                {
                    "role": "system",
                    "content": "You are a bot expert with a huge knowledge about movies and the cinema."
                },
                {
                    "role": "system",
                    "content": """
                    Two movie titles and plots will be provided, along with a target genre.
                    Using the titles, plots and genre as inspiration, generate the following:
                    * Step 1: Generate a new movie title that combines elements of the provided titles and fits the target genre. The title should be catchy and humorous.
                    * Step 2: Generate a 4-6 sentence movie plot synopsis for the new title, incorporating themes, characters, or plot points from the provided movies. Adapt them to fit the target genre.
                    * Step 3: Based on the generated movie plot and the key elements of the 2 movie posters, generate the movie poster description without using the movie's titles.
                                """
                },
                {
                    "role": "user",
                    "content": prompt
                },
                {
                    "role":"system",
                    "content": """
                Use the details below to generate the new movie title and plot.
                Use the description of the two posters to generate the new posterDescription without any title.
                Take care of not generating any violence.
                Take care of not generating any copyrighted content.
                Remove all mentions about copyrighted content and replace them with the generic words.
                """
                }
            ]
        )
        message = completion.choices[0].message
        movie = GenAIMovie.model_validate(json.loads(message.content))
        movie.prompt= prompt
        movie.poster_url = None
        return movie

def custom_openapi():
    """Customize the OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Movie Generate Service",
        version="0.0.1",
        summary="The Famous Movie Generate Service OpenAPI schema",
        description="This is the OpenAPI schema for the Movie Generate Service",
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
    return "Welcome to the Movie Generate Service"

@app.get('/env')
@log_request
async def env(request: Request):
    """Function to show the environment variables."""
    logger_uvicorn.info("env")
    sorted_env = OrderedDict(sorted(os.environ.items())) 
    return templates.TemplateResponse('env.html', {"request": request, "env": sorted_env}) 

@app.post('/generate')
@log_request
async def movie_generate(request: Request, movie1: Movie, movie2: Movie, genre: str) -> Movie:
    """Function to generate a new movie."""
    logger_uvicorn.info("movie_generate")
    return GenAiMovieService().generate_movie(movie1, movie2, genre)

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

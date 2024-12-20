"""Main module to manage the Movie Poster Service."""
import os
import sys
import logging
import json

import openai
import uvicorn

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi_logger.logger import log_request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


from dotenv import load_dotenv
from pydantic import BaseModel

from openai import AzureOpenAI

openai.log = "debug"

load_dotenv()

root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
templates = Jinja2Templates(directory="templates")

logger_uvicorn = logging.getLogger('uvicorn.error')

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
                    os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("OPENAI_API_VERSION"), os.getenv("AZURE_OPENAI_ENDPOINT"))

        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    def describe_poster(self, movie_title: str, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        logger.info("describe_poster called with %s", poster_url)
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
        logger.info("describe_poster: %s", response.choices[0].message.content)
        return response.choices[0].message.content

    def generate_poster(self, poster_description: str) -> str:
        """ Generate a new movie poster based on the description """
        logger.info("generate_poster called with %s", poster_description)
        try:
            client = AzureOpenAI()
            response = client.images.generate(
                model="dall-e-3",
                prompt="Generate a movie poster based on this description: "+poster_description,
                n=1,
                size='1024x1792'
            )
            json_response = json.loads(response.model_dump_json())
            url = json_response["data"][0]["url"]
            logger.info("generate_poster: %s", url)
        except Exception as e:
            logger.error("generate_poster: %s", e)
            url = "https://placehold.co/150x220/red/white?text=Image+Not+Available"
        return url

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
    return   templates.TemplateResponse('env.html', {"request": request,"AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"), "OPENAI_API_VERSION": os.getenv("OPENAI_API_VERSION"), "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT")})

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
    logger_uvicorn.info("movie_poster_generate")
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

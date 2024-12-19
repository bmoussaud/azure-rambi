from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
import json
import logging
from openai import AzureOpenAI
import openai
from dotenv import load_dotenv

load_dotenv()
openai.log = "debug"

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        except Exception as e:
            logger.error("generate_poster: %s", e)
            url = "https://placehold.co/150x220/red/white?text=Image+Not+Available"
        return url


app = FastAPI()
templates = Jinja2Templates(directory="templates")

class MoviePoster(BaseModel):
    """ Class to manage the movie poster """
    title: str
    description: str | None = None
    url: str | None = None

@app.get('/movie_poster/env')
async def env(request: Request):
    """Function to show the environment variables."""
    return   templates.TemplateResponse('env.html', {"request": request,"AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"), "OPENAI_API_VERSION": os.getenv("OPENAI_API_VERSION"), "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT")})

@app.get('/movie_poster/describe/{movie_title}')
async def movie_poster_describe(movie_title: str, url: str):
    """Function to show the movie poster description."""
    return GenAiMovieService().describe_poster(movie_title, url)

@app.post('/movie_poster/generate')
async def movie_poster_generate(poster: MoviePoster) -> MoviePoster:
    """Function to show the movie poster description."""
    poster.url = GenAiMovieService().generate_poster(poster.description)
    return poster

@app.get('/movie_poster/generateget')
async def movie_poster_generateget(poster: MoviePoster) -> MoviePoster:
    """Function to show the movie poster description."""
    poster.url = GenAiMovieService().generate_poster(poster.description)
    return poster

@app.get('/liveness')
async def liveness():
    """Function to check the liveness of the service."""
    return  "liveness"

@app.get('/readiness')
async def readiness():
    """Function to check the readiness of the service."""
    return  "readiness"


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)


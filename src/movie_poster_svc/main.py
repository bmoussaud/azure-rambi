from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from movie_poster_svc.gen_ai_movie_service import GenAiMovieService
from pydantic import BaseModel
import uvicorn
import os
import logging
import openai
from dotenv import load_dotenv

load_dotenv()
openai.log = "debug"

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class MoviePoster(BaseModel):
    """ Class to manage the movie poster """
    title: str
    description: str | None = None
    url: str | None = None

@app.get('/')
async def root(request: Request):
    """Function to show the environment variables."""
    return "Welcome to the Movie Poster Service"

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


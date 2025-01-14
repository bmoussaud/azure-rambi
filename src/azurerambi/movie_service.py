""" Class to manage the access to TMDB API """
import os
import json
import logging
from dataclasses import dataclass
from movie_poster import MoviePosterClient
from pydantic import BaseModel
import requests
from openai import AzureOpenAI
import openai
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

openai.log = "debug"
OpenAIInstrumentor().instrument()
RequestsInstrumentor().instrument()

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Movie(BaseModel):
    """ Data class for Movie """
    title: str
    plot: str
    poster_url: str
    poster_description: str = None
    

@dataclass
class GenAIMovie(Movie):
    """ Data class for GenAIMovie """
    prompt: str = None


class TMDBService:
    """ Class to manage the access to TMDB API """

    def __init__(self, end_point: str = None, api_key: str = None, ):
        logger.info("Initializing TMDBService")
        self._api_key = api_key
        self._end_point = end_point
       
    def get_movie_by_title(self, title) -> Movie:
        """ Get movie info from TMDB API """
        try:
            logger.info("Fetching movie with title: %s", title)
            _headers = {
                'Ocp-Apim-Subscription-Key': self._api_key
            }
            url = f"https://{self._end_point}/tmdb/3/search/movie?query={title}"
            logger.info("url: %s", url)
            response = requests.get(url, headers=_headers, timeout=10)
            logger.info("response: %s", response)
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    movie = data["results"][0]
                    return Movie(
                        title=movie["title"],
                        plot=movie["overview"],
                        poster_url=f"https://image.tmdb.org/t/p/original/{movie['poster_path']}",
                        poster_description=" "
                    )
            else:
                logger.error("Movie not found %s %s",title, response.status_code)
                return None
        except Exception as e:
            logger.error("get_movie_by_title: %s", e)
            return Movie(title=title, plot=str(e), poster_url="https://placehold.co/150x220?text=TMDB%20Error")


class GenAiMovieService:
    """ Class to manage the access to OpenAI API to generate a new movie """

    def __init__(self):
        logger.info("Initializing GenAiMovieService")
        #https://azrambi-openai-b76s6utvi44xo.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-05-13
        #https://azrambi-openai-b76s6utvi44xo.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
        logger.info("Initializing AzureOpenAI with api_key: %s, api_version: %s, azure_endpoint: %s",
                    os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("OPENAI_API_VERSION"), os.getenv("AZURE_OPENAI_ENDPOINT"))
        
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        self._movie_poster_client = MoviePosterClient()

    def describe_poster(self, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        logger.info("describe_poster called with %s", poster_url)
        content = self._movie_poster_client.describe_poster("movie", poster_url)
        logger.info("describe_poster: %s", content)
        return content

    def generate_poster(self, poster_description: str) -> str:
        """ Generate a new movie poster based on the description """
        logger.info("generate_poster called with %s", poster_description)
        try:
           url = self._movie_poster_client.generate_poster(poster_description)
        except Exception as e:
            logger.error("generate_poster: %s", e)
            url = "https://placehold.co/150x220/red/white?text=Image+Not+Available"
        logger.info("generate_poster: %s", url)
        return url

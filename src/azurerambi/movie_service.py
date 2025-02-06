""" Class to manage the access to TMDB API """
import os
import json
import logging
import requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from typing import Optional
from pydantic import BaseModel

RequestsInstrumentor().instrument()
# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Movie(BaseModel):
    """ Data class for Movie """
    id: str
    title: str
    plot: str
    poster_url: str
    poster_description: Optional[str] = None

class TMDBService:
    """ Class to manage the access to TMDB API """

    def __init__(self, end_point: str = None, api_key: str = None, ):
        logger.info("Initializing TMDBService %s", end_point)
        self._api_key = api_key
        self._end_point = end_point


    def get_movie_by_id(self, id) -> Movie:
        """ Get movie info from TMDB API """
        try:
            logger.info("Fetching movie with id: %s", id)
            _headers = {
                'api-key': self._api_key
            }
            url = f"https://{self._end_point}/tmdb/3/movie/{id}"
            logger.info("url: %s", url)
            response = requests.get(url, headers=_headers, timeout=10)
            logger.info("response: %s", response)
            if response.status_code == 200:
                data = response.json()
                return Movie(
                    id=data["id"],
                    title=data["title"],
                    plot=data["overview"],
                    poster_url=f"https://image.tmdb.org/t/p/original/{data['poster_path']}"
                )
            else:
                logger.error("Movie not found %s %s",id, response.status_code)
                return Movie(id="-1", title=id, plot=f"Movie not found {id} {response.status_code}",poster_url="https://placehold.co/150x220?text=Movie%20Not%20Found%20Error")
        except Exception as e:
            logger.error("get_movie_by_id: %s", e)
            return Movie(id="-1", title=id, plot=str(e), poster_url="https://placehold.co/150x220?text=TMDB%20Error")
        
    def get_movie_by_title(self, title) -> Movie:
        """ Get movie info from TMDB API """
        try:
            logger.info("Fetching movie with title: %s", title)
            _headers = {
                'api-key': self._api_key
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
                        id=movie["id"],
                        title=movie["title"],
                        plot=movie["overview"],
                        poster_url=f"https://image.tmdb.org/t/p/original/{movie['poster_path']}"
                    )
                else:
                    logger.error("Movie not found %s in the TMDB database",title)
                    return Movie(title=title, plot=f"Movie not found {title} in the TMDB database",poster_url="https://placehold.co/150x220?text=Movie%20Not%20Found")
            else:
                logger.error("Movie not found %s %s",title, response.status_code)
                return Movie(id="-1", title=title, plot=f"Movie not found {title} {response.status_code}",poster_url="https://placehold.co/150x220?text=Movie%20Not%20Found%20Error")
        except Exception as e:
            logger.error("get_movie_by_title: %s", e)
            return Movie(id="-1", title=title, plot=str(e), poster_url="https://placehold.co/150x220?text=TMDB%20Error")


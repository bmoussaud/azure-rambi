"""Movie Poster Generator Client"""
import requests
import logging
import os
import json

from opentelemetry.instrumentation.requests import RequestsInstrumentor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

RequestsInstrumentor().instrument()

class MoviePosterClient:
    """CLI class for the movie poster generator."""
    def __init__(self, endpoint: str = None, api_key: str = None):
        if endpoint is None:
            endpoint = os.getenv("MOVIE_POSTER_ENDPOINT")  

        if api_key is None:
            api_key = os.getenv("API_SUBSCRIPTION_KEY")

        self._endpoint = endpoint
        self._headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }

    def describe_poster(self, name, poster_url) -> str:
        """describe the image"""
        logger.info("%s Description of image at %s", name, poster_url)
        endpoint = f"{self._endpoint}/describe/{name}?url={poster_url}"

        logger.info("Calling endpoint %s", endpoint)
        response = requests.get(endpoint, headers=self._headers, timeout=300)
        if response.status_code == 200:
            logger.info("Response: %s", response.content)
            return response.content.decode('UTF-8')
        else:
            logger.error("Failed to retrieve data: %s %s", response.status_code, response.text)
            raise Exception(f"Failed to retrieve the poster description: {response.status_code} {response.text}")
        
    def generate_poster(self, desc: str) -> dict:
        """generate the image"""
        logger.info("generate_image of based on %s", desc)
        endpoint = f"{self._endpoint}/generate"
        poster = {
            "description": desc,
            "title":"movieposter"
        }
        logger.info("Calling endpoint %s", endpoint)
        logger.info(json.dumps(poster))

        response = requests.post(endpoint, json=poster, headers=self._headers, timeout=1000)
        logger.info("Response: %s", response)
        if response.status_code == 200:
            json_response  = response.json()
            logger.info(json.dumps(json_response))
            return json_response['url'] 
        else:
            logger.error("Failed to retrieve data: %s %s", response.status_code, response.text)
            raise Exception(f"Failed to retrieve the poster: {response.status_code} {response.text}")
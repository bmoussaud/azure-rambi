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

        logger.info("MoviePosterClient endpoint: %s", endpoint)
        
        if api_key is None:
            api_key = os.getenv("APIM_SUBSCRIPTION_KEY")

        self._endpoint = endpoint
        self._headers = {
            'api-key': api_key
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
        
    def generate_poster(self, movie_id: str, desc: str) -> dict:
        """generate the image"""
        logger.info("generate_image of based on %s", desc)
        endpoint = f"{self._endpoint}/generate"
        poster = {
            "id": movie_id,
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
            return json_response
        else:
            logger.error("Failed to retrieve data: %s %s", response.status_code, response.text)
            raise Exception(f"Failed to retrieve the poster: {response.status_code} {response.text}")
        
    def redirect_poster_url(self, movie_id: str) -> str:
        """redirect to the image"""
        endpoint = f"{self._endpoint}/poster/{movie_id}.png"
        logger.info("redirect_poster_url to endpoint %s", endpoint)
        return endpoint
    
    def get_validation_scores(self, movie_id: str) -> dict:
        """Get validation scores for a movie poster from movie_poster_agent_svc"""
        logger.info("Getting validation scores for movie_id: %s", movie_id)
        
        # Get the movie poster agent service endpoint
        agent_endpoint = os.getenv("MOVIE_POSTER_AGENT_ENDPOINT")
        if not agent_endpoint:
            logger.warning("MOVIE_POSTER_AGENT_ENDPOINT not configured")
            return None
            
        endpoint = f"{agent_endpoint}/validations/{movie_id}"
        logger.info("Calling validation endpoint: %s", endpoint)
        
        try:
            response = requests.get(endpoint, timeout=30)
            if response.status_code == 200:
                validation_data = response.json()
                logger.info("Validation response: %s", json.dumps(validation_data))
                return validation_data
            elif response.status_code == 404:
                logger.info("No validation found for movie_id: %s", movie_id)
                return None
            else:
                logger.error("Failed to get validation scores: %s %s", response.status_code, response.text)
                return None
        except Exception as e:
            logger.exception("Error getting validation scores for movie_id %s: %s", movie_id, str(e))
            return None
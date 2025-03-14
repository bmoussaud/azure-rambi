""" Azure Functions Python HTTP Trigger Example """
import json
import logging
import os
from datetime import datetime
import azure.functions as func
import requests
import httpx

#from opencensus.extension.azure.functions import OpenCensusExtension
#from opencensus.trace import config_integration

#config_integration.trace_integrations(['requests'])
#OpenCensusExtension.configure()

app = func.FunctionApp()

logging.info('Azure Rambu Event Handler Function App started.')

#curl https://rambi-events-handler.lemonground-ce949a08.francecentral.azurecontainerapps.io/api/hello   
#
@app.function_name(name="HttpTrigger1")
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """ HTTP trigger function that returns a sample response. """
    logging.info('Benoit Python HTTP trigger function processed a request.')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    create_movie_entry(f"movie_http_{timestamp}")
    return func.HttpResponse(
        "Benoit This HTTP triggered function executed successfully.",
        status_code=200
        )


@app.function_name("OnNewGeneratedMovie")
@app.queue_trigger(arg_name="msg", queue_name="generatedmovies",connection="RambiQueueStorageConnection")
def generated_movie_queue_trigger(msg: func.QueueMessage) -> None:
    """This function will be invoked whenever a message is added to the queue."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    create_movie_entry(f"movie_queue_{timestamp}")

def create_movie_entry(data):
    """Create a movie entry in the movie gallery service."""
    endpoint = os.getenv("MOVIE_GALLERY_SVC_ENDPOINT", "https://movie-gallery-svc")
    movie = {
        "title": f"Movie Title {data}", 
        "description": "Movie Description Bla Bla Bla Bla"
        }
    logging.info('Movie: %s', movie)
    json_movie = json.dumps(movie)
    logging.info('JSON Movie: %s', json_movie) 
    headers = {'Content-Type': 'application/json'}
    requests.post(
        f"{endpoint}/movies",
        data=json_movie,
        headers=headers,
        timeout=100,
        )
    logging.info("Movie added to movie-gallery-svc")

def create_movie_entry2(data):
    """Create a movie entry in the movie gallery service."""
    endpoint = os.getenv("MOVIE_GALLERY_SVC_ENDPOINT", "https://movie-gallery-svc")
    movie = {
        "title": f"Movie Title {data}", 
        "description": "Movie Description Bla Bla Bla Bla"
    }
    logging.info('Movie: %s', movie)
    json_movie = json.dumps(movie)
    logging.info('JSON Movie: %s', json_movie)
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = httpx.post(
            f"{endpoint}/movies",
            data=json_movie,
            headers=headers,
            timeout=100,
        )
        response.raise_for_status()
        logging.info("Movie added to movie-gallery-svc")
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")



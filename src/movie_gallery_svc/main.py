
import uuid
import json
import logging

from typing import List
from fastapi import FastAPI, Response, status

from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp
from settings import Settings
from store import MovieStore
from entities import MovieRequest, Movie

logging.basicConfig(level=logging.INFO)

app = FastAPI()
dapr_app = DaprApp(app)
#dapr_client = DaprClient()


@app.get('/', response_class = HTMLResponse)
async def root():
    """
    Root endpoint to check if the service is running.
    """
    logging.info("Movie Gallery API is running")
    return """
    <html>
        <head>
            <title>Movie Gallery API</title>
        </head>
        <body>
            <h1>Movie Gallery API Ready !</h1>
        </body>
    </html>
    """

@app.post("/movies", status_code = status.HTTP_201_CREATED)
async def add_movie(movie: MovieRequest):
    """
    Endpoint to add a new movie."""

    try:
        settings=Settings(DaprClient())

        store=MovieStore(settings)

        movie=Movie(
            uuid.uuid4().hex,
            movie.title,   
            movie.description   
        )

        logging.info("Saving new movie %s", movie)
        new_request=store.upsert(movie)

        return Response(content = json.dumps(new_request), media_type = "application/json")
    except Exception as e:
        logging.error('Error: %s', e)
        return Response(content = json.dumps([]), media_type = "application/json")

@app.get("/movies")
async def list_movies():
    """Endpoint to list all movies."""
    try:
        settings = Settings(DaprClient())
        movies = MovieStore(settings).find_all()
        return Response(content=json.dumps(movies), media_type="application/json")
    except Exception as e:
        logging.error('RuntimeError: %s', e)
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@app.get("/liveness")
async def liveness():
    """
    Liveness probe endpoint.
    """
    logging.info("Liveness probe")
    return Response(content=json.dumps({"status": "alive"}), media_type="application/json")

@app.get("/readiness")
async def readiness():
    """
    Readiness probe endpoint.
    """
    logging.info("Readiness probe")
    return Response(content=json.dumps({"status": "ready"}), media_type="application/json")

import uuid
import json
import logging
import uvicorn

from store import MovieStore
from entities import MovieRequest, Movie

from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp
import traceback

logging.basicConfig(level=logging.INFO)

app = FastAPI()
dapr_app = DaprApp(app)
#dapr_client = DaprClient()


@app.get('/', response_class = HTMLResponse)
def root():
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
            <h2>Movie Gallery API Ready !</h2>
        </body>
    </html>
    """

@app.post("/movies", status_code = status.HTTP_201_CREATED)
def add_movie(movie: MovieRequest):
    """Endpoint to add a new movie."""
    try:
        logging.info("Adding new movie")
        store=MovieStore(DaprClient())
        movie=Movie(
            uuid.uuid4().hex,
            movie.title,
            movie.description)
        logging.info("Saving new movie %s", movie)
        new_request=store.upsert(movie)
        return Response(content = json.dumps(new_request), media_type = "application/json")
    except Exception as e:
        logging.error('Add_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(content = json.dumps({'method':'add_movie','error':e}), media_type = "application/json")

@app.get("/movies")
def list_movies():
    """Endpoint to list all movies."""
    logging.info("Listing all movies")
    try:
        logging.info('initializing Dapr client')
        dapr_client = DaprClient()
        logging.info('initializing MovieStore')
        movies = MovieStore(dapr_client).find_all()
        return Response(content=json.dumps(movies), media_type="application/json")
    except Exception as e:
        logging.error('RuntimeError: %s', e)
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@app.get("/liveness")
def liveness():
    """
    Liveness probe endpoint.
    """
    #logging.info("Liveness probe")
    return Response(content=json.dumps({"status": "alive"}), media_type="application/json")

@app.get("/readiness")
def readiness():
    """
    Readiness probe endpoint.
    """
    #logging.info("Readiness probe")
    return Response(content=json.dumps({"status": "ready"}), media_type="application/json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
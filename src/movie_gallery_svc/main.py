import json
import logging
import uvicorn
import traceback

from entities import GeneratedMovie
from store import MovieStore
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp


logging.basicConfig(level=logging.INFO)

app = FastAPI()
dapr_app = DaprApp(app)
dapr_client = DaprClient()
store=MovieStore(dapr_client)

FastAPIInstrumentor.instrument_app(app, excluded_urls="liveness,readiness")

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
            <pre>Movie Gallery API Ready !</pre>
        </body>
    </html>
    """

@app.post("/movies", status_code = status.HTTP_201_CREATED)
def add_movie(movie: GeneratedMovie) -> GeneratedMovie:
    """Endpoint to add a new movie."""
    try:
        logging.info("Adding new movie %s", movie)
        inserted_generated_movie=store.upsert(movie)
        return inserted_generated_movie
    except Exception as e:
        logging.error('Add_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(content = json.dumps({'method':'add_movie','error':e}), media_type = "application/json")

@app.get("/movies/{movie_id}", response_model=GeneratedMovie)
def get_movie(movie_id: str) -> GeneratedMovie:
    """Endpoint to get a movie by ID."""
    logging.info("Getting movie with ID: %s", movie_id)
    try:
        movie = store.try_find_by_id(movie_id)
        if movie:
            return movie
        else:
            return Response(content=json.dumps({}), media_type="application/json", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logging.error('Get_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(content=json.dumps({'method':'get_movie','error':e}), media_type="application/json")
    

@app.get("/movies", response_model=list[GeneratedMovie])
def list_movies() -> list[GeneratedMovie]:
    """Endpoint to list all movies."""
    logging.info("Listing all movies")
    try:
        logging.info('initializing Dapr client')
        movies = store.find_all()
        # remove prompt from the movie
        for movie in movies:
            if isinstance(movie, GeneratedMovie):
                movie.prompt = None
                #movie.payload = None
        # convert to JSON
        d_movies = [movie.to_json() for movie in movies]
        logging.info('Movies JSON: %s', d_movies)
        # return as JSON
        logging.info('Returning movies as JSON')
        return movies
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
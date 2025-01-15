import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Cosmos DB configuration
COSMOS_DB_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")
COSMOS_DB_DATABASE = os.getenv("COSMOS_DB_DATABASE")
COSMOS_DB_CONTAINER = os.getenv("COSMOS_DB_CONTAINER")

# Initialize Cosmos client
client = CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)
database = client.create_database_if_not_exists(id=COSMOS_DB_DATABASE)
container = database.create_container_if_not_exists(
    id=COSMOS_DB_CONTAINER,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

class GeneratedMovie(BaseModel):
    id: str
    title: str
    plot: str
    poster_url: str
    source_movies: List[str]

@app.post("/movies/", response_model=GeneratedMovie)
def store_generated_movie(movie: GeneratedMovie):
    try:
        container.create_item(body=movie.dict())
        return movie
    except Exception as e:
        logger.error(f"Error storing movie: {e}")
        raise HTTPException(status_code=500, detail="Error storing movie")

@app.get("/movies/{movie_id}", response_model=GeneratedMovie)
def get_generated_movie(movie_id: str):
    try:
        movie = container.read_item(item=movie_id, partition_key=movie_id)
        return movie
    except Exception as e:
        logger.error(f"Error retrieving movie: {e}")
        raise HTTPException(status_code=404, detail="Movie not found")

@app.get("/movies/", response_model=List[GeneratedMovie])
def list_generated_movies():
    try:
        movies = list(container.read_all_items())
        return movies
    except Exception as e:
        logger.error(f"Error listing movies: {e}")
        raise HTTPException(status_code=500, detail="Error listing movies")

@app.delete("/movies/{movie_id}")
def delete_generated_movie(movie_id: str):
    try:
        container.delete_item(item=movie_id, partition_key=movie_id)
        return {"message": "Movie deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting movie: {e}")
        raise HTTPException(status_code=404, detail="Movie not found")

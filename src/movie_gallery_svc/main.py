from typing import List
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

# In-memory storage for movies
movies = []

class Movie(BaseModel):
    """
    Movie model for storing movie details."""
    title: str
    description: str

@app.post("/movies", response_model=Movie, status_code=201)
def add_movie(movie: Movie):
    """Endpoint to add a new movie."""
    movies.append(movie)
    return movie

@app.get("/movies", response_model=List[Movie])
def list_movies():
    """Endpoint to list all movies."""
    return movies

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)

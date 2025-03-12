from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In-memory storage for movies
movies = []

class Movie(BaseModel):
    title: str
    description: str

@app.post("/movies", response_model=Movie, status_code=201)
def add_movie(movie: Movie):
    movies.append(movie)
    return movie

@app.get("/movies", response_model=List[Movie])
def list_movies():
    return movies

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)

import json
from typing import Optional
from pydantic import BaseModel

class MovieRequest(BaseModel):
    """Request model for adding a new movie."""
    title: str
    description: str

class Movie(BaseModel):
    """Enhanced Movie model with all required fields"""
    id: str
    title: str
    plot: str
    poster_url: Optional[str] = None
    poster_description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert Movie instance to dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Movie':
        """Create Movie instance from dictionary"""
        return cls(**data)

    def __str__(self) -> str:
        """Return a string representation of the Movie instance"""
        return f"Movie(id={self.id}, title={self.title}, plot={self.plot}, poster_url={self.poster_url}, poster_description={self.poster_description})"

class MoviePayload(BaseModel):
    """Data class for movie generation payload"""
    movie1: Movie
    movie2: Movie
    genre: str

    def __repr__(self) -> str:
        """Return a string representation of the MoviePayload instance"""
        return f"MoviePayload(movie1={self.movie1}, movie2={self.movie2}, genre={self.genre})"
    

class GeneratedMovie(Movie):
    """Model for generated movie data extending the base Movie class"""
    prompt: str
    payload: MoviePayload

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            # Add custom encoders if needed
        }

    @classmethod
    def from_json(cls, json_str: str) -> 'GeneratedMovie':
        """Create a GeneratedMovie instance from a JSON string"""
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self) -> str:
        """Convert the GeneratedMovie instance to a JSON string"""
        return self.model_dump_json()
    
    def __str__(self) -> str:
        """Return a string representation of the GeneratedMovie instance"""
        return f"GeneratedMovie(id={self.id}, title={self.title}, plot={self.plot}, poster_url={self.poster_url}, poster_description={self.poster_description}, payload={self.payload})"
    

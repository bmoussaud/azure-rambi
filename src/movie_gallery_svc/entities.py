import json
import uuid
import logging
from pydantic import BaseModel
from typing import List

class MovieRequest(BaseModel):
    """Request model for adding a new movie."""
    title: str
    description: str

class Movie(dict):
    """Movie model for storing movie details."""
    def __init__(self, movie_id : str, title : str, description : str):
        dict.__init__(self, movie_id=movie_id, title=title, description=description)
   
    def __repr__(self):
        return f"MovieGallery(id={self['id']}, title={self['title']}, description={self['description']})"

    def getattr(self, key):
        """Get attribute value by key."""
        if key not in self:
            raise KeyError(f"Key '{key}' not found in Movie.")
        return self[key]

    def setattr(self, key, value):
        """Set attribute value by key."""
        if key not in self:
            raise KeyError(f"Key '{key}' not found in Movie.")
        if not isinstance(value, str):
            raise TypeError(f"Value for '{key}' must be a string.")
        self[key] = value

    def __str__(self):
        return f"Movie(movie_id={self['movie_id']}, title={self['title']}, description={self['description']})"
    
    @staticmethod
    def from_bytes(json_bytes : bytes) -> 'Movie':
        """Convert bytes to Movie object."""
        item = json.loads(json_bytes.decode('utf-8'))
        return Movie(
            item["id"],
            item["title"],
            item["description"]
        )
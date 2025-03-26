from pydantic import BaseModel
import json
import uuid
import logging
from typing import List

class MovieRequest(BaseModel):
    """Request model for adding a new movie."""
    title: str
    description: str

class Movie(dict):
    """Movie model for storing movie details."""
    def __init__(self, id : str, title : str, description : str):
        dict.__init__(self, id=id, title=title, description=description)
   
    def __repr__(self):
        return f"MovieGallery(id={self['id']}, title={self['title']}, description={self['description']})"

    def getattr(self, key):
        return self[key]

    def setattr(self, key, value):
        self[key] = value

    def __str__(self):
        return f"MovieGallery(id={self['id']}, title={self['title']}, description={self['description']})"
    
    @staticmethod
    def from_bytes(json_bytes : bytes) -> 'Movie':
        """Convert bytes to Movie object."""
        item = json.loads(json_bytes.decode('utf-8'))
        return Movie(
            item["id"],
            item["title"],
            item["description"]
        )
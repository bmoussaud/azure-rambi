# Pydantic models
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, UTC
import json

class MovieUpdateEvent(BaseModel):
    """Model for movie update events from pubsub."""
    movie_id: str
    title: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    internal_poster_url: Optional[str] = None
    created_at: Optional[str] = None

class PosterValidationRequest(BaseModel):
    """Request model for poster validation."""
    movie_id: str = Field(..., description="Unique identifier for the movie")
    poster_url: Optional[str] = Field(None, description="URL of the poster image")
    poster_description: str = Field(..., description="Description of the movie poster")
    movie_title: Optional[str] = Field(None, description="Movie title for context")
    movie_genre: Optional[str] = Field(None, description="Movie genre for context")
    language: Optional[str] = Field("en", description="Language for the validation response")

class ValidationScore(BaseModel):
    """Individual validation score."""
    category: str = Field(..., description="Validation category")
    score: int = Field(..., ge=0, le=100, description="Score from 0-100")
    reasoning: str = Field(..., description="Explanation of the score")

class PosterValidationResponse(BaseModel):
    """Response model for poster validation."""
    id: str = Field(..., description="Unique identifier for the validation response")
    overall_score: int = Field(..., ge=0, le=100, description="Overall validation score")
    detailed_scores: List[ValidationScore] = Field(..., description="Detailed breakdown of scores")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")
    validation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_json(cls, json_str: str) -> 'PosterValidationResponse':
        """Create a PosterValidationResponse instance from a JSON string"""
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self) -> str:
        """Convert the PosterValidationResponse instance to a JSON string"""
        return self.model_dump_json()
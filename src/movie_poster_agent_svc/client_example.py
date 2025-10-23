"""Example client for testing the Movie Poster Agent API."""

import asyncio
import json
from typing import Optional
import httpx


class MoviePosterAgentClient:
    """Client for interacting with the Movie Poster Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client."""
        self.base_url = base_url.rstrip('/')
        
    async def health_check(self) -> dict:
        """Check the health of the service."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def validate_poster_url(
        self,
        poster_url: str,
        description: str,
        movie_title: Optional[str] = None,
        movie_genre: Optional[str] = None
    ) -> dict:
        """Validate a movie poster from URL."""
        data = {
            "poster_description": description,
            "poster_url": poster_url
        }
        
        if movie_title:
            data["movie_title"] = movie_title
        if movie_genre:
            data["movie_genre"] = movie_genre
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/validate", data=data)
            response.raise_for_status()
            return response.json()
    
    async def validate_poster_file(
        self,
        image_path: str,
        description: str,
        movie_title: Optional[str] = None,
        movie_genre: Optional[str] = None
    ) -> dict:
        """Validate a movie poster from file."""
        data = {
            "poster_description": description
        }
        
        if movie_title:
            data["movie_title"] = movie_title
        if movie_genre:
            data["movie_genre"] = movie_genre
        
        with open(image_path, "rb") as f:
            files = {"poster_file": f}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/validate", 
                    data=data, 
                    files=files
                )
                response.raise_for_status()
                return response.json()
    
    async def validate_batch(self, requests: list) -> dict:
        """Validate multiple posters in batch."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/validate-batch",
                json=requests
            )
            response.raise_for_status()
            return response.json()


async def example_usage():
    """Example usage of the client."""
    client = MoviePosterAgentClient()
    
    print("🎬 Movie Poster Agent Client Demo")
    print("=" * 40)
    
    # Health check
    print("\n1. Health Check:")
    try:
        health = await client.health_check()
        print(f"✅ Service Status: {health['status']}")
        print(f"   Mode: {health.get('mode', 'unknown')}")
        print(f"   AI Configured: {health.get('ai_endpoint_configured', False)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Example validation with URL
    print("\n2. Poster Validation (URL):")
    try:
        result = await client.validate_poster_url(
            poster_url="https://example.com/movie-poster.jpg",
            description="A dark, moody poster featuring the main character in silhouette against a stormy sky",
            movie_title="The Storm Within",
            movie_genre="Drama"
        )
        
        print(f"   Overall Score: {result['overall_score']}/100")
        print(f"   Categories: {len(result['detailed_scores'])}")
        print(f"   Recommendations: {len(result['recommendations'])}")
        
        # Show detailed scores
        for score in result['detailed_scores']:
            print(f"   - {score['category']}: {score['score']}/100")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Example batch validation
    print("\n3. Batch Validation:")
    try:
        batch_requests = [
            {
                "poster_url": "https://example.com/poster1.jpg",
                "poster_description": "Action-packed poster with explosions",
                "movie_title": "Action Hero",
                "movie_genre": "Action"
            },
            {
                "poster_url": "https://example.com/poster2.jpg", 
                "poster_description": "Romantic comedy poster with bright colors",
                "movie_title": "Love Actually Maybe",
                "movie_genre": "Comedy"
            }
        ]
        
        results = await client.validate_batch(batch_requests)
        print(f"   Processed {len(results)} posters")
        
        for i, result in enumerate(results):
            print(f"   Poster {i+1}: {result['overall_score']}/100")
            
    except Exception as e:
        print(f"❌ Batch validation failed: {e}")
    
    print("\n🎯 Demo completed!")


if __name__ == "__main__":
    asyncio.run(example_usage())
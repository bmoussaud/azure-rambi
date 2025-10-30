"""Movie Poster Validation Agent using Microsoft Agent Framework."""

import asyncio
import os
import logging
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from io import BytesIO

from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image
import aiofiles
import httpx
from dotenv import load_dotenv
from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from agent_framework import ChatMessage, TextContent, UriContent, DataContent, Role
from urllib.parse import urlparse
from ai_tools import ImageLoader, get_image_content
from dapr.ext.fastapi import DaprApp
from dapr.clients import DaprClient
from store import ValidationStore
from cloudevents.http import from_http
from agent import PosterValidationAgent
from entities import PosterValidationRequest, PosterValidationResponse, MovieUpdateEvent
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure telemetry
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()
    logger.info("Azure Monitor telemetry configured")

app = FastAPI(
    title="Movie Poster Validation Agent",
    description="AI Agent for validating movie poster images and descriptions",
    version="1.0.0"
)

# Initialize DAPR
dapr_app = DaprApp(app)
store=ValidationStore(DaprClient())
# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Global agent instance
poster_agent = PosterValidationAgent()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Movie Poster Validation Agent is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    ai_configured = poster_agent.project_endpoint and poster_agent.project_endpoint != "https://demo.openai.azure.com"
    return {
        "status": "healthy",
        "service": "movie-poster-agent",
        "version": "1.0.0",
        "ai_endpoint_configured": ai_configured,
        "model": poster_agent.model_deployment,
        "mode": "production" if ai_configured else "demo"
    }

@app.post("/validate", response_model=PosterValidationResponse)
async def validate_poster_endpoint(
    movie_id: str = Form(..., description="Unique identifier for the movie"),
    poster_description: str = Form(..., description="Description of the movie poster"),
    movie_title: str = Form(None, description="Movie title for context"),
    movie_genre: str = Form(None, description="Movie genre for context"),
    poster_url: str = Form(None, description="URL of the poster image"),
    language: str = Form("en", description="Language for the validation response")
):
    """Validate a movie poster image and description."""
    try:
        # Validate input
        
        # Create validation request
        request = PosterValidationRequest(
            movie_id=movie_id,
            poster_url=poster_url,
            poster_description=poster_description,
            movie_title=movie_title,
            movie_genre=movie_genre,
            language=language
        )
        
        # Validate the poster
        result = await poster_agent.validate_poster(request)
        logger.info(f"Poster validation result for movie {request.movie_id}: {result}")
        logger.info(f"Validation completed with overall score: {result.overall_score}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in validation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during validation")


@app.get("/validations/{movie_id}", response_model=PosterValidationResponse)
async def get_validation(movie_id: str):
    """Get a specific validation result by movie ID."""
    try:
        logger.info(f"Retrieving validation for movie ID: {movie_id}")
        validation = store.try_find_by_id(movie_id)
        
        if validation is None:
            logger.warning(f"Validation not found for movie ID: {movie_id}")
            raise HTTPException(status_code=404, detail=f"Validation not found for movie ID: {movie_id}")
        
        logger.info(f"Retrieved validation for movie ID: {movie_id}")
        return validation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving validation for movie ID {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving validation")


@app.get("/validations", response_model=List[PosterValidationResponse])
async def list_validations():
    """List all stored validation results."""
    try:
        logger.info("Retrieving all validations")
        validations = store.find_all()
        
        logger.info(f"Retrieved {len(validations)} validations")
        return validations
    except Exception as e:
        logger.error(f"Error retrieving all validations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving validations")


@app.delete("/validations/{movie_id}")
async def delete_validation(movie_id: str):
    """Delete a validation result by movie ID."""
    try:
        logger.info(f"Deleting validation for movie ID: {movie_id}")
        
        # Check if validation exists first
        existing_validation = store.try_find_by_id(movie_id)
        if existing_validation is None:
            logger.warning(f"Validation not found for movie ID: {movie_id}")
            raise HTTPException(status_code=404, detail=f"Validation not found for movie ID: {movie_id}")
        
        # Delete the validation
        success = store.delete(movie_id)
        
        if success:
            logger.info(f"Successfully deleted validation for movie ID: {movie_id}")
            return {"message": f"Validation for movie ID {movie_id} deleted successfully", "success": True}
        else:
            logger.error(f"Failed to delete validation for movie ID: {movie_id}")
            raise HTTPException(status_code=500, detail="Failed to delete validation")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting validation for movie ID {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting validation")



@app.get("/liveness")
async def liveness():
    """Liveness probe endpoint."""
    return {"status": "alive"}

@app.get("/readiness")
async def readiness():
    """Readiness probe endpoint."""
    return {"status": "ready"}


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """DAPR subscription endpoint for service discovery."""
    return [
        {
            "pubsubname": "moviepubsub",
            "topic": "movie-updates",
            "route": "/movie-updates"
        }
    ]


@app.get("/env")
async def get_environment():
    """
    Environment information endpoint.
    Shows configuration and environment variables (sensitive values masked).
    """
    try:
        env_info = {
            "service": "movie-poster-agent",
            "version": "1.0.0",
            "environment_variables": {
                "AZURE_AI_PROJECT_ENDPOINT": os.getenv("AZURE_AI_PROJECT_ENDPOINT", "Not set"),
                "AZURE_AI_MODEL_DEPLOYMENT": os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o"),
                "PORT": os.getenv("PORT", "8005"),
                "PYTHON_VERSION": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "APPLICATIONINSIGHTS_CONNECTION_STRING": "***MASKED***" if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") else "Not set",
                "STORAGE_ACCOUNT_BLOB_URL": os.getenv("STORAGE_ACCOUNT_BLOB_URL", "Not set"),
                "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID", "Not set"),
            },
            "agent_configuration": {
                "project_endpoint_configured": poster_agent.project_endpoint is not None,
                "model_deployment": poster_agent.model_deployment,
                "image_loader_configured": hasattr(poster_agent, '_image_loader') and poster_agent._image_loader is not None,
            },
            "runtime_info": {
                "hostname": os.getenv("HOSTNAME", "Unknown"),
                "container_name": os.getenv("CONTAINER_APP_NAME", "Unknown"),
                "revision": os.getenv("CONTAINER_APP_REVISION", "Unknown"),
            }
        }
        
        return env_info
        
    except Exception as e:
        logger.error(f"Error getting environment info: {str(e)}")
        return Response(
            content=json.dumps({"error": "Failed to retrieve environment information"}),
            status_code=500,
            media_type="application/json"
        )




# DAPR subscription configuration endpoint
@dapr_app.subscribe(pubsub="moviepubsub", topic="movie-updates", route="/movie-updates")
async def movie_updates_subscription(request: Request):
    """DAPR subscription decorator for movie updates."""
    logger.info("🎬 DAPR subscription triggered!")
    try:
        # Get the request body (DAPR sends data in the body)
        body = await request.body()
        headers = dict(request.headers)
        logger.info(f"Headers: {headers}")
        logger.info("-Body---")
        logger.info(f"{body.decode('utf-8') if body else 'Empty body'}")
        logger.info("-/Body---")
        result = await poster_agent.validate_poster_str(body.decode('utf-8'), store_validation=True)
        logger.info(f"💾 validation result : {result}")
        return {"success": True}
    except Exception as e:
        logger.error(f"❌ Error in DAPR subscription handler: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
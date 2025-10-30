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
dapr_client = DaprClient()
store=ValidationStore(dapr_client)
# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)



class PosterValidationAgent:
    """Agent for validating movie posters using AI."""
    
    def __init__(self):
        """Initialize the validation agent."""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        
        logger.info(f"Initializing agent with endpoint: {self.project_endpoint}")
        logger.info(f"Using model deployment: {self.model_deployment}")

        self._image_loader = ImageLoader(os.getenv("AZURE_CLIENT_ID"))
       
    async def create_agent(self) -> ChatAgent:
        """Create and configure the chat agent."""
        #tools = [get_image_content]
        tools = []
        agent_instructions = """
You are a movie poster validation expert. Your job is to analyze movie posters and their descriptions to provide accurate validation scores.

For each validation request, you should includes the following categories in your analysis:

1. **Visual Quality Assessment (0-100)**: Evaluate the image quality, composition, resolution, and visual appeal
2. **Content Accuracy (0-100)**: Check if the poster accurately represents the described content
3. **Description Alignment (0-100)**: Verify how well the description matches what's actually shown in the image
4. **Professional Standards (0-100)**: Assess if the poster meets professional movie poster standards
5. **Genre Appropriateness (0-100)**: Determine if the visual style matches the movie genre

For each category, provide:
- A score from 0-100
- Clear reasoning explaining the score
- Specific observations about the poster


Finally, provide:
- An overall score (weighted average of all categories)
- 3-5 actionable recommendations for improvement

Be thorough, objective, and constructive in your analysis.
"""
        chat_client=AzureAIAgentClient(
                project_endpoint=self.project_endpoint,
                model_deployment_name=self.model_deployment,
                async_credential=DefaultAzureCredential(),
                agent_name="MoviePosterValidator",
            )
        # Enable Azure AI observability (optional but recommended)
        await chat_client.setup_azure_ai_observability()
        
        return ChatAgent(
            chat_client=chat_client,
            instructions=agent_instructions + "If you need to fetch the image content from a URL, use the `get_image_content` AI function which retrieves base64 encoded image data from Azure Blob Storage URLs" if len(tools) > 0 else ".",
            tools=tools
        )
        
    
    async def validate_poster(self, request: PosterValidationRequest) -> PosterValidationResponse:
        """Validate a movie poster using the AI agent."""
        try:
            #image_base64 = self._image_loader.encode_image_from_url(request.poster_url) if request.poster_url else None

            async with await self.create_agent() as agent:
                # Build the validation prompt
                validation_prompt = f"""
Please analyze this movie poster and provide a detailed validation assessment.

Movie Details:
- Movie ID: {request.movie_id or 'Not specified'}
- Title: {request.movie_title or 'Not specified'}
- Genre: {request.movie_genre or 'Not specified'}
- Description: {request.poster_description}
- Original Poster URL: {request.poster_url}
Provide your response in a structured format and the language is {request.language or "en"}.
"""
    
            message = ChatMessage(
                role=Role.USER,
                contents=[
                    TextContent(text=validation_prompt),
                    
                    #DataContent(
                    #    data=base64.b64decode(image_base64),
                    #    media_type="image/png"
                    #)
                ]
            )
            logger.info("Sending validation prompt to agent without image data content")
            logger.info(f"Prompt length: {len(message.contents[0].text)} characters")
            logger.info(f"{message.contents[0].text}")
            #logger.info(f"Image data size: {len(base64.b64decode(image_base64))} bytes")
            
            result = await agent.run(message, response_format=PosterValidationResponse)
            result.value.id = request.movie_id
            logger.info(f"Agent response received: {len(result.text)} characters")
            # Parse the response into structured format
            return result.value
                
        except Exception as e:
            logger.error(f"Error during poster validation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

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
        logger.info(f"Body (first 200 chars): {body[:200] if body else 'Empty body'}")
        
        # Parse the event data from body
        if body:
            try:
                event_data = json.loads(body.decode('utf-8'))
                logger.info(f"Parsed event data: {event_data}")
                logger.info(f"{json.dumps(event_data,indent=2)}")
                data = json.loads(json.loads(event_data.get("data","{}")))
                logger.info(f"{json.dumps(data,indent=2)}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from body: {e}")
                return {"success": False, "error": "Invalid JSON in request body"}
        else:
            logger.warning("Empty request body received")
            return {"success": False, "error": "Empty request body"}

        # Create Poster Validation Request
        logger.info("Create Poster Validation Request")
        poster_validation_request = PosterValidationRequest(
            movie_id=data.get('id','no id provided'),
            poster_url=data.get('internal_poster_url','no poster url provided'), 
            poster_description=data.get('poster_description', 'no description provided'),
            movie_title=data.get('title','no title provided'),
            movie_genre=data.get('genre','no genre provided'))
        
        logger.info(f"Created Poster Validation Request: {poster_validation_request}")
        logger.info(f"🖼️ Starting validation for movie '{poster_validation_request.movie_title}' (ID: {data.get('id')})")

        result = await poster_agent.validate_poster(poster_validation_request)

        logger.info(f"✅ Validation completed for movie '{poster_validation_request.movie_title}' with overall score: {result.overall_score}")
        logger.info(f"Results are:  {result}")
        # Store the validation result
        stored_result = store.upsert(result)
        logger.info(f"💾 Stored validation result for movie ID {poster_validation_request.movie_id}: {stored_result}")
        return {"success": True}
    except Exception as e:
        logger.error(f"❌ Error in DAPR subscription handler: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
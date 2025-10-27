"""Movie Poster Validation Agent using Microsoft Agent Framework."""

import asyncio
import os
import logging
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from io import BytesIO

from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form
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

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO    )

# Configure telemetry
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()
    logger.info("Azure Monitor telemetry configured")

app = FastAPI(
    title="Movie Poster Validation Agent",
    description="AI Agent for validating movie poster images and descriptions",
    version="1.0.0"
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Pydantic models
class PosterValidationRequest(BaseModel):
    """Request model for poster validation."""
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
    overall_score: int = Field(..., ge=0, le=100, description="Overall validation score")
    detailed_scores: List[ValidationScore] = Field(..., description="Detailed breakdown of scores")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")
    validation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class PosterValidationAgent:
    """Agent for validating movie posters using AI."""
    
    def __init__(self):
        """Initialize the validation agent."""
        self.project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        self.model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
        
        if not self.project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT environment variable is required")
        else:
            logger.info(f"Initializing agent with endpoint: {self.project_endpoint}")
            logger.info(f"Using model deployment: {self.model_deployment}")
        
        # Initialize blob storage for image processing with managed identity
        self.blob_service_client = None
        self.storage_account_url = os.getenv("STORAGE_ACCOUNT_BLOB_URL")
        
        if self.storage_account_url:
            # Use managed identity for blob storage access
            client_id = os.getenv("AZURE_CLIENT_ID")
            if client_id:
                logger.info(f"Using managed identity {client_id} for blob storage access")
                credential = ManagedIdentityCredential(client_id=client_id)
            else:
                logger.info("Using default Azure credential for blob storage access")
                credential = DefaultAzureCredential()
            
            self.blob_service_client = BlobServiceClient(
                account_url=self.storage_account_url,
                credential=credential
            )
            logger.info(f"Blob service client initialized with URL: {self.storage_account_url}")
    
    async def create_agent(self) -> ChatAgent:
        """Create and configure the chat agent."""
        agent_instructions = """
You are a movie poster validation expert. Your job is to analyze movie posters and their descriptions to provide accurate validation scores.

For each validation request, you should:

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
            instructions=agent_instructions,
        )
        
    
    async def encode_image_from_url(self, image_url: str) -> str:
        logger.info(f"Encoding image from URL: {image_url}")
        """Encode image from URL to base64, using managed identity for Azure blob storage URLs."""
        try:
            # Check if this is an Azure blob storage URL
            if self._is_azure_blob_url(image_url):
                logger.info("Detected Azure blob storage URL, using authenticated access")
                return await self._encode_image_from_blob_url(image_url)
            else:
                # Regular HTTP URL - use direct access
                logger.info("Using direct HTTP access for non-blob URL")
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    
                    logger.info(f"Image fetched successfully: {len(response.content)} bytes")
                    image = Image.open(BytesIO(response.content))
                    
                    # Convert to base64
                    logger.info("Encoding image to base64")
                    return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image from URL {image_url}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to process image from URL: {str(e)}")
    
    def _is_azure_blob_url(self, url: str) -> bool:
        """Check if URL is an Azure blob storage URL."""
        try:
            parsed = urlparse(url)
            return 'blob.core.windows.net' in parsed.netloc
        except Exception:
            return False
    
    async def _encode_image_from_blob_url(self, blob_url: str) -> str:
        """Encode image from Azure blob storage URL using managed identity."""
        try:
            if not self.blob_service_client:
                raise HTTPException(
                    status_code=500, 
                    detail="Blob storage client not configured for authenticated access"
                )
            
            # Parse the blob URL to extract container and blob name
            parsed = urlparse(blob_url)
            path_parts = parsed.path.lstrip('/').split('/')
            
            if len(path_parts) < 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid blob URL format: {blob_url}"
                )
            
            container_name = path_parts[0]
            blob_name = '/'.join(path_parts[1:])
            
            logger.info(f"Accessing blob: container={container_name}, blob={blob_name}")
            
            # Get blob client and download content
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Download blob content
            async with blob_client:
                blob_data = await blob_client.download_blob()
                content = await blob_data.readall()
            
            logger.info(f"Blob downloaded successfully: {len(content)} bytes")
            
            # Validate it's an image
            image = Image.open(BytesIO(content))
            
            # Convert to base64
            logger.info("Encoding blob image to base64")
            return base64.b64encode(content).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error accessing blob {blob_url}: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to access blob with managed identity: {str(e)}"
            )
    
    
    async def validate_poster(self, request: PosterValidationRequest) -> PosterValidationResponse:
        """Validate a movie poster using the AI agent."""
        try:
            image_base64 = await self.encode_image_from_url(request.poster_url)

            async with await self.create_agent() as agent:
                # Build the validation prompt
                validation_prompt = f"""
Please analyze this movie poster and provide a detailed validation assessment.

Movie Details:
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
                    DataContent(
                        data=base64.b64decode(image_base64),
                        media_type="image/png"
                    )
                ]
            )
            logger.info("Sending validation prompt to agent with image data content")
            logger.info(f"Prompt length: {len(message.contents[0].text)} characters")
            logger.info(f"{message.contents[0].text}")
            logger.info(f"Image data size: {len(base64.b64decode(image_base64))} bytes")
            
            result = await agent.run(message, response_format=PosterValidationResponse)
            
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
            poster_url=poster_url,
            poster_description=poster_description,
            movie_title=movie_title,
            movie_genre=movie_genre,
            language=language
        )
        
        # Validate the poster
        result = await poster_agent.validate_poster(request)
        
        logger.info(f"Validation completed with overall score: {result.overall_score}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in validation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during validation")



@app.get("/liveness")
async def liveness():
    """
    Liveness probe endpoint.
    """
    #logging.info("Liveness probe")
    return Response(content=json.dumps({"status": "alive"}), media_type="application/json")

@app.get("/readiness")
async def readiness():
    """
    Readiness probe endpoint.
    """
    #logging.info("Readiness probe")
    return Response(content=json.dumps({"status": "ready"}), media_type="application/json")

@app.get("/env")
async def environment_info():
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
                "blob_storage_configured": poster_agent.blob_service_client is not None,
                "storage_account_url": poster_agent.storage_account_url or "Not configured",
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
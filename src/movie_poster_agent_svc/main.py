"""Movie Poster Validation Agent using Microsoft Agent Framework."""

import asyncio
import os
import logging
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image
import aiofiles
import httpx
from dotenv import load_dotenv
from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

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
        
        # Initialize blob storage for image processing
        self.blob_client = None
        if storage_connection := os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
            self.blob_client = BlobServiceClient.from_connection_string(storage_connection)
    
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
        
        return ChatAgent(
            chat_client=AzureAIAgentClient(
                project_endpoint=self.project_endpoint,
                model_deployment_name=self.model_deployment,
                async_credential=DefaultAzureCredential(),
                agent_name="MoviePosterValidator",
            ),
            instructions=agent_instructions,
        )
    
    async def encode_image_from_url(self, image_url: str) -> str:
        """Download and encode image from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                # Validate it's an image
                image = Image.open(BytesIO(response.content))
                
                # Convert to base64
                return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image from URL {image_url}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to process image from URL: {str(e)}")
    
    async def encode_image_from_file(self, image_file: UploadFile) -> str:
        """Encode uploaded image file."""
        try:
            content = await image_file.read()
            
            # Validate it's an image
            image = Image.open(BytesIO(content))
            
            # Convert to base64
            return base64.b64encode(content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding uploaded image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to process uploaded image: {str(e)}")
    
    def parse_agent_response(self, response_text: str) -> PosterValidationResponse:
        """Parse the agent's response into structured validation results."""
        try:
            # This is a simplified parser - in production, you might want to use more sophisticated parsing
            # or structure the agent's response format more strictly

            logger.info("Parsing agent response")
            logger.info(response_text)
            
            lines = response_text.split('\n')
            detailed_scores = []
            recommendations = []
            overall_score = 75  # Default fallback
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for section headers
                if "Visual Quality" in line and ":" in line:
                    current_section = "visual_quality"
                elif "Content Accuracy" in line and ":" in line:
                    current_section = "content_accuracy"
                elif "Description Alignment" in line and ":" in line:
                    current_section = "description_alignment"
                elif "Professional Standards" in line and ":" in line:
                    current_section = "professional_standards"
                elif "Genre Appropriateness" in line and ":" in line:
                    current_section = "genre_appropriateness"
                elif "Overall Score" in line and ":" in line:
                    current_section = "overall"
                elif "Recommendations" in line:
                    current_section = "recommendations"
                
                # Extract scores and reasoning
                if current_section and current_section != "recommendations" and current_section != "overall":
                    if "/100" in line or "Score:" in line:
                        # Extract score
                        import re
                        score_match = re.search(r'(\d+)(?:/100)?', line)
                        if score_match:
                            score = int(score_match.group(1))
                            # Look for reasoning in the next few lines
                            reasoning = line.split(':', 1)[-1].strip() if ':' in line else "No specific reasoning provided"
                            
                            detailed_scores.append(ValidationScore(
                                category=current_section.replace('_', ' ').title(),
                                score=min(100, max(0, score)),
                                reasoning=reasoning
                            ))
                
                # Extract overall score
                if current_section == "overall" and any(char.isdigit() for char in line):
                    import re
                    score_match = re.search(r'(\d+)', line)
                    if score_match:
                        overall_score = int(score_match.group(1))
                
                # Extract recommendations
                if current_section == "recommendations" and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    recommendation = line.lstrip('-•* ').strip()
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Ensure we have at least some default scores if parsing failed
            if not detailed_scores:
                detailed_scores = [
                    ValidationScore(category="General Assessment", score=overall_score, reasoning="Automated assessment based on overall analysis")
                ]
            
            if not recommendations:
                recommendations = ["Consider professional design review", "Ensure high image quality", "Verify content accuracy"]
            
            return PosterValidationResponse(
                overall_score=min(100, max(0, overall_score)),
                detailed_scores=detailed_scores,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error parsing agent response: {str(e)}")
            # Return a fallback response
            return PosterValidationResponse(
                overall_score=50,
                detailed_scores=[
                    ValidationScore(category="General Assessment", score=50, reasoning="Unable to parse detailed analysis")
                ],
                recommendations=["Please review the poster manually due to analysis error"]
            )
    
    async def validate_poster(self, request: PosterValidationRequest, image_base64: Optional[str] = None) -> PosterValidationResponse:
        """Validate a movie poster using the AI agent."""
        try:
            async with await self.create_agent() as agent:
                # Build the validation prompt
                validation_prompt = f"""
Please analyze this movie poster and provide a detailed validation assessment.

Movie Details:
- Title: {request.movie_title or 'Not specified'}
- Genre: {request.movie_genre or 'Not specified'}
- Description: {request.poster_description}

Please evaluate the poster across these categories and provide scores from 0-100:

1. Visual Quality Assessment: Image quality, composition, resolution, visual appeal
2. Content Accuracy: Does the poster accurately represent the described content?
3. Description Alignment: How well does the description match the actual image?
4. Professional Standards: Does it meet professional movie poster standards?
5. Genre Appropriateness: Does the visual style match the movie genre?

For each category, provide:
- A score from 0-100
- Clear reasoning for the score

Finally, provide:
- An overall weighted score
- 3-5 specific recommendations for improvement
Provide your response in a structured format and the language is {request.language or "en"}.

Image: {"[Image provided for analysis]" if image_base64 else "[No image provided - analysis based on description only]"}
"""
                

            from agent_framework import ChatMessage, TextContent, UriContent, Role
            message = ChatMessage(
                role=Role.USER,
                contents=[
                    TextContent(text=validation_prompt),
                    UriContent(
                        uri=request.poster_url,
                        media_type="image/jpeg"
                    )
                ]
            )
            logger.info("Sending validation prompt to agent")
            logger.info(f"{message.contents[0].text[:200]}...")  # Log first 200 chars of prompt
            result = await agent.run(message, response_format=PosterValidationResponse)
            
            logger.info(f"Agent response received: {len(result.text)} characters")
            
            # Parse the response into structured format$
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
    poster_file: UploadFile = File(None, description="Upload poster image file")
):
    """Validate a movie poster image and description."""
    try:
        # Validate input
        if not poster_url and not poster_file:
            raise HTTPException(status_code=400, detail="Either poster_url or poster_file must be provided")
        
        if poster_url and poster_file:
            raise HTTPException(status_code=400, detail="Provide either poster_url or poster_file, not both")
        
        # Create validation request
        request = PosterValidationRequest(
            poster_url=poster_url,
            poster_description=poster_description,
            movie_title=movie_title,
            movie_genre=movie_genre
        )
        
        # Process image
        image_base64 = None
        if poster_url:
            image_base64 = await poster_agent.encode_image_from_url(poster_url)
            logger.info(f"Processed image from URL: {poster_url}")
        elif poster_file:
            image_base64 = await poster_agent.encode_image_from_file(poster_file)
            logger.info(f"Processed uploaded image: {poster_file.filename}")
        
        # Validate the poster
        result = await poster_agent.validate_poster(request, image_base64)
        
        logger.info(f"Validation completed with overall score: {result.overall_score}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in validation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during validation")

@app.post("/validate-batch", response_model=List[PosterValidationResponse])
async def validate_posters_batch(requests: List[PosterValidationRequest]):
    """Validate multiple movie posters in batch."""
    try:
        results = []
        
        for i, request in enumerate(requests):
            try:
                logger.info(f"Processing batch item {i+1}/{len(requests)}")
                
                # Process image if URL provided
                image_base64 = None
                if request.poster_url:
                    image_base64 = await poster_agent.encode_image_from_url(request.poster_url)
                
                # Validate the poster
                result = await poster_agent.validate_poster(request, image_base64)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing batch item {i+1}: {str(e)}")
                # Add error result for this item
                results.append(PosterValidationResponse(
                    overall_score=0,
                    detailed_scores=[
                        ValidationScore(category="Error", score=0, reasoning=f"Processing failed: {str(e)}")
                    ],
                    recommendations=["Please retry this validation individually"]
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Unexpected error in batch validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during batch validation")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
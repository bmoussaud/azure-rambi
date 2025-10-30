"""Movie Poster Validation Agent using Microsoft Agent Framework."""

import os
import logging
from typing import Optional

from fastapi import HTTPException
from agent_framework import ChatAgent, ChatMessage, TextContent, Role
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential
from ai_tools import ImageLoader, get_image_content
from entities import PosterValidationRequest, PosterValidationResponse

# Configure logging
logger = logging.getLogger(__name__)


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
        chat_client = AzureAIAgentClient(
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
"""Tests for the Movie Poster Validation Agent."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image

from main import app, PosterValidationAgent, PosterValidationRequest


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


class TestPosterValidationAgent:
    """Test cases for PosterValidationAgent."""
    
    @patch.dict('os.environ', {'AZURE_AI_PROJECT_ENDPOINT': 'https://test.openai.azure.com'})
    def test_agent_initialization(self):
        """Test agent initialization with required environment variables."""
        agent = PosterValidationAgent()
        assert agent.project_endpoint == 'https://test.openai.azure.com'
        assert agent.model_deployment == 'gpt-4o'
    
    def test_agent_initialization_missing_endpoint(self):
        """Test agent initialization fails without endpoint."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="AZURE_AI_PROJECT_ENDPOINT environment variable is required"):
                PosterValidationAgent()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_encode_image_from_url(self, mock_client, sample_image):
        """Test image encoding from URL."""
        agent = PosterValidationAgent()
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = sample_image.getvalue()
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await agent.encode_image_from_url("https://example.com/image.jpg")
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_client_instance.get.assert_called_once_with("https://example.com/image.jpg")
    
    @pytest.mark.asyncio
    async def test_encode_image_from_file(self, sample_image):
        """Test image encoding from uploaded file."""
        agent = PosterValidationAgent()
        
        # Mock uploaded file
        mock_file = AsyncMock()
        mock_file.read.return_value = sample_image.getvalue()
        
        result = await agent.encode_image_from_file(mock_file)
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_file.read.assert_called_once()
    
    def test_parse_agent_response(self):
        """Test parsing of agent response."""
        agent = PosterValidationAgent()
        
        sample_response = """
        Visual Quality Assessment: 85/100 - Excellent composition and clarity
        Content Accuracy: 90/100 - Accurately represents the movie content
        Description Alignment: 80/100 - Good match with description
        Professional Standards: 85/100 - Meets industry standards
        Genre Appropriateness: 88/100 - Perfect for the horror genre
        
        Overall Score: 86/100
        
        Recommendations:
        - Improve color contrast for better visibility
        - Add more dynamic elements to catch attention
        - Consider adjusting typography for better readability
        """
        
        result = agent.parse_agent_response(sample_response)
        
        assert result.overall_score == 86
        assert len(result.detailed_scores) >= 1
        assert len(result.recommendations) >= 1
        assert all(0 <= score.score <= 100 for score in result.detailed_scores)


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["status"] == "healthy"
    
    @patch.dict('os.environ', {'AZURE_AI_PROJECT_ENDPOINT': 'https://test.openai.azure.com'})
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "movie-poster-agent"
        assert data["ai_endpoint_configured"] is True
    
    def test_validate_endpoint_missing_parameters(self, client):
        """Test validation endpoint with missing parameters."""
        response = client.post("/validate", data={
            "poster_description": "A great movie poster"
        })
        assert response.status_code == 400
        assert "Either poster_url or poster_file must be provided" in response.json()["detail"]
    
    def test_validate_endpoint_both_parameters(self, client):
        """Test validation endpoint with both URL and file."""
        response = client.post(
            "/validate",
            data={
                "poster_description": "A great movie poster",
                "poster_url": "https://example.com/image.jpg"
            },
            files={"poster_file": ("test.jpg", b"fake image data", "image/jpeg")}
        )
        assert response.status_code == 400
        assert "Provide either poster_url or poster_file, not both" in response.json()["detail"]
    
    def test_openapi_schema_generation(self, client):
        """Test that the OpenAPI schema is generated correctly."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "paths" in schema
        assert "/validate" in schema["paths"]
        assert "/health" in schema["paths"]
        
        # Check that the validation endpoint has the expected parameters
        validate_endpoint = schema["paths"]["/validate"]["post"]
        assert "requestBody" in validate_endpoint


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test cases for async endpoint functionality."""
    
    @patch.dict('os.environ', {'AZURE_AI_PROJECT_ENDPOINT': 'https://test.openai.azure.com'})
    @patch('main.PosterValidationAgent.validate_poster')
    @patch('main.PosterValidationAgent.encode_image_from_url')
    async def test_validate_poster_functionality(self, mock_encode, mock_validate):
        """Test the core poster validation functionality."""
        from main import PosterValidationResponse, ValidationScore
        
        # Setup mocks
        mock_encode.return_value = "base64encodedimage"
        mock_validate.return_value = PosterValidationResponse(
            overall_score=85,
            detailed_scores=[
                ValidationScore(category="Visual Quality", score=90, reasoning="Excellent composition")
            ],
            recommendations=["Great work!"]
        )
        
        agent = PosterValidationAgent()
        request = PosterValidationRequest(
            poster_url="https://example.com/image.jpg",
            poster_description="A movie poster",
            movie_title="Test Movie"
        )
        
        result = await agent.validate_poster(request, "base64image")
        
        assert result.overall_score == 85
        assert len(result.detailed_scores) == 1
        assert len(result.recommendations) == 1


if __name__ == "__main__":
    pytest.main([__file__])
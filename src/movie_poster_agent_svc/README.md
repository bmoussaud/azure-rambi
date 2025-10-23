# Movie Poster Agent Service

This service provides AI-powered validation of movie poster images and descriptions using Microsoft Agent Framework and Azure AI Foundry.

## Features

- **Image Analysis**: Analyze poster images for visual quality and content accuracy
- **Description Validation**: Compare descriptions with actual image content
- **Professional Assessment**: Evaluate against movie poster industry standards
- **Batch Processing**: Support for validating multiple posters at once
- **Detailed Scoring**: Provides scores (0-100) across multiple categories:
  - Visual Quality Assessment
  - Content Accuracy
  - Description Alignment
  - Professional Standards
  - Genre Appropriateness

## API Endpoints

### `POST /validate`
Validate a single movie poster.

**Parameters:**
- `poster_description` (required): Description of the movie poster
- `movie_title` (optional): Movie title for context
- `movie_genre` (optional): Movie genre for context
- `poster_url` (optional): URL of the poster image
- `poster_file` (optional): Upload poster image file

**Response:**
```json
{
  "overall_score": 85,
  "detailed_scores": [
    {
      "category": "Visual Quality",
      "score": 90,
      "reasoning": "High resolution image with excellent composition"
    }
  ],
  "recommendations": [
    "Consider adjusting color balance",
    "Add more dynamic elements"
  ],
  "validation_timestamp": "2025-01-01T12:00:00Z"
}
```

### `POST /validate-batch`
Validate multiple movie posters in a single request.

### `GET /health`
Health check endpoint.

## Environment Variables

- `AZURE_AI_PROJECT_ENDPOINT`: Azure AI Foundry project endpoint (required)
- `AZURE_AI_MODEL_DEPLOYMENT`: Model deployment name (default: "gpt-4o")
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage connection string (optional)
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Application Insights connection string (optional)
- `PORT`: Port to run the service on (default: 8000)

## Development

### Prerequisites

- Python 3.11+
- uv package manager
- Azure AI Foundry project with deployed models

### Install Dependencies

```bash
uv pip install -e .
```

### Run Locally

```bash
python main.py
```

### Run with Docker

```bash
docker build -t movie-poster-agent .
docker run -p 8000:8000 \
  -e AZURE_AI_PROJECT_ENDPOINT="your-endpoint" \
  -e AZURE_AI_MODEL_DEPLOYMENT="gpt-4o" \
  movie-poster-agent
```

## Deployment

This service is designed to be deployed on Azure Container Apps as part of the Azure Rambi project.

## Architecture

The service uses:
- **Microsoft Agent Framework** for AI agent orchestration
- **Azure AI Foundry** for multimodal AI models (text + image)
- **FastAPI** for the web API
- **Pydantic** for data validation
- **Azure Storage** for image processing (optional)
- **Application Insights** for monitoring and telemetry
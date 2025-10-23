# Movie Poster Agent Service

## Overview

The Movie Poster Agent Service is a new Python-based microservice built using Microsoft Agent Framework and Azure AI Foundry. It provides AI-powered validation of movie poster images and descriptions, returning detailed scores and recommendations.

## ✅ What Was Created

### 1. Service Structure
- **Location**: `/src/movie_poster_agent_svc/`
- **Language**: Python 3.11+
- **Framework**: FastAPI + Microsoft Agent Framework
- **Dependencies**: Managed with `uv` (UV Package Manager)

### 2. Core Files
- `main.py` - Main FastAPI application with agent logic
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration for UV
- `Dockerfile` - Container configuration
- `README.md` - Service documentation
- `test_main.py` - Unit tests
- `client_example.py` - API client example
- `deploy.sh` - Deployment helper script
- `.env.template` - Environment configuration template

### 3. Infrastructure
- **Bicep Template**: `/infra/modules/apps/movie-poster-agent-svc.bicep`
- **Main Infrastructure**: Updated `/infra/main.bicep` to include the new service
- **Azure Configuration**: Updated `/azure.yaml` to deploy the service

### 4. Key Features
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

## 🚀 Deployment

The service is configured to deploy as an Azure Container App alongside the existing services.

### Azure Resources Used
- **Azure AI Foundry**: For the `gpt-4o` multimodal model
- **Azure Container Apps**: For hosting the service
- **Azure Storage**: For image processing (optional)
- **Application Insights**: For monitoring and telemetry
- **Managed Identity**: For secure authentication

### Environment Variables
- `AZURE_AI_PROJECT_ENDPOINT` - Azure AI Foundry project endpoint (required)
- `AZURE_AI_MODEL_DEPLOYMENT` - Model deployment name (default: "gpt-4o")
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Storage connection (optional)
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - App Insights connection (optional)

## 🔧 Local Development

1. **Install Dependencies**:
   ```bash
   cd src/movie_poster_agent_svc
   pip install --pre -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your Azure AI Foundry endpoint
   ```

3. **Run Locally**:
   ```bash
   python main.py
   # or
   ./deploy.sh run
   ```

4. **Test the Service**:
   ```bash
   curl http://localhost:8000/health
   python client_example.py
   ```

## 📋 API Endpoints

### `POST /validate`
Validate a single movie poster with image URL or file upload.

### `POST /validate-batch`
Validate multiple movie posters in a single request.

### `GET /health`
Health check endpoint with service status.

### `GET /`
Root endpoint with basic service information.

## 🧪 Testing

Run the test suite:
```bash
./deploy.sh test
# or
python -m pytest test_main.py -v
```

## 🐳 Docker

Build and run with Docker:
```bash
./deploy.sh build
docker run -p 8000:8000 -e AZURE_AI_PROJECT_ENDPOINT="your-endpoint" movie-poster-agent-svc
```

## 🔍 Integration

The service integrates seamlessly with the existing Azure Rambi architecture:
- Uses the same AI Foundry project and models
- Follows the same container app deployment patterns
- Uses the same monitoring and identity management
- Can be called by other services in the system

## 📝 Notes

- The service runs in "demo mode" if Azure AI endpoint is not configured
- Uses Agent Framework for sophisticated AI agent capabilities
- Supports both URL-based and file upload image validation
- Provides detailed scoring across multiple validation categories
- Ready for production deployment with proper security configurations
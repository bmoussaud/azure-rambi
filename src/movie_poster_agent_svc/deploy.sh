#!/bin/bash

# Movie Poster Agent Service Deployment Script
set -e

SERVICE_NAME="movie-poster-agent-svc"
SERVICE_DIR="/workspaces/azure-rambi/src/movie_poster_agent_svc"

echo "🎬 Movie Poster Agent Service Deployment"
echo "========================================"

# Function to show usage
show_usage() {
    echo "Usage: $0 [build|test|run|deploy]"
    echo ""
    echo "Commands:"
    echo "  build   - Build Docker image"
    echo "  test    - Run tests"
    echo "  run     - Run service locally"
    echo "  deploy  - Deploy to Azure using azd"
    echo ""
}

# Build Docker image
build_image() {
    echo "🔨 Building Docker image..."
    cd "$SERVICE_DIR"
    docker build -t "$SERVICE_NAME" .
    echo "✅ Docker image built successfully"
}

# Run tests
run_tests() {
    echo "🧪 Running tests..."
    cd "$SERVICE_DIR"
    if [ -f "requirements.txt" ]; then
        pip install --pre -r requirements.txt --quiet
    fi
    pip install pytest pytest-asyncio --quiet
    python -m pytest test_main.py -v
    echo "✅ Tests completed"
}

# Run service locally
run_local() {
    echo "🚀 Starting service locally..."
    cd "$SERVICE_DIR"
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo "⚠️  No .env file found. Copy .env.template to .env and configure it."
        echo "   Required: AZURE_AI_PROJECT_ENDPOINT"
        exit 1
    fi
    
    echo "Starting server on http://localhost:8000"
    echo "API docs available at http://localhost:8000/docs"
    python main.py
}

# Deploy to Azure
deploy_azure() {
    echo "☁️  Deploying to Azure..."
    cd "/workspaces/azure-rambi"
    
    # Check if azd is installed
    if ! command -v azd &> /dev/null; then
        echo "❌ Azure Developer CLI (azd) is not installed"
        exit 1
    fi
    
    echo "Deploying all services including $SERVICE_NAME..."
    azd deploy
    echo "✅ Deployment completed"
}

# Main script logic
case "$1" in
    "build")
        build_image
        ;;
    "test")
        run_tests
        ;;
    "run")
        run_local
        ;;
    "deploy")
        deploy_azure
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
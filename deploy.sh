#!/bin/bash

# Trading System - Simple Docker Deployment Script
# Uses ONLY the single Dockerfile for all environment setup

set -e

echo "🚀 Starting Trading System Deployment"
echo "📋 Using ONLY Dockerfile for environment setup"

# Build the Docker image using only the Dockerfile
echo "🔨 Building Docker image..."
docker build -t trading-system:latest .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Optional: Run the container locally for testing
if [ "$1" == "--run" ]; then
    echo "🏃 Running container locally for testing..."
    docker run -d \
        --name trading-system-test \
        -p 8000:8000 \
        --env-file config/production.env \
        trading-system:latest
    
    echo "🎯 Container started on http://localhost:8000"
    echo "🏥 Health check: http://localhost:8000/health"
    echo "📚 API docs: http://localhost:8000/docs"
fi

# Optional: Push to registry
if [ "$1" == "--push" ]; then
    if [ -z "$DOCKER_REGISTRY" ]; then
        echo "❌ DOCKER_REGISTRY environment variable not set"
        exit 1
    fi
    
    echo "📤 Pushing to registry: $DOCKER_REGISTRY"
    docker tag trading-system:latest $DOCKER_REGISTRY/trading-system:latest
    docker push $DOCKER_REGISTRY/trading-system:latest
    echo "✅ Image pushed successfully"
fi

echo "🎉 Deployment script completed"
echo "💡 Usage:"
echo "  ./deploy.sh           - Build only"
echo "  ./deploy.sh --run     - Build and run locally"
echo "  ./deploy.sh --push    - Build and push to registry" 
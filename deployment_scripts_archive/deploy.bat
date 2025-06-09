@echo off
REM Trading System - Simple Docker Deployment Script (Windows)
REM Uses ONLY the single Dockerfile for all environment setup

echo 🚀 Starting Trading System Deployment
echo 📋 Using ONLY Dockerfile for environment setup

REM Build the Docker image using only the Dockerfile
echo 🔨 Building Docker image...
docker build -t trading-system:latest .

if %ERRORLEVEL% EQU 0 (
    echo ✅ Docker image built successfully
) else (
    echo ❌ Docker build failed
    exit /b 1
)

REM Check for command line arguments
if "%1"=="--run" (
    echo 🏃 Running container locally for testing...
    docker run -d --name trading-system-test -p 8000:8000 --env-file config/production.env trading-system:latest
    
    echo 🎯 Container started on http://localhost:8000
    echo 🏥 Health check: http://localhost:8000/health
    echo 📚 API docs: http://localhost:8000/docs
)

if "%1"=="--push" (
    if "%DOCKER_REGISTRY%"=="" (
        echo ❌ DOCKER_REGISTRY environment variable not set
        exit /b 1
    )
    
    echo 📤 Pushing to registry: %DOCKER_REGISTRY%
    docker tag trading-system:latest %DOCKER_REGISTRY%/trading-system:latest
    docker push %DOCKER_REGISTRY%/trading-system:latest
    echo ✅ Image pushed successfully
)

echo 🎉 Deployment script completed
echo 💡 Usage:
echo   deploy.bat           - Build only
echo   deploy.bat --run     - Build and run locally
echo   deploy.bat --push    - Build and push to registry 
# Single Dockerfile Deployment Setup

## Overview
The trading system now uses **ONLY** a single Dockerfile for environment setup, eliminating confusion from multiple configuration files.

## Files Structure
```
trading-system-new/
├── Dockerfile              # Single Docker configuration file
├── requirements.txt        # Single Python dependencies file
├── docker-compose.yml      # Docker Compose configuration (uses Dockerfile)
├── deploy.sh              # Linux/Mac deployment script
├── deploy.bat             # Windows deployment script
└── config/
    └── production.env     # Environment variables
```

## What Was Removed
- ❌ `requirements-docker.txt`
- ❌ `requirements-ml.txt`  
- ❌ `requirements-test.txt`
- ❌ `requirements-local.txt`
- ❌ `requirements-minimal.txt`
- ❌ `requirements-prod.txt`
- ❌ `Dockerfile.production`

## What Remains
- ✅ `Dockerfile` - Single Docker configuration
- ✅ `requirements.txt` - Single Python dependencies file
- ✅ `docker-compose.yml` - Uses the single Dockerfile

## Deployment Commands

### Option 1: Using Deployment Scripts
```bash
# Linux/Mac
./deploy.sh                 # Build only
./deploy.sh --run          # Build and run locally
./deploy.sh --push         # Build and push to registry

# Windows
deploy.bat                 # Build only
deploy.bat --run          # Build and run locally  
deploy.bat --push         # Build and push to registry
```

### Option 2: Direct Docker Commands
```bash
# Build image
docker build -t trading-system:latest .

# Run locally for testing
docker run -d \
    --name trading-system-test \
    -p 8000:8000 \
    --env-file config/production.env \
    trading-system:latest

# Check health
curl http://localhost:8000/health
```

### Option 3: Docker Compose
```bash
# Start all services
docker-compose up -d

# Build and start
docker-compose up -d --build

# Stop services
docker-compose down
```

## Key Features of Single Dockerfile

1. **Multi-stage build**: Frontend (Node.js) + Backend (Python)
2. **Single requirements file**: Only `requirements.txt` is used
3. **Security**: Non-root user, minimal system dependencies
4. **Production-ready**: Health checks, proper environment variables
5. **Clean build**: No duplicate files or confusion

## Environment Variables
All environment variables are loaded from `config/production.env`:
- Database configuration
- Redis configuration  
- API keys and secrets
- JWT secrets
- Encryption keys

## DigitalOcean App Platform Deployment
The single Dockerfile will be automatically detected and used by DigitalOcean App Platform:

1. **Source**: GitHub repository
2. **Build**: Automatic Docker build using `Dockerfile`
3. **Environment**: Variables from App Platform settings
4. **Port**: Exposes port 8000
5. **Health Check**: `/health` endpoint

## Benefits
- ✅ **Simplicity**: Only one Docker configuration
- ✅ **Clarity**: No confusion about which requirements file to use
- ✅ **Maintainability**: Single source of truth
- ✅ **Reliability**: Consistent build across all environments
- ✅ **Security**: Built-in security best practices

## Troubleshooting
If deployment fails:
1. Check that `config/production.env` exists
2. Verify environment variables are set correctly
3. Ensure Docker daemon is running
4. Check Docker build logs for specific errors

## Production Deployment Status
- 🔨 **Dockerfile**: Simplified and production-ready
- 📦 **Dependencies**: Consolidated into single requirements.txt
- 🚀 **Deployment**: Ready for DigitalOcean App Platform
- 🔒 **Security**: Non-root user, minimal attack surface
- 📊 **Monitoring**: Health checks enabled 
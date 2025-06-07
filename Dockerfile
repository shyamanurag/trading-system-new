# Production-Ready Trading System Docker Image
FROM node:18-slim as frontend-builder

# Set working directory
WORKDIR /app

# Copy frontend package files and vite config
COPY src/frontend/package.json ./
COPY src/frontend/vite.config.js ./

# Copy frontend source code
COPY src/frontend/ ./

# Install dependencies and build frontend
RUN npm install --production=false
RUN npm run build

# Verify build output
RUN ls -la dist/ || echo "No dist directory found"
RUN ls -la dist/frontend/ || echo "No frontend build output found"

# Python application stage
FROM python:3.11-slim

# Build arguments for cache busting
ARG BUILD_DATE=2025-06-07
ARG VERSION=2.0.0

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    APP_PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libpq5 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy and install Python dependencies using ONLY requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from frontend builder
COPY --from=frontend-builder /app/dist/ ./dist/

# Create build timestamp
RUN echo "Build: ${BUILD_DATE} | Version: ${VERSION} | Single Requirements File: requirements.txt" > .build-timestamp

# Create logs directory and necessary directories
RUN mkdir -p /app/logs /app/backups /app/static

# Verify critical files exist
RUN ls -la health_check.py || echo "Warning: health_check.py not found"
RUN ls -la start_production.py || echo "Error: start_production.py missing"
RUN ls -la main.py || echo "Error: main.py missing"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check with fallback options
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD python health_check.py 2>/dev/null || curl -f http://localhost:8000/health 2>/dev/null || wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Start application with proper production settings
CMD ["python", "start_production.py"] 
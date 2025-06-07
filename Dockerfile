# Production-Ready Trading System Docker Image
FROM node:18-slim as frontend-builder

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./
COPY vite.config.js ./

# Copy frontend source code
COPY src/ ./src/

# Install dependencies and build frontend
RUN npm install --production=false
RUN npm run build

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
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libpq5 \
    curl \
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
COPY --from=frontend-builder /app/dist/frontend ./dist/frontend

# Create build timestamp
RUN echo "Build: ${BUILD_DATE} | Version: ${VERSION} | Single Requirements File: requirements.txt" > .build-timestamp

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 
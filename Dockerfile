# Multi-stage build for Trading System
FROM node:18-slim as frontend-builder

# Copy frontend files
WORKDIR /app
COPY package*.json ./
COPY vite.config.js ./
COPY src/ ./src/

# Build frontend from correct directory
RUN npm install
RUN npm run build

FROM python:3.11-slim as builder

# Build arguments for cache busting - REDIS DEBUG BUILD
ARG BUILD_DATE=2025-06-06-06-50
ARG FORCE_REBUILD=REDIS_DEBUG_BUILD_V3

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-docker.txt /app/requirements-docker.txt

# Install Python dependencies
WORKDIR /app
RUN pip install --no-cache-dir -r requirements-docker.txt

# Production stage
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application code
COPY . /app/

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/dist/frontend /app/dist/frontend

# Create timestamp file for cache busting - REDIS DEBUG BUILD
RUN echo "Build timestamp: ${BUILD_DATE} - Redis Debug Build - Environment Variable Priority Fix" > .build-timestamp

# Set environment variables
ENV PYTHONPATH=/app \
    PORT=8000 \
    ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
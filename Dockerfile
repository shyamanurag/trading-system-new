# Multi-stage build for Trading System
FROM python:3.11-slim as builder

# Build arguments for cache busting
ARG BUILD_DATE=2025-06-06-05-02
ARG FORCE_REBUILD=true

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
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application code
COPY . /app/

# Create timestamp file for cache busting
RUN echo "Build timestamp: ${BUILD_DATE}" > .build-timestamp

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
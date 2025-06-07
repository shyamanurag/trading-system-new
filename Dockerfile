# Multi-stage build for Trading System
FROM node:18-slim as frontend-builder

# Copy package files first
WORKDIR /app
COPY package*.json ./
COPY vite.config.js ./

# Copy the entire src directory
COPY src/ ./src/

# Change to frontend directory for Vite build (since vite.config.js has root: 'src/frontend')
WORKDIR /app/src/frontend

# Install dependencies and build from the frontend directory
RUN cd /app && npm install
RUN cd /app && npm run build

# Switch back to /app for copying built files
WORKDIR /app

FROM python:3.11-slim as builder

# Build arguments for cache busting - REDIS DEBUG BUILD
ARG BUILD_DATE=2025-06-07-16-00
ARG FORCE_REBUILD=KITECONNECT_FIX_V1

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
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

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

# Create timestamp file for cache busting - KITECONNECT FIX
RUN echo "Build timestamp: ${BUILD_DATE} - KiteConnect Fix - Single Requirements File" > .build-timestamp

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
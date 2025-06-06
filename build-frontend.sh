#!/bin/bash

echo "🚀 Building Trading System Frontend for DigitalOcean..."

# Set Node.js environment
export NODE_ENV=production
export NODE_VERSION=18

# Install dependencies
echo "📦 Installing dependencies..."
npm install --production=false

# Build the frontend
echo "🔨 Building frontend..."
npm run build

# Verify build output
if [ -d "dist/frontend" ]; then
    echo "✅ Frontend build successful!"
    echo "📁 Build output in dist/frontend"
    ls -la dist/frontend/
else
    echo "❌ Frontend build failed - no output directory found"
    exit 1
fi

echo "🎉 Frontend build complete!" 
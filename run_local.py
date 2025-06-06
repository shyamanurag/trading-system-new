#!/usr/bin/env python3
"""
Local Development Server - Simplified for Testing
Run the FastAPI app locally with minimal dependencies
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_local_environment():
    """Setup local development environment"""
    # Load environment variables
    load_dotenv()
    
    # Set minimal environment variables for local development
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('DEBUG', 'True')
    os.environ.setdefault('HOST', '127.0.0.1')
    os.environ.setdefault('PORT', '8000')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///./local_trading_system.db')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print("🚀 Starting Local Trading System API...")
    print(f"📍 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🌐 URL: http://{os.getenv('HOST')}:{os.getenv('PORT')}")
    print(f"📚 API Docs: http://{os.getenv('HOST')}:{os.getenv('PORT')}/docs")
    print(f"🏥 Health Check: http://{os.getenv('HOST')}:{os.getenv('PORT')}/health")

def create_minimal_main():
    """Create a minimal main.py that imports only what's available"""
    try:
        # Try to import the main app
        from main import app
        return app
    except ImportError as e:
        print(f"⚠️ Import error: {e}")
        print("📝 Creating minimal FastAPI app for testing...")
        
        # Create a minimal FastAPI app if main.py has issues
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        minimal_app = FastAPI(
            title="Trading System API - Local Dev",
            description="Minimal local development version",
            version="2.0.0-local"
        )
        
        @minimal_app.get("/")
        async def root():
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0-local",
                "service": "Trading System API - Local Development",
                "message": "Minimal version running locally"
            }
        
        @minimal_app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "api": True,
                    "local_mode": True
                }
            }
        
        return minimal_app

if __name__ == "__main__":
    setup_local_environment()
    
    # Get the app (main or minimal fallback)
    app = create_minimal_main()
    
    # Run the server
    uvicorn.run(
        app,
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 8000)),
        reload=True,  # Enable auto-reload for development
        log_level=os.getenv('LOG_LEVEL', 'info').lower(),
        access_log=True
    ) 
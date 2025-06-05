#!/usr/bin/env python3
"""
Trading System Server Startup Script
Runs the FastAPI server with proper configuration and error handling.
"""

import sys
import os
import uvicorn
from pathlib import Path

def main():
    """Start the trading system server."""
    try:
        print("🚀 Starting Trading System Server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,  # Enable auto-reload during development
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
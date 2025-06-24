#!/usr/bin/env python3
"""
Local development entry point for the trading system
Avoids relative import issues when running locally
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Import and run the app
    from bootstrap import app
    import uvicorn
    
    print("🚀 Starting AlgoAuto Trading System locally...")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
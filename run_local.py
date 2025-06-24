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

# Also add the parent directory for any parent imports
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Set environment to ensure we're running locally
    os.environ["ENVIRONMENT"] = "local"
    
    # Import and run the app - import as module since we added src to path
    import bootstrap
    import uvicorn
    
    print("🚀 Starting AlgoAuto Trading System locally...")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        bootstrap.app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
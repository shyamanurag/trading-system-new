#!/usr/bin/env python3
"""
COMPLETELY ISOLATED Local Development Server
===========================================
This script runs the trading system with ALL external connections disabled.
Perfect for debugging without any production dependencies.

Features:
- NO TrueData connections
- NO external API calls
- NO websocket connections
- Mock data for everything
- Local SQLite only
- Completely safe for development
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def setup_completely_isolated_environment():
    """Set up completely isolated development environment"""
    
    print("Setting up COMPLETELY ISOLATED local environment...")
    
    # CRITICAL: Force local development mode with ALL external connections disabled
    os.environ['LOCAL_DEVELOPMENT'] = 'true'
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['DEBUG'] = 'true'
    os.environ['PAPER_TRADING'] = 'true'
    os.environ['MOCK_TRADING'] = 'true'
    
    # DISABLE ALL EXTERNAL CONNECTIONS - CORRECT VARIABLE NAMES
    os.environ['TRUEDATA_DISABLED'] = 'true'
    os.environ['TRUEDATA_MOCK_MODE'] = 'true'
    os.environ['SKIP_TRUEDATA_AUTO_INIT'] = 'true'  # FIXED: Correct variable name
    os.environ['SKIP_TRUEDATA_INIT'] = 'true'       # Keep both for safety
    os.environ['WEBSOCKET_DISABLED'] = 'true'
    os.environ['ZERODHA_MOCK_MODE'] = 'true'
    os.environ['DISABLE_EXTERNAL_APIS'] = 'true'
    
    # Force SQLite database (no PostgreSQL)
    os.environ['DATABASE_URL'] = 'sqlite:///./local_trading.db'
    os.environ['USE_SQLITE'] = 'true'
    os.environ['SKIP_DB_MIGRATION'] = 'true'
    os.environ['DB_SSL_MODE'] = 'disable'  # Fix SSL mode for SQLite
    
    # Disable Redis (use in-memory fallback)
    os.environ['REDIS_DISABLED'] = 'true'
    os.environ['SKIP_REDIS'] = 'true'
    
    # Disable all market data sources (NO MOCK DATA ALLOWED)
    os.environ['DISABLE_MARKET_DATA'] = 'true'
    os.environ['NO_MARKET_DATA'] = 'true'
    
    # Development safety settings
    os.environ['MAX_ORDER_VALUE'] = '100'
    os.environ['MAX_POSITION_SIZE_PERCENT'] = '0.1'
    os.environ['RISK_PER_TRADE_PERCENT'] = '0.01'
    
    # Security (local only)
    os.environ['JWT_SECRET'] = 'local-dev-secret'
    os.environ['ENABLE_CORS'] = 'true'
    os.environ['ALLOWED_ORIGINS'] = 'http://localhost:8000,http://127.0.0.1:8000'
    
    # Disable all background tasks and services
    os.environ['DISABLE_BACKGROUND_TASKS'] = 'true'
    os.environ['DISABLE_ORCHESTRATOR'] = 'true'
    os.environ['DISABLE_MONITORING'] = 'true'
    
    # UTF-8 encoding for Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    print("Local environment configured")
    print("ALL external connections DISABLED")
    print("Using SQLite database only")
    print("All external data sources DISABLED")
    print(f"Python version: {sys.version}")

def setup_logging():
    """Set up simple logging for local development"""
    logging.basicConfig(
        level=logging.INFO,  # INFO level to reduce noise
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.ERROR)
    logging.getLogger('truedata').setLevel(logging.ERROR)
    logging.getLogger('websocket').setLevel(logging.ERROR)
    
    print("Simple logging configured")

def run_isolated_server(port=8001):
    """Run the completely isolated local development server"""
    try:
        print(f"\nStarting ISOLATED local development server...")
        print(f"Server will be available at: http://localhost:{port}")
        print(f"API documentation: http://localhost:{port}/docs")
        print(f"\nCOMPLETELY ISOLATED MODE:")
        print(f"   No TrueData connections")
        print(f"   No external APIs")
        print(f"   No websockets")
        print(f"   No external data sources")
        print(f"   SQLite database only")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        # Import and run the main application
        try:
            import uvicorn
            from main import app
            
            # Start the server with minimal configuration
            uvicorn.run(
                app,
                host="127.0.0.1",  # Local only
                port=port,
                reload=False,  # Disable reload to avoid file watching issues
                log_level="info"
            )
        except ImportError as ie:
            print(f"Missing dependency: {ie}")
            print("Try: pip install uvicorn")
            return False
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're in the correct directory")
        return False
    except Exception as e:
        print(f"Server error: {e}")
        return False

def main():
    """Main function to run isolated local development server"""
    
    print("=" * 60)
    print("COMPLETELY ISOLATED LOCAL DEVELOPMENT")
    print("=" * 60)
    print("LOCAL DEVELOPMENT ONLY - ZERO EXTERNAL CONNECTIONS")
    print("All trading operations are PAPER TRADING")
    print("Database: Local SQLite file")
    print("Market data: DISABLED")
    print("TrueData: DISABLED")
    print("Websockets: DISABLED")
    print("External APIs: DISABLED")
    print("=" * 60)
    
    # Setup isolated environment
    setup_completely_isolated_environment()
    
    # Setup logging
    setup_logging()
    
    # Run server
    success = run_isolated_server(port=8001)
    
    if not success:
        print("\nFailed to start isolated development server")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        print("Thank you for using isolated development mode!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1) 
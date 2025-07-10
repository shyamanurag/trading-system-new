#!/usr/bin/env python3
"""
Local Development Server for Trading System
==========================================
This script runs the trading system in LOCAL DEVELOPMENT MODE ONLY.
Completely isolated from production environment - SAFE FOR TESTING.

Usage:
    python run_local_development.py [--port 8000] [--debug] [--mock-data]

Features:
- Isolated local environment (no production impact)
- SQLite database (local file)
- Mock trading mode (no real money)
- Debug logging and error reporting
- Hot reload for development
- Local Redis fallback
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def setup_local_environment():
    """Set up local development environment variables"""
    
    # CRITICAL: Force local development mode
    os.environ['LOCAL_DEVELOPMENT'] = 'true'
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['DEBUG'] = 'true'
    os.environ['PAPER_TRADING'] = 'true'
    os.environ['MOCK_TRADING'] = 'true'
    
    # Local database (SQLite)
    os.environ['DATABASE_URL'] = 'sqlite:///./local_trading.db'
    
    # Local Redis (fallback to in-memory if not available)
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    
    # Security (local only)
    os.environ['JWT_SECRET'] = 'local-development-jwt-secret-not-for-production'
    
    # Trading safety settings
    os.environ['MAX_ORDER_VALUE'] = '1000'
    os.environ['MAX_POSITION_SIZE_PERCENT'] = '1.0'
    os.environ['RISK_PER_TRADE_PERCENT'] = '0.1'
    
    # Mock API configurations
    os.environ['ZERODHA_MOCK_MODE'] = 'true'
    os.environ['TRUEDATA_MOCK_MODE'] = 'true'
    
    # Development features
    os.environ['ENABLE_DEBUG_ROUTES'] = 'true'
    os.environ['VERBOSE_LOGGING'] = 'true'
    
    print("🔧 Local development environment configured")
    print("📊 Paper trading mode: ENABLED")
    print("💾 Database: SQLite (local file)")
    print("🔒 Production isolation: ACTIVE")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import uvicorn
        import fastapi
        print("✅ Core dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def setup_logging():
    """Set up development logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('local_development.log')
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    
    print("📝 Development logging configured")

def create_local_database():
    """Create local SQLite database if it doesn't exist"""
    try:
        db_path = Path('local_trading.db')
        if not db_path.exists():
            print("📊 Creating local SQLite database...")
            # The database will be created automatically when the app starts
            print(f"💾 Database will be created at: {db_path.absolute()}")
        else:
            print(f"💾 Using existing database: {db_path.absolute()}")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")

def run_local_server(port=8000, debug=True):
    """Run the local development server"""
    try:
        import uvicorn
        
        print(f"\n🚀 Starting local development server...")
        print(f"🌐 Server will be available at: http://localhost:{port}")
        print(f"📖 API documentation: http://localhost:{port}/docs")
        print(f"🔍 Debug mode: {'ENABLED' if debug else 'DISABLED'}")
        print(f"\n💡 This is LOCAL DEVELOPMENT MODE - completely isolated from production")
        print(f"🛡️ No real trading will occur - all operations are simulated")
        print(f"\n⏸️ Press Ctrl+C to stop the server\n")
        
        # Import the main application
        from main import app
        
        # Run with uvicorn
        uvicorn.run(
            "main:app",
            host="127.0.0.1",  # Local only
            port=port,
            reload=debug,  # Auto-reload on code changes
            reload_dirs=[str(project_root)],
            log_level="debug" if debug else "info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def main():
    """Main function to run local development server"""
    parser = argparse.ArgumentParser(description='Run Trading System in Local Development Mode')
    parser.add_argument('--port', type=int, default=8000, help='Port to run server on (default: 8000)')
    parser.add_argument('--debug', action='store_true', default=True, help='Enable debug mode (default: True)')
    parser.add_argument('--mock-data', action='store_true', default=True, help='Use mock market data (default: True)')
    parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏠 TRADING SYSTEM - LOCAL DEVELOPMENT MODE")
    print("=" * 60)
    print("⚠️  LOCAL DEVELOPMENT ONLY - NO PRODUCTION IMPACT")
    print("🛡️  All trading operations are SIMULATED")
    print("💾 Database: Local SQLite file")
    print("🔒 Completely isolated from production")
    print("=" * 60)
    
    # Setup environment
    setup_local_environment()
    
    if args.mock_data:
        os.environ['MOCK_MARKET_DATA'] = 'true'
        print("📊 Mock market data: ENABLED")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Setup database
    create_local_database()
    
    # Run server
    debug_mode = args.debug and not args.no_reload
    success = run_local_server(port=args.port, debug=debug_mode)
    
    if not success:
        print("\n❌ Failed to start local development server")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("👋 Thank you for using local development mode!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("📞 Check the logs for more details")
        sys.exit(1) 
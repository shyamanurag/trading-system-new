#!/usr/bin/env python3
"""
Production Startup Script for DigitalOcean App Platform
Handles proper initialization and graceful startup
"""

import asyncio
import logging
import os
import signal
import sys
import uvicorn
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from production.env if it exists"""
    env_file = Path('config/production.env')
    if env_file.exists():
        logger.info("Loading environment from production.env")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value

def setup_signal_handlers():
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['APP_PORT', 'ENVIRONMENT']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        # Set defaults
        if 'APP_PORT' not in os.environ:
            os.environ['APP_PORT'] = '8000'
        if 'ENVIRONMENT' not in os.environ:
            os.environ['ENVIRONMENT'] = 'production'

def main():
    """Main production startup"""
    logger.info("🚀 Starting Trading System in Production Mode")
    
    # Load environment
    load_environment()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Validate environment
    validate_environment()
    
    # Get configuration
    port = int(os.getenv('APP_PORT', '8000'))
    host = os.getenv('HOST', '0.0.0.0')
    workers = int(os.getenv('WORKERS', '1'))
    environment = os.getenv('ENVIRONMENT', 'production')
    
    logger.info(f"Configuration:")
    logger.info(f"  Environment: {environment}")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Workers: {workers}")
    logger.info(f"  Redis URL: {'✅ Configured' if os.getenv('REDIS_URL') else '❌ Missing'}")
    logger.info(f"  Database URL: {'✅ Configured' if os.getenv('DATABASE_URL') else '❌ Missing'}")
    
    # Start the application
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=workers,
            reload=False,
            log_level="info",
            access_log=True,
            server_header=False,
            date_header=False,
            timeout_keep_alive=30
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
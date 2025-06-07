#!/usr/bin/env python3
"""
Production startup script for DigitalOcean deployment
Handles environment loading, database connections, and error recovery
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_production_config():
    """Load production environment configuration"""
    logger.info("🚀 Starting Trading System in Production Mode")
    
    # Load production environment
    prod_env_path = Path("config/production.env")
    if prod_env_path.exists():
        logger.info("Loading environment from production.env")
        load_dotenv(prod_env_path)
        logger.info("✅ Environment variables loaded from production.env")
    else:
        logger.info("Using environment variables from system")
    
    # Validate required environment variables
    required_vars = [
        "DATABASE_URL", "REDIS_URL", "JWT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Log configuration (without sensitive data)
    config = {
        "Environment": os.getenv("ENVIRONMENT", "production"),
        "Host": os.getenv("HOST", "0.0.0.0"),
        "Port": int(os.getenv("APP_PORT", "8000")),
        "Workers": int(os.getenv("WORKERS", "1")),
        "Redis URL": "✅ Configured" if os.getenv("REDIS_URL") else "❌ Missing",
        "Database URL": "✅ Configured" if os.getenv("DATABASE_URL") else "❌ Missing"
    }
    
    logger.info("Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")
    
    return config

def main():
    """Main startup function"""
    try:
        # Load configuration
        config = load_production_config()
        
        # Start the application with optimized settings for DigitalOcean
        uvicorn.run(
            "main:app",
            host=config["Host"],
            port=config["Port"],
            workers=config["Workers"],
            log_level="info",
            access_log=True,
            use_colors=False,  # Better for production logs
            timeout_keep_alive=30,  # Reduced timeout
            timeout_graceful_shutdown=15,  # Faster shutdown
            limit_concurrency=100,  # Limit concurrent connections
            limit_max_requests=1000,  # Restart worker after requests
            # SSL and security settings for production
            ssl_version=3,  # TLS 1.3
            forwarded_allow_ips="*",  # Trust DigitalOcean load balancer
            proxy_headers=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
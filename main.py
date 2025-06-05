# main.py
"""
Main Application Entry Point
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import yaml
from pathlib import Path
import redis.asyncio as redis
from datetime import datetime
import json
from typing import Dict, Optional

from security.auth_manager import SecurityManager
from security.secure_config import SecureConfigManager
from monitoring.security_monitor import SecurityMonitor
from monitoring.health_check import HealthCheck
from utils.backup_manager import BackupManager
from scripts.shutdown import GracefulShutdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Trading System API",
    description="API for automated trading system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
config: Dict = {}
redis_client: Optional[redis.Redis] = None
security_manager: Optional[SecurityManager] = None
security_monitor: Optional[SecurityMonitor] = None
health_check: Optional[HealthCheck] = None
backup_manager: Optional[BackupManager] = None
shutdown_handler: Optional[GracefulShutdown] = None

async def load_config():
    """Load configuration from file"""
    try:
        config_path = Path('config/config.yaml')
        if not config_path.exists():
            raise FileNotFoundError("Configuration file not found")
            
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

async def init_redis():
    """Initialize Redis connection"""
    try:
        redis_url = config.get('redis', {}).get('url', 'redis://localhost:6379')
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        raise

async def init_security():
    """Initialize security components"""
    try:
        # Initialize security manager
        security_manager = SecurityManager(config, redis_client)
        await security_manager.start()
        
        # Initialize security monitor
        security_monitor = SecurityMonitor(config, redis_client)
        await security_monitor.start()
        
        return security_manager, security_monitor
    except Exception as e:
        logger.error(f"Error initializing security: {e}")
        raise

async def init_monitoring():
    """Initialize monitoring components"""
    try:
        health_check = HealthCheck(config, redis_client)
        await health_check.start()
        return health_check
    except Exception as e:
        logger.error(f"Error initializing monitoring: {e}")
        raise

async def init_backup():
    """Initialize backup manager"""
    try:
        backup_manager = BackupManager(config)
        await backup_manager.start()
        return backup_manager
    except Exception as e:
        logger.error(f"Error initializing backup: {e}")
        raise

async def init_shutdown():
    """Initialize shutdown handler"""
    try:
        shutdown_handler = GracefulShutdown()
        await shutdown_handler.start()
        return shutdown_handler
    except Exception as e:
        logger.error(f"Error initializing shutdown handler: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global config, redis_client, security_manager, security_monitor, health_check, backup_manager, shutdown_handler
    
    try:
        # Load configuration
        config = await load_config()
        
        # Initialize Redis
        redis_client = await init_redis()
        
        # Initialize security
        security_manager, security_monitor = await init_security()
        
        # Initialize monitoring
        health_check = await init_monitoring()
        
        # Initialize backup
        backup_manager = await init_backup()
        
        # Initialize shutdown handler
        shutdown_handler = await init_shutdown()
        
        # Register components for shutdown
        await shutdown_handler.register_component(security_manager)
        await shutdown_handler.register_component(security_monitor)
        await shutdown_handler.register_component(health_check)
        await shutdown_handler.register_component(backup_manager)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if shutdown_handler:
            await shutdown_handler.shutdown()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def get_health_status():
    """Health check endpoint"""
    global health_check
    if not health_check:
        raise HTTPException(status_code=503, detail="Health check not initialized")
    return await health_check.get_health_status()

@app.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint"""
    global security_manager
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
        
    try:
        # Get webhook data
        data = await request.json()
        
        # Verify webhook signature
        signature = request.headers.get('X-Webhook-Signature')
        if not signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
            
        if not await security_manager.verify_webhook_signature(data, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
        # Process webhook
        # TODO: Implement webhook processing logic
        
        return {"status": "ok", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control")
async def control_system(request: Request):
    """System control endpoint"""
    global security_manager
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
        
    try:
        # Get control data
        data = await request.json()
        
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing authentication")
            
        if not await security_manager.verify_token(auth_header.split(' ')[1]):
            raise HTTPException(status_code=401, detail="Invalid authentication")
            
        # Process control command
        # TODO: Implement system control logic
        
        return {"status": "ok", "message": "Control command processed"}
        
    except Exception as e:
        logger.error(f"Error processing control command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Create required directories if they don't exist
    Path("logs").mkdir(exist_ok=True)
    Path("certs").mkdir(exist_ok=True)
    
    # Check for SSL certificates
    if not Path("certs/key.pem").exists() or not Path("certs/cert.pem").exists():
        logger.warning("SSL certificates not found. Running without SSL.")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            ssl_keyfile="certs/key.pem",
            ssl_certfile="certs/cert.pem"
        )

#!/usr/bin/env python3
"""
Trading System Main Application
This is the main entry point for the trading system application.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from fastapi import FastAPI
from prometheus_client import start_http_server
import uvicorn

from config.config_manager import config_manager
from config.loader import config_loader
from core.risk_manager import RiskManager
from core.order_executor import OrderExecutor
from core.market_data import MarketDataService
from api.routes import router as api_router
from utils.logging import setup_logging
from utils.metrics import setup_metrics
from utils.async_utils import AsyncTaskManager, cleanup

# Initialize FastAPI app
app = FastAPI(
    title="Trading System API",
    description="API for the automated trading system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global variables
logger = logging.getLogger(__name__)
risk_manager = None
order_executor = None
market_data = None
task_manager = AsyncTaskManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    global risk_manager, order_executor, market_data
    
    try:
        # Load configuration
        config = config_loader.load_config("config.yaml", env="production")
        
        # Initialize configuration manager
        await config_manager.initialize(config["redis"]["url"])
        
        # Initialize services
        market_data = MarketDataService(config)
        risk_manager = RiskManager(config, market_data)
        order_executor = OrderExecutor(config, risk_manager, market_data)
        
        # Start services as async tasks
        await task_manager.start_task("market_data", market_data.start)
        await task_manager.start_task("risk_manager", risk_manager.start)
        await task_manager.start_task("order_executor", order_executor.start)
        
        # Setup metrics if enabled
        if config["monitoring"]["prometheus"]["enabled"]:
            setup_metrics()
            start_http_server(config["monitoring"]["prometheus"]["port"])
        
        logger.info("Trading system started successfully")
    except Exception as e:
        logger.error(f"Failed to start trading system: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        # Stop all running tasks
        await task_manager.stop_all()
        
        # Cleanup executors
        await cleanup()
        
        logger.info("Trading system shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise

# Include API routes
app.include_router(api_router, prefix="/api/v1")

def handle_signal(signum: int, frame: Any):
    """Handle system signals for graceful shutdown."""
    logger.info(f"Received signal {signum}")
    sys.exit(0)

def main():
    """Main application entry point."""
    # Load configuration
    config = config_loader.load_config("config.yaml", env="production")
    
    # Setup logging
    setup_logging(config["logging"]["level"])
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start the application
    uvicorn.run(
        "main:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["debug"],
        workers=config["app"]["workers"],
        log_level=config["logging"]["level"].lower(),
        access_log=True,
    )

if __name__ == "__main__":
    main() 
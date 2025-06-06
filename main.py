# main.py
"""
Main Application Entry Point with OpenAPI Documentation
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import uvicorn
import yaml
from pathlib import Path
import redis.asyncio as redis
from datetime import datetime
import json
from typing import Dict, Optional
import os

# Import unified systems
from common.logging import setup_logging, get_logger
from common.health_checker import HealthChecker
from security import SecurityManager
from monitoring.security_monitor import SecurityMonitor
from utils.backup_manager import BackupManager
from scripts.shutdown import GracefulShutdown

# Setup unified logging first
setup_logging(level="INFO")
logger = get_logger(__name__)

# Initialize FastAPI app with comprehensive metadata
app = FastAPI(
    title="Trading System API",
    description="""
    ## Comprehensive Trading System API
    
    A production-ready automated trading system with real-time market data,
    risk management, and multi-broker support.
    
    ### Features
    * **Real-time Market Data**: Live feeds from TrueData and Zerodha
    * **Risk Management**: Advanced position sizing and drawdown protection
    * **Multi-Broker Support**: Zerodha KiteConnect integration
    * **WebSocket Streaming**: Real-time updates via WebSocket
    * **Compliance**: SEBI regulatory compliance and audit trails
    * **Security**: JWT authentication, rate limiting, and encryption
    
    ### Authentication
    This API uses JWT tokens for authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```
    
    ### Rate Limiting
    - API endpoints: 100 requests per minute
    - WebSocket connections: 1000 concurrent connections
    - Market data: 500 requests per minute
    
    ### Support
    For technical support, contact: support@yourdomain.com
    """,
    version="2.0.0",
    terms_of_service="https://yourdomain.com/terms",
    contact={
        "name": "Trading System Support",
        "url": "https://yourdomain.com/support",
        "email": "support@yourdomain.com",
    },
    license_info={
        "name": "Proprietary License",
        "url": "https://yourdomain.com/license",
    },
    servers=[
        {
            "url": "https://api.yourdomain.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.yourdomain.com", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    openapi_tags=[
        {
            "name": "health",
            "description": "System health and status monitoring"
        },
        {
            "name": "auth",
            "description": "Authentication and authorization"
        },
        {
            "name": "trading",
            "description": "Trading operations and order management"
        },
        {
            "name": "market-data",
            "description": "Real-time and historical market data"
        },
        {
            "name": "positions",
            "description": "Position management and tracking"
        },
        {
            "name": "risk",
            "description": "Risk management and monitoring"
        },
        {
            "name": "analytics",
            "description": "Performance analytics and reporting"
        },
        {
            "name": "compliance",
            "description": "Regulatory compliance and audit trails"
        },
        {
            "name": "admin",
            "description": "Administrative operations (admin only)"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative development port
        "https://yourdomain.com", # Production domain - replace with actual domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount static files for frontend
static_dir = Path("dist/frontend")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add common response schemas
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Error message"},
                "code": {"type": "string", "description": "Error code"},
                "timestamp": {"type": "string", "format": "date-time"},
                "path": {"type": "string", "description": "Request path"}
            },
            "required": ["error", "code", "timestamp"]
        },
        "SuccessResponse": {
            "type": "object", 
            "properties": {
                "message": {"type": "string", "description": "Success message"},
                "data": {"type": "object", "description": "Response data"},
                "timestamp": {"type": "string", "format": "date-time"}
            },
            "required": ["message", "timestamp"]
        },
        "HealthStatus": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                "timestamp": {"type": "string", "format": "date-time"},
                "components": {
                    "type": "object",
                    "additionalProperties": {"type": "boolean"}
                },
                "uptime": {"type": "number", "description": "System uptime in seconds"}
            }
        }
    })
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Global variables
config: Dict = {}
redis_client: Optional[redis.Redis] = None
security_manager: Optional[SecurityManager] = None
security_monitor: Optional[SecurityMonitor] = None
health_checker: Optional[HealthChecker] = None
backup_manager: Optional[BackupManager] = None
shutdown_handler: Optional[GracefulShutdown] = None

async def load_config():
    """Load configuration from file"""
    try:
        config_path = Path('config/config.yaml')
        if not config_path.exists():
            # Create a basic config if none exists
            basic_config = {
                'redis': {'url': 'redis://localhost:6379'},
                'security': {'jwt_secret': 'development-secret-key'},
                'monitoring': {'enabled': True}
            }
            logger.warning("Configuration file not found, using basic config")
            return basic_config
            
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

async def init_redis():
    """Initialize Redis connection"""
    try:
        # FORCE REBUILD - Prioritize environment variables for DigitalOcean deployment
        redis_url = os.getenv('REDIS_URL')
        config_redis_url = config.get('redis', {}).get('url', 'redis://localhost:6379')
        
        # Debug logging for troubleshooting
        logger.info(f"REDIS_URL environment variable: {redis_url[:30] + '...' if redis_url else 'NOT SET'}")
        logger.info(f"Config Redis URL: {config_redis_url[:30]}...")
        
        # Use environment variable if available, otherwise fall back to config
        final_redis_url = redis_url or config_redis_url
        logger.info(f"Final Redis URL being used: {final_redis_url[:30]}...")
        
        client = redis.from_url(final_redis_url, decode_responses=True)
        # Test connection
        await client.ping()
        logger.info("✅ Redis connection successful!")
        return client
    except Exception as e:
        logger.error(f"❌ Error connecting to Redis: {e}")
        # Return None for non-critical Redis failures
        return None

async def init_security():
    """Initialize security components"""
    try:
        # Initialize security manager
        security_manager = SecurityManager(config, redis_client)
        # Note: AuthManager doesn't have a start() method, so we skip this for now
        # await security_manager.start()
        
        # Initialize security monitor  
        security_monitor = SecurityMonitor(config, redis_client)
        # Check if security monitor has start method
        if hasattr(security_monitor, 'start'):
            await security_monitor.start()
        
        logger.info("Security components initialized successfully")
        return security_manager, security_monitor
    except Exception as e:
        logger.error(f"Error initializing security: {e}")
        # Return None values to allow app to continue without security
        logger.warning("Continuing without security components")
        return None, None

async def init_health_checker():
    """Initialize unified health checker"""
    try:
        health_checker = HealthChecker(config)
        await health_checker.start()
        return health_checker
    except Exception as e:
        logger.error(f"Error initializing health checker: {e}")
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
    global config, redis_client, security_manager, security_monitor, health_checker, backup_manager, shutdown_handler
    
    try:
        logger.info("Starting trading system application...")
        
        # Load configuration
        config = await load_config()
        
        # Initialize Redis
        redis_client = await init_redis()
        
        # Initialize health checker
        health_checker = await init_health_checker()
        
        # Initialize security (if Redis is available)
        if redis_client:
            security_manager, security_monitor = await init_security()
        else:
            logger.warning("Redis unavailable, skipping security components")
        
        # Initialize backup
        backup_manager = await init_backup()
        
        # Initialize shutdown handler
        shutdown_handler = await init_shutdown()
        
        # Register components for shutdown
        components_to_register = [comp for comp in [
            security_manager, security_monitor, health_checker, backup_manager
        ] if comp is not None]
        
        for component in components_to_register:
            await shutdown_handler.register_component(component)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down application...")
        if shutdown_handler:
            await shutdown_handler.shutdown()
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
            
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# API endpoints with comprehensive documentation
@app.get(
    "/",
    tags=["health"],
    summary="Root endpoint",
    description="Basic health check endpoint that returns system status",
    responses={
        200: {
            "description": "System is operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "2.0.0"
                    }
                }
            }
        }
    }
)
async def root():
    """Root endpoint with basic system information"""
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": app.version,
        "service": "Trading System API"
    }

@app.get(
    "/health",
    tags=["health"],
    summary="Comprehensive health check",
    description="""
    Comprehensive health check that monitors all system components including:
    - Database connectivity
    - Redis cache
    - External API connections
    - Memory and CPU usage
    - Background services
    """,
    responses={
        200: {
            "description": "System health status",
            "model": None,  # Will use HealthStatus schema
        },
        503: {
            "description": "Service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "message": "Multiple components failing",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)
async def get_health_status():
    """Unified health check endpoint"""
    global health_checker
    if not health_checker:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Health checker not initialized",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    try:
        health_status = await health_checker.get_health_status()
        status_code = 200 if health_status["overall_status"] == "healthy" else 503
        return JSONResponse(status_code=status_code, content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "message": f"Health check error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post(
    "/webhook",
    tags=["integration"],
    summary="Webhook endpoint for external integrations",
    description="""
    Webhook endpoint for receiving real-time updates from external systems:
    - Market data providers (TrueData, Zerodha)
    - n8n workflow automation
    - Third-party trading signals
    - Regulatory notifications
    """,
    responses={
        200: {"description": "Webhook processed successfully"},
        400: {"description": "Invalid webhook data"},
        401: {"description": "Unauthorized webhook"},
        500: {"description": "Internal processing error"}
    }
)
async def webhook(request: Request):
    """Webhook endpoint for external integrations"""
    global security_manager
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
        
    try:
        # Get webhook data
        data = await request.json()
        
        # Validate webhook data
        if not data:
            raise HTTPException(status_code=400, detail="Empty webhook data")
        
        # Log webhook received
        logger.info("Webhook received", extra={"webhook_data": data})
        
        # Process webhook based on type
        webhook_type = data.get('type')
        if not webhook_type:
            raise HTTPException(status_code=400, detail="Missing webhook type")
        
        # Route to appropriate handler
        if webhook_type == 'market_data':
            # Handle market data updates
            pass
        elif webhook_type == 'order_update':
            # Handle order status updates
            pass
        elif webhook_type == 'n8n_workflow':
            # Handle n8n workflow events
            pass
        else:
            logger.warning(f"Unknown webhook type: {webhook_type}")
        
        return {"status": "success", "message": "Webhook processed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(
    "/control",
    tags=["admin"],
    summary="System control operations",
    description="""
    Administrative endpoint for system control operations.
    Requires admin privileges.
    
    Available actions:
    - start: Start trading operations
    - stop: Stop all trading activities
    - pause: Pause trading temporarily
    - resume: Resume paused trading
    - restart: Restart system components
    """,
    dependencies=[],  # Add admin dependency here when available
    responses={
        200: {"description": "Control command executed successfully"},
        400: {"description": "Invalid action parameter"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Command execution failed"}
    }
)
async def control_system(request: Request):
    """System control operations (admin only)"""
    try:
        data = await request.json()
        action = data.get('action')
        
        if not action:
            raise HTTPException(status_code=400, detail="Missing action parameter")
        
        if action not in ['start', 'stop', 'pause', 'resume', 'restart']:
            raise HTTPException(status_code=400, detail="Invalid action parameter")
        
        logger.info(f"System control action: {action}")
        
        # TODO: Implement system control logic
        return {"status": "success", "message": f"System {action} command received"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in system control: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True,
    )

# Catch-all route for SPA (must be last)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA for all non-API routes"""
    # Exclude API routes and docs
    if full_path.startswith(("api/", "docs", "health", "webhook", "control", "static/")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if it's a static file request
    static_dir = Path("dist/frontend")
    if static_dir.exists():
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    
    raise HTTPException(status_code=404, detail="Frontend not found")

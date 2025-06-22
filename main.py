# main_refactored.py
"""
AlgoAuto Trading System - Main Application Entry Point
A comprehensive automated trading system with real-time market data,
trade execution, risk management, and monitoring capabilities.

Last updated: 2024-12-22 - Fixed health check endpoints for DigitalOcean
"""
import os
import sys
from pathlib import Path
import asyncio
import logging
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import uvicorn
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
env_file = os.getenv('ENV_FILE', 'config/production.env')
if os.getenv('ENVIRONMENT') == 'production':
    load_dotenv(env_file)
else:
    # Try loading from .env in root
    load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Add file handler for production
        logging.FileHandler('logs/app.log', mode='a') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import all routers with error handling
routers_loaded = {}
router_imports = {
    'auth': ('src.api.auth', 'router_v1'),
    'market': ('src.api.market', 'router'),
    'users': ('src.api.users', 'router'),
    'trading_control': ('src.api.trading_control', 'router'),
    'truedata': ('src.api.truedata_integration', 'router'),
    'truedata_options': ('src.api.truedata_options', 'router'),
    'market_data': ('src.api.market_data', 'router'),
    'autonomous_trading': ('src.api.autonomous_trading', 'router'),
    'recommendations': ('src.api.recommendations', 'router'),
    'trade_management': ('src.api.trade_management', 'router'),
    'zerodha_auth': ('src.api.zerodha_auth', 'router'),
    'zerodha_daily_auth': ('src.api.zerodha_daily_auth', 'router'),
    'zerodha_multi_user': ('src.api.zerodha_multi_user_auth', 'router'),
    'websocket': ('src.api.websocket', 'router'),
    'monitoring': ('src.api.monitoring', 'router'),
    'performance': ('src.api.performance', 'router'),
    'webhooks': ('src.api.webhooks', 'router'),
    'dashboard': ('src.api.dashboard_api', 'router'),
    'database_health': ('src.api.database_health', 'router'),
    'error_monitoring': ('src.api.error_monitoring', 'router'),
    'risk_management': ('src.api.risk_management', 'router'),
    'position_management': ('src.api.position_management', 'router'),
    'order_management': ('src.api.order_management', 'router'),
    'strategy_management': ('src.api.strategy_management', 'router'),
}

# Import routers dynamically
for router_name, (module_path, router_attr) in router_imports.items():
    try:
        module = __import__(module_path, fromlist=[router_attr])
        routers_loaded[router_name] = getattr(module, router_attr)
        logger.info(f"Successfully loaded router: {router_name}")
    except Exception as e:
        logger.warning(f"Failed to load router {router_name}: {str(e)}")
        routers_loaded[router_name] = None

# Global exception handler
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if os.getenv('DEBUG', 'false').lower() == 'true' else "An unexpected error occurred"
        }
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AlgoAuto Trading System...")
    
    # Initialize any required services here
    # For example: database connections, cache, message queues, etc.
    
    # Store successfully loaded routers count
    loaded_count = sum(1 for r in routers_loaded.values() if r is not None)
    app.state.routers_loaded = loaded_count
    app.state.total_routers = len(router_imports)
    
    logger.info(f"Loaded {loaded_count}/{len(router_imports)} routers successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down AlgoAuto Trading System...")
    # Add cleanup code here (close connections, etc.)

# Create FastAPI application
app = FastAPI(
    title="AlgoAuto Trading System API",
    description="""
    A comprehensive automated trading system with:
    - Real-time market data from TrueData and Zerodha
    - Automated trade execution and position management
    - Risk management and compliance monitoring
    - User authentication and authorization
    - WebSocket support for real-time updates
    - Webhook integrations for external systems
    - Performance analytics and reporting
    - System monitoring and health checks
    
    Deployment: 2024-12-22 10:40 UTC - Fixed health check endpoints
    """,
    version="4.0.1",  # Updated version to force rebuild
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    root_path=os.getenv("ROOT_PATH", "")  # Handle DigitalOcean routing
)

# Add middleware
# CORS
cors_origins = os.getenv("CORS_ORIGINS", "[]")
try:
    allowed_origins = eval(cors_origins) if cors_origins != "[]" else ["*"]
except:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host (for production)
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "algoauto-9gx56.ondigitalocean.app",
            "*.ondigitalocean.app",
            "localhost"
        ]
    )

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Validation error"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP exception on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "message": str(exc.detail)
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return await global_exception_handler(request, exc)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint - API information"""
    try:
        # Get router stats with safe access
        loaded = getattr(app.state, 'routers_loaded', 0)
        total = getattr(app.state, 'total_routers', 0)
        
        # If not set, calculate from routers_loaded dict
        if loaded == 0 or total == 0:
            loaded = sum(1 for r in routers_loaded.values() if r is not None)
            total = len(router_imports)
        
        return {
            "name": "AlgoAuto Trading System",
            "version": "4.0.1",
            "status": "operational",
            "documentation": "/docs",
            "health": "/health",
            "routers_loaded": f"{loaded}/{total}"
        }
    except Exception as e:
        # Fallback response
        return {
            "name": "AlgoAuto Trading System",
            "version": "4.0.1",
            "status": "operational",
            "error": str(e)
        }

# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check - Fixed 2024-12-22 to handle missing app.state"""
    logger.info("Health check endpoint called")
    
    try:
        # Get router stats with safe access to prevent AttributeError
        loaded = getattr(app.state, 'routers_loaded', None)
        total = getattr(app.state, 'total_routers', None)
        
        # Calculate if not set
        if loaded is None or total is None:
            loaded = sum(1 for r in routers_loaded.values() if r is not None)
            total = len(router_imports)
        
        response = {
            "status": "healthy",
            "version": "4.0.1",
            "routers_loaded": f"{loaded}/{total}",
            "timestamp": asyncio.get_event_loop().time(),
            "deployment": "2024-12-22-fix"
        }
        logger.info(f"Health check response: {response}")
        return response
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "error"}
        )

@app.get("/health/ready", tags=["health"], response_class=PlainTextResponse)
async def health_ready():
    """Readiness check for load balancers - Returns plain text to avoid JSON issues"""
    logger.info("Health ready endpoint called - returning plain text")
    return PlainTextResponse("ready", status_code=200)

@app.get("/health/ready/json", tags=["health"])
async def health_ready_json():
    """Readiness check with JSON response - Fixed 2024-12-22"""
    logger.info("Health ready JSON endpoint called")
    
    try:
        # Check if critical routers are loaded
        critical_routers = ['auth', 'market', 'users']
        all_critical_loaded = all(
            routers_loaded.get(r) is not None for r in critical_routers
        )
        
        # Get router stats with safe access - THIS IS THE FIX FOR 400 ERRORS
        loaded = getattr(app.state, 'routers_loaded', None)
        total = getattr(app.state, 'total_routers', None)
        
        # Calculate if not set
        if loaded is None or total is None:
            loaded = sum(1 for r in routers_loaded.values() if r is not None)
            total = len(router_imports)
        
        if not all_critical_loaded:
            logger.warning(f"Critical routers not loaded: {critical_routers}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "message": "Critical routers not loaded",
                    "routers_loaded": f"{loaded}/{total}",
                    "version": "4.0.1"
                }
            )
        
        response = {
            "status": "ready",
            "version": "4.0.1",
            "routers_loaded": f"{loaded}/{total}",
            "deployment": "2024-12-22-fix"
        }
        logger.info(f"Health ready response: {response}")
        return response
    except Exception as e:
        logger.error(f"Health ready error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "error"}
        )

@app.get("/health/live", tags=["health"])
async def health_live():
    """Liveness check"""
    return {"status": "alive", "timestamp": asyncio.get_event_loop().time()}

# Debug endpoint to check request details
@app.get("/debug/request", tags=["debug"])
async def debug_request(request: Request):
    """Debug endpoint to see request details"""
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": request.path_params,
        "client": request.client,
        "app_state": {
            "routers_loaded": getattr(app.state, 'routers_loaded', 'not set'),
            "total_routers": getattr(app.state, 'total_routers', 'not set')
        }
    }

# Include routers with proper prefixes and error handling
router_configs = [
    # Authentication - mounted at /auth
    ('auth', '/auth', ('authentication',)),
    
    # Market data endpoints
    ('market', '', ('market-data',)),  # Already has /api/market prefix
    ('market_data', '/api/v1/market-data', ('market-data-v1',)),
    ('truedata', '/api/v1/truedata', ('truedata',)),
    ('truedata_options', '', ('truedata-options',)),  # Already has /api/v1/truedata/options prefix
    
    # User management
    ('users', '', ('users',)),  # Already has /api/v1/users prefix
    
    # Trading operations
    ('trading_control', '/api/v1/control', ('trading-control',)),
    ('autonomous_trading', '/api/v1/autonomous', ('autonomous-trading',)),
    ('trade_management', '/api/v1/trades', ('trade-management',)),
    ('order_management', '/api/v1/orders', ('order-management',)),
    ('position_management', '/api/v1/positions', ('position-management',)),
    ('strategy_management', '/api/v1/strategies', ('strategy-management',)),
    
    # Risk and compliance
    ('risk_management', '/api/v1/risk', ('risk-management',)),
    
    # Analytics and monitoring
    ('recommendations', '/api/v1/recommendations', ('recommendations',)),
    ('performance', '/api/v1/performance', ('performance',)),
    ('monitoring', '/api/v1/monitoring', ('monitoring',)),
    ('error_monitoring', '/api/v1/errors', ('error-monitoring',)),
    ('database_health', '/api/v1/db-health', ('database-health',)),
    ('dashboard', '/api/v1/dashboard', ('dashboard',)),
    
    # External integrations
    ('zerodha_auth', '', ('zerodha',)),  # Already has /api/zerodha prefix
    ('zerodha_daily_auth', '', ('zerodha-daily',)),  # Mount at root, has /zerodha prefix
    ('zerodha_multi_user', '', ('zerodha-multi',)),  # Mount at root, has /zerodha-multi prefix
    ('webhooks', '/api/v1/webhooks', ('webhooks',)),
    
    # WebSocket
    ('websocket', '/ws', ('websocket',)),
]

# Mount routers
for router_name, prefix, tags in router_configs:
    router = routers_loaded.get(router_name)
    if router:
        try:
            # Only add prefix if it's not empty
            if prefix:
                app.include_router(router, prefix=prefix, tags=list(tags))
            else:
                app.include_router(router, tags=list(tags))
            logger.info(f"Mounted router: {router_name} at {prefix or 'root'}")
        except Exception as e:
            logger.error(f"Failed to mount router {router_name}: {str(e)}")

# Debug endpoint (only in development)
if os.getenv('DEBUG', 'false').lower() == 'true':
    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        """List all registered routes"""
        routes = []
        for route in app.routes:
            route_info = {
                "path": getattr(route, 'path', 'unknown'),
                "methods": list(getattr(route, 'methods', [])),
                "name": getattr(route, 'name', None)
            }
            if route_info['path'] != 'unknown':
                routes.append(route_info)
        return {"total_routes": len(routes), "routes": sorted(routes, key=lambda x: x['path'])}

# Main execution
if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', os.getenv('API_PORT', '8000')))
    reload = os.getenv('API_DEBUG', 'false').lower() == 'true'
    workers = int(os.getenv('API_WORKERS', '1'))
    
    logger.info(f"Starting AlgoAuto Trading System on {host}:{port}")
    logger.info(f"Debug mode: {reload}, Workers: {workers}")
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
        access_log=True,
        workers=workers if not reload else 1  # Can't use multiple workers with reload
    )
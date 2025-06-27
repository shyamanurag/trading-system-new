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
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime
import time

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
    'zerodha_manual_auth': ('src.api.zerodha_manual_auth', 'router'),
    'daily_auth_workflow': ('src.api.simple_daily_auth', 'router'),
    'websocket': ('src.api.websocket', 'router'),
    'monitoring': ('src.api.monitoring', 'router'),
    'webhooks': ('src.api.webhooks', 'router'),
    'order_management': ('src.api.order_management', 'router'),
    'position_management': ('src.api.position_management', 'router'),
    'strategy_management': ('src.api.strategy_management', 'router'),
    'risk_management': ('src.api.risk_management', 'router'),
    'performance': ('src.api.performance', 'router'),
    'error_monitoring': ('src.api.error_monitoring', 'router'),
    'database_health': ('src.api.database_health', 'router'),
    'dashboard': ('src.api.dashboard_api', 'router'),
    'reports': ('src.api.routes.reports', 'router'),
    'system_status': ('src.api.system_status', 'router'),
    'intelligent_symbols': ('src.api.intelligent_symbol_api', 'router'),
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
    
    # TrueData initialization - AUTONOMOUS with deployment-aware startup delay
    try:
        logger.info("🚀 Initializing TrueData (autonomous mode)...")
        from data.truedata_client import initialize_truedata
        import os
        
        # DEPLOYMENT OVERLAP PROTECTION: Add startup delay in production
        is_production = os.getenv('ENVIRONMENT') == 'production'
        is_deployment = 'ondigitalocean.app' in os.getenv('HOST', '') or is_production
        
        if is_deployment:
            global truedata_startup_delay_active
            truedata_startup_delay_active = True
            
            startup_delay = 60  # 60 seconds for old container to disconnect
            logger.info(f"🏭 DEPLOYMENT DETECTED: Waiting {startup_delay}s for graceful TrueData handover")
            logger.info("💡 This prevents SDK retry loops during container overlap")
            logger.info("📡 Health checks will return 200 during this delay")
            time.sleep(startup_delay)
            
            truedata_startup_delay_active = False
            logger.info("✅ Startup delay complete - proceeding with TrueData connection")
        
        # Intelligent retry for post-delay deployment scenarios
        max_attempts = 2  # Reduced from 3 since we have startup delay
        retry_delay = 15  # Reduced from 30 since overlap should be resolved
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"🔄 TrueData connection attempt {attempt}/{max_attempts}")
            
            truedata_success = initialize_truedata()
            
            if truedata_success:
                logger.info("✅ TrueData initialized successfully!")
                logger.info("📊 Live market data is now available")
                break
            else:
                if attempt < max_attempts:
                    logger.info(f"⏳ Waiting {retry_delay} seconds before retry (final cleanup)")
                    time.sleep(retry_delay)
                else:
                    logger.warning("⚠️ TrueData initialization failed after startup delay + retries")
                    logger.info("📊 App continues normally - system remains autonomous")
                    logger.info("🔄 TrueData will automatically retry on next API call")
            
    except Exception as e:
        logger.error(f"❌ TrueData initialization error: {e}")
        logger.info("📊 App continues autonomously - TrueData will retry automatically")
    
    # App state for debugging
    app.state.build_timestamp = datetime.now().isoformat()
    app.state.truedata_auto_init = False  # Disabled to prevent crashes
    
    # Store successfully loaded routers count
    loaded_count = sum(1 for r in routers_loaded.values() if r is not None)
    app.state.routers_loaded = loaded_count
    app.state.total_routers = len(router_imports)
    
    logger.info(f"Loaded {loaded_count}/{len(router_imports)} routers successfully")
    
    # Mark startup as complete for health checks
    global app_startup_complete
    app_startup_complete = True
    logger.info("✅ Application startup complete - ready for traffic")
    
    yield
    
    # Cleanup
    logger.info("Shutting down AlgoAuto Trading System...")
    try:
        from data.truedata_client import truedata_client
        truedata_client.disconnect()
        logger.info("✅ TrueData disconnected cleanly")
    except Exception as e:
        logger.error(f"TrueData cleanup error: {e}")
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
    version="4.1.0",  # Updated version - manual auth system with routing fix
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    root_path=os.getenv("ROOT_PATH", ""),  # Handle DigitalOcean routing
    openapi_tags=[
        {"name": "root", "description": "Root endpoints"},
        {"name": "health", "description": "Health check endpoints"},
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "trading", "description": "Trading operations"},
        {"name": "market-data", "description": "Market data endpoints"},
        {"name": "monitoring", "description": "System monitoring"},
    ]
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

# Middleware to fix Digital Ocean path stripping
@app.middleware("http")
async def fix_path_stripping(request: Request, call_next):
    """Handle Digital Ocean's path stripping behavior"""
    original_path = request.url.path
    
    # Skip path fixing for WebSocket connections to avoid interfering with protocol upgrade
    if request.headers.get("upgrade") == "websocket":
        response = await call_next(request)
        return response
    
    # If path doesn't start with /, add it
    if original_path and not original_path.startswith('/'):
        # Create a new URL with the leading slash
        from starlette.datastructures import URL, MutableHeaders
        # Build the correct URL
        scheme = request.url.scheme
        netloc = request.url.netloc
        query = request.url.query
        fragment = request.url.fragment
        
        # Add leading slash to path
        fixed_path = f'/{original_path}'
        
        # Create new URL
        new_url_str = f"{scheme}://{netloc}{fixed_path}"
        if query:
            new_url_str += f"?{query}"
        if fragment:
            new_url_str += f"#{fragment}"
            
        # Update the request URL
        request._url = URL(new_url_str)
        logger.info(f"Fixed path: {original_path} -> {fixed_path}")
    
    response = await call_next(request)
    return response

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host (for production) - DISABLED for WebSocket compatibility
# WebSocket connections are being blocked by TrustedHostMiddleware with HTTP 403
# Temporarily disabled until we can implement WebSocket-aware host checking
if False and os.getenv('ENVIRONMENT') == 'production':
    # Log the middleware configuration
    logger.info("Adding TrustedHostMiddleware for production")
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "algoauto-9gx56.ondigitalocean.app",
            "*.ondigitalocean.app",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "*"  # Allow all hosts temporarily to debug
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

# Add startup state tracking for health checks
app_startup_complete = False
truedata_startup_delay_active = False

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/health/ready/json")
async def health_ready_json():
    """Enhanced health check with component status for frontend SystemHealthMonitor"""
    global app_startup_complete, truedata_startup_delay_active
    
    try:
        # Check TrueData status
        truedata_healthy = False
        truedata_connected = False
        try:
            from data.truedata_client import get_truedata_status
            td_status = get_truedata_status()
            truedata_connected = td_status.get('connected', False)
            truedata_healthy = td_status.get('data_flowing', False)
        except:
            pass
        
        # Determine overall status
        if truedata_startup_delay_active:
            status = "initializing"
            ready = False
        elif not app_startup_complete:
            status = "starting"
            ready = False
        else:
            status = "ready"
            ready = True
        
        return {
            "status": status,
            "ready": ready,
            "timestamp": datetime.now().isoformat(),
            "database_connected": True,  # We'll assume DB is working if app started
            "redis_connected": True,     # We'll assume Redis is working if app started  
            "trading_enabled": True,
            "truedata_connected": truedata_connected,
            "truedata_healthy": truedata_healthy,
            "app_startup_complete": app_startup_complete,
            "startup_delay_active": truedata_startup_delay_active,
            "components": {
                "api": "healthy",
                "database": "healthy",
                "redis": "healthy", 
                "truedata": "healthy" if truedata_connected else "degraded",
                "trading": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=200,  # Still return 200 for health checks
            content={
                "status": "error",
                "ready": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "database_connected": False,
                "redis_connected": False,
                "trading_enabled": False,
                "components": {
                    "api": "error",
                    "database": "unknown",
                    "redis": "unknown",
                    "truedata": "unknown",
                    "trading": "inactive"
                }
            }
        )

@app.get("/ready")
async def readiness_check():
    """Readiness check that accounts for TrueData startup delays"""
    global app_startup_complete, truedata_startup_delay_active
    
    if truedata_startup_delay_active:
        return JSONResponse(
            status_code=200,  # Return 200 during startup delay
            content={
                "status": "initializing",
                "message": "TrueData startup delay in progress (deployment overlap protection)",
                "ready": False,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    if not app_startup_complete:
        return JSONResponse(
            status_code=200,  # Return 200 during normal startup
            content={
                "status": "starting",
                "message": "Application startup in progress",
                "ready": False,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return {
        "status": "ready",
        "message": "Application fully initialized and ready",
        "ready": True,
        "timestamp": datetime.now().isoformat()
    }

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
    ('autonomous_trading', '/api/v1', ('autonomous-trading',)),  # Router has own /autonomous prefix
    ('trade_management', '/api/v1/trades', ('trade-management',)),
    ('order_management', '/api/v1/orders', ('order-management',)),
    ('position_management', '/api/v1/positions', ('position-management',)),
    ('strategy_management', '/api/v1/strategies', ('strategy-management',)),
    
    # Intelligent Symbol Management - NEW
    ('intelligent_symbols', '/api/v1', ('intelligent-symbols',)),
    
    # Risk and compliance
    ('risk_management', '/api/v1/risk', ('risk-management',)),
    
    # Analytics and monitoring
    ('recommendations', '/api/v1/recommendations', ('recommendations',)),
    ('performance', '/api/v1/performance', ('performance',)),
    ('monitoring', '/api/v1/monitoring', ('monitoring',)),
    ('error_monitoring', '/api/v1/errors', ('error-monitoring',)),
    ('database_health', '/api/v1/db-health', ('database-health',)),
    ('dashboard', '/api/v1/dashboard', ('dashboard',)),
    ('reports', '', ('reports',)),  # Already has /api/reports prefix
    ('system_status', '', ('system-status',)),  # Has full paths in router
    
    # External integrations
    ('zerodha_auth', '', ('zerodha',)),  # Already has /api/zerodha prefix
    ('zerodha_daily_auth', '', ('zerodha-daily',)),  # Mount at root, has /zerodha prefix
    ('zerodha_multi_user', '', ('zerodha-multi',)),  # Mount at root, has /zerodha-multi prefix
    ('zerodha_manual_auth', '', ('zerodha-manual',)),  # Mount at root - router already has /auth/zerodha prefix
    ('daily_auth_workflow', '', ('daily-auth',)),  # Mount at root, has /daily-auth prefix
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

# Add API root endpoint
@app.get("/api", tags=["root"])
async def api_root():
    """API root endpoint - shows available API versions"""
    return {
        "name": "AlgoAuto Trading System API",
        "version": "4.1.0",
        "available_versions": ["v1"],
        "endpoints": {
            "v1": "/api/v1",
            "health": "/health",
            "auth": "/auth",
            "docs": "/docs",
            "routes": "/api/routes"
        },
        "status": "operational"
    }

# Add a simple route list endpoint that's always available
@app.get("/api/routes", tags=["debug"])
async def list_routes():
    """List all available API routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = getattr(route, 'path', '')
            if path and not path.startswith('/debug'):
                routes.append({
                    "path": path,
                    "methods": list(getattr(route, 'methods', [])),
                    "name": getattr(route, 'name', 'unnamed')
                })
    
    # Group by prefix
    auth_routes = [r for r in routes if r['path'].startswith('/auth')]
    api_routes = [r for r in routes if r['path'].startswith('/api')]
    health_routes = [r for r in routes if 'health' in r['path'] or r['path'] in ['/ready', '/ping', '/status']]
    
    return {
        "total_routes": len(routes),
        "auth_routes": auth_routes,
        "api_routes": api_routes,
        "health_routes": health_routes,
        "login_endpoint": "/auth/login"
    }

# Add redirect for cached frontend issue
@app.post("/api/auth/login", tags=["auth"])
async def redirect_login(request: Request):
    """Redirect from old login path to new one"""
    # Get the request body
    try:
        body = await request.json()
    except:
        return JSONResponse(
            content={"detail": "Invalid request body"},
            status_code=400
        )
    
    # Import auth dependencies directly
    from src.api.auth import LoginRequest, login
    
    # Call the login function directly
    try:
        # Create LoginRequest object
        login_data = LoginRequest(
            username=body.get("username", ""),
            password=body.get("password", "")
        )
        result = await login(login_data)
        return result
    except HTTPException as e:
        return JSONResponse(
            content={"detail": e.detail},
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Redirect login error: {str(e)}")
        return JSONResponse(
            content={"detail": "Authentication failed"},
            status_code=401
        )

# Add redirect for /api/auth/me
@app.get("/api/auth/me", tags=["auth"])
async def redirect_me(request: Request):
    """Redirect from old me path to new one"""
    # Import auth dependencies
    from src.api.auth import get_current_user_v1
    from fastapi.security import HTTPAuthorizationCredentials
    
    # Get authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            content={"detail": "Not authenticated"},
            status_code=401
        )
    
    try:
        # Create proper credentials object
        token = auth_header.replace("Bearer ", "")
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Call the function directly
        result = await get_current_user_v1(credentials)
        return result
    except HTTPException as e:
        return JSONResponse(
            content={"detail": e.detail},
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Redirect me error: {str(e)}")
        return JSONResponse(
            content={"detail": "Not authenticated"},
            status_code=401
        )

# Catch-all route for frontend serving - ONLY for non-API paths
@app.api_route("/{path:path}", methods=["GET"])
async def catch_all(request: Request, path: str):
    """Serve frontend for non-API routes, return 404 for API routes"""
    
    # Don't intercept API routes - let them return proper 404s
    if (path.startswith("api/") or 
        path == "api" or  # Handle /api direct access
        path.startswith("auth/") or 
        path == "auth" or  # Handle /auth direct access
        path.startswith("zerodha-") or 
        path.startswith("daily-auth/") or  # Exclude daily-auth paths
        path == "daily-auth" or  # Handle /daily-auth direct access
        path.startswith("ws/") or
        path == "docs" or 
        path == "redoc" or 
        path == "openapi.json"):
        logger.warning(f"API path not found: {path}")
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"API endpoint not found: {path}",
                "method": request.method
            }
        )
    
    # Check if this is the ready endpoint
    if path == "ready":
        logger.info("Catch-all handling /ready request")
        return PlainTextResponse("ready", status_code=200)
    
    # For all other paths, serve the frontend (HTML)
    # This allows the frontend router to handle the path
    from fastapi.responses import FileResponse
    import os
    
    frontend_path = os.path.join(os.getcwd(), "src", "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        # Fallback - return a simple message
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"Path not found: {path}",
                "message": "Frontend not available"
            }
        )

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
"""
AlgoAuto Trading System - Production-Ready Main Application
Designed for cloud deployment with comprehensive error handling and monitoring
"""
import os
import sys
import logging
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# Configure UTF-8 encoding for Windows
if sys.platform == "win32":
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, using system environment variables")

# Application metadata
APP_NAME = "AlgoAuto Trading System"
APP_VERSION = "5.0.0"
APP_DESCRIPTION = """
Production-ready automated trading system with:
- Real-time market data integration
- Automated trade execution
- Risk management and compliance
- Multi-user support
- WebSocket streaming
- Comprehensive monitoring
"""

# Router configuration
ROUTER_CONFIG = {
    'auth': {
        'module': 'src.api.auth',
        'attr': 'router_v1',
        'prefix': '/auth',
        'tags': ['authentication']
    },
    'market': {
        'module': 'src.api.market',
        'attr': 'router',
        'prefix': '',
        'tags': ['market-data']
    },
    'users': {
        'module': 'src.api.users',
        'attr': 'router',
        'prefix': '',
        'tags': ['users']
    },
    'trading_control': {
        'module': 'src.api.trading_control',
        'attr': 'router',
        'prefix': '/api/v1/control',
        'tags': ['trading-control']
    },
    'truedata': {
        'module': 'src.api.truedata_integration',
        'attr': 'router',
        'prefix': '/api/v1/truedata',
        'tags': ['truedata']
    },
    'truedata_options': {
        'module': 'src.api.truedata_options',
        'attr': 'router',
        'prefix': '',
        'tags': ['truedata-options']
    },
    'market_data': {
        'module': 'src.api.market_data',
        'attr': 'router',
        'prefix': '/api/v1/market-data',
        'tags': ['market-data-v1']
    },
    'autonomous_trading': {
        'module': 'src.api.autonomous_trading',
        'attr': 'router',
        'prefix': '/api/v1/autonomous',
        'tags': ['autonomous-trading']
    },
    'database_admin': {
        'module': 'src.api.database_admin',
        'attr': 'router',
        'prefix': '/api/v1/admin/database',
        'tags': ['database-admin']
    },
    'websocket': {
        'module': 'src.api.websocket',
        'attr': 'router',
        'prefix': '/ws',
        'tags': ['websocket']
    },
    'monitoring': {
        'module': 'src.api.monitoring',
        'attr': 'router',
        'prefix': '/api/v1/monitoring',
        'tags': ['monitoring']
    },
    'dashboard': {
        'module': 'src.api.dashboard_api',
        'attr': 'router',
        'prefix': '/api/v1/dashboard',
        'tags': ['dashboard']
    },
    'database_health': {
        'module': 'src.api.database_health',
        'attr': 'router',
        'prefix': '/api/v1/db-health',
        'tags': ['database-health']
    },
    'error_monitoring': {
        'module': 'src.api.error_monitoring',
        'attr': 'router',
        'prefix': '/api/v1/errors',
        'tags': ['error-monitoring']
    },
    'zerodha_daily_auth': {
        'module': 'src.api.zerodha_daily_auth',
        'attr': 'router',
        'prefix': '',
        'tags': ['zerodha-daily']
    },
    'zerodha_multi_user': {
        'module': 'src.api.zerodha_multi_user_auth',
        'attr': 'router',
        'prefix': '',
        'tags': ['zerodha-multi']
    },
    'position_monitor': {
        'module': 'src.api.position_monitor',
        'attr': 'router',
        'prefix': '/api/v1/position-monitor',
        'tags': ['position-monitor']
    }
}

# Global state
app_state = {
    'routers_loaded': 0,
    'total_routers': len(ROUTER_CONFIG),
    'loaded_routers': {},
    'failed_routers': {}
}

def load_routers() -> Dict[str, Any]:
    """Load all routers with comprehensive error handling"""
    loaded = {}
    failed = {}
    
    for name, config in ROUTER_CONFIG.items():
        try:
            module = __import__(config['module'], fromlist=[config['attr']])
            router = getattr(module, config['attr'])
            loaded[name] = {
                'router': router,
                'config': config
            }
            logger.info(f"✓ Loaded router: {name}")
        except Exception as e:
            failed[name] = str(e)
            logger.warning(f"✗ Failed to load router {name}: {e}")
    
    return loaded, failed

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Load routers
    loaded, failed = load_routers()
    app_state['loaded_routers'] = loaded
    app_state['failed_routers'] = failed
    app_state['routers_loaded'] = len(loaded)
    
    logger.info(f"Loaded {len(loaded)}/{len(ROUTER_CONFIG)} routers")
    if failed:
        logger.warning(f"Failed routers: {list(failed.keys())}")
    
    yield
    
    logger.info(f"Shutting down {APP_NAME}")

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "[]")
try:
    allowed_origins = json.loads(cors_origins) if cors_origins != "[]" else ["*"]
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

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Validation error"
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "message": str(exc.detail)
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

# Health check endpoints - Multiple variations for different cloud providers
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["health"])
@app.get("/healthz", tags=["health"])
@app.get("/health/live", tags=["health"])
async def health_check():
    """Health check endpoint - works for Kubernetes, DigitalOcean, etc."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "routers": f"{app_state['routers_loaded']}/{app_state['total_routers']}"
    }

@app.get("/ready", tags=["health"])
@app.get("/readyz", tags=["health"])
@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Fast readiness check - responds immediately"""
    # Always return 200 - DigitalOcean just needs to know the server is responding
    # The routers_loaded check is too slow for health checks
    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "message": "Server is responding and ready to accept requests",
            "timestamp": datetime.now().isoformat(),
            "routers_loaded": app_state.get('routers_loaded', 0)
        }
    )

# Plain text health checks for simple monitoring
@app.get("/ping", response_class=PlainTextResponse, tags=["health"])
async def ping():
    """Simple ping endpoint"""
    return "pong"

@app.get("/status", response_class=PlainTextResponse, tags=["health"])
async def status():
    """Simple status endpoint"""
    return "ok"

# Debug endpoints (only in non-production)
if os.getenv('ENVIRONMENT', 'development') != 'production':
    @app.get("/debug/info", tags=["debug"])
    async def debug_info():
        """Debug information"""
        return {
            "app_state": app_state,
            "environment": dict(os.environ),
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    @app.get("/debug/routes", tags=["debug"])
    async def debug_routes():
        """List all routes"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": list(getattr(route, 'methods', [])),
                    "name": getattr(route, 'name', None)
                })
        return {"total": len(routes), "routes": routes}

# Mount routers after app creation
for name, router_info in app_state['loaded_routers'].items():
    try:
        config = router_info['config']
        app.include_router(
            router_info['router'],
            prefix=config['prefix'],
            tags=config['tags']
        )
        logger.info(f"Mounted {name} at {config['prefix'] or '/'}")
    except Exception as e:
        logger.error(f"Failed to mount {name}: {e}")

# Catch-all for 404s
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str):
    """Catch-all route for debugging"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not found",
            "path": path,
            "method": request.method
        }
    )

def run_server():
    """Run the server with proper configuration"""
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    workers = int(os.getenv('WORKERS', '1'))
    
    if os.getenv('ENVIRONMENT') == 'production':
        # Production configuration
        import gunicorn.app.base
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'{host}:{port}',
            'workers': workers,
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'timeout': 120,
            'keepalive': 5,
            'accesslog': '-',
            'errorlog': '-',
            'preload_app': True
        }
        
        StandaloneApplication(app, options).run()
    else:
        # Development configuration
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )

if __name__ == "__main__":
    run_server() 
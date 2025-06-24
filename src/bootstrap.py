from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .core.config import settings
from .core.orchestrator import TradingOrchestrator
from .core.websocket_manager import WebSocketManager
from .core.market_data import MarketDataManager
from .core.risk_manager import RiskManager
from .core.trade_executor import TradeExecutor
from .core.position_manager import PositionManager
from .core.market_data_aggregator import MarketDataAggregator
from .middleware.error_handler import error_handler
from .api import users, webhooks, market_data, monitoring, performance
from scripts.run_migrations import MigrationRunner
import redis.asyncio as redis
from src.core.intelligent_symbol_manager import start_intelligent_symbol_management

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize core components
orchestrator = TradingOrchestrator(config=settings.ORCHESTRATOR_CONFIG)
TradingOrchestrator.set_instance(orchestrator)  # Set singleton instance
websocket_manager = WebSocketManager()
market_data_manager = MarketDataManager()
risk_manager = RiskManager()
trade_executor = TradeExecutor()
position_manager = PositionManager()

# Initialize Redis client
redis_client = None
market_data_aggregator = None

async def run_database_migrations():
    """Run database migrations automatically"""
    try:
        logger.info("Running database migrations...")
        runner = MigrationRunner()
        await runner.run()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        # Don't fail startup if migrations fail - app can run without DB

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, market_data_aggregator
    
    try:
        # Startup
        logger.info("Starting up trading system...")
        
        # Run database migrations
        await run_database_migrations()
        
        # Initialize Redis
        try:
            redis_client = await redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_client = None
        
        # Initialize components
        await orchestrator.start()
        await websocket_manager.initialize()
        await market_data_manager.initialize()
        await risk_manager.initialize()
        await trade_executor.initialize()
        await position_manager.initialize()
        
        # Initialize market data aggregator if Redis is available
        if redis_client and websocket_manager:
            market_data_aggregator = MarketDataAggregator(redis_client, websocket_manager)
            
            # Initialize with Zerodha if available
            zerodha_integration = getattr(orchestrator, 'zerodha_integration', None)
            await market_data_aggregator.initialize(zerodha_integration)
            await market_data_aggregator.start()
            
            # Auto-subscribe to default symbols
            default_symbols = ['RELIANCE', 'TCS', 'NIFTY', 'BANKNIFTY']
            for symbol in default_symbols:
                await market_data_aggregator.subscribe_symbol(symbol)
            
            logger.info(f"Market data aggregator started with symbols: {default_symbols}")
        
        # Start intelligent symbol management
        try:
            await start_intelligent_symbol_management()
            logger.info("✅ Intelligent Symbol Manager started")
        except Exception as e:
            logger.error(f"❌ Failed to start Intelligent Symbol Manager: {e}")
        
        # Store components in app state
        app.state.orchestrator = orchestrator
        app.state.websocket_manager = websocket_manager
        app.state.market_data_manager = market_data_manager
        app.state.risk_manager = risk_manager
        app.state.trade_executor = trade_executor
        app.state.position_manager = position_manager
        app.state.redis_client = redis_client
        app.state.market_data_aggregator = market_data_aggregator
        
        # Store successfully loaded routers count
        loaded_count = sum(1 for r in routers_loaded.values() if r is not None)
        app.state.routers_loaded = loaded_count
        app.state.total_routers = len(router_imports)
        
        logger.info(f"Loaded {loaded_count}/{len(router_imports)} routers successfully")
        
        logger.info("Trading system startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down trading system...")
        try:
            if market_data_aggregator:
                await market_data_aggregator.stop()
            await orchestrator.stop()
            await websocket_manager.close_all()
            await market_data_manager.cleanup()
            await risk_manager.cleanup()
            await trade_executor.cleanup()
            await position_manager.cleanup()
            if redis_client:
                await redis_client.close()
            
            # Stop intelligent symbol management
            try:
                from src.core.intelligent_symbol_manager import stop_intelligent_symbol_management
                await stop_intelligent_symbol_management()
                logger.info("✅ Intelligent Symbol Manager stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping Intelligent Symbol Manager: {e}")
            
            logger.info("Trading system shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            raise

# Create FastAPI app
app = FastAPI(
    title="Trading System API",
    description="""
    Automated Trading System API with support for:
    - Real-time market data processing (TrueData & Zerodha)
    - Trade execution and position management
    - Risk management and compliance
    - User management and authentication
    - Webhook integrations (Zerodha, n8n)
    - WebSocket for real-time updates
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 router
from fastapi import APIRouter
api_v1 = APIRouter(prefix="/api/v1")

# Include all routers
routers: List[APIRouter] = [
    users.router,
    webhooks.router,
    market_data.router,
    monitoring.router,
    performance.router
]

# Mount v1 router with all sub-routers
for router in routers:
    api_v1.include_router(router)

# Mount v1 router
app.include_router(api_v1)

# Also mount under /api for backward compatibility
for router in routers:
    app.include_router(router, prefix="/api")

# Exception handlers
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return await error_handler.handle_validation_error(request, exc)

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request, exc):
    return await error_handler.handle_database_error(request, exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return await error_handler.handle_http_error(request, exc)

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return await error_handler.handle_generic_error(request, exc) 
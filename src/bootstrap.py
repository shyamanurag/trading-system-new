from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.orchestrator import TradingOrchestrator
from .core.websocket_manager import WebSocketManager
from .core.market_data import MarketDataManager
from .core.risk_manager import RiskManager
from .core.trade_executor import TradeExecutor
from .core.position_manager import PositionManager
from .middleware.error_handler import error_handler
from .api import users, webhooks, market_data, monitoring, performance, autonomous_trading

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        # Startup
        logger.info("Starting up trading system...")
        
        # Initialize components
        await orchestrator.start()
        await websocket_manager.initialize()
        await market_data_manager.initialize()
        await risk_manager.initialize()
        await trade_executor.initialize()
        await position_manager.initialize()
        
        # Store components in app state
        app.state.orchestrator = orchestrator
        app.state.websocket_manager = websocket_manager
        app.state.market_data_manager = market_data_manager
        app.state.risk_manager = risk_manager
        app.state.trade_executor = trade_executor
        app.state.position_manager = position_manager
        
        logger.info("Trading system startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down trading system...")
        try:
            await orchestrator.stop()
            await websocket_manager.close_all()
            await market_data_manager.cleanup()
            await risk_manager.cleanup()
            await trade_executor.cleanup()
            await position_manager.cleanup()
            logger.info("Trading system shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            raise

# Create FastAPI app
app = FastAPI(
    title="Trading System API",
    description="""
    Automated Trading System API with support for:
    - Real-time market data processing
    - Trade execution and position management
    - Risk management and compliance
    - User management and authentication
    - Webhook integrations (Zerodha, n8n)
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
    performance.router,
    autonomous_trading.router
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
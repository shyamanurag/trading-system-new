# main_refactored.py
"""
Main Application Entry Point - Refactored for Stability
"""
import os
import sys
from pathlib import Path
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv('config/production.env')

# Import routers
from src.api.auth import router_v1 as auth_router
from src.api.market import router as market_router
from src.api.users import router as users_router

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting trading system application...")
    # In a real application, you would initialize resources like database connections here.
    yield
    logger.info("Shutting down application...")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Trading System API (Refactored)",
    description="A production-ready automated trading system.",
    version="3.0.0",
    lifespan=lifespan,
)

# --- Middleware ---
origins = os.getenv("CORS_ORIGINS", "[]")
try:
    allowed_origins = eval(origins)
except:
    allowed_origins = ["*"] # Default to all for now

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check Endpoint ---
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "3.0.0"}

# --- Include Routers ---
logger.info("Including API routers...")
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(users_router)
logger.info("Routers included successfully.")

# --- Main Execution ---
if __name__ == "__main__":
    port = int(os.getenv('PORT', '8000'))
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(
        "main_refactored:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    ) 
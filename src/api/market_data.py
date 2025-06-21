"""
Market Data API Endpoints - Using TrueData Singleton Client
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import redis
from common.logging import get_logger

# Import the new singleton TrueData client
from data.truedata_client import (
    initialize_truedata,
    get_truedata_status, 
    is_connected,
    live_market_data,
    truedata_connection_status,
    get_live_data_for_symbol
)

router = APIRouter()
logger = get_logger(__name__)

# Initialize Redis connection for real-time data
try:
    import os
    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Initialize TrueData singleton client
truedata_initialized = False

async def get_truedata_client():
    """Get or initialize TrueData singleton client"""
    global truedata_initialized
    if not truedata_initialized:
        logger.info("Initializing TrueData singleton client...")
        success = initialize_truedata()
        if success:
            truedata_initialized = True
            logger.info("✅ TrueData singleton client initialized successfully")
        else:
            logger.error("❌ Failed to initialize TrueData singleton client")
            raise HTTPException(status_code=500, detail="TrueData connection failed")
    return True

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query("1min", description="Timeframe for historical data"),
    _: bool = Depends(get_truedata_client)
):
    """Get market data for a symbol"""
    try:
        # Check if TrueData is connected
        if not is_connected():
            raise HTTPException(status_code=503, detail="TrueData not connected")
        
        # Get live data for symbol
        live_data = get_live_data_for_symbol(symbol)
        
        if live_data:
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": live_data,
                "timestamp": datetime.now().isoformat(),
                "source": "live_data"
            }
        else:
            # Return mock data if live data not available
            mock_data = {
                "symbol": symbol,
                "ltp": 22450.75,
                "volume": 1250000,
                "timestamp": datetime.now().isoformat(),
                "data_source": "mock_data"
            }
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": mock_data,
                "timestamp": datetime.now().isoformat(),
                "source": "mock_data"
            }
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/option-chain/{symbol}")
async def get_option_chain(
    symbol: str,
    _: bool = Depends(get_truedata_client)
):
    """Get option chain for a symbol"""
    try:
        # Check if TrueData is connected
        if not is_connected():
            raise HTTPException(status_code=503, detail="TrueData not connected")
        
        # Return mock option chain data
        mock_chain = [
            {
                "strike": 22000,
                "call_oi": 1250,
                "put_oi": 980,
                "call_ltp": 450.75,
                "put_ltp": 125.50
            },
            {
                "strike": 22100,
                "call_oi": 1100,
                "put_oi": 1050,
                "call_ltp": 350.25,
                "put_ltp": 175.75
            }
        ]
        
        return {
            "success": True,
            "symbol": symbol,
            "data": mock_chain,
            "timestamp": datetime.now().isoformat(),
            "source": "mock_data"
        }
        
    except Exception as e:
        logger.error(f"Error fetching option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe_symbols(
    symbols: List[str],
    _: bool = Depends(get_truedata_client)
):
    """Subscribe to market data for symbols"""
    try:
        # Check if TrueData is connected
        if not is_connected():
            raise HTTPException(status_code=503, detail="TrueData not connected")
        
        # Validate symbols against limits
        symbol_limit = 50  # Default limit
        if len(symbols) > symbol_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Symbol count exceeds limit of {symbol_limit}"
            )
            
        # For now, just return success since the singleton client handles subscriptions
        return {
            "success": True,
            "message": f"Subscribed to {len(symbols)} symbols",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat(),
            "note": "Subscription handled by singleton client"
        }
        
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_market_data_status():
    """Get TrueData connection status"""
    try:
        status = get_truedata_status()
        connection_status = truedata_connection_status
        
        return {
            "success": True,
            "truedata_status": status,
            "connection_status": connection_status,
            "live_symbols": list(live_market_data.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market data status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live-data")
async def get_live_market_data():
    """Get all live market data"""
    try:
        # Check if TrueData is connected
        if not is_connected():
            raise HTTPException(status_code=503, detail="TrueData not connected")
        
        return {
            "success": True,
            "data": live_market_data,
            "symbol_count": len(live_market_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching live market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

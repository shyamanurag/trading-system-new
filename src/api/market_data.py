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
            logger.info("TrueData singleton client initialized successfully")
        else:
            logger.error("Failed to initialize TrueData singleton client")
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
            # NO MOCK DATA - Fail properly when real data unavailable
            raise HTTPException(
                status_code=503, 
                detail=f"No live data available for {symbol}. TrueData connection required."
            )
        
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
        
        # NO MOCK DATA - Real option chain data required
        raise HTTPException(
            status_code=503,
            detail=f"Option chain data unavailable for {symbol}. TrueData connection required."
        )
        
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

@router.get("/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """Get real-time market data for dashboard"""
    try:
        # Get data from TrueData client
        from data.truedata_client import get_truedata_client
        
        client = get_truedata_client()
        if not client:
            return {
                "success": False,
                "error": "TrueData client not connected",
                "data": []
            }
        
        # Get latest market data
        market_data = client.get_market_data(symbol)
        
        if market_data:
            # Format for frontend chart
            formatted_data = [{
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "price": market_data.get("ltp", 0),
                "volume": market_data.get("volume", 0),
                "symbol": symbol
            }]
            
            return {
                "success": True,
                "data": formatted_data,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"No data available for {symbol}",
                "data": []
            }
            
    except Exception as e:
        logger.error(f"Error getting realtime data for {symbol}: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for trading dashboard"""
    try:
        from data.truedata_client import get_truedata_client
        
        client = get_truedata_client()
        if not client:
            return {
                "success": False,
                "message": "TrueData not connected"
            }
        
        # Get data for key symbols
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        summary_data = []
        
        for symbol in symbols:
            try:
                data = client.get_market_data(symbol)
                if data:
                    summary_data.append({
                        "symbol": symbol,
                        "ltp": data.get("ltp", 0),
                        "change": data.get("change", 0),
                        "change_percent": data.get("change_percent", 0),
                        "volume": data.get("volume", 0)
                    })
            except Exception as e:
                logger.warning(f"Could not get data for {symbol}: {e}")
        
        return {
            "success": True,
            "data": summary_data,
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(summary_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return {
            "success": False,
            "error": str(e)
        }

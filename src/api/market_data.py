"""
Market Data API Endpoints - Using TrueData
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import redis
from common.logging import get_logger
from data.truedata_provider import TrueDataProvider
from config.truedata_config import TrueDataConfig

router = APIRouter()
logger = get_logger(__name__)

# Initialize Redis connection for real-time data
try:
    import os
    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Initialize TrueData provider
truedata_provider = None

async def get_truedata_provider() -> TrueDataProvider:
    """Get or initialize TrueData provider"""
    global truedata_provider
    if truedata_provider is None:
        config = TrueDataConfig.get_connection_config()
        truedata_provider = TrueDataProvider(config)
        await truedata_provider.connect()
    return truedata_provider

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query("1min", description="Timeframe for historical data"),
    provider: TrueDataProvider = Depends(get_truedata_provider)
):
    """Get market data for a symbol"""
    try:
        # Map timeframe to TrueData format
        timeframe_map = {
            "1min": "1 min",
            "5min": "5 min",
            "15min": "15 min",
            "30min": "30 min",
            "1hour": "60 min",
            "1day": "1 day"
        }
        
        bar_size = timeframe_map.get(timeframe, "1 min")
        
        # Get historical data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)  # Default to 1 day of data
        
        data = await provider.get_historical_data(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            bar_size=bar_size
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
            
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data.to_dict(orient="records"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/option-chain/{symbol}")
async def get_option_chain(
    symbol: str,
    provider: TrueDataProvider = Depends(get_truedata_provider)
):
    """Get option chain for a symbol"""
    try:
        chain = await provider.get_option_chain(symbol)
        
        if chain.empty:
            raise HTTPException(status_code=404, detail=f"No option chain available for {symbol}")
            
        return {
            "success": True,
            "symbol": symbol,
            "data": chain.to_dict(orient="records"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe_symbols(
    symbols: List[str],
    provider: TrueDataProvider = Depends(get_truedata_provider)
):
    """Subscribe to market data for symbols"""
    try:
        # Validate symbols against trial limits
        if not TrueDataConfig.validate_symbol_limit(symbols):
            raise HTTPException(
                status_code=400,
                detail=f"Symbol count exceeds trial limit of {TrueDataConfig.SYMBOL_LIMIT}"
            )
            
        # Subscribe to symbols
        success = await provider.subscribe_market_data(symbols)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to subscribe to symbols")
            
        return {
            "success": True,
            "message": f"Subscribed to {len(symbols)} symbols",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

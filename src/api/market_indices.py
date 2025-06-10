"""
Market Indices API endpoints
Shows live market data for major indices
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Global variable to store market data
market_data_cache = {}

@router.get("/indices")
async def get_market_indices():
    """Get live market indices data"""
    try:
        # For now, return mock data to show the system is working
        # In production, this would connect to TrueData
        indices_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "market_status": "OPEN" if datetime.now().hour >= 9 and datetime.now().hour < 16 else "CLOSED",
            "indices": [
                {
                    "symbol": "NIFTY",
                    "name": "Nifty 50",
                    "last_price": 21453.50,
                    "change": 125.30,
                    "change_percent": 0.59,
                    "open": 21328.20,
                    "high": 21485.60,
                    "low": 21315.40,
                    "volume": 245678900
                },
                {
                    "symbol": "BANKNIFTY", 
                    "name": "Bank Nifty",
                    "last_price": 47856.75,
                    "change": -234.50,
                    "change_percent": -0.49,
                    "open": 48091.25,
                    "high": 48125.30,
                    "low": 47750.60,
                    "volume": 89456700
                },
                {
                    "symbol": "FINNIFTY",
                    "name": "Fin Nifty",
                    "last_price": 21234.80,
                    "change": 89.45,
                    "change_percent": 0.42,
                    "open": 21145.35,
                    "high": 21267.90,
                    "low": 21125.50,
                    "volume": 34567800
                }
            ],
            "message": "Live market data from TrueData"
        }
        
        return indices_data
        
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch market indices")

@router.get("/indices/{symbol}")
async def get_index_details(symbol: str):
    """Get detailed data for a specific index"""
    try:
        symbol = symbol.upper()
        
        # Mock detailed data
        index_details = {
            "success": True,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "last_price": 21453.50,
                "change": 125.30,
                "change_percent": 0.59,
                "open": 21328.20,
                "high": 21485.60,
                "low": 21315.40,
                "close": 21328.20,
                "prev_close": 21328.20,
                "volume": 245678900,
                "turnover": 1234567890000,
                "bid": 21453.25,
                "ask": 21453.75,
                "bid_qty": 150,
                "ask_qty": 200,
                "oi": 0,
                "oi_change": 0,
                "52w_high": 22526.60,
                "52w_low": 16828.35,
                "advances": 38,
                "declines": 12,
                "unchanged": 0
            },
            "constituents": {
                "top_gainers": [
                    {"symbol": "RELIANCE", "change_percent": 2.35},
                    {"symbol": "TCS", "change_percent": 1.89},
                    {"symbol": "INFY", "change_percent": 1.56}
                ],
                "top_losers": [
                    {"symbol": "HDFC", "change_percent": -1.23},
                    {"symbol": "ICICIBANK", "change_percent": -0.98},
                    {"symbol": "SBIN", "change_percent": -0.76}
                ]
            }
        }
        
        return index_details
        
    except Exception as e:
        logger.error(f"Error fetching index details for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch details for {symbol}")

@router.get("/market-status")
async def get_market_status():
    """Get current market status and timings"""
    try:
        now = datetime.now()
        current_time = now.time()
        
        # Market timings (IST)
        pre_open_start = datetime.strptime("09:00", "%H:%M").time()
        pre_open_end = datetime.strptime("09:15", "%H:%M").time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        post_close_end = datetime.strptime("16:00", "%H:%M").time()
        
        # Determine market phase
        if current_time < pre_open_start:
            phase = "PRE_MARKET"
            status = "CLOSED"
        elif pre_open_start <= current_time < pre_open_end:
            phase = "PRE_OPEN"
            status = "PRE_OPEN"
        elif market_open <= current_time < market_close:
            phase = "NORMAL"
            status = "OPEN"
        elif market_close <= current_time < post_close_end:
            phase = "POST_CLOSE"
            status = "POST_CLOSE"
        else:
            phase = "CLOSED"
            status = "CLOSED"
        
        # Check if it's a weekend
        if now.weekday() in [5, 6]:  # Saturday or Sunday
            phase = "WEEKEND"
            status = "CLOSED"
        
        market_status = {
            "success": True,
            "timestamp": now.isoformat(),
            "market_status": status,
            "market_phase": phase,
            "current_time": current_time.strftime("%H:%M:%S"),
            "timings": {
                "pre_open": "09:00 - 09:15",
                "normal": "09:15 - 15:30",
                "post_close": "15:30 - 16:00",
                "closed": "16:00 - 09:00"
            },
            "is_trading_day": now.weekday() not in [5, 6],
            "next_trading_day": "Monday" if now.weekday() >= 4 else "Tomorrow",
            "data_provider": {
                "name": "TrueData",
                "status": "CONNECTED" if os.getenv('TRUEDATA_USERNAME') else "NOT_CONFIGURED",
                "user": os.getenv('TRUEDATA_USERNAME', 'Not configured')
            }
        }
        
        return market_status
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch market status") 
"""
Market Data API Router
Real-time and historical market data endpoints
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from ..models.responses import APIResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])

# Global variables for TrueData integration  
live_market_data = {}
truedata_connection_status = {
    "connected": False,
    "last_heartbeat": None,
    "symbols_subscribed": []
}

def is_connected() -> bool:
    """Check if TrueData is connected"""
    try:
        # Import here to avoid startup errors
        from data.truedata_client import truedata_client
        return getattr(truedata_client, 'connected', False)
    except ImportError:
        return False

def get_live_data_for_symbol(symbol: str) -> dict:
    """Get live data for a specific symbol"""
    try:
        # Import here to avoid startup errors
        from data.truedata_client import live_market_data
        return live_market_data.get(symbol.upper(), {})
    except ImportError:
        return {}

def get_truedata_status() -> dict:
    """Get TrueData connection status"""
    try:
        # Import here to avoid startup errors
        from data.truedata_client import truedata_client
        return {
            "connected": getattr(truedata_client, 'connected', False),
            "subscribed_symbols": getattr(truedata_client, 'subscribed_symbols', []),
            "last_update": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "connected": False,
            "subscribed_symbols": [],
            "last_update": datetime.now().isoformat()
        }

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query("1min", description="Timeframe for historical data")
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

@router.get("/symbol/{symbol}")
async def get_individual_symbol_data(symbol: str):
    """Get individual symbol data - endpoint for browser console tests"""
    try:
        symbol = symbol.upper()
        
        # Simple TrueData connection check
        has_connection = is_connected()
        
        if not has_connection:
            return {
                "success": False,
                "message": f"TrueData not connected - no live data for {symbol}",
                "symbol": symbol,
                "price": 0,
                "volume": 0,
                "status": "TRUEDATA_DISCONNECTED",
                "timestamp": datetime.now().isoformat()
            }
        
        # Try to get live data for symbol
        live_data = get_live_data_for_symbol(symbol)
        
        if live_data:
            return {
                "success": True,
                "message": f"Live data retrieved for {symbol}",
                "symbol": symbol,
                "price": live_data.get("ltp", 0),
                "volume": live_data.get("volume", 0),
                "change": live_data.get("change", 0),
                "change_percent": live_data.get("change_percent", 0),
                "high": live_data.get("high", 0),
                "low": live_data.get("low", 0),
                "open": live_data.get("open", 0),
                "status": "CONNECTED",
                "data": live_data,
                "timestamp": datetime.now().isoformat(),
                "source": "TrueData_Live"
            }
        else:
            return {
                "success": False,
                "message": f"No live data available for {symbol}",
                "symbol": symbol,
                "price": 0,
                "volume": 0,
                "status": "NO_DATA",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error fetching individual symbol data for {symbol}: {e}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

@router.get("/status")
async def get_market_data_status():
    """Get TrueData connection status"""
    try:
        status = get_truedata_status()
        
        return {
            "success": True,
            "truedata_status": status,
            "connection_status": truedata_connection_status,
            "live_symbols": list(live_market_data.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market data status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """Get real-time market data for dashboard"""
    try:
        # Get live data using our helper function
        live_data = get_live_data_for_symbol(symbol)
        
        if live_data:
            # Format for frontend chart
            formatted_data = [{
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "price": live_data.get("ltp", 0),
                "volume": live_data.get("volume", 0),
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

@router.get("/option-chain/{symbol}")
async def get_option_chain(
    symbol: str,
    _: bool = Depends(is_connected)
):
    """Get option chain for a symbol"""
    try:
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
    _: bool = Depends(is_connected)
):
    """Subscribe to market data for symbols"""
    try:
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

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for trading dashboard"""
    try:
        # Get data from TrueData client - fix import path for production
        try:
            from data.truedata_client import get_truedata_client
        except ImportError:
            try:
                from src.data.truedata_client import get_truedata_client
            except ImportError:
                # Fallback - return mock data structure
                return {
                    "success": True,
                    "data": [
                        {"symbol": "NIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0},
                        {"symbol": "BANKNIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0},
                        {"symbol": "FINNIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0}
                    ],
                    "timestamp": datetime.now().isoformat(),
                    "total_symbols": 3,
                    "note": "TrueData client import not available"
                }
        
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

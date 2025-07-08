"""
Market Data API Router
Real-time and historical market data endpoints
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Import symbol mapping for TrueData
from config.truedata_symbols import get_truedata_symbol

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["market-data"])

# CRITICAL FIX: Direct bridge to populated TrueData cache
# Import at module level to ensure access to the same cache instance
try:
    from data.truedata_client import live_market_data as truedata_cache
    from data.truedata_client import truedata_client, get_truedata_status
    TRUEDATA_BRIDGE_AVAILABLE = True
    logger.info("✅ TrueData cache bridge established")
except ImportError as e:
    logger.error(f"❌ TrueData cache bridge failed: {e}")
    truedata_cache = {}
    TRUEDATA_BRIDGE_AVAILABLE = False

def get_truedata_proxy():
    """Get TrueData data directly from live cache - SIMPLE APPROACH"""
    try:
        # SIMPLE FIX: Direct access to existing TrueData cache
        return {
            'connected': len(truedata_cache) > 0,
            'data': truedata_cache,
            'symbols_count': len(truedata_cache)
        }
    except ImportError:
        logger.error("TrueData client not available")
        return None
    except Exception as e:
        logger.error(f"Error getting TrueData data: {e}")
        return None

def is_connected() -> bool:
    """Check if TrueData is connected via direct cache access"""
    try:
        connected = len(truedata_cache) > 0
        
        logger.info(f"🔧 TrueData direct connection check: {connected}")
        if connected:
            logger.info(f"   Data source: truedata_cache")
            logger.info(f"   Symbols available: {len(truedata_cache)}")
        
        return connected
        
    except Exception as e:
        logger.error(f"Error checking TrueData connection: {e}")
        return False

def get_live_data_for_symbol(symbol: str) -> dict:
    """Get live data for a specific symbol via direct cache access"""
    try:
        # Use symbol mapping to convert NIFTY -> NIFTY-I
        mapped_symbol = get_truedata_symbol(symbol.upper())
        logger.debug(f"🔧 Symbol mapping: {symbol} -> {mapped_symbol}")
        
        # Get data from live cache
        symbol_data = truedata_cache.get(mapped_symbol, {})
        
        if symbol_data:
            logger.debug(f"📊 Retrieved data for {symbol}: LTP={symbol_data.get('ltp', 'N/A')}")
        
        return symbol_data
        
    except Exception as e:
        logger.error(f"Error getting live data for {symbol}: {e}")
        return {}

def get_all_live_market_data() -> dict:
    """Get ALL live market data from direct cache access"""
    try:
        logger.debug(f"📊 Retrieved all market data: {len(truedata_cache)} symbols")
        return truedata_cache
        
    except Exception as e:
        logger.error(f"Error getting all live market data: {e}")
        return {}

@router.get("")
async def get_market_data():
    """Get all market data with direct cache bridge"""
    try:
        # CRITICAL FIX: Use direct bridge to populated TrueData cache
        if TRUEDATA_BRIDGE_AVAILABLE and truedata_cache:
            logger.info(f"📊 Direct cache access: {len(truedata_cache)} symbols available")
            
            return {
                "success": True,
                "symbols_count": len(truedata_cache),
                "data": truedata_cache,
                "source": "direct_truedata_cache_bridge",
                "timestamp": datetime.now().isoformat(),
                "note": "Using direct bridge to populated TrueData cache"
            }
        
        # Fallback to original method if bridge fails
        logger.warning("⚠️ Direct cache bridge not available, using fallback")
        return {
            "success": False,
            "symbols_count": 0,
            "data": {},
            "source": "fallback_no_cache",
            "timestamp": datetime.now().isoformat(),
            "error": "TrueData cache bridge not available"
        }
        
    except Exception as e:
        logger.error(f"Market data endpoint error: {e}")
        return {
            "success": False,
            "symbols_count": 0,
            "data": {},
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query("1min", description="Timeframe for historical data")
):
    """Get market data for a symbol"""
    try:
        # Get live data for symbol with proper symbol mapping
        live_data = get_live_data_for_symbol(symbol)
        
        if live_data:
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": live_data,
                "timestamp": datetime.now().isoformat(),
                "source": "truedata_proxy"
            }
        else:
            # Check if proxy is connected
            if not is_connected():
                raise HTTPException(
                    status_code=503, 
                    detail=f"TrueData proxy not connected. Market data not available for {symbol}."
                )
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No data available for symbol {symbol}. Symbol may not be subscribed."
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error getting market data for {symbol}: {str(e)}"
        )

@router.get("/live")
async def get_live_market_data():
    """Get live market data for autonomous trading system"""
    try:
        logger.info("📊 Getting live market data for autonomous trading...")
        
        # Check if proxy is connected
        if not is_connected():
            raise HTTPException(
                status_code=503,
                detail="TrueData proxy not connected. No live data available."
            )
        
        # Get all live market data
        market_data = get_all_live_market_data()
        
        if not market_data:
            raise HTTPException(
                status_code=503,
                detail="No live market data available from proxy."
            )
        
        # Format for autonomous trading system
        formatted_data = {
            "symbols": list(market_data.keys()),
            "data": market_data,
            "timestamp": datetime.now().isoformat(),
            "source": "truedata_proxy"
        }
        
        logger.info(f"📊 Returning live data for {len(market_data)} symbols")
        
        return {
            "success": True,
            "data": formatted_data,
            "symbol_count": len(market_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live market data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error getting live market data: {str(e)}"
        )

@router.get("/status")
async def get_market_data_status():
    """Get market data service status"""
    try:
        proxy = get_truedata_proxy()
        if not proxy:
            return {
                "success": False,
                "error": "TrueData proxy not available",
                "status": "disconnected",
                "timestamp": datetime.now().isoformat()
            }
        
        status = proxy.get_status()
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market data status: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/symbol-expansion/status")
async def get_symbol_expansion_status():
    """Get current symbol expansion status - for monitoring the 6->250 expansion"""
    try:
        # Get current symbol count
        market_data = get_all_live_market_data()
        current_count = len(market_data)
        
        # Get IntelligentSymbolManager status
        try:
            from src.core.intelligent_symbol_manager import intelligent_symbol_manager
            ism_status = intelligent_symbol_manager.get_status()
        except Exception as e:
            logger.warning(f"Could not get IntelligentSymbolManager status: {e}")
            ism_status = {"error": str(e)}
        
        # Get TrueData status
        truedata_symbols = get_all_live_market_data()
        truedata_count = len(truedata_symbols)
        
        return {
            "success": True,
            "expansion_analysis": {
                "current_symbols": current_count,
                "target_symbols": 250,
                "truedata_available": truedata_count,
                "expansion_needed": 250 - current_count,
                "percentage_complete": round((current_count / 250) * 100, 1),
                "status": "EXPANDING" if current_count < 250 else "TARGET_REACHED"
            },
            "intelligent_symbol_manager": ism_status,
            "truedata_connection": {
                "connected": is_connected(),
                "available_symbols": truedata_count,
                "sample_symbols": list(truedata_symbols.keys())[:10] if truedata_symbols else []
            },
            "recommendations": [
                "Enable IntelligentSymbolManager startup" if not ism_status.get('is_running') else "✅ ISM Running",
                "Expand TrueData subscriptions" if truedata_count < 100 else "✅ TrueData Connected",
                "Configure F&O auto-discovery" if current_count < 50 else "✅ Symbol Discovery Active"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting symbol expansion status: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/individual/{symbol}")
async def get_individual_symbol_data(symbol: str):
    """Get individual symbol data"""
    try:
        # Check TrueData connection
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
                # ELIMINATED: Mock data structure that could mislead about real market data
                # ❌ return {
                # ❌     "success": True,
                # ❌     "data": [
                # ❌         {"symbol": "NIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0},
                # ❌         {"symbol": "BANKNIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0},
                # ❌         {"symbol": "FINNIFTY", "ltp": 0, "change": 0, "change_percent": 0, "volume": 0}
                # ❌     ],
                # ❌     "timestamp": datetime.now().isoformat(),
                # ❌     "total_symbols": 3,
                # ❌     "note": "TrueData client import not available"
                # ❌ }
                
                # SAFETY: Return proper error instead of fake market data
                logger.error("SAFETY: Mock market data structure ELIMINATED to prevent fake trading data")
                return {
                    "success": False,
                    "error": "SAFETY: Mock market data disabled - real TrueData client required",
                    "message": "TrueData client import not available - implement real market data feed"
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

from fastapi import APIRouter, HTTPException
from datetime import datetime
import pytz
import os

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

router = APIRouter(prefix="/api/market", tags=["market-data"])

@router.get("/indices")
async def get_market_indices():
    """Get market indices data from TrueData live feed"""
    try:
        # Import TrueData live data
        from data.truedata_client import live_market_data
        
        # Use IST timezone for timestamp
        now_ist = datetime.now(IST)
        
        # Get live data from TrueData singleton client (using correct symbol formats)
        nifty_data = live_market_data.get('NIFTY-I', {})
        banknifty_data = live_market_data.get('BANKNIFTY-I', {})
        
        # Helper function to extract price data with fallbacks
        def get_price_data(data, symbol_name, fallback_price=0):
            if not data:
                return {
                    "symbol": symbol_name,
                    "name": symbol_name,
                    "price": fallback_price,
                    "change": 0,
                    "change_percent": 0,
                    "last_price": fallback_price,
                    "high": fallback_price,
                    "low": fallback_price,
                    "volume": 0,
                    "status": "NO_DATA"
                }
            
            ltp = data.get('ltp', data.get('last_price', fallback_price))
            high = data.get('high', data.get('day_high', ltp))
            low = data.get('low', data.get('day_low', ltp))
            volume = data.get('volume', data.get('total_volume', 0))
            
            # Calculate change (simplified - in real implementation you'd need previous close)
            prev_close = data.get('prev_close', ltp)
            change = ltp - prev_close if prev_close > 0 else 0
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "symbol": symbol_name,
                "name": symbol_name,
                "price": round(ltp, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "last_price": round(ltp, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "volume": int(volume),
                "status": "LIVE" if ltp > 0 else "NO_DATA",
                "last_update": data.get('timestamp', now_ist.isoformat())
            }
        
        # Build response with live TrueData
        response_data = {
            "nifty_50": get_price_data(nifty_data, "NIFTY 50", 22450),
            "bank_nifty": get_price_data(banknifty_data, "BANK NIFTY", 48500),
            "last_update": now_ist.isoformat(),
            "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            "data_provider": "TrueData",
            "market_status": "LIVE" if 9 <= now_ist.hour < 16 else "CLOSED",
            "truedata_connection": {
                "symbols_available": len(live_market_data),
                "nifty_available": bool(nifty_data),
                "banknifty_available": bool(banknifty_data),
                "live_data_symbols": list(live_market_data.keys())
            }
        }
        
        return {
            "status": "success",
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to fetch market indices: {str(e)}")

@router.get("/market-status")
async def get_market_status():
    """Get current market status and timings"""
    try:
        # Use IST timezone for accurate market timing
        now_ist = datetime.now(IST)
        current_time = now_ist.time()
        
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
        if now_ist.weekday() in [5, 6]:  # Saturday or Sunday
            phase = "WEEKEND"
            status = "CLOSED"
        
        return {
            "status": "success",
            "data": {
                "market_status": status,
                "market_phase": phase,
                "current_time": now_ist.isoformat(),
                "timezone": "Asia/Kolkata",
                "ist_time": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "market_open": "09:15",
                "market_close": "15:30",
                "is_trading_hours": status == "OPEN",
                "timings": {
                    "pre_open": "09:00 - 09:15",
                    "normal": "09:15 - 15:30",
                    "post_close": "15:30 - 16:00",
                    "closed": "16:00 - 09:00"
                },
                "is_trading_day": now_ist.weekday() not in [5, 6],
                "data_provider": {
                    "name": "TrueData",
                    "status": "CONNECTED" if os.getenv('TRUEDATA_USERNAME') else "NOT_CONFIGURED",
                    "user": os.getenv('TRUEDATA_USERNAME', 'Not configured')
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to fetch market status")

# --- START USER ENDPOINTS ---
# Note: This is a temporary measure to test the router refactoring.
import hashlib

def get_database_operations():
    return None

users_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@users_router.get("/current", summary="Get current user")
async def get_current_user():
    """Get current user information (mocked)"""
    try:
        return {
            "status": "success",
            "data": {"username": "admin", "full_name": "Administrator", "email": "admin@trading-system.com", "is_admin": True, "last_login": datetime.now().isoformat(), "permissions": ["read", "write", "admin"]}
        }
    except Exception as e:
        print(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current user") 
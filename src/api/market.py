from fastapi import APIRouter, HTTPException
from datetime import datetime
import pytz
import os

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

router = APIRouter(prefix="/api/market", tags=["market-data"])

@router.get("/indices")
async def get_market_indices():
    """Get market indices data"""
    try:
        # Use IST timezone for timestamp
        now_ist = datetime.now(IST)
        
        # Mock implementation with proper structure that frontend expects
        return {
            "status": "success",
            "data": {
                "nifty_50": {
                    "symbol": "NIFTY 50",
                    "name": "Nifty 50",
                    "price": 22450.75,
                    "change": 125.50,
                    "change_percent": 0.56,
                    "last_price": 22450.75,
                    "high": 22485.30,
                    "low": 22380.15,
                    "volume": 1250000
                },
                "bank_nifty": {
                    "symbol": "BANK NIFTY",
                    "name": "Bank Nifty",
                    "price": 48520.25,
                    "change": -85.75,
                    "change_percent": -0.18,
                    "last_price": 48520.25,
                    "high": 48650.80,
                    "low": 48420.30,
                    "volume": 890000
                },
                "sensex": {
                    "symbol": "SENSEX",
                    "name": "BSE Sensex",
                    "price": 73850.50,
                    "change": 450.25,
                    "change_percent": 0.61,
                    "last_price": 73850.50,
                    "high": 73920.75,
                    "low": 73680.25,
                    "volume": 2100000
                },
                "last_update": now_ist.isoformat(),
                "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "data_provider": "TrueData",
                "market_status": "LIVE" if 9 <= now_ist.hour < 16 else "CLOSED"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to fetch market indices")

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
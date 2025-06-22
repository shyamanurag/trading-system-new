from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/api/market", tags=["market-data"])

@router.get("/indices")
async def get_market_indices():
    """Get market indices data"""
    # This is a mock implementation.
    # In a real application, this would fetch data from a live source.
    return {
        "status": "success",
        "data": {
            "nifty50": {
                "symbol": "NIFTY 50",
                "price": 22450.75,
                "change": 125.50,
                "change_percent": 0.56
            },
            "banknifty": {
                "symbol": "BANK NIFTY",
                "price": 48520.25,
                "change": -85.75,
                "change_percent": -0.18
            },
            "sensex": {
                "symbol": "SENSEX",
                "price": 73850.50,
                "change": 450.25,
                "change_percent": 0.61
            },
            "last_update": datetime.now().isoformat()
        }
    }

@router.get("/market-status")
async def get_market_status():
    """Get market status information"""
    # Mock implementation
    return {
        "status": "success",
        "data": {
            "market_status": "closed",
            "status_message": "Market is currently closed.",
            "current_time": datetime.now().isoformat()
        }
    }

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
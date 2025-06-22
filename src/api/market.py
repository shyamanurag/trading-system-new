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
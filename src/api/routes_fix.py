"""
Quick fix for missing routes - redirect to correct endpoints
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/v1/positions")
async def get_positions():
    """Temporary endpoint for positions"""
    return {
        "success": True,
        "positions": [],
        "message": "No active positions"
    }

@router.get("/api/v1/orders")
async def get_orders():
    """Temporary endpoint for orders"""
    return {
        "success": True,
        "orders": [],
        "message": "No active orders"
    }

@router.get("/api/v1/trades")
async def get_trades():
    """Temporary endpoint for trades"""
    return {
        "success": True,
        "trades": [],
        "message": "No trades today"
    } 
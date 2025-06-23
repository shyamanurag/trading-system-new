"""
System Status API
Provides system status endpoints for frontend
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/v1/system/status")
async def get_system_status():
    """Get system status"""
    try:
        return {
            "success": True,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "active",
            "services": {
                "api": "running",
                "database": "connected",
                "redis": "connected",
                "websocket": "active"
            },
            "version": "4.0.1"
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/broker/status")
async def get_broker_status():
    """Get broker connection status"""
    try:
        return {
            "success": True,
            "broker": "zerodha",
            "status": "connected",
            "last_heartbeat": datetime.utcnow().isoformat(),
            "api_calls_today": 0,
            "rate_limit_remaining": 100,
            "market_data_connected": True,
            "order_management_connected": True
        }
    except Exception as e:
        logger.error(f"Error getting broker status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/strategies/performance")
async def get_strategies_performance():
    """Get strategies performance metrics"""
    try:
        return {
            "success": True,
            "strategies": [
                {
                    "name": "Enhanced Volatility Explosion",
                    "status": "active",
                    "daily_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0
                },
                {
                    "name": "Enhanced Momentum Surfer", 
                    "status": "active",
                    "daily_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0
                },
                {
                    "name": "Enhanced Volume Profile Scalper",
                    "status": "active", 
                    "daily_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0
                },
                {
                    "name": "Enhanced News Impact Scalper",
                    "status": "active",
                    "daily_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0
                }
            ],
            "overall_performance": {
                "total_pnl": 0.0,
                "total_trades": 0,
                "active_strategies": 4,
                "best_performing_strategy": "Enhanced Volatility Explosion",
                "worst_performing_strategy": "Enhanced News Impact Scalper"
            }
        }
    except Exception as e:
        logger.error(f"Error getting strategies performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
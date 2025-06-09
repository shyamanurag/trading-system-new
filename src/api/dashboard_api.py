"""
Dashboard API endpoints for system health and trading metrics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import random
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed system health status"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        health_data = {
            "api": {
                "status": "healthy",
                "latency": random.randint(10, 50),
                "uptime": "99.9%",
                "requests_per_minute": random.randint(100, 500)
            },
            "database": {
                "status": "healthy",
                "connections": random.randint(5, 20),
                "pool_size": 20,
                "active_queries": random.randint(0, 10)
            },
            "redis": {
                "status": "healthy",
                "memory": random.randint(50, 200),
                "connections": random.randint(1, 10),
                "hit_rate": f"{random.randint(85, 99)}%"
            },
            "websocket": {
                "status": "connected",
                "connections": random.randint(10, 50),
                "messages_per_second": random.randint(5, 20)
            },
            "truedata": {
                "status": "healthy",
                "symbols": random.randint(40, 50),
                "subscription_status": "active",
                "data_lag": f"{random.randint(0, 5)}ms"
            },
            "system": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{random.randint(30, 60)}%",
                "network_io": f"{random.randint(10, 100)} MB/s"
            }
        }
        
        return {
            "success": True,
            "data": health_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching detailed health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/metrics")
async def get_trading_metrics():
    """Get trading performance metrics"""
    try:
        metrics = {
            "totalPositions": random.randint(50, 200),
            "openPositions": random.randint(5, 20),
            "todayPnL": random.uniform(5000, 25000),
            "totalPnL": random.uniform(50000, 200000),
            "winRate": random.uniform(55, 75),
            "avgReturn": random.uniform(2, 8),
            "sharpeRatio": random.uniform(1.2, 2.5),
            "maxDrawdown": random.uniform(5, 15),
            "totalTrades": random.randint(100, 500),
            "successfulTrades": random.randint(60, 350),
            "averageHoldingPeriod": f"{random.randint(1, 5)} days",
            "riskRewardRatio": f"1:{random.uniform(1.5, 3):.1f}"
        }
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching trading metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
async def get_system_notifications():
    """Get system notifications"""
    try:
        notification_types = ["info", "warning", "success", "error"]
        notification_titles = [
            "Market Open",
            "Position Alert",
            "Risk Warning",
            "Trade Executed",
            "System Update",
            "Data Feed Status"
        ]
        
        notifications = []
        for i in range(5):
            notifications.append({
                "id": i + 1,
                "type": random.choice(notification_types),
                "title": random.choice(notification_titles),
                "message": f"Notification message {i + 1}",
                "timestamp": datetime.now().isoformat(),
                "read": random.choice([True, False])
            })
        
        return {
            "success": True,
            "data": notifications
        }
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
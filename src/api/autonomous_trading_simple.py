"""
Simple Autonomous Trading API - MINIMAL EFFECTIVE SOLUTION
==========================================================
Uses simple trader instead of complex orchestrator
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Add root directory to Python path
root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging
from src.models.responses import (
    BaseResponse,
    TradingStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/autonomous-simple")

@router.get("/status", response_model=TradingStatusResponse)
async def get_simple_status():
    """Get simple autonomous trading status"""
    try:
        from simple_autonomous_trader import get_simple_trading_status
        
        status = get_simple_trading_status()
        
        return TradingStatusResponse(
            success=True,
            message="Simple trading status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Error getting simple trading status: {str(e)}")
        return TradingStatusResponse(
            success=False,
            message=f"Simple trading status error: {str(e)}",
            data={
                "is_active": False,
                "session_id": f"error_{int(datetime.now().timestamp())}",
                "start_time": None,
                "active_strategies": [],
                "total_trades": 0,
                "system_ready": False,
                "timestamp": datetime.utcnow()
            }
        )

@router.post("/start", response_model=BaseResponse)
async def start_simple_trading():
    """Start simple autonomous trading"""
    try:
        logger.info("🚀 Starting Simple Autonomous Trading...")
        
        from simple_autonomous_trader import start_simple_autonomous_trading
        
        success = await start_simple_autonomous_trading()
        
        if success:
            return BaseResponse(
                success=True,
                message="Simple autonomous trading started successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to start simple autonomous trading")
            
    except Exception as e:
        logger.error(f"Error starting simple trading: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start simple autonomous trading: {str(e)}")

@router.post("/stop", response_model=BaseResponse)
async def stop_simple_trading():
    """Stop simple autonomous trading"""
    try:
        logger.info("🛑 Stopping Simple Autonomous Trading...")
        
        from simple_autonomous_trader import stop_simple_autonomous_trading
        
        stop_simple_autonomous_trading()
        
        return BaseResponse(
            success=True,
            message="Simple autonomous trading stopped successfully"
        )
        
    except Exception as e:
        logger.error(f"Error stopping simple trading: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simple autonomous trading: {str(e)}")

@router.get("/test", response_model=BaseResponse)
async def test_simple_system():
    """Test simple autonomous system components"""
    try:
        logger.info("🧪 Testing Simple Autonomous System...")
        
        from simple_autonomous_trader import SimpleAutonomousTrader
        
        # Create test instance
        trader = SimpleAutonomousTrader()
        
        # Test initialization
        init_success = await trader.initialize()
        
        if init_success:
            return BaseResponse(
                success=True,
                message="Simple autonomous system test passed - all components working"
            )
        else:
            return BaseResponse(
                success=False,
                message="Simple autonomous system test failed - check TrueData and Zerodha connections"
            )
            
    except Exception as e:
        logger.error(f"Error testing simple system: {str(e)}")
        return BaseResponse(
            success=False,
            message=f"Simple autonomous system test error: {str(e)}"
        ) 
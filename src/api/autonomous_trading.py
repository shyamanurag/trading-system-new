"""
Autonomous Trading API
Handles automated trading operations
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import logging
from src.models.responses import (
    BaseResponse,
    TradingStatusResponse,
    PositionResponse,
    PerformanceMetricsResponse,
    StrategyResponse,
    RiskMetricsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/autonomous")

# Lazy import to avoid circular dependency
async def get_orchestrator():
    """Get orchestrator instance with lazy import"""
    from src.core.orchestrator import get_orchestrator as get_orchestrator_instance
    return await get_orchestrator_instance()

@router.get("/status", response_model=TradingStatusResponse)
async def get_status(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get current autonomous trading status"""
    try:
        status = await orchestrator.get_trading_status()
        return TradingStatusResponse(
            success=True,
            message="Trading status retrieved successfully",
            data={
                "is_active": status["is_active"],
                "session_id": status["session_id"],
                "start_time": status["start_time"],
                "last_heartbeat": status["last_heartbeat"],
                "active_strategies": status["active_strategies"],
                "active_positions": status["active_positions"],
                "total_trades": status["total_trades"],
                "daily_pnl": status["daily_pnl"],
                "risk_status": status["risk_status"],
                "market_status": status["market_status"],
                "timestamp": datetime.utcnow()
            }
        )
    except Exception as e:
        logger.error(f"Error getting trading status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start", response_model=BaseResponse)
async def start_trading(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Start autonomous trading"""
    try:
        # Check if trading components are actually initialized (not just system_ready flag)
        components_ready = (
            hasattr(orchestrator, 'strategies') and orchestrator.strategies is not None and
            hasattr(orchestrator, 'risk_manager') and orchestrator.risk_manager is not None and
            hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine is not None
        )
        
        # Force initialization if components are missing (regardless of system_ready flag)
        if not components_ready:
            logger.info("Trading components not initialized, forcing full system initialization...")
            init_success = await orchestrator.initialize_system()
            if not init_success:
                raise HTTPException(status_code=500, detail="Failed to initialize trading system")
        else:
            logger.info("Trading components already initialized, proceeding with trading activation...")
        
        # Now enable trading
        trading_enabled = await orchestrator.enable_trading()
        
        if trading_enabled:
            return BaseResponse(
                success=True,
                message="Autonomous trading started successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to enable trading - system not ready")
            
    except Exception as e:
        logger.error(f"Error starting trading: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=BaseResponse)
async def stop_trading(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Stop autonomous trading"""
    try:
        await orchestrator.disable_trading()
        return BaseResponse(
            success=True,
            message="Autonomous trading stopped successfully"
        )
    except Exception as e:
        logger.error(f"Error stopping trading: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=PositionResponse)
async def get_positions(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get current positions"""
    try:
        # Handle case where position_tracker isn't fully initialized
        if hasattr(orchestrator, 'position_tracker') and hasattr(orchestrator.position_tracker, 'get_all_positions'):
            positions = await orchestrator.position_tracker.get_all_positions()
        else:
            positions = []  # Return empty list if not initialized
        
        return PositionResponse(
            success=True,
            message="Positions retrieved successfully",
            data=positions
        )
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get trading performance metrics"""
    try:
        # Return basic metrics for now
        metrics = {
            "total_trades": getattr(orchestrator, 'total_trades', 0),
            "daily_pnl": getattr(orchestrator, 'daily_pnl', 0.0),
            "active_positions": len(getattr(orchestrator, 'active_positions', [])),
            "win_rate": 0.0,
            "sharpe_ratio": 0.0
        }
        return PerformanceMetricsResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies", response_model=StrategyResponse)
async def get_strategies(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get active trading strategies"""
    try:
        # Fix: Use strategies dictionary instead of strategy_engine
        if hasattr(orchestrator, 'strategies') and orchestrator.strategies:
            strategies = {key: {
                'name': info.get('name', key),
                'active': info.get('active', False),
                'last_signal': info.get('last_signal', None)
            } for key, info in orchestrator.strategies.items()}
        else:
            strategies = {}
        return StrategyResponse(
            success=True,
            message="Strategies retrieved successfully",
            data=strategies
        )
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get current risk metrics"""
    try:
        # Fix: Check if risk_manager is properly initialized
        if hasattr(orchestrator, 'risk_manager') and orchestrator.risk_manager is not None:
            risk_metrics = await orchestrator.risk_manager.get_risk_metrics()
        else:
            # Return default risk metrics if not initialized
            risk_metrics = {
                "max_daily_loss": 50000,
                "current_exposure": 0,
                "available_capital": 0,
                "risk_score": 0,
                "status": "risk_manager_not_initialized"
            }
        return RiskMetricsResponse(
            success=True,
            message="Risk metrics retrieved successfully",
            data=risk_metrics
        )
    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
"""
Debug API Endpoints
Reveals internal orchestrator state for troubleshooting
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from src.core.orchestrator import TradingOrchestrator
from models.responses import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug")

def get_orchestrator() -> TradingOrchestrator:
    """Get the singleton orchestrator instance"""
    orchestrator = TradingOrchestrator.get_instance()
    orchestrator._initialize()
    return orchestrator

@router.get("/orchestrator", response_model=Dict[str, Any])
async def get_orchestrator_debug(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get detailed debug information about orchestrator state"""
    try:
        # Get all internal state
        debug_info = {
            "orchestrator_state": {
                "system_ready": getattr(orchestrator, 'system_ready', 'NOT_SET'),
                "is_active": getattr(orchestrator, 'is_active', 'NOT_SET'),
                "session_id": getattr(orchestrator, 'session_id', 'NOT_SET'),
                "start_time": str(getattr(orchestrator, 'start_time', 'NOT_SET')),
                "total_trades": getattr(orchestrator, 'total_trades', 'NOT_SET'),
                "active_strategies": len(getattr(orchestrator, 'active_strategies', [])),
                "active_positions": len(getattr(orchestrator, 'active_positions', [])),
            },
            "component_status": {
                "zerodha": "AVAILABLE" if getattr(orchestrator, 'zerodha', None) else "NOT_SET",
                "risk_manager": type(getattr(orchestrator, 'risk_manager', None)).__name__ if getattr(orchestrator, 'risk_manager', None) else "NOT_SET",
                "position_tracker": type(getattr(orchestrator, 'position_tracker', None)).__name__ if getattr(orchestrator, 'position_tracker', None) else "NOT_SET",
                "market_data": type(getattr(orchestrator, 'market_data', None)).__name__ if getattr(orchestrator, 'market_data', None) else "NOT_SET",
                "strategy_engine": type(getattr(orchestrator, 'strategy_engine', None)).__name__ if getattr(orchestrator, 'strategy_engine', None) else "NOT_SET",
                "trade_engine": type(getattr(orchestrator, 'trade_engine', None)).__name__ if getattr(orchestrator, 'trade_engine', None) else "NOT_SET",
                "connection_manager": type(getattr(orchestrator, 'connection_manager', None)).__name__ if getattr(orchestrator, 'connection_manager', None) else "NOT_SET",
                "pre_market_analyzer": type(getattr(orchestrator, 'pre_market_analyzer', None)).__name__ if getattr(orchestrator, 'pre_market_analyzer', None) else "NOT_SET",
            },
            "trading_readiness": {
                "market_open": orchestrator._is_market_open(),
                "can_start_trading": orchestrator._can_start_trading(),
            },
            "timestamps": {
                "current_time": datetime.now().isoformat(),
                "debug_generated": datetime.utcnow().isoformat()
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error getting debug info: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@router.post("/force-initialize", response_model=BaseResponse)
async def force_initialize_system(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Force system initialization for debugging"""
    try:
        logger.info("🔧 Force initializing system...")
        
        # Reset state
        orchestrator.system_ready = False
        
        # Try to initialize
        result = await orchestrator.initialize_system()
        
        return BaseResponse(
            success=result,
            message=f"Force initialization {'succeeded' if result else 'failed'}"
        )
        
    except Exception as e:
        logger.error(f"Force initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force-enable-trading", response_model=BaseResponse)
async def force_enable_trading(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Force enable trading for debugging"""
    try:
        logger.info("🔧 Force enabling trading...")
        
        # Bypass system_ready check temporarily
        original_system_ready = orchestrator.system_ready
        orchestrator.system_ready = True
        
        # Try to enable trading
        result = await orchestrator.enable_trading()
        
        # Restore original state if it failed
        if not result:
            orchestrator.system_ready = original_system_ready
        
        return BaseResponse(
            success=result,
            message=f"Force enable trading {'succeeded' if result else 'failed'}"
        )
        
    except Exception as e:
        logger.error(f"Force enable trading error: {e}")
        # Restore original state
        orchestrator.system_ready = original_system_ready
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-state-setting", response_model=Dict[str, Any])
async def test_state_setting(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Test basic state setting to isolate the issue"""
    try:
        logger.info("🧪 TEST: Starting basic state setting test")
        
        # Get initial state
        initial_active = getattr(orchestrator, 'is_active', 'MISSING')
        logger.info(f"   Initial is_active: {initial_active}")
        
        # Test 1: Direct assignment
        orchestrator.is_active = True
        after_direct = getattr(orchestrator, 'is_active', 'MISSING')
        logger.info(f"   After direct assignment: {after_direct}")
        
        # Test 2: setattr
        setattr(orchestrator, 'is_active', True)
        after_setattr = getattr(orchestrator, 'is_active', 'MISSING')
        logger.info(f"   After setattr: {after_setattr}")
        
        # Test 3: dict assignment
        orchestrator.__dict__['is_active'] = True
        after_dict = orchestrator.__dict__.get('is_active', 'MISSING')
        logger.info(f"   After dict assignment: {after_dict}")
        
        # Test 4: Check if it persists
        final_check = orchestrator.is_active
        logger.info(f"   Final check: {final_check}")
        
        return {
            "test_results": {
                "initial": initial_active,
                "after_direct": after_direct,
                "after_setattr": after_setattr,
                "after_dict": after_dict,
                "final_check": final_check,
                "success": final_check == True
            },
            "orchestrator_id": getattr(orchestrator, '_instance_id', 'unknown'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"State setting test failed: {e}")
        return {
            "error": str(e),
            "test_results": None,
            "timestamp": datetime.utcnow().isoformat()
        } 
"""
Debug API Endpoints
Reveals internal orchestrator state for troubleshooting
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from src.core.orchestrator import TradingOrchestrator
# Use shared dependency to fix singleton issue
from src.core.dependencies import get_orchestrator
from models.responses import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug")

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

@router.post("/test-enable-trading", response_model=Dict[str, Any])
async def test_enable_trading_direct(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Test enable_trading method directly with full exception handling"""
    try:
        logger.info("🧪 TEST: Calling enable_trading() directly")
        
        # Capture before state
        before_state = {
            "is_active": getattr(orchestrator, 'is_active', 'MISSING'),
            "session_id": getattr(orchestrator, 'session_id', 'MISSING'),
            "start_time": str(getattr(orchestrator, 'start_time', 'MISSING')),
            "system_ready": getattr(orchestrator, 'system_ready', 'MISSING')
        }
        logger.info(f"   Before state: {before_state}")
        
        # Call enable_trading with exception handling
        try:
            result = await orchestrator.enable_trading()
            logger.info(f"   enable_trading() returned: {result}")
        except Exception as enable_error:
            logger.error(f"   EXCEPTION in enable_trading(): {enable_error}")
            return {
                "error": f"Exception in enable_trading(): {str(enable_error)}",
                "before_state": before_state,
                "after_state": None,
                "result": None
            }
        
        # Capture after state
        after_state = {
            "is_active": getattr(orchestrator, 'is_active', 'MISSING'),
            "session_id": getattr(orchestrator, 'session_id', 'MISSING'),
            "start_time": str(getattr(orchestrator, 'start_time', 'MISSING')),
            "system_ready": getattr(orchestrator, 'system_ready', 'MISSING')
        }
        logger.info(f"   After state: {after_state}")
        
        # Analysis
        analysis = {
            "method_returned": result,
            "is_active_changed": before_state["is_active"] != after_state["is_active"],
            "session_created": after_state["session_id"] != "MISSING" and after_state["session_id"] is not None,
            "start_time_set": after_state["start_time"] != "MISSING" and after_state["start_time"] != "None"
        }
        
        return {
            "before_state": before_state,
            "after_state": after_state,
            "result": result,
            "analysis": analysis,
            "orchestrator_id": getattr(orchestrator, '_instance_id', 'unknown'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test enable trading failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/test-minimal-enable", response_model=Dict[str, Any])
async def test_minimal_enable(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Minimal enable test - just set state and return immediately"""
    try:
        logger.info("🧪 MINIMAL TEST: Setting state and returning immediately")
        
        # Get before state
        before_active = getattr(orchestrator, 'is_active', 'MISSING')
        before_session = getattr(orchestrator, 'session_id', 'MISSING')
        
        # Set state (copy of bulletproof logic)
        logger.info("🔥 MINIMAL: Setting core state")
        orchestrator.is_active = True
        orchestrator.session_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        orchestrator.start_time = datetime.utcnow()
        
        # Get after state immediately
        after_active = getattr(orchestrator, 'is_active', 'MISSING')
        after_session = getattr(orchestrator, 'session_id', 'MISSING')
        
        logger.info(f"🔍 MINIMAL RESULT: {before_active} -> {after_active}, session: {after_session}")
        
        return {
            "test_type": "minimal_enable",
            "before": {
                "is_active": before_active,
                "session_id": before_session
            },
            "after": {
                "is_active": after_active,
                "session_id": after_session
            },
            "success": after_active == True and after_session is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Minimal enable test failed: {e}")
        return {
            "error": str(e),
            "test_type": "minimal_enable_failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/test-bulletproof-deployed", response_model=Dict[str, Any])
async def test_bulletproof_deployed(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Test if the bulletproof enable_trading code is actually deployed"""
    try:
        logger.info("🧪 TESTING: Checking if bulletproof code is deployed")
        
        # Try to call enable_trading and capture any specific logs
        import io
        import sys
        from contextlib import redirect_stderr, redirect_stdout
        
        # Capture logs during enable_trading call
        log_capture = io.StringIO()
        
        try:
            # Call enable_trading with logging capture
            result = await orchestrator.enable_trading()
            
            return {
                "test_type": "bulletproof_deployment_check",
                "enable_trading_result": result,
                "bulletproof_deployed": "BULLETPROOF: Setting core state" in str(log_capture.getvalue()),
                "current_is_active": getattr(orchestrator, 'is_active', 'MISSING'),
                "current_session_id": getattr(orchestrator, 'session_id', 'MISSING'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as enable_error:
            return {
                "test_type": "bulletproof_deployment_check",
                "enable_trading_error": str(enable_error),
                "current_is_active": getattr(orchestrator, 'is_active', 'MISSING'),
                "current_session_id": getattr(orchestrator, 'session_id', 'MISSING'),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Bulletproof deployment test failed: {e}")
        return {
            "error": str(e),
            "test_type": "bulletproof_deployment_check_failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/test-signal-generation")
async def test_signal_generation(orchestrator: TradingOrchestrator = Depends(get_orchestrator)):
    """Test if trading strategies are generating signals"""
    try:
        logger.info("🔍 TESTING SIGNAL GENERATION")
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'market_open': orchestrator._is_market_open(),
            'strategy_engine_exists': orchestrator.strategy_engine is not None,
            'market_data_exists': orchestrator.market_data is not None,
            'signals_generated': 0,
            'signal_details': [],
            'market_data_sample': {},
            'errors': []
        }
        
        # Test 1: Check if market data is available
        if orchestrator.market_data:
            try:
                symbols = ['BANKNIFTY', 'NIFTY', 'SBIN']
                market_data = await orchestrator.market_data.get_latest_data(symbols)
                result['market_data_sample'] = {
                    'symbols_returned': list(market_data.keys()),
                    'sample_data_keys': list(market_data.values())[0].keys() if market_data else [],
                    'price_history_type': type(market_data[symbols[0]]['price_history']).__name__ if market_data and 'price_history' in market_data.get(symbols[0], {}) else None,
                    'price_history_length': len(market_data[symbols[0]]['price_history']) if market_data and 'price_history' in market_data.get(symbols[0], {}) else 0
                }
            except Exception as e:
                result['errors'].append(f"Market data error: {str(e)}")
        
        # Test 2: Try to generate signals
        if orchestrator.strategy_engine and orchestrator.market_data:
            try:
                symbols = ['BANKNIFTY', 'NIFTY', 'SBIN']
                market_data = await orchestrator.market_data.get_latest_data(symbols)
                
                if market_data:
                    # Try to generate signals
                    signals = await orchestrator.strategy_engine.generate_all_signals(market_data)
                    
                    result['signals_generated'] = len(signals)
                    result['signal_details'] = [
                        {
                            'symbol': signal.symbol,
                            'side': signal.side.value if hasattr(signal.side, 'value') else str(signal.side),
                            'quality_score': signal.quality_score,
                            'strategy_name': signal.strategy_name
                        }
                        for signal in signals[:5]  # First 5 signals
                    ]
                    
            except Exception as e:
                result['errors'].append(f"Signal generation error: {str(e)}")
        else:
            if not orchestrator.strategy_engine:
                result['errors'].append("Strategy engine not initialized")
            if not orchestrator.market_data:
                result['errors'].append("Market data not initialized")
        
        # Test 3: Check trading loop status
        result['trading_loop_info'] = {
            'is_active': orchestrator.is_active,
            'system_ready': orchestrator.system_ready,
            'active_strategies': orchestrator.active_strategies
        }
        
        logger.info(f"📊 Signal generation test results: {result['signals_generated']} signals, {len(result['errors'])} errors")
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Signal generation test failed: {e}")
        return {"success": False, "error": str(e)} 
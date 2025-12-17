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
import asyncio  # ⚡ FIXED: Added missing import
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
    """Get orchestrator instance - FAST PATH first, then async fallback with timeout"""
    try:
        # FAST PATH: Check global instance directly (no async, no blocking)
        # This is set by main.py during startup and avoids blocking API calls
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        if orchestrator is not None:
            return orchestrator
        
        # SLOW PATH: Try async initialization with timeout
        # This should rarely be hit in production (only if API called before startup completes)
        from src.core.orchestrator import get_orchestrator as get_orchestrator_async
        try:
            orchestrator = await asyncio.wait_for(get_orchestrator_async(), timeout=5.0)
            return orchestrator
        except asyncio.TimeoutError:
            logger.warning("⚠️ Orchestrator initialization timed out (5s) - returning None")
            return None
    except ImportError as import_error:
        logger.error(f"Cannot import orchestrator: {import_error}")
        return None
    except Exception as e:
        logger.error(f"Error getting orchestrator: {e}")
        return None

@router.get("/status", response_model=TradingStatusResponse)
async def get_status():
    """Get current autonomous trading status - NON-BLOCKING to prevent 504"""
    try:
        # CRITICAL FIX: Cache status for 15 seconds to prevent API hammering
        import time
        current_time = time.time()
        
        # Check if we have cached data less than 15 seconds old
        if hasattr(get_status, '_cache') and hasattr(get_status, '_cache_time'):
            if current_time - get_status._cache_time < 15:
                logger.info("📊 Using cached autonomous status (preventing API hammering)")
                return get_status._cache
        
        # 🚀 CRITICAL FIX: Get orchestrator WITHOUT blocking - just check global instance
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()  # Fast, non-blocking
        
        # CRITICAL FIX: Ensure we get proper status even if orchestrator is not fully initialized
        if not orchestrator or not hasattr(orchestrator, 'get_trading_status'):
            logger.warning("Orchestrator not properly initialized - using fallback status")
            return TradingStatusResponse(
                success=True,
                message="Trading status retrieved (fallback mode)",
                data={
                    "is_active": False,
                    "session_id": f"fallback_{int(datetime.now().timestamp())}",
                    "start_time": None,
                    "last_heartbeat": datetime.now().isoformat(),
                    "active_strategies": [],
                    "active_strategies_count": 0,  # CRITICAL FIX: Add count to fallback
                    "active_positions": 0,
                    "total_trades": 0,
                    "daily_pnl": 0.0,
                    "risk_status": {"status": "not_initialized"},
                    "market_status": "UNKNOWN",
                    "system_ready": False,
                    "timestamp": datetime.utcnow()
                }
            )
        
        status = await orchestrator.get_trading_status()
        
        # CRITICAL FIX: Handle case where status might be missing keys
        safe_status = {
            "is_active": status.get("is_active", False),
            "session_id": status.get("session_id", f"session_{int(datetime.now().timestamp())}"),
            "start_time": status.get("start_time"),
            "last_heartbeat": status.get("last_heartbeat", datetime.now().isoformat()),
            "active_strategies": status.get("active_strategies", []),
            "active_strategies_count": status.get("active_strategies_count", len(status.get("active_strategies", []))),  # Use count from orchestrator
            "active_positions": status.get("active_positions", 0),
            "total_trades": status.get("total_trades", 0),
            "daily_pnl": status.get("daily_pnl", 0.0),
            "risk_status": status.get("risk_status", {"status": "unknown"}),
            "market_status": status.get("market_status", "UNKNOWN"),
            "system_ready": status.get("system_ready", False),
            "timestamp": datetime.utcnow()
        }
        
        result = TradingStatusResponse(
            success=True,
            message="Trading status retrieved successfully",
            data=safe_status
        )
        
        # Cache the result for 15 seconds
        get_status._cache = result
        get_status._cache_time = current_time
        logger.info(f"📊 Cached autonomous status result for 15 seconds")
        
        return result
    except Exception as e:
        logger.error(f"Error getting trading status: {str(e)}")
        # Return safe fallback instead of failing
        return TradingStatusResponse(
            success=True,
            message=f"Trading status error: {str(e)}",
            data={
                "is_active": False,
                "session_id": f"error_{int(datetime.now().timestamp())}",
                "start_time": None,
                "last_heartbeat": datetime.now().isoformat(),
                "active_strategies": [],
                "active_strategies_count": 0,  # CRITICAL FIX: Add count to fallback
                "active_positions": 0,
                "total_trades": 0,
                "daily_pnl": 0.0,
                "risk_status": {"status": "error", "error": str(e)},
                "market_status": "ERROR",
                "system_ready": False,
                "timestamp": datetime.utcnow()
            }
        )

@router.post("/reset", response_model=BaseResponse)
async def reset_orchestrator():
    """Reset orchestrator instance to force recreation with new code"""
    try:
        logger.info("🔄 Resetting orchestrator instance...")
        
        # Reset the singleton instance
        from src.core.orchestrator import TradingOrchestrator
        TradingOrchestrator.reset_instance()
        
        # Also reset the global instance
        from src.core.orchestrator import set_orchestrator_instance
        set_orchestrator_instance(None)
        
        logger.info("✅ Orchestrator instance reset successfully")
        return BaseResponse(
            success=True,
            message="Orchestrator instance reset successfully - next API call will create fresh instance"
        )
        
    except Exception as e:
        logger.error(f"Error resetting orchestrator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset orchestrator: {str(e)}")

@router.post("/start", response_model=BaseResponse)
async def start_trading():
    """
    Start autonomous trading - Returns immediately, initialization happens in background
    ⚡ FIXED: No more 504 timeouts - NO DEPENDENCY INJECTION to avoid blocking
    """
    try:
        logger.info("🚀 Starting autonomous trading system...")
        
        # 🚀 CRITICAL FIX: Get orchestrator WITHOUT blocking - check global only
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()  # Fast, non-blocking check
        
        # 🚀 CRITICAL FIX: Start initialization in background to avoid 504 timeout
        async def background_startup():
            """Background task to initialize and start trading"""
            try:
                logger.info("🔄 Background startup initiated...")
                
                # Get or create orchestrator
                local_orchestrator = orchestrator
                if not local_orchestrator:
                    logger.warning("❌ Orchestrator not available - creating new instance...")
                    from src.core.orchestrator import TradingOrchestrator, set_orchestrator_instance
                    
                    logger.info("🔧 Creating orchestrator instance...")
                    local_orchestrator = TradingOrchestrator()
                    
                    # Initialize the orchestrator
                    init_success = await local_orchestrator.initialize()
                    
                    if init_success and local_orchestrator:
                        set_orchestrator_instance(local_orchestrator)
                        logger.info("✅ Orchestrator created and initialized")
                    else:
                        logger.error("❌ Failed to initialize orchestrator")
                        return
                
                # Force complete system initialization
                logger.info("🔄 Forcing complete system initialization...")
                
                # 🚨 CRITICAL FIX: PRESERVE existing zerodha_client with fresh token!
                # Token was submitted BEFORE /start, don't create new client with stale credentials
                existing_zerodha_client = getattr(local_orchestrator, 'zerodha_client', None)
                if existing_zerodha_client:
                    logger.info("✅ PRESERVING existing Zerodha client (has fresh token)")
                    logger.info(f"   Token length: {len(existing_zerodha_client.access_token) if hasattr(existing_zerodha_client, 'access_token') and existing_zerodha_client.access_token else 0}")
                
                # Clear running state but NOT initialization state
                # 🚨 CRITICAL FIX: Don't clear is_initialized - let the guard in orchestrator handle it
                if hasattr(local_orchestrator, 'is_running'):
                    local_orchestrator.is_running = False
                
                # Initialize if not already done (orchestrator has built-in guard)
                init_success = await local_orchestrator.initialize()
                
                # 🚨 CRITICAL FIX: Restore the preserved zerodha_client after initialization
                # initialize() may have created a new client with stale credentials
                if existing_zerodha_client:
                    local_orchestrator.zerodha_client = existing_zerodha_client
                    logger.info("✅ RESTORED preserved Zerodha client after initialization")
                    
                    # Also update trade_engine and order_manager with preserved client
                    if hasattr(local_orchestrator, 'trade_engine') and local_orchestrator.trade_engine:
                        local_orchestrator.trade_engine.zerodha_client = existing_zerodha_client
                        logger.info("✅ Updated trade_engine with preserved Zerodha client")
                    if hasattr(local_orchestrator, 'order_manager') and local_orchestrator.order_manager:
                        local_orchestrator.order_manager.zerodha_client = existing_zerodha_client
                        logger.info("✅ Updated order_manager with preserved Zerodha client")
                
                if not init_success:
                    logger.error("❌ System initialization failed")
                    return
                
                logger.info(f"✅ System initialized with {len(local_orchestrator.strategies) if hasattr(local_orchestrator, 'strategies') else 0} strategies")
                
                # Force trading start
                logger.info("🚀 Force starting trading system...")
                
                # Set running state directly
                local_orchestrator.is_running = True
                
                # Activate all strategies
                if hasattr(local_orchestrator, 'strategies'):
                    for strategy_key in local_orchestrator.strategies:
                        local_orchestrator.strategies[strategy_key]['active'] = True
                        if hasattr(local_orchestrator, 'active_strategies'):
                            if strategy_key not in local_orchestrator.active_strategies:
                                local_orchestrator.active_strategies.append(strategy_key)
                
                # Start the trading loop if available
                if hasattr(local_orchestrator, 'start_trading'):
                    try:
                        await local_orchestrator.start_trading()
                        logger.info("✅ Trading loop started successfully")
                    except Exception as start_error:
                        logger.warning(f"⚠️ Trading loop start failed: {start_error}")
                
                logger.info("✅ Autonomous trading system fully initialized and running")
                
            except Exception as bg_error:
                logger.error(f"❌ Background startup failed: {bg_error}")
        
        # Start background task
        asyncio.create_task(background_startup())
        
        # Return immediately (don't wait for initialization)
        logger.info("✅ Autonomous trading startup initiated in background")
        
        return BaseResponse(
            success=True,
            message="🚀 Trading system is starting in background. Check /status endpoint in 10-15 seconds."
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trading: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start autonomous trading: {str(e)}")

@router.post("/stop", response_model=BaseResponse)
async def stop_trading():
    """Stop autonomous trading - NON-BLOCKING"""
    from src.core.orchestrator import get_orchestrator_instance
    orchestrator = get_orchestrator_instance()
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
async def get_performance():
    """Get trading performance metrics - NON-BLOCKING"""
    from src.core.orchestrator import get_orchestrator_instance
    orchestrator = get_orchestrator_instance()
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
async def get_risk_metrics():
    """Get current risk metrics - NON-BLOCKING"""
    from src.core.orchestrator import get_orchestrator_instance
    orchestrator = get_orchestrator_instance()
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

@router.get("/orders")
async def get_orders(
    orchestrator: Any = Depends(get_orchestrator)
):
    """Get today's orders"""
    try:
        # Get today's orders from database
        from datetime import date
        today = date.today()
        
        # Try to get orders from database
        try:
            from src.core.database import get_db
            db_session = next(get_db())
            if db_session:
                # Get orders for today
                from sqlalchemy import text
                query = text("""
                    SELECT order_id, symbol, order_type, side, quantity, price, status, 
                           strategy_name, created_at, filled_at
                    FROM orders 
                    WHERE DATE(created_at) = :today
                    ORDER BY created_at DESC
                """)
                result = db_session.execute(query, {"today": today})
                orders = []
                for row in result:
                    orders.append({
                        "order_id": row.order_id,
                        "symbol": row.symbol,
                        "order_type": row.order_type,
                        "side": row.side,
                        "quantity": row.quantity,
                        "price": float(row.price) if row.price else None,
                        "status": row.status,
                        "strategy_name": row.strategy_name,
                        "created_at": row.created_at.isoformat(),
                        "filled_at": row.filled_at.isoformat() if row.filled_at else None
                    })
                
                return {
                    "success": True,
                    "message": f"Found {len(orders)} orders for today",
                    "data": orders,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("Database session not available")
                return {
                    "success": True,
                    "message": "No orders found (database unavailable)",
                    "data": [],
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as db_error:
            logger.warning(f"Database query failed: {db_error}")
            # Return empty list if database fails
            return {
                "success": True,
                "message": "No orders found (database unavailable)",
                "data": [],
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades")
async def get_trades():
    """Get today's trades from Zerodha - NON-BLOCKING"""
    from src.core.orchestrator import get_orchestrator_instance
    orchestrator = get_orchestrator_instance()
    try:
        # Get Zerodha client
        if not orchestrator or not orchestrator.zerodha_client:
            return {
                "success": False,
                "trades": [],
                "message": "Zerodha client not available",
                "source": "ZERODHA_API"
            }
        
        # Get orders directly from Zerodha API
        logger.info("📋 Fetching today's orders from Zerodha API...")
        orders = await orchestrator.zerodha_client.get_orders()
        
        if not orders:
            logger.warning("⚠️ No orders returned from Zerodha API")
            return {
                "success": True,
                "trades": [],
                "count": 0,
                "message": "No orders found in Zerodha",
                "source": "ZERODHA_API",
                "timestamp": datetime.now().isoformat()
            }
        
        # Filter today's orders and format as trades
        formatted_trades = []
        today = datetime.now().date()
        
        logger.info(f"📋 Processing {len(orders)} orders from Zerodha...")
        
        for order in orders:
            try:
                # Get order timestamp
                order_timestamp = order.get('order_timestamp', '')
                if order_timestamp:
                    try:
                        if 'T' in order_timestamp:
                            order_date = datetime.fromisoformat(order_timestamp.replace('Z', '+00:00'))
                        else:
                            order_date = datetime.strptime(order_timestamp, '%Y-%m-%d %H:%M:%S')
                        
                        # Only include today's orders
                        if order_date.date() != today:
                            continue
                    except:
                        # Include orders with unparseable timestamps
                        pass
                
                # Only include completed orders
                status = order.get('status', '')
                if status not in ['COMPLETE', 'EXECUTED']:
                    continue
                
                symbol = order.get('tradingsymbol', 'UNKNOWN')
                quantity = order.get('quantity', 0)
                price = order.get('average_price', order.get('price', 0))
                side = order.get('transaction_type', 'UNKNOWN')
                
                # Calculate basic P&L (for completed orders)
                pnl = 0
                pnl_percent = 0
                
                trade_info = {
                    "trade_id": order.get('order_id', 'UNKNOWN'),
                    "symbol": symbol,
                    "trade_type": side.lower(),
                    "quantity": quantity,
                    "price": price,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "status": status,
                    "strategy": "Manual/Zerodha",
                    "commission": 0,  # Zerodha doesn't provide this in orders API
                    "executed_at": order_timestamp
                }
                
                formatted_trades.append(trade_info)
                
                logger.info(f"📊 Trade: {symbol} | {side} | Qty: {quantity} | Price: ₹{price}")
                
            except Exception as order_error:
                logger.warning(f"Error processing order: {order_error}")
                continue
        
        logger.info(f"📊 TRADES SUMMARY: {len(formatted_trades)} trades found for today")
        
        return {
            "success": True,
            "trades": formatted_trades,
            "count": len(formatted_trades),
            "message": f"Retrieved {len(formatted_trades)} trades from Zerodha",
            "source": "ZERODHA_API",
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
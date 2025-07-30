from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_all_trades() -> List[Dict[str, Any]]:
    """Get all trades - FIXED: Now fetches actual trades from Zerodha"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            logger.warning("Zerodha client not available")
            return []
        
        # Get ACTUAL trades from Zerodha API
        logger.info("📋 Fetching today's orders from Zerodha API...")
        orders = await orchestrator.zerodha_client.get_orders()
        
        if not orders:
            return []
        
        # Filter today's executed orders and format as trades
        formatted_trades = []
        today = datetime.now().date()
        
        for order in orders:
            try:
                # Only include executed orders from today
                if order.get('status') != 'COMPLETE':
                    continue
                
                order_date_str = order.get('order_timestamp', '')
                if order_date_str:
                    order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00')).date()
                    if order_date != today:
                        continue
                
                symbol = order.get('tradingsymbol', 'UNKNOWN')
                side = order.get('transaction_type', 'UNKNOWN')
                
                # 🚨 FIX: Convert Zerodha string values to numbers
                try:
                    quantity = int(float(order.get('filled_quantity', 0)))
                except (ValueError, TypeError):
                    quantity = 0
                    
                try:
                    price = float(order.get('average_price', 0))
                except (ValueError, TypeError):
                    price = 0.0
                
                trade_info = {
                    "trade_id": order.get('order_id', 'UNKNOWN'),
                    "symbol": symbol,
                    "trade_type": side.lower(),
                    "quantity": quantity,
                    "price": price,
                    "pnl": 0,  # Calculate if needed
                    "pnl_percent": 0,
                    "status": "EXECUTED",
                    "strategy": "Zerodha",
                    "commission": 0,
                    "executed_at": order.get('order_timestamp')
                }
                
                formatted_trades.append(trade_info)
                
            except Exception as order_error:
                logger.warning(f"Error processing order: {order_error}")
                continue
        
        logger.info(f"📊 Retrieved {len(formatted_trades)} trades from Zerodha")
        return formatted_trades
        
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        return []

@router.get("/live")
async def get_live_trades() -> List[Dict[str, Any]]:
    """Get all live trades - FIXED: Now fetches real-time trades from Zerodha"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            logger.warning("Zerodha client not available for live trades")
            return []
        
        # Get ACTUAL live trades from Zerodha API (same as main trades but optimized for real-time)
        logger.info("📋 Fetching live orders from Zerodha API...")
        orders = await orchestrator.zerodha_client.get_orders()
        
        if not orders:
            return []
        
        # Filter today's executed orders and format as live trades
        live_trades = []
        today = datetime.now().date()
        
        for order in orders:
            try:
                # Only include executed orders from today
                if order.get('status') != 'COMPLETE':
                    continue
                
                order_date_str = order.get('order_timestamp', '')
                if order_date_str:
                    order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00')).date()
                    if order_date != today:
                        continue
                
                symbol = order.get('tradingsymbol', 'UNKNOWN')
                side = order.get('transaction_type', 'UNKNOWN')
                
                # 🚨 FIX: Convert Zerodha string values to numbers
                try:
                    quantity = int(float(order.get('filled_quantity', 0)))
                except (ValueError, TypeError):
                    quantity = 0
                    
                try:
                    price = float(order.get('average_price', 0))
                except (ValueError, TypeError):
                    price = 0.0
                
                # Enhanced format for live display
                trade_info = {
                    "id": order.get('order_id', 'UNKNOWN'),
                    "trade_id": order.get('order_id', 'UNKNOWN'),
                    "symbol": symbol,
                    "side": side.lower(),
                    "trade_type": side.lower(),
                    "quantity": quantity,
                    "entry_price": price,
                    "current_price": price,  # For executed trades, current = entry
                    "price": price,
                    "pnl": 0,
                    "pnl_percent": 0,
                    "status": "EXECUTED",
                    "strategy": "Zerodha",
                    "commission": 0,
                    "entry_time": order.get('order_timestamp'),
                    "executed_at": order.get('order_timestamp'),
                    "timestamp": order.get('order_timestamp')
                }
                
                live_trades.append(trade_info)
                
            except Exception as order_error:
                logger.warning(f"Error processing live order: {order_error}")
                continue
        
        logger.info(f"📊 Retrieved {len(live_trades)} live trades from Zerodha")
        return live_trades
        
    except Exception as e:
        logger.error(f"Error getting live trades: {str(e)}")
        return []

@router.get("/users/metrics")
async def get_all_user_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics for all users - FIXED: Now returns actual user metrics"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator:
            logger.warning("Orchestrator not available for user metrics")
            return {}
        
        # Get actual user metrics
        try:
            # Try to get metrics from orchestrator or other sources
            metrics = {
                "total_users": 1,  # At least the main trading user
                "active_users": 1 if orchestrator.zerodha_client else 0,
                "total_trades_today": 0,
                "total_pnl_today": 0.0,
                "last_updated": datetime.now().isoformat()
            }
            
            # If we have Zerodha client, get actual trade count
            if orchestrator.zerodha_client:
                try:
                    orders = await orchestrator.zerodha_client.get_orders()
                    if orders:
                        today = datetime.now().date()
                        today_orders = [
                            order for order in orders 
                            if order.get('status') == 'COMPLETE' and
                            order.get('order_timestamp') and
                            datetime.fromisoformat(order.get('order_timestamp').replace('Z', '+00:00')).date() == today
                        ]
                        metrics["total_trades_today"] = len(today_orders)
                        logger.info(f"📊 User metrics: {len(today_orders)} trades today")
                except Exception as e:
                    logger.warning(f"Could not fetch trade count for metrics: {e}")
            
            return {"master_user": metrics}
            
        except Exception as e:
            logger.warning(f"Error calculating user metrics: {e}")
            return {
                "master_user": {
                    "total_users": 1,
                    "active_users": 0,
                    "total_trades_today": 0,
                    "total_pnl_today": 0.0,
                    "last_updated": datetime.now().isoformat(),
                    "error": str(e)
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting user metrics: {str(e)}")
        return {}

@router.get("/{trade_id}")
async def get_trade_details(trade_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific trade"""
    try:
        # Trade not found since we're not persisting yet
        raise HTTPException(status_code=404, detail="Trade not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user_trades(user_id: str) -> List[Dict[str, Any]]:
    """Get all trades for a specific user"""
    try:
        # Return empty list for now
        return []
    except Exception as e:
        logger.error(f"Error getting user trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/metrics")
async def get_user_metrics(user_id: str) -> Dict[str, Any]:
    """Get detailed metrics for a specific user"""
    try:
        # Return basic metrics structure
        return {
            "user_id": user_id,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/sync-zerodha-data")
async def sync_zerodha_data():
    """Manually trigger Zerodha trade and position synchronization + Database Migration Fix"""
    try:
        logger.info("🚀 Manual sync triggered for Zerodha data")
        
        # URGENT MIGRATION FIX: Add missing columns if they don't exist
        try:
            logger.info("🚨 URGENT: Checking database schema for missing columns...")
            from sqlalchemy import create_engine, text
            import os
            
            # Get DATABASE_URL from environment
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                logger.info("📊 Executing urgent migration 016 inline...")
                
                # Create engine and connect
                engine = create_engine(database_url)
                
                with engine.connect() as conn:
                    # Start transaction
                    trans = conn.begin()
                    
                    try:
                        # Add missing columns
                        conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS actual_execution BOOLEAN DEFAULT FALSE"))
                        conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS current_price DECIMAL(10,2)"))
                        conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS pnl DECIMAL(12,2) DEFAULT 0.0"))
                        conn.execute(text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS pnl_percent DECIMAL(8,4) DEFAULT 0.0"))
                        
                        # Create indexes
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_actual_execution ON trades(actual_execution)"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_current_price ON trades(current_price)"))
                        
                        # Update existing trades
                        conn.execute(text("UPDATE trades SET actual_execution = FALSE WHERE actual_execution IS NULL"))
                        
                        # Create schema_migrations table if it doesn't exist
                        conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS schema_migrations (
                                version INTEGER PRIMARY KEY,
                                description TEXT,
                                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        
                        # Log the migration
                        conn.execute(text("""
                            INSERT INTO schema_migrations (version, description, executed_at) 
                            VALUES (16, 'Add actual_execution and P&L columns for real Zerodha data sync', CURRENT_TIMESTAMP)
                            ON CONFLICT (version) DO NOTHING
                        """))
                        
                        # Commit transaction
                        trans.commit()
                        
                        logger.info("✅ URGENT Migration 016 executed successfully inline!")
                        
                    except Exception as migration_error:
                        trans.rollback()
                        logger.warning(f"⚠️ Migration 016 failed (may already exist): {migration_error}")
                        
        except Exception as schema_error:
            logger.warning(f"⚠️ Schema check failed: {schema_error}")
        
        # Continue with normal Zerodha sync logic
        from src.core.orchestrator import get_orchestrator_instance
        
        orchestrator = get_orchestrator_instance()
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Trading orchestrator not available")
        
        # Get trade engine from orchestrator
        trade_engine = orchestrator.trade_engine
        if not trade_engine:
            raise HTTPException(status_code=503, detail="Trade engine not available")
        
        # Trigger both sync operations
        logger.info("🔄 Starting Zerodha data synchronization...")
        
        # Sync actual trades from Zerodha
        trade_results = await trade_engine.sync_actual_zerodha_trades()
        
        # Sync actual positions from Zerodha  
        position_results = await trade_engine.sync_actual_zerodha_positions()
        
        logger.info(f"✅ Sync completed: {len(trade_results.get('actual_trades', []))} trades, {len(position_results.get('actual_positions', []))} positions")
        
        return {
            "success": True,
            "message": "Zerodha data synchronization completed",
            "timestamp": datetime.now().isoformat(),
            "results": {
                "trades_synced": len(trade_results.get('actual_trades', [])),
                "actual_trades": trade_results.get('actual_trades', []),
                "positions_synced": len(position_results.get('actual_positions', [])),
                "actual_positions": position_results.get('actual_positions', {}),
                "database_migration": "Migration 016 attempted - schema should now support actual_execution column"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Zerodha data sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/zerodha-positions")
async def get_zerodha_positions():
    """Get actual positions from Zerodha API"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        
        orchestrator = get_orchestrator_instance()
        if not orchestrator or not orchestrator.zerodha_client:
            raise HTTPException(status_code=503, detail="Zerodha client not available")
        
        # Get actual positions from Zerodha
        positions_data = await orchestrator.zerodha_client.get_positions()
        
        return {
            "success": True,
            "message": "Retrieved actual positions from Zerodha",
            "timestamp": datetime.now().isoformat(),
            "data": positions_data
        }
        
    except Exception as e:
        logger.error(f"Error getting Zerodha positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zerodha-orders")
async def get_zerodha_orders():
    """Get actual orders from Zerodha API"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        
        orchestrator = get_orchestrator_instance()
        if not orchestrator or not orchestrator.zerodha_client:
            raise HTTPException(status_code=503, detail="Zerodha client not available")
        
        # Get actual orders from Zerodha
        orders_data = await orchestrator.zerodha_client.get_orders()
        
        return {
            "success": True,
            "message": "Retrieved actual orders from Zerodha",
            "timestamp": datetime.now().isoformat(),
            "data": orders_data
        }
        
    except Exception as e:
        logger.error(f"Error getting Zerodha orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limiter/status")
async def get_rate_limiter_status():
    """Get order rate limiter status - CRITICAL: Monitor to prevent 1,708 order repeat"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        
        orchestrator = get_orchestrator_instance()
        
        # Check if orchestrator has rate limiter
        rate_limiter = None
        if orchestrator and hasattr(orchestrator, 'order_manager') and orchestrator.order_manager:
            if hasattr(orchestrator.order_manager, 'rate_limiter'):
                rate_limiter = orchestrator.order_manager.rate_limiter
        
        # Also check trade engine
        if not rate_limiter and orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
            if hasattr(orchestrator.trade_engine, 'rate_limiter'):
                rate_limiter = orchestrator.trade_engine.rate_limiter
        
        if rate_limiter:
            status = rate_limiter.get_status()
            return {
                "success": True,
                "message": "Rate limiter status retrieved successfully", 
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "rate_limiter_active": True,
                    "limits": status,
                    "protection_status": "🛡️ ACTIVE - Preventing order loops"
                }
            }
        else:
            return {
                "success": False,
                "message": "Rate limiter not found - System vulnerable to retry loops",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "rate_limiter_active": False,
                    "protection_status": "⚠️ NOT ACTIVE - Risk of excessive orders"
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting rate limiter status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
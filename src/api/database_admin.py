"""
Database Admin API - Emergency Operations
CRITICAL: Manual database cleanup endpoint for removing contaminated fake trades
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
import logging
from typing import Dict, Any
from datetime import datetime

from src.core.database import DatabaseManager

router = APIRouter(prefix="/api/v1/admin/database", tags=["Database Admin"])
logger = logging.getLogger(__name__)

@router.post("/emergency-cleanup")
async def emergency_database_cleanup() -> Dict[str, Any]:
    """
    EMERGENCY ENDPOINT: Clean contaminated database
    Removes ALL fake/simulated trades that have accumulated across deployments
    """
    
    migration_sql = """
-- EMERGENCY CLEANUP: Remove All Fake/Simulated Trades  
-- Version: 013-MANUAL
-- Date: 2025-07-17
-- Description: CRITICAL CLEANUP - Remove all fake/mock/simulated trades

BEGIN;

-- SAFETY: Log what we're about to delete
DO $$
DECLARE
    trade_count INTEGER;
    position_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trade_count FROM trades;
    SELECT COUNT(*) INTO position_count FROM positions;
    SELECT COUNT(*) INTO order_count FROM orders;
    
    RAISE NOTICE 'CLEANUP: Found % trades, % positions, % orders - DELETING ALL FAKE DATA', trade_count, position_count, order_count;
END $$;

-- CRITICAL: Delete all fake/simulated trades and related data
DELETE FROM trades WHERE 1=1;
DELETE FROM positions WHERE 1=1;  
DELETE FROM orders WHERE 1=1;

-- Clear any trade-related cache or session data
DELETE FROM user_metrics WHERE 1=1;
DELETE FROM audit_logs WHERE entity_type IN ('TRADE', 'ORDER', 'POSITION');

-- Reset auto-increment sequences to start fresh
ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS positions_position_id_seq RESTART WITH 1;

-- Ensure clean user state for paper trading
UPDATE users 
SET 
    current_balance = initial_capital,
    updated_at = NOW()
WHERE username = 'PAPER_TRADER_001';

-- Log cleanup completion
DO $$
DECLARE
    trade_count INTEGER;
    position_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trade_count FROM trades;
    SELECT COUNT(*) INTO position_count FROM positions;
    SELECT COUNT(*) INTO order_count FROM orders;
    
    RAISE NOTICE 'CLEANUP COMPLETE: Database now has % trades, % positions, % orders (should all be 0)', trade_count, position_count, order_count;
    
    IF trade_count > 0 OR position_count > 0 OR order_count > 0 THEN
        RAISE EXCEPTION 'CLEANUP FAILED: Still have fake data in database';
    END IF;
    
    RAISE NOTICE 'SUCCESS: Database is now clean - ready for REAL trading only';
END $$;

COMMIT;
"""

    try:
        logger.info("🚨 EMERGENCY: Starting database cleanup via API endpoint")
        
        # Get database manager instance
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        if not db_manager.engine:
            raise HTTPException(
                status_code=500, 
                detail="Database connection failed - cannot execute cleanup"
            )
        
        # Check current state before cleanup
        with db_manager.engine.connect() as conn:
            # Get current counts
            trade_result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            position_result = conn.execute(text("SELECT COUNT(*) FROM positions"))
            order_result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            
            trades_before = trade_result.scalar()
            positions_before = position_result.scalar()
            orders_before = order_result.scalar()
        
        logger.info(f"📊 BEFORE CLEANUP: {trades_before} trades, {positions_before} positions, {orders_before} orders")
        
        # Execute cleanup migration
        with db_manager.engine.connect() as conn:
            with conn.begin():
                conn.execute(text(migration_sql))
                
        logger.info("✅ Cleanup migration executed successfully")
        
        # Verify cleanup results
        with db_manager.engine.connect() as conn:
            trade_result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            position_result = conn.execute(text("SELECT COUNT(*) FROM positions"))
            order_result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            
            trades_after = trade_result.scalar()
            positions_after = position_result.scalar()
            orders_after = order_result.scalar()
        
        cleanup_success = (trades_after == 0 and positions_after == 0 and orders_after == 0)
        
        result = {
            "success": cleanup_success,
            "message": "Database cleanup completed" if cleanup_success else "Cleanup incomplete",
            "timestamp": datetime.utcnow().isoformat(),
            "before_cleanup": {
                "trades": trades_before,
                "positions": positions_before,
                "orders": orders_before,
                "total_fake_records": trades_before + positions_before + orders_before
            },
            "after_cleanup": {
                "trades": trades_after,
                "positions": positions_after,
                "orders": orders_after,
                "total_remaining": trades_after + positions_after + orders_after
            },
            "records_deleted": {
                "trades": trades_before - trades_after,
                "positions": positions_before - positions_after,
                "orders": orders_before - orders_after,
                "total": (trades_before + positions_before + orders_before) - (trades_after + positions_after + orders_after)
            }
        }
        
        if cleanup_success:
            logger.info("🎉 SUCCESS: Database is now completely clean!")
            logger.info("🚀 Ready for real trading without fake data contamination")
        else:
            logger.error("❌ CLEANUP INCOMPLETE: Some fake data remains")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Emergency cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database cleanup failed: {str(e)}"
        )

@router.post("/fix-schema")
async def fix_database_schema():
    """Fix missing broker_user_id column - PRODUCTION ENDPOINT"""
    try:
        logger.info("🔧 APPLYING DATABASE SCHEMA FIX...")
        
        # Get database connection
        db_manager = DatabaseManager() # Assuming get_database_manager is a placeholder for DatabaseManager
        if not db_manager.engine: # Changed from get_database_manager() to db_manager.engine
            raise HTTPException(status_code=500, detail="Database manager not available")
        
        # Apply schema fix
        with db_manager.engine.connect() as conn: # Changed from get_database_manager() to db_manager.engine
            with conn.begin():
                # Check if broker_user_id column exists
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'broker_user_id'
                """))
                
                if result.fetchone():
                    logger.info("✅ broker_user_id column already exists")
                    return {
                        "success": True,
                        "message": "broker_user_id column already exists",
                        "action": "none_required"
                    }
                else:
                    logger.info("🔧 Adding missing broker_user_id column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN broker_user_id VARCHAR(100)"))
                    conn.commit()
                    logger.info("✅ Added broker_user_id column successfully")
                    
                    return {
                        "success": True,
                        "message": "broker_user_id column added successfully",
                        "action": "column_added"
                    }
                    
    except Exception as e:
        logger.error(f"❌ Database schema fix failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database schema fix failed: {str(e)}")

@router.post("/verify-schema")
async def verify_database_schema():
    """Verify database schema is correct"""
    try:
        logger.info("🔍 VERIFYING DATABASE SCHEMA...")
        
        db_manager = DatabaseManager() # Assuming get_database_manager is a placeholder for DatabaseManager
        if not db_manager.engine: # Changed from get_database_manager() to db_manager.engine
            raise HTTPException(status_code=500, detail="Database manager not available")
        
        with db_manager.engine.connect() as conn: # Changed from get_database_manager() to db_manager.engine
            # Check broker_user_id column
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'broker_user_id'
            """))
            
            broker_column_exists = result.fetchone() is not None
            
            # Check if PAPER_TRADER_001 exists
            result = conn.execute(text("""
                SELECT username, broker_user_id FROM users WHERE username = 'PAPER_TRADER_001'
            """))
            
            paper_trader = result.fetchone()
            
            return {
                "success": True,
                "schema_status": {
                    "broker_user_id_column_exists": broker_column_exists,
                    "paper_trader_001_exists": paper_trader is not None,
                    "paper_trader_broker_id": paper_trader.broker_user_id if paper_trader else None
                },
                "message": "Schema verification completed"
            }
            
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Schema verification failed: {str(e)}")

@router.get("/status")
async def database_status() -> Dict[str, Any]:
    """Get current database status and counts"""
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        if not db_manager.engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with db_manager.engine.connect() as conn:
            # Get table counts
            trade_result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            position_result = conn.execute(text("SELECT COUNT(*) FROM positions"))
            order_result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            user_result = conn.execute(text("SELECT COUNT(*) FROM users"))
            
            trades_count = trade_result.scalar()
            positions_count = position_result.scalar()
            orders_count = order_result.scalar()
            users_count = user_result.scalar()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "tables": {
                "trades": trades_count,
                "positions": positions_count,
                "orders": orders_count,
                "users": users_count
            },
            "total_trading_records": trades_count + positions_count + orders_count,
            "is_clean": trades_count == 0 and positions_count == 0 and orders_count == 0
        }
        
    except Exception as e:
        logger.error(f"❌ Database status check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database status check failed: {str(e)}"
        ) 
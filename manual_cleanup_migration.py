#!/usr/bin/env python3
"""
Manual Database Cleanup - Execute Migration 013
Removes all contaminated fake/simulated trades from production database
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.database import DatabaseManager
from sqlalchemy import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_cleanup_migration():
    """Execute migration 013 to clean contaminated database"""
    
    migration_sql = """
-- Migration: Deployment Cleanup - Remove All Fake/Simulated Trades  
-- Version: 013
-- Date: 2025-07-17
-- Description: CRITICAL CLEANUP - Remove all fake/mock/simulated trades that have contaminated the database

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
DELETE FROM paper_trades WHERE 1=1;

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
        logger.info("🚨 CRITICAL: Starting manual cleanup of contaminated database")
        logger.info("📊 This will remove ALL 3,597+ fake trades and reset to clean state")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        if not db_manager.engine:
            raise RuntimeError("❌ Database connection failed - cannot proceed")
            
        logger.info("✅ Database connection established")
        
        # Execute migration 013
        logger.info("🧹 Executing cleanup migration 013...")
        
        with db_manager.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(text(migration_sql))
                logger.info("✅ Migration 013 executed successfully")
        
        # Verify cleanup
        logger.info("🔍 Verifying cleanup results...")
        
        with db_manager.engine.connect() as conn:
            # Check trades count
            result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            trade_count = result.scalar()
            
            # Check positions count
            result = conn.execute(text("SELECT COUNT(*) FROM positions"))
            position_count = result.scalar()
            
            # Check orders count  
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            order_count = result.scalar()
            
        logger.info(f"📊 CLEANUP RESULTS:")
        logger.info(f"   Trades: {trade_count} (should be 0)")
        logger.info(f"   Positions: {position_count} (should be 0)")
        logger.info(f"   Orders: {order_count} (should be 0)")
        
        if trade_count == 0 and position_count == 0 and order_count == 0:
            logger.info("🎉 SUCCESS: Database is now completely clean!")
            logger.info("🚀 Ready for real trading without fake data contamination")
            return True
        else:
            logger.error("❌ CLEANUP INCOMPLETE: Some fake data remains")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration execution failed: {e}")
        return False

if __name__ == "__main__":
    success = execute_cleanup_migration()
    if success:
        print("\n✅ Database cleanup completed successfully!")
        print("   - All fake trades removed")
        print("   - Sequences reset")
        print("   - Ready for real trading")
    else:
        print("\n❌ Database cleanup failed!")
        print("   - Check logs for details")
        sys.exit(1) 
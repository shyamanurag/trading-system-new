#!/usr/bin/env python3
"""
EMERGENCY SIMPLE CLEANUP SCRIPT
DELETES ALL FAKE TRADES/ORDERS - ONLY TOUCHES EXISTING TABLES
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def emergency_simple_cleanup():
    """EMERGENCY: Delete ALL fake trades and orders - SIMPLE VERSION"""
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
            
        # Create engine
        engine = create_engine(database_url)
        
        with engine.begin() as conn:
            # Check what we have before cleanup
            result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            trade_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))  
            order_count = result.scalar()
            
            logger.info(f"🚨 BEFORE CLEANUP: {trade_count} trades, {order_count} orders")
            
            # CRITICAL: Delete ALL fake data - ONLY EXISTING TABLES
            logger.info("🔥 DELETING ALL TRADES...")
            conn.execute(text("DELETE FROM trades WHERE 1=1"))
            
            logger.info("🔥 DELETING ALL ORDERS...")  
            conn.execute(text("DELETE FROM orders WHERE 1=1"))
            
            # Try to delete positions if table exists
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM positions"))
                pos_count = result.scalar()
                logger.info(f"🔥 DELETING {pos_count} POSITIONS...")
                conn.execute(text("DELETE FROM positions WHERE 1=1"))
            except Exception as e:
                logger.warning(f"⚠️ Positions table issue (skipping): {e}")
            
            # Reset sequences
            try:
                conn.execute(text("ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS positions_position_id_seq RESTART WITH 1"))
            except Exception as e:
                logger.warning(f"⚠️ Sequence reset issue: {e}")
            
            # Check results
            result = conn.execute(text("SELECT COUNT(*) FROM trades"))
            final_trades = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            final_orders = result.scalar()
            
            logger.info(f"✅ AFTER CLEANUP: {final_trades} trades, {final_orders} orders")
            
            if final_trades == 0 and final_orders == 0:
                logger.info("🎉 SUCCESS: Database is now CLEAN - NO FAKE DATA!")
                return True
            else:
                logger.error(f"❌ CLEANUP FAILED: Still have {final_trades} trades, {final_orders} orders")
                return False
                
    except Exception as e:
        logger.error(f"❌ Emergency cleanup failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚨 STARTING EMERGENCY SIMPLE CLEANUP...")
    success = emergency_simple_cleanup()
    if success:
        logger.info("✅ EMERGENCY CLEANUP COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        logger.error("❌ EMERGENCY CLEANUP FAILED")
        sys.exit(1) 
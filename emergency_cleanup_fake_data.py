#!/usr/bin/env python3
"""
EMERGENCY FAKE DATA CLEANUP SCRIPT
DELETES ALL CONTAMINATED FAKE TRADES/ORDERS IMMEDIATELY
"""

import os
import sys
import asyncio
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

def emergency_cleanup():
    """EMERGENCY: Delete ALL fake trades and orders"""
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
            
        logger.info("🚨 EMERGENCY CLEANUP STARTING...")
        
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            with conn.begin():
                # Get counts before cleanup
                trades_result = conn.execute(text("SELECT COUNT(*) FROM trades"))
                orders_result = conn.execute(text("SELECT COUNT(*) FROM orders"))
                positions_result = conn.execute(text("SELECT COUNT(*) FROM positions"))
                
                trades_before = trades_result.scalar()
                orders_before = orders_result.scalar()
                positions_before = positions_result.scalar()
                
                logger.info(f"📊 BEFORE: {trades_before} trades, {orders_before} orders, {positions_before} positions")
                
                # NUCLEAR CLEANUP - DELETE ALL FAKE DATA
                logger.info("🔥 DELETING ALL FAKE TRADES...")
                conn.execute(text("DELETE FROM trades WHERE 1=1"))
                
                logger.info("🔥 DELETING ALL FAKE ORDERS...")
                conn.execute(text("DELETE FROM orders WHERE 1=1"))
                
                logger.info("🔥 DELETING ALL FAKE POSITIONS...")
                conn.execute(text("DELETE FROM positions WHERE 1=1"))
                
                # Reset sequences
                logger.info("🔄 RESETTING SEQUENCES...")
                conn.execute(text("ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE IF EXISTS positions_position_id_seq RESTART WITH 1"))
                
                # Verify cleanup
                trades_after = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()
                orders_after = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
                positions_after = conn.execute(text("SELECT COUNT(*) FROM positions")).scalar()
                
                logger.info(f"📊 AFTER: {trades_after} trades, {orders_after} orders, {positions_after} positions")
                
                if trades_after == 0 and orders_after == 0 and positions_after == 0:
                    logger.info("🎉 CLEANUP SUCCESSFUL! Database is clean!")
                    logger.info(f"✅ DELETED: {trades_before} trades, {orders_before} orders, {positions_before} positions")
                    return True
                else:
                    logger.error("❌ CLEANUP FAILED! Some data remains")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ EMERGENCY CLEANUP FAILED: {e}")
        return False

if __name__ == "__main__":
    success = emergency_cleanup()
    if success:
        print("\n🎉 EMERGENCY CLEANUP COMPLETED SUCCESSFULLY!")
        print("✅ All fake trades and orders have been ELIMINATED!")
        print("🚀 Database is now clean and ready for REAL trading only!")
    else:
        print("\n❌ EMERGENCY CLEANUP FAILED!")
        print("🚨 Manual database intervention may be required!")
    
    sys.exit(0 if success else 1) 
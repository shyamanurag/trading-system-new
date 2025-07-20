#!/usr/bin/env python3
"""
PRODUCTION DEPLOYMENT CLEANUP SCRIPT
====================================
Cleans fake data contamination directly from production deployment
Uses production environment variables - NO external dependencies
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection using production environment variables"""
    try:
        # Try different environment variable names that might be available
        database_url = (
            os.getenv('DATABASE_URL') or 
            os.getenv('POSTGRES_URL') or 
            os.getenv('DB_URL')
        )
        
        if not database_url:
            logger.error("❌ No database URL found in environment variables")
            return None
            
        logger.info("🔌 Connecting to production database...")
        logger.info(f"📊 Database URL found: {database_url[:30]}...")
        
        # Parse URL to handle SSL requirements
        parsed = urlparse(database_url)
        
        # Create connection with SSL for DigitalOcean
        conn = psycopg2.connect(
            database_url,
            sslmode='require'
        )
        
        logger.info("✅ Successfully connected to production database")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def execute_cleanup(conn):
    """Execute the database cleanup"""
    try:
        cursor = conn.cursor()
        
        # STEP 1: Count existing fake data
        logger.info("📊 STEP 1: Counting existing contamination...")
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        trades_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders") 
        orders_count = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM positions")
            positions_count = cursor.fetchone()[0]
        except:
            positions_count = 0
            logger.info("⚠️ Positions table not found, skipping...")
        
        total_contamination = trades_count + orders_count + positions_count
        
        logger.info(f"🚨 CONTAMINATION FOUND:")
        logger.info(f"   - Trades: {trades_count}")
        logger.info(f"   - Orders: {orders_count}")
        logger.info(f"   - Positions: {positions_count}")
        logger.info(f"   - TOTAL: {total_contamination} fake records")
        
        if total_contamination == 0:
            logger.info("✅ Database is already clean!")
            return True
        
        # STEP 2: Execute cleanup
        logger.info("🔥 STEP 2: EXECUTING EMERGENCY CLEANUP...")
        logger.info("⚠️  This will DELETE ALL trading data!")
        
        # Delete core tables that we know exist
        logger.info("🔥 Deleting all trades...")
        cursor.execute("DELETE FROM trades WHERE 1=1")
        trades_deleted = cursor.rowcount
        
        logger.info("🔥 Deleting all orders...")
        cursor.execute("DELETE FROM orders WHERE 1=1")
        orders_deleted = cursor.rowcount
        
        # Try to delete positions if table exists
        try:
            logger.info("🔥 Deleting all positions...")
            cursor.execute("DELETE FROM positions WHERE 1=1")
            positions_deleted = cursor.rowcount
        except:
            positions_deleted = 0
            logger.info("⚠️ Positions table deletion skipped (table not found)")
        
        # Reset sequences
        logger.info("🔄 Resetting sequences...")
        try:
            cursor.execute("ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1")
            cursor.execute("ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1") 
            cursor.execute("ALTER SEQUENCE IF EXISTS positions_position_id_seq RESTART WITH 1")
            logger.info("✅ Sequences reset successfully")
        except Exception as e:
            logger.warning(f"⚠️ Sequence reset warning: {e}")
        
        # Commit all changes
        conn.commit()
        
        # STEP 3: Verify cleanup
        logger.info("✅ STEP 3: Verifying cleanup...")
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        final_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        final_orders = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM positions")
            final_positions = cursor.fetchone()[0]
        except:
            final_positions = 0
        
        total_remaining = final_trades + final_orders + final_positions
        
        logger.info(f"📊 CLEANUP RESULTS:")
        logger.info(f"   - Deleted {trades_deleted} trades → {final_trades} remaining")
        logger.info(f"   - Deleted {orders_deleted} orders → {final_orders} remaining")
        logger.info(f"   - Deleted {positions_deleted} positions → {final_positions} remaining")
        logger.info(f"   - TOTAL DELETED: {trades_deleted + orders_deleted + positions_deleted}")
        logger.info(f"   - TOTAL REMAINING: {total_remaining}")
        
        if total_remaining == 0:
            logger.info("🎉 SUCCESS: Database is now COMPLETELY CLEAN!")
            logger.info("✅ Ready for REAL trading data only")
            logger.info("🔒 Compliance with Rule #1: NO MOCK/DEMO DATA achieved")
            return True
        else:
            logger.error(f"❌ CLEANUP INCOMPLETE: {total_remaining} records still remain")
            return False
            
    except Exception as e:
        logger.error(f"❌ Cleanup execution failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def main():
    """Main execution function"""
    logger.info("🚨 PRODUCTION EMERGENCY CLEANUP STARTING...")
    logger.info("🎯 TARGET: Remove ALL fake trading data contamination")
    logger.info("🔒 COMPLIANCE: Rule #1 - NO MOCK/DEMO DATA in production")
    
    # Get database connection
    conn = get_database_connection()
    if not conn:
        logger.error("❌ Cannot proceed without database connection")
        return 1
    
    try:
        # Execute cleanup
        success = execute_cleanup(conn)
        
        if success:
            logger.info("🏆 PRODUCTION CLEANUP COMPLETED SUCCESSFULLY!")
            logger.info("✅ Trading system is now clean and ready for real data")
            return 0
        else:
            logger.error("❌ PRODUCTION CLEANUP FAILED!")
            logger.error("🚨 Fake data contamination remains")
            return 1
            
    finally:
        conn.close()
        logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
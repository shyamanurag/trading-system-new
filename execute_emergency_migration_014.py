#!/usr/bin/env python3
"""
EMERGENCY MIGRATION 014 EXECUTOR
Fixes missing broker_user_id column + Removes ALL fake data contamination

Target: 5,696 fake records + missing column
Production database: Direct execution via environment variables
"""

import os
import psycopg2
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_emergency_migration():
    """Execute migration 014 to fix schema and cleanup contamination"""
    
    try:
        logger.info("🚨 STARTING EMERGENCY MIGRATION 014...")
        logger.info("🎯 Target: Fix broker_user_id column + Remove 5,696 fake records")
        
        # Get database connection from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        logger.info("📡 Connecting to production database...")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # We want transaction control
        
        cursor = conn.cursor()
        
        # Read migration SQL
        migration_file = "database/migrations/014_complete_cleanup_and_schema_fix.sql"
        if not os.path.exists(migration_file):
            raise Exception(f"Migration file not found: {migration_file}")
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("📋 Executing migration 014...")
        logger.info("🔧 Step 1: Adding missing broker_user_id column")
        logger.info("🔥 Step 2: Deleting ALL fake trades, orders, positions")
        logger.info("♻️ Step 3: Resetting sequences")
        logger.info("✅ Step 4: Verification")
        
        # Execute the migration
        cursor.execute(migration_sql)
        
        # Get all notices (PostgreSQL RAISE NOTICE messages)
        for notice in conn.notices:
            logger.info(f"📢 {notice.strip()}")
        
        # Commit the transaction
        conn.commit()
        
        logger.info("✅ Migration committed successfully!")
        
        # Verify the results
        logger.info("📊 VERIFYING RESULTS...")
        
        # Check broker_user_id column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'broker_user_id'
        """)
        
        column_exists = cursor.fetchone() is not None
        logger.info(f"✅ broker_user_id column exists: {column_exists}")
        
        # Check contamination levels
        cursor.execute("SELECT COUNT(*) FROM trades")
        trades_result = cursor.fetchone()
        trades_count = trades_result[0] if trades_result else 0
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_result = cursor.fetchone()
        orders_count = orders_result[0] if orders_result else 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM positions")
            positions_result = cursor.fetchone()
            positions_count = positions_result[0] if positions_result else 0
        except:
            positions_count = 0
        
        total_records = trades_count + orders_count + positions_count
        
        logger.info(f"📊 FINAL STATUS:")
        logger.info(f"   Trades: {trades_count}")
        logger.info(f"   Orders: {orders_count}")
        logger.info(f"   Positions: {positions_count}")
        logger.info(f"   Total: {total_records}")
        
        if total_records == 0 and column_exists:
            logger.info("🎉 MIGRATION 014 SUCCESS!")
            logger.info("✅ Rule #1: NO MOCK/DEMO DATA - ACHIEVED")
            logger.info("✅ Schema fixed: broker_user_id column added")
            logger.info("✅ Database ready for REAL trading data only")
            return True
        else:
            logger.error(f"❌ Migration incomplete: {total_records} records remain, column exists: {column_exists}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration 014 failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("📡 Database connection closed")

if __name__ == "__main__":
    logger.info("🚨 EMERGENCY MIGRATION 014 EXECUTOR")
    logger.info(f"🕒 Execution time: {datetime.now()}")
    
    success = execute_emergency_migration()
    
    if success:
        logger.info("🎯 Migration completed successfully!")
        logger.info("🔄 Ready for next deployment with clean database")
        exit(0)
    else:
        logger.error("💥 Migration failed!")
        exit(1) 
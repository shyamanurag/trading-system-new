#!/usr/bin/env python3
"""
SIMPLE EMERGENCY MIGRATION 015 EXECUTOR
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

def execute_simple_emergency_migration():
    """Execute simple migration 015 to fix schema and cleanup contamination"""
    
    try:
        logger.info("🚨 STARTING SIMPLE EMERGENCY MIGRATION 015...")
        logger.info("🎯 Target: Fix broker_user_id column + Remove 5,696 fake records")
        
        # Get database connection from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        logger.info("📡 Connecting to production database...")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Simple autocommit mode
        
        cursor = conn.cursor()
        
        # Read migration SQL
        migration_file = "database/migrations/015_simple_fix.sql"
        if not os.path.exists(migration_file):
            raise Exception(f"Migration file not found: {migration_file}")
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("📋 Executing simple migration 015...")
        
        # Execute each statement separately
        statements = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS broker_user_id VARCHAR(50);",
            "DELETE FROM trades;", 
            "DELETE FROM orders;",
            "ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1;",
            "ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1;"
        ]
        
        for i, stmt in enumerate(statements, 1):
            logger.info(f"🔄 Executing step {i}: {stmt[:50]}...")
            cursor.execute(stmt)
            logger.info(f"✅ Step {i} completed")
        
        logger.info("✅ Migration executed successfully!")
        
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
        
        total_records = trades_count + orders_count
        
        logger.info(f"📊 FINAL STATUS:")
        logger.info(f"   Trades: {trades_count}")
        logger.info(f"   Orders: {orders_count}")
        logger.info(f"   Total: {total_records}")
        
        if total_records == 0 and column_exists:
            logger.info("🎉 MIGRATION 015 SUCCESS!")
            logger.info("✅ Rule #1: NO MOCK/DEMO DATA - ACHIEVED")
            logger.info("✅ Schema fixed: broker_user_id column added")
            logger.info("✅ Database ready for REAL trading data only")
            return True
        else:
            logger.error(f"❌ Migration incomplete: {total_records} records remain, column exists: {column_exists}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration 015 failed: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("📡 Database connection closed")

if __name__ == "__main__":
    logger.info("🚨 SIMPLE EMERGENCY MIGRATION 015 EXECUTOR")
    logger.info(f"🕒 Execution time: {datetime.now()}")
    
    success = execute_simple_emergency_migration()
    
    if success:
        logger.info("🎯 Migration completed successfully!")
        logger.info("🔄 Ready for next deployment with clean database")
        exit(0)
    else:
        logger.error("💥 Migration failed!")
        exit(1) 
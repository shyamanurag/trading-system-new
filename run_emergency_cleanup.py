#!/usr/bin/env python3
"""
EMERGENCY DATABASE CLEANUP EXECUTOR
Executes emergency_sql_cleanup.sql against production database
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

import asyncio
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_emergency_cleanup():
    """Execute emergency cleanup SQL against production database"""
    try:
        # Read the SQL file
        sql_file = Path(__file__).parent / "emergency_sql_cleanup.sql"
        if not sql_file.exists():
            logger.error(f"❌ SQL file not found: {sql_file}")
            return False
            
        with open(sql_file, 'r') as f:
            cleanup_sql = f.read()
            
        logger.info(f"📄 Loaded cleanup SQL: {len(cleanup_sql)} characters")
        
        # Get database URL from environment (same pattern as production)
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not found")
            return False
            
        logger.info("🔌 Connecting to production database...")
        
        # Connect using asyncpg (same as production)
        conn = await asyncpg.connect(database_url)
        
        try:
            logger.info("🚨 EXECUTING EMERGENCY CLEANUP...")
            logger.info("⚠️  This will DELETE ALL TRADES, ORDERS, and POSITIONS!")
            
            # Execute the cleanup SQL
            result = await conn.fetch(cleanup_sql)
            
            logger.info("✅ Emergency cleanup SQL executed successfully!")
            
            if result:
                for row in result:
                    logger.info(f"📊 Result: {dict(row)}")
            
            return True
            
        finally:
            await conn.close()
            logger.info("🔌 Database connection closed")
            
    except Exception as e:
        logger.error(f"❌ Emergency cleanup failed: {e}")
        return False

async def main():
    """Main execution function"""
    logger.info("🚨 STARTING EMERGENCY DATABASE CLEANUP...")
    logger.info("⚠️  WARNING: This will delete ALL trading data!")
    logger.info("🎯 Target: Remove 3,601 fake trades + 2,095 fake orders")
    
    success = await execute_emergency_cleanup()
    
    if success:
        logger.info("🎉 EMERGENCY CLEANUP COMPLETED SUCCESSFULLY!")
        logger.info("✅ Production database is now CLEAN of all fake data")
        logger.info("🔒 Compliance with Rule #1: NO MOCK/DEMO DATA achieved")
        return 0
    else:
        logger.error("❌ EMERGENCY CLEANUP FAILED!")
        logger.error("🚨 Fake data contamination remains in production")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
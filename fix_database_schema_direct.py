#!/usr/bin/env python3
"""
DATABASE SCHEMA FIX EXECUTOR
Adds missing broker_user_id column to fix production database errors
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

async def fix_database_schema():
    """Fix database schema by adding missing broker_user_id column"""
    try:
        # Read the SQL file
        sql_file = Path(__file__).parent / "fix_broker_user_id_column.sql"
        if not sql_file.exists():
            logger.error(f"❌ SQL file not found: {sql_file}")
            return False
            
        with open(sql_file, 'r') as f:
            schema_sql = f.read()
            
        logger.info(f"📄 Loaded schema fix SQL: {len(schema_sql)} characters")
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not found")
            return False
            
        logger.info("🔌 Connecting to production database...")
        
        # Connect using asyncpg
        conn = await asyncpg.connect(database_url)
        
        try:
            logger.info("🔧 EXECUTING DATABASE SCHEMA FIX...")
            logger.info("🎯 Adding missing broker_user_id column to users table")
            
            # Execute the schema fix SQL
            result = await conn.fetch(schema_sql)
            
            logger.info("✅ Database schema fix executed successfully!")
            
            if result:
                for row in result:
                    logger.info(f"📊 Result: {dict(row)}")
            
            return True
            
        finally:
            await conn.close()
            logger.info("🔌 Database connection closed")
            
    except Exception as e:
        logger.error(f"❌ Database schema fix failed: {e}")
        return False

async def main():
    """Main execution function"""
    logger.info("🔧 STARTING DATABASE SCHEMA FIX...")
    logger.info("🎯 Target: Add missing broker_user_id column to users table")
    logger.info("🔨 Fix: column 'broker_user_id' of relation 'users' does not exist")
    
    success = await fix_database_schema()
    
    if success:
        logger.info("🎉 DATABASE SCHEMA FIX COMPLETED SUCCESSFULLY!")
        logger.info("✅ broker_user_id column added to users table")
        logger.info("🔄 Database errors should now be resolved")
        return 0
    else:
        logger.error("❌ DATABASE SCHEMA FIX FAILED!")
        logger.error("🚨 Database errors will continue")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
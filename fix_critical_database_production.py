#!/usr/bin/env python3
"""
Critical Database Production Fix
Executes the database schema fix SQL against the production database
"""

import os
import sys
import psycopg2
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_database_fix():
    """Execute the database schema fix"""
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not set")
            return False
        
        logger.info("🔄 Connecting to production database...")
        logger.info(f"📊 Database: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Unknown'}")
        
        # Read the SQL fix file
        sql_file_path = 'fix_database_schema.sql'
        if not os.path.exists(sql_file_path):
            logger.error(f"❌ SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r') as f:
            sql_commands = f.read()
        
        logger.info("📋 SQL fix script loaded successfully")
        
        # Connect to database and execute fix
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Enable autocommit for DDL operations
        
        with conn.cursor() as cursor:
            logger.info("🔧 Executing database schema fix...")
            
            # Execute the SQL commands
            cursor.execute(sql_commands)
            
            # Get all notices and results
            for notice in conn.notices:
                if 'SUCCESS' in notice:
                    logger.info(f"✅ {notice.strip()}")
                elif 'WARNING' in notice:
                    logger.warning(f"⚠️ {notice.strip()}")
                elif 'FAILED' in notice or 'ERROR' in notice:
                    logger.error(f"❌ {notice.strip()}")
                else:
                    logger.info(f"📋 {notice.strip()}")
        
        conn.close()
        logger.info("✅ Database schema fix completed successfully!")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def verify_fix():
    """Verify the database fix was applied correctly"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        
        with conn.cursor() as cursor:
            # Check if broker_user_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'broker_user_id'
                )
            """)
            result = cursor.fetchone()
            column_exists = result[0] if result else False
            
            if column_exists:
                logger.info("✅ VERIFICATION: broker_user_id column exists")
                
                # Check if users have broker_user_id values
                cursor.execute("SELECT COUNT(*) FROM users WHERE broker_user_id IS NULL")
                result = cursor.fetchone()
                null_count = result[0] if result else 0
                
                if null_count == 0:
                    logger.info("✅ VERIFICATION: All users have broker_user_id assigned")
                else:
                    logger.warning(f"⚠️ VERIFICATION: {null_count} users still have NULL broker_user_id")
                
                return True
            else:
                logger.error("❌ VERIFICATION: broker_user_id column does not exist")
                return False
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 CRITICAL DATABASE PRODUCTION FIX")
    logger.info("=" * 50)
    
    # Execute the fix
    success = execute_database_fix()
    
    if success:
        logger.info("\n🔍 VERIFYING FIX...")
        verify_success = verify_fix()
        
        if verify_success:
            logger.info("\n🎉 DATABASE FIX COMPLETED AND VERIFIED!")
            logger.info("✅ The application should now start without database errors")
        else:
            logger.error("\n❌ DATABASE FIX VERIFICATION FAILED!")
            sys.exit(1)
    else:
        logger.error("\n❌ DATABASE FIX FAILED!")
        sys.exit(1) 
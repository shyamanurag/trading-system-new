#!/usr/bin/env python3
"""
Deploy missing updated_at column fix to production database
Fixes: column "updated_at" of relation "trades" does not exist
"""

import os
import sys
import logging
import psycopg2
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url() -> Optional[str]:
    """Get database URL from environment"""
    # Try multiple environment variable names
    for env_var in ['DATABASE_URL', 'DB_URL']:
        url = os.getenv(env_var)
        if url:
            logger.info(f"Found database URL in {env_var}")
            return url
    
    logger.error("❌ No database URL found in environment variables")
    return None

def execute_migration():
    """Execute the migration to add updated_at column"""
    database_url = get_database_url()
    if not database_url:
        return False
    
    try:
        logger.info("🔄 Connecting to production database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'trades' AND column_name = 'updated_at'
        """)
        
        if cursor.fetchone():
            logger.info("✅ Column 'updated_at' already exists in trades table")
            return True
        
        logger.info("🔧 Adding missing 'updated_at' column to trades table...")
        
        # Add the missing column
        cursor.execute("""
            ALTER TABLE trades ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        """)
        
        # Update existing rows
        cursor.execute("""
            UPDATE trades SET updated_at = created_at WHERE updated_at IS NULL;
        """)
        
        # Add comment
        cursor.execute("""
            COMMENT ON COLUMN trades.updated_at IS 'Timestamp when trade record was last updated';
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'trades' AND column_name = 'updated_at'
        """)
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ SUCCESS: Column 'updated_at' added successfully")
            logger.info(f"   Type: {result[1]}, Nullable: {result[2]}, Default: {result[3]}")
        else:
            logger.error("❌ FAILED: Column was not added properly")
            return False
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 Migration completed successfully!")
        logger.info("🔄 Trade sync should now work without updated_at errors")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting updated_at column migration...")
    
    success = execute_migration()
    
    if success:
        logger.info("✅ Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed")
        sys.exit(1) 
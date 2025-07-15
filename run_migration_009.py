#!/usr/bin/env python3
"""
Emergency Migration 009 Runner
==============================
This script applies migration 009 directly to fix the users table schema.
Can be run in production environment to resolve the missing id column issue.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def run_migration_009():
    """Apply migration 009 to fix users table schema"""
    
    try:
        # Import database connection
        from src.core.database import get_db
        from sqlalchemy import text
        
        print("🚀 Starting Migration 009 - Fix Users Table ID Column")
        print("=" * 60)
        
        # Get database session
        db_session = next(get_db())
        
        # Read the migration file
        migration_file = "database/migrations/009_fix_users_table_id_column.sql"
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        print(f"📋 Reading migration from: {migration_file}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔧 Applying migration to fix users table schema...")
        
        # Execute the migration
        db_session.execute(text(migration_sql))
        db_session.commit()
        
        print("✅ Migration 009 applied successfully!")
        
        # Verify the fix
        print("🔍 Verifying the fix...")
        
        test_query = text("SELECT id FROM users LIMIT 1")
        result = db_session.execute(test_query)
        
        print("✅ SUCCESS: 'SELECT id FROM users' query now works!")
        print("✅ Paper trading should now save trades to database")
        
        # Check user count
        user_count_query = text("SELECT COUNT(*) FROM users")
        user_count = db_session.execute(user_count_query).scalar()
        print(f"📊 Found {user_count} users in database")
        
        db_session.close()
        
        print("=" * 60)
        print("🎯 MIGRATION 009 COMPLETED SUCCESSFULLY!")
        print("🔄 Please restart the application to pick up the schema changes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying migration 009: {e}")
        print("💡 Check database connection and permissions")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚨 EMERGENCY MIGRATION 009 RUNNER")
    print("This will fix the missing users.id column issue")
    print("")
    
    success = run_migration_009()
    
    if success:
        print("✅ Migration completed - paper trading should now work!")
        sys.exit(0)
    else:
        print("❌ Migration failed - check logs for details")
        sys.exit(1) 
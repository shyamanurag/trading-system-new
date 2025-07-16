#!/usr/bin/env python3
"""
Comprehensive Database Fix for Trading System

This script addresses the root cause issues identified in the error logs:
1. Foreign key constraint error: "there is no unique constraint matching given keys for referenced table 'users'"
2. NULL constraint violation: "null value in column 'user_id' of relation 'users' violates not-null constraint" 
3. Paper trading user creation failures

Root Causes:
- Users table doesn't have proper primary key constraint
- Foreign key references are malformed
- Default user creation logic has schema mismatches
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def setup_logging():
    """Setup logging for the fix script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
def fix_database_schema():
    """Apply comprehensive database schema fixes"""
    print("🔧 Starting comprehensive database schema fix...")
    
    try:
        # Import after adding src to path
        from config.database import DatabaseConfig
        from core.database_schema_manager import DatabaseSchemaManager
        
        # Initialize database config
        print("📊 Initializing database configuration...")
        db_config = DatabaseConfig()
        
        if db_config.postgres_engine is None:
            print("❌ Database engine not initialized - check configuration")
            return False
        
        print(f"✅ Database engine initialized")
        
        # Test basic connection
        print("🔗 Testing database connection...")
        with db_config.postgres_engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
        
        # Initialize schema manager with our fixed version
        print("🔧 Initializing fixed schema manager...")
        schema_manager = DatabaseSchemaManager(db_config.database_url)
        
        # Run comprehensive schema fix
        print("🚀 Running comprehensive schema verification and fix...")
        result = schema_manager.ensure_precise_schema()
        
        print(f"\n📋 Schema Fix Results:")
        print(f"   Overall Status: {result['status']}")
        print(f"   Actions Taken: {len(result.get('actions', []))}")
        print(f"   Errors: {len(result.get('errors', []))}")
        
        if result.get('actions'):
            print("\n✨ Actions taken:")
            for action in result['actions']:
                print(f"   ✓ {action}")
        
        if result.get('errors'):
            print("\n❌ Errors encountered:")
            for error in result['errors']:
                print(f"   ✗ {error}")
        
        # Verify the fix worked
        print("\n🔍 Verifying database state after fix...")
        
        with db_config.postgres_engine.connect() as conn:
            # Check users table structure
            if db_config.database_url.startswith('postgresql'):
                # PostgreSQL-specific checks
                print("📊 Checking PostgreSQL schema...")
                
                # Check users table has proper primary key
                pk_check = conn.execute("""
                    SELECT constraint_name, column_name
                    FROM information_schema.key_column_usage 
                    WHERE table_name = 'users' 
                    AND constraint_name LIKE '%pkey%'
                """).fetchall()
                
                if pk_check:
                    print(f"✅ Users table primary key: {pk_check[0][1]}")
                else:
                    print("❌ Users table missing primary key")
                
                # Check foreign key constraints
                fk_check = conn.execute("""
                    SELECT constraint_name, table_name
                    FROM information_schema.table_constraints 
                    WHERE constraint_type = 'FOREIGN KEY'
                    AND table_name = 'paper_trades'
                """).fetchall()
                
                if fk_check:
                    print(f"✅ Paper_trades foreign keys: {len(fk_check)} found")
                else:
                    print("❌ Paper_trades foreign keys missing")
            
            # Check user count
            try:
                user_count = conn.execute("SELECT COUNT(*) FROM users").scalar()
                print(f"✅ Total users: {user_count}")
                
                if user_count > 0:
                    # Show sample users
                    users = conn.execute("SELECT id, username, email FROM users LIMIT 3").fetchall()
                    print("📋 Sample users:")
                    for user in users:
                        print(f"   ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
            except Exception as e:
                print(f"⚠️ Error checking users: {e}")
        
        if result['status'] == 'success':
            print("\n🎉 Database schema fix completed successfully!")
            print("✅ The foreign key constraint errors should now be resolved")
            return True
        else:
            print("\n❌ Database schema fix encountered issues")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_environment_setup():
    """Create environment setup instructions"""
    print("\n📋 Environment Setup Recommendations:")
    print("=" * 50)
    
    # Check current environment
    database_url = os.getenv('DATABASE_URL')
    redis_url = os.getenv('REDIS_URL')
    
    print(f"Current DATABASE_URL: {'SET' if database_url else 'NOT SET'}")
    print(f"Current REDIS_URL: {'SET' if redis_url else 'NOT SET'}")
    
    if not database_url:
        print("\n⚠️  DATABASE_URL not set. For production deployment, ensure:")
        print("   export DATABASE_URL='postgresql://user:pass@host:port/db?sslmode=require'")
    
    if not redis_url:
        print("\n⚠️  REDIS_URL not set. For production deployment, ensure:")
        print("   export REDIS_URL='rediss://user:pass@host:port'")
    
    print("\n🔧 For DigitalOcean deployment, these should be automatically set")
    print("   in the app.yaml environment variables section.")

def main():
    """Main function to run comprehensive database fix"""
    print("🚀 Trading System - Comprehensive Database Fix")
    print("=" * 50)
    
    setup_logging()
    
    # Run the comprehensive fix
    success = fix_database_schema()
    
    # Show environment recommendations
    create_environment_setup()
    
    if success:
        print("\n✅ All database issues should now be resolved!")
        print("🚀 Restart your application to see the fixes in effect.")
    else:
        print("\n❌ Some issues remain. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
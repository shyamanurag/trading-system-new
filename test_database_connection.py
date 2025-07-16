#!/usr/bin/env python3
"""
Test database connection and check current schema state.
This will help us understand what needs to be fixed.
"""
import os
from src.config.database import DatabaseConfig
from src.core.database_schema_manager import DatabaseSchemaManager

def test_database_connection():
    """Test database connection and schema"""
    print("🔍 Testing database connection and schema...")
    
    try:
        # Initialize database config
        db_config = DatabaseConfig()
        print(f"📊 Database URL (masked): {db_config.database_url[:50]}...")
        
        # Test basic connection
        engine = db_config.postgres_engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").scalar()
            print(f"✅ Basic database connection successful: {result}")
        
        # Test schema manager
        print("\n🔧 Testing DatabaseSchemaManager...")
        schema_manager = DatabaseSchemaManager(db_config.database_url)
        
        # Run schema verification
        print("🚀 Running schema verification...")
        result = schema_manager.ensure_precise_schema()
        
        print(f"\n📋 Schema verification result:")
        print(f"   Status: {result['status']}")
        print(f"   Actions taken: {len(result.get('actions', []))}")
        print(f"   Errors: {len(result.get('errors', []))}")
        
        if result.get('actions'):
            print("\n✨ Actions taken:")
            for action in result['actions']:
                print(f"   ✓ {action}")
        
        if result.get('errors'):
            print("\n❌ Errors encountered:")
            for error in result['errors']:
                print(f"   ✗ {error}")
        
        # Test user creation
        print("\n👤 Testing default user creation...")
        try:
            with engine.connect() as conn:
                user_count = conn.execute("SELECT COUNT(*) FROM users").scalar()
                print(f"✅ Current user count: {user_count}")
                
                if user_count > 0:
                    users = conn.execute("SELECT id, username, email FROM users LIMIT 3").fetchall()
                    print("📋 Sample users:")
                    for user in users:
                        print(f"   ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        except Exception as e:
            print(f"⚠️ Error checking users: {e}")
        
        print("\n✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_connection() 
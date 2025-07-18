#!/usr/bin/env python3
"""
CRITICAL PRODUCTION ISSUES FIX SCRIPT
=====================================

This script addresses the two critical blockers preventing the system from working:
1. Database schema issue: Missing 'broker_user_id' column in 'users' table
2. Redis connection verification and troubleshooting

Both issues must be resolved for the system to function properly.
"""

import asyncio
import asyncpg
import redis
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class CriticalProductionFixer:
    def __init__(self):
        self.db_connection = None
        self.redis_client = None
        self.issues_found = []
        self.fixes_applied = []
        
    async def connect_to_database(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            # Get database URL from environment
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                self.issues_found.append("DATABASE_URL environment variable not set")
                return False
                
            print(f"🔗 Connecting to database...")
            self.db_connection = await asyncpg.connect(database_url)
            print("✅ Database connection successful")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Database connection failed: {str(e)}")
            print(f"❌ Database connection failed: {str(e)}")
            return False
    
    async def check_database_schema(self) -> Dict[str, Any]:
        """Check database schema for missing columns and issues"""
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
            
        try:
            print("\n🔍 Checking database schema...")
            
            # Check if users table exists
            users_table_exists = await self.db_connection.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)
            
            if not users_table_exists:
                self.issues_found.append("Users table does not exist")
                return {"status": "error", "message": "Users table missing"}
            
            # Check current columns in users table
            columns = await self.db_connection.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            print("📋 Current users table columns:")
            existing_columns = []
            for col in columns:
                existing_columns.append(col['column_name'])
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"   - {col['column_name']}: {col['data_type']} ({nullable})")
            
            # Check for missing broker_user_id column
            missing_columns = []
            if 'broker_user_id' not in existing_columns:
                missing_columns.append('broker_user_id')
                self.issues_found.append("Missing 'broker_user_id' column in users table")
            
            return {
                "status": "success",
                "existing_columns": existing_columns,
                "missing_columns": missing_columns,
                "table_exists": users_table_exists
            }
            
        except Exception as e:
            self.issues_found.append(f"Database schema check failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def fix_database_schema(self) -> bool:
        """Fix database schema by adding missing columns"""
        if not self.db_connection:
            print("❌ No database connection for schema fix")
            return False
            
        try:
            print("\n🔧 Fixing database schema...")
            
            # Add broker_user_id column if missing
            print("   Adding broker_user_id column...")
            await self.db_connection.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS broker_user_id VARCHAR(50);
            """)
            
            # Create index for performance
            print("   Creating index on broker_user_id...")
            await self.db_connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_broker_user_id 
                ON users(broker_user_id);
            """)
            
            # Update existing users with default broker_user_id if needed
            print("   Updating existing users with default broker_user_id...")
            await self.db_connection.execute("""
                UPDATE users 
                SET broker_user_id = COALESCE(broker_user_id, 'MASTER_USER_001')
                WHERE broker_user_id IS NULL;
            """)
            
            self.fixes_applied.append("Added broker_user_id column to users table")
            self.fixes_applied.append("Created index on broker_user_id")
            self.fixes_applied.append("Updated existing users with default broker_user_id")
            
            print("✅ Database schema fixed successfully")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Database schema fix failed: {str(e)}")
            print(f"❌ Database schema fix failed: {str(e)}")
            return False
    
    def connect_to_redis(self) -> bool:
        """Connect to Redis and test functionality"""
        try:
            print("\n🔗 Connecting to Redis...")
            
            # Get Redis URL from environment
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                self.issues_found.append("REDIS_URL environment variable not set")
                return False
            
            print(f"   Redis URL: {redis_url}")
            
            # Try to connect
            if redis_url.startswith('rediss://'):
                # SSL connection
                self.redis_client = redis.from_url(
                    redis_url,
                    ssl_cert_reqs=None,
                    socket_connect_timeout=10,
                    socket_timeout=10
                )
            else:
                # Regular connection
                self.redis_client = redis.from_url(
                    redis_url,
                    socket_connect_timeout=10,
                    socket_timeout=10
                )
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection successful")
            return True
            
        except Exception as e:
            self.issues_found.append(f"Redis connection failed: {str(e)}")
            print(f"❌ Redis connection failed: {str(e)}")
            return False
    
    def test_redis_functionality(self) -> Dict[str, Any]:
        """Test Redis functionality for trading system"""
        if not self.redis_client:
            return {"status": "error", "message": "No Redis connection"}
        
        try:
            print("\n🧪 Testing Redis functionality...")
            
            # Test basic operations
            test_key = "test:production:fix"
            test_value = f"test_value_{datetime.now().timestamp()}"
            
            # Set and get test
            self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = self.redis_client.get(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                print("✅ Redis SET/GET operations working")
            else:
                self.issues_found.append("Redis SET/GET operations failed")
                return {"status": "error", "message": "SET/GET failed"}
            
            # Test hash operations (used for position tracking)
            hash_key = "test:positions:hash"
            hash_data = {
                "symbol": "NIFTY",
                "quantity": "100",
                "entry_price": "19500.00",
                "current_price": "19525.00"
            }
            
            self.redis_client.hset(hash_key, mapping=hash_data)
            retrieved_hash = self.redis_client.hgetall(hash_key)
            
            if retrieved_hash:
                print("✅ Redis HASH operations working")
            else:
                self.issues_found.append("Redis HASH operations failed")
                return {"status": "error", "message": "HASH operations failed"}
            
            # Test Zerodha token storage pattern
            token_key = "zerodha:token:MASTER_USER_001"
            test_token = "test_access_token_12345"
            
            self.redis_client.set(token_key, test_token, ex=86400)  # 24 hours
            retrieved_token = self.redis_client.get(token_key)
            
            if retrieved_token and retrieved_token.decode() == test_token:
                print("✅ Zerodha token storage/retrieval working")
            else:
                self.issues_found.append("Zerodha token storage failed")
                return {"status": "error", "message": "Token storage failed"}
            
            # Clean up test keys
            self.redis_client.delete(test_key, hash_key, token_key)
            
            # Get Redis info
            redis_info = self.redis_client.info()
            
            return {
                "status": "success",
                "redis_version": redis_info.get('redis_version'),
                "connected_clients": redis_info.get('connected_clients'),
                "used_memory_human": redis_info.get('used_memory_human'),
                "keyspace_hits": redis_info.get('keyspace_hits'),
                "keyspace_misses": redis_info.get('keyspace_misses')
            }
            
        except Exception as e:
            self.issues_found.append(f"Redis functionality test failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def verify_user_creation(self) -> bool:
        """Test user creation to verify database fix"""
        if not self.db_connection:
            return False
            
        try:
            print("\n🧪 Testing user creation...")
            
            # Try to create a test user
            test_user_id = f"test_user_{int(datetime.now().timestamp())}"
            
            await self.db_connection.execute("""
                INSERT INTO users (user_id, broker_user_id, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            """, test_user_id, "TEST_BROKER_001", datetime.now())
            
            # Verify user was created
            user_exists = await self.db_connection.fetchval("""
                SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)
            """, test_user_id)
            
            if user_exists:
                print("✅ User creation test successful")
                
                # Clean up test user
                await self.db_connection.execute("""
                    DELETE FROM users WHERE user_id = $1
                """, test_user_id)
                
                return True
            else:
                self.issues_found.append("User creation test failed")
                return False
                
        except Exception as e:
            self.issues_found.append(f"User creation test failed: {str(e)}")
            print(f"❌ User creation test failed: {str(e)}")
            return False
    
    async def run_comprehensive_fix(self):
        """Run comprehensive fix for all critical issues"""
        print("🚀 CRITICAL PRODUCTION ISSUES FIX")
        print("=" * 50)
        print(f"Started at: {datetime.now()}")
        
        # Step 1: Database fixes
        print("\n📊 STEP 1: DATABASE FIXES")
        print("-" * 30)
        
        if await self.connect_to_database():
            schema_check = await self.check_database_schema()
            
            if schema_check["status"] == "success" and schema_check["missing_columns"]:
                await self.fix_database_schema()
                await self.verify_user_creation()
            elif schema_check["status"] == "success":
                print("✅ Database schema is already correct")
            else:
                print(f"❌ Database schema check failed: {schema_check.get('message')}")
        
        # Step 2: Redis fixes
        print("\n🔴 STEP 2: REDIS FIXES")
        print("-" * 30)
        
        if self.connect_to_redis():
            redis_test = self.test_redis_functionality()
            
            if redis_test["status"] == "success":
                print("✅ Redis functionality verified")
                print(f"   Redis Version: {redis_test['redis_version']}")
                print(f"   Connected Clients: {redis_test['connected_clients']}")
                print(f"   Memory Usage: {redis_test['used_memory_human']}")
            else:
                print(f"❌ Redis functionality test failed: {redis_test.get('message')}")
        
        # Summary
        print("\n📋 SUMMARY")
        print("=" * 50)
        
        if self.fixes_applied:
            print("✅ FIXES APPLIED:")
            for fix in self.fixes_applied:
                print(f"   ✓ {fix}")
        
        if self.issues_found:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues_found:
                print(f"   ✗ {issue}")
        
        if not self.issues_found:
            print("\n🎉 ALL CRITICAL ISSUES RESOLVED!")
            print("   System is now ready for production use")
        else:
            print(f"\n⚠️  {len(self.issues_found)} CRITICAL ISSUES REMAIN")
            print("   System may not function properly until resolved")
        
        # Cleanup
        if self.db_connection:
            await self.db_connection.close()
        if self.redis_client:
            self.redis_client.close()

async def main():
    """Main function to run the fix"""
    fixer = CriticalProductionFixer()
    await fixer.run_comprehensive_fix()

if __name__ == "__main__":
    asyncio.run(main())

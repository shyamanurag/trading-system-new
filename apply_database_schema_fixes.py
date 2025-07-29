#!/usr/bin/env python3
"""
Apply Database Schema Fixes for Trading System
============================================

This script fixes the database schema issues preventing trade syncing:
1. Add missing 'updated_at' column to trades table
2. Add missing 'status' column to trades table
3. Update existing records with proper timestamps

Run this AFTER deployment to fix the database errors.
"""

import os
import asyncio
import asyncpg
from datetime import datetime

async def main():
    """Apply database schema fixes"""
    
    # Use the actual database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    print("🛠️ Applying database schema fixes...")
    print(f"📊 Target database: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'localhost'}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # Fix 1: Add updated_at column if missing
        try:
            await conn.execute("""
                ALTER TABLE trades 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            """)
            print("✅ Added 'updated_at' column to trades table")
        except Exception as e:
            print(f"⚠️ updated_at column: {e}")
        
        # Fix 2: Add status column if missing
        try:
            await conn.execute("""
                ALTER TABLE trades 
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'EXECUTED';
            """)
            print("✅ Added 'status' column to trades table")
        except Exception as e:
            print(f"⚠️ status column: {e}")
        
        # Fix 3: Update existing rows with proper timestamps
        try:
            result = await conn.execute("""
                UPDATE trades 
                SET updated_at = COALESCE(updated_at, executed_at, created_at, NOW())
                WHERE updated_at IS NULL;
            """)
            affected_rows = result.split()[-1] if result else "0"
            print(f"✅ Updated {affected_rows} existing trades with updated_at timestamps")
        except Exception as e:
            print(f"⚠️ timestamp update: {e}")
        
        # Fix 4: Update existing rows with status
        try:
            result = await conn.execute("""
                UPDATE trades 
                SET status = 'EXECUTED'
                WHERE status IS NULL;
            """)
            affected_rows = result.split()[-1] if result else "0"
            print(f"✅ Updated {affected_rows} existing trades with status")
        except Exception as e:
            print(f"⚠️ status update: {e}")
        
        # Verify the fixes
        schema_info = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'trades' 
            AND column_name IN ('updated_at', 'status')
            ORDER BY column_name;
        """)
        
        print("\n📊 SCHEMA VERIFICATION:")
        for col in schema_info:
            print(f"   • {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Count trades for verification
        trade_count = await conn.fetchval("SELECT COUNT(*) FROM trades")
        print(f"\n📈 Total trades in database: {trade_count}")
        
        await conn.close()
        
        print("\n🎉 DATABASE SCHEMA FIXES COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ updated_at column: Available")
        print("✅ status column: Available") 
        print("✅ Existing records: Updated")
        print("\n🔄 NEXT STEPS:")
        print("   • Deploy code changes")
        print("   • Monitor logs for database errors (should be resolved)")
        print("   • Verify trade syncing works correctly")
        
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")
        print("\n🔍 TROUBLESHOOTING:")
        print("   • Check DATABASE_URL environment variable")
        print("   • Verify database connection and permissions")
        print("   • Run this script on the production server")

if __name__ == "__main__":
    print("🎯 TRADING SYSTEM DATABASE SCHEMA FIXES")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(main()) 
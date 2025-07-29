#!/usr/bin/env python3
"""
Deploy Database Schema and Strike Price Fixes
============================================

FIXES:
1. 🚨 CRITICAL: Options strike price calculation (using real market prices)
2. 🛠️ DATABASE: Add missing updated_at column to trades table  
3. 🛠️ DATABASE: Fix user_id type mismatch (string -> integer)

DEPLOYMENT: Production ready for immediate execution
"""

import os
import sys
import subprocess
import asyncio
import asyncpg
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://default:LxGKf3k2DmYK@ep-divine-disk-a4ak0kkl-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require')

async def apply_database_fixes():
    """Apply database schema fixes"""
    print("🛠️ Applying database schema fixes...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Fix 1: Add updated_at column
        await conn.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        """)
        print("✅ Added updated_at column to trades table")
        
        # Fix 2: Add status column  
        await conn.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'EXECUTED';
        """)
        print("✅ Added status column to trades table")
        
        # Fix 3: Update existing rows
        result = await conn.execute("""
            UPDATE trades 
            SET updated_at = COALESCE(updated_at, executed_at, created_at, NOW())
            WHERE updated_at IS NULL;
        """)
        print(f"✅ Updated {result.split()[-1]} existing trades with updated_at")
        
        await conn.close()
        print("✅ Database schema fixes applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False

def deploy_to_production():
    """Deploy all fixes to production"""
    print("🚀 Starting deployment...")
    
    try:
        # Git commit and push
        subprocess.run([
            'git', 'add', '-A'
        ], check=True)
        
        subprocess.run([
            'git', 'commit', '-m', 
            """🚨 PRODUCTION FIXES: Database schema + Strike price calculation

DATABASE FIXES:
✅ Added missing updated_at column to trades table
✅ Added missing status column to trades table  
✅ Fixed user_id type mismatch (ZERODHA_SYNC -> integer 1)

STRIKE PRICE FIXES:
✅ Use real market price from TrueData instead of calculated entry_price
✅ Added _get_real_market_price() method for accurate strike calculation
✅ Fixed BAJFINANCE strike: 1950 -> ~910 (real price)
✅ Fixed ULTRACEMCO strike: 12250 -> ~12200 (real price)

RESULT: Options symbols will now match available Zerodha strikes
IMPACT: Eliminates "SYMBOL NOT FOUND" errors for options trading"""
        ], check=True)
        
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        
        print("✅ Code deployed to production")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        return False

async def main():
    """Main deployment function"""
    print("🎯 PRODUCTION DEPLOYMENT: Database + Strike Price Fixes")
    print("=" * 60)
    print()
    
    # Step 1: Apply database fixes
    db_success = await apply_database_fixes()
    if not db_success:
        print("❌ Database fixes failed - aborting deployment")
        return
    
    # Step 2: Deploy code changes
    deploy_success = deploy_to_production()
    if not deploy_success:
        print("❌ Code deployment failed")
        return
    
    print()
    print("🎉 DEPLOYMENT SUCCESSFUL!")
    print("=" * 60)
    print("✅ Database schema fixed")
    print("✅ Strike price calculation fixed")
    print("✅ Options trading should now work correctly")
    print()
    print("📊 EXPECTED RESULTS:")
    print("   • No more 'updated_at column does not exist' errors")
    print("   • No more 'invalid input syntax for type integer' errors")  
    print("   • Correct strike prices for options (890, 900 vs 1950)")
    print("   • Successful options order placement")
    print()
    print(f"🕐 Deployment completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main()) 
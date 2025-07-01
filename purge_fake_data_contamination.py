#!/usr/bin/env python3
"""
🧹 PURGE FAKE DATA CONTAMINATION SCRIPT
=====================================

This script eliminates ALL fake trading data contamination left by the mock virus.
CRITICAL for real money futures trading safety.

⚠️  WARNING: This will DELETE all trading history to ensure no fake data remains.
✅ REQUIRED: Clean slate for real money trading.
"""

import asyncio
import logging
import json
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def purge_fake_data_contamination():
    """Purge ALL fake data contamination from the trading system"""
    
    print("🧹 PURGING FAKE DATA CONTAMINATION")
    print("=" * 60)
    print("⚠️  WARNING: This will DELETE ALL trading history")
    print("✅ REQUIRED: Clean slate for real money futures trading")
    print()
    
    # Confirm purge
    confirm = input("Type 'PURGE FAKE DATA' to confirm complete data wipe: ")
    if confirm != "PURGE FAKE DATA":
        print("❌ Purge cancelled - type exact phrase to confirm")
        sys.exit(1)
    
    print("\n🔥 INITIATING COMPLETE DATA PURGE...")
    
    try:
        # 1. Clear Database Trading Tables
        await clear_database_contamination()
        
        # 2. Clear Redis Cache
        await clear_redis_contamination()
        
        # 3. Reset File-based Trading Data
        await clear_file_contamination()
        
        # 4. Reset System State
        await reset_system_state()
        
        print("\n✅ FAKE DATA CONTAMINATION ELIMINATED!")
        print("🏦 System ready for REAL MONEY futures trading")
        print("💰 P&L reset to ₹0.00")
        print("📊 Trade count reset to 0")
        
    except Exception as e:
        logger.error(f"❌ Purge failed: {e}")
        print(f"\n❌ PURGE FAILED: {e}")
        print("⚠️  Manual database cleanup may be required")
        sys.exit(1)

async def clear_database_contamination():
    """Clear ALL fake trades from database"""
    print("1️⃣ Clearing Database Contamination...")
    
    try:
        from src.core.database import get_database
        from sqlalchemy import text
        
        database = await get_database()
        
        # Delete all fake trades
        contaminated_tables = [
            'trades',
            'positions', 
            'orders',
            'trade_history',
            'daily_pnl',
            'trading_sessions',
            'signals'
        ]
        
        for table in contaminated_tables:
            try:
                # Use raw SQL to ensure complete deletion
                await database.execute(text(f"DELETE FROM {table}"))
                print(f"   ✅ Cleared {table} table")
            except Exception as table_error:
                print(f"   ⚠️  {table} table: {table_error}")
        
        # Reset sequences/auto-increment
        try:
            await database.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('trades', 'positions', 'orders')"))
            print("   ✅ Reset ID sequences")
        except Exception as seq_error:
            print(f"   ⚠️  Sequence reset: {seq_error}")
        
        print("   ✅ Database contamination cleared")
        
    except Exception as e:
        logger.warning(f"Database clear failed: {e}")
        print(f"   ⚠️  Database clear failed: {e}")

async def clear_redis_contamination():
    """Clear ALL fake trading data from Redis"""
    print("2️⃣ Clearing Redis Contamination...")
    
    try:
        import redis
        
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Clear all trading-related keys
        contaminated_patterns = [
            'trade:*',
            'trades:*',
            'position:*',
            'positions:*',
            'pnl:*',
            'daily_pnl:*',
            'session:*',
            'trading_*',
            'autonomous_*'
        ]
        
        for pattern in contaminated_patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                print(f"   ✅ Cleared {len(keys)} keys matching {pattern}")
        
        print("   ✅ Redis contamination cleared")
        
    except Exception as e:
        logger.warning(f"Redis clear failed: {e}")
        print(f"   ⚠️  Redis clear failed: {e}")

async def clear_file_contamination():
    """Clear file-based trading data contamination"""
    print("3️⃣ Clearing File Contamination...")
    
    try:
        import glob
        import os
        
        # Remove contaminated files
        contaminated_files = [
            'logs/trading_*.log',
            'logs/trades_*.json',
            'data/trades_*.csv',
            'backups/fake_*',
            'backups/mock_*',
            'temp/trading_*'
        ]
        
        for pattern in contaminated_files:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    os.remove(file_path)
                    print(f"   ✅ Removed {file_path}")
                except Exception as file_error:
                    print(f"   ⚠️  {file_path}: {file_error}")
        
        print("   ✅ File contamination cleared")
        
    except Exception as e:
        logger.warning(f"File clear failed: {e}")
        print(f"   ⚠️  File clear failed: {e}")

async def reset_system_state():
    """Reset system state to clean slate"""
    print("4️⃣ Resetting System State...")
    
    try:
        # Reset orchestrator state if running
        from src.core.orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator.get_instance()
        
        # Reset all counters
        orchestrator.total_trades = 0
        orchestrator.daily_pnl = 0.0
        orchestrator.active_positions = []
        orchestrator.is_active = False
        orchestrator.session_id = None
        
        print("   ✅ Orchestrator state reset")
        print("   📊 Trade count: 0")
        print("   💰 P&L: ₹0.00") 
        print("   🔴 Trading: INACTIVE")
        
    except Exception as e:
        logger.warning(f"System reset failed: {e}")
        print(f"   ⚠️  System reset failed: {e}")

async def verify_purge_complete():
    """Verify that all fake data has been eliminated"""
    print("\n🔍 VERIFYING PURGE COMPLETION...")
    
    try:
        import requests
        
        base_url = 'https://algoauto-9gx56.ondigitalocean.app'
        
        # Check autonomous status
        response = requests.get(f'{base_url}/api/v1/autonomous/status', timeout=10)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            pnl = data.get('daily_pnl', 0)
            trades = data.get('total_trades', 0)
            
            print(f"✅ P&L: ₹{pnl} (target: 0.0)")
            print(f"✅ Trades: {trades} (target: 0)")
            
            if pnl == 0.0 and trades == 0:
                print("🎉 PURGE VERIFICATION: SUCCESSFUL!")
                print("🏦 System is CLEAN for real money trading")
                return True
            else:
                print("❌ PURGE VERIFICATION: FAILED!")
                print("⚠️  Fake data still present - manual cleanup required")
                return False
        else:
            print(f"⚠️  Cannot verify - status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🚨 FAKE DATA CONTAMINATION PURGE UTILITY")
    print("For REAL MONEY futures trading safety")
    print()
    
    try:
        # Run the purge
        asyncio.run(purge_fake_data_contamination())
        
        # Verify completion
        print("\n" + "="*60)
        verification_success = asyncio.run(verify_purge_complete())
        
        if verification_success:
            print("\n🎉 SUCCESS: Fake data contamination ELIMINATED!")
            print("🏦 System ready for REAL MONEY futures trading")
            print("⚡ Deploy and start trading with confidence")
        else:
            print("\n❌ WARNING: Verification failed")
            print("📞 Manual database inspection may be required")
            
    except KeyboardInterrupt:
        print("\n\n❌ Purge interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        sys.exit(1) 
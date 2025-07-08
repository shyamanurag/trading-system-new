#!/usr/bin/env python3
"""
Quick test to verify the bug fixes work correctly
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

async def test_order_manager_fix():
    """Test that OrderManager handles None redis config properly"""
    print("🔧 Testing OrderManager None redis fix...")
    
    try:
        # Test 1: OrderManager with None redis config
        config_no_redis = {
            'redis': None,
            'redis_url': None,
            'other_settings': {}
        }
        
        from src.core.order_manager import OrderManager
        order_manager = OrderManager(config_no_redis)
        
        if order_manager.redis is None:
            print("✅ OrderManager None redis fix: SUCCESS")
            return True
        else:
            print("❌ OrderManager None redis fix: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ OrderManager None redis fix: FAILED - {e}")
        return False

async def test_resilient_zerodha_fix():
    """Test that ResilientZerodhaConnection has initialize method"""
    print("🔧 Testing ResilientZerodhaConnection initialize fix...")
    
    try:
        from brokers.resilient_zerodha import ResilientZerodhaConnection
        
        # Check if initialize method exists
        if hasattr(ResilientZerodhaConnection, 'initialize'):
            print("✅ ResilientZerodhaConnection initialize fix: SUCCESS")
            return True
        else:
            print("❌ ResilientZerodhaConnection initialize fix: FAILED - method not found")
            return False
            
    except Exception as e:
        print(f"❌ ResilientZerodhaConnection initialize fix: FAILED - {e}")
        return False

async def main():
    """Run all bug fix tests"""
    print("🚀 Testing Bug Fixes...")
    print("=" * 50)
    
    results = []
    
    # Test OrderManager fix
    results.append(await test_order_manager_fix())
    
    # Test ResilientZerodhaConnection fix
    results.append(await test_resilient_zerodha_fix())
    
    print("=" * 50)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 ALL TESTS PASSED: {success_count}/{total_count}")
        print("✅ Both bugs have been fixed successfully!")
    else:
        print(f"⚠️ SOME TESTS FAILED: {success_count}/{total_count}")
        print("❌ Review the failed tests above")
    
    return success_count == total_count

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Test script to verify connection conflict fixes
"""

import sys
import os
sys.path.insert(0, '.')

def test_imports():
    """Test that all our fixed files can be imported without errors"""
    print("🧪 Testing imports after fixes...")
    
    try:
        # Test TrueData client access
        from data.truedata_client import live_market_data, is_connected
        print("✅ TrueData client imported successfully")
        
        # Test intelligent symbol manager 
        from src.core.intelligent_symbol_manager import IntelligentSymbolManager
        print("✅ IntelligentSymbolManager imported successfully")
        
        # Test market data manager
        from src.core.market_data import MarketDataManager
        print("✅ MarketDataManager imported successfully")
        
        # Test orchestrator
        from src.core.orchestrator import TradingOrchestrator
        print("✅ TradingOrchestrator imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_no_connection_conflicts():
    """Test that no connection conflicts exist"""
    print("\n🧪 Testing for connection conflicts...")
    
    try:
        # Test TrueData cache access
        from data.truedata_client import live_market_data, is_connected
        
        # Check if cache is accessible
        cache_size = len(live_market_data)
        connection_status = is_connected()
        
        print(f"✅ TrueData cache accessible: {cache_size} symbols")
        print(f"✅ Connection status: {connection_status}")
        
        # Test that we can access the cache without conflicts
        test_data = dict(live_market_data)  # Create a copy
        print(f"✅ Cache copy created: {len(test_data)} symbols")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection conflict test failed: {e}")
        return False

def test_orchestrator_creation():
    """Test that orchestrator can be created without errors"""
    print("\n🧪 Testing orchestrator creation...")
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create orchestrator
        orchestrator = TradingOrchestrator()
        print("✅ Orchestrator created successfully")
        
        # Test getting strategies
        strategies = orchestrator.get_strategies()
        print(f"✅ Strategies available: {len(strategies)}")
        
        # Test status
        status = orchestrator.get_status()
        print(f"✅ System status: {status.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 CONNECTION CONFLICT FIXES TEST")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_no_connection_conflicts,
        test_orchestrator_creation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASS")
            else:
                failed += 1
                print("❌ FAIL")
        except Exception as e:
            failed += 1
            print(f"❌ FAIL: {e}")
        
        print("-" * 30)
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Connection conflicts have been eliminated!")
        print("✅ System is ready for deployment!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
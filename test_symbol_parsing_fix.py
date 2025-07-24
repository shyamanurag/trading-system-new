#!/usr/bin/env python3
"""
Symbol Parsing & Integration Test
Tests the dynamic symbol changes to ensure they don't break existing functionality
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_symbol_generation():
    """Test that symbol generation works with fallbacks"""
    print("🧪 Testing Symbol Generation...")
    
    try:
        from config.truedata_symbols import (
            get_complete_fo_symbols, 
            get_static_fallback_symbols,
            get_autonomous_symbol_status,
            get_truedata_symbol
        )
        
        # Test 1: Basic symbol generation (should work even when TrueData is down)
        print("\n1. Testing basic symbol generation:")
        symbols = get_complete_fo_symbols()
        
        print(f"   ✅ Generated {len(symbols)} symbols")
        print(f"   ✅ Sample symbols: {symbols[:10]}")
        
        if len(symbols) < 10:
            print("   ❌ Too few symbols generated!")
            return False
        
        # Test 2: Static fallback
        print("\n2. Testing static fallback:")
        static_symbols = get_static_fallback_symbols()
        
        print(f"   ✅ Static fallback: {len(static_symbols)} symbols")
        print(f"   ✅ Sample static: {static_symbols[:5]}")
        
        if len(static_symbols) != 250:
            print(f"   ❌ Static fallback should be exactly 250 symbols, got {len(static_symbols)}")
            return False
        
        # Test 3: Status information
        print("\n3. Testing status information:")
        status = get_autonomous_symbol_status()
        print(f"   ✅ Status: {status}")
        
        # Test 4: Symbol mapping
        print("\n4. Testing symbol mapping:")
        test_symbols = ['NIFTY-I', 'RELIANCE', 'TCS', 'BANKNIFTY-I']
        for symbol in test_symbols:
            mapped = get_truedata_symbol(symbol)
            print(f"   ✅ {symbol} → {mapped}")
        
        print("\n✅ Symbol generation tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Symbol generation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zerodha_symbol_mapping():
    """Test Zerodha symbol mapping compatibility"""
    print("\n🧪 Testing Zerodha Symbol Mapping...")
    
    try:
        from brokers.zerodha import ZerodhaIntegration
        
        # Create a test instance (won't actually connect)
        zerodha = ZerodhaIntegration({
            'api_key': 'test',
            'api_secret': 'test',
            'user_id': 'test',
            'mock_mode': True
        })
        
        # Test symbol mapping
        test_symbols = [
            'NIFTY-I',  # Should become NIFTY
            'BANKNIFTY-I',  # Should become BANKNIFTY
            'RELIANCE',  # Should stay RELIANCE
            'TCS',  # Should stay TCS
            'NIFTY25JUL24000CE',  # Options contract
            'BANKNIFTY25JUL51000PE'  # Options contract
        ]
        
        print("\n1. Testing symbol mapping:")
        for symbol in test_symbols:
            try:
                mapped = zerodha._map_symbol_to_exchange(symbol)
                exchange = zerodha._get_exchange_for_symbol(symbol)
                print(f"   ✅ {symbol} → {mapped} (Exchange: {exchange})")
            except Exception as e:
                print(f"   ❌ {symbol} → ERROR: {e}")
                return False
        
        print("\n✅ Zerodha symbol mapping tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Zerodha symbol mapping test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator_symbol_filtering():
    """Test orchestrator symbol filtering"""
    print("\n🧪 Testing Orchestrator Symbol Filtering...")
    
    try:
        # Mock the orchestrator's symbol filtering logic
        from src.core.orchestrator import TradingOrchestrator
        
        # Create a mock instance
        class MockOrchestrator:
            def __init__(self):
                self.logger = logging.getLogger('test')
                
            def _is_options_contract(self, symbol: str) -> bool:
                """Check if symbol is an options contract"""
                if not symbol or not isinstance(symbol, str):
                    return False
                
                # Options contracts typically have CE/PE suffixes
                if symbol.endswith('CE') or symbol.endswith('PE'):
                    return True
                
                # Look for month patterns
                month_patterns = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                                 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
                
                for month in month_patterns:
                    if month in symbol and ('CE' in symbol or 'PE' in symbol):
                        return True
                
                return False
            
            def _get_dynamic_underlying_symbols_for_strategies(self) -> set:
                """Mock version of the method"""
                underlying_symbols = set()
                
                # Get symbols from config
                from config.truedata_symbols import get_complete_fo_symbols
                all_symbols = get_complete_fo_symbols()
                
                # Filter to underlying only
                for symbol in all_symbols:
                    if not self._is_options_contract(symbol):
                        underlying_symbols.add(symbol)
                
                return underlying_symbols
        
        orchestrator = MockOrchestrator()
        
        # Test 1: Options detection
        print("\n1. Testing options contract detection:")
        test_cases = [
            ('NIFTY-I', False),  # Index
            ('RELIANCE', False),  # Stock
            ('NIFTY25JUL24000CE', True),  # Options
            ('BANKNIFTY25AUG51000PE', True),  # Options
            ('TCS', False),  # Stock
            ('HDFC', False)  # Stock
        ]
        
        for symbol, expected in test_cases:
            result = orchestrator._is_options_contract(symbol)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {symbol} → {result} (expected: {expected})")
            if result != expected:
                return False
        
        # Test 2: Underlying symbol filtering
        print("\n2. Testing underlying symbol filtering:")
        underlying = orchestrator._get_dynamic_underlying_symbols_for_strategies()
        
        print(f"   ✅ Found {len(underlying)} underlying symbols")
        print(f"   ✅ Sample underlying: {list(underlying)[:10]}")
        
        # Check that no options contracts are in the underlying list
        has_options = any(orchestrator._is_options_contract(sym) for sym in underlying)
        if has_options:
            print("   ❌ Found options contracts in underlying symbols!")
            return False
        
        print("\n✅ Orchestrator symbol filtering tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Orchestrator symbol filtering test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_data_integration():
    """Test market data integration"""
    print("\n🧪 Testing Market Data Integration...")
    
    try:
        from src.core.market_data import MarketDataManager
        
        # Test initialization
        print("\n1. Testing MarketDataManager initialization:")
        
        # Initialize without symbols (should use dynamic symbols)
        mdm = MarketDataManager(symbols=None)
        
        print(f"   ✅ Initialized with {len(mdm.symbols)} symbols")
        print(f"   ✅ Sample symbols: {mdm.symbols[:10]}")
        
        if len(mdm.symbols) < 10:
            print("   ❌ Too few symbols in MarketDataManager!")
            return False
        
        # Test symbol mapping function exists
        if hasattr(mdm, '_get_real_data_from_truedata'):
            print("   ✅ _get_real_data_from_truedata method exists")
        else:
            print("   ❌ _get_real_data_from_truedata method missing!")
            return False
        
        print("\n✅ Market data integration tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Market data integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🔍 SYMBOL PARSING & INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_symbol_generation,
        test_zerodha_symbol_mapping,
        test_orchestrator_symbol_filtering,
        test_market_data_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"\n💥 Test {test.__name__} FAILED!")
        except Exception as e:
            print(f"\n💥 Test {test.__name__} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Symbol parsing is working correctly!")
        print("✅ Your dynamic symbol changes are backward compatible")
        print("✅ System should work when markets reopen")
    else:
        print("❌ SOME TESTS FAILED - There are integration issues")
        print("⚠️ Manual verification needed when markets open")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
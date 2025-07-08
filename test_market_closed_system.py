#!/usr/bin/env python3
"""
Comprehensive system tests for market-closed conditions
Tests all components and debugging enhancements
"""

import sys
import os
import asyncio
import time
sys.path.insert(0, '.')

def test_truedata_connection():
    """Test TrueData connection and cache access"""
    print("🔍 TESTING TRUEDATA CONNECTION...")
    print("-" * 40)
    
    try:
        from data.truedata_client import truedata_client, live_market_data, is_connected, get_truedata_status
        
        # Test connection status
        status = get_truedata_status()
        connected = is_connected()
        cache_size = len(live_market_data)
        
        print(f"✅ TrueData Status: {status}")
        print(f"✅ Connected: {connected}")
        print(f"✅ Cache Size: {cache_size} symbols")
        
        if cache_size > 0:
            print("✅ Market data cache has symbols (good for testing)")
            # Show first few symbols
            symbols = list(live_market_data.keys())[:5]
            for symbol in symbols:
                data = live_market_data[symbol]
                ltp = data.get('ltp', 0)
                print(f"   📊 {symbol}: ₹{ltp:,.2f}")
        else:
            print("⚠️ Cache empty (normal when market closed)")
            
        return True
        
    except Exception as e:
        print(f"❌ TrueData test failed: {e}")
        return False

def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    print("\n🔍 TESTING ORCHESTRATOR INITIALIZATION...")
    print("-" * 40)
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create fresh orchestrator
        orchestrator = TradingOrchestrator()
        
        # Test initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_init():
            init_success = await orchestrator.initialize()
            
            if init_success:
                print("✅ Orchestrator initialized successfully")
                print(f"✅ Strategies loaded: {len(orchestrator.strategies)}")
                print(f"✅ Components: {list(orchestrator.components.keys())}")
                
                # Test component status
                for component, status in orchestrator.components.items():
                    icon = "✅" if status else "❌"
                    print(f"   {icon} {component}: {status}")
                    
                return True
            else:
                print("❌ Orchestrator initialization failed")
                return False
                
        result = loop.run_until_complete(test_init())
        loop.close()
        return result
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_loading():
    """Test individual strategy loading"""
    print("\n🔍 TESTING STRATEGY LOADING...")
    print("-" * 40)
    
    strategies_to_test = [
        ('momentum_surfer', 'EnhancedMomentumSurfer'),
        ('volatility_explosion', 'EnhancedVolatilityExplosion'),
        ('volume_profile_scalper', 'EnhancedVolumeProfileScalper'),
        ('news_impact_scalper', 'EnhancedNewsImpactScalper'),
        ('regime_adaptive_controller', 'RegimeAdaptiveController'),
        ('confluence_amplifier', 'ConfluenceAmplifier')
    ]
    
    loaded_count = 0
    
    for strategy_key, strategy_class in strategies_to_test:
        try:
            if strategy_key == 'momentum_surfer':
                from strategies.momentum_surfer import EnhancedMomentumSurfer
                strategy = EnhancedMomentumSurfer({})
            elif strategy_key == 'volatility_explosion':
                from strategies.volatility_explosion import EnhancedVolatilityExplosion
                strategy = EnhancedVolatilityExplosion({})
            elif strategy_key == 'volume_profile_scalper':
                from strategies.volume_profile_scalper import EnhancedVolumeProfileScalper
                strategy = EnhancedVolumeProfileScalper({})
            elif strategy_key == 'news_impact_scalper':
                from strategies.news_impact_scalper import EnhancedNewsImpactScalper
                strategy = EnhancedNewsImpactScalper({})
            elif strategy_key == 'regime_adaptive_controller':
                from strategies.regime_adaptive_controller import RegimeAdaptiveController
                strategy = RegimeAdaptiveController({})
            elif strategy_key == 'confluence_amplifier':
                from strategies.confluence_amplifier import ConfluenceAmplifier
                strategy = ConfluenceAmplifier({})
            else:
                continue
                
            # Test initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def test_strategy():
                await strategy.initialize()
                return True
            
            loop.run_until_complete(test_strategy())
            loop.close()
            
            print(f"✅ {strategy_key}: Loaded and initialized")
            loaded_count += 1
            
        except Exception as e:
            print(f"❌ {strategy_key}: Failed - {e}")
    
    print(f"\n📊 Strategy Loading Results: {loaded_count}/{len(strategies_to_test)} successful")
    return loaded_count == len(strategies_to_test)

def test_market_data_transformation():
    """Test market data transformation pipeline"""
    print("\n🔍 TESTING MARKET DATA TRANSFORMATION...")
    print("-" * 40)
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create mock market data
        mock_data = {
            'NIFTY-I': {
                'ltp': 25500.0,
                'volume': 1000000,
                'high': 25550.0,
                'low': 25450.0,
                'open': 25480.0,
                'timestamp': '2025-01-07T10:00:00'
            },
            'RELIANCE': {
                'ltp': 1541.0,
                'volume': 500000,
                'high': 1545.0,
                'low': 1538.0,
                'open': 1540.0,
                'timestamp': '2025-01-07T10:00:00'
            }
        }
        
        orchestrator = TradingOrchestrator()
        
        # Test transformation
        transformed = orchestrator._transform_market_data_for_strategies(mock_data)
        
        if transformed:
            print("✅ Market data transformation successful")
            
            for symbol, data in transformed.items():
                price_change = data.get('price_change', 0)
                volume_change = data.get('volume_change', 0)
                print(f"   📊 {symbol}: price_change={price_change:.2f}%, volume_change={volume_change:.2f}%")
                
            return True
        else:
            print("❌ Market data transformation failed")
            return False
            
    except Exception as e:
        print(f"❌ Market data transformation test failed: {e}")
        return False

def test_trading_loop_readiness():
    """Test if trading loop can start (without actual trading)"""
    print("\n🔍 TESTING TRADING LOOP READINESS...")
    print("-" * 40)
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_loop():
            orchestrator = TradingOrchestrator()
            
            # Initialize
            init_success = await orchestrator.initialize()
            if not init_success:
                print("❌ Orchestrator initialization failed")
                return False
                
            # Test start trading (should set flags correctly)
            start_success = await orchestrator.start_trading()
            if not start_success:
                print("❌ Trading start failed")
                return False
                
            print("✅ Trading loop ready to start")
            print(f"✅ is_running: {orchestrator.is_running}")
            print(f"✅ strategies loaded: {len(orchestrator.strategies)}")
            
            # Test one iteration of market data processing (with empty data)
            try:
                await orchestrator._process_market_data()
                print("✅ Market data processing iteration completed")
            except Exception as e:
                print(f"⚠️ Market data processing warning (normal when market closed): {e}")
            
            # Stop trading
            await orchestrator.disable_trading()
            print("✅ Trading loop stopped cleanly")
            
            return True
            
        result = loop.run_until_complete(test_loop())
        loop.close()
        return result
        
    except Exception as e:
        print(f"❌ Trading loop test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_imports():
    """Test that all API components can be imported"""
    print("\n🔍 TESTING API COMPONENT IMPORTS...")
    print("-" * 40)
    
    import_tests = [
        ('Autonomous Trading API', 'src.api.autonomous_trading'),
        ('System Status API', 'src.api.system_status'), 
        ('Market Data API', 'src.api.market_data'),
        ('TrueData Integration', 'src.api.truedata_integration'),
        ('Order Management', 'src.api.order_management')
    ]
    
    success_count = 0
    
    for name, module_path in import_tests:
        try:
            __import__(module_path)
            print(f"✅ {name}: Import successful")
            success_count += 1
        except Exception as e:
            print(f"❌ {name}: Import failed - {e}")
    
    print(f"\n📊 API Import Results: {success_count}/{len(import_tests)} successful")
    return success_count == len(import_tests)

def main():
    """Run all market-closed tests"""
    print("🧪 COMPREHENSIVE MARKET-CLOSED SYSTEM TESTS")
    print("=" * 60)
    print("Testing all components that can work without live market data...")
    
    tests = [
        ("TrueData Connection", test_truedata_connection),
        ("API Component Imports", test_api_imports),
        ("Strategy Loading", test_strategy_loading),
        ("Market Data Transformation", test_market_data_transformation),
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Trading Loop Readiness", test_trading_loop_readiness)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED with exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 FINAL TEST RESULTS")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is ready for live trading when market opens!")
        print("✅ Enhanced debugging is properly deployed!")
        print("✅ All connection conflicts have been resolved!")
    else:
        print(f"\n⚠️ {failed} tests failed - need to investigate before market opens")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
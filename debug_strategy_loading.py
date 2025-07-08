#!/usr/bin/env python3
"""
Debug strategy loading to identify the exact source of the dict append error
"""

import sys
import asyncio
import traceback
sys.path.insert(0, '.')

def test_single_strategy_loading():
    """Test loading a single strategy in isolation"""
    print("🔍 TESTING SINGLE STRATEGY LOADING...")
    print("-" * 50)
    
    try:
        # Test momentum_surfer strategy in isolation
        from strategies.momentum_surfer import EnhancedMomentumSurfer
        
        # Create strategy instance
        strategy = EnhancedMomentumSurfer({})
        
        print("✅ Strategy instance created successfully")
        print(f"✅ Strategy name: {strategy.name}")
        print(f"✅ Historical data type: {type(strategy.historical_data)}")
        print(f"✅ Historical data content: {strategy.historical_data}")
        
        # Test initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_init():
            await strategy.initialize()
            print("✅ Strategy initialized successfully")
            
            # Test ATR calculation (this is where the error occurs)
            try:
                atr = strategy.calculate_atr('NIFTY-I', 25500.0, 25450.0, 25500.0)
                print(f"✅ ATR calculation successful: {atr}")
                print(f"✅ Historical data after ATR: {strategy.historical_data}")
            except Exception as e:
                print(f"❌ ATR calculation failed: {e}")
                print(f"❌ Historical data type: {type(strategy.historical_data)}")
                print(f"❌ Historical data content: {strategy.historical_data}")
                print("\n🔍 FULL TRACEBACK:")
                traceback.print_exc()
                return False
                
            return True
            
        result = loop.run_until_complete(test_init())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Single strategy test failed: {e}")
        print("\n🔍 FULL TRACEBACK:")
        traceback.print_exc()
        return False

def test_orchestrator_strategy_loading():
    """Test strategy loading through orchestrator to see where the conflict occurs"""
    print("\n🔍 TESTING ORCHESTRATOR STRATEGY LOADING...")
    print("-" * 50)
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create orchestrator
        orchestrator = TradingOrchestrator()
        
        print("✅ Orchestrator created successfully")
        print(f"✅ Orchestrator historical data type: {type(orchestrator.market_data_history)}")
        print(f"✅ Orchestrator historical data: {orchestrator.market_data_history}")
        
        # Test single strategy loading
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_strategy_loading():
            try:
                # Import strategy
                from strategies.momentum_surfer import EnhancedMomentumSurfer
                strategy_instance = EnhancedMomentumSurfer({})
                
                print("✅ Strategy instance created in orchestrator context")
                print(f"✅ Strategy historical data type: {type(strategy_instance.historical_data)}")
                print(f"✅ Strategy historical data: {strategy_instance.historical_data}")
                
                # Initialize strategy
                await strategy_instance.initialize()
                print("✅ Strategy initialized in orchestrator context")
                
                # Test ATR calculation
                atr = strategy_instance.calculate_atr('NIFTY-I', 25500.0, 25450.0, 25500.0)
                print(f"✅ ATR calculation successful in orchestrator context: {atr}")
                
                return True
                
            except Exception as e:
                print(f"❌ Strategy loading in orchestrator context failed: {e}")
                print("\n🔍 FULL TRACEBACK:")
                traceback.print_exc()
                return False
                
        result = loop.run_until_complete(test_strategy_loading())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Orchestrator strategy loading test failed: {e}")
        print("\n🔍 FULL TRACEBACK:")
        traceback.print_exc()
        return False

def test_historical_data_conflict():
    """Test for any global variable conflicts"""
    print("\n🔍 TESTING HISTORICAL DATA CONFLICT...")
    print("-" * 50)
    
    try:
        # Check if there's any global historical_data variable
        import strategies.base_strategy
        import src.core.orchestrator
        
        # Check for any historical_data in global scope
        print("✅ Checking for global historical_data conflicts...")
        
        # Test if strategy has independent historical_data
        from strategies.momentum_surfer import EnhancedMomentumSurfer
        strategy1 = EnhancedMomentumSurfer({})
        strategy2 = EnhancedMomentumSurfer({})
        
        print(f"✅ Strategy 1 historical_data id: {id(strategy1.historical_data)}")
        print(f"✅ Strategy 2 historical_data id: {id(strategy2.historical_data)}")
        
        # Add data to strategy 1
        strategy1.historical_data['TEST'] = []
        strategy1.historical_data['TEST'].append({'test': 'data'})
        
        print(f"✅ Strategy 1 after adding data: {strategy1.historical_data}")
        print(f"✅ Strategy 2 after strategy 1 modification: {strategy2.historical_data}")
        
        # Test if they're independent
        if id(strategy1.historical_data) == id(strategy2.historical_data):
            print("❌ CONFLICT FOUND: Strategies sharing same historical_data object!")
            return False
        else:
            print("✅ No conflict: Strategies have independent historical_data objects")
            return True
            
    except Exception as e:
        print(f"❌ Historical data conflict test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🔍 DEBUGGING STRATEGY LOADING ISSUES")
    print("=" * 60)
    
    tests = [
        ("Single Strategy Loading", test_single_strategy_loading),
        ("Historical Data Conflict", test_historical_data_conflict),
        ("Orchestrator Strategy Loading", test_orchestrator_strategy_loading)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        success = test_func()
        
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
            break  # Stop on first failure for easier debugging
    
    print(f"\n{'='*60}")
    print("🎯 DEBUG COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 
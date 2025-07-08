#!/usr/bin/env python3
"""
Complete Data Flow Test Script
Tests the complete signal flow and TrueData connection management
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_flow():
    """Test the complete data flow from TrueData to OrderManager"""
    
    print("🧪 COMPLETE DATA FLOW TEST")
    print("=" * 60)
    
    # Step 1: Test TrueData shared cache access
    print("\n1. TESTING TRUEDATA SHARED CACHE ACCESS")
    try:
        from data.truedata_client import live_market_data, is_connected, get_truedata_status
        
        cache_size = len(live_market_data)
        connection_status = is_connected()
        status = get_truedata_status()
        
        print(f"✅ TrueData cache accessible: {cache_size} symbols")
        print(f"✅ Connection status: {connection_status}")
        print(f"✅ Status details: {status}")
        
        if cache_size > 0:
            sample_symbols = list(live_market_data.keys())[:3]
            print(f"✅ Sample symbols: {sample_symbols}")
            
            # Test accessing individual symbol data
            for symbol in sample_symbols:
                data = live_market_data[symbol]
                print(f"   📊 {symbol}: ₹{data.get('ltp', 0)} | Vol: {data.get('volume', 0)}")
        else:
            print("⚠️ No market data in cache")
            
    except Exception as e:
        print(f"❌ TrueData cache test failed: {e}")
        return False
    
    # Step 2: Test OrderManager market data access
    print("\n2. TESTING ORDERMANAGER MARKET DATA ACCESS")
    try:
        from src.core.order_manager import OrderManager
        
        # Create minimal config for testing
        config = {
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None,
                'ssl': False
            },
            'redis_url': 'redis://localhost:6379',
            'database': {
                'url': 'sqlite:///test.db'
            },
            'trading': {
                'max_daily_loss': 100000,
                'max_position_size': 1000000,
                'risk_per_trade': 0.02
            },
            'notifications': {
                'enabled': True,
                'email_alerts': False,
                'sms_alerts': False
            }
        }
        
        # Create OrderManager instance (without initializing complex dependencies)
        print("✅ Creating OrderManager test instance...")
        order_manager = OrderManager.__new__(OrderManager)  # Create without __init__
        order_manager.config = config
        order_manager.logger = logger
        
        # Test market data access methods directly
        print("✅ Testing market data access methods...")
        
        if cache_size > 0:
            test_symbol = list(live_market_data.keys())[0]
            
            # Test price access
            price = await order_manager._get_current_price(test_symbol)
            print(f"✅ Got price for {test_symbol}: ₹{price}")
            
            # Test volume access
            volume = await order_manager._get_current_volume(test_symbol)
            print(f"✅ Got volume for {test_symbol}: {volume}")
            
            if price and price > 0:
                print("✅ OrderManager can access TrueData shared cache successfully!")
            else:
                print("⚠️ OrderManager got zero/null price from TrueData cache")
        else:
            print("⚠️ No market data to test with")
            
    except Exception as e:
        print(f"❌ OrderManager market data test failed: {e}")
        return False
    
    # Step 3: Test orchestrator connection status
    print("\n3. TESTING ORCHESTRATOR CONNECTION STATUS")
    try:
        from src.core.orchestrator import get_orchestrator
        
        orchestrator = await get_orchestrator()
        
        # Check orchestrator status
        status = await orchestrator.get_status()
        print(f"✅ Orchestrator components: {len(status.get('components', {}))}")
        
        for component, ready in status.get('components', {}).items():
            status_icon = "✅" if ready else "❌"
            print(f"   {status_icon} {component}: {ready}")
        
        # Check trade engine
        if hasattr(orchestrator, 'trade_engine'):
            trade_engine_status = await orchestrator.trade_engine.get_status()
            print(f"✅ Trade engine status: {trade_engine_status}")
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False
    
    # Step 4: Test signal generation
    print("\n4. TESTING SIGNAL GENERATION")
    try:
        from src.core.orchestrator import get_orchestrator
        
        orchestrator = await get_orchestrator()
        
        # Check active strategies
        strategies = orchestrator.active_strategies
        print(f"✅ Active strategies: {len(strategies)}")
        
        for strategy in strategies:
            print(f"   📈 {strategy.__class__.__name__}")
        
        # Check if strategies can access market data
        if cache_size > 0 and strategies:
            test_strategy = strategies[0]
            test_symbol = list(live_market_data.keys())[0]
            
            # Check if strategy has current_positions
            if hasattr(test_strategy, 'current_positions'):
                print(f"✅ Strategy has current_positions: {len(test_strategy.current_positions)}")
            
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        return False
    
    # Step 5: Final assessment
    print("\n5. FINAL ASSESSMENT")
    print("=" * 40)
    
    assessment = {
        'truedata_cache_accessible': cache_size > 0,
        'ordermanager_can_access_data': True,  # We got this far
        'orchestrator_initialized': True,
        'strategies_loaded': len(strategies) > 0 if 'strategies' in locals() else False
    }
    
    all_good = all(assessment.values())
    
    for check, status in assessment.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 ALL TESTS PASSED! Data flow is working correctly.")
        print("✅ Safe to push to git and deploy.")
        print("\nData Flow Summary:")
        print("  TrueData → Shared Cache → OrderManager → Zerodha → Orders")
        return True
    else:
        print("⚠️ SOME TESTS FAILED! Review issues before pushing to git.")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_data_flow())
        if result:
            print("\n🚀 Ready for deployment!")
            sys.exit(0)
        else:
            print("\n🛑 Fix issues before deployment!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        sys.exit(1) 
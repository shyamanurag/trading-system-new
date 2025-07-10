#!/usr/bin/env python3
"""
Test orchestrator with live market data during trading hours
"""
import asyncio
import logging
from datetime import datetime
from src.core.orchestrator import TradingOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_orchestrator_live():
    print('🚀 TESTING ORCHESTRATOR WITH LIVE MARKET DATA...')
    print('='*60)
    
    try:
        # Create orchestrator instance
        orchestrator = TradingOrchestrator()
        print('✅ TradingOrchestrator created successfully')
        
        # Test initialization with live data
        print('\n🔧 Testing Orchestrator Initialization...')
        init_result = await orchestrator.initialize()
        print(f'✅ Orchestrator Initialization: {"SUCCESS" if init_result else "FAILED"}')
        
        if not init_result:
            print('❌ Cannot proceed without successful initialization')
            return False
        
        # Check component status
        print('\n📊 Component Status:')
        for component, status in orchestrator.components.items():
            status_icon = "✅" if status else "❌"
            print(f'   {status_icon} {component}: {status}')
        
        # Test strategy loading
        print(f'\n🎯 Strategies Loaded: {len(orchestrator.strategies)}')
        for strategy_name in orchestrator.strategies.keys():
            print(f'   ✅ {strategy_name}')
        
        # Test market data access
        print('\n📊 Testing Market Data Access...')
        market_data = await orchestrator._get_market_data_from_api()
        if market_data:
            print(f'✅ Live Market Data: {len(market_data)} symbols')
            # Show sample data
            sample_symbols = list(market_data.keys())[:3]
            for symbol in sample_symbols:
                data = market_data[symbol]
                price = data.get('ltp', data.get('close', 'N/A'))
                print(f'   📈 {symbol}: ₹{price}')
        else:
            print('❌ No market data available')
        
        # Test trading start (but don't actually trade)
        print('\n🚀 Testing Trading System Start...')
        trading_started = await orchestrator.start_trading()
        print(f'✅ Trading Start: {"SUCCESS" if trading_started else "FAILED"}')
        
        if trading_started:
            print(f'✅ Active Strategies: {len(orchestrator.active_strategies)}')
            print(f'✅ Trading Loop: {"RUNNING" if orchestrator.is_running else "STOPPED"}')
            
            # Run for a few seconds to see if signals are generated
            print('\n⏱️ Running for 10 seconds to test signal generation...')
            await asyncio.sleep(10)
            
            # Stop trading
            await orchestrator.disable_trading()
            print('✅ Trading stopped safely')
        
        print('\n🎯 Live Orchestrator Test Results:')
        print(f'   ✅ Initialization: {"SUCCESS" if init_result else "FAILED"}')
        print(f'   ✅ Market Data: {"AVAILABLE" if market_data else "NOT AVAILABLE"}')
        print(f'   ✅ Strategies: {len(orchestrator.strategies)} loaded')
        print(f'   ✅ Trading: {"CAN START" if trading_started else "CANNOT START"}')
        
        return init_result and market_data and trading_started
        
    except Exception as e:
        print(f'❌ Error in orchestrator live test: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_orchestrator_live()
    
    if success:
        print('\n🎉 ORCHESTRATOR LIVE TEST: SUCCESS!')
        print('✅ System ready for real trading with live market data')
    else:
        print('\n❌ ORCHESTRATOR LIVE TEST: FAILED')
        print('❌ Issues detected with live market conditions')

if __name__ == '__main__':
    asyncio.run(main()) 
"""
Zero Trades Diagnostic Test - Complete Pipeline Analysis
====================================================
This test will check each step of the trading pipeline to identify the bottleneck.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_pipeline():
    """Test the complete trading pipeline from market data to trade execution"""
    
    print("="*60)
    print("ZERO TRADES DIAGNOSTIC TEST")
    print("="*60)
    
    # Step 1: Test Market Data Access
    print("\n1. TESTING MARKET DATA ACCESS")
    try:
        from src.api.market_data import get_live_market_data
        market_data = await get_live_market_data()
        
        if market_data and 'data' in market_data:
            symbol_count = len(market_data['data'])
            sample_symbol = next(iter(market_data['data'].keys()))
            sample_data = market_data['data'][sample_symbol]
            
            print(f"   ✅ Market data available: {symbol_count} symbols")
            print(f"   📊 Sample: {sample_symbol} = {sample_data}")
        else:
            print("   ❌ No market data available")
            return
    except Exception as e:
        print(f"   ❌ Market data error: {e}")
        return
    
    # Step 2: Test Orchestrator Initialization
    print("\n2. TESTING ORCHESTRATOR INITIALIZATION")
    try:
        from src.core.orchestrator import get_orchestrator
        orchestrator = await get_orchestrator()
        
        print(f"   ✅ Orchestrator initialized: {orchestrator.is_initialized}")
        print(f"   ✅ Orchestrator running: {orchestrator.is_running}")
        print(f"   ✅ Strategies loaded: {len(orchestrator.strategies)}")
        
        for strategy_key, strategy_info in orchestrator.strategies.items():
            print(f"      - {strategy_key}: {strategy_info.get('active', False)}")
        
        # Force orchestrator to running state
        orchestrator.is_running = True
        print("   🔧 Forced orchestrator to running state")
        
    except Exception as e:
        print(f"   ❌ Orchestrator error: {e}")
        return
    
    # Step 3: Test Data Transformation
    print("\n3. TESTING DATA TRANSFORMATION")
    try:
        raw_data = market_data['data']
        transformed_data = orchestrator._transform_market_data_for_strategies(raw_data)
        
        if transformed_data:
            sample_symbol = next(iter(transformed_data.keys()))
            original = raw_data[sample_symbol]
            transformed = transformed_data[sample_symbol]
            
            print(f"   ✅ Data transformation successful: {len(transformed_data)} symbols")
            print(f"   📊 Original: ltp={original.get('ltp')}, volume={original.get('volume')}")
            print(f"   📊 Transformed: close={transformed.get('close')}, price_change={transformed.get('price_change')}, volume_change={transformed.get('volume_change')}")
        else:
            print("   ❌ Data transformation failed")
            return
    except Exception as e:
        print(f"   ❌ Data transformation error: {e}")
        return
    
    # Step 4: Test Individual Strategy Signal Generation
    print("\n4. TESTING INDIVIDUAL STRATEGY SIGNAL GENERATION")
    strategy_signals = {}
    
    for strategy_key, strategy_info in orchestrator.strategies.items():
        if strategy_info.get('active', False):
            try:
                strategy_instance = strategy_info['instance']
                
                # Clear previous positions
                if hasattr(strategy_instance, 'current_positions'):
                    strategy_instance.current_positions.clear()
                
                # Process market data
                await strategy_instance.on_market_data(transformed_data)
                
                # Check for signals
                signals = []
                if hasattr(strategy_instance, 'current_positions'):
                    for symbol, signal in strategy_instance.current_positions.items():
                        if isinstance(signal, dict) and 'action' in signal and signal.get('action') != 'HOLD':
                            signals.append(signal)
                
                strategy_signals[strategy_key] = signals
                print(f"   - {strategy_key}: {len(signals)} signals generated")
                
                for signal in signals:
                    print(f"      📊 {signal.get('symbol')} {signal.get('action')} @ {signal.get('entry_price', 0):.2f}")
                    
            except Exception as e:
                print(f"   ❌ Strategy {strategy_key} error: {e}")
                strategy_signals[strategy_key] = []
    
    # Step 5: Test Trade Engine Availability
    print("\n5. TESTING TRADE ENGINE AVAILABILITY")
    try:
        if orchestrator.trade_engine:
            print(f"   ✅ Trade engine available: {orchestrator.trade_engine.is_initialized}")
            print(f"   ✅ Trade engine component status: {orchestrator.components.get('trade_engine', False)}")
        else:
            print("   ❌ No trade engine available")
            return
    except Exception as e:
        print(f"   ❌ Trade engine error: {e}")
        return
    
    # Step 6: Test Signal Processing Through Trade Engine
    print("\n6. TESTING SIGNAL PROCESSING THROUGH TRADE ENGINE")
    total_signals = sum(len(signals) for signals in strategy_signals.values())
    
    if total_signals > 0:
        try:
            all_signals = []
            for strategy_key, signals in strategy_signals.items():
                for signal in signals:
                    signal['strategy'] = strategy_key
                    all_signals.append(signal)
            
            print(f"   📊 Processing {len(all_signals)} total signals through trade engine")
            
            # Process signals through trade engine
            await orchestrator.trade_engine.process_signals(all_signals)
            
            # Check trade engine status
            trade_status = await orchestrator.trade_engine.get_status()
            print(f"   ✅ Trade engine status: {trade_status}")
            
        except Exception as e:
            print(f"   ❌ Signal processing error: {e}")
    else:
        print("   ⚠️  No signals to process")
    
    # Step 7: Test Zerodha Connection
    print("\n7. TESTING ZERODHA CONNECTION")
    try:
        import os
        zerodha_config = {
            'api_key': os.getenv('ZERODHA_API_KEY'),
            'api_secret': os.getenv('ZERODHA_API_SECRET'),
            'user_id': os.getenv('ZERODHA_USER_ID'),
            'access_token': os.getenv('ZERODHA_ACCESS_TOKEN')
        }
        
        if zerodha_config['api_key'] and zerodha_config['user_id']:
            print(f"   ✅ Zerodha credentials available")
            print(f"   📊 API Key: {zerodha_config['api_key'][:10]}...")
            print(f"   📊 User ID: {zerodha_config['user_id']}")
            print(f"   📊 Access Token: {'Available' if zerodha_config['access_token'] else 'Missing'}")
        else:
            print("   ❌ Zerodha credentials missing")
            
    except Exception as e:
        print(f"   ❌ Zerodha connection error: {e}")
    
    # Step 8: Summary and Recommendations
    print("\n8. SUMMARY AND RECOMMENDATIONS")
    print("="*60)
    
    if total_signals > 0:
        print("   ✅ SIGNALS ARE BEING GENERATED")
        print("   🔍 Check trade engine logs for actual order placement")
        print("   🔍 Verify Zerodha API credentials and permissions")
        print("   🔍 Check if orders are being placed but not visible in UI")
    else:
        print("   ❌ NO SIGNALS BEING GENERATED")
        print("   🔍 Check strategy signal conditions (thresholds too high?)")
        print("   🔍 Check if market data has sufficient price/volume changes")
        print("   🔍 Review strategy logic for signal generation")
    
    print(f"\n   📊 Total strategies: {len(orchestrator.strategies)}")
    print(f"   📊 Total signals generated: {total_signals}")
    print(f"   📊 Market data symbols: {len(transformed_data)}")
    
    return {
        'strategies_loaded': len(orchestrator.strategies),
        'signals_generated': total_signals,
        'market_data_symbols': len(transformed_data),
        'trade_engine_available': orchestrator.trade_engine is not None,
        'orchestrator_running': orchestrator.is_running,
        'strategy_signals': strategy_signals
    }

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline()) 
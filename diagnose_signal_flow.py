#!/usr/bin/env python3
"""
Signal Flow Diagnostic Script
Test the complete signal generation and processing pipeline
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

async def test_signal_flow():
    """Test the complete signal flow from market data to order placement"""
    
    print("🔍 SIGNAL FLOW DIAGNOSTIC")
    print("=" * 50)
    
    # Step 1: Test Orchestrator and Market Data
    print("\n1. TESTING ORCHESTRATOR AND MARKET DATA")
    try:
        from src.core.orchestrator import get_orchestrator
        orchestrator = await get_orchestrator()
        
        print(f"   ✅ Orchestrator initialized: {orchestrator.is_initialized}")
        print(f"   ✅ Trade engine available: {orchestrator.trade_engine is not None}")
        print(f"   ✅ Strategies loaded: {len(orchestrator.strategies)}")
        
        # Get market data
        market_data = await orchestrator._get_market_data_from_api()
        print(f"   ✅ Market data symbols: {len(market_data)}")
        
        if not market_data:
            print("   ❌ No market data - cannot test signal generation")
            return
            
    except Exception as e:
        print(f"   ❌ Orchestrator setup failed: {e}")
        return
    
    # Step 2: Test Market Data Transformation
    print("\n2. TESTING MARKET DATA TRANSFORMATION")
    try:
        transformed_data = orchestrator._transform_market_data_for_strategies(market_data)
        
        if transformed_data:
            sample_symbol = next(iter(transformed_data.keys()))
            transformed_sample = transformed_data[sample_symbol]
            
            print(f"   ✅ Transformation successful: {len(transformed_data)} symbols")
            print(f"   📊 Sample: {sample_symbol}")
            print(f"      - Price: ₹{transformed_sample.get('close', 0):.2f}")
            print(f"      - Price change: {transformed_sample.get('price_change', 0):.2f}%")
            print(f"      - Volume change: {transformed_sample.get('volume_change', 0):.2f}%")
        else:
            print("   ❌ Data transformation failed")
            return
            
    except Exception as e:
        print(f"   ❌ Data transformation error: {e}")
        return
    
    # Step 3: Test Individual Strategy Signal Generation
    print("\n3. TESTING INDIVIDUAL STRATEGY SIGNAL GENERATION")
    strategy_signals = {}
    
    for strategy_key, strategy_info in orchestrator.strategies.items():
        if strategy_info.get('active', False) and 'instance' in strategy_info:
            try:
                strategy_instance = strategy_info['instance']
                
                # Clear any existing signals
                strategy_instance.current_positions = {}
                
                # Test signal generation directly
                print(f"\n   🔍 Testing {strategy_key}:")
                
                # Call the strategy's signal generation method directly
                if hasattr(strategy_instance, '_generate_signals'):
                    signals = strategy_instance._generate_signals(transformed_data)
                    print(f"      - Generated {len(signals)} signals")
                    
                    strategy_signals[strategy_key] = signals
                    
                    for signal in signals:
                        print(f"      - Signal: {signal['symbol']} {signal['action']} "
                              f"(confidence: {signal.get('confidence', 0):.2f})")
                        
                else:
                    print(f"      - No _generate_signals method found")
                    
            except Exception as e:
                print(f"      - Error: {e}")
                
    # Step 4: Test Trade Engine Signal Processing
    print("\n4. TESTING TRADE ENGINE SIGNAL PROCESSING")
    
    if strategy_signals:
        # Test one signal through the trade engine
        for strategy_key, signals in strategy_signals.items():
            if signals:
                test_signal = signals[0]
                print(f"\n   🧪 Testing signal processing for {test_signal['symbol']} from {strategy_key}")
                
                try:
                    # Test send_to_trade_engine
                    strategy_instance = orchestrator.strategies[strategy_key]['instance']
                    success = await strategy_instance.send_to_trade_engine(test_signal)
                    
                    print(f"      - send_to_trade_engine result: {success}")
                    
                    # Check if signal was set in current_positions
                    if test_signal['symbol'] in strategy_instance.current_positions:
                        print(f"      - Signal stored in current_positions: ✅")
                    else:
                        print(f"      - Signal NOT stored in current_positions: ❌")
                        
                    # Check trade engine signal queue
                    if hasattr(orchestrator.trade_engine, 'signal_queue'):
                        queue_size = len(orchestrator.trade_engine.signal_queue)
                        print(f"      - Trade engine signal queue size: {queue_size}")
                        
                        if queue_size > 0:
                            latest_signal = orchestrator.trade_engine.signal_queue[-1]
                            print(f"      - Latest queued signal: {latest_signal.get('signal', {}).get('symbol', 'N/A')}")
                            print(f"      - Signal processed: {latest_signal.get('processed', False)}")
                            print(f"      - Signal status: {latest_signal.get('status', 'N/A')}")
                            
                except Exception as e:
                    print(f"      - Trade engine test failed: {e}")
                    
                break  # Test only one signal
    else:
        print("   ⚠️ No signals generated to test")
    
    # Step 5: Test Orchestrator Signal Collection
    print("\n5. TESTING ORCHESTRATOR SIGNAL COLLECTION")
    
    try:
        # Simulate orchestrator signal collection
        collected_signals = []
        
        for strategy_key, strategy_info in orchestrator.strategies.items():
            if strategy_info.get('active', False) and 'instance' in strategy_info:
                strategy_instance = strategy_info['instance']
                
                if hasattr(strategy_instance, 'current_positions'):
                    for symbol, signal in strategy_instance.current_positions.items():
                        if isinstance(signal, dict) and 'action' in signal and signal.get('action') != 'HOLD':
                            collected_signals.append({
                                'strategy': strategy_key,
                                'symbol': symbol,
                                'action': signal['action'],
                                'confidence': signal.get('confidence', 0)
                            })
        
        print(f"   📊 Signals collected by orchestrator: {len(collected_signals)}")
        
        for signal in collected_signals:
            print(f"      - {signal['strategy']}: {signal['symbol']} {signal['action']} "
                  f"(confidence: {signal['confidence']:.2f})")
            
    except Exception as e:
        print(f"   ❌ Orchestrator signal collection failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_signal_flow()) 
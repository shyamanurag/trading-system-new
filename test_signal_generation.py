#!/usr/bin/env python3
"""
Comprehensive test script to check:
A) If signals are being generated
B) If orders are being created from signals  
C) Orchestrator component status
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.orchestrator import TradingOrchestrator

async def test_signal_and_order_pipeline():
    """Test the complete signal generation and order creation pipeline"""
    print("🧪 TESTING SIGNAL GENERATION & ORDER CREATION PIPELINE...")
    
    # Initialize orchestrator
    orchestrator = TradingOrchestrator()
    await orchestrator.initialize()
    
    print(f"\n📊 ORCHESTRATOR COMPONENT STATUS:")
    print(f"System Ready: {orchestrator.is_initialized}")
    print(f"Trading Active: {orchestrator.is_running}")
    print(f"Strategies Loaded: {len(orchestrator.strategies)}")
    print(f"Active Strategies: {orchestrator.active_strategies}")
    
    print(f"\n🔧 COMPONENT STATUS:")
    for component, status in orchestrator.components.items():
        print(f"  {component}: {'✅ ACTIVE' if status else '❌ FAILED'}")
    
    # Test 1: Check strategy loading
    print(f"\n📦 STRATEGY LOADING TEST:")
    print(f"Expected: 6 strategies")
    print(f"Actual: {len(orchestrator.strategies)} strategies")
    
    for strategy_key, strategy_info in orchestrator.strategies.items():
        print(f"  ✅ {strategy_key}: {strategy_info.get('name', 'N/A')}")
    
    # Test 2: Create realistic market data with price changes
    print(f"\n💹 TESTING SIGNAL GENERATION WITH REALISTIC DATA...")
    
    # Simulate realistic market data with strong momentum (should trigger signals)
    test_market_data = {
        'NIFTY': {
            'ltp': 24600.0,  # Current price
            'volume': 500000,
            'high': 24650.0,
            'low': 24500.0,
            'open': 24520.0,
            'timestamp': datetime.now().isoformat()
        },
        'BANKNIFTY': {
            'ltp': 52100.0,  # Current price  
            'volume': 350000,
            'high': 52200.0,
            'low': 52000.0,
            'open': 52050.0,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # First call - establish baseline (no signals expected)
    print("  📈 First data call (establishing baseline)...")
    transformed_data1 = orchestrator._transform_market_data_for_strategies(test_market_data)
    await orchestrator._run_strategies(transformed_data1)
    
    # Second call - simulate strong momentum (signals expected)
    print("  🚀 Second data call (strong momentum - expecting signals)...")
    momentum_data = {
        'NIFTY': {
            'ltp': 24750.0,  # +1.5% price increase - should trigger BUY signal
            'volume': 650000,  # +30% volume increase - strong momentum
            'high': 24800.0,
            'low': 24500.0,
            'open': 24520.0,
            'timestamp': datetime.now().isoformat()
        },
        'BANKNIFTY': {
            'ltp': 51800.0,  # -0.6% price decrease - should trigger SELL signal  
            'volume': 450000,  # +28% volume increase
            'high': 52200.0,
            'low': 51750.0,
            'open': 52050.0,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    transformed_data2 = orchestrator._transform_market_data_for_strategies(momentum_data)
    
    # Show transformation results
    print(f"\n🔄 DATA TRANSFORMATION RESULTS:")
    for symbol, data in transformed_data2.items():
        print(f"  {symbol}: close={data['close']}, price_change={data['price_change']}%, volume_change={data['volume_change']}%")
    
    # Capture signals
    print(f"\n🎯 RUNNING STRATEGIES WITH MOMENTUM DATA...")
    
    # Clear any existing signals
    for strategy_info in orchestrator.strategies.values():
        if hasattr(strategy_info.get('instance'), 'current_positions'):
            strategy_info['instance'].current_positions.clear()
    
    # Run strategies and capture signals
    await orchestrator._run_strategies(transformed_data2)
    
    # Test 3: Check signal generation
    print(f"\n📡 SIGNAL GENERATION RESULTS:")
    total_signals = 0
    
    for strategy_key, strategy_info in orchestrator.strategies.items():
        strategy_instance = strategy_info.get('instance')
        if strategy_instance and hasattr(strategy_instance, 'current_positions'):
            strategy_signals = 0
            for symbol, signal in strategy_instance.current_positions.items():
                if signal and isinstance(signal, dict) and signal.get('action') != 'HOLD':
                    strategy_signals += 1
                    total_signals += 1
                    print(f"  ✅ {strategy_key} -> {symbol}: {signal.get('action')} (confidence: {signal.get('confidence', 'N/A')})")
            
            if strategy_signals == 0:
                print(f"  ⚪ {strategy_key}: No signals generated")
    
    print(f"\n📊 SIGNAL SUMMARY:")
    print(f"Total signals generated: {total_signals}")
    
    # Test 4: Check trade engine processing
    print(f"\n⚙️ TRADE ENGINE STATUS:")
    if orchestrator.trade_engine:
        engine_status = await orchestrator.trade_engine.get_status()
        print(f"  Initialized: {engine_status.get('initialized', False)}")
        print(f"  Running: {engine_status.get('running', False)}")
        print(f"  Signals processed: {engine_status.get('signals_processed', 0)}")
        print(f"  Pending signals: {engine_status.get('pending_signals', 0)}")
        
        # Check signal queue
        if hasattr(orchestrator.trade_engine, 'signal_queue'):
            print(f"  Signal queue length: {len(orchestrator.trade_engine.signal_queue)}")
            for i, queued_signal in enumerate(orchestrator.trade_engine.signal_queue[-3:]):  # Show last 3
                signal_info = queued_signal.get('signal', {})
                status = queued_signal.get('status', 'UNKNOWN')
                print(f"    Signal {i+1}: {signal_info.get('symbol', 'N/A')} {signal_info.get('action', 'N/A')} - Status: {status}")
    else:
        print("  ❌ Trade engine not available")
    
    # Test 5: Overall system health
    print(f"\n🏥 SYSTEM HEALTH CHECK:")
    if total_signals > 0:
        print("  ✅ Signal generation: WORKING")
    else:
        print("  ❌ Signal generation: NO SIGNALS GENERATED")
        print("     - Check if strategies are receiving proper data format")
        print("     - Check if momentum thresholds are met")
    
    if orchestrator.components.get('trade_engine', False):
        print("  ✅ Trade engine: ACTIVE")
    else:
        print("  ❌ Trade engine: INACTIVE")
    
    strategy_count = len(orchestrator.strategies)
    if strategy_count == 6:
        print("  ✅ Strategy loading: ALL 6 STRATEGIES LOADED")
    else:
        print(f"  ⚠️ Strategy loading: ONLY {strategy_count}/6 STRATEGIES LOADED")
    
    print(f"\n{'='*60}")
    if total_signals > 0 and orchestrator.components.get('trade_engine', False):
        print("🎉 PIPELINE STATUS: SIGNALS GENERATED & TRADE ENGINE ACTIVE")
        print("✅ Orders should be created from signals")
    elif total_signals > 0:
        print("⚠️ PIPELINE STATUS: SIGNALS GENERATED BUT TRADE ENGINE ISSUE")
        print("❌ Orders may not be created from signals")
    else:
        print("❌ PIPELINE STATUS: NO SIGNALS GENERATED")
        print("❌ No orders will be created")
    
    return {
        'signals_generated': total_signals,
        'strategies_loaded': strategy_count,
        'trade_engine_active': orchestrator.components.get('trade_engine', False),
        'system_ready': orchestrator.is_initialized
    }

if __name__ == "__main__":
    result = asyncio.run(test_signal_and_order_pipeline())
    print(f"\n📈 FINAL RESULTS: {result}") 
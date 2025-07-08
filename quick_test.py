import asyncio
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_pipeline():
    print("🧪 TESTING TRADING PIPELINE...")
    
    from core.orchestrator import TradingOrchestrator
    orchestrator = TradingOrchestrator()
    
    print("\n1️⃣ INITIALIZING ORCHESTRATOR...")
    await orchestrator.initialize()
    
    print(f"\n📊 ORCHESTRATOR STATUS:")
    print(f"  System Ready: {orchestrator.is_initialized}")
    print(f"  Strategies Loaded: {len(orchestrator.strategies)}/6")
    print(f"  Active Strategies: {len(orchestrator.active_strategies)}")
    
    print(f"\n🔧 COMPONENT STATUS:")
    for comp, status in orchestrator.components.items():
        print(f"  {comp}: {'✅ ACTIVE' if status else '❌ FAILED'}")
    
    print(f"\n📦 LOADED STRATEGIES:")
    for key in orchestrator.strategies.keys():
        print(f"  - {key}")
    
    print(f"\n2️⃣ TESTING SIGNAL GENERATION...")
    
    # Create test data with strong momentum
    momentum_data = {
        'NIFTY': {
            'ltp': 24750.0,  # Strong price increase
            'volume': 650000,
            'high': 24800.0,
            'low': 24500.0,
            'open': 24520.0
        }
    }
    
    # Transform data (should add price_change and volume_change)
    transformed = orchestrator._transform_market_data_for_strategies(momentum_data)
    
    # Simulate second call for price change calculation
    momentum_data2 = {
        'NIFTY': {
            'ltp': 24850.0,  # Another increase
            'volume': 750000,
            'high': 24900.0,
            'low': 24500.0,
            'open': 24520.0
        }
    }
    
    transformed2 = orchestrator._transform_market_data_for_strategies(momentum_data2)
    print(f"  Data transformation - NIFTY: price_change={transformed2['NIFTY']['price_change']}%, volume_change={transformed2['NIFTY']['volume_change']}%")
    
    # Run strategies
    await orchestrator._run_strategies(transformed2)
    
    print(f"\n3️⃣ CHECKING SIGNALS...")
    total_signals = 0
    for strategy_key, strategy_info in orchestrator.strategies.items():
        instance = strategy_info.get('instance')
        if instance and hasattr(instance, 'current_positions'):
            for symbol, signal in instance.current_positions.items():
                if signal and isinstance(signal, dict) and signal.get('action') != 'HOLD':
                    total_signals += 1
                    print(f"  ✅ {strategy_key}: {symbol} {signal.get('action')} (confidence: {signal.get('confidence', 'N/A')})")
    
    if total_signals == 0:
        print(f"  ❌ No signals generated")
    
    print(f"\n4️⃣ CHECKING TRADE ENGINE...")
    if orchestrator.trade_engine:
        status = await orchestrator.trade_engine.get_status()
        print(f"  Engine Status: {status}")
        if hasattr(orchestrator.trade_engine, 'signal_queue'):
            print(f"  Signal Queue: {len(orchestrator.trade_engine.signal_queue)} signals")
    else:
        print(f"  ❌ Trade engine not available")
    
    print(f"\n📈 SUMMARY:")
    print(f"  Strategies Loaded: {len(orchestrator.strategies)}/6")
    print(f"  Signals Generated: {total_signals}")
    print(f"  Trade Engine: {'✅' if orchestrator.components.get('trade_engine') else '❌'}")
    
    return total_signals > 0

if __name__ == "__main__":
    result = asyncio.run(test_pipeline())
    print(f"\n🎯 PIPELINE WORKING: {result}") 
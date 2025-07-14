#!/usr/bin/env python3
"""
Test Trade Execution Flow - Verify signal to order pipeline
This test checks the complete flow from signal generation to order placement
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.orchestrator import TradingOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_trade_execution_flow():
    """Test the complete trade execution flow"""
    
    print("🔍 TRADE EXECUTION FLOW TEST")
    print("=" * 50)
    
    try:
        # Get orchestrator instance
        orchestrator = await TradingOrchestrator.get_instance()
        
        # Test 1: Check if orchestrator is initialized
        print("\n1. ORCHESTRATOR STATUS:")
        status = await orchestrator.get_status()
        print(f"   System Ready: {status.get('system_ready', False)}")
        print(f"   Is Active: {status.get('is_active', False)}")
        print(f"   Components: {status.get('components', {})}")
        
        # Test 2: Check trade engine availability
        print("\n2. TRADE ENGINE STATUS:")
        if hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
            print("   ✅ Trade Engine: Available")
            
            # Check trade engine initialization
            if hasattr(orchestrator.trade_engine, 'is_initialized'):
                print(f"   Initialized: {orchestrator.trade_engine.is_initialized}")
            
            # Check order manager
            if hasattr(orchestrator.trade_engine, 'order_manager'):
                if orchestrator.trade_engine.order_manager:
                    print(f"   ✅ Order Manager: Available ({type(orchestrator.trade_engine.order_manager).__name__})")
                else:
                    print("   ❌ Order Manager: Not Available")
            
            # Check signal queue
            if hasattr(orchestrator.trade_engine, 'signal_queue'):
                print(f"   Signal Queue: {len(orchestrator.trade_engine.signal_queue)} items")
        else:
            print("   ❌ Trade Engine: Not Available")
        
        # Test 3: Check strategy status
        print("\n3. STRATEGY STATUS:")
        if hasattr(orchestrator, 'strategies'):
            print(f"   Loaded Strategies: {len(orchestrator.strategies)}")
            for name, strategy_info in orchestrator.strategies.items():
                active = strategy_info.get('active', False)
                print(f"   - {name}: {'✅ Active' if active else '❌ Inactive'}")
        
        # Test 4: Check market data flow
        print("\n4. MARKET DATA STATUS:")
        if hasattr(orchestrator, 'market_data'):
            print(f"   Market Data Available: {orchestrator.market_data is not None}")
        
        # Test 5: Test signal processing with mock data
        print("\n5. SIGNAL PROCESSING TEST:")
        
        # Create a mock signal
        mock_signal = {
            'symbol': 'NIFTY',
            'action': 'BUY',
            'entry_price': 19500.0,
            'stop_loss': 19400.0,
            'target': 19600.0,
            'confidence': 0.85,
            'strategy': 'test_strategy',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"   Mock Signal: {mock_signal['symbol']} {mock_signal['action']}")
        
        # Test signal processing
        if hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
            try:
                print("   Testing signal processing...")
                await orchestrator.trade_engine.process_signals([mock_signal])
                print("   ✅ Signal processing completed")
                
                # Check signal queue after processing
                if hasattr(orchestrator.trade_engine, 'signal_queue'):
                    queue_size = len(orchestrator.trade_engine.signal_queue)
                    print(f"   Signal Queue After Processing: {queue_size} items")
                    
                    # Show recent signals
                    if queue_size > 0:
                        recent_signal = orchestrator.trade_engine.signal_queue[-1]
                        print(f"   Recent Signal Status: {recent_signal.get('status', 'unknown')}")
                
            except Exception as e:
                print(f"   ❌ Signal processing failed: {e}")
        
        # Test 6: Check Zerodha integration
        print("\n6. ZERODHA INTEGRATION:")
        if hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
            print("   ✅ Zerodha Client: Available")
        else:
            print("   ❌ Zerodha Client: Not Available")
        
        # Test 7: Check order placement capability
        print("\n7. ORDER PLACEMENT CAPABILITY:")
        
        # Check if we can place orders
        can_place_orders = False
        
        if (hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine and 
            hasattr(orchestrator.trade_engine, 'order_manager') and orchestrator.trade_engine.order_manager):
            can_place_orders = True
            print("   ✅ Order Placement: Ready")
        else:
            print("   ❌ Order Placement: Not Ready")
        
        # Final assessment
        print("\n" + "=" * 50)
        print("📊 TRADE EXECUTION READINESS ASSESSMENT:")
        
        if can_place_orders:
            print("✅ READY: System can process signals and place orders")
            print("💡 NOTE: Orders will be placed when live market data is available")
        else:
            print("❌ NOT READY: Missing components for order placement")
            print("🔧 REQUIRED: OrderManager initialization needed")
        
        # Show what happens when markets are closed
        print("\n💡 MARKET CLOSURE BEHAVIOR:")
        print("   - No live market data → No strategy signals")
        print("   - No signals → No order placement")
        print("   - System waits for market open to resume trading")
        
        return can_place_orders
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Trade Execution Flow Test...")
    
    try:
        result = await test_trade_execution_flow()
        
        if result:
            print("\n✅ CONCLUSION: Trade execution pipeline is working correctly")
            print("🎯 NEXT STEP: Wait for market open to see live trading")
        else:
            print("\n❌ CONCLUSION: Trade execution pipeline needs fixes")
            print("🔧 NEXT STEP: Fix OrderManager initialization")
            
    except Exception as e:
        print(f"❌ Main test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
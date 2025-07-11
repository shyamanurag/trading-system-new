import os
import sys
import asyncio
sys.path.insert(0, ".")

async def test_zerodha_pipeline():
    print(" Zerodha Pipeline Comprehensive Test")
    print("=" * 50)
    
    # 1. Test environment variables
    print("\n1.  Environment Variables:")
    env_vars = {
        "ZERODHA_API_KEY": os.getenv("ZERODHA_API_KEY"),
        "ZERODHA_API_SECRET": os.getenv("ZERODHA_API_SECRET"),
        "ZERODHA_USER_ID": os.getenv("ZERODHA_USER_ID"),
        "ZERODHA_ACCESS_TOKEN": os.getenv("ZERODHA_ACCESS_TOKEN"),
        "ZERODHA_PIN": os.getenv("ZERODHA_PIN")
    }
    
    for var, value in env_vars.items():
        if value:
            print(f"    {var}: {value[:10]}...")
        else:
            print(f"    {var}: NOT SET")
    
    # 2. Test orchestrator initialization
    print("\n2.  Orchestrator Components Test:")
    try:
        from src.core.orchestrator import TradingOrchestrator
        orchestrator = TradingOrchestrator()
        await orchestrator.initialize()
        
        components = orchestrator.components
        component_count = len(components)
        active_count = sum(1 for status in components.values() if status)
        
        print(f"    Components: {active_count}/{component_count} active")
        
        for component, status in components.items():
            status_icon = "" if status else ""
            print(f"   {status_icon} {component}: {status}")
        
        # Check specific Zerodha status
        zerodha_status = components.get("zerodha", False)
        print(f"\n    Zerodha Component Status: {zerodha_status}")
        
        if hasattr(orchestrator, "zerodha") and orchestrator.zerodha:
            print("    Zerodha client available in orchestrator")
        else:
            print("     Zerodha client not available - bypass logic will be used")
        
    except Exception as e:
        print(f"    Orchestrator test failed: {e}")
    
    # 3. Test trade engine and signal processing
    print("\n3.  Signal Processing Test:")
    try:
        from src.core.orchestrator import TradeEngine
        
        trade_engine = TradeEngine()
        await trade_engine.initialize()
        
        # Create a test signal
        test_signal = {
            "symbol": "NIFTY25JAN26000PE",
            "action": "BUY",
            "confidence": 0.85,
            "strategy": "TEST_STRATEGY"
        }
        
        print(f"    Test Signal: {test_signal[\"symbol\"]} {test_signal[\"action\"]}")
        
        # Process the signal
        await trade_engine.process_signals([test_signal])
        
        # Check results
        queue_length = len(trade_engine.signal_queue)
        print(f"    Signals processed: {queue_length}")
        
        for i, queued_signal in enumerate(trade_engine.signal_queue):
            signal_data = queued_signal.get("signal", {})
            symbol = signal_data.get("symbol", "UNKNOWN")
            action = signal_data.get("action", "UNKNOWN")
            processed = queued_signal.get("processed", False)
            status = queued_signal.get("status", "UNKNOWN")
            order_id = queued_signal.get("order_id", "None")
            
            print(f"    Signal {i+1}: {symbol} {action}")
            print(f"      Processed: {processed}")
            print(f"      Status: {status}")
            print(f"      Order ID: {order_id}")
        
    except Exception as e:
        print(f"    Signal processing test failed: {e}")
    
    print("\n" + "=" * 50)
    print(" Zerodha Pipeline Test Complete")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_zerodha_pipeline())


#!/usr/bin/env python3
import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def test_orchestrator():
    """Test orchestrator initialization"""
    try:
        print("Testing orchestrator initialization...")
        
        # Import orchestrator
        from src.core.orchestrator import TradingOrchestrator
        
        # Create instance
        orchestrator = TradingOrchestrator()
        
        # Try to initialize
        print("Initializing orchestrator...")
        success = await orchestrator.initialize()
        
        print(f"Initialization result: {success}")
        print(f"Is initialized: {orchestrator.is_initialized}")
        print(f"Components status: {orchestrator.components}")
        
        if success:
            print("✅ Orchestrator initialized successfully!")
            
            # Test trading start
            print("Testing trading start...")
            trading_started = await orchestrator.start_trading()
            print(f"Trading started: {trading_started}")
            
        else:
            print("❌ Orchestrator initialization failed!")
            
    except Exception as e:
        print(f"Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator()) 
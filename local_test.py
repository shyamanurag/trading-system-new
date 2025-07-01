#!/usr/bin/env python3
"""
LOCAL TEST: Validate orchestrator before deployment
This should run successfully locally before any git push
"""
import sys
import os
from pathlib import Path
import asyncio
import logging

# Add src directory to path
src_path = str(Path(__file__).parent / "src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Reduce logging noise
logging.basicConfig(level=logging.ERROR)

async def test_orchestrator_locally():
    """Test orchestrator initialization locally"""
    try:
        print("🔄 Testing orchestrator locally...")
        from core.orchestrator import TradingOrchestrator
        
        # Create orchestrator
        orch = TradingOrchestrator()
        print("✅ Orchestrator created successfully")
        
        # Test initialization
        result = await orch.initialize_system()
        print(f"📊 Initialize result: {result}")
        
        if result:
            print("🎉 LOCAL SUCCESS - Safe to deploy!")
        else:
            print("❌ LOCAL FAILURE - Do NOT deploy")
            
        # Check component status
        components = ['strategy_engine', 'risk_manager', 'trade_engine', 'market_data', 'position_tracker', 'order_manager']
        print("\n📊 Component Status:")
        for comp in components:
            status = '✅ OK' if getattr(orch, comp, None) else '❌ FAILED'
            print(f"  {comp}: {status}")
            
        return result
        
    except Exception as e:
        print(f"❌ LOCAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_orchestrator_locally())
    
    if result:
        print("\n✅ LOCAL TEST PASSED - Ready for deployment")
        sys.exit(0)
    else:
        print("\n❌ LOCAL TEST FAILED - Fix issues before deployment")
        sys.exit(1) 
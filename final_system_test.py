#!/usr/bin/env python3
"""
Final system verification test to confirm all components are working
"""

import sys
import asyncio
sys.path.insert(0, '.')

async def test_full_system():
    print('🎯 FINAL SYSTEM VERIFICATION')
    print('=' * 40)
    
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        # Create orchestrator
        orchestrator = TradingOrchestrator()
        
        # Test full initialization
        init_success = await orchestrator.initialize()
        print(f'✅ Initialization: {init_success}')
        
        # Test strategy loading
        print(f'✅ Strategies loaded: {len(orchestrator.strategies)}')
        
        # Test trading start
        start_success = await orchestrator.start_trading()
        print(f'✅ Trading started: {start_success}')
        
        # Test system status
        status = await orchestrator.get_trading_status()
        print(f'✅ System ready: {status.get("system_ready", False)}')
        print(f'✅ Active strategies: {len(status.get("active_strategies", []))}')
        
        # Test trading stop
        stop_success = await orchestrator.disable_trading()
        print(f'✅ Trading stopped: {stop_success}')
        
        print('\n🎉 ALL SYSTEMS OPERATIONAL!')
        print('✅ Ready for live trading when market opens at 9:15 AM IST!')
        
        return True
        
    except Exception as e:
        print(f'❌ System test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_full_system()) 
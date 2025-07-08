#!/usr/bin/env python3
"""
Check Live Strategy Status and Activate Scalping Strategies
Diagnose why 0 strategies are active and fix it
"""

import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.orchestrator import get_orchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveStrategyStatusChecker:
    """Check and fix live strategy status"""
    
    def __init__(self):
        self.orchestrator = None
        
    async def check_and_fix_strategies(self):
        """Check strategy status and activate if needed"""
        print("🔍 LIVE STRATEGY STATUS CHECK")
        print("=" * 50)
        
        try:
            # Get orchestrator instance
            print("\n1. Getting orchestrator instance...")
            self.orchestrator = await get_orchestrator()
            
            if not self.orchestrator:
                print("❌ Failed to get orchestrator instance")
                return False
                
            print(f"✅ Orchestrator instance obtained: {type(self.orchestrator).__name__}")
            print(f"   - Initialized: {self.orchestrator.is_initialized}")
            print(f"   - Running: {self.orchestrator.is_running}")
            
            # Check current strategy status
            print("\n2. Checking current strategy status...")
            await self._check_current_strategies()
            
            # Initialize if needed
            if not self.orchestrator.is_initialized:
                print("\n3. Initializing orchestrator...")
                init_success = await self.orchestrator.initialize()
                if init_success:
                    print("✅ Orchestrator initialization successful")
                else:
                    print("❌ Orchestrator initialization failed")
                    return False
            else:
                print("\n3. Orchestrator already initialized ✅")
            
            # Check strategies after initialization
            print("\n4. Checking strategies after initialization...")
            await self._check_current_strategies()
            
            # Start trading if not running
            if not self.orchestrator.is_running:
                print("\n5. Starting trading system...")
                start_success = await self.orchestrator.start_trading()
                if start_success:
                    print("✅ Trading system started successfully")
                else:
                    print("❌ Failed to start trading system")
                    return False
            else:
                print("\n5. Trading system already running ✅")
                
            # Final strategy check
            print("\n6. Final strategy status check...")
            await self._check_current_strategies()
            
            # Test scalping optimization
            print("\n7. Testing scalping optimizations...")
            await self._test_scalping_optimizations()
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking strategy status: {e}")
            logger.error(f"Strategy status check failed: {e}")
            return False
    
    async def _check_current_strategies(self):
        """Check current strategy status"""
        try:
            strategies = getattr(self.orchestrator, 'strategies', {})
            active_strategies = getattr(self.orchestrator, 'active_strategies', [])
            
            print(f"   📊 Loaded strategies: {len(strategies)}")
            print(f"   🎯 Active strategies: {len(active_strategies)}")
            
            if strategies:
                print("   📋 Strategy details:")
                for key, strategy_info in strategies.items():
                    name = strategy_info.get('name', key)
                    active = strategy_info.get('active', False)
                    has_instance = 'instance' in strategy_info
                    status = "🟢 ACTIVE" if active else "🔴 INACTIVE"
                    instance_status = "✅ LOADED" if has_instance else "❌ NOT LOADED"
                    print(f"      {name}: {status} | {instance_status}")
            else:
                print("   ⚠️  No strategies loaded")
                
            # Check scalping strategies specifically
            scalping_strategies = ['volume_profile_scalper', 'news_impact_scalper', 'volatility_explosion', 'momentum_surfer']
            loaded_scalping = [s for s in scalping_strategies if s in strategies]
            
            if loaded_scalping:
                print(f"   🎯 Scalping strategies loaded: {len(loaded_scalping)}/4")
                for strategy in loaded_scalping:
                    strategy_info = strategies[strategy]
                    active = strategy_info.get('active', False)
                    print(f"      ⚡ {strategy}: {'ACTIVE' if active else 'INACTIVE'}")
            else:
                print("   ❌ No scalping strategies loaded!")
                
        except Exception as e:
            print(f"   ❌ Error checking strategies: {e}")
    
    async def _test_scalping_optimizations(self):
        """Test if scalping optimizations are working"""
        try:
            strategies = getattr(self.orchestrator, 'strategies', {})
            
            if not strategies:
                print("   ❌ No strategies to test")
                return
                
            print("   🧪 Testing scalping parameters...")
            
            # Test each scalping strategy
            scalping_tests = {}
            
            for strategy_key, strategy_info in strategies.items():
                if 'instance' in strategy_info:
                    instance = strategy_info['instance']
                    
                    # Check for scalping optimizations
                    cooldown_optimized = hasattr(instance, 'scalping_cooldown')
                    symbol_cooldown = hasattr(instance, 'symbol_cooldowns')
                    tight_stop_losses = False
                    
                    # Check ATR multipliers for tighter stops
                    if hasattr(instance, 'atr_multipliers'):
                        multipliers = instance.atr_multipliers
                        if isinstance(multipliers, dict):
                            max_multiplier = max(multipliers.values())
                            tight_stop_losses = max_multiplier <= 2.0  # Scalping should be <= 2.0
                    
                    scalping_tests[strategy_key] = {
                        'cooldown_optimized': cooldown_optimized,
                        'symbol_cooldown': symbol_cooldown,
                        'tight_stop_losses': tight_stop_losses,
                        'scalping_ready': cooldown_optimized and symbol_cooldown and tight_stop_losses
                    }
            
            # Report results
            scalping_ready_count = sum(1 for test in scalping_tests.values() if test['scalping_ready'])
            print(f"   📊 Scalping optimization results: {scalping_ready_count}/{len(scalping_tests)} strategies optimized")
            
            for strategy, results in scalping_tests.items():
                status = "🎯 SCALPING READY" if results['scalping_ready'] else "⚠️  NEEDS OPTIMIZATION"
                print(f"      {strategy}: {status}")
                if not results['scalping_ready']:
                    missing = []
                    if not results['cooldown_optimized']: missing.append('cooldown')
                    if not results['symbol_cooldown']: missing.append('symbol_cooldown')
                    if not results['tight_stop_losses']: missing.append('tight_stops')
                    print(f"         Missing: {', '.join(missing)}")
            
            # Test signal generation capability
            print("   🔄 Testing signal generation capability...")
            sample_data = {
                'RELIANCE': {
                    'close': 2500.0,
                    'high': 2510.0,
                    'low': 2490.0,
                    'volume': 1000000,
                    'price_change': 0.4,
                    'volume_change': 20
                }
            }
            
            signals_generated = 0
            for strategy_key, strategy_info in strategies.items():
                if 'instance' in strategy_info and strategy_info.get('active', False):
                    try:
                        instance = strategy_info['instance']
                        instance.is_active = True
                        
                        # Test signal generation
                        await instance.on_market_data(sample_data)
                        
                        # Check if signals were generated
                        if hasattr(instance, 'current_positions') and instance.current_positions:
                            signals_generated += len(instance.current_positions)
                            
                    except Exception as e:
                        print(f"         ⚠️  {strategy_key} signal test failed: {e}")
            
            print(f"   🎯 Signal generation test: {signals_generated} signals generated")
            
        except Exception as e:
            print(f"   ❌ Error testing scalping optimizations: {e}")

async def main():
    """Main function"""
    checker = LiveStrategyStatusChecker()
    success = await checker.check_and_fix_strategies()
    
    if success:
        print("\n🎯 STRATEGY STATUS CHECK COMPLETE")
        print("=" * 40)
        print("✅ All checks completed successfully")
        print("🚀 Scalping strategies should now be active")
        print("\n💡 Next steps:")
        print("1. Monitor trading dashboard")
        print("2. Watch for scalping signals")
        print("3. Check position management")
    else:
        print("\n❌ STRATEGY STATUS CHECK FAILED")
        print("=" * 40)
        print("⚠️  Manual intervention may be required")

if __name__ == "__main__":
    asyncio.run(main()) 
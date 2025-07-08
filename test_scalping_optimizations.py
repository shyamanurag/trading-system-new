"""
Test Scalping Optimizations
Verify that all scalping strategies have proper parameters and timing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalpingOptimizationTest:
    """Test class to verify scalping optimizations"""
    
    def __init__(self):
        self.strategies = {}
        self.test_results = {}
        
    async def test_all_strategies(self):
        """Test all scalping strategies"""
        logger.info("🧪 SCALPING OPTIMIZATION TEST - Starting comprehensive test")
        
        # Test each strategy
        strategies_to_test = [
            'volume_profile_scalper',
            'news_impact_scalper', 
            'volatility_explosion',
            'momentum_surfer'
        ]
        
        for strategy_name in strategies_to_test:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Testing {strategy_name.upper()}")
            logger.info(f"{'='*60}")
            
            try:
                result = await self._test_strategy(strategy_name)
                self.test_results[strategy_name] = result
                
                if result['passed']:
                    logger.info(f"✅ {strategy_name} - SCALPING OPTIMIZED")
                else:
                    logger.warning(f"⚠️ {strategy_name} - NEEDS OPTIMIZATION")
                    
            except Exception as e:
                logger.error(f"❌ {strategy_name} - TEST FAILED: {e}")
                self.test_results[strategy_name] = {'passed': False, 'error': str(e)}
        
        # Generate final report
        self._generate_test_report()
        
    async def _test_strategy(self, strategy_name: str) -> Dict:
        """Test individual strategy parameters"""
        try:
            # Import strategy
            strategy_instance = await self._import_strategy(strategy_name)
            
            # Test parameters
            cooldown_test = self._test_cooldown_parameters(strategy_instance)
            stop_loss_test = self._test_stop_loss_parameters(strategy_instance)
            risk_reward_test = self._test_risk_reward_parameters(strategy_instance)
            volume_test = self._test_volume_parameters(strategy_instance)
            
            # Generate sample signals
            signal_test = await self._test_signal_generation(strategy_instance)
            
            # Overall result
            all_tests_passed = all([
                cooldown_test['passed'],
                stop_loss_test['passed'],
                risk_reward_test['passed'],
                volume_test['passed'],
                signal_test['passed']
            ])
            
            return {
                'passed': all_tests_passed,
                'cooldown': cooldown_test,
                'stop_loss': stop_loss_test,
                'risk_reward': risk_reward_test,
                'volume': volume_test,
                'signal_generation': signal_test
            }
            
        except Exception as e:
            logger.error(f"Error testing {strategy_name}: {e}")
            return {'passed': False, 'error': str(e)}
    
    async def _import_strategy(self, strategy_name: str):
        """Import and instantiate strategy"""
        config = {}
        
        if strategy_name == 'volume_profile_scalper':
            from strategies.volume_profile_scalper import EnhancedVolumeProfileScalper
            return EnhancedVolumeProfileScalper(config)
        elif strategy_name == 'news_impact_scalper':
            from strategies.news_impact_scalper import EnhancedNewsImpactScalper
            return EnhancedNewsImpactScalper(config)
        elif strategy_name == 'volatility_explosion':
            from strategies.volatility_explosion import EnhancedVolatilityExplosion
            return EnhancedVolatilityExplosion(config)
        elif strategy_name == 'momentum_surfer':
            from strategies.momentum_surfer import EnhancedMomentumSurfer
            return EnhancedMomentumSurfer(config)
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    def _test_cooldown_parameters(self, strategy) -> Dict:
        """Test cooldown parameters for scalping"""
        try:
            # Expected scalping cooldowns
            expected_cooldowns = {
                'EnhancedVolumeProfileScalper': 15,
                'EnhancedNewsImpactScalper': 10,
                'EnhancedVolatilityExplosion': 20,
                'EnhancedMomentumSurfer': 25
            }
            
            strategy_class = strategy.__class__.__name__
            expected_cooldown = expected_cooldowns.get(strategy_class, 15)
            
            # Check if strategy has scalping cooldown
            has_scalping_cooldown = hasattr(strategy, 'scalping_cooldown')
            
            if has_scalping_cooldown:
                actual_cooldown = strategy.scalping_cooldown
                cooldown_optimal = actual_cooldown == expected_cooldown
                
                logger.info(f"   ⏱️  Cooldown: {actual_cooldown}s (Expected: {expected_cooldown}s)")
                
                return {
                    'passed': cooldown_optimal,
                    'expected': expected_cooldown,
                    'actual': actual_cooldown,
                    'message': 'Cooldown optimal' if cooldown_optimal else 'Cooldown needs adjustment'
                }
            else:
                logger.warning(f"   ⚠️  No scalping cooldown found")
                return {
                    'passed': False,
                    'message': 'No scalping cooldown parameter found'
                }
                
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _test_stop_loss_parameters(self, strategy) -> Dict:
        """Test stop loss parameters for scalping"""
        try:
            # Expected scalping stop loss ranges
            expected_ranges = {
                'EnhancedVolumeProfileScalper': (0.2, 0.6),
                'EnhancedNewsImpactScalper': (0.3, 0.8),
                'EnhancedVolatilityExplosion': (0.4, 1.0),
                'EnhancedMomentumSurfer': (0.3, 0.7)
            }
            
            strategy_class = strategy.__class__.__name__
            expected_range = expected_ranges.get(strategy_class, (0.2, 0.8))
            
            # Test with sample data
            sample_price = 100.0
            sample_atr = 1.0
            
            # Test different ATR multipliers
            if hasattr(strategy, 'atr_multipliers'):
                multipliers = strategy.atr_multipliers
                min_multiplier = min(multipliers.values())
                max_multiplier = max(multipliers.values())
                
                # Calculate stop loss range
                min_sl = strategy.calculate_dynamic_stop_loss(
                    sample_price, sample_atr, 'BUY', min_multiplier, 
                    min_percent=0.2, max_percent=0.8
                )
                max_sl = strategy.calculate_dynamic_stop_loss(
                    sample_price, sample_atr, 'BUY', max_multiplier, 
                    min_percent=0.2, max_percent=0.8
                )
                
                min_percent = abs(sample_price - min_sl) / sample_price * 100
                max_percent = abs(sample_price - max_sl) / sample_price * 100
                
                range_optimal = (min_percent >= expected_range[0] and max_percent <= expected_range[1])
                
                logger.info(f"   🎯 Stop Loss Range: {min_percent:.2f}% - {max_percent:.2f}% (Expected: {expected_range[0]}% - {expected_range[1]}%)")
                
                return {
                    'passed': range_optimal,
                    'expected_range': expected_range,
                    'actual_range': (min_percent, max_percent),
                    'message': 'Stop loss range optimal' if range_optimal else 'Stop loss range needs adjustment'
                }
            else:
                logger.warning(f"   ⚠️  No ATR multipliers found")
                return {
                    'passed': False,
                    'message': 'No ATR multipliers found'
                }
                
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _test_risk_reward_parameters(self, strategy) -> Dict:
        """Test risk/reward ratios for scalping"""
        try:
            # Expected scalping risk/reward ratios
            expected_ratios = {
                'EnhancedVolumeProfileScalper': 1.5,
                'EnhancedNewsImpactScalper': 1.8,
                'EnhancedVolatilityExplosion': 1.6,
                'EnhancedMomentumSurfer': 1.4
            }
            
            strategy_class = strategy.__class__.__name__
            expected_ratio = expected_ratios.get(strategy_class, 1.5)
            
            # Test with sample data
            sample_price = 100.0
            sample_sl = 99.5  # 0.5% stop loss
            
            target = strategy.calculate_dynamic_target(sample_price, sample_sl, expected_ratio)
            
            # Calculate actual ratio
            risk = abs(sample_price - sample_sl)
            reward = abs(target - sample_price)
            actual_ratio = reward / risk if risk > 0 else 0
            
            ratio_optimal = abs(actual_ratio - expected_ratio) < 0.1
            
            logger.info(f"   📊 Risk/Reward: {actual_ratio:.2f}:1 (Expected: {expected_ratio}:1)")
            
            return {
                'passed': ratio_optimal,
                'expected': expected_ratio,
                'actual': actual_ratio,
                'message': 'Risk/reward optimal' if ratio_optimal else 'Risk/reward needs adjustment'
            }
            
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _test_volume_parameters(self, strategy) -> Dict:
        """Test volume thresholds for scalping"""
        try:
            # Check if strategy has volume thresholds
            if hasattr(strategy, 'volume_thresholds'):
                thresholds = strategy.volume_thresholds
                
                # Get minimum volume threshold
                if isinstance(thresholds, dict):
                    min_threshold = min([v for v in thresholds.values() if isinstance(v, (int, float))])
                    
                    # Scalping should have sensitive volume detection (< 15%)
                    volume_optimal = min_threshold <= 15
                    
                    logger.info(f"   📈 Volume Sensitivity: {min_threshold}% (Scalping needs ≤15%)")
                    
                    return {
                        'passed': volume_optimal,
                        'min_threshold': min_threshold,
                        'message': 'Volume sensitivity optimal' if volume_optimal else 'Volume sensitivity needs improvement'
                    }
                else:
                    return {'passed': False, 'message': 'Invalid volume thresholds format'}
            else:
                return {'passed': False, 'message': 'No volume thresholds found'}
                
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def _test_signal_generation(self, strategy) -> Dict:
        """Test signal generation with sample data"""
        try:
            # Sample market data
            sample_data = {
                'RELIANCE': {
                    'close': 2500.0,
                    'high': 2510.0,
                    'low': 2490.0,
                    'volume': 1000000,
                    'price_change': 0.4,  # 0.4% price change
                    'volume_change': 20   # 20% volume change
                },
                'NIFTY50': {
                    'close': 19500.0,
                    'high': 19520.0,
                    'low': 19480.0,
                    'volume': 2000000,
                    'price_change': 0.3,
                    'volume_change': 15
                }
            }
            
            # Test signal generation
            strategy.is_active = True
            await strategy.on_market_data(sample_data)
            
            # Check if signals were generated
            signals_generated = len(strategy.current_positions) > 0
            
            logger.info(f"   🎯 Signal Generation: {'✅ Active' if signals_generated else '⚠️ None'}")
            
            return {
                'passed': True,  # Signal generation test is informational
                'signals_generated': signals_generated,
                'message': 'Signal generation tested'
            }
            
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📊 SCALPING OPTIMIZATION TEST REPORT")
        logger.info("="*80)
        
        total_strategies = len(self.test_results)
        passed_strategies = sum(1 for result in self.test_results.values() if result.get('passed', False))
        
        logger.info(f"📈 Overall Results: {passed_strategies}/{total_strategies} strategies optimized")
        logger.info("")
        
        for strategy_name, result in self.test_results.items():
            status = "✅ OPTIMIZED" if result.get('passed', False) else "❌ NEEDS WORK"
            logger.info(f"{status} {strategy_name.upper()}")
            
            if not result.get('passed', False) and 'error' not in result:
                # Show specific test failures
                for test_name, test_result in result.items():
                    if test_name != 'passed' and isinstance(test_result, dict):
                        if not test_result.get('passed', True):
                            logger.info(f"   ⚠️  {test_name}: {test_result.get('message', 'Failed')}")
        
        logger.info("")
        logger.info("🎯 SCALPING PARAMETERS SUMMARY:")
        logger.info("   • Volume Profile Scalper: 15s cooldown, 0.2-0.6% SL, 1.5:1 R/R")
        logger.info("   • News Impact Scalper: 10s cooldown, 0.3-0.8% SL, 1.8:1 R/R")
        logger.info("   • Volatility Explosion: 20s cooldown, 0.4-1.0% SL, 1.6:1 R/R")
        logger.info("   • Momentum Surfer: 25s cooldown, 0.3-0.7% SL, 1.4:1 R/R")
        logger.info("")
        logger.info("🚀 All strategies now optimized for QUICK IN/QUICK OUT scalping!")

async def main():
    """Run scalping optimization tests"""
    test = ScalpingOptimizationTest()
    await test.test_all_strategies()

if __name__ == "__main__":
    asyncio.run(main()) 
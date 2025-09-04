#!/usr/bin/env python3
"""
TRADING STRATEGY BACKTESTING RUNNER
====================================

Simple backtesting script for all improved trading strategies.
Run this to test your strategies before live trading.

Usage:
    python backtest_runner.py --strategy momentum
    python backtest_runner.py --strategy all
    python backtest_runner.py --strategy nifty --config conservative
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# Import strategies
from strategies.momentum_surfer import EnhancedMomentumSurfer
from strategies.optimized_volume_scalper import OptimizedVolumeScalper
from strategies.volatility_explosion import EnhancedVolatilityExplosion
from strategies.regime_adaptive_controller import RegimeAdaptiveController
from strategies.news_impact_scalper import ProfessionalOptionsSpecialist


class BacktestRunner:
    """Simple backtesting runner for trading strategies"""

    def __init__(self):
        self.strategies = {
            'momentum': EnhancedMomentumSurfer,
            'microstructure': OptimizedVolumeScalper,
            'nifty': EnhancedVolatilityExplosion,
            'regime': RegimeAdaptiveController,
            'options': ProfessionalOptionsSpecialist
        }

    def create_sample_historical_data(self, symbol: str = 'RELIANCE', days: int = 30) -> Dict[str, List]:
        """
        Create sample historical data for backtesting
        In production, replace this with real market data
        """
        print(f"📊 Creating {days} days of sample data for {symbol}...")

        # Generate realistic price data
        base_price = 2500.0  # Sample price
        data_points = []

        current_time = datetime.now()

        for i in range(days * 24):  # Hourly data points
            # Add some realistic price movement
            price_change = np.random.normal(0, 0.02)  # 2% daily volatility
            volume = np.random.randint(10000, 500000)  # Realistic volume

            price = base_price * (1 + price_change * (i / (days * 24)))

            data_point = {
                'timestamp': (current_time - timedelta(hours=i)).isoformat(),
                'symbol': symbol,
                'open': round(price * 0.998, 2),
                'high': round(price * 1.005, 2),
                'low': round(price * 0.995, 2),
                'close': round(price, 2),
                'volume': volume,
                'ltp': round(price, 2),
                'change_percent': round(price_change * 100, 2)
            }

            data_points.append(data_point)

        return {symbol: data_points[::-1]}  # Reverse to chronological order

    def create_conservative_config(self, strategy_name: str) -> Dict:
        """Create conservative configuration for safe backtesting"""
        base_config = {
            'backtest_mode': True,
            'max_daily_loss': -1000,  # Conservative loss limit
            'max_daily_trades': 5,    # Limited trades for safety
            'max_consecutive_losses': 2
        }

        # Strategy-specific conservative settings
        if strategy_name == 'momentum':
            base_config.update({
                'momentum_threshold': 0.025,  # Higher threshold (more selective)
                'profit_booking_threshold': 0.25,
                'stop_loss_threshold': 0.15
            })
        elif strategy_name == 'microstructure':
            base_config.update({
                'volatility_cluster_threshold': 1.8,  # Higher threshold
                'order_flow_imbalance_threshold': 0.8,
                'min_liquidity_threshold': 300000  # Higher liquidity requirement
            })
        elif strategy_name == 'nifty':
            base_config.update({
                'nifty_target_points': 40,  # Smaller targets
                'nifty_stop_points': 20,    # Wider stops
                'max_daily_loss': -1500
            })
        elif strategy_name == 'options':
            base_config.update({
                'iv_rank_threshold': 40,  # Higher IV requirement
                'profit_target': 0.30,    # Lower profit target
                'stop_loss': 0.25
            })

        return base_config

    def run_single_strategy_backtest(self, strategy_name: str, config_name: str = 'conservative'):
        """Run backtest for a single strategy"""
        print(f"\n{'='*60}")
        print(f"🚀 BACKTESTING: {strategy_name.upper()} STRATEGY")
        print(f"{'='*60}")

        try:
            # Get strategy class
            strategy_class = self.strategies.get(strategy_name.lower())
            if not strategy_class:
                print(f"❌ Strategy '{strategy_name}' not found!")
                return None

            # Create configuration
            config = self.create_conservative_config(strategy_name)
            print(f"⚙️ Configuration: {config_name}")
            print(f"📊 Key Parameters: {json.dumps(config, indent=2, default=str)}")

            # Initialize strategy
            strategy = strategy_class(config)
            print(f"✅ Strategy initialized: {strategy.name}")

            # Create sample historical data
            historical_data = self.create_sample_historical_data()

            # Run backtest
            print("\n🔬 Running backtest...")
            start_time = datetime.now()

            import asyncio
            results = asyncio.run(strategy.run_backtest(historical_data))

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Print results
            print(f"\n✅ BACKTEST COMPLETED in {duration:.1f} seconds")
            print(f"📊 Results: {json.dumps(results, indent=2, default=str)}")

            # Get detailed report
            report = strategy.get_backtest_report()
            print(f"\n📋 DETAILED REPORT:")
            print(report)

            # Get risk status
            risk_report = strategy.get_risk_status_report()
            print(f"\n🛡️ RISK STATUS:")
            print(risk_report)

            # Performance assessment
            self.assess_performance(results, strategy_name)

            return results

        except Exception as e:
            print(f"❌ Backtest failed for {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_all_strategies_backtest(self):
        """Run backtest for all strategies"""
        print("🎯 RUNNING COMPREHENSIVE BACKTEST SUITE")
        print("=" * 60)

        results = {}
        for strategy_name in self.strategies.keys():
            try:
                result = self.run_single_strategy_backtest(strategy_name, 'conservative')
                if result:
                    results[strategy_name] = result
            except Exception as e:
                print(f"❌ Failed to backtest {strategy_name}: {e}")

        # Summary comparison
        self.print_comparison_summary(results)

    def assess_performance(self, results: Dict, strategy_name: str):
        """Assess backtest performance and provide recommendations"""
        print(f"\n🎯 PERFORMANCE ASSESSMENT: {strategy_name.upper()}")

        # Key metrics to check
        win_rate = results.get('win_rate', 0)
        profit_factor = results.get('profit_factor', 0)
        max_drawdown = results.get('max_drawdown', 0)
        total_pnl = results.get('total_pnl', 0)
        total_signals = results.get('total_signals', 0)

        # Assessment criteria
        assessment = {
            'win_rate': 'PASS' if win_rate >= 0.55 else 'REVIEW',
            'profit_factor': 'PASS' if profit_factor >= 1.5 else 'REVIEW',
            'max_drawdown': 'PASS' if max_drawdown <= 1000 else 'REVIEW',
            'total_signals': 'PASS' if total_signals >= 10 else 'REVIEW'
        }

        print("📊 METRICS:")
        print(f"  Win Rate: {win_rate:.1%} ({assessment['win_rate']})")
        print(f"  Profit Factor: {profit_factor:.2f} ({assessment['profit_factor']})")
        print(f"  Max Drawdown: ₹{max_drawdown:.0f} ({assessment['max_drawdown']})")
        print(f"  Total Signals: {total_signals} ({assessment['total_signals']})")

        # Overall assessment
        failed_checks = [k for k, v in assessment.items() if v == 'REVIEW']
        if not failed_checks:
            print("✅ OVERALL: STRATEGY PASSES ALL CRITERIA - READY FOR LIVE TESTING")
        else:
            print(f"⚠️ OVERALL: {len(failed_checks)} metrics need review before live testing")
            print(f"   Areas to improve: {', '.join(failed_checks)}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if win_rate < 0.55:
            print("   - Increase selectivity (higher thresholds)")
        if profit_factor < 1.5:
            print("   - Improve risk-reward ratio")
        if max_drawdown > 1000:
            print("   - Reduce position sizes")
        if total_signals < 10:
            print("   - Review market conditions or data quality")

    def print_comparison_summary(self, results: Dict):
        """Print comparison summary of all strategies"""
        print(f"\n{'='*80}")
        print("🎯 STRATEGY COMPARISON SUMMARY")
        print(f"{'='*80}")

        if not results:
            print("❌ No successful backtests to compare")
            return

        print(f"{'Strategy':<20} {'Win Rate':<10} {'Profit Factor':<15} {'Max DD':<10} {'Signals':<8}")
        print("-" * 80)

        for strategy_name, result in results.items():
            win_rate = result.get('win_rate', 0)
            profit_factor = result.get('profit_factor', 0)
            max_dd = result.get('max_drawdown', 0)
            signals = result.get('total_signals', 0)

            print(f"{strategy_name:<20} {win_rate:<10.1%} {profit_factor:<15.2f} ₹{max_dd:<10.0f} {signals:<8}")

        # Best performers
        best_win_rate = max(results.items(), key=lambda x: x[1].get('win_rate', 0))
        best_profit_factor = max(results.items(), key=lambda x: x[1].get('profit_factor', 0))

        print(f"\n🏆 BEST PERFORMERS:")
        print(f"   Highest Win Rate: {best_win_rate[0]} ({best_win_rate[1]['win_rate']:.1%})")
        print(f"   Best Profit Factor: {best_profit_factor[0]} ({best_profit_factor[1]['profit_factor']:.2f})")


def main():
    """Main backtesting function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backtest_runner.py --strategy momentum")
        print("  python backtest_runner.py --strategy all")
        print("  python backtest_runner.py --strategy nifty --config conservative")
        print("\nAvailable strategies:")
        print("  - momentum (Enhanced Momentum Surfer)")
        print("  - microstructure (Volume Scalper)")
        print("  - nifty (Nifty Intelligence Engine)")
        print("  - regime (Regime Adaptive Controller)")
        print("  - options (Options Specialist)")
        return

    runner = BacktestRunner()

    # Parse arguments
    strategy_name = None
    config_name = 'conservative'

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--strategy':
            strategy_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--config':
            config_name = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if strategy_name == 'all':
        runner.run_all_strategies_backtest()
    elif strategy_name:
        runner.run_single_strategy_backtest(strategy_name, config_name)
    else:
        print("❌ Please specify a strategy name or 'all'")


if __name__ == "__main__":
    main()

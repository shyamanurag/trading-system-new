#!/usr/bin/env python3
"""
SIMPLE BACKTEST DEMO
===================

Quick demonstration of backtesting your improved strategies.
This creates sample data and runs a basic backtest.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.momentum_surfer import EnhancedMomentumSurfer
from datetime import datetime, timedelta
import numpy as np


def create_sample_data():
    """Create sample historical data"""
    print("📊 Creating sample historical data...")

    data = []
    base_price = 2500.0
    current_time = datetime.now()

    # Create 30 days of hourly data
    for i in range(30 * 24):
        # Realistic price movement
        price_change = np.random.normal(0, 0.015)  # 1.5% daily volatility
        volume = np.random.randint(50000, 300000)

        price = base_price * (1 + price_change * (i / (30 * 24)))

        data_point = {
            'timestamp': (current_time - timedelta(hours=i)).isoformat(),
            'symbol': 'RELIANCE',
            'open': round(price * 0.998, 2),
            'high': round(price * 1.003, 2),
            'low': round(price * 0.997, 2),
            'close': round(price, 2),
            'volume': volume,
            'ltp': round(price, 2),
            'change_percent': round(price_change * 100, 2)
        }
        data.append(data_point)

    return {'RELIANCE': data[::-1]}  # Reverse for chronological order


def run_momentum_backtest():
    """Run momentum strategy backtest"""
    print("🚀 MOMENTUM STRATEGY BACKTEST")
    print("=" * 50)

    # Conservative configuration for backtesting
    config = {
        'backtest_mode': True,
        'momentum_threshold': 0.025,  # Higher threshold (more selective)
        'max_daily_loss': -1000,      # Conservative loss limit
        'max_daily_trades': 5,        # Limited trades for safety
        'max_consecutive_losses': 2
    }

    print(f"⚙️ Configuration: {config}")

    try:
        # Initialize strategy
        strategy = EnhancedMomentumSurfer(config)
        print(f"✅ Strategy initialized: {strategy.name}")

        # Create sample data
        historical_data = create_sample_data()

        # Run backtest
        print("\n🔬 Running backtest...")
        start_time = datetime.now()

        import asyncio
        results = asyncio.run(strategy.run_backtest(historical_data))

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ BACKTEST COMPLETED in {duration:.1f} seconds")

        # Display key results
        print("\n📊 KEY RESULTS:")
        print(f"  Total Signals: {results.get('total_signals', 0)}")
        print(f"  Win Rate: {results.get('win_rate', 0):.1%}")
        print(f"  Profit Factor: {results.get('profit_factor', 0):.2f}")
        print(f"  Max Drawdown: ₹{results.get('max_drawdown', 0):.0f}")
        print(f"  Total P&L: ₹{results.get('total_pnl', 0):,.2f}")

        # Performance assessment
        win_rate = results.get('win_rate', 0)
        profit_factor = results.get('profit_factor', 0)
        max_drawdown = results.get('max_drawdown', 0)

        print("\n🎯 ASSESSMENT:")
        if win_rate >= 0.55 and profit_factor >= 1.5 and max_drawdown <= 1000:
            print("✅ STRATEGY PASSES ALL CRITERIA - READY FOR LIVE TESTING")
        else:
            print("⚠️ STRATEGY NEEDS PARAMETER TUNING")
            if win_rate < 0.55:
                print("   - Win rate below 55% - increase selectivity")
            if profit_factor < 1.5:
                print("   - Profit factor below 1.5 - improve risk-reward")
            if max_drawdown > 1000:
                print("   - Drawdown too high - reduce position sizes")

        # Show risk status
        print("\n🛡️ CURRENT RISK STATUS:")
        risk_report = strategy.get_risk_status_report()
        print(risk_report)

        return results

    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def show_usage_examples():
    """Show usage examples"""
    print("\n" + "="*60)
    print("📚 BACKTESTING USAGE EXAMPLES")
    print("="*60)

    examples = [
        "# Test momentum strategy",
        "python simple_backtest.py momentum",
        "",
        "# Test all strategies",
        "python simple_backtest.py all",
        "",
        "# Test with custom configuration",
        "from strategies.momentum_surfer import EnhancedMomentumSurfer",
        "config = {'momentum_threshold': 0.03, 'max_daily_loss': -800}",
        "strategy = EnhancedMomentumSurfer(config)",
        "results = strategy.run_backtest(historical_data)",
        "print(strategy.get_backtest_report())",
        "",
        "# Get risk status during live trading",
        "risk_status = strategy.get_risk_status_report()",
        "print(risk_status)"
    ]

    for example in examples:
        print(example)


def main():
    """Main function"""
    if len(sys.argv) > 1:
        strategy_name = sys.argv[1].lower()

        if strategy_name == 'momentum':
            run_momentum_backtest()
        elif strategy_name == 'all':
            print("Running all strategies...")
            run_momentum_backtest()
            print("\n" + "="*50)
            print("Add other strategies here...")
        else:
            print(f"Unknown strategy: {strategy_name}")
            show_usage_examples()
    else:
        print("🔬 SIMPLE BACKTEST DEMO")
        print("="*50)
        print("Running momentum strategy backtest with sample data...")
        print()

        run_momentum_backtest()
        show_usage_examples()


if __name__ == "__main__":
    main()

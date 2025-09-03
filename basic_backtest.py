#!/usr/bin/env python3
"""
BASIC BACKTEST DEMO - Simple Example
====================================

Ultra-simple backtesting example for one strategy.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
import numpy as np

# Add the project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_sample_data():
    """Create simple sample data"""
    print("📊 Creating sample data...")
    data = []
    base_price = 2500.0

    # Create 100 data points
    for i in range(100):
        price_change = np.random.normal(0, 0.01)  # 1% volatility
        price = base_price * (1 + price_change)
        volume = np.random.randint(50000, 200000)

        data.append({
            'close': round(price, 2),
            'volume': volume,
            'change_percent': round(price_change * 100, 2)
        })

    return {'RELIANCE': data}


async def demo_backtest():
    """Demonstrate backtesting"""
    print("🚀 BASIC BACKTEST DEMO")
    print("=" * 40)

    try:
        # Import strategy directly (avoid __init__.py issues)
        from strategies.momentum_surfer import EnhancedMomentumSurfer

        # Simple config
        config = {
            'backtest_mode': True,
            'momentum_threshold': 0.02,
            'max_daily_loss': -1000,
            'max_daily_trades': 5
        }

        print("⚙️ Config:", config)

        # Create strategy
        strategy = EnhancedMomentumSurfer(config)
        print(f"✅ Strategy created: {strategy.name}")

        # Create sample data
        data = create_sample_data()
        print(f"📊 Sample data created: {len(data['RELIANCE'])} points")

        # Run backtest
        print("\n🔬 Running backtest...")
        start_time = datetime.now()

        results = await strategy.run_backtest(data)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ BACKTEST COMPLETED in {duration:.1f} seconds")

        # Show results
        print("\n📊 RESULTS:")
        print(f"  Signals: {results.get('total_signals', 0)}")
        print(f"  Win Rate: {results.get('win_rate', 0):.1%}")
        print(f"  Profit Factor: {results.get('profit_factor', 0):.2f}")
        print(f"  Total P&L: ₹{results.get('total_pnl', 0):,.0f}")

        # Show risk status
        risk_report = strategy.get_risk_status_report()
        print("\n🛡️ RISK STATUS:")
        print(risk_report)

        return results

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    print("🔬 BASIC BACKTEST DEMO")
    print("This demonstrates how to backtest your improved strategies.\n")

    # Run the demo
    results = asyncio.run(demo_backtest())

    if results:
        print("\n✅ SUCCESS! Your strategy backtesting is working.")
        print("💡 Next steps:")
        print("   1. Replace sample data with real market data")
        print("   2. Adjust strategy parameters based on results")
        print("   3. Test multiple strategies")
        print("   4. Run with real money (conservatively)")
    else:
        print("\n❌ Backtest failed. Check error messages above.")


if __name__ == "__main__":
    main()

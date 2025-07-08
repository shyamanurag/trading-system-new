#!/usr/bin/env python3
"""
Live Trade Monitoring
====================
Monitor real-time signal generation and trade execution
"""

import requests
import time
import json
from datetime import datetime

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def get_live_trading_status():
    """Get current live trading status"""
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error getting trading status: {e}")
        return None

def get_recent_signals():
    """Get recent trading signals"""
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/signals/recent", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error getting signals: {e}")
        return None

def get_market_data():
    """Get current market data"""
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/market-data", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error getting market data: {e}")
        return None

def monitor_live_system():
    """Monitor live trading system"""
    print("📊 LIVE TRADING SYSTEM MONITOR")
    print("=" * 50)
    
    # Get trading status
    trading_status = get_live_trading_status()
    if trading_status and trading_status.get('success'):
        data = trading_status['data']
        
        print(f"🎯 SYSTEM STATUS:")
        print(f"   ✅ Active: {data.get('is_active', False)}")
        print(f"   ✅ System Ready: {data.get('system_ready', False)}")
        print(f"   📊 Market: {data.get('market_status', 'unknown')}")
        print(f"   🎯 Active Strategies: {len(data.get('active_strategies', []))}")
        print(f"   💰 Daily PnL: ${data.get('daily_pnl', 0):,.2f}")
        print(f"   📈 Total Trades: {data.get('total_trades', 0)}")
        print(f"   🏛️ Active Positions: {len(data.get('active_positions', []))}")
        
        # Show strategies
        strategies = data.get('active_strategies', [])
        print(f"\n🎯 ACTIVE STRATEGIES ({len(strategies)}):")
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")
        
        # Risk status
        risk = data.get('risk_status', {})
        print(f"\n🛡️ RISK STATUS:")
        print(f"   Status: {risk.get('status', 'unknown')}")
        print(f"   Max Daily Loss: ${risk.get('max_daily_loss', 0):,}")
        print(f"   Current Exposure: ${risk.get('current_exposure', 0):,}")
        
    else:
        print("❌ Could not get trading status")
        return False
    
    # Get market data
    market_data = get_market_data()
    if market_data:
        symbol_count = len(market_data) if isinstance(market_data, dict) else 0
        print(f"\n📈 MARKET DATA:")
        print(f"   📊 Active Symbols: {symbol_count}")
        
        if symbol_count > 0:
            # Show sample symbols with prices
            sample_symbols = list(market_data.keys())[:5]
            print(f"   💹 Sample Prices:")
            for symbol in sample_symbols:
                price_data = market_data[symbol]
                current_price = price_data.get('ltp', price_data.get('close', 0))
                print(f"      {symbol}: ₹{current_price}")
    
    # Get recent signals
    signals = get_recent_signals()
    if signals:
        print(f"\n📡 RECENT SIGNALS:")
        if isinstance(signals, dict) and 'signals' in signals:
            signal_list = signals['signals']
            print(f"   📊 Total Signals: {len(signal_list)}")
            
            # Show recent signals
            for signal in signal_list[-5:]:  # Last 5 signals
                symbol = signal.get('symbol', 'UNKNOWN')
                action = signal.get('action', 'UNKNOWN')
                confidence = signal.get('confidence', 0)
                strategy = signal.get('strategy', 'UNKNOWN')
                timestamp = signal.get('timestamp', '')
                
                print(f"      📊 {symbol} {action} (Conf: {confidence:.1f}%) - {strategy}")
        else:
            print("   ℹ️ No recent signals")
    
    print(f"\n⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    return True

def continuous_monitor():
    """Continuously monitor the live system"""
    print("🔄 STARTING CONTINUOUS MONITOR...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            print("\n" + "="*60)
            success = monitor_live_system()
            
            if success:
                print("\n✅ Monitor cycle completed")
            else:
                print("\n❌ Monitor cycle failed")
            
            print("⏱️ Waiting 30 seconds for next update...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")

if __name__ == "__main__":
    # Single check
    monitor_live_system()
    
    # Ask if user wants continuous monitoring
    print("\n" + "="*50)
    response = input("Start continuous monitoring? (y/n): ").lower().strip()
    
    if response == 'y':
        continuous_monitor()
    else:
        print("📊 Single check completed") 
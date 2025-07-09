#!/usr/bin/env python3
"""
Quick Deployed System Check
"""

import requests
import json

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_deployed_status():
    """Check deployed system trading status"""
    print("🔍 DEPLOYED SYSTEM STATUS CHECK")
    print("=" * 40)
    
    try:
        # Test trading status endpoint
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                trading_data = data['data']
                print(f"✅ API Response: {response.status_code}")
                print(f"📊 Active Strategies: {len(trading_data.get('active_strategies', []))}")
                print(f"📊 Strategy Names: {trading_data.get('active_strategies', [])}")
                print(f"📊 System Ready: {trading_data.get('system_ready', False)}")
                print(f"📊 Is Active: {trading_data.get('is_active', False)}")
                print(f"📊 Market Status: {trading_data.get('market_status', 'Unknown')}")
                print(f"📊 Total Trades: {trading_data.get('total_trades', 0)}")
                print(f"📊 Daily PNL: {trading_data.get('daily_pnl', 0.0)}")
                
                return trading_data
            else:
                print(f"❌ Unexpected response format: {data}")
                return None
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def check_market_data():
    """Check if market data is flowing"""
    print(f"\n📈 MARKET DATA CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/market-data/symbols", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            symbols = len(data) if isinstance(data, dict) else 0
            print(f"✅ Market Data: {symbols} symbols")
            
            if symbols > 0:
                # Show sample symbols
                sample_symbols = list(data.keys())[:3]
                print(f"Sample symbols: {sample_symbols}")
                return True
            else:
                print(f"❌ No market data symbols")
                return False
        else:
            print(f"❌ Market Data Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Market Data Error: {e}")
        return False

def main():
    """Main function"""
    trading_status = check_deployed_status()
    market_data_ok = check_market_data()
    
    print(f"\n🎯 SUMMARY")
    print("=" * 20)
    
    if trading_status:
        active_strategies = len(trading_status.get('active_strategies', []))
        total_trades = trading_status.get('total_trades', 0)
        
        print(f"📊 Strategies: {active_strategies} active")
        print(f"📊 Trades: {total_trades} executed")
        
        if active_strategies == 0:
            print(f"🚨 CRITICAL: No active strategies")
            print(f"💡 IMMEDIATE ACTION NEEDED:")
            print(f"   1. Check strategy initialization logs")
            print(f"   2. Verify orchestrator startup")
            print(f"   3. Test strategy loading manually")
        else:
            print(f"✅ Strategies are active")
            
        if total_trades == 0:
            print(f"⚠️ No trades executed yet")
            print(f"💡 Check signal generation and market conditions")
        else:
            print(f"✅ Trading is active")
            
    else:
        print(f"❌ Could not get trading status")
    
    if market_data_ok:
        print(f"✅ Market data is flowing")
    else:
        print(f"⚠️ Market data issues detected")

if __name__ == "__main__":
    main() 
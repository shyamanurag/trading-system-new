#!/usr/bin/env python3
"""
Quick Deployed System Check
"""

import requests
import json

DEPLOYED_URL = "https://trading-system-new-production.onrender.com"

def check_deployed_status():
    """Check deployed system trading status"""
    print("🔍 DEPLOYED SYSTEM STATUS CHECK")
    print("=" * 40)
    
    try:
        # Test trading status endpoint
        response = requests.get(f"{DEPLOYED_URL}/api/v1/trading/status", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"📊 Active Strategies: {data.get('active_strategies', [])}")
            print(f"📊 Total Strategies: {data.get('total_strategies', 0)}")
            print(f"📊 System Ready: {data.get('system_ready', False)}")
            print(f"📊 Is Active: {data.get('is_active', False)}")
            print(f"📊 Market Status: {data.get('market_status', 'Unknown')}")
            
            # Show strategy details if available
            if 'strategy_details' in data and data['strategy_details']:
                print(f"\n📋 Strategy Details:")
                for strategy in data['strategy_details']:
                    name = strategy.get('name', 'Unknown')
                    active = strategy.get('active', False)
                    status = strategy.get('status', 'Unknown')
                    initialized = strategy.get('initialized', False)
                    print(f"   {name}: {status} (Active: {active}, Init: {initialized})")
            else:
                print(f"\n❌ No strategy details found")
                
            return data
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
        response = requests.get(f"{DEPLOYED_URL}/api/v1/market-data", timeout=15)
        
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
        total_strategies = trading_status.get('total_strategies', 0)
        
        print(f"📊 Strategies: {active_strategies}/{total_strategies} active")
        
        if active_strategies == 0:
            print(f"🚨 CRITICAL: No active strategies")
            print(f"💡 IMMEDIATE ACTION NEEDED:")
            print(f"   1. Check strategy initialization logs")
            print(f"   2. Verify orchestrator startup")
            print(f"   3. Test strategy loading manually")
        else:
            print(f"✅ Strategies are active")
            
    else:
        print(f"❌ Could not get trading status")
    
    if market_data_ok:
        print(f"✅ Market data is flowing")
    else:
        print(f"⚠️ Market data issues detected")

if __name__ == "__main__":
    main() 
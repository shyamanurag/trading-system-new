#!/usr/bin/env python3
"""
Debug TrueData Symbols - Check what symbols are actually available
"""

import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def debug_truedata():
    """Debug TrueData symbol availability"""
    print("🔍 DEBUGGING TRUEDATA SYMBOLS")
    print("=" * 50)
    
    # Get TrueData status with detailed info
    try:
        response = requests.get(f"{BASE_URL}/api/v1/truedata/truedata/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print("📊 TrueData Status:")
            print(json.dumps(status_data, indent=2))
            
            # Check what symbols are actually subscribed
            data = status_data.get('data', {})
            connected = data.get('connected', False)
            total_symbols = data.get('total_symbols', 0)
            subscribed = data.get('subscribed_symbols', [])
            
            print(f"\n🔌 Connected: {connected}")
            print(f"📈 Total Symbols: {total_symbols}")
            print(f"📋 Subscribed Symbols: {subscribed}")
            
        else:
            print(f"❌ Status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    # Check what the market indices API sees
    print("\n" + "=" * 50)
    print("🔍 MARKET INDICES API DEBUG")
    
    try:
        response = requests.get(f"{BASE_URL}/api/market/indices", timeout=10)
        if response.status_code == 200:
            indices_data = response.json()
            
            # Extract TrueData connection info
            truedata_info = indices_data.get('data', {}).get('truedata_connection', {})
            
            print("📊 Market API TrueData Info:")
            print(json.dumps(truedata_info, indent=2))
            
            symbols_available = truedata_info.get('symbols_available', 0)
            live_symbols = truedata_info.get('live_data_symbols', [])
            nifty_available = truedata_info.get('nifty_available', False)
            banknifty_available = truedata_info.get('banknifty_available', False)
            
            print(f"\n📈 Symbols Available: {symbols_available}")
            print(f"📋 Live Data Symbols: {live_symbols}")
            print(f"🎯 NIFTY-I Available: {nifty_available}")
            print(f"🎯 BANKNIFTY-I Available: {banknifty_available}")
            
            # Show actual index data
            indices = indices_data.get('data', {}).get('indices', [])
            print(f"\n📊 Index Data:")
            for idx in indices:
                symbol = idx.get('symbol')
                price = idx.get('last_price')
                status = idx.get('status')
                print(f"   {symbol}: ₹{price} ({status})")
                
        else:
            print(f"❌ Market indices check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting market indices: {e}")

if __name__ == "__main__":
    debug_truedata() 
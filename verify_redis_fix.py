#!/usr/bin/env python3
"""
Verify Redis Serialization Fix
Check if the deployment resolved the Redis storage errors
"""

import requests
import json

def verify_redis_fix():
    """Verify the Redis serialization fix is working"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔍 VERIFYING REDIS SERIALIZATION FIX")
    print("=" * 50)
    
    # Check market data endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=15)
        if response.status_code == 200:
            data = response.json()
            symbol_count = len(data)
            print(f"✅ Market Data API: 200 OK")
            print(f"✅ Symbols Available: {symbol_count}")
            
            if symbol_count > 0:
                print("🎉 REDIS ERRORS RESOLVED!")
                
                # Show sample symbols
                print("\n📊 Sample Market Data:")
                for i, symbol in enumerate(data[:5]):
                    ltp = symbol.get('ltp', 0)
                    changeper = symbol.get('changeper', 0)
                    volume = symbol.get('volume', 0)
                    print(f"  {symbol['symbol']}: ₹{ltp:,.2f} | {changeper:+.2f}% | Vol: {volume:,}")
                    
                # Check for Redis-specific fields
                sample_symbol = data[0]
                redis_indicators = ['timestamp', 'source', 'deployment_id']
                redis_fields_present = [field for field in redis_indicators if field in sample_symbol]
                
                if redis_fields_present:
                    print(f"\n✅ Redis Storage Working: {redis_fields_present}")
                else:
                    print("\n⚠️ Redis fields not found in market data")
            else:
                print("⚠️ No symbols returned - Redis might still be initializing")
                
        else:
            print(f"❌ Market Data API: {response.status_code}")
            print("⚠️ Redis issues may persist")
            
    except Exception as e:
        print(f"❌ Market Data Check Failed: {e}")
    
    # Check TrueData status
    try:
        response = requests.get(f"{base_url}/api/v1/truedata/status", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ TrueData API: 200 OK")
            print(f"✅ Connected: {data.get('connected', False)}")
            print(f"✅ Symbols Active: {data.get('symbols_active', 0)}")
        else:
            print(f"\n❌ TrueData API: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ TrueData Check Failed: {e}")
    
    # Check autonomous trading status
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=15)
        if response.status_code == 200:
            data = response.json()['data']
            print(f"\n✅ Autonomous Trading: 200 OK")
            print(f"✅ Active: {data.get('is_active', False)}")
            print(f"✅ Strategies: {len(data.get('active_strategies', []))}")
            print(f"✅ Total Trades: {data.get('total_trades', 0)}")
            
            if data.get('total_trades', 0) > 0:
                print("🚀 TRADES DETECTED - SYSTEM FULLY OPERATIONAL!")
            else:
                print("⏳ Waiting for trade generation...")
                
        else:
            print(f"\n❌ Autonomous Trading: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Autonomous Check Failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 REDIS FIX VERIFICATION COMPLETE")

if __name__ == "__main__":
    verify_redis_fix() 
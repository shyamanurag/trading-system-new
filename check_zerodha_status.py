#!/usr/bin/env python3
import requests
import json

try:
    print("🔍 Checking deployed app status...")
    r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
    print(f'HTTP Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'🎯 System Status:')
        print(f'  Active: {data["data"]["is_active"]}')
        print(f'  Total Trades: {data["data"]["total_trades"]}')
        print(f'  Strategies: {data["data"]["active_strategies_count"]}')
        print(f'  System Ready: {data["data"].get("system_ready", "Unknown")}')
        
        # Check broker status
        broker_status = data["data"].get("broker_status", "Unknown")
        print(f'  Broker Status: {broker_status}')
        
        # Check if there are any details about why no trades
        if data["data"]["total_trades"] == 0:
            print("\n❌ ZERO TRADES - Need to investigate why")
            print("Possible causes:")
            print("1. Zerodha not connected")
            print("2. OrderManager not processing signals")
            print("3. Signals not reaching trade engine")
            print("4. Market conditions not generating trades")
        
        # Print full response for debugging
        print(f"\n📋 Full Response:")
        print(json.dumps(data, indent=2)[:1000] + "...")
        
    else:
        print(f"❌ Error: {r.status_code}")
        print(f"Response: {r.text}")
        
except Exception as e:
    print(f"❌ Error checking status: {e}")
    import traceback
    traceback.print_exc() 
import requests
import json

try:
    print("🔍 Checking deployed app status...")
    r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
    print(f'HTTP Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'🎯 System Status:')
        print(f'  Active: {data["data"]["is_active"]}')
        print(f'  Total Trades: {data["data"]["total_trades"]}')
        print(f'  Strategies: {data["data"]["active_strategies_count"]}')
        print(f'  System Ready: {data["data"].get("system_ready", "Unknown")}')
        
        # Check broker status
        broker_status = data["data"].get("broker_status", "Unknown")
        print(f'  Broker Status: {broker_status}')
        
        # Check if there are any details about why no trades
        if data["data"]["total_trades"] == 0:
            print("\n❌ ZERO TRADES - Need to investigate why")
            print("Possible causes:")
            print("1. Zerodha not connected")
            print("2. OrderManager not processing signals")
            print("3. Signals not reaching trade engine")
            print("4. Market conditions not generating trades")
        
        # Print full response for debugging
        print(f"\n📋 Full Response:")
        print(json.dumps(data, indent=2)[:1000] + "...")
        
    else:
        print(f"❌ Error: {r.status_code}")
        print(f"Response: {r.text}")
        
except Exception as e:
    print(f"❌ Error checking status: {e}")
    import traceback
    traceback.print_exc() 
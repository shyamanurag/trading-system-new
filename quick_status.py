#!/usr/bin/env python3
import requests

try:
    r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'Total Trades: {data["data"]["total_trades"]}')
        print(f'Active: {data["data"]["is_active"]}')
        print(f'Strategies: {data["data"]["active_strategies_count"]}')
        
        if data["data"]["total_trades"] == 0:
            print("❌ ZERO TRADES CONFIRMED - Likely due to expired Zerodha token")
        else:
            print("✅ TRADES DETECTED")
    else:
        print(f"Error: {r.text}")
        
except Exception as e:
    print(f"Error: {e}") 
import requests

try:
    r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'Total Trades: {data["data"]["total_trades"]}')
        print(f'Active: {data["data"]["is_active"]}')
        print(f'Strategies: {data["data"]["active_strategies_count"]}')
        
        if data["data"]["total_trades"] == 0:
            print("❌ ZERO TRADES CONFIRMED - Likely due to expired Zerodha token")
        else:
            print("✅ TRADES DETECTED")
    else:
        print(f"Error: {r.text}")
        
except Exception as e:
    print(f"Error: {e}") 
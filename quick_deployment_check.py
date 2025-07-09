#!/usr/bin/env python3
"""
Quick Deployment Check - Verify Redis Fix
"""

import requests
import json

def check_deployment():
    print("🔍 DEPLOYMENT STATUS CHECK")
    print("=" * 40)
    
    url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check autonomous status
    try:
        response = requests.get(f"{url}/api/v1/autonomous/status", timeout=10)
        print(f"Autonomous: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Active: {data.get('is_active', False)}")
            print(f"  Strategies: {data.get('active_strategies', 0)}")
            print(f"  Trades: {data.get('total_trades', 0)}")
    except Exception as e:
        print(f"Autonomous: ERROR - {e}")
    
    # Check market data
    try:
        response = requests.get(f"{url}/api/v1/market-data", timeout=10)
        print(f"Market Data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            print(f"  Symbols: {count}")
            if count > 0:
                print("  ✅ REDIS ERRORS RESOLVED!")
            else:
                print("  ⚠️ No symbols returned")
    except Exception as e:
        print(f"Market Data: ERROR - {e}")
    
    # Check TrueData status
    try:
        response = requests.get(f"{url}/api/v1/truedata/status", timeout=10)
        print(f"TrueData: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Connected: {data.get('connected', False)}")
            print(f"  Symbols Active: {data.get('symbols_active', 0)}")
    except Exception as e:
        print(f"TrueData: ERROR - {e}")

if __name__ == "__main__":
    check_deployment() 
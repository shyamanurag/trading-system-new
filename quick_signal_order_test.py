#!/usr/bin/env python3
"""
Quick Signal and Order Processing Test
"""

import requests
import json
import time

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_system():
    print("🚀 SIGNAL & ORDER PROCESSING TEST")
    print("=" * 40)
    
    # Test 1: System Status
    print("\n1. SYSTEM STATUS")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/autonomous/status")
        print(f"   Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()['data']
            print(f"   Active: {data.get('is_active', False)}")
            print(f"   Strategies: {data.get('active_strategies_count', 0)}")
            print(f"   Total Trades: {data.get('total_trades', 0)}")
        else:
            print(f"   Error: {r.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Broker Status
    print("\n2. BROKER STATUS")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/broker/status")
        print(f"   Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Broker: {data.get('broker', 'Unknown')}")
            print(f"   Connected: {data.get('status', 'Unknown')}")
            print(f"   API Calls: {data.get('api_calls_today', 0)}")
        else:
            print(f"   Error: {r.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Signals
    print("\n3. SIGNALS")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/signals")
        print(f"   Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            signals = data.get('data', [])
            print(f"   Signals Count: {len(signals)}")
            if signals:
                latest = signals[0]
                print(f"   Latest: {latest.get('symbol', 'N/A')} {latest.get('action', 'N/A')}")
        else:
            print(f"   Error: {r.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 4: Orders
    print("\n4. ORDERS")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/autonomous/orders")
        print(f"   Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            orders = data.get('data', [])
            print(f"   Orders Count: {len(orders)}")
            if orders:
                latest = orders[0]
                print(f"   Latest: {latest.get('symbol', 'N/A')} - {latest.get('status', 'N/A')}")
        else:
            print(f"   Error: {r.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 5: Start Trading & Monitor
    print("\n5. START TRADING & MONITOR")
    try:
        print("   🚀 Starting autonomous trading...")
        r = requests.post(f"{BASE_URL}/api/v1/autonomous/start")
        print(f"   Start Status: {r.status_code}")
        
        if r.status_code == 200:
            print("   ✅ Started successfully")
            
            # Monitor for 15 seconds
            print("   ⏰ Monitoring for 15 seconds...")
            for i in range(3):
                time.sleep(5)
                
                # Check status
                status_r = requests.get(f"{BASE_URL}/api/v1/autonomous/status")
                broker_r = requests.get(f"{BASE_URL}/api/v1/broker/status")
                
                trades = 0
                api_calls = 0
                
                if status_r.status_code == 200:
                    trades = status_r.json()['data'].get('total_trades', 0)
                
                if broker_r.status_code == 200:
                    api_calls = broker_r.json().get('api_calls_today', 0)
                
                print(f"   Check {i+1}: Trades={trades}, API Calls={api_calls}")
                
                if trades > 0:
                    print("   ✅ TRADES DETECTED!")
                    break
                elif api_calls > 0:
                    print("   🔄 API CALLS DETECTED!")
        else:
            print(f"   ❌ Start failed: {r.text[:100]}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 40)
    print("TEST COMPLETED")

if __name__ == "__main__":
    test_system() 
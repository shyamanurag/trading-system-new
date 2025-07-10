#!/usr/bin/env python3
"""
Test deployed orchestrator initialization in detail
"""
import requests
import json
import time

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_deployed_system():
    """Test deployed system components systematically"""
    print("🎯 COMPREHENSIVE DEPLOYED SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Basic health
    print("\n1️⃣ Testing basic health...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/health", timeout=10)
        print(f"Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: Market data pipeline
    print("\n2️⃣ Testing market data pipeline...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/market/indices", timeout=10)
        print(f"Market data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                indices = data.get('data', {}).get('indices', [])
                print(f"  ✅ Market data working: {len(indices)} indices")
                for idx in indices[:2]:  # Show first 2
                    print(f"    {idx.get('symbol')}: {idx.get('last_price')}")
            else:
                print(f"  ❌ Market data not working: {data}")
        else:
            print(f"  ❌ Market data failed: {response.text}")
    except Exception as e:
        print(f"  ❌ Market data error: {e}")
    
    # Test 3: Broker connectivity
    print("\n3️⃣ Testing broker connectivity...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/control/users/broker", timeout=10)
        print(f"Broker: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                broker_data = data.get('data', {})
                print(f"  ✅ Broker connected: {broker_data.get('broker')}")
                print(f"    Status: {broker_data.get('kite_status')}")
                print(f"    Trading: {broker_data.get('trading_enabled')}")
            else:
                print(f"  ❌ Broker not connected: {data}")
    except Exception as e:
        print(f"  ❌ Broker error: {e}")
    
    # Test 4: Redis/TrueData connectivity
    print("\n4️⃣ Testing Redis/TrueData...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/market-data", timeout=10)
        print(f"Redis/TrueData: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                market_data = data.get('data', {})
                print(f"  ✅ TrueData flowing: {len(market_data)} symbols")
            else:
                print(f"  ❌ TrueData not flowing: {data}")
    except Exception as e:
        print(f"  ❌ TrueData error: {e}")
    
    # Test 5: Autonomous system attempt
    print("\n5️⃣ Testing autonomous system...")
    try:
        # First check status
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        print(f"Autonomous status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            is_fallback = "fallback mode" in data.get('message', '')
            print(f"  {'❌' if is_fallback else '✅'} Status: {data.get('message', 'unknown')}")
            
            if data.get('success') and data.get('data'):
                status_data = data['data']
                print(f"    Active: {status_data.get('is_active', False)}")
                print(f"    Strategies: {status_data.get('active_strategies_count', 0)}")
                print(f"    Trades: {status_data.get('total_trades', 0)}")
                print(f"    Ready: {status_data.get('system_ready', False)}")
        
        # Try to start
        print("\n  🚀 Attempting to start autonomous trading...")
        response = requests.post(f"{DEPLOYED_URL}/api/v1/autonomous/start", timeout=15)
        print(f"  Start result: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"    ✅ Started successfully!")
                print(f"    Message: {data.get('message', 'No message')}")
            else:
                print(f"    ❌ Start failed: {data.get('message', 'No message')}")
        else:
            print(f"    ❌ HTTP error: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Autonomous system error: {e}")
    
    # Test 6: Check what's actually running
    print("\n6️⃣ Testing what's actually working...")
    
    # Check signals
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/signals/recent", timeout=10)
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', [])
            print(f"  📊 Signals: {len(signals)} available")
            for signal in signals[:2]:  # Show first 2
                sig_data = signal.get('signal', {})
                print(f"    {sig_data.get('symbol', 'unknown')}: {sig_data.get('action', 'unknown')} @ {sig_data.get('price', 'unknown')}")
        else:
            print(f"  ❌ Signals failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Signals error: {e}")
    
    # Check orders
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/orders", timeout=10)
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            print(f"  📋 Orders: {len(orders)} found")
        else:
            print(f"  ❌ Orders failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Orders error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DEPLOYMENT TEST COMPLETE")

if __name__ == "__main__":
    test_deployed_system() 
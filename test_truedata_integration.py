#!/usr/bin/env python3
"""
Test script for TrueData integration
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_truedata_endpoints():
    """Test TrueData API endpoints"""
    print("🔍 Testing TrueData Integration")
    print("=" * 50)
    
    # Test data
    credentials = {
        "username": "your_truedata_username",
        "password": "your_truedata_password"
    }
    
    symbols = ['CRUDEOIL2506165300CE', 'CRUDEOIL2506165300PE', 'NIFTY', 'BANKNIFTY']
    
    try:
        # Test 1: Connect to TrueData
        print("\n1️⃣ Testing TrueData Connection")
        response = requests.post(f"{BASE_URL}/api/v1/truedata/connect", json=credentials)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Connection successful")
        else:
            print(f"   ❌ Connection failed: {response.text}")
        
        # Test 2: Get status
        print("\n2️⃣ Testing Status Check")
        response = requests.get(f"{BASE_URL}/api/v1/truedata/status")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('connected', False)}")
            print(f"   📊 Subscribed symbols: {data.get('total_symbols', 0)}")
        else:
            print(f"   ❌ Status check failed: {response.text}")
        
        # Test 3: Subscribe to symbols
        print("\n3️⃣ Testing Symbol Subscription")
        response = requests.post(f"{BASE_URL}/api/v1/truedata/subscribe", json=symbols)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Subscribed to {len(symbols)} symbols")
        else:
            print(f"   ❌ Subscription failed: {response.text}")
        
        # Test 4: Get market data
        print("\n4️⃣ Testing Market Data Retrieval")
        for symbol in symbols[:2]:  # Test first 2 symbols
            response = requests.get(f"{BASE_URL}/api/v1/truedata/data/{symbol}")
            print(f"   {symbol}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Data available for {symbol}")
                else:
                    print(f"   ⚠️  No data yet for {symbol}")
            else:
                print(f"   ❌ Failed to get data for {symbol}")
        
        # Test 5: Get all market data
        print("\n5️⃣ Testing All Market Data")
        response = requests.get(f"{BASE_URL}/api/v1/truedata/data")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved data for {data.get('total_symbols', 0)} symbols")
        else:
            print(f"   ❌ Failed to get all data: {response.text}")
        
        print(f"\n✅ TrueData integration test completed at {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

def test_simple_truedata_script():
    """Test the original TrueData script"""
    print("\n🔍 Testing Original TrueData Script")
    print("=" * 50)
    
    print("""
📋 Original TrueData Script:
```python
from truedata import TD_live
import time
import logging

username = "your_username"
password = "your_password"

port = 8084
url = "push.truedata.in"

td_obj = TD_live(username, password, live_port=port, 
                 log_level=logging.WARNING, url=url, compression=False)

symbols = ['CRUDEOIL2506165300CE', 'CRUDEOIL2506165300PE']
req_ids = td_obj.start_live_data(symbols)
time.sleep(1)

@td_obj.trade_callback
def my_tick_data(tick_data):
    print("tick data", tick_data)

@td_obj.greek_callback
def mygreek_bidask(greek_data):
    print("greek >", greek_data)

# Keep your thread alive
while True:
    time.sleep(120)
```
""")
    
    print("💡 To use this script:")
    print("   1. Install TrueData: pip install truedata")
    print("   2. Replace username/password with your credentials")
    print("   3. Run the script: python truedata_script.py")
    print("   4. The script will continuously receive market data")

if __name__ == "__main__":
    print("🚀 TrueData Integration Test Suite")
    print("=" * 60)
    
    # Test API endpoints (if routing is fixed)
    test_truedata_endpoints()
    
    # Show original script
    test_simple_truedata_script()
    
    print(f"\n📋 Next Steps:")
    print("   1. Fix the routing issue in DigitalOcean")
    print("   2. Install TrueData library: pip install truedata")
    print("   3. Add TrueData credentials to environment variables")
    print("   4. Test the integration endpoints")
    print("   5. Integrate with your trading strategies") 
#!/usr/bin/env python3
"""
Complete System Test - Automatically connects TrueData and tests everything
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"
TRUEDATA_CREDENTIALS = {
    "username": "tdwsp697",
    "password": "shyam@697"
}
SYMBOLS_TO_SUBSCRIBE = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']

def test_api(endpoint, method="GET", data=None, description=""):
    """Test an API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔍 Testing: {description or endpoint}")
        
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                print(f"   Response: {response.text[:200]}")
                return None
        else:
            print(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   Exception: {str(e)}")
        return None

def connect_truedata():
    """Automatically connect to TrueData"""
    print("\n🔌 CONNECTING TO TRUEDATA...")
    
    result = test_api(
        "/api/v1/truedata/truedata/connect",
        method="POST",
        data=TRUEDATA_CREDENTIALS,
        description="TrueData Connection"
    )
    
    if result and result.get('success'):
        print("   ✅ TrueData connected successfully!")
        return True
    else:
        print("   ❌ TrueData connection failed!")
        return False

def subscribe_symbols():
    """Subscribe to market symbols"""
    print("\n📊 SUBSCRIBING TO SYMBOLS...")
    
    result = test_api(
        "/api/v1/truedata/truedata/subscribe",
        method="POST",
        data=SYMBOLS_TO_SUBSCRIBE,
        description="Symbol Subscription"
    )
    
    if result and result.get('success'):
        symbols = result.get('symbols', [])
        print(f"   ✅ Subscribed to {len(symbols)} symbols: {symbols}")
        return True
    else:
        print("   ❌ Symbol subscription failed!")
        return False

def wait_for_data(max_wait=30):
    """Wait for live data to start flowing"""
    print(f"\n⏳ WAITING FOR LIVE DATA (max {max_wait}s)...")
    
    for i in range(max_wait):
        status = test_api("/api/v1/truedata/truedata/status", description="Data Check")
        
        if status and status.get('data', {}).get('connected'):
            symbols_available = status.get('data', {}).get('total_symbols', 0)
            if symbols_available > 0:
                print(f"   ✅ Live data flowing! {symbols_available} symbols available")
                return True
        
        if i < max_wait - 1:  # Don't sleep on last iteration
            print(f"   ⏳ Waiting... ({i+1}/{max_wait})")
            time.sleep(1)
    
    print("   ⚠️ Timeout waiting for live data")
    return False

def test_market_data():
    """Test market data endpoints with live data"""
    print("\n📈 TESTING MARKET DATA...")
    
    # Test market indices
    indices_data = test_api("/api/market/indices", description="Market Indices")
    
    if indices_data and indices_data.get('success'):
        indices = indices_data.get('data', {}).get('indices', [])
        truedata_info = indices_data.get('data', {}).get('truedata_connection', {})
        
        print(f"   📊 Found {len(indices)} indices")
        print(f"   🔌 TrueData symbols: {truedata_info.get('symbols_available', 0)}")
        
        for idx in indices:
            symbol = idx.get('symbol', 'Unknown')
            price = idx.get('last_price', 0)
            status = idx.get('status', 'Unknown')
            
            if price > 0 and status == "LIVE":
                print(f"   ✅ {symbol}: ₹{price} (LIVE DATA)")
            elif price == 0 and status == "NO_DATA":
                print(f"   ⚠️ {symbol}: ₹{price} (NO DATA - Expected when TrueData disconnected)")
            else:
                print(f"   ❓ {symbol}: ₹{price} (Status: {status})")
        
        return len([idx for idx in indices if idx.get('last_price', 0) > 0]) > 0
    
    return False

def test_system_health():
    """Test overall system health"""
    print("\n🏥 TESTING SYSTEM HEALTH...")
    
    # Test market status
    market_status = test_api("/api/market/market-status", description="Market Status")
    if market_status and market_status.get('success'):
        status = market_status.get('data', {}).get('market_status', 'Unknown')
        phase = market_status.get('data', {}).get('market_phase', 'Unknown')
        print(f"   📅 Market: {status} ({phase})")
    
    # Test API root
    api_info = test_api("/api", description="API Info")
    if api_info:
        version = api_info.get('version', 'Unknown')
        print(f"   🔧 API Version: {version}")
    
    return True

def main():
    """Run complete system test"""
    print("🚀 COMPLETE SYSTEM TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    total_tests = 5
    
    # Step 1: Connect TrueData
    if connect_truedata():
        success_count += 1
        
        # Step 2: Subscribe to symbols
        if subscribe_symbols():
            success_count += 1
            
            # Step 3: Wait for data
            if wait_for_data():
                success_count += 1
                
                # Step 4: Test market data
                if test_market_data():
                    success_count += 1
    
    # Step 5: Test system health (always run)
    if test_system_health():
        success_count += 1
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"✅ Tests Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED - System is fully operational!")
    elif success_count >= 3:
        print("⚠️ PARTIAL SUCCESS - Core functionality working")
    else:
        print("❌ SYSTEM ISSUES - Multiple failures detected")
    
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test Simplified Deployment - Version 4.2.0
Tests that our simplified TrueData system is working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_health_endpoints():
    """Test that health endpoints return JSON (not HTML)"""
    print("🏥 Testing Health Endpoints...")
    
    try:
        # Test /health/ready/json - this was returning HTML before
        response = requests.get(f"{BASE_URL}/health/ready/json")
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print("✅ /health/ready/json returns JSON (FIXED!)")
            print(f"   Status: {data.get('status')}")
            print(f"   Ready: {data.get('ready')}")
            print(f"   TrueData Connected: {data.get('truedata_connected')}")
            return True
        else:
            print("❌ Still returning HTML instead of JSON")
            print(f"Content-Type: {response.headers.get('content-type')}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_api_version():
    """Test that API shows our new version"""
    print("\n📊 Testing API Version...")
    
    try:
        response = requests.get(f"{BASE_URL}/api")
        if response.status_code == 200:
            data = response.json()
            version = data.get('version')
            print(f"✅ API Version: {version}")
            
            if version == "4.2.0":
                print("✅ Correct version deployed (simplified system)")
                return True
            else:
                print(f"⚠️ Expected 4.2.0, got {version}")
                return False
        else:
            print(f"❌ API endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API version test failed: {e}")
        return False

def test_truedata_simplified():
    """Test that TrueData shows simplified status"""
    print("\n📡 Testing Simplified TrueData...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/truedata/truedata/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ TrueData status endpoint working")
            
            td_data = data.get('data', {})
            print(f"   Connected: {td_data.get('connected')}")
            print(f"   Username: {td_data.get('username')}")
            print(f"   Symbols Active: {td_data.get('symbols_active')}")
            print(f"   Autonomous Mode: {td_data.get('autonomous_mode')}")
            
            # Check for simplified attributes (no complex circuit breaker stuff)
            if 'autonomous_mode' in td_data and 'can_retry' in td_data:
                print("✅ Simplified TrueData client detected")
                return True
            else:
                print("⚠️ May still be old complex version")
                return False
                
        else:
            print(f"❌ TrueData endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ TrueData test failed: {e}")
        return False

def test_market_data():
    """Test market data with simplified TrueData"""
    print("\n📈 Testing Market Data...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/market/indices")
        if response.status_code == 200:
            data = response.json()
            print("✅ Market indices endpoint working")
            
            indices = data.get('data', {}).get('indices', [])
            if indices:
                for idx in indices[:2]:  # Show first 2
                    print(f"   {idx.get('symbol')}: ₹{idx.get('last_price')} ({idx.get('status')})")
                print("✅ Market data flowing")
                return True
            else:
                print("⚠️ No market data available")
                return False
                
        else:
            print(f"❌ Market data endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_startup_speed():
    """Test that there are no long startup delays"""
    print("\n⚡ Testing Startup Speed...")
    
    try:
        start_time = datetime.now()
        response = requests.get(f"{BASE_URL}/ready")
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        print(f"✅ Ready endpoint response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ready') and response_time < 5.0:
                print("✅ Fast startup confirmed (no 120s delays)")
                return True
            else:
                print(f"⚠️ Slow response or not ready: {response_time}s")
                return False
        else:
            print(f"❌ Ready endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Startup speed test failed: {e}")
        return False

def main():
    """Run all simplified deployment tests"""
    print("🚀 Testing Simplified Deployment (v4.2.0)")
    print("=" * 50)
    print(f"Target: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Health Endpoints (JSON Fix)", test_health_endpoints),
        ("API Version (4.2.0)", test_api_version),
        ("TrueData Simplified", test_truedata_simplified),
        ("Market Data", test_market_data),
        ("Startup Speed", test_startup_speed),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print()
    
    print("📊 SIMPLIFIED DEPLOYMENT TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 SIMPLIFIED DEPLOYMENT SUCCESS!")
        print("🧠 Intelligence over complexity achieved!")
        print("⚡ Fast startup, simple code, working system!")
    else:
        print("⚠️ Some issues detected - may need investigation")
    
    return passed == total

if __name__ == "__main__":
    main() 
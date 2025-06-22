#!/usr/bin/env python3
"""
Simple API Routing Fix Test
Tests if the routing fix worked by checking critical endpoints.
"""

import requests
import time

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_api_fix():
    """Test if API routing fix worked"""
    print("🔧 Testing API Routing Fix")
    print(f"📍 URL: {BASE_URL}")
    print("=" * 50)
    
    # Test critical endpoints that were failing
    test_endpoints = [
        "/api/v1/market/indices",
        "/api/v1/market/market-status",
        "/api/market/indices", 
        "/api/market/market-status",
        "/api/v1/dashboard/data",
        "/api/v1/users",
        "/api/v1/auth/test"
    ]
    
    success_count = 0
    total_count = len(test_endpoints)
    
    for endpoint in test_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"\n🔍 Testing: {endpoint}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - {response.status_code}")
                try:
                    data = response.json()
                    if "status" in data:
                        print(f"   📄 Status: {data['status']}")
                    elif "message" in data:
                        print(f"   📄 Message: {data['message']}")
                except:
                    print(f"   📄 Response: {response.text[:50]}...")
                success_count += 1
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                print(f"   📄 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 ERROR - {str(e)}")
        
        time.sleep(1)  # Rate limiting
    
    print(f"\n" + "=" * 50)
    print(f"📊 RESULTS: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("🎉 ALL ENDPOINTS WORKING! Routing fix successful!")
    elif success_count > total_count // 2:
        print("⚠️  MOST ENDPOINTS WORKING! Partial fix.")
    else:
        print("🚨 MOST ENDPOINTS FAILING! Routing issue persists.")
    
    print(f"\n⏰ Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_api_fix() 
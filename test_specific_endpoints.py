#!/usr/bin/env python3
"""
Test specific endpoints to check if ROOT_PATH removal worked
"""

import requests

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_endpoint(path, expected_response_type):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        print(f"\n🔍 Testing: {path}")
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text[:200]
            if "Frontend not found" in content:
                print(f"   ❌ Served by Frontend")
                return False
            elif "error" in content.lower() or "not found" in content.lower():
                print(f"   ✅ Reached API (404 - endpoint not found)")
                return True
            else:
                print(f"   ✅ API Response: {content}")
                return True
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def main():
    print("🔍 Testing Specific Endpoints After ROOT_PATH Removal")
    print("=" * 60)
    
    # Test endpoints that should work if ROOT_PATH is removed
    endpoints = [
        ("/api/market/indices", "Should return market data JSON"),
        ("/api/market/market-status", "Should return market status JSON"),
        ("/api/v1/market/data", "Should return market data JSON"),
        ("/api/v1/dashboard/data", "Should return dashboard data JSON"),
        ("/api/v1/users", "Should return users list JSON"),
    ]
    
    api_reached = 0
    frontend_served = 0
    
    for path, description in endpoints:
        print(f"\n📋 {description}")
        if test_endpoint(path, "api"):
            api_reached += 1
        else:
            frontend_served += 1
    
    print(f"\n📊 Results:")
    print(f"   ✅ Reached API: {api_reached}")
    print(f"   ❌ Served by Frontend: {frontend_served}")
    
    if api_reached > 0 and frontend_served > 0:
        print(f"\n🚨 ISSUE: Inconsistent routing - some endpoints reach API, others don't")
        print(f"   → This suggests ROOT_PATH removal is partially applied")
        print(f"   → Wait for deployment to complete fully")
    elif api_reached == 0:
        print(f"\n❌ ISSUE: No endpoints reaching API")
        print(f"   → ROOT_PATH removal didn't work or routing is broken")
    elif frontend_served == 0:
        print(f"\n✅ SUCCESS: All endpoints reaching API!")
        print(f"   → ROOT_PATH removal worked correctly")

if __name__ == "__main__":
    main() 
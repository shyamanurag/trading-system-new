#!/usr/bin/env python3
"""
Debug script to understand DigitalOcean routing behavior
"""

import requests
import time

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_endpoint_pattern(pattern, description):
    """Test a specific endpoint pattern"""
    url = f"{BASE_URL}{pattern}"
    try:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text[:200]
            if "Frontend not found" in content:
                print(f"   ❌ Served by Frontend: {content}")
                return "frontend"
            elif "error" in content.lower() or "not found" in content.lower():
                print(f"   ✅ Reached API: {content}")
                return "api"
            else:
                print(f"   ✅ API Response: {content}")
                return "api"
        else:
            print(f"   ❌ Error: {response.text[:200]}")
            return "error"
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return "error"

def main():
    print("🔍 Debugging DigitalOcean Routing Behavior")
    print("=" * 60)
    
    # Test different endpoint patterns
    patterns = [
        ("/api/market/indices", "API Market Indices"),
        ("/api/v1/market/data", "API V1 Market Data"),
        ("/api/v1/dashboard/data", "API V1 Dashboard"),
        ("/api/v1/users", "API V1 Users"),
        ("/api/v1/auth/test", "API V1 Auth Test"),
        ("/v1/auth/test", "V1 Auth Test"),
        ("/health", "Health Check"),
        ("/docs", "API Docs"),
        ("/api/test", "API Test"),
        ("/api/v1/test", "API V1 Test"),
    ]
    
    results = {"api": 0, "frontend": 0, "error": 0}
    
    for pattern, description in patterns:
        result = test_endpoint_pattern(pattern, description)
        results[result] += 1
        time.sleep(0.5)
    
    print(f"\n📊 Routing Analysis:")
    print(f"   ✅ Reached API: {results['api']}")
    print(f"   ❌ Served by Frontend: {results['frontend']}")
    print(f"   ⚠️  Errors: {results['error']}")
    
    if results['frontend'] > 0:
        print(f"\n🚨 ISSUE: DigitalOcean is inconsistently routing /api/* paths")
        print(f"   → Some reach the API, others are served by frontend")
        print(f"   → This indicates the app spec update wasn't applied correctly")
        print(f"   → Solution: Force redeploy in DigitalOcean dashboard")
    else:
        print(f"\n✅ All /api/* paths are reaching the API correctly!")

if __name__ == "__main__":
    main() 
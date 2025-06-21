#!/usr/bin/env python3
"""
Comprehensive test script for deployed trading system app
Tests all major endpoints to verify routing and functionality
"""

import requests
import json
import time
from datetime import datetime

# Base URL
BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_endpoint(url, method="GET", expected_status=200, description=""):
    """Test a single endpoint"""
    try:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        response = requests.request(method, url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ PASS - Expected {expected_status}, got {response.status_code}")
            
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
        return response.status_code == expected_status
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    """Run comprehensive tests"""
    print("🚀 Starting comprehensive tests for deployed trading system app")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"⏰ Test time: {datetime.now().isoformat()}")
    
    tests = [
        # Basic health checks
        (f"{BASE_URL}/health", "GET", 200, "Basic health check"),
        (f"{BASE_URL}/health/ready", "GET", 200, "Readiness check"),
        (f"{BASE_URL}/health/alive", "GET", 200, "Liveness check"),
        
        # Root endpoint
        (f"{BASE_URL}/", "GET", 200, "Root endpoint (should serve frontend)"),
        
        # API v1 endpoints (should work)
        (f"{BASE_URL}/v1/auth/test", "GET", 200, "Auth test endpoint"),
        (f"{BASE_URL}/api/v1/auth/test", "GET", 200, "API v1 auth test endpoint"),
        (f"{BASE_URL}/api/v1/dashboard/data", "GET", 200, "Dashboard data endpoint"),
        (f"{BASE_URL}/api/v1/health/data", "GET", 200, "Health data endpoint"),
        (f"{BASE_URL}/api/v1/users/current", "GET", 200, "Current user endpoint"),
        
        # Market endpoints (these were failing)
        (f"{BASE_URL}/api/market/indices", "GET", 200, "Market indices endpoint"),
        (f"{BASE_URL}/api/market/market-status", "GET", 200, "Market status endpoint"),
        (f"{BASE_URL}/api/v1/market/data", "GET", 200, "Market data endpoint"),
        
        # Other API endpoints
        (f"{BASE_URL}/api/v1/users", "GET", 200, "Users list endpoint"),
        (f"{BASE_URL}/api/v1/recommendations/elite", "GET", 200, "Elite recommendations endpoint"),
        (f"{BASE_URL}/api/v1/performance/elite-trades", "GET", 200, "Elite performance endpoint"),
        
        # WebSocket endpoint (should return upgrade required)
        (f"{BASE_URL}/ws/test", "GET", 426, "WebSocket endpoint"),
        
        # Admin endpoints
        (f"{BASE_URL}/docs", "GET", 200, "API documentation"),
        (f"{BASE_URL}/openapi.json", "GET", 200, "OpenAPI schema"),
    ]
    
    passed = 0
    failed = 0
    
    for url, method, expected_status, description in tests:
        if test_endpoint(url, method, expected_status, description):
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print(f"\n🎉 All tests passed! Your app is working perfectly!")
    else:
        print(f"\n⚠️  Some tests failed. Check the deployment status.")
    
    print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main() 
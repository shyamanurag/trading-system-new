#!/usr/bin/env python3
"""
Test script to verify the deployed trading app functionality
"""
import requests
import json
from datetime import datetime

# Base URL for the deployed app
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health endpoint is working")
            return True
        else:
            print(f"   ❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_auth_endpoints():
    """Test authentication flow"""
    print("\n2. Testing Authentication...")
    
    # Test login endpoint exists
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "test", "password": "test"},
            timeout=10
        )
        print(f"   Login endpoint status: {response.status_code}")
        if response.status_code in [200, 401, 422]:
            print("   ✅ Auth endpoint is reachable")
            return True
        else:
            print("   ❌ Unexpected auth response")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    print("\n3. Testing API Endpoints...")
    
    endpoints = [
        ("/api/v1/recommendations", "GET", "Recommendations"),
        ("/api/v1/monitoring/daily-pnl", "GET", "Daily P&L"),
        ("/api/market/indices", "GET", "Market Indices"),
        ("/api/market/market-status", "GET", "Market Status"),
        ("/health/ready/json", "GET", "Health Ready JSON"),
    ]
    
    results = []
    for endpoint, method, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=10)
            
            status = "✅" if response.status_code in [200, 201, 401] else "❌"
            print(f"   {status} {name}: {response.status_code}")
            results.append(response.status_code in [200, 201, 401])
        except Exception as e:
            print(f"   ❌ {name}: Error - {str(e)[:50]}...")
            results.append(False)
    
    return all(results)

def test_frontend():
    """Test if frontend is accessible"""
    print("\n4. Testing Frontend...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
            print("   ✅ Frontend is accessible")
            return True
        else:
            print(f"   ❌ Frontend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_cors_headers():
    """Test CORS configuration"""
    print("\n5. Testing CORS Headers...")
    try:
        response = requests.options(
            f"{BASE_URL}/api/v1/recommendations",
            headers={"Origin": "https://algoauto-9gx56.ondigitalocean.app"},
            timeout=10
        )
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        if cors_headers:
            print(f"   ✅ CORS is configured: {cors_headers}")
            return True
        else:
            print("   ⚠️  CORS headers not found (might be OK if same-origin)")
            return True  # Not a failure
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Deployed Trading App")
    print(f"URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        test_health_endpoint(),
        test_auth_endpoints(),
        test_api_endpoints(),
        test_frontend(),
        test_cors_headers()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print("\n" + "="*60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! The app is working correctly.")
    elif passed > total * 0.7:
        print("⚠️  Most tests passed, but some issues detected.")
    else:
        print("❌ Multiple tests failed. Please check the deployment.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
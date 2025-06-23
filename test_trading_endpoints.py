#!/usr/bin/env python3
"""Test specific trading endpoints that were previously failing."""

import requests
import json
import sys
from datetime import datetime

# DigitalOcean deployment URL
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_endpoint(endpoint, expected_status=200, method="GET", data=None):
    """Test a single endpoint and return results."""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        status_code = response.status_code
        success = status_code == expected_status
        
        if success:
            print(f"✅ {endpoint} - Status: {status_code}")
        else:
            print(f"❌ {endpoint} - Status: {status_code} (Expected: {expected_status})")
            if status_code == 404:
                print(f"   → Endpoint not found")
            elif status_code == 500:
                print(f"   → Internal server error")
                try:
                    error_detail = response.json()
                    print(f"   → Error: {error_detail}")
                except:
                    print(f"   → Error: {response.text[:200]}")
        
        return success, status_code
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - Connection Error: {e}")
        return False, 0

def main():
    print(f"☁️  Testing trading endpoints at {BASE_URL}")
    print(f"\n🚀 Trading Endpoints Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test trading endpoints with correct paths from route list
    trading_endpoints = [
        "/api/v1/positions/",            # Trailing slash required
        "/api/v1/orders/",               # Trailing slash required
        "/api/v1/trades/",               # Trailing slash required
        "/api/v1/monitoring/daily-pnl",
        "/api/v1/recommendations/",      # Trailing slash required
        "/api/v1/monitoring/components",
        "/api/v1/monitoring/metrics"
        # Note: autonomous endpoints not found in deployed routes - router mounting issue
    ]
    
    print("\n📊 Trading Endpoints")
    print("-" * 30)
    
    passed = 0
    total = len(trading_endpoints)
    
    for endpoint in trading_endpoints:
        success, status_code = test_endpoint(endpoint)
        if success:
            passed += 1
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All trading endpoints are working!")
    else:
        print(f"\n⚠️  {total - passed} endpoints still need attention")

if __name__ == "__main__":
    main() 
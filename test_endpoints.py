#!/usr/bin/env python3
"""Test script to check API endpoints"""

import requests

def test_endpoint(url, name):
    try:
        response = requests.get(url, timeout=10)
        print(f"{name}: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.text[:100]}...")
        else:
            print(f"  Response: {response.text[:100]}...")
    except Exception as e:
        print(f"{name}: Error - {e}")
    print()

# Test endpoints
base_url = "https://algoauto-jd32t.ondigitalocean.app"

print("Testing API endpoints...")
print("=" * 50)

test_endpoint(f"{base_url}/health", "Health endpoint")
test_endpoint(f"{base_url}/market/indices", "Market indices (no /api)")
test_endpoint(f"{base_url}/api/market/indices", "Market indices (with /api)")
test_endpoint(f"{base_url}/market/market-status", "Market status (no /api)")
test_endpoint(f"{base_url}/api/market/market-status", "Market status (with /api)")
test_endpoint(f"{base_url}/api/v1/auth/test", "Auth test")
test_endpoint(f"{base_url}/api/v1/market/data", "Market data v1")
test_endpoint(f"{base_url}/api/v1/dashboard/data", "Dashboard data")
test_endpoint(f"{base_url}/api/test/routes", "Test routes") 
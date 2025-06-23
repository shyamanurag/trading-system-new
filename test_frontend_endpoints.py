#!/usr/bin/env python3
"""Test specific frontend endpoints that are failing."""

import requests
import json
from datetime import datetime

# DigitalOcean deployment URL
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_endpoint(endpoint, expected_status=200):
    """Test a single endpoint and return results."""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        print(f"📍 {endpoint}")
        print(f"   Status: {status_code}")
        
        if status_code == 200:
            print(f"   ✅ Working")
        elif status_code == 404:
            print(f"   ❌ Not Found")
        elif status_code == 500:
            print(f"   ⚠️  Server Error")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                error_text = response.text[:300]
                print(f"   Error: {error_text}")
        else:
            print(f"   ⚠️  Unexpected status: {status_code}")
        
        print()
        return status_code == expected_status
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - Connection Error: {e}")
        return False

def main():
    print(f"☁️  Testing frontend endpoints at {BASE_URL}")
    print(f"\n🚀 Frontend Endpoints Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Frontend endpoints that are failing
    frontend_endpoints = [
        "/api/v1/strategies/performance",
        "/api/v1/autonomous/status", 
        "/api/v1/broker/status",
        "/api/v1/system/status"
    ]
    
    print("\n📊 Frontend Endpoints")
    print("-" * 30)
    
    for endpoint in frontend_endpoints:
        test_endpoint(endpoint)
    
    print("=" * 60)
    print("🔍 Checking alternative endpoints...")
    print("-" * 30)
    
    # Check if alternative endpoints exist
    alternative_endpoints = [
        "/api/v1/performance/performance/metrics",  # Alternative for strategies/performance
        "/api/v1/monitoring/trading-status",        # Alternative for system/status
        "/api/v1/monitoring/connections"            # Alternative for broker/status
    ]
    
    for endpoint in alternative_endpoints:
        test_endpoint(endpoint)

if __name__ == "__main__":
    main() 
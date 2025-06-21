#!/usr/bin/env python3
"""
Test script to check endpoint availability on deployed backend
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_endpoint(path, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ {path} - Status: {response.status_code}")
        if response.status_code == expected_status:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ {path} - Error: {e}")
    print()

def main():
    print(f"🔍 Testing endpoints on {BASE_URL}")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test basic endpoints
    test_endpoint("/")
    test_endpoint("/health")
    test_endpoint("/health/ready")
    
    # Test API endpoints
    test_endpoint("/api/v1/auth/test")
    test_endpoint("/api/v1/market/indices")
    test_endpoint("/api/v1/market/market-status")
    test_endpoint("/api/market/indices")
    test_endpoint("/api/market/market-status")
    
    # Test debug endpoint
    test_endpoint("/api/debug/routes")
    
    # Test v1 endpoints
    test_endpoint("/v1/market/indices")
    test_endpoint("/v1/market/market-status")
    
    # Test dashboard endpoints
    test_endpoint("/api/v1/dashboard/data")
    test_endpoint("/api/v1/health/data")
    
    print("=" * 60)
    print("🏁 Testing complete!")

if __name__ == "__main__":
    main() 
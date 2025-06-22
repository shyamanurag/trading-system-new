#!/usr/bin/env python3
"""
Test the deployed API to verify endpoints are working correctly
"""

import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_endpoint(method, path, data=None):
    """Test an endpoint and print results"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"Unsupported method: {method}")
            return
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"Response: {response.text[:200]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Testing AlgoAuto Deployed API")
    print("="*60)
    
    # Test health endpoints
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/ready")
    test_endpoint("GET", "/api/routes")
    
    # Test the correct login endpoint
    print("\n\nTesting CORRECT login endpoint:")
    test_endpoint("POST", "/auth/login", {
        "username": "admin",
        "password": "admin123"
    })
    
    # Test the incorrect login endpoint (what browser is trying)
    print("\n\nTesting INCORRECT login endpoint (what browser is using):")
    test_endpoint("POST", "/api/auth/login", {
        "username": "admin",
        "password": "admin123"
    })
    
    # Test market endpoints
    test_endpoint("GET", "/api/market/indices")
    test_endpoint("GET", "/api/market/market-status")

if __name__ == "__main__":
    main() 
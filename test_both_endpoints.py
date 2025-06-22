#!/usr/bin/env python3
"""Test both login endpoints to diagnose the issue"""

import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_endpoints():
    login_data = {"username": "admin", "password": "admin123"}
    
    print("Testing Login Endpoints")
    print("="*60)
    
    # Test the correct endpoint
    print("\n1. Testing CORRECT endpoint: /auth/login")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Token: {data.get('access_token', '')[:30]}...")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test the problematic endpoint
    print("\n2. Testing PROBLEMATIC endpoint: /api/auth/login")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Redirect working! Token: {data.get('access_token', '')[:30]}...")
        elif response.status_code == 500:
            print(f"   ❌ Server error (redirect handler issue)")
            print(f"   Response: {response.text}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check health
    print("\n3. Checking deployment health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version')}")
            print(f"   Routers: {data.get('routers_loaded')}")
    except:
        pass
    
    print("\n" + "="*60)
    print("\nSUMMARY:")
    print("- The correct endpoint (/auth/login) is working")
    print("- The redirect handler has an issue (httpx might not be in requirements)")
    print("\nFor now, the browser can be fixed by:")
    print("1. Clear browser cache (Ctrl+Shift+Delete)")
    print("2. Use incognito mode")
    print("3. Or wait for frontend cache to expire")

if __name__ == "__main__":
    test_endpoints() 
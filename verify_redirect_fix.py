#!/usr/bin/env python3
"""Verify the redirect fix is working"""

import requests
import time
import sys

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def wait_for_deployment():
    """Wait for the new deployment to be live"""
    print("Checking deployment status...")
    for i in range(30):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                version = data.get('version', '')
                if '4.0.2' in version or 'redirect' in version:
                    print(f"✅ New deployment is live! Version: {version}")
                    return True
                else:
                    print(f"⏳ Waiting... Current version: {version}")
        except:
            print("⏳ Waiting for deployment...")
        time.sleep(10)
    return False

def test_redirect():
    """Test the redirect functionality"""
    print("\nTesting redirect functionality...")
    print("="*60)
    
    # Test data
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    # Test the old endpoint (should now work via redirect)
    print("\n1. Testing OLD endpoint: /api/auth/login (should redirect)")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ SUCCESS - Redirect is working!")
            data = response.json()
            if "access_token" in data:
                print(f"   ✅ Token received: {data['access_token'][:30]}...")
                return True
        else:
            print(f"   ❌ FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    return False

def main():
    print("AlgoAuto Redirect Fix Verification")
    print("="*60)
    
    # Wait for deployment
    if not wait_for_deployment():
        print("❌ Deployment timeout - please check DigitalOcean dashboard")
        sys.exit(1)
    
    # Test redirect
    if test_redirect():
        print("\n✅ REDIRECT FIX IS WORKING!")
        print("\nThe browser should now be able to login successfully.")
        print("If you still see issues, please clear your browser cache:")
        print("  1. Press Ctrl+Shift+Delete in Chrome")
        print("  2. Select 'Cached images and files'")
        print("  3. Click 'Clear data'")
        print("  4. Refresh the page")
    else:
        print("\n❌ Redirect test failed - checking deployment logs...")

if __name__ == "__main__":
    main() 
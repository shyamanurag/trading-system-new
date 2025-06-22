#!/usr/bin/env python3
"""Monitor deployment and test redirect when ready"""

import requests
import time
import sys
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_deployment():
    """Check current deployment version"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('version', 'unknown'), data
        return 'error', None
    except Exception as e:
        return 'error', str(e)

def test_redirect():
    """Test if redirect is working"""
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        # Test the problematic endpoint
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔍 AlgoAuto Deployment Monitor")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Monitoring: {BASE_URL}")
    print("\nWaiting for deployment with redirect fix (version 4.0.2)...")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_version = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            version, data = check_deployment()
            
            # Print status every 5 checks or when version changes
            if check_count % 5 == 1 or version != last_version:
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if version == 'error':
                    print(f"[{timestamp}] ❌ Error checking deployment: {data}")
                else:
                    print(f"[{timestamp}] 📦 Version: {version}")
                    
                    # Check if new version is deployed
                    if '4.0.2' in version or 'redirect' in version.lower():
                        print(f"\n✅ NEW DEPLOYMENT DETECTED!")
                        print(f"Version: {version}")
                        print(f"Full data: {data}")
                        
                        # Test redirect
                        print("\nTesting redirect functionality...")
                        if test_redirect():
                            print("✅ REDIRECT IS WORKING! Login via /api/auth/login successful!")
                            print("\n🎉 Deployment successful! The browser login should work now.")
                            print("\nIf you still see issues in the browser:")
                            print("1. Clear browser cache (Ctrl+Shift+Delete)")
                            print("2. Hard refresh the page (Ctrl+Shift+R)")
                            return 0
                        else:
                            print("❌ Redirect test failed")
                            return 1
                
                last_version = version
            
            # Wait before next check
            time.sleep(20)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 
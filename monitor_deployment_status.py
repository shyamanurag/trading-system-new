#!/usr/bin/env python3
"""Monitor deployment status and test when ready"""

import requests
import time
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_deployment():
    """Check deployment status"""
    try:
        # Check health endpoint
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            version = data.get('version', 'unknown')
            deployment = data.get('deployment', 'unknown')
            return True, version, deployment
        return False, None, None
    except:
        return False, None, None

def test_endpoints():
    """Test key endpoints"""
    tests = [
        ("POST", "/auth/login", {"username": "admin", "password": "admin123"}),
        ("GET", "/api/market/indices", None),
        ("GET", "/health", None)
    ]
    
    results = []
    for method, path, data in tests:
        try:
            if method == "POST":
                r = requests.post(f"{BASE_URL}{path}", json=data, timeout=5)
            else:
                r = requests.get(f"{BASE_URL}{path}", timeout=5)
            results.append((path, r.status_code))
        except Exception as e:
            results.append((path, f"Error: {str(e)}"))
    
    return results

def main():
    print("🔍 Monitoring AlgoAuto Deployment")
    print("="*60)
    print(f"URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nPress Ctrl+C to stop\n")
    
    last_status = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            is_up, version, deployment = check_deployment()
            
            # Print status every 5 checks or on change
            if check_count % 5 == 1 or is_up != last_status:
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if is_up:
                    print(f"[{timestamp}] ✅ API is UP - Version: {version}")
                    
                    # Run endpoint tests
                    print(f"[{timestamp}] Running endpoint tests...")
                    results = test_endpoints()
                    for endpoint, status in results:
                        status_icon = "✅" if isinstance(status, int) and status < 400 else "❌"
                        print(f"  {status_icon} {endpoint}: {status}")
                    
                    # Check if it's the new deployment
                    if version and ('4.0.2' in version or 'redirect' in version):
                        print(f"\n🎉 New deployment detected!")
                        print(f"Version: {version}")
                        print(f"Deployment: {deployment}")
                else:
                    print(f"[{timestamp}] ❌ API is DOWN or deploying...")
                
                last_status = is_up
            
            time.sleep(20)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Trace Singleton Issue
"""

import requests
import json
import time
import sys

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_singleton():
    print("🔍 TRACING SINGLETON")
    
    # Get status before
    print("1. Status before...")
    status_before = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
    print(f"   Code: {status_before.status_code}")
    if status_before.status_code == 200:
        is_active_before = status_before.json().get('data', {}).get('is_active', False)
        print(f"   is_active: {is_active_before}")
    
    # Enable trading
    print("\n2. Enabling trading...")
    enable_response = requests.post(f"{BASE_URL}/api/v1/autonomous/start", timeout=15)
    print(f"   Code: {enable_response.status_code}")
    if enable_response.status_code == 200:
        enable_data = enable_response.json()
        print(f"   Success: {enable_data.get('success')}")
    
    # Status after
    print("\n3. Status after...")
    status_after = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
    print(f"   Code: {status_after.status_code}")
    if status_after.status_code == 200:
        is_active_after = status_after.json().get('data', {}).get('is_active', False)
        print(f"   is_active: {is_active_after}")
        
        if is_active_after:
            print("\n✅ WORKING!")
            return True
        else:
            print("\n❌ STILL BROKEN")
            return False
    
    return False

if __name__ == "__main__":
    time.sleep(15)  # Wait for deployment
    success = test_singleton()
    sys.exit(0 if success else 1) 
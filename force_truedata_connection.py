#!/usr/bin/env python3
"""
Force TrueData Connection Script
"""

import requests
import time
import json

def force_truedata_connection():
    """Force TrueData to connect"""
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔄 Forcing TrueData connection...")
    
    try:
        # Try to trigger TrueData connection
        response = requests.get(f"{base_url}/api/v1/truedata/force-connect", timeout=30)
        if response.status_code == 200:
            print("✅ TrueData force-connect triggered")
        else:
            print(f"⚠️ Force-connect returned {response.status_code}")
    except Exception as e:
        print(f"❌ Force-connect failed: {e}")
    
    # Wait a bit
    print("⏳ Waiting 10 seconds for connection...")
    time.sleep(10)
    
    # Check status
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', {})) if data.get('data') else 0
            print(f"📊 Market data: {count} symbols")
            
            if count > 0:
                print("✅ TrueData is working!")
                return True
            else:
                print("❌ TrueData still not flowing")
                return False
        else:
            print(f"❌ Market data check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

if __name__ == "__main__":
    force_truedata_connection() 
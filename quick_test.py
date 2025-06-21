#!/usr/bin/env python3
"""
Quick test to check current deployment status
"""

import requests

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def quick_test():
    print("🔍 Quick Status Check")
    print("=" * 50)
    
    # Test key endpoints
    endpoints = [
        ("/health", "Basic Health"),
        ("/v1/auth/test", "V1 Auth Test"),
        ("/api/v1/auth/test", "API V1 Auth Test"),
        ("/api/market/indices", "Market Indices"),
        ("/api/market/market-status", "Market Status"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: WORKING (200)")
            else:
                print(f"❌ {description}: FAILED ({response.status_code})")
                print(f"   Response: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {description}: ERROR - {str(e)}")
    
    print("\n📋 Summary:")
    print("- If /api/v1/auth/test works but /api/market/* doesn't:")
    print("  → ROOT_PATH is still being applied")
    print("  → Deployment with updated config hasn't completed")
    print("- If all /api/* endpoints fail:")
    print("  → DigitalOcean routing issue")
    print("- If all work:")
    print("  → Everything is fixed! 🎉")

if __name__ == "__main__":
    quick_test() 
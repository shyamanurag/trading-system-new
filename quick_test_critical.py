#!/usr/bin/env python3
"""
Quick Test for Critical Endpoints
Tests only the most important endpoints that were failing.
"""

import requests
import time

BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def quick_test():
    """Quick test of critical endpoints"""
    print("🚀 Quick Test of Critical Endpoints")
    print(f"📍 URL: {BASE_URL}")
    print("=" * 50)
    
    # Critical endpoints that were failing
    critical_endpoints = [
        "/api/v1/market/indices",
        "/api/v1/market/market-status", 
        "/api/market/indices",
        "/api/market/market-status",
        "/api/v1/dashboard/data",
        "/api/v1/health/data",
        "/api/v1/users",
        "/api/v1/auth/test"
    ]
    
    for endpoint in critical_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - {response.status_code}")
                try:
                    data = response.json()
                    if "status" in data:
                        print(f"   📄 Status: {data['status']}")
                except:
                    pass
            else:
                print(f"❌ {endpoint} - {response.status_code}")
                print(f"   📄 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"💥 {endpoint} - ERROR: {str(e)}")
        
        time.sleep(1)  # Rate limiting
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    quick_test() 
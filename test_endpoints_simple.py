#!/usr/bin/env python3
"""Test endpoints after revert"""
import requests

def test_endpoints():
    print("🔍 Testing previously working endpoints after revert...")
    
    endpoints = [
        ("GET", "https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status"),
        ("GET", "https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/dashboard/summary"), 
        ("GET", "https://algoauto-9gx56.ondigitalocean.app/api/market/indices"),
        ("GET", "https://algoauto-9gx56.ondigitalocean.app/api/market/market-status")
    ]
    
    for method, url in endpoints:
        try:
            r = requests.get(url, timeout=10)
            status = "✅ RESTORED" if r.status_code == 200 else f"❌ {r.status_code}"
            endpoint_name = url.split("/")[-1]
            print(f"{status} - {endpoint_name}")
        except Exception as e:
            endpoint_name = url.split("/")[-1]
            print(f"❌ ERROR - {endpoint_name}: {str(e)[:50]}")
    
    print("\n🎯 Testing the original problematic endpoint:")
    try:
        r = requests.post("https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start", json={}, timeout=10)
        if r.status_code == 500:
            print("✅ Back to original 500 error (as expected)")
        else:
            print(f"📊 Status: {r.status_code}")
        print(f"Response: {r.text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoints() 
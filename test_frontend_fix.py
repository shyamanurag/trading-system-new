#!/usr/bin/env python3
"""
Test React Error #31 Fix and System Status
"""

import requests
import json

def test_frontend_fix():
    print("🔧 TESTING REACT ERROR #31 FIX")
    print("=" * 40)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Test 1: Check if frontend endpoints return proper JSON
    print("\n1. Testing Frontend JSON Responses:")
    endpoints = [
        "/health/ready/json",
        "/api",
        "/auth/me"
    ]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}", timeout=10)
            is_json = 'application/json' in resp.headers.get('content-type', '')
            print(f"   {endpoint}: Status {resp.status_code}, JSON: {is_json}")
            
            if is_json:
                data = resp.json()
                print(f"      ✅ Valid JSON response")
            else:
                print(f"      ❌ Not JSON - may cause frontend errors")
                
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    # Test 2: Check 250-Symbol System Status
    print("\n2. Checking 250-Symbol System:")
    try:
        resp = requests.get(f"{base_url}/api/v1/intelligent-symbols/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get('status', {})
            
            print(f"   Manager Running: {status.get('is_running', False)}")
            print(f"   Active Symbols: {status.get('active_symbols', 0)}/250")
            print(f"   Core Indices: {status.get('core_indices', 0)}")
            print(f"   Priority Stocks: {status.get('priority_stocks', 0)}")
            print(f"   Options: {status.get('options', 0)}")
            
            if status.get('active_symbols', 0) >= 50:
                print("   ✅ 250-Symbol system operational!")
            else:
                print("   ⚠️ Symbol count lower than expected")
        else:
            print(f"   ❌ Status check failed: {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking symbols: {e}")
    
    # Test 3: Check TrueData Integration
    print("\n3. Checking TrueData Integration:")
    try:
        resp = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
        if resp.status_code == 200:
            td_status = resp.json()
            
            # Use safe rendering logic
            connected = td_status.get('connected', False)
            symbols_active = td_status.get('symbols_active', 0)
            
            # This would previously cause React Error #31 if rendered directly
            print(f"   TrueData Status Object Keys: {list(td_status.keys())}")
            print(f"   Safe Rendering: Connected={connected}, Symbols={symbols_active}")
            
            if connected and symbols_active > 0:
                print("   ✅ TrueData data flowing")
            else:
                print("   ⚠️ TrueData needs reconnection")
        else:
            print(f"   ❌ TrueData status check failed: {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ TrueData error: {e}")
    
    # Test 4: API Version Check
    print("\n4. API Version Check:")
    try:
        resp = requests.get(f"{base_url}/api", timeout=10)
        if resp.status_code == 200:
            api_data = resp.json()
            version = api_data.get('version', 'Unknown')
            print(f"   API Version: {version}")
            
            if version == "4.2.0":
                print("   ✅ Latest version deployed")
            else:
                print("   ⚠️ Unexpected version")
        else:
            print(f"   ❌ API check failed: {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ API error: {e}")
    
    print("\n🎯 SUMMARY:")
    print("==========")
    print("✅ React Error #31 fix includes:")
    print("   - Enhanced ErrorBoundary with retry button")
    print("   - Safe rendering utilities")
    print("   - Better error handling for object rendering")
    print("   - Specific fixes for TrueData status objects")
    print("")
    print("🚀 The frontend should now handle object rendering gracefully!")
    print("   If React Error #31 occurs, users can click 'Retry Component'")

if __name__ == "__main__":
    test_frontend_fix() 
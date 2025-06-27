#!/usr/bin/env python3
"""
Test the 250-Symbol Dynamic Trading System Breakthrough
"""

import requests
import json

def test_breakthrough_deployment():
    print("🎯 TESTING 250-SYMBOL BREAKTHROUGH DEPLOYMENT")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # 1. Check API Version
    print("\n📊 1. Checking API Version:")
    try:
        resp = requests.get(f"{base_url}/api", timeout=10)
        api_info = resp.json()
        version = api_info.get('version', 'unknown')
        print(f"   API Version: {version}")
        
        if version == "4.2.0":
            print("   ✅ Correct version deployed")
        else:
            print("   ⚠️ Unexpected version")
    except Exception as e:
        print(f"   ❌ API Error: {e}")
    
    # 2. Check App Health 
    print("\n🏥 2. Checking App Health:")
    try:
        resp = requests.get(f"{base_url}/health/ready/json", timeout=10)
        health = resp.json()
        status = health.get('status', 'unknown')
        startup_complete = health.get('app_startup_complete', False)
        
        print(f"   Status: {status}")
        print(f"   Startup Complete: {startup_complete}")
        
        if status == "ready" and startup_complete:
            print("   ✅ App fully initialized")
        else:
            print("   ⚠️ App still starting up")
    except Exception as e:
        print(f"   ❌ Health Error: {e}")
    
    # 3. Check Intelligent Symbol Manager
    print("\n🤖 3. Checking Intelligent Symbol Manager:")
    try:
        resp = requests.get(f"{base_url}/api/v1/intelligent-symbols/status", timeout=10)
        result = resp.json()
        
        if result.get('success'):
            status = result['status']
            is_running = status.get('is_running', False)
            active_symbols = status.get('active_symbols', 0)
            max_symbols = status.get('max_symbols', 0)
            utilization = status.get('symbol_utilization', '0/0')
            
            print(f"   Running: {is_running}")
            print(f"   Active Symbols: {active_symbols}")
            print(f"   Max Symbols: {max_symbols}")
            print(f"   Utilization: {utilization}")
            
            if is_running and active_symbols > 50:
                print("   🎉 BREAKTHROUGH SUCCESS: 250-symbol system LIVE!")
                return True
            elif is_running and active_symbols > 0:
                print("   ⚡ Manager running, building symbol list...")
                return "partial"
            elif is_running:
                print("   🔄 Manager running but no symbols yet")
                return "starting"
            else:
                print("   ❌ Manager not running - startup may have failed")
                return False
        else:
            print(f"   ❌ API Error: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Symbol Manager Error: {e}")
        return False
    
    # 4. Try Manual Start if not running
    print("\n🔧 4. Attempting Manual Start:")
    try:
        resp = requests.post(f"{base_url}/api/v1/intelligent-symbols/start", timeout=30)
        result = resp.json()
        
        if result.get('success'):
            print("   ✅ Successfully started manually!")
            
            # Check status again
            resp = requests.get(f"{base_url}/api/v1/intelligent-symbols/status", timeout=10)
            status_result = resp.json()
            if status_result.get('success'):
                status = status_result['status']
                print(f"   🤖 Now Running: {status.get('is_running', False)}")
                print(f"   📊 Active Symbols: {status.get('active_symbols', 0)}")
                
                if status.get('active_symbols', 0) > 0:
                    print("   🎉 BREAKTHROUGH ACHIEVED!")
                    return True
                    
        else:
            print(f"   ❌ Manual start failed: {result.get('message', 'unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Manual start error: {e}")
    
    return False

if __name__ == "__main__":
    test_breakthrough_deployment() 
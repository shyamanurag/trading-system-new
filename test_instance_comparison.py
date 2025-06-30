#!/usr/bin/env python3
"""
Test Instance Comparison - Check if different endpoints use same orchestrator
"""

import requests
import json
import sys

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_instance_consistency():
    """Test if different endpoints are using the same orchestrator instance"""
    print("🔍 TESTING ORCHESTRATOR INSTANCE CONSISTENCY")
    print("=" * 50)
    
    try:
        # Step 1: Get debug info to see instance ID
        print("📊 Step 1: Getting debug info...")
        debug_response = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=10)
        
        if debug_response.status_code != 200:
            print(f"❌ Debug endpoint failed: {debug_response.status_code}")
            return False
        
        debug_data = debug_response.json()
        debug_is_active = debug_data.get('orchestrator_state', {}).get('is_active', 'NOT_SET')
        print(f"   Debug endpoint is_active: {debug_is_active}")
        
        # Step 2: Get status from autonomous endpoint
        print("\n📊 Step 2: Getting autonomous status...")
        status_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        
        if status_response.status_code != 200:
            print(f"❌ Status endpoint failed: {status_response.status_code}")
            return False
        
        status_data = status_response.json()
        autonomous_is_active = status_data.get('data', {}).get('is_active', 'NOT_SET')
        print(f"   Autonomous endpoint is_active: {autonomous_is_active}")
        
        # Step 3: Compare values
        print(f"\n🔍 INSTANCE COMPARISON:")
        print(f"   Debug is_active: {debug_is_active}")
        print(f"   Autonomous is_active: {autonomous_is_active}")
        
        if debug_is_active == autonomous_is_active:
            print("✅ SAME INSTANCE: Both endpoints show same is_active value")
        else:
            print("❌ DIFFERENT INSTANCES: Endpoints show different is_active values!")
            return False
        
        # Step 4: Try to enable trading and check both endpoints
        print(f"\n🚀 Step 3: Enabling trading...")
        enable_response = requests.post(f"{BASE_URL}/api/v1/autonomous/start", timeout=15)
        
        if enable_response.status_code != 200:
            print(f"❌ Enable failed: {enable_response.status_code}")
            print(f"   Response: {enable_response.text}")
            return False
        
        enable_data = enable_response.json()
        enable_success = enable_data.get('success', False)
        print(f"   Enable success: {enable_success}")
        
        # Step 5: Check both endpoints after enable
        print(f"\n📊 Step 4: Checking both endpoints after enable...")
        
        # Check debug endpoint
        debug_after = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=10)
        if debug_after.status_code == 200:
            debug_after_data = debug_after.json()
            debug_after_active = debug_after_data.get('orchestrator_state', {}).get('is_active', 'NOT_SET')
            print(f"   Debug after enable: {debug_after_active}")
        else:
            print(f"   Debug after failed: {debug_after.status_code}")
            return False
        
        # Check autonomous endpoint
        status_after = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        if status_after.status_code == 200:
            status_after_data = status_after.json()
            autonomous_after_active = status_after_data.get('data', {}).get('is_active', 'NOT_SET')
            print(f"   Autonomous after enable: {autonomous_after_active}")
        else:
            print(f"   Autonomous after failed: {status_after.status_code}")
            return False
        
        # Final analysis
        print(f"\n🎯 FINAL ANALYSIS:")
        print(f"   Enable claimed success: {enable_success}")
        print(f"   Debug shows is_active: {debug_after_active}")
        print(f"   Autonomous shows is_active: {autonomous_after_active}")
        
        if enable_success and debug_after_active and autonomous_after_active:
            print("\n🎉 SUCCESS: Everything working correctly!")
            return True
        elif enable_success and not debug_after_active and not autonomous_after_active:
            print("\n❌ CONSISTENT FAILURE: Both endpoints show same failure")
            print("💡 Issue is in enable_trading() method logic")
            return False
        elif debug_after_active != autonomous_after_active:
            print("\n❌ INSTANCE MISMATCH: Different endpoints show different states")
            print("💡 Multiple orchestrator instances detected")
            return False
        else:
            print("\n❌ UNKNOWN ISSUE: Unexpected state combination")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_instance_consistency()
    sys.exit(0 if success else 1) 
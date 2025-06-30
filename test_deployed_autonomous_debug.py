#!/usr/bin/env python3
"""
Test Deployed Autonomous Trading - Root Cause Analysis
"""

import requests
import json
import time
from datetime import datetime
import sys

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_autonomous_issue():
    """Test the autonomous trading issue"""
    print("🎯 DEPLOYED APP DIAGNOSTIC")
    print("=" * 40)
    
    try:
        # Test 1: Get status before
        print("📊 Getting initial status...")
        status_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        print(f"   Status: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_before = status_response.json()
            is_active_before = status_before.get('data', {}).get('is_active', False)
            print(f"   is_active before: {is_active_before}")
        else:
            print(f"   Error: {status_response.text}")
            return False
        
        # Test 2: Try to start trading
        print("\n🚀 Testing autonomous start...")
        start_response = requests.post(f"{BASE_URL}/api/v1/autonomous/start", 
                                     headers={"Content-Type": "application/json"},
                                     timeout=15)
        print(f"   Start status: {start_response.status_code}")
        print(f"   Start response: {start_response.text}")
        
        if start_response.status_code != 200:
            print("❌ Start failed")
            return False
        
        start_data = start_response.json()
        start_success = start_data.get('success', False)
        print(f"   Start success: {start_success}")
        
        # Test 3: Get status after
        print("\n📊 Getting status after start...")
        time.sleep(2)
        status_after_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        
        if status_after_response.status_code == 200:
            status_after = status_after_response.json()
            is_active_after = status_after.get('data', {}).get('is_active', False)
            print(f"   is_active after: {is_active_after}")
        else:
            print(f"   Error: {status_after_response.text}")
            return False
        
        # Test 4: Check debug endpoints (if deployed)
        print("\n🔍 Testing debug endpoints...")
        try:
            debug_response = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=10)
            print(f"   Debug status: {debug_response.status_code}")
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                orchestrator_state = debug_data.get('orchestrator_state', {})
                
                print(f"   system_ready: {orchestrator_state.get('system_ready')}")
                print(f"   is_active: {orchestrator_state.get('is_active')}")
                
                trading_readiness = debug_data.get('trading_readiness', {})
                print(f"   can_start_trading: {trading_readiness.get('can_start_trading')}")
                print(f"   market_open: {trading_readiness.get('market_open')}")
                
            elif debug_response.status_code == 404:
                print("   Debug endpoints not deployed yet")
            else:
                print(f"   Debug error: {debug_response.text}")
                
        except Exception as e:
            print(f"   Debug test failed: {e}")
        
        # Analysis
        print(f"\n🧐 ANALYSIS:")
        print(f"   Start success: {start_success}")
        print(f"   is_active changed: {is_active_before} -> {is_active_after}")
        
        if start_success and not is_active_after:
            print("\n🎯 ISSUE CONFIRMED:")
            print("❌ Start succeeds but is_active stays False")
            print("💡 enable_trading() claims success but doesn't activate")
            return True
        else:
            print("✅ No issue detected or different problem")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_autonomous_issue()
    sys.exit(0 if success else 1) 
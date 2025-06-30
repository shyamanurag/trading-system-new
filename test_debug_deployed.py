#!/usr/bin/env python3
"""
Test Debug Endpoints - Wait for deployment and reveal internal state
"""

import requests
import json
import time
import sys

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_debug_endpoints():
    """Check if debug endpoints are deployed"""
    print("🔍 Testing debug endpoint deployment...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Debug endpoints deployed!")
            debug_data = response.json()
            
            print("\n🔬 ORCHESTRATOR INTERNAL STATE:")
            print("=" * 40)
            
            # Show orchestrator state
            orchestrator_state = debug_data.get('orchestrator_state', {})
            print(f"system_ready: {orchestrator_state.get('system_ready')}")
            print(f"is_active: {orchestrator_state.get('is_active')}")
            print(f"session_id: {orchestrator_state.get('session_id')}")
            print(f"start_time: {orchestrator_state.get('start_time')}")
            
            # Show component status
            print(f"\n🔧 COMPONENT STATUS:")
            component_status = debug_data.get('component_status', {})
            for name, status in component_status.items():
                print(f"   {name}: {status}")
            
            # Show trading readiness
            print(f"\n🎯 TRADING READINESS:")
            trading_readiness = debug_data.get('trading_readiness', {})
            print(f"   market_open: {trading_readiness.get('market_open')}")
            print(f"   can_start_trading: {trading_readiness.get('can_start_trading')}")
            
            # Identify the exact problem
            system_ready = orchestrator_state.get('system_ready')
            can_start = trading_readiness.get('can_start_trading')
            
            print(f"\n🎯 ROOT CAUSE ANALYSIS:")
            if system_ready == False:
                print("❌ FOUND IT: system_ready = False")
                print("💡 This causes enable_trading() early return")
                print("🔧 Fix: System initialization is failing")
            elif can_start == False:
                print("❌ FOUND IT: can_start_trading = False") 
                print("💡 Trading readiness conditions not met")
                print("🔧 Fix: Check _can_start_trading() logic")
            else:
                print("🤔 MYSTERY: Both system_ready and can_start_trading OK")
                print("❓ Issue may be in enable_trading() method itself")
            
            return True
            
        elif response.status_code == 404:
            print("⏰ Debug endpoints not deployed yet")
            return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_force_methods():
    """Test force initialization and enable methods"""
    print(f"\n🔧 Testing force methods...")
    
    try:
        # Test force initialization
        print("   Testing force-initialize...")
        response = requests.post(f"{BASE_URL}/api/v1/debug/force-initialize", timeout=15)
        print(f"   Force init: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Result: {result}")
        
        # Test force enable trading
        print("   Testing force-enable-trading...")
        response = requests.post(f"{BASE_URL}/api/v1/debug/force-enable-trading", timeout=15)
        print(f"   Force enable: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Result: {result}")
            
            # Check if force enable worked
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                is_active = status_data.get('data', {}).get('is_active', False)
                print(f"   is_active after force: {is_active}")
                
                if is_active:
                    print("🎉 SUCCESS: Force enable worked!")
                    print("💡 Confirms issue is in system_ready check")
                else:
                    print("❌ Force enable also failed")
                    print("💡 Issue deeper in enable_trading() logic")
        
    except Exception as e:
        print(f"❌ Force test failed: {e}")

def main():
    """Main test function"""
    print("🎯 DEBUG ENDPOINT TEST")
    print("=" * 30)
    
    # Wait up to 5 minutes for deployment
    max_attempts = 10
    for attempt in range(max_attempts):
        print(f"\n🔄 Attempt {attempt + 1}/{max_attempts}")
        
        if check_debug_endpoints():
            # Debug endpoints are available, test force methods
            test_force_methods()
            return True
        
        if attempt < max_attempts - 1:
            print("⏰ Waiting 30 seconds for deployment...")
            time.sleep(30)
    
    print("❌ Debug endpoints never became available")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
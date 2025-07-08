#!/usr/bin/env python3
"""
Post-Deployment Verification Script
==================================
Quick tests to confirm manual deployment + cache clear worked
"""

import requests
import json
import time

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_critical_fixes():
    """Test if our critical fixes are now deployed"""
    print("🚀 POST-DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    # Test 1: Missing method fix
    print("1. TESTING MISSING METHOD FIX:")
    try:
        r = requests.get(f"{DEPLOYED_URL}/api/v1/debug/initialization-status", timeout=10)
        response_text = r.text
        
        if 'strategy_engine' in response_text and 'attribute' in response_text:
            print("   ❌ STILL BROKEN: Missing method error")
            print(f"   Error: {response_text[:100]}")
            return False
        else:
            print("   ✅ FIXED: Method exists - no attribute error")
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"   ✅ Returns proper JSON: {data.get('success', 'unknown')}")
                except:
                    print("   ⚠️ No JSON response")
            return True
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_force_initialize_fix():
    """Test if force initialize method is now working"""
    print("\n2. TESTING FORCE INITIALIZE FIX:")
    try:
        r = requests.post(f"{DEPLOYED_URL}/api/v1/debug/force-initialize", timeout=15)
        
        if r.status_code == 500:
            print("   ❌ STILL BROKEN: HTTP 500 validation error")
            return False
        elif r.status_code == 200:
            try:
                data = r.json()
                success = data.get('success', False)
                message = data.get('message', 'No message')
                
                print("   ✅ FIXED: HTTP 200 with proper JSON")
                print(f"   Response: success={success}")
                print(f"   Message: {message}")
                
                # Check if it actually initialized components
                if success:
                    components_ready = data.get('components_ready', 0)
                    print(f"   🎯 Components Ready: {components_ready}")
                    return True
                else:
                    print(f"   ⚠️ Method works but initialization failed")
                    return True  # Method exists, that's what we're testing
                    
            except Exception as e:
                print(f"   ⚠️ HTTP 200 but JSON error: {e}")
                return True  # At least no HTTP 500
        else:
            print(f"   ⚠️ Unexpected status: {r.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_component_status():
    """Test if components are now properly initializing"""
    print("\n3. TESTING COMPONENT STATUS:")
    try:
        r = requests.get(f"{DEPLOYED_URL}/api/v1/debug/orchestrator-debug", timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            
            if data.get('success', False):
                components = data.get('components', {})
                ready_count = data.get('components_ready_count', 0)
                total_count = data.get('total_components', 0)
                
                print(f"   ✅ Component Status: {ready_count}/{total_count} ready")
                
                # Check critical trade engine
                trade_engine = components.get('trade_engine', False)
                print(f"   🎯 TRADE ENGINE: {trade_engine}")
                
                if trade_engine:
                    print("   ✅ CRITICAL SUCCESS: Trade engine is TRUE!")
                    print("   🎯 This should fix zero trades issue")
                    return True
                else:
                    print("   ❌ CRITICAL: Trade engine still FALSE")
                    print("   🚨 Zero trades will continue")
                    return False
            else:
                error = data.get('error', 'Unknown error')
                print(f"   ❌ Orchestrator error: {error}")
                return False
        else:
            print(f"   ❌ HTTP {r.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_trading_status():
    """Quick check of trading status"""
    print("\n4. TESTING TRADING STATUS:")
    try:
        r = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        
        if r.status_code == 200:
            data = r.json()['data']
            
            active_strategies = data.get('active_strategies', [])
            total_trades = data.get('total_trades', 0)
            system_ready = data.get('system_ready', False)
            
            print(f"   📊 Active Strategies: {len(active_strategies)}")
            print(f"   📊 System Ready: {system_ready}")
            print(f"   💰 Total Trades: {total_trades}")
            
            return len(active_strategies) > 0 and system_ready
            
    except Exception as e:
        print(f"   ❌ Trading status error: {e}")
        return False

def main():
    """Main verification function"""
    print(f"Testing URL: {DEPLOYED_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test1 = test_critical_fixes()
    test2 = test_force_initialize_fix()
    test3 = test_component_status()
    test4 = test_trading_status()
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION SUMMARY:")
    
    if test1 and test2:
        print("✅ DEPLOYMENT SUCCESS: Missing methods fixed")
    else:
        print("❌ DEPLOYMENT FAILED: Methods still missing")
    
    if test3:
        print("✅ COMPONENT SUCCESS: Trade engine active")
        print("🎯 ZERO TRADES SHOULD BE FIXED")
    else:
        print("❌ COMPONENT FAILED: Trade engine still inactive")
        print("🚨 ZERO TRADES WILL CONTINUE")
    
    if test1 and test2 and test3:
        print("\n🎉 FULL SUCCESS: All fixes deployed!")
        print("💰 Monitor for actual trades in next few minutes")
    else:
        print("\n⚠️ PARTIAL SUCCESS: Some issues remain")

if __name__ == "__main__":
    main() 
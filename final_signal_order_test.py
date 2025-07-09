#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_broker_status():
    """Test broker connectivity and API activity"""
    print("🔍 BROKER STATUS & API ACTIVITY")
    print("-" * 40)
    
    try:
        r = requests.get(f"{BASE_URL}/api/v1/broker/status")
        print(f"   Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Broker: {data.get('broker', 'Unknown')}")
            print(f"   ✅ Connected: {data.get('status', 'Unknown')}")
            print(f"   ✅ API Calls Today: {data.get('api_calls_today', 0)}")
            print(f"   ✅ Market Data Connected: {data.get('market_data_connected', False)}")
            print(f"   ✅ Order Management Connected: {data.get('order_management_connected', False)}")
            
            return True, data.get('api_calls_today', 0)
        else:
            print(f"   ❌ Failed: {r.text[:100]}")
            return False, 0
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, 0

def test_autonomous_endpoints():
    """Test autonomous trading endpoints"""
    print("\n🔍 AUTONOMOUS TRADING ENDPOINTS")
    print("-" * 40)
    
    endpoints = [
        ('GET', '/api/v1/autonomous/status'),
        ('POST', '/api/v1/autonomous/start')
    ]
    
    results = {}
    
    for method, endpoint in endpoints:
        try:
            print(f"   Testing {method} {endpoint}...")
            
            if method == 'POST':
                r = requests.post(f"{BASE_URL}{endpoint}")
            else:
                r = requests.get(f"{BASE_URL}{endpoint}")
            
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"   ✅ Success: {data}")
                results[endpoint] = {"success": True, "data": data}
            else:
                print(f"   ❌ Error: {r.text[:100]}")
                results[endpoint] = {"success": False, "error": r.text[:100]}
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results[endpoint] = {"success": False, "error": str(e)}
    
    return results

def monitor_api_activity(initial_calls, duration=15):
    """Monitor API activity over time"""
    print(f"\n🔍 MONITORING API ACTIVITY ({duration} seconds)")
    print("-" * 40)
    
    print(f"   Initial API Calls: {initial_calls}")
    print(f"   Monitoring for {duration} seconds...")
    
    for i in range(duration):
        time.sleep(1)
        if i % 5 == 0:  # Check every 5 seconds
            try:
                r = requests.get(f"{BASE_URL}/api/v1/broker/status")
                if r.status_code == 200:
                    data = r.json()
                    current_calls = data.get('api_calls_today', 0)
                    if current_calls > initial_calls:
                        print(f"   ✅ API ACTIVITY at {i}s: {current_calls - initial_calls} new calls")
                        return True, current_calls - initial_calls
                    else:
                        print(f"   ⏰ {i}s: No new activity ({current_calls} total)")
            except:
                pass
    
    # Final check
    try:
        r = requests.get(f"{BASE_URL}/api/v1/broker/status")
        if r.status_code == 200:
            data = r.json()
            final_calls = data.get('api_calls_today', 0)
            new_calls = final_calls - initial_calls
            
            if new_calls > 0:
                print(f"   ✅ FINAL RESULT: {new_calls} new API calls detected")
                return True, new_calls
            else:
                print(f"   ⚠️  FINAL RESULT: No new API calls detected")
                return False, 0
    except:
        pass
    
    return False, 0

def main():
    print("🚀 COMPREHENSIVE SIGNAL & ORDER PROCESSING TEST")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: {BASE_URL}")
    
    # Test 1: Broker Status
    broker_success, initial_api_calls = test_broker_status()
    
    if not broker_success:
        print("\n❌ BROKER CONNECTIVITY FAILED - Cannot proceed with tests")
        return
    
    # Test 2: Autonomous Endpoints
    autonomous_results = test_autonomous_endpoints()
    
    # Test 3: Monitor API Activity
    api_activity, new_calls = monitor_api_activity(initial_api_calls)
    
    # Final Analysis
    print(f"\n📊 FINAL ANALYSIS")
    print("=" * 60)
    
    print(f"🎯 BROKER CONNECTIVITY: {'✅ WORKING' if broker_success else '❌ FAILED'}")
    
    autonomous_working = any(result.get('success', False) for result in autonomous_results.values())
    print(f"🎯 AUTONOMOUS ENDPOINTS: {'✅ WORKING' if autonomous_working else '❌ FAILED'}")
    
    print(f"🎯 API ACTIVITY: {'✅ DETECTED' if api_activity else '⚠️  NONE'}")
    
    if api_activity:
        print(f"   📈 OrderManager made {new_calls} API calls to Zerodha")
        print("   ✅ Signal → OrderManager → Zerodha pipeline is WORKING")
    else:
        print("   ⚠️  OrderManager is not making API calls")
        print("   ❌ Signal → OrderManager → Zerodha pipeline needs investigation")
    
    print("\n💡 RECOMMENDATIONS:")
    
    if broker_success and autonomous_working and api_activity:
        print("   🎉 ALL SYSTEMS OPERATIONAL!")
        print("   ✅ Signal and order processing pipeline is working correctly")
        print("   🚀 System is ready for live trading")
    elif broker_success and api_activity:
        print("   🔧 Partial Success: API calls detected but autonomous endpoints have issues")
        print("   ⚠️  OrderManager is working but may need autonomous endpoint fixes")
    elif broker_success:
        print("   🔧 Broker connected but no trading activity detected")
        print("   ❌ Check orchestrator initialization and signal generation")
    else:
        print("   🚨 Critical issues detected")
        print("   ❌ System not ready for live trading")
    
    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main() 
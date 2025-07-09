#!/usr/bin/env python3
"""
Signal and Order Processing Diagnosis
=====================================
Comprehensive diagnosis focusing on what's working vs what needs fixes
"""

import requests
import time
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_working_endpoints():
    """Test endpoints that should be working"""
    print("🔍 TESTING KNOWN WORKING ENDPOINTS")
    print("=" * 50)
    
    working_endpoints = {
        "Broker Status": "/api/v1/broker/status",
        "Debug Orchestrator": "/api/v1/debug/orchestrator",
        "Debug System": "/api/v1/debug/system-ready",
        "Debug Initialize": "/api/v1/debug/initialize",
        "Debug Signals": "/api/v1/debug/test-signal-generation"
    }
    
    results = {}
    
    for name, endpoint in working_endpoints.items():
        try:
            print(f"\n📊 {name}")
            r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"   ✅ Response: {str(data)[:100]}...")
                results[name] = {"success": True, "data": data}
            else:
                print(f"   ❌ Error: {r.text[:100]}")
                results[name] = {"success": False, "error": r.text[:100]}
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results[name] = {"success": False, "error": str(e)}
    
    return results

def test_signal_generation():
    """Test signal generation capabilities"""
    print("\n🔍 TESTING SIGNAL GENERATION")
    print("=" * 50)
    
    try:
        # Try to trigger signal generation via debug endpoint
        print("📡 Attempting to trigger signal generation...")
        r = requests.post(f"{BASE_URL}/api/v1/debug/test-signal-generation", timeout=15)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Signals generated: {data}")
            return True, data
        else:
            print(f"   ❌ Failed: {r.text[:100]}")
            return False, r.text[:100]
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, str(e)

def test_order_processing():
    """Test order processing through available endpoints"""
    print("\n🔍 TESTING ORDER PROCESSING")
    print("=" * 50)
    
    try:
        # Check if we can access order-related debug endpoints
        endpoints = [
            "/api/v1/debug/check-order-manager",
            "/api/v1/debug/test-order-flow"
        ]
        
        for endpoint in endpoints:
            print(f"📋 Testing {endpoint}")
            try:
                r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                print(f"   Status: {r.status_code}")
                
                if r.status_code == 200:
                    data = r.json()
                    print(f"   ✅ Response: {str(data)[:100]}...")
                else:
                    print(f"   ❌ Error: {r.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        return True, "Order processing tests completed"
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, str(e)

def test_orchestrator_status():
    """Test orchestrator status and initialization"""
    print("\n🔍 TESTING ORCHESTRATOR STATUS")
    print("=" * 50)
    
    try:
        # Test orchestrator debug endpoint
        print("🎛️ Checking orchestrator status...")
        r = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=10)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Orchestrator data: {json.dumps(data, indent=2)}")
            
            # Check key orchestrator fields
            if 'is_initialized' in data:
                print(f"   📊 Initialized: {data['is_initialized']}")
            if 'is_running' in data:
                print(f"   📊 Running: {data['is_running']}")
            if 'strategies_count' in data:
                print(f"   📊 Strategies: {data['strategies_count']}")
            if 'components' in data:
                print(f"   📊 Components: {data['components']}")
                
            return True, data
        else:
            print(f"   ❌ Failed: {r.text[:100]}")
            return False, r.text[:100]
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, str(e)

def attempt_system_initialization():
    """Attempt to initialize the system"""
    print("\n🔍 ATTEMPTING SYSTEM INITIALIZATION")
    print("=" * 50)
    
    try:
        # Try to force initialization
        print("🚀 Forcing system initialization...")
        r = requests.post(f"{BASE_URL}/api/v1/debug/force-initialize", timeout=20)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Initialization response: {data}")
            return True, data
        else:
            print(f"   ❌ Initialization failed: {r.text[:100]}")
            return False, r.text[:100]
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, str(e)

def test_pipeline_flow():
    """Test the complete pipeline flow"""
    print("\n🔍 TESTING COMPLETE PIPELINE FLOW")
    print("=" * 50)
    
    try:
        # Step 1: Check broker connectivity
        print("1️⃣ Checking broker connectivity...")
        broker_r = requests.get(f"{BASE_URL}/api/v1/broker/status")
        if broker_r.status_code == 200:
            broker_data = broker_r.json()
            print(f"   ✅ Broker connected: {broker_data.get('status')}")
            print(f"   📊 API calls today: {broker_data.get('api_calls_today', 0)}")
        else:
            print(f"   ❌ Broker check failed")
            return False, "Broker connectivity failed"
        
        # Step 2: Try to access any working autonomous endpoint
        print("\n2️⃣ Testing autonomous endpoints...")
        autonomous_endpoints = [
            "/api/v1/autonomous/start",
            "/api/v1/autonomous/status"
        ]
        
        for endpoint in autonomous_endpoints:
            try:
                if endpoint.endswith('/start'):
                    r = requests.post(f"{BASE_URL}{endpoint}")
                else:
                    r = requests.get(f"{BASE_URL}{endpoint}")
                
                print(f"   {endpoint}: {r.status_code}")
                
                if r.status_code == 200:
                    print(f"   ✅ Working: {endpoint}")
                elif r.status_code == 500:
                    print(f"   ❌ Server error: {endpoint}")
                    
            except Exception as e:
                print(f"   ❌ Exception on {endpoint}: {e}")
        
        # Step 3: Monitor broker for API activity
        print("\n3️⃣ Monitoring broker for API activity...")
        initial_calls = broker_data.get('api_calls_today', 0)
        
        print(f"   📊 Initial API calls: {initial_calls}")
        print("   ⏰ Waiting 10 seconds...")
        time.sleep(10)
        
        final_broker_r = requests.get(f"{BASE_URL}/api/v1/broker/status")
        if final_broker_r.status_code == 200:
            final_broker_data = final_broker_r.json()
            final_calls = final_broker_data.get('api_calls_today', 0)
            print(f"   📊 Final API calls: {final_calls}")
            
            if final_calls > initial_calls:
                print(f"   ✅ API ACTIVITY DETECTED! ({final_calls - initial_calls} new calls)")
                return True, f"Pipeline working - {final_calls - initial_calls} API calls made"
            else:
                print(f"   ⚠️ No new API calls detected")
                return False, "No API activity detected"
        
        return True, "Pipeline test completed"
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, str(e)

def generate_diagnosis_report(results):
    """Generate comprehensive diagnosis report"""
    print("\n" + "=" * 60)
    print("📊 SIGNAL & ORDER PROCESSING DIAGNOSIS REPORT")
    print("=" * 60)
    
    print("\n🎯 KEY FINDINGS:")
    
    # Analyze broker connectivity
    broker_working = any("Broker" in key and result.get("success") for key, result in results.items())
    if broker_working:
        print("   ✅ Zerodha broker connectivity: WORKING")
    else:
        print("   ❌ Zerodha broker connectivity: FAILED")
    
    # Analyze orchestrator status
    orchestrator_working = any("orchestrator" in key.lower() and result.get("success") for key, result in results.items())
    if orchestrator_working:
        print("   ✅ Orchestrator system: PARTIALLY WORKING")
    else:
        print("   ❌ Orchestrator system: NEEDS INVESTIGATION")
    
    # Analyze signal generation
    signals_working = any("signal" in key.lower() and result.get("success") for key, result in results.items())
    if signals_working:
        print("   ✅ Signal generation: WORKING")
    else:
        print("   ⚠️ Signal generation: NEEDS TESTING")
    
    print("\n💡 RECOMMENDATIONS:")
    
    if broker_working and orchestrator_working:
        print("   🎉 Core components are working!")
        print("   🔧 Focus on autonomous trading endpoint fixes")
        print("   ⚠️ 500 errors indicate orchestrator dependency injection issues")
    elif broker_working:
        print("   🔧 Broker is connected but orchestrator needs initialization")
        print("   🚀 Try force initialization through debug endpoints")
    else:
        print("   🚨 Critical connectivity issues detected")
        print("   ❌ Check deployment status and system logs")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Wait for deployment to complete (if recent changes)")
    print("   2. Use debug endpoints to force system initialization")
    print("   3. Monitor broker API calls for OrderManager activity")
    print("   4. Check system logs for specific error messages")

def main():
    """Run comprehensive signal and order processing diagnosis"""
    print("🚀 SIGNAL & ORDER PROCESSING DIAGNOSIS")
    print("=" * 60)
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target URL: {BASE_URL}")
    
    results = {}
    
    # Run diagnostic tests
    results.update(test_working_endpoints())
    results["signal_generation"] = {"success": *test_signal_generation()}
    results["order_processing"] = {"success": *test_order_processing()}
    results["orchestrator_status"] = {"success": *test_orchestrator_status()}
    results["system_initialization"] = {"success": *attempt_system_initialization()}
    results["pipeline_flow"] = {"success": *test_pipeline_flow()}
    
    # Generate report
    generate_diagnosis_report(results)
    
    print(f"\n⏰ Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main() 
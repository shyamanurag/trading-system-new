#!/usr/bin/env python3
"""
Debug 500 Errors in Autonomous Trading Endpoints
================================================
Comprehensive debugging to identify root cause of persistent 500 errors
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_all_endpoints():
    """Test all available endpoints to identify working vs failing ones"""
    print("🔍 TESTING ALL ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ('GET', '/api/v1/broker/status'),
        ('GET', '/api/v1/autonomous/status'),
        ('POST', '/api/v1/autonomous/start'),
        ('GET', '/api/v1/debug/orchestrator'),
        ('GET', '/api/v1/debug/system-ready'),
        ('GET', '/api/v1/debug/initialize'),
        ('POST', '/api/v1/debug/force-initialize'),
        ('GET', '/api/v1/health'),
        ('GET', '/api/v1/monitoring/status'),
        ('GET', '/api/v1/strategies'),
        ('GET', '/api/v1/signals'),
    ]
    
    results = {}
    
    for method, endpoint in endpoints:
        try:
            print(f"\n📡 Testing {method} {endpoint}")
            
            if method == 'POST':
                r = requests.post(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"   ✅ Success: {str(data)[:100]}...")
                    results[endpoint] = {'status': 'success', 'data': data}
                except:
                    print(f"   ✅ Success: {r.text[:100]}...")
                    results[endpoint] = {'status': 'success', 'data': r.text}
            elif r.status_code == 404:
                print(f"   ❌ Not Found: {r.text[:100]}")
                results[endpoint] = {'status': 'not_found', 'error': r.text}
            elif r.status_code == 500:
                print(f"   ❌ Server Error: {r.text[:100]}")
                results[endpoint] = {'status': 'server_error', 'error': r.text}
            else:
                print(f"   ⚠️  Status {r.status_code}: {r.text[:100]}")
                results[endpoint] = {'status': r.status_code, 'error': r.text}
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results[endpoint] = {'status': 'exception', 'error': str(e)}
    
    return results

def analyze_deployment_state():
    """Analyze the deployment state and identify issues"""
    print("\n🔍 DEPLOYMENT STATE ANALYSIS")
    print("=" * 50)
    
    # Check deployment timestamp
    try:
        print("📅 Checking deployment timestamp...")
        r = requests.get(f"{BASE_URL}/api/v1/debug/system-ready", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ System Ready Response: {data}")
        else:
            print(f"   ❌ System Ready Failed: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ System Ready Exception: {e}")
    
    # Check if orchestrator is initialized
    try:
        print("\n🎛️ Checking orchestrator status...")
        r = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Orchestrator Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   ❌ Orchestrator Failed: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Orchestrator Exception: {e}")
    
    # Try to force initialize
    try:
        print("\n🚀 Attempting forced initialization...")
        r = requests.post(f"{BASE_URL}/api/v1/debug/force-initialize", timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Force Initialize Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   ❌ Force Initialize Failed: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Force Initialize Exception: {e}")

def test_autonomous_endpoints_directly():
    """Test autonomous endpoints with detailed error analysis"""
    print("\n🔍 DETAILED AUTONOMOUS ENDPOINT TESTING")
    print("=" * 50)
    
    # Test status endpoint
    try:
        print("📊 Testing autonomous status endpoint...")
        r = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        print(f"   Status Code: {r.status_code}")
        print(f"   Headers: {dict(r.headers)}")
        print(f"   Response: {r.text}")
        
        if r.status_code == 500:
            print("   🔍 This is a 500 Internal Server Error")
            print("   🔍 This suggests an unhandled exception in the autonomous trading API")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test start endpoint
    try:
        print("\n🚀 Testing autonomous start endpoint...")
        r = requests.post(f"{BASE_URL}/api/v1/autonomous/start", timeout=15)
        print(f"   Status Code: {r.status_code}")
        print(f"   Headers: {dict(r.headers)}")
        print(f"   Response: {r.text}")
        
        if r.status_code == 500:
            print("   🔍 This is a 500 Internal Server Error")
            print("   🔍 This suggests an unhandled exception in the autonomous trading API")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def generate_diagnostic_report(endpoint_results):
    """Generate comprehensive diagnostic report"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE 500 ERROR DIAGNOSIS REPORT")
    print("=" * 70)
    
    print(f"⏰ Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target System: {BASE_URL}")
    
    # Analyze endpoint results
    working_endpoints = [ep for ep, result in endpoint_results.items() if result['status'] == 'success']
    failing_endpoints = [ep for ep, result in endpoint_results.items() if result['status'] == 'server_error']
    not_found_endpoints = [ep for ep, result in endpoint_results.items() if result['status'] == 'not_found']
    
    print(f"\n📊 ENDPOINT STATUS SUMMARY:")
    print(f"   ✅ Working Endpoints: {len(working_endpoints)}")
    print(f"   ❌ 500 Error Endpoints: {len(failing_endpoints)}")
    print(f"   ❌ 404 Not Found Endpoints: {len(not_found_endpoints)}")
    
    if working_endpoints:
        print(f"\n✅ WORKING ENDPOINTS:")
        for ep in working_endpoints:
            print(f"   - {ep}")
    
    if failing_endpoints:
        print(f"\n❌ FAILING ENDPOINTS (500 Errors):")
        for ep in failing_endpoints:
            print(f"   - {ep}")
    
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    # Check specific patterns
    broker_working = '/api/v1/broker/status' in working_endpoints
    autonomous_failing = any('/autonomous/' in ep for ep in failing_endpoints)
    debug_working = any('/debug/' in ep for ep in working_endpoints)
    
    if broker_working and autonomous_failing:
        print("   🎯 PATTERN IDENTIFIED: Broker working but autonomous endpoints failing")
        print("   🔍 ROOT CAUSE: Orchestrator dependency injection issue")
        print("   🔧 SOLUTION: Fix orchestrator initialization in autonomous API")
    
    if debug_working and autonomous_failing:
        print("   🎯 PATTERN IDENTIFIED: Debug endpoints working but autonomous failing")
        print("   🔍 ROOT CAUSE: Orchestrator accessible via debug but not via autonomous API")
        print("   🔧 SOLUTION: Fix get_orchestrator() function in autonomous API")
    
    print(f"\n💡 IMMEDIATE ACTIONS:")
    print("   1. Check orchestrator initialization in autonomous_trading.py")
    print("   2. Verify get_orchestrator() function is properly implemented")
    print("   3. Check if TradingOrchestrator.get_instance() method exists")
    print("   4. Verify deployment completed successfully")
    print("   5. Check system logs for specific error messages")

def main():
    """Run comprehensive 500 error diagnosis"""
    print("🚀 COMPREHENSIVE 500 ERROR DIAGNOSIS")
    print("=" * 70)
    
    # Test all endpoints
    endpoint_results = test_all_endpoints()
    
    # Analyze deployment state
    analyze_deployment_state()
    
    # Test autonomous endpoints specifically
    test_autonomous_endpoints_directly()
    
    # Generate diagnostic report
    generate_diagnostic_report(endpoint_results)
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main() 
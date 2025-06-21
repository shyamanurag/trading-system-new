#!/usr/bin/env python3
"""
Comprehensive Deployment Test Script
Tests all key endpoints after redeployment with cleaned requirements.
"""

import requests
import json
import time
from datetime import datetime

# Base URL for the deployed application
BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"🔍 Testing: {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ PASS - Expected {expected_status}, got {response.status_code}")
            
            # Try to parse JSON response
            try:
                json_data = response.json()
                print(f"   📄 Response: {json.dumps(json_data, indent=2)[:200]}...")
            except:
                print(f"   📄 Response: {response.text[:200]}...")
            
            return True
        else:
            print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT - Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   🔌 CONNECTION ERROR - Could not connect")
        return False
    except Exception as e:
        print(f"   💥 ERROR - {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Deployment Test")
    print(f"📍 Testing URL: {BASE_URL}")
    print(f"⏰ Test Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test results tracking
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # 1. Basic Health Checks
    print("\n🏥 HEALTH CHECKS")
    print("-" * 30)
    
    health_endpoints = [
        ("/", 200),
        ("/health", 200),
        ("/health/alive", 200),
        ("/health/ready", 200),
    ]
    
    for endpoint, expected_status in health_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)  # Rate limiting
    
    # 2. API Documentation
    print("\n📚 API DOCUMENTATION")
    print("-" * 30)
    
    docs_endpoints = [
        ("/docs", 200),
        ("/openapi.json", 200),
    ]
    
    for endpoint, expected_status in docs_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 3. Authentication Endpoints
    print("\n🔐 AUTHENTICATION")
    print("-" * 30)
    
    auth_endpoints = [
        ("/api/v1/auth/test", 200),
        ("/auth/test", 200),
    ]
    
    for endpoint, expected_status in auth_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 4. Market Data Endpoints (CRITICAL)
    print("\n📈 MARKET DATA (CRITICAL)")
    print("-" * 30)
    
    market_endpoints = [
        ("/api/v1/market/indices", 200),
        ("/api/v1/market/market-status", 200),
        ("/api/market/indices", 200),
        ("/api/market/market-status", 200),
        ("/market/indices", 200),
        ("/market/market-status", 200),
    ]
    
    for endpoint, expected_status in market_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 5. Dashboard and Analytics
    print("\n📊 DASHBOARD & ANALYTICS")
    print("-" * 30)
    
    dashboard_endpoints = [
        ("/api/v1/dashboard/data", 200),
        ("/api/v1/health/data", 200),
        ("/api/v1/market/data", 200),
    ]
    
    for endpoint, expected_status in dashboard_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 6. User Management
    print("\n👥 USER MANAGEMENT")
    print("-" * 30)
    
    user_endpoints = [
        ("/api/v1/users", 200),
        ("/api/v1/users/current", 200),
    ]
    
    for endpoint, expected_status in user_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 7. Trading and Recommendations
    print("\n💹 TRADING & RECOMMENDATIONS")
    print("-" * 30)
    
    trading_endpoints = [
        ("/api/v1/recommendations/elite", 200),
        ("/api/v1/performance/elite-trades", 200),
        ("/api/v1/performance/daily-pnl", 200),
    ]
    
    for endpoint, expected_status in trading_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 8. Debug and Test Endpoints
    print("\n🐛 DEBUG & TEST")
    print("-" * 30)
    
    debug_endpoints = [
        ("/api/test/routes", 200),
        ("/api/debug/routes", 200),
    ]
    
    for endpoint, expected_status in debug_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 9. WebSocket Endpoints
    print("\n🔌 WEBSOCKET ENDPOINTS")
    print("-" * 30)
    
    ws_endpoints = [
        ("/api/websocket/stats", 200),
    ]
    
    for endpoint, expected_status in ws_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # 10. System Control
    print("\n⚙️ SYSTEM CONTROL")
    print("-" * 30)
    
    control_endpoints = [
        ("/webhook", 405),  # Should return Method Not Allowed for GET
        ("/control", 405),  # Should return Method Not Allowed for GET
    ]
    
    for endpoint, expected_status in control_endpoints:
        total_tests += 1
        if test_endpoint(endpoint, expected_status=expected_status):
            passed_tests += 1
        else:
            failed_tests += 1
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Deployment is working perfectly!")
    elif failed_tests <= 3:
        print(f"\n⚠️  {failed_tests} tests failed. Most functionality is working.")
    else:
        print(f"\n🚨 {failed_tests} tests failed. There may be deployment issues.")
    
    print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main() 
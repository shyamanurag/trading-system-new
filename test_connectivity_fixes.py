#!/usr/bin/env python3
"""
Test script to verify frontend-to-backend connectivity fixes
"""
import requests
import json
import sys
from datetime import datetime

# Test endpoints that were causing connectivity issues
TEST_ENDPOINTS = [
    {
        "name": "Users Performance (New)",
        "url": "https://algoauto-9gx56.ondigitalocean.app/api/v1/users/performance",
        "method": "GET",
        "expected_fields": ["success", "data", "timestamp"]
    },
    {
        "name": "Market Indices (New)",
        "url": "https://algoauto-9gx56.ondigitalocean.app/api/market/indices",
        "method": "GET",
        "expected_fields": ["success", "data", "timestamp"]
    },
    {
        "name": "Dashboard Data (Standardized)",
        "url": "https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/data",
        "method": "GET",
        "expected_fields": ["success", "data", "timestamp"]
    },
    {
        "name": "Elite Recommendations",
        "url": "https://algoauto-9gx56.ondigitalocean.app/api/v1/elite",
        "method": "GET",
        "expected_fields": ["success", "data", "timestamp"]
    },
    {
        "name": "Strategies Management",
        "url": "https://algoauto-9gx56.ondigitalocean.app/api/v1/strategies",
        "method": "GET",
        "expected_fields": []  # May return empty array
    },
    {
        "name": "WebSocket Test Page",
        "url": "https://algoauto-9gx56.ondigitalocean.app/ws/test",
        "method": "GET",
        "expected_fields": []  # HTML page
    }
]

def test_endpoint(endpoint_info):
    """Test a single endpoint"""
    print(f"\n🔍 Testing: {endpoint_info['name']}")
    print(f"📡 URL: {endpoint_info['url']}")
    
    try:
        # Make request with timeout
        response = requests.get(endpoint_info['url'], timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        
        # Check if it's JSON response
        try:
            json_data = response.json()
            print(f"📄 Response Type: JSON")
            
            # Check expected fields
            if endpoint_info['expected_fields']:
                for field in endpoint_info['expected_fields']:
                    if field in json_data:
                        print(f"✅ Field '{field}': Present")
                    else:
                        print(f"❌ Field '{field}': Missing")
            
            # Show sample data structure
            if isinstance(json_data, dict):
                print(f"📊 Data Structure: {list(json_data.keys())}")
            elif isinstance(json_data, list):
                print(f"📊 Data Structure: Array with {len(json_data)} items")
            
        except json.JSONDecodeError:
            print(f"📄 Response Type: Non-JSON (HTML/Text)")
            print(f"📝 Content Length: {len(response.text)} bytes")
            
        return {
            "success": True,
            "status_code": response.status_code,
            "response_size": len(response.text)
        }
        
    except requests.exceptions.Timeout:
        print(f"⏱️ Request timed out")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error")
        return {"success": False, "error": "connection_error"}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Run all connectivity tests"""
    print("🚀 Frontend-to-Backend Connectivity Test Suite")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    results = []
    
    for endpoint in TEST_ENDPOINTS:
        result = test_endpoint(endpoint)
        results.append({
            "endpoint": endpoint['name'],
            "result": result
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 CONNECTIVITY TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['result']['success'])
    total_tests = len(results)
    
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
    
    # Details
    for result in results:
        status = "✅ PASS" if result['result']['success'] else "❌ FAIL"
        print(f"{status} - {result['endpoint']}")
        
        if not result['result']['success']:
            print(f"    Error: {result['result']['error']}")
    
    print(f"\n⏰ Completed at: {datetime.now().isoformat()}")
    
    if successful_tests == total_tests:
        print("🎉 ALL CONNECTIVITY TESTS PASSED!")
        sys.exit(0)
    else:
        print("⚠️ Some connectivity issues remain")
        sys.exit(1)

if __name__ == "__main__":
    main() 
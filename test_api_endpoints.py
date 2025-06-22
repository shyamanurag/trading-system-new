#!/usr/bin/env python3
"""
API Endpoint Tests for AlgoAuto Trading System
Tests all critical endpoints to ensure they're working correctly
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration
BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"
LOCAL_URL = "http://localhost:8000"

# Use local URL if --local flag is passed
if len(sys.argv) > 1 and sys.argv[1] == "--local":
    BASE_URL = LOCAL_URL
    print(f"🏠 Testing locally at {BASE_URL}")
else:
    print(f"☁️  Testing deployment at {BASE_URL}")

# Test credentials
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def test_endpoint(method: str, path: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, expected_status: int = 200) -> Tuple[bool, str]:
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        if response.status_code == expected_status:
            return True, f"Status: {response.status_code}"
        else:
            return False, f"Expected {expected_status}, got {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.ConnectionError:
        return False, "Connection failed"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def print_result(test_name: str, success: bool, message: str):
    """Print test result with color"""
    if success:
        print(f"{Colors.GREEN}✅ {test_name}{Colors.RESET} - {message}")
    else:
        print(f"{Colors.RED}❌ {test_name}{Colors.RESET} - {message}")

def main():
    """Run all tests"""
    print(f"\n🚀 AlgoAuto API Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # 1. Health Check Endpoints
    print(f"\n{Colors.BLUE}🏥 Health Checks{Colors.RESET}")
    print("-" * 30)
    
    health_tests = [
        ("Root", "GET", "/", None, None, 200),
        ("Health", "GET", "/health", None, None, 200),
        ("Ready", "GET", "/ready", None, None, 200),
    ]
    
    for test_name, method, path, data, headers, expected in health_tests:
        success, message = test_endpoint(method, path, data, headers, expected)
        results.append(success)
        print_result(test_name, success, message)
    
    # 2. Authentication
    print(f"\n{Colors.BLUE}🔐 Authentication{Colors.RESET}")
    print("-" * 30)
    
    # Test login
    success, message = test_endpoint("POST", "/auth/login", TEST_USER, None, 200)
    results.append(success)
    print_result("Login", success, message)
    
    # Extract token if login successful
    token = None
    if success:
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
            token = response.json().get("access_token")
            auth_headers = {"Authorization": f"Bearer {token}"}
        except:
            auth_headers = None
    else:
        auth_headers = None
    
    # 3. Market Data Endpoints
    print(f"\n{Colors.BLUE}📈 Market Data{Colors.RESET}")
    print("-" * 30)
    
    market_tests = [
        ("Market Indices", "GET", "/api/market/indices", None, None, 200),
        ("Market Status", "GET", "/api/market/market-status", None, None, 200),
    ]
    
    for test_name, method, path, data, headers, expected in market_tests:
        success, message = test_endpoint(method, path, data, headers, expected)
        results.append(success)
        print_result(test_name, success, message)
    
    # 4. User Endpoints (requires auth)
    if auth_headers:
        print(f"\n{Colors.BLUE}👥 User Management{Colors.RESET}")
        print("-" * 30)
        
        user_tests = [
            ("Current User", "GET", "/api/v1/users/current", None, auth_headers, 200),
            ("User List", "GET", "/api/v1/users/", None, auth_headers, 200),
        ]
        
        for test_name, method, path, data, headers, expected in user_tests:
            success, message = test_endpoint(method, path, data, headers, expected)
            results.append(success)
            print_result(test_name, success, message)
    
    # 5. API Documentation
    print(f"\n{Colors.BLUE}📚 API Documentation{Colors.RESET}")
    print("-" * 30)
    
    doc_tests = [
        ("OpenAPI Docs", "GET", "/docs", None, None, 200),
        ("API Routes List", "GET", "/api/routes", None, None, 200),
    ]
    
    for test_name, method, path, data, headers, expected in doc_tests:
        success, message = test_endpoint(method, path, data, headers, expected)
        results.append(success)
        print_result(test_name, success, message)
    
    # Summary
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"{Colors.BLUE}📊 Test Summary{Colors.RESET}")
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}✅ Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}❌ Failed: {failed}{Colors.RESET}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Check the logs above.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
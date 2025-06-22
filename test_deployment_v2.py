import requests
import os
from datetime import datetime
import time

# --- Configuration ---
BASE_URL = "https://algoauto-jd32t.ondigitalocean.app"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
access_token = None

# --- Helper Functions ---
def print_header(text):
    print("\n" + "="*50)
    print(f" {text}")
    print("="*50)

def print_test_result(test_name, status, details=""):
    print(f"[*] Test: {test_name:<30} | Status: {status:<10} | Details: {details}")

# --- Test Functions ---

def test_health_check():
    """Tests if the basic health endpoint is responsive."""
    test_name = "Health Check (/health)"
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        if response.status_code == 200:
            print_test_result(test_name, "✅ PASS", f"Status: {response.status_code}")
            return True
        else:
            print_test_result(test_name, "❌ FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.RequestException as e:
        print_test_result(test_name, "❌ FAIL", f"Error: {e}")
        return False

def test_login():
    """Tests the login functionality and retrieves an access token."""
    global access_token
    test_name = "Admin Login (/api/auth/login)"
    try:
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                print_test_result(test_name, "✅ PASS", "Successfully retrieved access token.")
                return True
            else:
                print_test_result(test_name, "❌ FAIL", "Login successful but no access token in response.")
                return False
        else:
            print_test_result(test_name, "❌ FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.RequestException as e:
        print_test_result(test_name, "❌ FAIL", f"Error: {e}")
        return False

def test_market_data_endpoint():
    """Tests a non-authenticated market data endpoint."""
    test_name = "Market Data (/api/market/indices)"
    try:
        response = requests.get(f"{BASE_URL}/api/market/indices", timeout=15)
        if response.status_code == 200:
            print_test_result(test_name, "✅ PASS", f"Status: {response.status_code}")
            return True
        else:
            print_test_result(test_name, "❌ FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.RequestException as e:
        print_test_result(test_name, "❌ FAIL", f"Error: {e}")
        return False

def test_authenticated_endpoint():
    """Tests an endpoint that requires authentication."""
    test_name = "Authenticated Route (/api/auth/me)"
    if not access_token:
        print_test_result(test_name, "SKIPPED", "No access token available.")
        return False
        
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15)
        if response.status_code == 200:
            print_test_result(test_name, "✅ PASS", f"Status: {response.status_code}")
            return True
        else:
            print_test_result(test_name, "❌ FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except requests.RequestException as e:
        print_test_result(test_name, "❌ FAIL", f"Error: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    print_header(f"Running Deployment Tests on {BASE_URL}")
    
    # Run tests
    health_ok = test_health_check()
    login_ok = False
    if health_ok:
        login_ok = test_login()
    
    market_data_ok = test_market_data_endpoint()
    
    auth_route_ok = False
    if login_ok:
        auth_route_ok = test_authenticated_endpoint()

    # Final summary
    print_header("Test Summary")
    print(f"  - Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"  - Admin Login:    {'✅ PASS' if login_ok else '❌ FAIL'}")
    print(f"  - Market Data:  {'✅ PASS' if market_data_ok else '❌ FAIL'}")
    print(f"  - Auth Route:   {'✅ PASS' if auth_route_ok else '❌ FAIL'}")
    print("="*50)

    if all([health_ok, login_ok, market_data_ok, auth_route_ok]):
        print("\n🎉 All critical tests passed! The deployment is stable.")
    else:
        print("\n🚨 Some tests failed. Please review the logs above.") 
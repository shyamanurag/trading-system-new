"""
Test all API endpoints to identify which ones are failing
"""
import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "https://algoauto-ua2iq.ondigitalocean.app"

# List of all endpoints being called by the frontend
endpoints = [
    # Dashboard endpoints
    ("GET", "/api/dashboard/summary", "Dashboard Summary"),
    ("GET", "/performance/daily-pnl", "Daily P&L"),
    ("GET", "/recommendations/elite", "Elite Recommendations"),
    
    # Market data endpoints
    ("GET", "/market/indices", "Market Indices"),
    ("GET", "/market/market-status", "Market Status"),
    
    # Autonomous trading endpoints
    ("GET", "/autonomous/status", "Autonomous Status"),
    ("GET", "/api/trading/status", "Trading Status"),
    ("GET", "/api/users/broker", "Broker Users"),
    
    # Performance endpoints
    ("GET", "/performance/elite-trades", "Elite Trades Performance"),
    ("GET", "/performance/summary", "Performance Summary"),
    
    # User endpoints
    ("GET", "/api/users", "All Users"),
]

def test_endpoint(method, path, description):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json={}, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"Response (text): {response.text[:200]}...")
        else:
            print("❌ FAILED")
            print(f"Response: {response.text[:200]}...")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print(f"Testing API Endpoints at {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    results = []
    
    for method, path, description in endpoints:
        success = test_endpoint(method, path, description)
        results.append((path, description, success))
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for _, _, success in results if success)
    total_count = len(results)
    
    print(f"\nTotal Endpoints: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    
    print("\nFailed Endpoints:")
    for path, description, success in results:
        if not success:
            print(f"  ❌ {path} - {description}")
    
    print("\nSuccessful Endpoints:")
    for path, description, success in results:
        if success:
            print(f"  ✅ {path} - {description}")

if __name__ == "__main__":
    main() 
import requests
import time
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

print("🚀 SIGNAL & ORDER PROCESSING STATUS CHECK")
print("=" * 50)

# Test broker status
print("\n1. BROKER STATUS")
r = requests.get(f"{BASE_URL}/api/v1/broker/status")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Broker: {data.get('broker')}")
    print(f"Connected: {data.get('status')}")
    print(f"API Calls: {data.get('api_calls_today', 0)}")
    api_calls_before = data.get('api_calls_today', 0)
    print(f"Initial API Calls: {api_calls_before}")
else:
    print("Broker status failed")
    exit(1)

# Test autonomous endpoints
print("\n2. AUTONOMOUS ENDPOINTS TEST")
endpoints = [
    ('POST', '/api/v1/autonomous/start'),
    ('GET', '/api/v1/autonomous/status')
]

for method, endpoint in endpoints:
    try:
        if method == 'POST':
            r = requests.post(f"{BASE_URL}{endpoint}")
        else:
            r = requests.get(f"{BASE_URL}{endpoint}")
        print(f"{method} {endpoint}: {r.status_code}")
        if r.status_code == 200:
            print(f"  Success: {r.json()}")
        else:
            print(f"  Error: {r.text[:50]}...")
    except Exception as e:
        print(f"{method} {endpoint}: Exception - {e}")

# Monitor for API activity
print("\n3. MONITORING API ACTIVITY")
print("Waiting 10 seconds to check for API calls...")
time.sleep(10)

r = requests.get(f"{BASE_URL}/api/v1/broker/status")
if r.status_code == 200:
    data = r.json()
    api_calls_after = data.get('api_calls_today', 0)
    print(f"Final API Calls: {api_calls_after}")
    
    if api_calls_after > api_calls_before:
        print(f"✅ API ACTIVITY DETECTED: {api_calls_after - api_calls_before} new calls")
        print("OrderManager is successfully reaching Zerodha!")
    else:
        print("⚠️  No new API calls detected")
        print("OrderManager may not be processing signals")

print("\nTest completed") 
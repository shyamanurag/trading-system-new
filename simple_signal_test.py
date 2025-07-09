import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

print("🚀 SIGNAL & ORDER PROCESSING QUICK TEST")
print("=" * 50)

# Test 1: Broker Status  
print("\n1️⃣ BROKER STATUS")
r = requests.get(f"{BASE_URL}/api/v1/broker/status")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Broker: {data.get('broker')}")
    print(f"   Connected: {data.get('status')}")
    print(f"   API Calls Today: {data.get('api_calls_today', 0)}")
    print(f"   Market Data Connected: {data.get('market_data_connected')}")
    print(f"   Order Management Connected: {data.get('order_management_connected')}")

# Test 2: Debug Orchestrator
print("\n2️⃣ ORCHESTRATOR DEBUG")
r = requests.get(f"{BASE_URL}/api/v1/debug/orchestrator")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Orchestrator Data: {json.dumps(data, indent=4)}")

# Test 3: System Ready
print("\n3️⃣ SYSTEM READY CHECK")
r = requests.get(f"{BASE_URL}/api/v1/debug/system-ready")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   System Ready: {data}")

# Test 4: Autonomous Status (may fail with 500)
print("\n4️⃣ AUTONOMOUS STATUS")
r = requests.get(f"{BASE_URL}/api/v1/autonomous/status")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Autonomous Data: {json.dumps(data, indent=4)}")
else:
    print(f"   Error: {r.text[:100]}")

# Test 5: Try Start Trading
print("\n5️⃣ TRY START TRADING")
r = requests.post(f"{BASE_URL}/api/v1/autonomous/start")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Start Response: {data}")
else:
    print(f"   Error: {r.text[:100]}")

print("\n" + "=" * 50)
print("TEST COMPLETED") 
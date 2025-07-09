#!/usr/bin/env python3
import requests
import time

print("⏰ Waiting 10 seconds for system to process...")
time.sleep(10)

# Check trading status
r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
data = r.json()
total_trades = data['data']['total_trades']

# Check broker API calls
r2 = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
broker_data = r2.json()
api_calls = broker_data.get('api_calls_today', 0)

print(f"Total Trades: {total_trades}")
print(f"API Calls Today: {api_calls}")

if total_trades > 0:
    print("✅ SUCCESS: Trades are working!")
elif api_calls > 0:
    print("🔄 PROGRESS: API calls made but no completed trades yet")
else:
    print("❌ ISSUE: Still no trades or API calls") 
import requests
import time

print("⏰ Waiting 10 seconds for system to process...")
time.sleep(10)

# Check trading status
r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
data = r.json()
total_trades = data['data']['total_trades']

# Check broker API calls
r2 = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
broker_data = r2.json()
api_calls = broker_data.get('api_calls_today', 0)

print(f"Total Trades: {total_trades}")
print(f"API Calls Today: {api_calls}")

if total_trades > 0:
    print("✅ SUCCESS: Trades are working!")
elif api_calls > 0:
    print("🔄 PROGRESS: API calls made but no completed trades yet")
else:
    print("❌ ISSUE: Still no trades or API calls") 
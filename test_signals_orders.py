import requests
import time

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

print('🚀 SIGNAL & ORDER PROCESSING TEST')
print('=' * 40)

# Test 1: System Status
print('\n1. SYSTEM STATUS')
try:
    r = requests.get(f'{BASE_URL}/api/v1/autonomous/status')
    print(f'   Status Code: {r.status_code}')
    if r.status_code == 200:
        data = r.json()['data']
        print(f'   Active: {data.get("is_active", False)}')
        print(f'   Strategies: {data.get("active_strategies_count", 0)}')
        print(f'   Total Trades: {data.get("total_trades", 0)}')
    else:
        print(f'   Error: {r.text[:100]}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 2: Broker Status
print('\n2. BROKER STATUS')
try:
    r = requests.get(f'{BASE_URL}/api/v1/broker/status')
    print(f'   Status Code: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'   Broker: {data.get("broker", "Unknown")}')
        print(f'   Connected: {data.get("status", "Unknown")}')
        print(f'   API Calls: {data.get("api_calls_today", 0)}')
    else:
        print(f'   Error: {r.text[:100]}')
except Exception as e:
    print(f'   Exception: {e}')

# Test 3: Start Trading
print('\n3. START TRADING TEST')
try:
    print('   🚀 Starting autonomous trading...')
    r = requests.post(f'{BASE_URL}/api/v1/autonomous/start')
    print(f'   Start Status: {r.status_code}')
    
    if r.status_code == 200:
        print('   ✅ Started successfully')
        
        # Quick monitor
        print('   ⏰ Monitoring for 10 seconds...')
        time.sleep(10)
        
        # Check results
        status_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status')
        broker_r = requests.get(f'{BASE_URL}/api/v1/broker/status')
        
        if status_r.status_code == 200:
            trades = status_r.json()['data'].get('total_trades', 0)
            print(f'   📊 Total Trades: {trades}')
        
        if broker_r.status_code == 200:
            api_calls = broker_r.json().get('api_calls_today', 0)
            print(f'   📊 API Calls: {api_calls}')
    else:
        print(f'   ❌ Start failed: {r.text[:100]}')
        
except Exception as e:
    print(f'   Exception: {e}')

print('\n' + '=' * 40)
print('TEST COMPLETED') 
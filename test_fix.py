#!/usr/bin/env python3

import requests

def test_deployment_fix():
    print('🔄 Testing deployment fix...')
    print('=' * 50)
    
    # Test 1: Autonomous trading status (500 error fix)
    print('TEST 1: Autonomous Trading Status (500 Error Fix)')
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            print(f'✅ SUCCESS! Autonomous trading API working: {response.status_code}')
            print(f'   - Is Active: {trading_data.get("is_active")}')
            print(f'   - System Ready: {trading_data.get("system_ready")}')
            print(f'   - Active Strategies: {len(trading_data.get("active_strategies", []))}')
            print(f'   - Total Trades: {trading_data.get("total_trades")}')
            print(f'🎉 500 ERROR FIXED!')
        else:
            print(f'❌ Still getting {response.status_code} error')
            print(f'   Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Autonomous error: {e}')
    
    print()
    
    # Test 2: Dashboard summary API (404 error check)
    print('TEST 2: Dashboard Summary API (404 Error Check)')
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/summary', timeout=10)
        if response.status_code == 200:
            print(f'✅ Dashboard summary API working: {response.status_code}')
            print('💡 Frontend should use /dashboard/summary NOT /dashboard/dashboard/summary')
        else:
            print(f'❌ Dashboard summary: {response.status_code}')
    except Exception as e:
        print(f'❌ Dashboard error: {e}')
    
    print()
    
    # Test 3: Autonomous trading start
    print('TEST 3: Autonomous Trading Start')
    try:
        response = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Start endpoint working: {response.status_code}')
            print(f'   Success: {result.get("success")}')
            print(f'   Message: {result.get("message")}')
        else:
            print(f'❌ Start endpoint: {response.status_code}')
    except Exception as e:
        print(f'❌ Start error: {e}')
    
    print()
    print('🎯 SUMMARY:')
    print('1. If autonomous/status works: 500 error is FIXED')
    print('2. If dashboard/summary works: 404 error is frontend route issue')
    print('3. If autonomous/start works: Button should work')

if __name__ == "__main__":
    test_deployment_fix() 
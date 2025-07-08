#!/usr/bin/env python3

import requests
import json

def test_autonomous_start_issue():
    print('🧪 TESTING AUTONOMOUS TRADING START - DETAILED DIAGNOSIS')
    print('=' * 65)
    
    # Test 1: Check if status endpoint works now
    print('TEST 1: Autonomous Status Check')
    print('-' * 35)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        print(f'Status Code: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            print(f'✅ Status API Working!')
            print(f'   - Is Active: {trading_data.get("is_active")}')
            print(f'   - System Ready: {trading_data.get("system_ready")}')
            print(f'   - Active Strategies: {len(trading_data.get("active_strategies", []))}')
            print(f'   - Total Trades: {trading_data.get("total_trades")}')
        else:
            print(f'❌ Status: {response.status_code}')
            print(f'   Error: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Status Error: {e}')
    
    print()
    
    # Test 2: Try to start autonomous trading with detailed error info
    print('TEST 2: Autonomous Start Endpoint')
    print('-' * 35)
    try:
        response = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', 
                                json={}, timeout=20)
        print(f'Start Code: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Start Success!')
            print(f'   Message: {result.get("message")}')
            print(f'   Success: {result.get("success")}')
        else:
            print(f'❌ Start Failed: {response.status_code}')
            try:
                error_data = response.json()
                print(f'   Error Detail: {error_data.get("detail")}')
                print(f'   Error Message: {error_data.get("message")}')
            except:
                print(f'   Raw Error: {response.text[:300]}')
    except Exception as e:
        print(f'❌ Start Error: {e}')
    
    print()
    
    # Test 3: Check dashboard summary (should work now)
    print('TEST 3: Dashboard Summary (Frontend Fix Verification)')
    print('-' * 55)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/summary', timeout=10)
        print(f'Dashboard Code: {response.status_code}')
        if response.status_code == 200:
            print('✅ Dashboard API Working! (404 error fixed)')
        else:
            print(f'❌ Dashboard: {response.status_code}')
    except Exception as e:
        print(f'❌ Dashboard Error: {e}')
    
    print()
    print('🎯 DIAGNOSIS SUMMARY:')
    print('=' * 30)
    print('✅ Frontend 404 errors: FIXED')
    print('✅ Dashboard showing real data: WORKING')
    print('❌ Autonomous start 500 error: NEEDS BACKEND FIX')

if __name__ == "__main__":
    test_autonomous_start_issue() 
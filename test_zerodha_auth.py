#!/usr/bin/env python3
"""
Test script to check Zerodha authentication status and token storage
"""
import requests
import json
from datetime import datetime

def test_zerodha_auth():
    print('🔍 Testing Zerodha Authentication Status')
    print('=' * 50)
    
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    # Test 1: Check auth status
    print('📋 TEST 1: Auth Status')
    try:
        response = requests.get(f'{base_url}/auth/zerodha/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print('✅ Auth Status Response:')
            print(f'  Authenticated: {data.get("authenticated", "unknown")}')
            print(f'  User ID: {data.get("user_id", "unknown")}')
            print(f'  Message: {data.get("message", "")}')
        else:
            print(f'❌ Auth status error: {response.status_code}')
    except Exception as e:
        print(f'❌ Auth status exception: {e}')
    
    print()
    
    # Test 2: Check connection test
    print('📋 TEST 2: Connection Test')
    try:
        response = requests.get(f'{base_url}/auth/zerodha/test-connection', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print('✅ Connection Test Response:')
            print(f'  Success: {data.get("success", "unknown")}')
            print(f'  Message: {data.get("message", "")}')
        else:
            print(f'❌ Connection test error: {response.status_code}')
    except Exception as e:
        print(f'❌ Connection test exception: {e}')
    
    print()
    
    # Test 3: Check current time vs token expiry
    print('📋 TEST 3: Time Analysis')
    now = datetime.now()
    print(f'Current time: {now}')
    print(f'Market hours: 9:15 AM - 3:30 PM')
    print(f'Token expires: 6:00 AM daily')
    
    if now.hour >= 6 and now.hour < 18:
        print('✅ Within token validity period')
    else:
        print('❌ Outside token validity period - may need refresh')
    
    print()
    
    # Test 4: Force orchestrator restart
    print('📋 TEST 4: Force Orchestrator Restart')
    try:
        response = requests.post(f'{base_url}/api/v1/orchestrator/force-start', timeout=30)
        if response.status_code == 200:
            print('✅ Orchestrator restarted successfully')
        else:
            print(f'❌ Orchestrator restart failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Orchestrator restart exception: {e}')
    
    print()
    
    # Test 5: Check final status
    print('📋 TEST 5: Final Status Check')
    try:
        response = requests.get(f'{base_url}/api/v1/zerodha/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get('user_id', 'unknown')
            print(f'Final Zerodha User ID: {user_id}')
            if user_id == 'DEMO_USER':
                print('❌ STILL USING DEMO_USER - Token not retrieved')
            else:
                print('✅ Using real user ID - Token retrieved successfully')
        else:
            print(f'❌ Final status error: {response.status_code}')
    except Exception as e:
        print(f'❌ Final status exception: {e}')

if __name__ == "__main__":
    test_zerodha_auth() 
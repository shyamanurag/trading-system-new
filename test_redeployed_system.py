#!/usr/bin/env python3
"""
Test redeployed system to diagnose 500 error
"""

import requests
import json

def test_redeployed_system():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    print('🔍 DIAGNOSING REDEPLOYED SYSTEM')
    print('=' * 50)

    # Test autonomous status
    print('1️⃣ Autonomous Status:')
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous/status', timeout=10)
        print(f'   Status Code: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            is_active = data.get('data', {}).get('is_active', False)
            pnl = data.get('data', {}).get('daily_pnl', 0)
            print(f'   Active: {is_active} | P&L: ₹{pnl}')
        else:
            print(f'   Error: {response.text[:200]}')
    except Exception as e:
        print(f'   Exception: {e}')

    print()

    # Test TrueData
    print('2️⃣ TrueData Status:')
    try:
        response = requests.get(f'{base_url}/api/v1/truedata/status', timeout=10)
        print(f'   Status Code: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            connected = data.get('data', {}).get('connected', False)
            print(f'   Connected: {connected}')
        else:
            print(f'   Error: {response.text[:200]}')
    except Exception as e:
        print(f'   Exception: {e}')

    print()

    # Test Zerodha auth
    print('3️⃣ Zerodha Authentication:')
    try:
        response = requests.get(f'{base_url}/auth/zerodha/status', timeout=10)
        print(f'   Status Code: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            authenticated = data.get('authenticated', False)
            print(f'   Authenticated: {authenticated}')
        else:
            print(f'   Error: {response.text[:200]}')
    except Exception as e:
        print(f'   Exception: {e}')

    print()

    # Attempt to start trading and get detailed error
    print('4️⃣ Start Trading (Detailed Error):')
    try:
        response = requests.post(f'{base_url}/api/v1/autonomous/start', timeout=15)
        print(f'   Status Code: {response.status_code}')
        print(f'   Response Text: {response.text}')
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                error_detail = data.get('detail', 'No detail provided')
                print(f'   Error Detail: {error_detail}')
            except:
                print('   Could not parse JSON response')
    except Exception as e:
        print(f'   Exception: {e}')

    print()
    print('🎯 SUMMARY: Check the detailed error above to understand the 500 error')

if __name__ == "__main__":
    test_redeployed_system() 
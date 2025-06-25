#!/usr/bin/env python3
"""
Fix Market Data - Connect TrueData and Subscribe to Indices
"""

import requests
import json
import time

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def fix_market_data():
    """Connect TrueData and subscribe to indices"""
    print('🔧 FIXING MARKET DATA ISSUE')
    print('=' * 40)
    
    # Step 1: Connect TrueData
    print('\n1️⃣ Connecting TrueData...')
    try:
        connect_data = {
            'username': 'tdwsp697',
            'password': 'shyam@697'
        }
        
        response = requests.post(
            f'{BASE_URL}/api/v1/truedata/truedata/connect',
            json=connect_data,
            timeout=20
        )
        
        print(f'   Connect Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            message = data.get('message', 'N/A')
            print(f'   Success: {success}')
            print(f'   Message: {message}')
            
            if success:
                print('   ✅ TrueData connected successfully!')
            else:
                print(f'   ❌ Connection failed: {message}')
                return False
        else:
            print(f'   ❌ Connect request failed: {response.status_code}')
            print(f'   Response: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'   ❌ Error connecting TrueData: {e}')
        return False
    
    # Step 2: Wait a moment for connection to establish
    print('\n⏳ Waiting for connection to establish...')
    time.sleep(3)
    
    # Step 3: Subscribe to indices
    print('\n2️⃣ Subscribing to indices...')
    try:
        symbols = ['NIFTY-I', 'BANKNIFTY-I']  # Correct format for indices
        
        for symbol in symbols:
            subscribe_data = {'symbol': symbol}
            
            response = requests.post(
                f'{BASE_URL}/api/v1/truedata/truedata/subscribe',
                json=subscribe_data,
                timeout=15
            )
            
            print(f'   {symbol}: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                message = data.get('message', 'N/A')
                print(f'     Success: {success}, Message: {message}')
            else:
                print(f'     Failed: {response.text[:100]}')
                
    except Exception as e:
        print(f'   ❌ Error subscribing to symbols: {e}')
    
    # Step 4: Check status
    print('\n3️⃣ Checking final status...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/truedata/truedata/status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            symbols_count = data.get('symbols_available', 0)
            live_symbols = data.get('live_data_symbols', [])
            
            print(f'   Connected: {connected}')
            print(f'   Symbols Available: {symbols_count}')
            print(f'   Live Symbols: {live_symbols}')
            
            if connected and symbols_count > 0:
                print('   ✅ Market data should now be flowing!')
                return True
            else:
                print('   ❌ Still not getting data')
                return False
        else:
            print(f'   ❌ Status check failed: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'   ❌ Error checking status: {e}')
        return False

if __name__ == "__main__":
    success = fix_market_data()
    
    if success:
        print('\n🎉 MARKET DATA FIXED!')
        print('   → NIFTY and BANK NIFTY should now show live values')
        print('   → Refresh your dashboard to see the updates')
    else:
        print('\n❌ MARKET DATA STILL NOT WORKING')
        print('   → Check TrueData credentials')
        print('   → Verify symbol formats')
        print('   → Check network connectivity') 
#!/usr/bin/env python3
"""
Subscribe to NIFTY and BANK NIFTY Indices
"""

import requests
import json
import time

def subscribe_indices():
    """Subscribe to NIFTY and BANK NIFTY indices"""
    print('📊 SUBSCRIBING TO MARKET INDICES')
    print('=' * 40)
    
    # Subscribe to indices
    symbols = ['NIFTY-I', 'BANKNIFTY-I']
    
    for symbol in symbols:
        print(f'\n📈 Subscribing to {symbol}...')
        try:
            subscribe_data = {'symbol': symbol}
            
            response = requests.post(
                'https://algoauto-9gx56.ondigitalocean.app/api/v1/truedata/truedata/subscribe',
                json=subscribe_data,
                timeout=15
            )
            
            print(f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                message = data.get('message', 'N/A')
                print(f'   Success: {success}')
                print(f'   Message: {message}')
                
                if success:
                    print(f'   ✅ {symbol} subscribed successfully!')
                else:
                    print(f'   ❌ {symbol} subscription failed: {message}')
            else:
                print(f'   ❌ Request failed: {response.text[:100]}')
                
        except Exception as e:
            print(f'   ❌ Error subscribing to {symbol}: {e}')
    
    print('\n⏳ Waiting for data to flow...')
    time.sleep(5)
    
    # Check final status
    print('\n📊 Checking TrueData status...')
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/truedata/truedata/status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            symbols_count = data.get('symbols_available', 0)
            live_symbols = data.get('live_data_symbols', [])
            
            print(f'   Connected: {connected}')
            print(f'   Symbols Available: {symbols_count}')
            print(f'   Live Symbols: {live_symbols}')
            
            if connected and symbols_count > 0:
                print('\n✅ TrueData is connected with live data!')
                
                # Check if NIFTY and BANK NIFTY are in the list
                nifty_available = 'NIFTY-I' in live_symbols
                banknifty_available = 'BANKNIFTY-I' in live_symbols
                
                print(f'   NIFTY-I available: {nifty_available}')
                print(f'   BANKNIFTY-I available: {banknifty_available}')
                
                return True
            else:
                print('\n❌ TrueData not properly connected or no data')
                return False
        else:
            print(f'   ❌ Status check failed: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'   ❌ Status check error: {e}')
        return False

if __name__ == "__main__":
    success = subscribe_indices()
    
    if success:
        print('\n🎉 MARKET INDICES SUBSCRIBED!')
        print('   → NIFTY and BANK NIFTY should now show live values')
        print('   → Refresh your dashboard to see real prices')
        print('   → Market data is now flowing from TrueData')
    else:
        print('\n❌ SUBSCRIPTION FAILED')
        print('   → Check TrueData connection')
        print('   → Verify symbol formats')
        print('   → Contact support if issue persists') 
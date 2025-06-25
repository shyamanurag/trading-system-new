#!/usr/bin/env python3
"""
Check Market Data Flow Issue
"""

import requests
import json

def check_market_data():
    """Check why NIFTY and BANK NIFTY show 0 values"""
    print('🔍 DIAGNOSING MARKET DATA ISSUE')
    print('=' * 50)
    
    # 1. Check TrueData connection status
    print('\n1️⃣ CHECKING TRUEDATA CONNECTION:')
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/truedata/truedata/status', timeout=10)
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            symbols_count = data.get('symbols_available', 0)
            live_symbols = data.get('live_data_symbols', [])
            
            print(f'   Connected: {connected}')
            print(f'   Symbols Available: {symbols_count}')
            print(f'   Live Data Symbols: {live_symbols}')
            
            if not connected:
                print('   ❌ TrueData not connected - need to connect first')
            elif symbols_count == 0:
                print('   ❌ No symbols subscribed - need to subscribe to NIFTY-I, BANKNIFTY-I')
            else:
                print('   ✅ TrueData connection looks good')
        else:
            print(f'   ❌ TrueData status check failed: {response.status_code}')
            
    except Exception as e:
        print(f'   ❌ Error checking TrueData: {e}')
    
    # 2. Check market indices endpoint
    print('\n2️⃣ CHECKING MARKET INDICES ENDPOINT:')
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/market/indices', timeout=10)
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'   Response keys: {list(data.keys())}')
            
            # Check NIFTY data
            if 'NIFTY' in data:
                nifty = data['NIFTY']
                print(f'   NIFTY - LTP: {nifty.get("ltp", "N/A")}, Volume: {nifty.get("volume", "N/A")}')
            
            # Check BANK NIFTY data  
            if 'BANKNIFTY' in data:
                banknifty = data['BANKNIFTY']
                print(f'   BANKNIFTY - LTP: {banknifty.get("ltp", "N/A")}, Volume: {banknifty.get("volume", "N/A")}')
                
            # Print first 300 chars of response
            print(f'   Sample data: {str(data)[:300]}...')
        else:
            print(f'   ❌ Market indices failed: {response.status_code}')
            
    except Exception as e:
        print(f'   ❌ Error checking market indices: {e}')
    
    # 3. Check if TrueData needs to be connected
    print('\n3️⃣ SOLUTION RECOMMENDATIONS:')
    print('   If TrueData is not connected:')
    print('   → Visit: /api/v1/truedata/truedata/connect')
    print('   → Use credentials: tdwsp697 / shyam@697')
    print('')
    print('   If connected but no symbols:')
    print('   → Subscribe to NIFTY-I and BANKNIFTY-I')
    print('   → Check symbol format (might need -I suffix for indices)')

if __name__ == "__main__":
    check_market_data() 
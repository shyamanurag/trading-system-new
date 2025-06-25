#!/usr/bin/env python3
"""
Connect TrueData and Fix Market Data
"""

import sys
import os
import time

# Add current directory to path
sys.path.append('.')

def connect_truedata():
    """Connect TrueData and get live market data"""
    print('🔌 CONNECTING TRUEDATA FOR MARKET DATA')
    print('=' * 50)
    
    try:
        # Import TrueData client
        from data.truedata_client import TrueDataSingletonClient, live_market_data, truedata_connection_status
        
        # Check current status
        print('\n📊 Current Status:')
        connected = truedata_connection_status.get('connected', False)
        username = truedata_connection_status.get('username', 'N/A')
        error = truedata_connection_status.get('error', 'None')
        data_count = len(live_market_data)
        
        print(f'   Connected: {connected}')
        print(f'   Username: {username}')
        print(f'   Error: {error}')
        print(f'   Live data symbols: {data_count}')
        
        if data_count > 0:
            symbols = list(live_market_data.keys())[:5]
            print(f'   Sample symbols: {symbols}')
            
            # Check if we have NIFTY and BANK NIFTY data
            nifty_data = live_market_data.get('NIFTY-I', {})
            banknifty_data = live_market_data.get('BANKNIFTY-I', {})
            
            print(f'   NIFTY-I data: {bool(nifty_data)}')
            print(f'   BANKNIFTY-I data: {bool(banknifty_data)}')
            
            if nifty_data:
                ltp = nifty_data.get('ltp', 0)
                print(f'   NIFTY LTP: {ltp}')
            if banknifty_data:
                ltp = banknifty_data.get('ltp', 0)
                print(f'   BANKNIFTY LTP: {ltp}')
        
        # If not connected, try to connect
        if not connected:
            print('\n🔌 Attempting to connect TrueData...')
            client = TrueDataSingletonClient()
            success = client.connect()
            
            print(f'   Connection result: {success}')
            
            if success:
                print('   ✅ Connected! Waiting for data...')
                time.sleep(5)
                
                # Check data again
                new_data_count = len(live_market_data)
                print(f'   Live data symbols after connection: {new_data_count}')
                
                if new_data_count > 0:
                    print('   ✅ Market data is now flowing!')
                    
                    # Check specific symbols
                    nifty_data = live_market_data.get('NIFTY-I', {})
                    banknifty_data = live_market_data.get('BANKNIFTY-I', {})
                    
                    if nifty_data:
                        ltp = nifty_data.get('ltp', 0)
                        print(f'   NIFTY-I LTP: {ltp}')
                    if banknifty_data:
                        ltp = banknifty_data.get('ltp', 0)
                        print(f'   BANKNIFTY-I LTP: {ltp}')
                        
                    return True
                else:
                    print('   ❌ Connected but no data received')
                    return False
            else:
                print('   ❌ Connection failed')
                return False
        else:
            print('\n✅ Already connected!')
            return True
            
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = connect_truedata()
    
    if success:
        print('\n🎉 TRUEDATA CONNECTED!')
        print('   → Market data should now show live values')
        print('   → NIFTY and BANK NIFTY should display real prices')
        print('   → Refresh your dashboard to see updates')
    else:
        print('\n❌ TRUEDATA CONNECTION FAILED')
        print('   → Check credentials: tdwsp697 / shyam@697')
        print('   → Verify account subscription status')
        print('   → Contact TrueData support if needed') 
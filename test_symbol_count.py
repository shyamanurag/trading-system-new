#!/usr/bin/env python3
"""
Test if TrueData client is using all configured symbols (6 instead of 4)
"""

import requests
import json
import time

def test_symbol_count():
    """Test if TrueData is using the complete DEFAULT_SYMBOLS configuration"""
    print('🔍 TESTING TRUEDATA SYMBOL CONFIGURATION')
    print('=' * 50)
    
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    # Get current status
    print('\n📊 Current TrueData Status:')
    try:
        resp = requests.get(f'{base_url}/api/v1/truedata/truedata/status', timeout=10)
        if resp.status_code == 200:
            status = resp.json()
            connected = status.get('connected', False)
            symbols_active = status.get('symbols_active', 0)
            last_error = status.get('last_error', 'None')
            
            print(f'   Connected: {connected}')
            print(f'   Symbols Active: {symbols_active}')
            print(f'   Last Error: {last_error}')
            
            # Check expected vs actual
            expected_symbols = 6  # From DEFAULT_SYMBOLS configuration
            
            if symbols_active == expected_symbols:
                print(f'   ✅ CORRECT: {symbols_active}/{expected_symbols} symbols active')
                return True
            else:
                print(f'   ❌ ISSUE: Only {symbols_active}/{expected_symbols} symbols active')
                print(f'   🔄 Need to force reconnection with new configuration...')
                
                # Try disconnect and reconnect
                print('\n🔄 Forcing reconnection...')
                
                # Disconnect first
                try:
                    resp = requests.post(f'{base_url}/api/v1/truedata/truedata/disconnect', timeout=10)
                    print(f'   Disconnect: HTTP {resp.status_code}')
                except Exception as e:
                    print(f'   Disconnect error: {e}')
                
                # Wait
                print('   Waiting 5 seconds...')
                time.sleep(5)
                
                # Reconnect
                try:
                    resp = requests.post(f'{base_url}/api/v1/truedata/truedata/reconnect', timeout=15)
                    result = resp.json()
                    success = result.get('success', False)
                    message = result.get('message', 'Unknown')
                    
                    print(f'   Reconnect: {success}')
                    if not success:
                        print(f'   Message: {message}')
                        
                except Exception as e:
                    print(f'   Reconnect error: {e}')
                
                # Check status again
                print('\n📊 Status After Reconnection:')
                time.sleep(3)
                
                try:
                    resp = requests.get(f'{base_url}/api/v1/truedata/truedata/status', timeout=10)
                    if resp.status_code == 200:
                        status = resp.json()
                        connected = status.get('connected', False)
                        symbols_active = status.get('symbols_active', 0)
                        
                        print(f'   Connected: {connected}')
                        print(f'   Symbols Active: {symbols_active}')
                        
                        if symbols_active == expected_symbols:
                            print(f'   ✅ SUCCESS: Now {symbols_active}/{expected_symbols} symbols!')
                            return True
                        else:
                            print(f'   ❌ STILL ISSUE: Only {symbols_active}/{expected_symbols} symbols')
                            return False
                    
                except Exception as e:
                    print(f'   Status check error: {e}')
                    return False
        else:
            print(f'   ❌ Status request failed: HTTP {resp.status_code}')
            return False
            
    except Exception as e:
        print(f'   ❌ Error getting status: {e}')
        return False

if __name__ == "__main__":
    success = test_symbol_count()
    
    if success:
        print('\n🎉 SYMBOL CONFIGURATION TEST PASSED!')
        print('   → All 6 DEFAULT_SYMBOLS are now active')
        print('   → NIFTY-I, BANKNIFTY-I, RELIANCE, TCS, HDFC, INFY')
        print('   → Backend has complete market data for trading')
    else:
        print('\n❌ SYMBOL CONFIGURATION ISSUE')
        print('   → Only 4 symbols active instead of 6')
        print('   → May need manual intervention or deployment restart') 
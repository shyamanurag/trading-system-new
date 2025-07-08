#!/usr/bin/env python3

import requests

def test_autonomous_after_simple_fix():
    print('🧪 TESTING AUTONOMOUS TRADING - POST DEPLOYMENT')
    print('=' * 60)
    print('✅ TrueData connected (user confirmed)')
    print('✅ Zerodha daily auth completed')
    print('✅ Simple fix deployed (direct cache access)')
    print()

    # Test 1: Check autonomous trading status
    print('TEST 1: Autonomous Trading Status')
    print('-' * 40)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f'✅ API Response: {response.status_code}')
            print(f'  - Is Active: {trading_data.get("is_active")}')
            print(f'  - System Ready: {trading_data.get("system_ready")}')
            print(f'  - Active Strategies: {len(trading_data.get("active_strategies", []))}')
            print(f'  - Total Trades: {trading_data.get("total_trades")}')
            print(f'  - Market Status: {trading_data.get("market_status")}')
            
            risk_status = trading_data.get("risk_status", {})
            print(f'  - Risk Status: {risk_status.get("status", "Unknown")}')
            
        else:
            print(f'❌ Autonomous status failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Autonomous status error: {e}')

    print()

    # Test 2: Check market data availability (our simple fix target)
    print('TEST 2: Market Data Availability (Simple Fix Target)')
    print('-' * 50)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data/live', timeout=10)
        if response.status_code == 200:
            data = response.json()
            live_data = data.get('data', {})
            symbols = live_data.get('symbols', [])
            
            print(f'✅ Live Data API: {response.status_code}')
            print(f'  - Symbols Available: {len(symbols)}')
            
            if len(symbols) > 0:
                print('  🎉 SUCCESS! Market data now available to autonomous system!')
                # Show sample symbols
                sample_symbols = symbols[:3]
                print(f'  - Sample symbols: {sample_symbols}')
            else:
                print('  ❌ No symbols in live data - simple fix may need more time')
        else:
            print(f'❌ Market data API failed: {response.status_code}')
            if response.status_code == 503:
                print('  💡 This was the original problem - TrueData connection required')
                print('  🔧 Our simple fix should solve this!')
    except Exception as e:
        print(f'❌ Market data error: {e}')

    print()

    # Test 3: Try to start autonomous trading
    print('TEST 3: Autonomous Trading Start Button Fix')
    print('-' * 45)
    try:
        # Check if there's a start endpoint
        response = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Start command: {response.status_code}')
            print(f'  - Success: {result.get("success")}')
            print(f'  - Message: {result.get("message")}')
            
            if result.get("success"):
                print('  🎉 Autonomous trading started successfully!')
            else:
                print(f'  ❌ Start failed: {result.get("message")}')
                
        elif response.status_code == 404:
            print(f'❌ Start endpoint not found: {response.status_code}')
            print('  💡 This explains why the button doesnt work!')
            print('  🔧 Need to check autonomous trading router deployment')
        else:
            print(f'❌ Start command failed: {response.status_code}')
            try:
                error_data = response.json()
                print(f'  Error: {error_data.get("detail", "Unknown error")}')
            except:
                print(f'  Raw error: {response.text[:100]}')
                
    except Exception as e:
        print(f'❌ Start command error: {e}')

    print()
    print('🎯 DIAGNOSIS SUMMARY:')
    print('=' * 30)
    print('1. Simple fix for market data: Check if live data API works')
    print('2. Button issue: Check if start endpoint exists')  
    print('3. If both work: System should be ready for autonomous trading')

if __name__ == "__main__":
    test_autonomous_after_simple_fix() 
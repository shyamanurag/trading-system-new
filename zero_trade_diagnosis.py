#!/usr/bin/env python3

import requests
import json

def diagnose_zero_trades():
    print('🚨 ZERO TRADE DIAGNOSIS - COMPREHENSIVE ANALYSIS')
    print('=' * 60)
    print('🎯 Tracing the complete trade execution pipeline...')
    print()
    
    # STEP 1: Check autonomous trading system status
    print('STEP 1: Autonomous Trading System Status')
    print('-' * 45)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            is_active = trading_data.get('is_active')
            system_ready = trading_data.get('system_ready')
            active_strategies = trading_data.get('active_strategies', [])
            total_trades = trading_data.get('total_trades', 0)
            market_data_available = trading_data.get('market_data_available')
            
            print(f'✅ System Active: {is_active}')
            print(f'✅ System Ready: {system_ready}')
            print(f'📊 Active Strategies: {len(active_strategies)}')
            print(f'📈 Total Trades: {total_trades}')
            print(f'🚨 Market Data Available: {market_data_available}')
            
            if not market_data_available:
                print('🚨 CRITICAL: No market data = No signals = Zero trades!')
            
        else:
            print(f'❌ Autonomous status failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Error: {e}')
    
    print()
    
    # STEP 2: Check market data API directly
    print('STEP 2: Market Data API Direct Check')
    print('-' * 40)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data/live', timeout=10)
        if response.status_code == 200:
            data = response.json()
            live_data = data.get('data', {})
            symbols = live_data.get('symbols', [])
            
            print(f'✅ Market Data API: {response.status_code}')
            print(f'📊 Available Symbols: {len(symbols)}')
            
            if len(symbols) > 0:
                print(f'📈 Sample symbols: {symbols[:5]}')
                print('✅ Market data is available!')
            else:
                print('🚨 CRITICAL: Market data API returns empty symbols!')
                
        else:
            print(f'❌ Market Data API failed: {response.status_code}')
            if response.status_code == 503:
                print('💡 503 = Service unavailable - TrueData connection issue')
    except Exception as e:
        print(f'❌ Market Data Error: {e}')
    
    print()
    
    # STEP 3: Check strategy performance
    print('STEP 3: Strategy Signal Generation Check')
    print('-' * 42)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/strategies', timeout=10)
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('data', {})
            
            print(f'✅ Strategy API: {response.status_code}')
            print(f'📊 Total Strategies: {len(strategies)}')
            
            for name, info in strategies.items():
                active = info.get('active', False)
                last_signal = info.get('last_signal', 'Never')
                print(f'   - {name}: {"🟢 Active" if active else "🔴 Inactive"} | Last Signal: {last_signal}')
                
        else:
            print(f'❌ Strategy API failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Strategy Error: {e}')
    
    print()
    
    # STEP 4: Check positions and orders
    print('STEP 4: Positions and Orders Check')
    print('-' * 35)
    try:
        # Check positions
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/positions', timeout=10)
        if response.status_code == 200:
            data = response.json()
            positions = data.get('data', [])
            print(f'📊 Current Positions: {len(positions)}')
        else:
            print(f'❌ Positions API: {response.status_code}')
            
        # Check orders
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/orders', timeout=10)
        if response.status_code == 200:
            print(f'📊 Recent Orders: Available')
        else:
            print(f'❌ Orders API: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Positions/Orders Error: {e}')
    
    print()
    
    # STEP 5: Test Zerodha connectivity after re-auth
    print('STEP 5: Zerodha Authentication Status')
    print('-' * 38)
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            authenticated = data.get('authenticated', False)
            trading_ready = data.get('trading_ready', False)
            print(f'✅ Zerodha Auth Status: {response.status_code}')
            print(f'🔐 Authenticated: {authenticated}')
            print(f'📈 Trading Ready: {trading_ready}')
        else:
            print(f'❌ Zerodha Auth failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Zerodha Auth Error: {e}')
    
    print()
    
    # DIAGNOSIS SUMMARY
    print('🎯 ZERO TRADE DIAGNOSIS SUMMARY')
    print('=' * 40)
    print('ROOT CAUSE ANALYSIS:')
    print('1. If Market Data = None → Strategies get no data → No signals → Zero trades')
    print('2. If Strategies inactive → No signals generated → Zero trades')  
    print('3. If Zerodha not authenticated → Signals generated but no orders → Zero trades')
    print('4. If Trade engine broken → Signals lost in processing → Zero trades')
    print()
    print('💡 LIKELY CAUSE: Market data not reaching strategies due to TrueData connection')
    print('🔧 SOLUTION: Fix TrueData integration to autonomous trading pipeline')

if __name__ == "__main__":
    diagnose_zero_trades() 
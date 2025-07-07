#!/usr/bin/env python3

import requests
import json
import time

def debug_strategy_activity():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    print('🔍 DEBUGGING STRATEGY ACTIVITY AND SIGNAL FLOW:')
    print('=' * 60)
    
    # Step 1: Check strategies
    print('STEP 1: Check loaded strategies...')
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous/strategies', timeout=10)
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('data', {}).get('strategies', [])
            
            print(f'Total strategies loaded: {len(strategies)}')
            for i, strategy in enumerate(strategies, 1):
                name = strategy.get('name', 'Unknown')
                status = strategy.get('status', 'Unknown')
                print(f'  {i}. {name} - Status: {status}')
            
            if len(strategies) > 0:
                print('✅ Strategies are loaded!')
            else:
                print('❌ NO STRATEGIES LOADED!')
                
        else:
            print(f'❌ Strategy check failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error checking strategies: {e}')
    
    # Step 2: Check for orders (evidence of signal processing)
    print('\\nSTEP 2: Check for orders (evidence of trades)...')
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous/orders', timeout=10)
        if response.status_code == 200:
            data = response.json()
            orders = data.get('data', {}).get('orders', [])
            
            print(f'Total orders today: {len(orders)}')
            if len(orders) > 0:
                print('✅ Orders found - signals are being processed!')
                for order in orders[:5]:  # Show first 5 orders
                    print(f'  - {order.get("symbol", "Unknown")} {order.get("transaction_type", "Unknown")} Qty: {order.get("quantity", 0)}')
            else:
                print('❌ NO ORDERS FOUND - signals not reaching trade engine!')
                
        else:
            print(f'❌ Order check failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error checking orders: {e}')
    
    # Step 3: Check market data flow
    print('\\nSTEP 3: Check market data availability...')
    try:
        response = requests.get(f'{base_url}/api/v1/market-data/live', timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})
            
            symbols = market_data.get('symbols', [])
            print(f'Market data symbols: {len(symbols)}')
            
            if len(symbols) > 0:
                print('✅ Market data is flowing!')
                # Show a few symbols with their data
                for symbol in symbols[:3]:
                    symbol_data = market_data.get(symbol, {})
                    ltp = symbol_data.get('ltp', 'N/A')
                    print(f'  - {symbol}: LTP = {ltp}')
            else:
                print('❌ NO MARKET DATA FOUND!')
                
        else:
            print(f'❌ Market data check failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error checking market data: {e}')
    
    # Step 4: Check positions (evidence of actual trades)
    print('\\nSTEP 4: Check current positions...')
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous/positions', timeout=10)
        if response.status_code == 200:
            data = response.json()
            positions = data.get('data', {}).get('positions', [])
            
            print(f'Current positions: {len(positions)}')
            if len(positions) > 0:
                print('✅ Positions found - trades are being executed!')
                for position in positions:
                    print(f'  - {position.get("symbol", "Unknown")}: {position.get("quantity", 0)} @ {position.get("price", 0)}')
            else:
                print('❌ NO POSITIONS FOUND - no trades executed!')
                
        else:
            print(f'❌ Position check failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error checking positions: {e}')
    
    print('\\n🎯 DIAGNOSIS:')
    print('- If strategies are loaded but no orders: Signal generation problem')
    print('- If market data is missing: Data flow problem')
    print('- If orders exist but no positions: Trade execution problem')
    print('- If no activity at all: Orchestrator processing loop problem')

if __name__ == "__main__":
    debug_strategy_activity() 
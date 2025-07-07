#!/usr/bin/env python3

import requests
import json

def check_autonomous_status():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    print('🔍 AUTONOMOUS TRADING STATUS CHECK:')
    print('=' * 50)
    
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f'Current Status:')
            print(f'  - Is Active: {trading_data.get("is_active")}')
            print(f'  - System Ready: {trading_data.get("system_ready")}')
            print(f'  - Active Strategies: {len(trading_data.get("active_strategies", []))}')
            print(f'  - Active Positions: {trading_data.get("active_positions")}')
            print(f'  - Total Trades: {trading_data.get("total_trades")}')
            print(f'  - Market Status: {trading_data.get("market_status")}')
            print(f'  - Risk Status: {trading_data.get("risk_status")}')
            
            if trading_data.get('is_active'):
                print('\\n🎉 AUTONOMOUS TRADING IS ACTIVE!')
            else:
                print('\\n❌ AUTONOMOUS TRADING IS INACTIVE!')
                print('Root Cause: System is not started')
                
        else:
            print(f'❌ Status check failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_autonomous_status() 
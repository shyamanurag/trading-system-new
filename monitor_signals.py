#!/usr/bin/env python3
"""
Real-time Signal Generation Monitor
Monitor trading signals and system activity with fresh Zerodha auth
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def monitor_signals():
    print('🔍 REAL-TIME SIGNAL MONITORING')
    print('=' * 50)
    print(f'Started: {datetime.now().strftime("%H:%M:%S")}')
    print('Monitoring signal generation with fresh Zerodha auth...')
    print()
    
    try:
        # Check current system status
        status_response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=5)
        if status_response.status_code == 200:
            data = status_response.json()['data']
            print(f'✅ System Active: {data["is_active"]}')
            print(f'✅ Active Strategies: {len(data["active_strategies"])}')
            print(f'🔄 Total Trades: {data["total_trades"]}')
            print(f'💰 Daily PNL: {data["daily_pnl"]}')
            print(f'📊 Market Status: {data["market_status"]}')
            print(f'🎯 Strategies: {", ".join(data["active_strategies"])}')
            print()
        
        # Check market data flow
        try:
            market_response = requests.get(f'{BASE_URL}/api/v1/market-data/symbols', timeout=5)
            if market_response.status_code == 200:
                market_data = market_response.json()
                print(f'📈 Market Data: {len(market_data)} symbols active')
                print()
        except:
            print('📈 Market Data: Checking...')
        
        # Monitor for signals every 10 seconds
        print('🔄 Starting signal monitoring (60 seconds)...')
        previous_trades = 0
        previous_pnl = 0.0
        
        for i in range(6):  # 1 minute of monitoring
            try:
                # Check for new trades/signals
                status_check = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=3)
                if status_check.status_code == 200:
                    current_data = status_check.json()['data']
                    trades = current_data['total_trades']
                    pnl = current_data['daily_pnl']
                    
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Check for new activity
                    if trades > previous_trades:
                        print(f'🚨 [{timestamp}] NEW TRADE! Total: {trades} (was {previous_trades})')
                        previous_trades = trades
                    
                    if pnl != previous_pnl:
                        print(f'💰 [{timestamp}] PNL CHANGE: {pnl} (was {previous_pnl})')
                        previous_pnl = pnl
                    
                    # Regular status update
                    market_status = current_data.get('market_status', 'unknown')
                    print(f'[{timestamp}] Trades: {trades} | PNL: {pnl} | Market: {market_status}')
                    
                    if trades > 0:
                        print(f'🎉 TRADING ACTIVE! Total trades: {trades}')
                
                time.sleep(10)
                
            except Exception as e:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] Monitor error: {e}')
                time.sleep(5)
        
        print('\n✅ Monitoring complete. System is active and ready for signals.')
        print('💡 Keep checking /api/v1/autonomous/status for real-time updates.')
        
    except Exception as e:
        print(f'❌ Monitoring failed: {e}')

if __name__ == "__main__":
    monitor_signals() 
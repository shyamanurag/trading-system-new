#!/usr/bin/env python3
"""
Monitor Live Trading System - Show real-time activity
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def monitor_live_trading():
    print('🔍 MONITORING LIVE TRADING SYSTEM')
    print('=' * 60)
    print(f'Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('Monitoring every 10 seconds...')
    print('Press Ctrl+C to stop\n')
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f'[{timestamp}] 🔄 Checking system activity...')
            
            # 1. Check trading status
            try:
                response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        trading_data = data.get('data', {})
                        session_id = trading_data.get('session_id', 'N/A')
                        is_active = trading_data.get('is_active', False)
                        strategies = len(trading_data.get('active_strategies', []))
                        
                        print(f'   🤖 Trading: {"🟢 ACTIVE" if is_active else "🔴 STOPPED"}')
                        print(f'   📊 Session: {session_id}')
                        print(f'   🎯 Strategies: {strategies} running')
            except Exception as e:
                print(f'   ❌ Status check failed: {e}')
            
            # 2. Check elite recommendations
            try:
                response = requests.get(f'{BASE_URL}/api/v1/elite/', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        recommendations = data.get('recommendations', [])
                        print(f'   ⭐ Elite Trades: {len(recommendations)} opportunities')
                        
                        # Show highest confidence trade
                        if recommendations:
                            best_trade = max(recommendations, key=lambda x: x.get('confidence', 0))
                            symbol = best_trade.get('symbol', 'N/A')
                            confidence = best_trade.get('confidence', 0)
                            direction = best_trade.get('direction', 'N/A')
                            entry = best_trade.get('entry_price', 0)
                            current = best_trade.get('current_price', 0)
                            
                            print(f'   🎯 Best Trade: {symbol} {direction} @ ₹{entry} ({confidence}% confidence)')
                            print(f'   📈 Current Price: ₹{current}')
            except Exception as e:
                print(f'   ❌ Elite trades check failed: {e}')
            
            # 3. Check live market data
            try:
                response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    symbol_count = data.get('symbol_count', 0)
                    print(f'   📊 Market Data: {symbol_count} symbols flowing')
                    
                    # Show sample prices
                    if 'data' in data and data['data']:
                        sample_symbols = ['BANKNIFTY-I', 'MARUTI', 'RELIANCE']
                        for symbol in sample_symbols:
                            if symbol in data['data']:
                                symbol_data = data['data'][symbol]
                                price = symbol_data.get('current_price', symbol_data.get('price', 0))
                                print(f'     {symbol}: ₹{price}')
            except Exception as e:
                print(f'   ❌ Market data check failed: {e}')
            
            # 4. Check positions (if any)
            try:
                response = requests.get(f'{BASE_URL}/api/v1/positions', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        positions = data.get('positions', [])
                        print(f'   📋 Active Positions: {len(positions)}')
                        
                        if positions:
                            for pos in positions[:2]:  # Show first 2 positions
                                symbol = pos.get('symbol', 'N/A')
                                quantity = pos.get('quantity', 0)
                                price = pos.get('average_price', 0)
                                pnl = pos.get('pnl', 0)
                                print(f'     {symbol}: {quantity} @ ₹{price} (P&L: ₹{pnl})')
            except Exception as e:
                print(f'   ❌ Positions check failed: {e}')
            
            print('   ' + '-' * 40)
            time.sleep(10)  # Wait 10 seconds before next check
            
    except KeyboardInterrupt:
        print('\n\n🛑 Monitoring stopped by user')
        print('Trading system continues running autonomously!')
    except Exception as e:
        print(f'\n❌ Monitoring error: {e}')
        print('Trading system continues running autonomously!')

if __name__ == "__main__":
    monitor_live_trading() 
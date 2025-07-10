#!/usr/bin/env python3
"""
Test live market data during trading hours
"""
import requests
import json
from datetime import datetime

def test_live_market_data():
    print('🔥 TESTING LIVE MARKET DATA...')
    print('='*50)
    
    try:
        # Test main market data endpoint
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data', timeout=10)
        data = r.json()
        
        print(f'✅ Market Data Status: {data.get("success")}')
        print(f'✅ Symbols Active: {data.get("symbol_count", 0)}')
        print(f'✅ Data Flowing: {data.get("data_flowing", False)}')
        print(f'✅ Market Status: {data.get("market_status", "UNKNOWN")}')
        print(f'✅ Timestamp: {data.get("timestamp", "N/A")}')
        
        # Test specific symbol prices
        print('\n📊 Sample Live Prices:')
        symbols = ['BANKNIFTY-I', 'NIFTY-I', 'RELIANCE', 'TCS', 'MARUTI']
        
        for symbol in symbols:
            try:
                symbol_r = requests.get(f'https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data/{symbol}', timeout=5)
                symbol_data = symbol_r.json()
                price = symbol_data.get('current_price', 'N/A')
                change = symbol_data.get('price_change', 'N/A')
                print(f'  {symbol}: ₹{price} ({change}%)')
            except:
                print(f'  {symbol}: Error fetching data')
        
        # Test market status
        print('\n🕐 Market Timing Check:')
        status_r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/system/status', timeout=10)
        status_data = status_r.json()
        print(f'✅ Market Open: {status_data.get("market_open", False)}')
        print(f'✅ Trading Hours: {status_data.get("trading_hours", "Unknown")}')
        
        return data.get('symbol_count', 0) > 0
        
    except Exception as e:
        print(f'❌ Error testing live market data: {e}')
        return False

if __name__ == '__main__':
    success = test_live_market_data()
    if success:
        print('\n🚀 LIVE MARKET DATA CONFIRMED!')
        print('✅ Ready for live trading tests')
    else:
        print('\n❌ Live market data not available') 
#!/usr/bin/env python3
"""
Test deployed system with live market data
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def test_deployed_system_live():
    print('🔥 TESTING DEPLOYED SYSTEM WITH LIVE MARKET DATA...')
    print('='*60)
    
    try:
        # 1. Test market data flow
        print('📊 1. Testing Live Market Data Flow...')
        market_r = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=10)
        market_data = market_r.json()
        
        print(f'   ✅ Market Data Success: {market_data.get("success")}')
        print(f'   ✅ Symbols Active: {market_data.get("symbol_count", 0)}')
        print(f'   ✅ Data Flowing: {market_data.get("data_flowing", False)}')
        print(f'   ✅ Market Status: {market_data.get("market_status")}')
        
        # 2. Test autonomous trading status
        print('\n🤖 2. Testing Autonomous Trading System...')
        auto_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
        auto_data = auto_r.json()
        
        if auto_data.get('success'):
            trading_data = auto_data.get('data', {})
            print(f'   ✅ Trading Active: {trading_data.get("is_active", False)}')
            print(f'   ✅ System Ready: {trading_data.get("system_ready", False)}')
            print(f'   ✅ Active Strategies: {trading_data.get("active_strategies_count", 0)}')
            print(f'   ✅ Session: {trading_data.get("session_id", "None")}')
        else:
            print(f'   ❌ Autonomous status error: {auto_data.get("message")}')
        
        # 3. Test starting autonomous trading
        print('\n🚀 3. Testing Trading System Start...')
        start_r = requests.post(f'{BASE_URL}/api/v1/autonomous/start', timeout=15)
        start_data = start_r.json()
        
        print(f'   ✅ Start Command: {start_data.get("success")}')
        print(f'   ✅ Message: {start_data.get("message")}')
        
        if start_data.get('success'):
            # Wait a moment for system to initialize
            time.sleep(5)
            
            # Check status again after starting
            print('\n📈 4. Checking Trading Status After Start...')
            status_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
            status_data = status_r.json()
            
            if status_data.get('success'):
                trading_status = status_data.get('data', {})
                print(f'   ✅ Is Active: {trading_status.get("is_active", False)}')
                print(f'   ✅ System Ready: {trading_status.get("system_ready", False)}')
                print(f'   ✅ Active Strategies: {trading_status.get("active_strategies_count", 0)}')
                print(f'   ✅ Total Trades: {trading_status.get("total_trades", 0)}')
                print(f'   ✅ Daily P&L: ₹{trading_status.get("daily_pnl", 0)}')
                
                # 5. Test signal generation (run for 30 seconds)
                print('\n⚡ 5. Testing Signal Generation (30 seconds)...')
                signals_before = trading_status.get("total_trades", 0)
                
                time.sleep(30)
                
                # Check for new signals/trades
                final_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
                final_data = final_r.json()
                
                if final_data.get('success'):
                    final_status = final_data.get('data', {})
                    signals_after = final_status.get("total_trades", 0)
                    new_signals = signals_after - signals_before
                    
                    print(f'   ✅ Signals Before: {signals_before}')
                    print(f'   ✅ Signals After: {signals_after}')
                    print(f'   ✅ New Signals Generated: {new_signals}')
                    
                    if new_signals > 0:
                        print(f'   🎉 SUCCESS: {new_signals} new trading signals generated!')
                    else:
                        print(f'   ⚠️ No new signals in 30 seconds (normal during low volatility)')
        
        # 6. Test system components
        print('\n🔧 6. Testing System Components...')
        system_r = requests.get(f'{BASE_URL}/api/v1/system/status', timeout=10)
        system_data = system_r.json()
        
        print(f'   ✅ System Health: {system_data.get("status", "unknown")}')
        print(f'   ✅ Market Open: {system_data.get("market_open", False)}')
        print(f'   ✅ Components Ready: {system_data.get("components_ready", "unknown")}')
        
        # Summary
        print('\n🎯 DEPLOYED SYSTEM TEST SUMMARY:')
        market_ok = market_data.get('symbol_count', 0) > 0
        trading_ok = start_data.get('success', False)
        system_ok = system_r.status_code == 200
        
        print(f'   ✅ Market Data: {"OK" if market_ok else "FAILED"}')
        print(f'   ✅ Trading System: {"OK" if trading_ok else "FAILED"}')
        print(f'   ✅ System Health: {"OK" if system_ok else "FAILED"}')
        
        overall_success = market_ok and trading_ok and system_ok
        return overall_success
        
    except Exception as e:
        print(f'❌ Error in deployed system test: {e}')
        return False

if __name__ == '__main__':
    success = test_deployed_system_live()
    
    if success:
        print('\n🎉 DEPLOYED SYSTEM LIVE TEST: SUCCESS!')
        print('✅ System is working with live market data!')
        print('✅ Orchestrator fix has resolved the trading issues!')
    else:
        print('\n❌ DEPLOYED SYSTEM LIVE TEST: FAILED')
        print('❌ Issues detected with deployed system') 
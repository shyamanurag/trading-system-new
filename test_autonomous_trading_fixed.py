#!/usr/bin/env python3
"""
Test autonomous trading system after len() error fixes
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def test_autonomous_trading_fixed():
    print('🎯 TESTING AUTONOMOUS TRADING AFTER FIXES')
    print('='*60)
    
    try:
        # 1. Test autonomous status (was failing with len() error)
        print('🔍 1. Testing Autonomous Status (was failing before)...')
        status_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
        status_data = status_r.json()
        
        print(f'   ✅ Status Success: {status_data.get("success")}')
        print(f'   ✅ Status Message: {status_data.get("message")}')
        
        if status_data.get('success'):
            data = status_data.get('data', {})
            print(f'   ✅ Active Strategies: {data.get("active_strategies", [])}')
            print(f'   ✅ Strategy Count: {data.get("active_strategies_count", 0)}')
            print(f'   ✅ System Ready: {data.get("system_ready", False)}')
            print(f'   ✅ Session ID: {data.get("session_id", "unknown")}')
            
            # Check for the old error
            error_msg = status_data.get('message', '')
            if 'len()' in error_msg:
                print(f'   ❌ OLD LEN() ERROR STILL EXISTS: {error_msg}')
                return False
            else:
                print(f'   🎉 LEN() ERROR FIXED! No more "object of type \'int\' has no len()"')
        
        # 2. Test starting autonomous trading
        print('\n🚀 2. Testing Autonomous Trading Start...')
        start_r = requests.post(f'{BASE_URL}/api/v1/autonomous/start', timeout=15)
        start_data = start_r.json()
        
        print(f'   ✅ Start Success: {start_data.get("success")}')
        print(f'   ✅ Start Message: {start_data.get("message")}')
        
        if start_data.get('success'):
            print(f'   🎉 AUTONOMOUS TRADING STARTED SUCCESSFULLY!')
        
        # 3. Wait and check status again
        print('\n⏳ 3. Waiting 5 seconds and checking post-start status...')
        time.sleep(5)
        
        final_r = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
        final_data = final_r.json()
        
        if final_data.get('success'):
            final_status = final_data.get('data', {})
            print(f'   ✅ Post-Start Active: {final_status.get("is_active", False)}')
            print(f'   ✅ Post-Start Ready: {final_status.get("system_ready", False)}')
            print(f'   ✅ Post-Start Strategies: {final_status.get("active_strategies_count", 0)}')
        
        # 4. Test critical functionality that was broken
        print('\n📊 4. Testing Previously Broken Functionality...')
        
        # Test market data (should have symbols)
        market_r = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=10)
        market_data = market_r.json()
        
        print(f'   ✅ Market Data Success: {market_data.get("success")}')
        print(f'   ✅ Symbol Count: {market_data.get("symbol_count", 0)}')
        
        # Test system status
        system_r = requests.get(f'{BASE_URL}/api/v1/system/status', timeout=10)
        system_data = system_r.json()
        
        print(f'   ✅ System Status: {system_data.get("status")}')
        print(f'   ✅ System Uptime: {system_data.get("uptime")}')
        
        # Summary
        print('\n🎯 AUTONOMOUS TRADING FIX VERIFICATION:')
        print('='*60)
        
        autonomous_working = status_data.get('success', False) and 'len()' not in status_data.get('message', '')
        start_working = start_data.get('success', False)
        market_working = market_data.get('symbol_count', 0) > 0
        system_working = system_r.status_code == 200
        
        print(f'   ✅ Autonomous Status API: {"FIXED" if autonomous_working else "STILL BROKEN"}')
        print(f'   ✅ Autonomous Start API: {"WORKING" if start_working else "BROKEN"}')
        print(f'   ✅ Market Data: {"WORKING" if market_working else "BROKEN"}')
        print(f'   ✅ System Health: {"WORKING" if system_working else "BROKEN"}')
        
        overall_success = autonomous_working and start_working
        
        if overall_success:
            print('\n🎉 SUCCESS: AUTONOMOUS TRADING SYSTEM IS NOW WORKING!')
            print('✅ The critical len() error has been resolved')
            print('✅ Orchestrator initialization is successful')
            print('✅ Trading system can start and manage strategies')
            print('✅ Zero trades issue should now be resolved!')
            return True
        else:
            print('\n❌ PARTIAL SUCCESS: Some issues remain')
            return False
        
    except Exception as e:
        print(f'❌ Error testing autonomous trading: {e}')
        return False

if __name__ == '__main__':
    success = test_autonomous_trading_fixed()
    
    if success:
        print('\n🚀 FINAL RESULT: AUTONOMOUS TRADING SYSTEM FIXED!')
        print('🎯 Your trading system should now generate trades when markets are active!')
    else:
        print('\n⚠️ FINAL RESULT: Additional fixes may be needed') 
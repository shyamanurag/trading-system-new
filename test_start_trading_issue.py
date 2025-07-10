#!/usr/bin/env python3
"""
Test why start trading button isn't actually starting trading
"""
import requests
import time

def test_start_trading_issue():
    print("🔍 TESTING START TRADING ISSUE...")
    print("="*60)
    
    try:
        # Check initial status
        print("📊 1. INITIAL STATUS:")
        r1 = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        data1 = r1.json()
        print(f"   - Is Active: {data1['data']['is_active']}")
        print(f"   - System Ready: {data1['data']['system_ready']}")
        print(f"   - Market Status: {data1['data']['market_status']}")
        print(f"   - Strategies: {data1['data']['active_strategies_count']}")
        
        # Try to start trading
        print("\n🚀 2. STARTING TRADING...")
        r2 = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start')
        start_data = r2.json()
        print(f"   - Start Success: {start_data['success']}")
        print(f"   - Start Message: {start_data['message']}")
        
        # Wait and check status again
        print("\n⏳ 3. WAITING 3 SECONDS...")
        time.sleep(3)
        
        print("\n📊 4. STATUS AFTER START:")
        r3 = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        data3 = r3.json()
        print(f"   - Is Active: {data3['data']['is_active']}")
        print(f"   - System Ready: {data3['data']['system_ready']}")
        print(f"   - Market Status: {data3['data']['market_status']}")
        print(f"   - Session: {data3['data']['session_id']}")
        
        # Check dashboard values
        print("\n📈 5. DASHBOARD VALUES:")
        r4 = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/dashboard/summary')
        dash_data = r4.json()
        if dash_data.get('success'):
            sys_metrics = dash_data.get('system_metrics', {})
            print(f"   - AUM: {sys_metrics.get('aum', 0)}")
            print(f"   - Active Users: {sys_metrics.get('active_users', 0)}")
            print(f"   - Total Trades: {sys_metrics.get('total_trades', 0)}")
            print(f"   - Daily PnL: {sys_metrics.get('daily_pnl', 0)}")
            
            users = dash_data.get('users', [])
            print(f"   - Users Count: {len(users)}")
        else:
            print(f"   - Dashboard Error: {dash_data.get('error')}")
        
        # Analysis
        print("\n🔍 6. ANALYSIS:")
        if start_data['success'] and not data3['data']['is_active']:
            print("❌ ISSUE FOUND: Start returns success but system doesn't become active")
            if data3['data']['market_status'] == 'UNKNOWN':
                print("💡 LIKELY CAUSE: Market data connection missing")
            else:
                print("💡 LIKELY CAUSE: Check orchestrator _can_start_trading() conditions")
        elif data3['data']['is_active']:
            print("✅ Start trading is working - system becomes active")
        else:
            print("❌ Start trading failed completely")
            
    except Exception as e:
        print(f"❌ Error testing start trading: {e}")

if __name__ == "__main__":
    test_start_trading_issue() 
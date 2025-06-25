#!/usr/bin/env python3
"""
Test Autonomous Trading with Pre-configured Broker
"""

import requests
import json
import time

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def test_autonomous_trading():
    """Test if autonomous trading starts with pre-configured broker"""
    print('🚀 TESTING AUTONOMOUS TRADING WITH PRE-CONFIGURED BROKER')
    print('=' * 70)

    # Try to start autonomous trading now that we have broker users
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/autonomous/start',
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f'📤 Starting autonomous trading...')
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'   ✅ Success: {result.get("message", "Trading started")}')
            
            # Check final status
            print(f'\n⏳ Waiting for system startup...')
            time.sleep(5)  # Wait for startup
            
            status_response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                trading_data = status_data.get('data', {})
                
                is_active = trading_data.get('is_active', False)
                session_id = trading_data.get('session_id')
                start_time = trading_data.get('start_time')
                strategies = trading_data.get('active_strategies', [])
                
                print(f'\n📊 FINAL STATUS CHECK:')
                print(f'   🤖 Trading Active: {is_active}')
                print(f'   🆔 Session ID: {session_id}')
                print(f'   ⏰ Start Time: {start_time}')
                print(f'   📈 Active Strategies: {len(strategies)}')
                
                if is_active:
                    print(f'\n🎉 SUCCESS! AUTONOMOUS TRADING IS NOW RUNNING!')
                    print(f'✅ Pre-configured broker setup working perfectly')
                    print(f'📈 System ready for live trading')
                    return True
                else:
                    print(f'\n⚠️ Trading engine started but not active yet')
                    print(f'💡 May need daily Zerodha authentication token')
                    print(f'🔑 Next step: Visit /daily-auth for token setup')
                    return False
            else:
                print(f'   ❌ Status check failed: {status_response.status_code}')
                return False
        else:
            print(f'   ❌ Failed: {response.text[:300]}')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def check_broker_users():
    """Check current broker users"""
    print(f'\n🏦 CHECKING BROKER USERS:')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/control/users/broker', timeout=10)
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            print(f'   📊 Total Users: {len(users)}')
            for user in users:
                user_id = user.get('user_id', 'Unknown')
                name = user.get('name', 'Unknown')
                capital = user.get('initial_capital', 0)
                paper_trading = user.get('paper_trading', True)
                print(f'   👤 {user_id}: {name}')
                print(f'      💰 Capital: ₹{capital:,.2f}')
                print(f'      📝 Mode: {"Paper" if paper_trading else "Live"} Trading')
        else:
            print(f'   ❌ Failed to get users: {response.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

def main():
    """Main test function"""
    # Check broker users first
    check_broker_users()
    
    # Test autonomous trading
    success = test_autonomous_trading()
    
    print(f'\n' + '=' * 70)
    if success:
        print('🎉 AUTONOMOUS TRADING IS RUNNING!')
        print('✅ No daily auth needed - system is ready!')
    else:
        print('⚠️ AUTONOMOUS TRADING NEEDS DAILY AUTH')
        print('🔑 Visit: https://algoauto-9gx56.ondigitalocean.app/daily-auth')
        print('📋 Complete daily authentication to activate trading')
    print('=' * 70)

if __name__ == "__main__":
    main() 
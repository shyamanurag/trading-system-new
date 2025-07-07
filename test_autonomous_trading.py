#!/usr/bin/env python3

import requests
import json
import time

def test_autonomous_trading():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    print('🚀 AUTONOMOUS TRADING SYSTEM TEST')
    print('=' * 60)
    
    # Step 1: Check current status
    print('STEP 1: Check current autonomous trading status...')
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous-trading/status', timeout=15)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f'✅ Status Check Result:')
            print(f'  - Is Active: {trading_data.get("is_active")}')
            print(f'  - System Ready: {trading_data.get("system_ready")}')
            print(f'  - Active Strategies: {len(trading_data.get("active_strategies", []))}')
            print(f'  - Total Trades: {trading_data.get("total_trades")}')
            print(f'  - Market Status: {trading_data.get("market_status")}')
            
            if trading_data.get("is_active"):
                print('🎉 Autonomous trading is already ACTIVE!')
                return
            else:
                print('⚠️  Autonomous trading is INACTIVE - attempting to start...')
                
        else:
            print(f'❌ Status check failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Status check error: {e}')
    
    # Step 2: Attempt to start autonomous trading
    print('\\nSTEP 2: Start autonomous trading...')
    try:
        response = requests.post(f'{base_url}/api/v1/autonomous-trading/start', timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Start Command Result:')
            print(f'  - Success: {data.get("success")}')
            print(f'  - Message: {data.get("message")}')
            
            if data.get("success"):
                print('🎉 Autonomous trading started successfully!')
            else:
                print(f'❌ Start failed: {data.get("message")}')
                return
                
        else:
            print(f'❌ Start command failed: {response.status_code}')
            try:
                error_data = response.json()
                print(f'     Error: {error_data.get("detail", "Unknown error")}')
            except:
                print(f'     Raw error: {response.text[:200]}')
            return
            
    except Exception as e:
        print(f'❌ Start command error: {e}')
        return
    
    # Step 3: Verify trading is now active
    print('\\nSTEP 3: Verify autonomous trading is now active...')
    time.sleep(3)  # Wait a moment for system to initialize
    
    try:
        response = requests.get(f'{base_url}/api/v1/autonomous-trading/status', timeout=15)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f'✅ Verification Result:')
            print(f'  - Is Active: {trading_data.get("is_active")}')
            print(f'  - System Ready: {trading_data.get("system_ready")}')
            print(f'  - Active Strategies: {trading_data.get("active_strategies")}')
            print(f'  - Market Status: {trading_data.get("market_status")}')
            
            if trading_data.get("is_active"):
                print('🎉 SUCCESS: Autonomous trading is now ACTIVE!')
                
                # Check for actual trading activity
                print('\\nSTEP 4: Check for trading activity...')
                
                # Check positions
                try:
                    pos_response = requests.get(f'{base_url}/api/v1/autonomous-trading/positions', timeout=10)
                    if pos_response.status_code == 200:
                        pos_data = pos_response.json()
                        positions = pos_data.get('data', {}).get('positions', [])
                        print(f'  - Current positions: {len(positions)}')
                    else:
                        print(f'  - Positions check failed: {pos_response.status_code}')
                except Exception as e:
                    print(f'  - Positions error: {e}')
                
                # Check orders
                try:
                    ord_response = requests.get(f'{base_url}/api/v1/autonomous-trading/orders', timeout=10)
                    if ord_response.status_code == 200:
                        ord_data = ord_response.json()
                        orders = ord_data.get('data', {}).get('orders', [])
                        print(f'  - Current orders: {len(orders)}')
                    else:
                        print(f'  - Orders check failed: {ord_response.status_code}')
                except Exception as e:
                    print(f'  - Orders error: {e}')
                
            else:
                print('❌ FAILED: Autonomous trading is still INACTIVE after start command!')
                
        else:
            print(f'❌ Verification failed: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Verification error: {e}')
    
    print('\\n🎯 SUMMARY:')
    print('- The autonomous trading system should now be active if all steps succeeded')
    print('- If still inactive, there may be orchestrator initialization issues')
    print('- Check market data connection and Zerodha authentication')

if __name__ == "__main__":
    test_autonomous_trading() 
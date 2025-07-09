#!/usr/bin/env python3
import requests
import json

def check_trading_status():
    print("🔍 Checking trading system status...")
    
    try:
        # Check autonomous status
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Active: {data['data']['is_active']}")
            print(f"Strategies: {data['data']['active_strategies_count']}")
            print(f"Total Trades: {data['data']['total_trades']}")
            print(f"Session ID: {data['data']['session_id']}")
            
            # Check for OrderManager and Zerodha status
            order_manager_status = data['data'].get('order_manager_status', 'N/A')
            broker_status = data['data'].get('broker_status', 'N/A')
            
            print(f"OrderManager Status: {order_manager_status}")
            print(f"Broker Status: {broker_status}")
            
            if data['data']['total_trades'] == 0:
                print("❌ ZERO TRADES DETECTED")
                print("Possible causes:")
                print("1. OrderManager not initialized")
                print("2. Zerodha credentials missing")
                print("3. Signals not reaching trade engine")
                return False
            else:
                print("✅ TRADES DETECTED")
                return True
        else:
            print(f"Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error checking status: {e}")
        return False

if __name__ == "__main__":
    check_trading_status() 
import requests
import json

def check_trading_status():
    print("🔍 Checking trading system status...")
    
    try:
        # Check autonomous status
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Active: {data['data']['is_active']}")
            print(f"Strategies: {data['data']['active_strategies_count']}")
            print(f"Total Trades: {data['data']['total_trades']}")
            print(f"Session ID: {data['data']['session_id']}")
            
            # Check for OrderManager and Zerodha status
            order_manager_status = data['data'].get('order_manager_status', 'N/A')
            broker_status = data['data'].get('broker_status', 'N/A')
            
            print(f"OrderManager Status: {order_manager_status}")
            print(f"Broker Status: {broker_status}")
            
            if data['data']['total_trades'] == 0:
                print("❌ ZERO TRADES DETECTED")
                print("Possible causes:")
                print("1. OrderManager not initialized")
                print("2. Zerodha credentials missing")
                print("3. Signals not reaching trade engine")
                return False
            else:
                print("✅ TRADES DETECTED")
                return True
        else:
            print(f"Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error checking status: {e}")
        return False

if __name__ == "__main__":
    check_trading_status() 
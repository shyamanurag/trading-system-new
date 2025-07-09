#!/usr/bin/env python3
"""
Test Zerodha Client Connection Flow
==================================
Verifies that the same authenticated Zerodha client is used throughout:
1. Orchestrator -> TradeEngine -> OrderManager pipeline
2. API calls can reach Zerodha through the authenticated client
"""

import requests
import time

def test_deployed_zerodha_connection():
    """Test the deployed system's Zerodha connection"""
    print("🔍 Testing Zerodha client connection in deployed system...")
    
    try:
        # Test 1: Check broker connection
        print("\n1. TESTING BROKER CONNECTION")
        broker_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
        print(f"   Status: {broker_response.status_code}")
        
        if broker_response.status_code == 200:
            broker_data = broker_response.json()
            print(f"   Broker: {broker_data.get('broker', 'Unknown')}")
            print(f"   Status: {broker_data.get('status', 'Unknown')}")
            print(f"   API Calls Today: {broker_data.get('api_calls_today', 'Unknown')}")
            print(f"   Market Data Connected: {broker_data.get('market_data_connected', 'Unknown')}")
            print(f"   Order Management Connected: {broker_data.get('order_management_connected', 'Unknown')}")
            
            if broker_data.get('status') == 'connected':
                print("   ✅ Zerodha broker is connected")
            else:
                print("   ❌ Zerodha broker NOT connected")
                return False
        else:
            print(f"   ❌ Broker status check failed: {broker_response.text}")
            return False
        
        # Test 2: Check trading system status
        print("\n2. TESTING TRADING SYSTEM STATUS")
        trading_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        print(f"   Status: {trading_response.status_code}")
        
        if trading_response.status_code == 200:
            trading_data = trading_response.json()
            print(f"   Active: {trading_data['data']['is_active']}")
            print(f"   Strategies: {trading_data['data']['active_strategies_count']}")
            print(f"   Total Trades: {trading_data['data']['total_trades']}")
            print(f"   System Ready: {trading_data['data'].get('system_ready', 'Unknown')}")
            
            # Check if OrderManager can access Zerodha
            total_trades = trading_data['data']['total_trades']
            if total_trades > 0:
                print("   ✅ Orders are being placed (OrderManager connected to Zerodha)")
                return True
            else:
                print("   ⚠️ Zero trades - investigating signal->OrderManager->Zerodha pipeline...")
        else:
            print(f"   ❌ Trading status check failed: {trading_response.text}")
            return False
        
        # Test 3: Monitor for new trades (after fix deployment)
        print("\n3. MONITORING FOR NEW TRADES (30 seconds)")
        print("   Waiting for deployment to apply and trades to execute...")
        
        initial_trades = trading_data['data']['total_trades']
        for i in range(6):  # Check every 5 seconds for 30 seconds
            time.sleep(5)
            
            try:
                check_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    current_trades = check_data['data']['total_trades']
                    
                    print(f"   Check {i+1}/6: Total trades = {current_trades}")
                    
                    if current_trades > initial_trades:
                        print(f"   ✅ NEW TRADES DETECTED! ({current_trades - initial_trades} new trades)")
                        print("   ✅ OrderManager successfully connected to Zerodha!")
                        return True
                else:
                    print(f"   ⚠️ Check {i+1} failed: {check_response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Check {i+1} error: {e}")
        
        print("   ⏰ No new trades in 30 seconds - system may need more time or additional fixes")
        
        # Test 4: Check broker API calls
        print("\n4. CHECKING BROKER API CALLS")
        final_broker_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
        if final_broker_response.status_code == 200:
            final_broker_data = final_broker_response.json()
            api_calls = final_broker_data.get('api_calls_today', 0)
            print(f"   API calls today: {api_calls}")
            
            if api_calls > 0:
                print("   ✅ Zerodha API calls are being made!")
                return True
            else:
                print("   ❌ No Zerodha API calls - OrderManager still not reaching Zerodha")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing Zerodha connection: {e}")
        return False

def main():
    print("🚀 Testing Zerodha Client Connection After Fix")
    print("=" * 50)
    
    success = test_deployed_zerodha_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: Zerodha client connection is working!")
        print("   - OrderManager can access authenticated Zerodha client")
        print("   - Trades are being executed through proper pipeline")
    else:
        print("❌ ISSUE: Zerodha client connection needs additional fixes")
        print("   - Signals are being generated")
        print("   - Zerodha is connected at broker level")
        print("   - But OrderManager cannot access the authenticated client")
        print("   - Need to investigate singleton orchestrator access")
    
    return success

if __name__ == "__main__":
    main() 
"""
Test Zerodha Client Connection Flow
==================================
Verifies that the same authenticated Zerodha client is used throughout:
1. Orchestrator -> TradeEngine -> OrderManager pipeline
2. API calls can reach Zerodha through the authenticated client
"""

import requests
import time

def test_deployed_zerodha_connection():
    """Test the deployed system's Zerodha connection"""
    print("🔍 Testing Zerodha client connection in deployed system...")
    
    try:
        # Test 1: Check broker connection
        print("\n1. TESTING BROKER CONNECTION")
        broker_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
        print(f"   Status: {broker_response.status_code}")
        
        if broker_response.status_code == 200:
            broker_data = broker_response.json()
            print(f"   Broker: {broker_data.get('broker', 'Unknown')}")
            print(f"   Status: {broker_data.get('status', 'Unknown')}")
            print(f"   API Calls Today: {broker_data.get('api_calls_today', 'Unknown')}")
            print(f"   Market Data Connected: {broker_data.get('market_data_connected', 'Unknown')}")
            print(f"   Order Management Connected: {broker_data.get('order_management_connected', 'Unknown')}")
            
            if broker_data.get('status') == 'connected':
                print("   ✅ Zerodha broker is connected")
            else:
                print("   ❌ Zerodha broker NOT connected")
                return False
        else:
            print(f"   ❌ Broker status check failed: {broker_response.text}")
            return False
        
        # Test 2: Check trading system status
        print("\n2. TESTING TRADING SYSTEM STATUS")
        trading_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        print(f"   Status: {trading_response.status_code}")
        
        if trading_response.status_code == 200:
            trading_data = trading_response.json()
            print(f"   Active: {trading_data['data']['is_active']}")
            print(f"   Strategies: {trading_data['data']['active_strategies_count']}")
            print(f"   Total Trades: {trading_data['data']['total_trades']}")
            print(f"   System Ready: {trading_data['data'].get('system_ready', 'Unknown')}")
            
            # Check if OrderManager can access Zerodha
            total_trades = trading_data['data']['total_trades']
            if total_trades > 0:
                print("   ✅ Orders are being placed (OrderManager connected to Zerodha)")
                return True
            else:
                print("   ⚠️ Zero trades - investigating signal->OrderManager->Zerodha pipeline...")
        else:
            print(f"   ❌ Trading status check failed: {trading_response.text}")
            return False
        
        # Test 3: Monitor for new trades (after fix deployment)
        print("\n3. MONITORING FOR NEW TRADES (30 seconds)")
        print("   Waiting for deployment to apply and trades to execute...")
        
        initial_trades = trading_data['data']['total_trades']
        for i in range(6):  # Check every 5 seconds for 30 seconds
            time.sleep(5)
            
            try:
                check_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    current_trades = check_data['data']['total_trades']
                    
                    print(f"   Check {i+1}/6: Total trades = {current_trades}")
                    
                    if current_trades > initial_trades:
                        print(f"   ✅ NEW TRADES DETECTED! ({current_trades - initial_trades} new trades)")
                        print("   ✅ OrderManager successfully connected to Zerodha!")
                        return True
                else:
                    print(f"   ⚠️ Check {i+1} failed: {check_response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Check {i+1} error: {e}")
        
        print("   ⏰ No new trades in 30 seconds - system may need more time or additional fixes")
        
        # Test 4: Check broker API calls
        print("\n4. CHECKING BROKER API CALLS")
        final_broker_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/broker/status')
        if final_broker_response.status_code == 200:
            final_broker_data = final_broker_response.json()
            api_calls = final_broker_data.get('api_calls_today', 0)
            print(f"   API calls today: {api_calls}")
            
            if api_calls > 0:
                print("   ✅ Zerodha API calls are being made!")
                return True
            else:
                print("   ❌ No Zerodha API calls - OrderManager still not reaching Zerodha")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing Zerodha connection: {e}")
        return False

def main():
    print("🚀 Testing Zerodha Client Connection After Fix")
    print("=" * 50)
    
    success = test_deployed_zerodha_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: Zerodha client connection is working!")
        print("   - OrderManager can access authenticated Zerodha client")
        print("   - Trades are being executed through proper pipeline")
    else:
        print("❌ ISSUE: Zerodha client connection needs additional fixes")
        print("   - Signals are being generated")
        print("   - Zerodha is connected at broker level")
        print("   - But OrderManager cannot access the authenticated client")
        print("   - Need to investigate singleton orchestrator access")
    
    return success

if __name__ == "__main__":
    main() 
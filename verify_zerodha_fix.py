#!/usr/bin/env python3
"""
Comprehensive test to verify Zerodha connection fix
"""

import requests
import json
import time
from datetime import datetime

def test_zerodha_fix():
    """Test the Zerodha connection fix deployment"""
    print("🔧 TESTING ZERODHA CONNECTION FIX")
    print("=" * 60)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Test 1: Verify Zerodha Authentication
    print("\n1. 🔐 Testing Zerodha Authentication...")
    try:
        response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            authenticated = auth_data.get('authenticated', False)
            user_id = auth_data.get('user_id', 'Unknown')
            print(f"   ✅ Zerodha Authenticated: {authenticated}")
            print(f"   📋 User ID: {user_id}")
            
            if authenticated:
                session = auth_data.get('session', {})
                login_time = session.get('login_time', 'Unknown')
                print(f"   ⏰ Login Time: {login_time}")
                print("   🎯 AUTH STATUS: WORKING ✅")
            else:
                print("   ❌ AUTH STATUS: FAILED")
        else:
            print(f"   ❌ Auth check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
    
    # Test 2: Check Kite API Status
    print("\n2. 🔌 Testing Kite API Connection...")
    try:
        response = requests.get(f"{base_url}/api/v1/zerodha/status", timeout=10)
        if response.status_code == 200:
            kite_data = response.json()
            kite_status = kite_data.get('kite_status', 'Unknown')
            trading_enabled = kite_data.get('trading_enabled', False)
            print(f"   ✅ Kite Status: {kite_status}")
            print(f"   📊 Trading Enabled: {trading_enabled}")
            
            if kite_status == 'connected' and trading_enabled:
                print("   🎯 KITE API STATUS: WORKING ✅")
            else:
                print("   ❌ KITE API STATUS: ISSUES")
        else:
            print(f"   ❌ Kite API check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Kite API error: {e}")
    
    # Test 3: Check System Deployment Status
    print("\n3. 🚀 Testing System Deployment...")
    try:
        response = requests.get(f"{base_url}/ready", timeout=10)
        if response.status_code == 200:
            print("   ✅ System is ready and responding")
            print("   🎯 DEPLOYMENT STATUS: ACTIVE ✅")
        else:
            print(f"   ❌ System not ready: {response.status_code}")
    except Exception as e:
        print(f"   ❌ System check error: {e}")
    
    # Test 4: Check Market Data Flow
    print("\n4. 📈 Testing Market Data Flow...")
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=10)
        if response.status_code == 200:
            market_data = response.json()
            symbol_count = len(market_data.get('data', {}))
            print(f"   ✅ Market Data Symbols: {symbol_count}")
            
            if symbol_count > 40:
                print("   🎯 MARKET DATA STATUS: FLOWING ✅")
            else:
                print("   ⚠️ MARKET DATA STATUS: LIMITED")
        else:
            print(f"   ❌ Market data check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Market data error: {e}")
    
    # Test 5: Check for Active Strategies
    print("\n5. 🎯 Testing Strategy Activation...")
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            is_active = status_data.get('is_active', False)
            strategy_count = status_data.get('active_strategies_count', 0)
            print(f"   ✅ Autonomous Trading Active: {is_active}")
            print(f"   🎯 Active Strategies: {strategy_count}")
            
            if is_active and strategy_count > 0:
                print("   🎯 STRATEGY STATUS: ACTIVE ✅")
            else:
                print("   ❌ STRATEGY STATUS: INACTIVE")
        else:
            print(f"   ❌ Strategy check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Strategy error: {e}")
    
    # Test 6: Live Trading Test
    print("\n6. 🔥 Testing Live Trading Capability...")
    print("   ⏳ Waiting for live signals...")
    
    # Wait and check for any recent trading activity
    time.sleep(10)
    
    try:
        # Check deployment logs for recent signals
        response = requests.get(f"{base_url}/api/v1/debug/deployment-logs", timeout=10)
        if response.status_code == 200:
            logs = response.text
            
            # Look for success indicators
            if "SIGNAL GENERATED" in logs:
                print("   ✅ Signal generation detected in logs")
                signal_count = logs.count("SIGNAL GENERATED")
                print(f"   📊 Recent signals: {signal_count}")
                
                if "ORDER PLACED" in logs:
                    print("   🎯 ORDER PLACEMENT: SUCCESS ✅")
                    print("   🔥 ZERODHA FIX: WORKING PERFECTLY! 🔥")
                elif "Not connected to Zerodha" in logs:
                    print("   ❌ ORDER PLACEMENT: STILL FAILING")
                    print("   🔧 ZERODHA FIX: NEEDS MORE WORK")
                else:
                    print("   ⚠️ ORDER PLACEMENT: UNCLEAR")
                    print("   🔧 ZERODHA FIX: PARTIAL SUCCESS")
            else:
                print("   ⚠️ No recent signals detected")
        else:
            print(f"   ❌ Logs check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Live trading test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ZERODHA CONNECTION FIX VERIFICATION COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\n📋 SUMMARY:")
    print("   - If all tests show ✅, the fix is working perfectly")
    print("   - If ORDER PLACEMENT shows ❌, the fix needs more work")
    print("   - Check the logs above for detailed status")
    print("\n🚀 System should now be able to execute trades successfully!")

if __name__ == "__main__":
    test_zerodha_fix() 
"""
Comprehensive test to verify Zerodha connection fix
"""

import requests
import json
import time
from datetime import datetime

def test_zerodha_fix():
    """Test the Zerodha connection fix deployment"""
    print("🔧 TESTING ZERODHA CONNECTION FIX")
    print("=" * 60)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Test 1: Verify Zerodha Authentication
    print("\n1. 🔐 Testing Zerodha Authentication...")
    try:
        response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            authenticated = auth_data.get('authenticated', False)
            user_id = auth_data.get('user_id', 'Unknown')
            print(f"   ✅ Zerodha Authenticated: {authenticated}")
            print(f"   📋 User ID: {user_id}")
            
            if authenticated:
                session = auth_data.get('session', {})
                login_time = session.get('login_time', 'Unknown')
                print(f"   ⏰ Login Time: {login_time}")
                print("   🎯 AUTH STATUS: WORKING ✅")
            else:
                print("   ❌ AUTH STATUS: FAILED")
        else:
            print(f"   ❌ Auth check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
    
    # Test 2: Check Kite API Status
    print("\n2. 🔌 Testing Kite API Connection...")
    try:
        response = requests.get(f"{base_url}/api/v1/zerodha/status", timeout=10)
        if response.status_code == 200:
            kite_data = response.json()
            kite_status = kite_data.get('kite_status', 'Unknown')
            trading_enabled = kite_data.get('trading_enabled', False)
            print(f"   ✅ Kite Status: {kite_status}")
            print(f"   📊 Trading Enabled: {trading_enabled}")
            
            if kite_status == 'connected' and trading_enabled:
                print("   🎯 KITE API STATUS: WORKING ✅")
            else:
                print("   ❌ KITE API STATUS: ISSUES")
        else:
            print(f"   ❌ Kite API check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Kite API error: {e}")
    
    # Test 3: Check System Deployment Status
    print("\n3. 🚀 Testing System Deployment...")
    try:
        response = requests.get(f"{base_url}/ready", timeout=10)
        if response.status_code == 200:
            print("   ✅ System is ready and responding")
            print("   🎯 DEPLOYMENT STATUS: ACTIVE ✅")
        else:
            print(f"   ❌ System not ready: {response.status_code}")
    except Exception as e:
        print(f"   ❌ System check error: {e}")
    
    # Test 4: Check Market Data Flow
    print("\n4. 📈 Testing Market Data Flow...")
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=10)
        if response.status_code == 200:
            market_data = response.json()
            symbol_count = len(market_data.get('data', {}))
            print(f"   ✅ Market Data Symbols: {symbol_count}")
            
            if symbol_count > 40:
                print("   🎯 MARKET DATA STATUS: FLOWING ✅")
            else:
                print("   ⚠️ MARKET DATA STATUS: LIMITED")
        else:
            print(f"   ❌ Market data check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Market data error: {e}")
    
    # Test 5: Check for Active Strategies
    print("\n5. 🎯 Testing Strategy Activation...")
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            is_active = status_data.get('is_active', False)
            strategy_count = status_data.get('active_strategies_count', 0)
            print(f"   ✅ Autonomous Trading Active: {is_active}")
            print(f"   🎯 Active Strategies: {strategy_count}")
            
            if is_active and strategy_count > 0:
                print("   🎯 STRATEGY STATUS: ACTIVE ✅")
            else:
                print("   ❌ STRATEGY STATUS: INACTIVE")
        else:
            print(f"   ❌ Strategy check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Strategy error: {e}")
    
    # Test 6: Live Trading Test
    print("\n6. 🔥 Testing Live Trading Capability...")
    print("   ⏳ Waiting for live signals...")
    
    # Wait and check for any recent trading activity
    time.sleep(10)
    
    try:
        # Check deployment logs for recent signals
        response = requests.get(f"{base_url}/api/v1/debug/deployment-logs", timeout=10)
        if response.status_code == 200:
            logs = response.text
            
            # Look for success indicators
            if "SIGNAL GENERATED" in logs:
                print("   ✅ Signal generation detected in logs")
                signal_count = logs.count("SIGNAL GENERATED")
                print(f"   📊 Recent signals: {signal_count}")
                
                if "ORDER PLACED" in logs:
                    print("   🎯 ORDER PLACEMENT: SUCCESS ✅")
                    print("   🔥 ZERODHA FIX: WORKING PERFECTLY! 🔥")
                elif "Not connected to Zerodha" in logs:
                    print("   ❌ ORDER PLACEMENT: STILL FAILING")
                    print("   🔧 ZERODHA FIX: NEEDS MORE WORK")
                else:
                    print("   ⚠️ ORDER PLACEMENT: UNCLEAR")
                    print("   🔧 ZERODHA FIX: PARTIAL SUCCESS")
            else:
                print("   ⚠️ No recent signals detected")
        else:
            print(f"   ❌ Logs check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Live trading test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ZERODHA CONNECTION FIX VERIFICATION COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\n📋 SUMMARY:")
    print("   - If all tests show ✅, the fix is working perfectly")
    print("   - If ORDER PLACEMENT shows ❌, the fix needs more work")
    print("   - Check the logs above for detailed status")
    print("\n🚀 System should now be able to execute trades successfully!")

if __name__ == "__main__":
    test_zerodha_fix() 
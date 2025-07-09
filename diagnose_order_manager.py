#!/usr/bin/env python3
"""
Diagnostic script to check why signals are not reaching the order manager
"""

import requests
import json
import time
from datetime import datetime

def diagnose_order_manager():
    """Diagnose order manager issues"""
    print("🔍 DIAGNOSING ORDER MANAGER ISSUES")
    print("=" * 60)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check 1: System Status
    print("\n1. 📊 CHECKING SYSTEM STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Total Orders: {data.get('total_orders', 0)}")
            print(f"   ✅ Active Orders: {data.get('active_orders', 0)}")
            
            components = data.get('components', {})
            print(f"   ✅ Trade Engine: {components.get('trade_engine', 'Unknown')}")
            print(f"   ✅ Order Manager: {components.get('order_manager', 'Unknown')}")
            print(f"   ✅ Zerodha: {components.get('zerodha', 'Unknown')}")
        else:
            print(f"   ❌ System status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ System status error: {e}")
    
    # Check 2: Trading Status
    print("\n2. 🎯 CHECKING TRADING STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            print(f"   ✅ Trading Active: {trading_data.get('is_active', False)}")
            print(f"   ✅ Active Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"   ✅ System Ready: {trading_data.get('system_ready', False)}")
            print(f"   ✅ Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check strategy details
            strategies = trading_data.get('strategies', {})
            if strategies:
                print(f"   📊 Strategy Details:")
                for strategy_name, strategy_info in strategies.items():
                    print(f"      - {strategy_name}: {strategy_info.get('active', False)}")
        else:
            print(f"   ❌ Trading status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Trading status error: {e}")
    
    # Check 3: Recent Logs for Signal Processing
    print("\n3. 📋 CHECKING RECENT LOGS FOR SIGNAL PROCESSING...")
    try:
        response = requests.get(f"{base_url}/api/v1/debug/logs", timeout=10)
        if response.status_code == 200:
            logs = response.text
            
            # Look for key log patterns
            key_patterns = [
                "🚨 SIGNAL COLLECTED",
                "🚀 Processing",
                "signals through trade engine",
                "No OrderManager available",
                "PLACING ORDER",
                "Trade engine not available",
                "📭 No signals generated",
                "OrderManager initialization failed"
            ]
            
            found_patterns = {}
            for pattern in key_patterns:
                count = logs.count(pattern)
                if count > 0:
                    found_patterns[pattern] = count
            
            if found_patterns:
                print("   📊 Log Pattern Analysis:")
                for pattern, count in found_patterns.items():
                    print(f"      - '{pattern}': {count} occurrences")
            else:
                print("   ❌ No relevant log patterns found")
                
        else:
            print(f"   ❌ Log check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Log analysis error: {e}")
    
    # Check 4: Order Endpoints
    print("\n4. 💰 CHECKING ORDER ENDPOINTS...")
    order_endpoints = [
        "/api/v1/orders",
        "/api/v1/trading/orders",
        "/api/v1/system/orders"
    ]
    
    for endpoint in order_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                order_count = len(data.get('orders', data if isinstance(data, list) else []))
                print(f"   ✅ {endpoint}: {order_count} orders")
            else:
                print(f"   ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
    
    # Check 5: Trade Engine Status
    print("\n5. ⚙️ CHECKING TRADE ENGINE STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/orchestrator/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Orchestrator Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Trade Engine: {data.get('trade_engine', {}).get('initialized', False)}")
            print(f"   ✅ Components: {data.get('components', {})}")
        else:
            # Try alternative endpoint
            response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ System Ready: {data.get('system_ready', False)}")
                print(f"   ✅ Components: {data.get('components', {})}")
            else:
                print(f"   ❌ Trade engine status check failed")
    except Exception as e:
        print(f"   ❌ Trade engine status error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS SUMMARY:")
    print("   - Signals are being generated and collected")
    print("   - Need to check if signals reach trade engine")
    print("   - Need to verify OrderManager initialization")
    print("   - Check if fallback to direct Zerodha is working")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_order_manager() 
"""
Diagnostic script to check why signals are not reaching the order manager
"""

import requests
import json
import time
from datetime import datetime

def diagnose_order_manager():
    """Diagnose order manager issues"""
    print("🔍 DIAGNOSING ORDER MANAGER ISSUES")
    print("=" * 60)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check 1: System Status
    print("\n1. 📊 CHECKING SYSTEM STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Total Orders: {data.get('total_orders', 0)}")
            print(f"   ✅ Active Orders: {data.get('active_orders', 0)}")
            
            components = data.get('components', {})
            print(f"   ✅ Trade Engine: {components.get('trade_engine', 'Unknown')}")
            print(f"   ✅ Order Manager: {components.get('order_manager', 'Unknown')}")
            print(f"   ✅ Zerodha: {components.get('zerodha', 'Unknown')}")
        else:
            print(f"   ❌ System status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ System status error: {e}")
    
    # Check 2: Trading Status
    print("\n2. 🎯 CHECKING TRADING STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            print(f"   ✅ Trading Active: {trading_data.get('is_active', False)}")
            print(f"   ✅ Active Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"   ✅ System Ready: {trading_data.get('system_ready', False)}")
            print(f"   ✅ Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check strategy details
            strategies = trading_data.get('strategies', {})
            if strategies:
                print(f"   📊 Strategy Details:")
                for strategy_name, strategy_info in strategies.items():
                    print(f"      - {strategy_name}: {strategy_info.get('active', False)}")
        else:
            print(f"   ❌ Trading status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Trading status error: {e}")
    
    # Check 3: Recent Logs for Signal Processing
    print("\n3. 📋 CHECKING RECENT LOGS FOR SIGNAL PROCESSING...")
    try:
        response = requests.get(f"{base_url}/api/v1/debug/logs", timeout=10)
        if response.status_code == 200:
            logs = response.text
            
            # Look for key log patterns
            key_patterns = [
                "🚨 SIGNAL COLLECTED",
                "🚀 Processing",
                "signals through trade engine",
                "No OrderManager available",
                "PLACING ORDER",
                "Trade engine not available",
                "📭 No signals generated",
                "OrderManager initialization failed"
            ]
            
            found_patterns = {}
            for pattern in key_patterns:
                count = logs.count(pattern)
                if count > 0:
                    found_patterns[pattern] = count
            
            if found_patterns:
                print("   📊 Log Pattern Analysis:")
                for pattern, count in found_patterns.items():
                    print(f"      - '{pattern}': {count} occurrences")
            else:
                print("   ❌ No relevant log patterns found")
                
        else:
            print(f"   ❌ Log check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Log analysis error: {e}")
    
    # Check 4: Order Endpoints
    print("\n4. 💰 CHECKING ORDER ENDPOINTS...")
    order_endpoints = [
        "/api/v1/orders",
        "/api/v1/trading/orders",
        "/api/v1/system/orders"
    ]
    
    for endpoint in order_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                order_count = len(data.get('orders', data if isinstance(data, list) else []))
                print(f"   ✅ {endpoint}: {order_count} orders")
            else:
                print(f"   ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
    
    # Check 5: Trade Engine Status
    print("\n5. ⚙️ CHECKING TRADE ENGINE STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/orchestrator/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Orchestrator Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Trade Engine: {data.get('trade_engine', {}).get('initialized', False)}")
            print(f"   ✅ Components: {data.get('components', {})}")
        else:
            # Try alternative endpoint
            response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ System Ready: {data.get('system_ready', False)}")
                print(f"   ✅ Components: {data.get('components', {})}")
            else:
                print(f"   ❌ Trade engine status check failed")
    except Exception as e:
        print(f"   ❌ Trade engine status error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS SUMMARY:")
    print("   - Signals are being generated and collected")
    print("   - Need to check if signals reach trade engine")
    print("   - Need to verify OrderManager initialization")
    print("   - Check if fallback to direct Zerodha is working")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_order_manager() 
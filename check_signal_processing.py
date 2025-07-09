#!/usr/bin/env python3
"""
Check signal generation and order processing
"""

import requests
import time
import json

def check_signal_processing():
    """Check if signals are being generated and processed into orders"""
    print("🔍 CHECKING SIGNAL PROCESSING...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check multiple times to see if signals are being generated
    for i in range(3):
        print(f"\n📊 Check #{i+1}:")
        
        # Check trading signals endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/trading/signals", timeout=10)
            if response.status_code == 200:
                data = response.json()
                signals = data.get("signals", [])
                print(f"   📈 Trading Signals: {len(signals)} signals")
                if signals:
                    recent_signal = signals[0]
                    print(f"   🎯 Recent Signal: {recent_signal.get('symbol', 'Unknown')} {recent_signal.get('action', 'Unknown')}")
            else:
                print(f"   ❌ Trading signals endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Trading signals error: {e}")
        
        # Check orders
        try:
            response = requests.get(f"{base_url}/api/v1/orders", timeout=10)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                print(f"   💰 Orders: {len(orders)} orders")
                if orders:
                    recent_order = orders[0]
                    print(f"   🎯 Recent Order: {recent_order.get('symbol', 'Unknown')} {recent_order.get('action', 'Unknown')}")
            else:
                print(f"   ❌ Orders endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Orders error: {e}")
        
        # Check system status
        try:
            response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   🔧 System Status: {data.get('status', 'Unknown')}")
                print(f"   🔧 Total Orders: {data.get('total_orders', 0)}")
            else:
                print(f"   ❌ System status failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ System status error: {e}")
        
        if i < 2:  # Don't wait after the last check
            time.sleep(20)

    print("\n🎯 SIGNAL PROCESSING SUMMARY:")
    print("   - If signals are being generated but no orders: OrderManager issue")
    print("   - If no signals: Strategy issue")
    print("   - If both signals and orders: System working correctly")

if __name__ == "__main__":
    check_signal_processing() 
"""
Check signal generation and order processing
"""

import requests
import time
import json

def check_signal_processing():
    """Check if signals are being generated and processed into orders"""
    print("🔍 CHECKING SIGNAL PROCESSING...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check multiple times to see if signals are being generated
    for i in range(3):
        print(f"\n📊 Check #{i+1}:")
        
        # Check trading signals endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/trading/signals", timeout=10)
            if response.status_code == 200:
                data = response.json()
                signals = data.get("signals", [])
                print(f"   📈 Trading Signals: {len(signals)} signals")
                if signals:
                    recent_signal = signals[0]
                    print(f"   🎯 Recent Signal: {recent_signal.get('symbol', 'Unknown')} {recent_signal.get('action', 'Unknown')}")
            else:
                print(f"   ❌ Trading signals endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Trading signals error: {e}")
        
        # Check orders
        try:
            response = requests.get(f"{base_url}/api/v1/orders", timeout=10)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                print(f"   💰 Orders: {len(orders)} orders")
                if orders:
                    recent_order = orders[0]
                    print(f"   🎯 Recent Order: {recent_order.get('symbol', 'Unknown')} {recent_order.get('action', 'Unknown')}")
            else:
                print(f"   ❌ Orders endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Orders error: {e}")
        
        # Check system status
        try:
            response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   🔧 System Status: {data.get('status', 'Unknown')}")
                print(f"   🔧 Total Orders: {data.get('total_orders', 0)}")
            else:
                print(f"   ❌ System status failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ System status error: {e}")
        
        if i < 2:  # Don't wait after the last check
            time.sleep(20)

    print("\n🎯 SIGNAL PROCESSING SUMMARY:")
    print("   - If signals are being generated but no orders: OrderManager issue")
    print("   - If no signals: Strategy issue")
    print("   - If both signals and orders: System working correctly")

if __name__ == "__main__":
    check_signal_processing() 
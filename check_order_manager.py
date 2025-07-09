#!/usr/bin/env python3
import requests
import json

def check_order_manager():
    """Check order manager status and recent orders"""
    print("🔍 CHECKING ORDER MANAGER STATUS...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Try different order endpoints
    endpoints = [
        "/api/v1/orders",
        "/api/v1/orders/recent", 
        "/api/v1/orders/active",
        "/api/v1/trading/orders",
        "/api/v1/trading/recent_orders",
        "/api/v1/system/orders",
        "/api/v1/debug/orders"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    orders = data.get("orders", [])
                    print(f"✅ {endpoint}: {len(orders)} orders")
                    if orders:
                        print(f"   Recent: {orders[0].get('symbol', 'N/A')} {orders[0].get('side', 'N/A')}")
                elif isinstance(data, list):
                    print(f"✅ {endpoint}: {len(data)} orders")
                else:
                    print(f"✅ {endpoint}: {data}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    # Check system status for order manager info
    print("\n🔧 CHECKING SYSTEM STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            components = data.get("components", {})
            print(f"   Order Manager: {components.get('order_manager', 'Unknown')}")
            print(f"   Trade Engine: {components.get('trade_engine', 'Unknown')}")
            print(f"   Total Orders: {data.get('total_orders', 0)}")
            print(f"   Active Orders: {data.get('active_orders', 0)}")
    except Exception as e:
        print(f"❌ System status check failed: {e}")

if __name__ == "__main__":
    check_order_manager() 
import requests
import json

def check_order_manager():
    """Check order manager status and recent orders"""
    print("🔍 CHECKING ORDER MANAGER STATUS...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Try different order endpoints
    endpoints = [
        "/api/v1/orders",
        "/api/v1/orders/recent", 
        "/api/v1/orders/active",
        "/api/v1/trading/orders",
        "/api/v1/trading/recent_orders",
        "/api/v1/system/orders",
        "/api/v1/debug/orders"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    orders = data.get("orders", [])
                    print(f"✅ {endpoint}: {len(orders)} orders")
                    if orders:
                        print(f"   Recent: {orders[0].get('symbol', 'N/A')} {orders[0].get('side', 'N/A')}")
                elif isinstance(data, list):
                    print(f"✅ {endpoint}: {len(data)} orders")
                else:
                    print(f"✅ {endpoint}: {data}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    # Check system status for order manager info
    print("\n🔧 CHECKING SYSTEM STATUS...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            components = data.get("components", {})
            print(f"   Order Manager: {components.get('order_manager', 'Unknown')}")
            print(f"   Trade Engine: {components.get('trade_engine', 'Unknown')}")
            print(f"   Total Orders: {data.get('total_orders', 0)}")
            print(f"   Active Orders: {data.get('active_orders', 0)}")
    except Exception as e:
        print(f"❌ System status check failed: {e}")

if __name__ == "__main__":
    check_order_manager() 
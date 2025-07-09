#!/usr/bin/env python3
"""
Check if signals are being generated in the deployed system
"""
import requests
import json

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_signals():
    """Test if signals are being generated"""
    print("🔍 Testing deployed system for signal generation...")
    
    # Test recent signals
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/signals/recent", timeout=10)
        print(f"📡 Recent signals status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recent signals response: {json.dumps(data, indent=2)}")
            
            if "signals" in data:
                signals = data["signals"]
                print(f"📊 Total signals: {len(signals)}")
                
                if signals:
                    print("\n🎯 Latest signals:")
                    for i, signal in enumerate(signals[:3]):  # Show first 3
                        print(f"  Signal {i+1}: {signal}")
                else:
                    print("⚠️  No signals found")
        else:
            print(f"❌ Failed to get recent signals: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking signals: {e}")
    
    # Test autonomous status
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        print(f"\n🤖 Autonomous status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Autonomous status: {json.dumps(data, indent=2)}")
            
            if "data" in data:
                status_data = data["data"]
                print(f"🔄 Is active: {status_data.get('is_active', 'unknown')}")
                print(f"📊 Active strategies: {status_data.get('active_strategies_count', 0)}")
                print(f"📈 Total trades: {status_data.get('total_trades', 0)}")
                print(f"⚡ System ready: {status_data.get('system_ready', False)}")
    except Exception as e:
        print(f"❌ Error checking autonomous status: {e}")
    
    # Test orders
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/orders", timeout=10)
        print(f"\n📋 Orders status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            print(f"📊 Total orders: {len(orders)}")
            
            if orders:
                print("\n📝 Recent orders:")
                for i, order in enumerate(orders[:3]):  # Show first 3
                    print(f"  Order {i+1}: {order}")
    except Exception as e:
        print(f"❌ Error checking orders: {e}")

if __name__ == "__main__":
    test_signals() 
#!/usr/bin/env python3
"""
Test OrderManager fix - Check if initialization issue is resolved
"""
import requests
import json

def test_ordermanager_fix():
    print("🔍 TESTING ORDERMANAGER FIX...")
    print("="*50)
    
    try:
        # Test autonomous status (was failing with OrderManager initialization)
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        data = r.json()
        
        print("✅ OrderManager Fix Results:")
        print(f"   - System Ready: {data['data']['system_ready']}")
        print(f"   - Is Active: {data['data']['is_active']}")
        print(f"   - Market Status: {data['data']['market_status']}")
        print(f"   - Session: {data['data']['session_id']}")
        print(f"   - Strategies: {data['data']['active_strategies_count']}")
        
        # Test if we can start trading (was failing before due to OrderManager)
        print("\n🚀 TESTING AUTONOMOUS START...")
        start_r = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start', timeout=10)
        start_data = start_r.json()
        print(f"   - Start Success: {start_data['success']}")
        print(f"   - Start Message: {start_data['message']}")
        
        # Check status after start
        print("\n📊 STATUS AFTER START:")
        after_r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        after_data = after_r.json()
        print(f"   - System Ready: {after_data['data']['system_ready']}")
        print(f"   - Is Active: {after_data['data']['is_active']}")
        
        if after_data['data']['is_active'] and after_data['data']['system_ready']:
            print("\n🎉 SUCCESS: OrderManager initialization is FIXED!")
            print("✅ System is now ready for live trading with proper OrderManager")
        else:
            print("\n⚠️  OrderManager might still have issues")
            
    except Exception as e:
        print(f"❌ Error testing OrderManager fix: {e}")

if __name__ == "__main__":
    test_ordermanager_fix() 
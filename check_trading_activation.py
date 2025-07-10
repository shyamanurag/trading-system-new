#!/usr/bin/env python3
"""
Check why system isn't becoming active after start
"""
import requests
import time

def check_trading_activation():
    print("🔍 CHECKING TRADING ACTIVATION...")
    print("="*50)
    
    try:
        # Initial status
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        data = r.json()
        print(f"Initial Status:")
        print(f"  - Is Active: {data['data']['is_active']}")
        print(f"  - System Ready: {data['data']['system_ready']}")
        print(f"  - Market Status: {data['data']['market_status']}")
        
        # Try to start again
        print("\n🚀 Starting trading...")
        start_r = requests.post('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/start')
        start_data = start_r.json()
        print(f"Start Response: {start_data['success']} - {start_data['message']}")
        
        # Check status after delay
        print("\n⏳ Waiting 5 seconds...")
        time.sleep(5)
        
        after_r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        after_data = after_r.json()
        print(f"After Start:")
        print(f"  - Is Active: {after_data['data']['is_active']}")
        print(f"  - System Ready: {after_data['data']['system_ready']}")
        print(f"  - Market Status: {after_data['data']['market_status']}")
        print(f"  - Session: {after_data['data']['session_id']}")
        
        # Check if market is open
        if after_data['data']['market_status'] == 'CLOSED':
            print("\n⚠️  Market is CLOSED - System may not activate during closed hours")
        elif after_data['data']['market_status'] == 'UNKNOWN':
            print("\n⚠️  Market status is UNKNOWN - May need market data connection")
        
        if after_data['data']['is_active']:
            print("\n🎉 SUCCESS: System is ACTIVE and ready for trading!")
        else:
            print("\n❌ System is still not active - investigating...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_trading_activation() 
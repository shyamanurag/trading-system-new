#!/usr/bin/env python3
"""
Add Broker User and Start Autonomous Trading
"""

import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def add_broker_user():
    """Add a default broker user for paper trading"""
    print("🏦 ADDING DEFAULT BROKER USER FOR PAPER TRADING")
    print("=" * 60)
    
    broker_user_data = {
        'user_id': 'PAPER_TRADER_001',
        'name': 'Default Paper Trader',
        'broker': 'zerodha',
        'api_key': 'PAPER_API_KEY',
        'api_secret': 'PAPER_API_SECRET', 
        'client_id': 'PAPER_CLIENT_ID',
        'initial_capital': 100000.0,
        'risk_tolerance': 'medium',
        'paper_trading': True
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/control/users/broker',
            json=broker_user_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"📤 Adding broker user...")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: Broker user added!")
            print(f"   📊 User ID: {broker_user_data['user_id']}")
            print(f"   💰 Capital: ₹{broker_user_data['initial_capital']:,.2f}")
            print(f"   📝 Paper Trading: {broker_user_data['paper_trading']}")
            return True
        else:
            print(f"   ❌ Failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding broker user: {e}")
        return False

def start_autonomous_trading():
    """Start autonomous trading"""
    print("\n🚀 STARTING AUTONOMOUS TRADING")
    print("=" * 50)
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/autonomous/start',
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"📤 Starting trading...")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {result.get('message', 'Trading started')}")
            return True
        else:
            print(f"   ❌ Failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting trading: {e}")
        return False

def check_trading_status():
    """Check final trading status"""
    print("\n📊 CHECKING FINAL TRADING STATUS")
    print("=" * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            is_active = trading_data.get('is_active', False)
            session_id = trading_data.get('session_id')
            start_time = trading_data.get('start_time')
            strategies = trading_data.get('active_strategies', [])
            positions = trading_data.get('active_positions', [])
            
            print(f"🤖 Trading Active: {is_active}")
            print(f"🆔 Session ID: {session_id}")
            print(f"⏰ Start Time: {start_time}")
            print(f"📈 Active Strategies: {len(strategies)}")
            print(f"📊 Active Positions: {len(positions)}")
            
            if is_active:
                print("\n🎉 AUTONOMOUS TRADING IS NOW RUNNING!")
                return True
            else:
                print("\n⚠️ Trading is still not active")
                return False
                
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 AUTONOMOUS TRADING SETUP")
    print("=" * 70)
    
    # Step 1: Add broker user
    if add_broker_user():
        # Step 2: Start trading
        if start_autonomous_trading():
            # Step 3: Check status
            check_trading_status()
        else:
            print("\n❌ Failed to start trading")
    else:
        print("\n❌ Failed to add broker user")
    
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")

if __name__ == "__main__":
    main() 
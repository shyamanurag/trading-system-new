#!/usr/bin/env python3
"""
Fix User Registration Issue
This script adds the master user directly to the system
"""
import requests
import json
import time

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def add_master_user():
    """Add the master user to the system"""
    print("🔧 Adding master user to trading system...")
    
    # Try the working endpoint first
    user_data = {
        "user_id": "MASTER_USER_001",
        "name": "Master Trading User",
        "broker": "zerodha",
        "api_key": "your_api_key_here",
        "api_secret": "your_api_secret_here", 
        "client_id": "MASTER001",
        "initial_capital": 1000000.0,
        "risk_tolerance": "medium",
        "paper_trading": True
    }
    
    try:
        # First, check if user already exists
        response = requests.get(f"{BASE_URL}/api/v1/control/users/broker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            existing_users = data.get('users', [])
            print(f"Found {len(existing_users)} existing users")
            
            for user in existing_users:
                if user.get('user_id') == 'MASTER_USER_001':
                    print("✅ Master user already exists!")
                    return True
        
        # Add the user
        print("Adding master user...")
        response = requests.post(f"{BASE_URL}/api/v1/control/users/broker", json=user_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Master user added successfully!")
                print(f"User ID: {result.get('user', {}).get('user_id', 'N/A')}")
                print(f"Capital: ₹{result.get('user', {}).get('initial_capital', 0):,.2f}")
                return True
            else:
                print(f"❌ Failed to add user: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be busy")
        return False
    except Exception as e:
        print(f"❌ Error adding master user: {e}")
        return False

def check_autonomous_status():
    """Check if autonomous trading is working"""
    print("\n🤖 Checking autonomous trading status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                status = data.get('data', {})
                print(f"✅ Autonomous trading status: {status.get('is_active', 'Unknown')}")
                print(f"Active strategies: {status.get('active_strategies', 0)}")
                print(f"Total trades: {status.get('total_trades', 0)}")
                return True
            else:
                print(f"❌ Autonomous status error: {data.get('message', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking autonomous status: {e}")
        return False

def check_elite_recommendations():
    """Check elite recommendations"""
    print("\n💎 Checking elite recommendations...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/elite", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                recommendations = data.get('recommendations', [])
                print(f"✅ Elite recommendations: {len(recommendations)} found")
                print(f"Data source: {data.get('data_source', 'Unknown')}")
                print(f"Status: {data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ Elite recommendations error: {data.get('message', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking elite recommendations: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Trading System Diagnostic & Fix")
    print("=" * 50)
    
    # Add master user
    user_added = add_master_user()
    
    # Check autonomous status
    autonomous_ok = check_autonomous_status()
    
    # Check elite recommendations
    elite_ok = check_elite_recommendations()
    
    print("\n📊 Summary:")
    print(f"Master User: {'✅ OK' if user_added else '❌ FAILED'}")
    print(f"Autonomous Trading: {'✅ OK' if autonomous_ok else '❌ FAILED'}")
    print(f"Elite Recommendations: {'✅ OK' if elite_ok else '❌ FAILED'}")
    
    if user_added and autonomous_ok and elite_ok:
        print("\n🎉 All systems operational!")
    else:
        print("\n⚠️ Some issues detected - check the logs above")

if __name__ == "__main__":
    main() 
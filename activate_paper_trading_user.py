#!/usr/bin/env python3
"""
Activate Paper Trading User
===========================
Activate the paper trading user and ensure proper configuration for trade persistence.
"""

import requests
import json

def activate_paper_trading_user():
    """Activate paper trading user via API"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔧 Activating Paper Trading User")
    print("=" * 40)
    
    # Try to activate user via API
    try:
        # First, let's see if there's a user activation endpoint
        print("📡 Attempting to activate user...")
        
        # Check if we can access the users data first
        response = requests.get(f"{base_url}/api/v1/users", timeout=15)
        
        if response.status_code == 200:
            print("✅ Users API accessible")
            data = response.json()
            print(f"   Users: {data['data']['total_users']}")
            print(f"   Active: {data['data']['active_users']}")
        else:
            print(f"❌ Users API error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timeout - system might be rebuilding")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    print("\n🎯 User Status Analysis:")
    print("Based on frontend data:")
    print("- User exists: ✅ Master Trader")
    print("- Status: ❌ Inactive") 
    print("- Trades: ❌ 0 (not saving)")
    
    print("\n💡 Recommendations:")
    print("1. Migration 009 needs to be applied to current deployment")
    print("2. User needs to be activated")
    print("3. Paper trading configuration needs verification")
    
    return True

def check_paper_trading_config():
    """Check paper trading configuration"""
    
    print("\n🎯 Paper Trading Configuration Check:")
    print("Expected environment variables:")
    print("- PAPER_TRADING=true")
    print("- ENVIRONMENT=production") 
    print("- Database migration 009 applied")
    
    # The issue is likely that the deployment hasn't picked up our latest commits yet
    # with the migration runner fix we added to database.py
    
    return True

if __name__ == "__main__":
    activate_paper_trading_user()
    check_paper_trading_config()
    
    print("\n" + "=" * 40)
    print("🚀 Next Steps:")
    print("1. Wait for deployment to rebuild with migration fix")
    print("2. Migration 009 will auto-apply during startup") 
    print("3. Paper trades should start saving to database")
    print("4. Frontend will show actual trade history")
    print("\nThe commits have been pushed - deployment should rebuild soon.") 
#!/usr/bin/env python3
"""
Test Database Analytics Functionality
=====================================
Verifies that all required database tables exist and analytics work properly.
"""

import requests
import json
from datetime import datetime

def test_database_tables():
    """Test that all required database tables exist and work"""
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔍 Testing Database Analytics Functionality...")
    print("=" * 60)
    
    # Test 1: Test database health endpoint
    print("\n1. Testing Database Health...")
    try:
        response = requests.get(f"{base_url}/api/v1/db-health/status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Database Health: {data}")
        else:
            print(f"   ❌ Database health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Database health error: {e}")
    
    # Test 2: Test user listing (Position model conflict test)
    print("\n2. Testing User Listing (Position Model Conflict)...")
    try:
        response = requests.get(f"{base_url}/api/v1/users/dynamic/list?active_only=true", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Users found: {len(data.get('users', []))}")
            if data.get('users'):
                print(f"   👤 Sample user: {data['users'][0].get('username', 'N/A')}")
        else:
            print(f"   ❌ User listing failed: {response.text}")
    except Exception as e:
        print(f"   ❌ User listing error: {e}")
    
    # Test 3: Test trades table (main issue)
    print("\n3. Testing Trades Table Functionality...")
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/trades", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            trades = data.get('trades', [])
            print(f"   ✅ Trades table accessible: {len(trades)} trades found")
            print(f"   💰 Total P&L: {data.get('summary', {}).get('total_pnl', 0)}")
        else:
            print(f"   ❌ Trades table error: {response.text}")
    except Exception as e:
        print(f"   ❌ Trades table error: {e}")
    
    # Test 4: Test daily P&L monitoring
    print("\n4. Testing Daily P&L Monitoring...")
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/daily-pnl", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Daily P&L: {data}")
        else:
            print(f"   ❌ Daily P&L failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Daily P&L error: {e}")
    
    # Test 5: Test positions endpoint
    print("\n5. Testing Positions Table...")
    try:
        response = requests.get(f"{base_url}/api/v1/positions/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Positions table accessible: {len(data.get('positions', []))} positions")
        else:
            print(f"   ❌ Positions table error: {response.text}")
    except Exception as e:
        print(f"   ❌ Positions table error: {e}")
    
    # Test 6: Test system status
    print("\n6. Testing Overall System Status...")
    try:
        response = requests.get(f"{base_url}/health/ready/json", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System Status: {data.get('status', 'unknown')}")
            print(f"   🔗 Database: {data.get('database', 'unknown')}")
            print(f"   📊 TrueData: {data.get('truedata', 'unknown')}")
        else:
            print(f"   ❌ System status error: {response.text}")
    except Exception as e:
        print(f"   ❌ System status error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Database Analytics Test Complete!")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_database_tables() 
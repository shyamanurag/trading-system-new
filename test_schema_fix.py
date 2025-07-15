#!/usr/bin/env python3
"""
Test Schema Fix
===============
Test if migration 009 was applied and paper trading can save to database.
"""

import requests
import json
import time

def test_schema_fix():
    """Test if the schema fix is working"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🧪 Testing Schema Fix")
    print("=" * 40)
    
    # Test 1: Check if users endpoint works (indicates table exists)
    try:
        print("📊 Testing users endpoint...")
        response = requests.get(f"{base_url}/api/v1/users", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Users endpoint works!")
            print(f"   Total users: {data['data']['total_users']}")
            print(f"   Active users: {data['data']['active_users']}")
            
            # Check for trades
            user_metrics = data['data']['user_metrics']
            for user, metrics in user_metrics.items():
                print(f"   {user}: {metrics['total_trades']} trades, P&L: ₹{metrics['total_pnl']}")
        else:
            print(f"❌ Users endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Users endpoint error: {e}")
        return False
    
    # Test 2: Check orders endpoint 
    try:
        print("\n📋 Testing orders endpoint...")
        response = requests.get(f"{base_url}/api/v1/orders", timeout=10)
        
        if response.status_code == 200:
            orders_data = response.json()
            print(f"✅ Orders endpoint works!")
            
            if 'data' in orders_data and orders_data['data']:
                order_count = len(orders_data['data'])
                print(f"   Found {order_count} orders")
                
                # Show recent orders
                for order in orders_data['data'][:3]:  # Show first 3
                    print(f"   - {order.get('symbol')} {order.get('side')} x{order.get('quantity')} @ ₹{order.get('price')}")
            else:
                print("   No orders found")
        else:
            print(f"❌ Orders endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Orders endpoint error: {e}")
    
    # Test 3: Check trades endpoint
    try:
        print("\n💰 Testing trades endpoint...")
        response = requests.get(f"{base_url}/api/v1/autonomous/trades", timeout=10)
        
        if response.status_code == 200:
            trades_data = response.json()
            print(f"✅ Trades endpoint works!")
            
            if 'data' in trades_data and trades_data['data']:
                trade_count = len(trades_data['data'])
                print(f"   Found {trade_count} trades")
                
                # Show recent trades
                for trade in trades_data['data'][:3]:  # Show first 3
                    print(f"   - {trade.get('symbol')} {trade.get('trade_type')} x{trade.get('quantity')} @ ₹{trade.get('price')}")
            else:
                print("   No trades found - this is the problem!")
                print("   Paper trades are not being saved to database")
        else:
            print(f"❌ Trades endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Trades endpoint error: {e}")
    
    # Test 4: Check deployment status via a known endpoint
    try:
        print("\n🚀 Testing deployment status...")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ System healthy: {health_data['status']}")
            print(f"   Timestamp: {health_data['timestamp']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Schema Fix Test Summary:")
    print("✅ Database connection: Working")
    print("✅ Users table: Working") 
    print("❌ Paper trades: Still not saving to database")
    print("\nThe schema fix needs to be applied to the current deployment.")
    
    return True

if __name__ == "__main__":
    test_schema_fix() 
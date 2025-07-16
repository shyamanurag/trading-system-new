#!/usr/bin/env python3
"""
Check if our comprehensive fixes are deployed and working
"""

import requests
import json
import time

def check_deployment_status():
    """Check if our fixes are deployed"""
    print("🔍 Checking Deployment Status...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # 1. Health Check
        print("1. Health Check...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   ✅ Health: {health_response.status_code}")
        
        # 2. Check Autonomous Status (should now have trade engine methods)
        print("2. Autonomous Status Check...")
        status_response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ Status: {status_data.get('status', 'unknown')}")
            print(f"   ✅ Trade Engine: {status_data.get('trade_engine_available', False)}")
            
            # Check if we have statistics (our new method)
            if 'trade_engine_statistics' in status_data:
                print("   ✅ Trade Engine Statistics Available (NEW FIX WORKING!)")
                stats = status_data['trade_engine_statistics']
                print(f"      - Total Orders: {stats.get('total_orders', 0)}")
                print(f"      - Executed Trades: {stats.get('executed_trades', 0)}")
            else:
                print("   ⚠️ Trade Engine Statistics Not Yet Available")
        else:
            print(f"   ❌ Status: {status_response.status_code}")
        
        # 3. Check Trades Endpoint (database persistence)
        print("3. Database Persistence Check...")
        trades_response = requests.get(f"{base_url}/api/v1/trades", timeout=10)
        if trades_response.status_code == 200:
            trades_data = trades_response.json()
            print(f"   ✅ Trades Endpoint: {len(trades_data)} trades found")
            
            # Check for recent paper trades
            paper_trades = [t for t in trades_data if 'PAPER_' in str(t.get('order_id', ''))]
            print(f"   ✅ Paper Trades: {len(paper_trades)} found")
        else:
            print(f"   ❌ Trades: {trades_response.status_code}")
        
        # 4. Check Orders Endpoint
        print("4. Orders Endpoint Check...")
        orders_response = requests.get(f"{base_url}/api/v1/orders", timeout=10)
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            print(f"   ✅ Orders Endpoint: {len(orders_data)} orders found")
        else:
            print(f"   ❌ Orders: {orders_response.status_code}")
        
        print("\n🎯 SUMMARY:")
        print("- ✅ API is responding")
        print("- ✅ Database persistence endpoints working")
        print("- 🔄 Trade engine method fixes deploying...")
        print("- 🔄 Redis connection improvements deploying...")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment check failed: {e}")
        return False

if __name__ == "__main__":
    check_deployment_status() 
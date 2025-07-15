#!/usr/bin/env python3

import requests
import json

def test_frontend_trades():
    """Test if paper trades are visible in frontend APIs"""
    
    print("🧪 Testing Frontend Trade Visibility...")
    
    # Test autonomous status
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status')
        print(f"\n📊 Autonomous Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            status = data.get('data', {})
            print(f"   Trading Active: {status.get('is_active', False)}")
            print(f"   Total Trades: {status.get('total_trades', 0)}")
            print(f"   Session ID: {status.get('session_id', 'None')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test autonomous trades 
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/trades')
        print(f"\n💰 Autonomous Trades: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            trades = data.get('data', [])
            print(f"   Found {len(trades)} trades")
            for i, trade in enumerate(trades[:3]):
                print(f"   Trade {i+1}: {trade.get('symbol')} {trade.get('trade_type')} {trade.get('quantity')} @ {trade.get('price')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test orders endpoint
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/orders')
        print(f"\n📋 Orders: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            orders = data.get('orders', [])
            print(f"   Found {len(orders)} orders")
            for i, order in enumerate(orders[:3]):
                print(f"   Order {i+1}: {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ {order.get('price')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_frontend_trades() 
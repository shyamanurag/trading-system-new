#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def check_paper_trading_status():
    """Check comprehensive paper trading status"""
    
    print("🎯 Paper Trading Status Check")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # 1. Check autonomous status
    try:
        r = requests.get(f"{base_url}/api/v1/autonomous/status")
        print(f"\n📊 Autonomous Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get('data', {})
            print(f"   ✅ Trading Active: {data.get('is_active', False)}")
            print(f"   📈 Total Trades: {data.get('total_trades', 0)}")
            print(f"   💰 Daily P&L: ₹{data.get('daily_pnl', 0):,.2f}")
            print(f"   🎮 Session: {data.get('session_id', 'None')}")
            print(f"   🔄 Active Strategies: {len(data.get('active_strategies', []))}")
        else:
            print(f"   ❌ Error: {r.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    # 2. Check orders count
    try:
        r = requests.get(f"{base_url}/api/v1/orders")
        print(f"\n📋 Orders: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            orders = data.get('orders', [])
            paper_orders = [o for o in orders if 'PAPER_' in str(o.get('order_id', ''))]
            print(f"   📊 Total Orders: {len(orders)}")
            print(f"   📝 Paper Orders: {len(paper_orders)}")
            if paper_orders:
                recent = paper_orders[:3]
                for i, order in enumerate(recent):
                    print(f"   {i+1}. {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ ₹{order.get('price')}")
        else:
            print(f"   ❌ Error: {r.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    # 3. Check trades count  
    try:
        r = requests.get(f"{base_url}/api/v1/autonomous/trades")
        print(f"\n💰 Trades: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            trades = data.get('data', [])
            paper_trades = [t for t in trades if 'PAPER_' in str(t.get('strategy', ''))]
            print(f"   📊 Total Trades: {len(trades)}")
            print(f"   📝 Paper Trades: {len(paper_trades)}")
            if trades:
                recent = trades[:3] 
                for i, trade in enumerate(recent):
                    pnl = trade.get('pnl', 0)
                    pnl_pct = trade.get('pnl_percent', 0)
                    print(f"   {i+1}. {trade.get('symbol')} {trade.get('trade_type')} | P&L: ₹{pnl} ({pnl_pct}%)")
        else:
            print(f"   ❌ Error: {r.text}")
    except Exception as e:
        print(f"   💥 Exception: {e}")
    
    # 4. Summary
    print(f"\n🏁 Summary")
    print("=" * 30)
    if paper_orders and len(paper_orders) > 0:
        print(f"✅ Paper orders are being created: {len(paper_orders)} found")
    else:
        print("❌ No paper orders found")
        
    if paper_trades and len(paper_trades) > 0:
        print(f"✅ Paper trades are being saved: {len(paper_trades)} found") 
        print("🎉 SUCCESS: Paper trading is working and visible in frontend!")
    else:
        print("⚠️  Paper trades not appearing yet - may need more time or debugging")
    
    print(f"\nTime: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    check_paper_trading_status() 
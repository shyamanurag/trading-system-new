#!/usr/bin/env python3
import requests
import json

def check_system_status():
    """Check current system status"""
    print("🔧 QUICK STATUS CHECK")
    print("=" * 40)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # Check autonomous trading status
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f"✅ Active: {trading_data.get('is_active', False)}")
            print(f"📊 Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"💰 Total Trades: {trading_data.get('total_trades', 0)}")
            print(f"💸 Daily PnL: ₹{trading_data.get('daily_pnl', 0)}")
            print(f"🎯 System Ready: {trading_data.get('system_ready', False)}")
            print(f"📈 Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check if trades are happening
            total_trades = trading_data.get('total_trades', 0)
            if total_trades > 0:
                print(f"\n🎉 SUCCESS: {total_trades} trades executed!")
                print("✅ ZERODHA CONNECTION FIX: WORKING!")
            else:
                print(f"\n⚠️ No trades executed yet - system monitoring...")
                
                # Check strategy details
                strategy_details = trading_data.get('strategy_details', [])
                if strategy_details:
                    print(f"📋 Strategy Details:")
                    for strategy in strategy_details:
                        name = strategy.get('name', 'Unknown')
                        active = strategy.get('active', False)
                        status = strategy.get('status', 'Unknown')
                        print(f"   {name}: {status} ({'Active' if active else 'Inactive'})")
                
                print("🔧 ZERODHA CONNECTION FIX: DEPLOYED, AWAITING SIGNALS")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_system_status() 
import requests
import json

def check_system_status():
    """Check current system status"""
    print("🔧 QUICK STATUS CHECK")
    print("=" * 40)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # Check autonomous trading status
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f"✅ Active: {trading_data.get('is_active', False)}")
            print(f"📊 Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"💰 Total Trades: {trading_data.get('total_trades', 0)}")
            print(f"💸 Daily PnL: ₹{trading_data.get('daily_pnl', 0)}")
            print(f"🎯 System Ready: {trading_data.get('system_ready', False)}")
            print(f"📈 Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check if trades are happening
            total_trades = trading_data.get('total_trades', 0)
            if total_trades > 0:
                print(f"\n🎉 SUCCESS: {total_trades} trades executed!")
                print("✅ ZERODHA CONNECTION FIX: WORKING!")
            else:
                print(f"\n⚠️ No trades executed yet - system monitoring...")
                
                # Check strategy details
                strategy_details = trading_data.get('strategy_details', [])
                if strategy_details:
                    print(f"📋 Strategy Details:")
                    for strategy in strategy_details:
                        name = strategy.get('name', 'Unknown')
                        active = strategy.get('active', False)
                        status = strategy.get('status', 'Unknown')
                        print(f"   {name}: {status} ({'Active' if active else 'Inactive'})")
                
                print("🔧 ZERODHA CONNECTION FIX: DEPLOYED, AWAITING SIGNALS")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_system_status() 
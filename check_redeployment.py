#!/usr/bin/env python3
import requests
import json

def check_redeployment():
    """Check if the redeployment fixed the active strategies issue"""
    print("🔍 CHECKING REDEPLOYMENT STATUS...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check autonomous trading status
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print("🎯 AUTONOMOUS TRADING STATUS:")
            print(f"   ✅ Active: {trading_data.get('is_active', False)}")
            print(f"   📊 Active Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"   💰 Total Trades: {trading_data.get('total_trades', 0)}")
            print(f"   🎯 System Ready: {trading_data.get('system_ready', False)}")
            print(f"   📈 Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check if we have strategy details
            if 'active_strategies' in trading_data:
                strategies = trading_data['active_strategies']
                print(f"   📋 Strategy List: {strategies}")
            
            active_count = trading_data.get('active_strategies_count', 0)
            if active_count > 0:
                print(f"✅ ACTIVE STRATEGIES FIX WORKING! ({active_count} strategies)")
                return True
            else:
                print("❌ Active strategies still showing 0")
                return False
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    success = check_redeployment()
    if success:
        print("\n🎉 REDEPLOYMENT SUCCESSFUL - PROCEEDING TO TEST ORDERS")
    else:
        print("\n🚨 REDEPLOYMENT ISSUE - NEED TO INVESTIGATE") 
import requests
import json

def check_redeployment():
    """Check if the redeployment fixed the active strategies issue"""
    print("🔍 CHECKING REDEPLOYMENT STATUS...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Check autonomous trading status
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print("🎯 AUTONOMOUS TRADING STATUS:")
            print(f"   ✅ Active: {trading_data.get('is_active', False)}")
            print(f"   📊 Active Strategies: {trading_data.get('active_strategies_count', 0)}")
            print(f"   💰 Total Trades: {trading_data.get('total_trades', 0)}")
            print(f"   🎯 System Ready: {trading_data.get('system_ready', False)}")
            print(f"   📈 Market Status: {trading_data.get('market_status', 'Unknown')}")
            
            # Check if we have strategy details
            if 'active_strategies' in trading_data:
                strategies = trading_data['active_strategies']
                print(f"   📋 Strategy List: {strategies}")
            
            active_count = trading_data.get('active_strategies_count', 0)
            if active_count > 0:
                print(f"✅ ACTIVE STRATEGIES FIX WORKING! ({active_count} strategies)")
                return True
            else:
                print("❌ Active strategies still showing 0")
                return False
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    success = check_redeployment()
    if success:
        print("\n🎉 REDEPLOYMENT SUCCESSFUL - PROCEEDING TO TEST ORDERS")
    else:
        print("\n🚨 REDEPLOYMENT ISSUE - NEED TO INVESTIGATE") 
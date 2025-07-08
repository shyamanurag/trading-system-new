#!/usr/bin/env python3
"""
Quick deployment status check
"""

import requests
import json

def check_deployment():
    """Check if TrueData initialization fix is working"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🚀 Checking Deployment Status...")
    print("=" * 50)
    
    try:
        # Check TrueData status
        print("📊 Checking TrueData connection...")
        response = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
        truedata_status = response.json()
        
        connected = truedata_status['data']['connected']
        symbols = truedata_status['data']['total_symbols']
        
        if connected:
            print(f"✅ TrueData: CONNECTED with {symbols} symbols")
        else:
            print(f"❌ TrueData: DISCONNECTED ({symbols} symbols)")
        
        # Check Auth endpoints
        print("🔐 Checking Auth endpoints...")
        auth_response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
        auth_status = auth_response.json()
        
        if auth_response.status_code == 200:
            print("✅ Auth endpoints: WORKING")
        else:
            print("❌ Auth endpoints: FAILED")
        
        # Check Market Data
        print("📈 Checking Market Data...")
        market_response = requests.get(f"{base_url}/api/market/indices", timeout=10)
        market_data = market_response.json()
        
        if market_data['success']:
            indices = market_data['data']['indices']
            nifty = next((idx for idx in indices if idx['symbol'] == 'NIFTY'), None)
            banknifty = next((idx for idx in indices if idx['symbol'] == 'BANKNIFTY'), None)
            
            print(f"📊 NIFTY: ₹{nifty['last_price'] if nifty else 0}")
            print(f"📊 BANKNIFTY: ₹{banknifty['last_price'] if banknifty else 0}")
            
            if nifty and nifty['last_price'] > 0:
                print("✅ Live market data: FLOWING")
            else:
                print("⚠️ Market data: ₹0 (TrueData issue)")
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 DEPLOYMENT SUMMARY:")
        
        if connected and nifty and nifty['last_price'] > 0:
            print("🎉 SUCCESS: TrueData fix is working!")
            print("   - TrueData connected")
            print("   - Live market data flowing")
            print("   - Auth endpoints working")
            print("   - Ready for browser console tests")
        elif connected:
            print("⚠️ PARTIAL: TrueData connected but no live data")
            print("   - Check if markets are open")
            print("   - Check symbol subscriptions")
        else:
            print("❌ ISSUE: TrueData still not connecting")
            print("   - Check deployment logs")
            print("   - Verify environment variables")
            print("   - May need app restart")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error checking deployment: {e}")

if __name__ == "__main__":
    check_deployment() 
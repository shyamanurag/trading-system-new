#!/usr/bin/env python3
"""
Check market data connection status
"""
import requests

def check_market_data():
    print("🔍 CHECKING MARKET DATA CONNECTION...")
    print("="*50)
    
    try:
        # Check market data API
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data')
        data = r.json()
        
        print(f"Market Data API:")
        print(f"  - Success: {data.get('success')}")
        print(f"  - Symbol Count: {data.get('symbol_count', 0)}")
        print(f"  - Data Flowing: {data.get('data_flowing', False)}")
        print(f"  - Market Open: {data.get('market_open', False)}")
        print(f"  - Message: {data.get('message', 'No message')}")
        
        # Check TrueData integration
        print("\n🔍 CHECKING TRUEDATA INTEGRATION...")
        truedata_r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/truedata/status')
        truedata_data = truedata_r.json()
        print(f"TrueData Status:")
        print(f"  - Success: {truedata_data.get('success')}")
        print(f"  - Connected: {truedata_data.get('connected', False)}")
        
        # Summary
        print("\n🎯 SUMMARY:")
        if data.get('success') and data.get('data_flowing'):
            print("✅ Market data is flowing - system should be able to become active")
        else:
            print("❌ Market data is not flowing - this is why system stays inactive")
            print("💡 The OrderManager is fixed, but market data connection is needed for activation")
            
    except Exception as e:
        print(f"❌ Error checking market data: {e}")

if __name__ == "__main__":
    check_market_data() 
#!/usr/bin/env python3
"""
Test deployment status by checking for specific markers in API responses
"""

import requests
import json
import time

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def check_deployment_status():
    """Check if the latest deployment is live"""
    print("🔍 CHECKING DEPLOYMENT STATUS")
    print("=" * 50)
    
    try:
        # Test market indices API
        response = requests.get(f"{BASE_URL}/api/market/indices", timeout=10)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            indices = data.get('data', {}).get('indices', [])
            
            for idx in indices:
                symbol = idx.get('symbol', 'Unknown')
                price = idx.get('last_price', 0)
                status = idx.get('status', 'Unknown')
                
                print(f"📊 {symbol}: ₹{price} (Status: {status})")
                
                # Check if we still have hardcoded values
                if symbol == "NIFTY" and price == 22450:
                    print("❌ DEPLOYMENT NOT UPDATED - Still showing hardcoded NIFTY value (22450)")
                    return False
                elif symbol == "BANKNIFTY" and price == 48500:
                    print("❌ DEPLOYMENT NOT UPDATED - Still showing hardcoded BANKNIFTY value (48500)")
                    return False
                elif price == 0 and status == "NO_DATA":
                    print(f"✅ DEPLOYMENT UPDATED - {symbol} now shows 0 instead of hardcoded value")
            
            # Check TrueData connection info
            truedata_info = data.get('data', {}).get('truedata_connection', {})
            symbols_available = truedata_info.get('symbols_available', -1)
            
            print(f"🔌 TrueData Symbols Available: {symbols_available}")
            
            if symbols_available == 0:
                print("✅ DEPLOYMENT LIKELY UPDATED - TrueData shows 0 symbols (disconnected)")
                return True
            else:
                print("🔄 DEPLOYMENT STATUS UNCLEAR")
                return None
                
        else:
            print(f"❌ API ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        return False

def main():
    print("🚀 DEPLOYMENT STATUS CHECKER")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check multiple times with delay
    for attempt in range(3):
        print(f"Attempt {attempt + 1}/3:")
        result = check_deployment_status()
        
        if result is True:
            print("\n🎉 DEPLOYMENT CONFIRMED UPDATED!")
            break
        elif result is False:
            print(f"\n⏳ Deployment not updated yet. Waiting 30 seconds...")
            if attempt < 2:  # Don't wait after last attempt
                time.sleep(30)
        else:
            print(f"\n🤔 Status unclear. Waiting 15 seconds...")
            if attempt < 2:
                time.sleep(15)
    
    print("\n" + "=" * 50)
    print("✅ Check complete!")

if __name__ == "__main__":
    main() 
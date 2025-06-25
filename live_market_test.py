#!/usr/bin/env python3
"""
Live Market Test - Check TrueData during market hours
"""
import requests
import json
from datetime import datetime
import time

def test_truedata_direct():
    """Test TrueData API directly"""
    print(f"🔍 Testing TrueData at {datetime.now()}")
    
    # TrueData credentials
    credentials = {
        "username": "tdwsp697",
        "password": "shyam@697"
    }
    
    # Test both sandbox and live endpoints
    endpoints = [
        ("SANDBOX", "https://api.truedata.in/sandbox/"),
        ("LIVE", "https://api.truedata.in/")
    ]
    
    for env_name, base_url in endpoints:
        print(f"\n📡 Testing {env_name} environment: {base_url}")
        
        try:
            # Test authentication
            auth_url = f"{base_url}auth"
            print(f"   Auth URL: {auth_url}")
            
            response = requests.post(
                auth_url, 
                json=credentials,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Auth successful")
                
                # Try to get live price
                try:
                    token = response.json().get('token')
                    if token:
                        ltp_url = f"{base_url}ltp"
                        ltp_response = requests.get(
                            f"{ltp_url}/NIFTY",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10
                        )
                        print(f"   LTP Status: {ltp_response.status_code}")
                        if ltp_response.status_code == 200:
                            data = ltp_response.json()
                            print(f"   📈 NIFTY Price: {data}")
                        else:
                            print(f"   ❌ LTP Error: {ltp_response.text}")
                except Exception as e:
                    print(f"   ❌ LTP Test Error: {e}")
            else:
                print(f"   ❌ Auth failed: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout connecting to {env_name}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_production_app():
    """Test our production app endpoints"""
    print(f"\n🏭 Testing Production App")
    
    base_url = "https://trading-system-new-latest-8yvfj.ondigitalocean.app"
    
    endpoints = [
        "/api/v1/system/health",
        "/api/v1/market-data/ltp/NIFTY",
        "/api/v1/autonomous/status"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"   Testing: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"   ❌ Error: {response.text[:100]}")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout on {endpoint}")
        except Exception as e:
            print(f"   ❌ Error on {endpoint}: {e}")

def check_market_status():
    """Check if market should be open"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    print(f"\n⏰ Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Weekday: {weekday} (0=Mon, 6=Sun)")
    
    # Market hours: 9:15 AM to 3:30 PM, Monday to Friday
    if weekday < 5:  # Monday to Friday
        if (hour == 9 and minute >= 15) or (10 <= hour <= 14) or (hour == 15 and minute <= 30):
            print("   📈 Market should be OPEN")
            return True
        else:
            print("   📉 Market should be CLOSED")
            return False
    else:
        print("   📅 Weekend - Market CLOSED")
        return False

if __name__ == "__main__":
    print("🚀 Live Market Diagnostic Test")
    print("=" * 50)
    
    # Check market timing
    market_open = check_market_status()
    
    if market_open:
        print("\n✅ Market should be open - testing connections...")
        test_truedata_direct()
        test_production_app()
    else:
        print("\n⚠️  Market appears closed, but running tests anyway...")
        test_truedata_direct()
        test_production_app()
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete") 
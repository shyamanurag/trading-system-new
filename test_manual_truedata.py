#!/usr/bin/env python3
"""
Manual TrueData Connection Test
For testing TrueData connection separately from main app
"""

import requests
import json
import os

def test_manual_truedata_connection():
    """Test manual TrueData connection"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("📊 MANUAL TRUEDATA CONNECTION TEST")
    print("=" * 50)
    
    try:
        # First check current status
        print("1. Checking current TrueData status...")
        status_response = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            connected = status_data.get('data', {}).get('connected', False)
            symbols = status_data.get('data', {}).get('subscribed_symbols', [])  # Fixed field name
            total_symbols = status_data.get('data', {}).get('total_symbols', 0)
            
            print(f"   Current status: {'CONNECTED' if connected else 'DISCONNECTED'}")
            print(f"   Subscribed symbols: {total_symbols} ({symbols[:3]}{'...' if len(symbols) > 3 else ''})")
            
            if not connected:
                print("\n2. Attempting manual connection...")
                
                # Get credentials from environment or use defaults
                credentials = {
                    "username": "tdwsp697",  # From your environment config
                    "password": "shyam@697"
                }
                
                print(f"   Using credentials: {credentials['username']} / {'*' * len(credentials['password'])}")
                
                # Try to establish connection
                connect_response = requests.post(
                    f"{base_url}/api/v1/truedata/truedata/connect", 
                    json=credentials,
                    timeout=30
                )
                
                print(f"   Connection response status: {connect_response.status_code}")
                
                if connect_response.status_code == 200:
                    connect_data = connect_response.json()
                    print("✅ Connection attempt completed")
                    print(f"   Result: {connect_data.get('message', 'No message')}")
                    
                    # Check status again
                    print("\n3. Checking status after connection attempt...")
                    status_response = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
                    if status_response.status_code == 200:
                        new_status = status_response.json()
                        new_connected = new_status.get('data', {}).get('connected', False)
                        new_symbols = new_status.get('data', {}).get('total_symbols', 0)
                        
                        print(f"   New status: {'CONNECTED' if new_connected else 'STILL DISCONNECTED'}")
                        print(f"   New symbols: {new_symbols}")
                        
                        if new_connected:
                            print("🎉 SUCCESS: TrueData is now connected!")
                            
                            # Test subscribing to symbols
                            print("\n4. Testing symbol subscription...")
                            test_symbols = ["NIFTY-I", "BANKNIFTY-I", "RELIANCE"]
                            
                            subscribe_response = requests.post(
                                f"{base_url}/api/v1/truedata/truedata/subscribe",
                                json=test_symbols,
                                timeout=15
                            )
                            
                            if subscribe_response.status_code == 200:
                                subscribe_data = subscribe_response.json()
                                print(f"✅ Subscription successful: {subscribe_data.get('message')}")
                                
                                # Final status check
                                print("\n5. Final status check...")
                                final_status = requests.get(f"{base_url}/api/v1/truedata/truedata/status", timeout=10)
                                if final_status.status_code == 200:
                                    final_data = final_status.json()
                                    final_symbols = final_data.get('data', {}).get('total_symbols', 0)
                                    symbols_list = final_data.get('data', {}).get('subscribed_symbols', [])
                                    print(f"   Final symbol count: {final_symbols}")
                                    print(f"   Subscribed to: {symbols_list}")
                                    
                            else:
                                print(f"⚠️ Subscription failed: {subscribe_response.status_code}")
                        else:
                            print("⚠️ TrueData still disconnected (may be library issue)")
                            print("   This is expected due to the TrueData library bug we found")
                            print("   The emergency fix prevents crashes but connection may still fail")
                            
                elif connect_response.status_code == 400:
                    error_data = connect_response.json()
                    print(f"❌ Bad Request: {error_data.get('detail', 'Unknown error')}")
                    
                elif connect_response.status_code == 500:
                    error_data = connect_response.json()
                    print(f"❌ Server Error: {error_data.get('detail', 'Internal server error')}")
                    print("   This may be due to the TrueData library bug")
                    
                else:
                    print(f"❌ Connection failed: HTTP {connect_response.status_code}")
                    try:
                        error_text = connect_response.text
                        print(f"   Error details: {error_text[:200]}...")
                    except:
                        pass
                    
            else:
                print("✅ TrueData already connected!")
                print(f"   Connected with {total_symbols} symbols")
                
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
            print("   App may not be responding properly")
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - app may be down or restarting")
    except requests.exceptions.ReadTimeout:
        print("❌ Read timeout - TrueData connection attempt may be taking too long")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("📋 MANUAL CONNECTION TEST SUMMARY:")
    print("   - This tests the manual TrueData connection API")
    print("   - If connection fails, it's likely due to TrueData library bugs")
    print("   - The emergency fix prevents crashes but may not fix connection issues")
    print("   - You can still use paper trading mode without TrueData")

if __name__ == "__main__":
    test_manual_truedata_connection() 
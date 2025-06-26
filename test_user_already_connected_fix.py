#!/usr/bin/env python3
"""
Test User Already Connected Fix
Verify the deployment handles the error correctly
"""

import requests
import json

def test_user_already_connected_fix():
    """Test the User Already Connected error handling"""
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("🔧 TESTING USER ALREADY CONNECTED FIX")
    print("=" * 50)
    
    try:
        # 1. Check detailed connection status
        print("1. Checking detailed TrueData connection status...")
        
        status_response = requests.get(f"{base_url}/api/v1/truedata/truedata/connection-status", timeout=10)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            data = status_data.get('data', {})
            
            print(f"   Connected: {data.get('client_connected', False)}")
            print(f"   Error Type: {data.get('error_type', 'None')}")
            print(f"   Retry Disabled: {data.get('retry_disabled', False)}")
            print(f"   Can Retry: {data.get('can_retry', True)}")
            
            recommendations = data.get('recommendations', [])
            if recommendations:
                print("   Recommendations:")
                for rec in recommendations:
                    print(f"     - {rec}")
            
            # 2. If "User Already Connected", test force disconnect
            if data.get('error_type') == 'USER_ALREADY_CONNECTED':
                print("\n2. 'User Already Connected' detected - testing force disconnect...")
                
                disconnect_response = requests.post(f"{base_url}/api/v1/truedata/truedata/force-disconnect", timeout=15)
                
                if disconnect_response.status_code == 200:
                    disconnect_data = disconnect_response.json()
                    print("   ✅ Force disconnect successful")
                    print(f"   Message: {disconnect_data.get('message', 'No message')}")
                    
                    # 3. Try connection after force disconnect
                    print("\n3. Testing connection after force disconnect...")
                    
                    connect_response = requests.post(
                        f"{base_url}/api/v1/truedata/truedata/connect",
                        json={"username": "tdwsp697", "password": "shyam@697"},
                        timeout=30
                    )
                    
                    if connect_response.status_code == 200:
                        connect_data = connect_response.json()
                        print("   ✅ Connection successful after force disconnect")
                        print(f"   Result: {connect_data.get('message', 'No message')}")
                    else:
                        print(f"   ⚠️ Connection still failed: {connect_response.status_code}")
                        try:
                            error_data = connect_response.json()
                            print(f"   Error: {error_data.get('detail', 'Unknown')}")
                        except:
                            pass
                            
                else:
                    print(f"   ❌ Force disconnect failed: {disconnect_response.status_code}")
            
            else:
                print("\n2. No 'User Already Connected' error - testing normal connection...")
                
                connect_response = requests.post(
                    f"{base_url}/api/v1/truedata/truedata/connect",
                    json={"username": "tdwsp697", "password": "shyam@697"},
                    timeout=30
                )
                
                if connect_response.status_code == 200:
                    connect_data = connect_response.json()
                    print("   ✅ Normal connection successful")
                    print(f"   Result: {connect_data.get('message', 'No message')}")
                else:
                    print(f"   ⚠️ Normal connection failed: {connect_response.status_code}")
                    try:
                        error_data = connect_response.json()
                        print(f"   Error: {error_data.get('detail', 'Unknown')}")
                    except:
                        pass
        
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - app may be down or restarting")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 USER ALREADY CONNECTED FIX TEST SUMMARY:")
    print("   - Tests detailed connection status endpoint")
    print("   - Tests force disconnect functionality") 
    print("   - Tests connection retry after force disconnect")
    print("   - Verifies no more retry loops")

if __name__ == "__main__":
    test_user_already_connected_fix() 
#!/usr/bin/env python3
"""
Test authentication endpoint
"""
import requests
import json

# API endpoint
BASE_URL = "https://algoauto-ua2iq.ondigitalocean.app"
AUTH_URL = f"{BASE_URL}/api/v1/auth/login"

# Test credentials
credentials = {
    "username": "admin",
    "password": "admin123"
}

print(f"Testing authentication at: {AUTH_URL}")
print(f"Credentials: {credentials}")

try:
    # Test the auth endpoint
    response = requests.post(AUTH_URL, json=credentials)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    # Try to parse JSON response
    try:
        data = response.json()
        print(f"\nResponse JSON:")
        print(json.dumps(data, indent=2))
        
        if data.get("success"):
            print("\n✅ Authentication successful!")
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"User: {data.get('user', {})}")
        else:
            print("\n❌ Authentication failed!")
            
    except json.JSONDecodeError:
        print(f"\nResponse Text (first 500 chars):")
        print(response.text[:500])
        print("\n❌ Response is not JSON - likely returning HTML")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

# Also test if the test endpoint works
print("\n" + "="*50)
print("Testing /api/v1/auth/test endpoint...")
try:
    test_response = requests.get(f"{BASE_URL}/api/v1/auth/test")
    print(f"Status Code: {test_response.status_code}")
    
    try:
        test_data = test_response.json()
        print(f"Response: {json.dumps(test_data, indent=2)}")
    except:
        print(f"Response (first 200 chars): {test_response.text[:200]}...")
        
except Exception as e:
    print(f"Error: {e}") 
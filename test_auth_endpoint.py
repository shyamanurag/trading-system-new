"""
Test authentication endpoint
"""
import requests
import json

# Test against deployed app
base_url = "https://algoauto-ua2iq.ondigitalocean.app"
auth_endpoint = f"{base_url}/api/v1/auth/login"

# Test credentials
test_data = {
    "username": "admin",
    "password": "admin123"
}

print(f"Testing authentication endpoint: {auth_endpoint}")
print(f"Credentials: {test_data}")

try:
    # Test if API is reachable
    health_response = requests.get(f"{base_url}/health/alive", timeout=5)
    print(f"\nHealth check: {health_response.status_code}")
    
    # Test auth endpoint
    response = requests.post(
        auth_endpoint,
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nAuth response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess! Response: {json.dumps(data, indent=2)}")
    else:
        print(f"\nError response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\nConnection error: {e}") 
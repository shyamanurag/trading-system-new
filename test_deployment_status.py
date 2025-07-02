#!/usr/bin/env python3
import requests
import json
import sys

def test_deployment():
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print("Testing deployment status...")
    
    # Test 1: Basic health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Health check error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: System status endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/monitoring/system-status", timeout=10)
        print(f"System Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"System status error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Autonomous trading endpoint
    try:
        response = requests.post(
            f"{base_url}/api/v1/autonomous/start",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Autonomous Trading Start: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Autonomous trading error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Market data endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=10)
        print(f"Market Data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Symbols count: {data.get('symbol_count', 0)}")
            print(f"Success: {data.get('success', False)}")
            print(f"Message: {data.get('message', 'No message')}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Market data error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: API routes endpoint
    try:
        response = requests.get(f"{base_url}/api/routes", timeout=10)
        print(f"API Routes: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total routes: {data.get('total_routes', 0)}")
            print(f"API routes count: {len(data.get('api_routes', []))}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"API routes error: {e}")

if __name__ == "__main__":
    test_deployment() 
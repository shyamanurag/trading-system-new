import requests
import json

# DigitalOcean app URL
BASE_URL = "https://algoauto-ua2iq.ondigitalocean.app"

def test_endpoints():
    """Test various API endpoints"""
    
    endpoints = [
        "/",
        "/health",
        "/health/ready",
        "/market/indices",
        "/market/movers",
        "/market/sectors",
        "/api/health/detailed",
        "/api/trading/metrics"
    ]
    
    print(f"Testing API endpoints on {BASE_URL}\n")
    
    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data:
                        print(f"  Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'list'}")
                    else:
                        print(f"  Response keys: {list(data.keys())}")
                except:
                    print(f"  Response: {response.text[:100]}...")
            else:
                print(f"  Error: {response.text[:100]}...")
                
            print()
            
        except Exception as e:
            print(f"  Error: {str(e)}\n")

if __name__ == "__main__":
    test_endpoints() 
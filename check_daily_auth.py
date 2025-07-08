#!/usr/bin/env python3
import requests

def main():
    print("🔍 CHECKING DAILY AUTH DEPLOYMENT")
    print("=" * 50)
    
    # Check if routes are loaded
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/routes', timeout=10)
        if r.status_code == 200:
            data = r.json()
            routes = data.get('api_routes', [])
            daily_routes = [route for route in routes if 'daily-auth' in route.get('path', '')]
            print(f"📊 Daily auth routes found: {len(daily_routes)}")
            
            if daily_routes:
                for route in daily_routes:
                    methods = route.get('methods', [])
                    path = route.get('path', '')
                    print(f"  - {methods} {path}")
            else:
                print("❌ No daily-auth routes found in API")
        else:
            print(f"❌ Routes check failed: {r.status_code}")
    except Exception as e:
        print(f"❌ Routes check error: {e}")
    
    print("\n🔍 TESTING ENDPOINTS")
    print("-" * 30)
    
    # Test main page
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/daily-auth/', timeout=10)
        print(f"📄 Main page: {r.status_code} ({r.headers.get('content-type', 'unknown')[:20]})")
    except Exception as e:
        print(f"❌ Main page error: {e}")
    
    # Test status endpoint
    try:
        r = requests.get('https://algoauto-9gx56.ondigitalocean.app/daily-auth/status', timeout=10)
        content_type = r.headers.get('content-type', 'unknown')
        print(f"📊 Status endpoint: {r.status_code} ({content_type[:20]})")
        
        if 'application/json' in content_type:
            try:
                data = r.json()
                print(f"✅ JSON response: {data}")
            except:
                print("❌ Invalid JSON")
        elif 'text/html' in content_type:
            print("❌ Returning HTML instead of JSON - router not working")
            print(f"First 100 chars: {r.text[:100]}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test Daily Auth Routes Loading
"""

import requests

def check_routes():
    """Check if daily auth routes are loaded"""
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/routes', timeout=10)
        print(f'Routes endpoint status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            routes = data.get('api_routes', [])
            
            # Look for daily-auth routes
            daily_routes = [r for r in routes if 'daily-auth' in r.get('path', '')]
            print(f'Daily auth routes found: {len(daily_routes)}')
            
            if daily_routes:
                print('✅ Daily auth routes are loaded:')
                for route in daily_routes:
                    methods = route.get('methods', [])
                    path = route.get('path', '')
                    print(f'  - {methods} {path}')
            else:
                print('❌ No daily auth routes found')
                
            print(f'Total API routes: {len(routes)}')
            
            # Test direct access to daily-auth status
            print('\n🔍 Testing direct access to /daily-auth/status:')
            status_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/daily-auth/status', timeout=10)
            print(f'Status endpoint: {status_response.status_code}')
            print(f'Content-Type: {status_response.headers.get("content-type", "unknown")}')
            
            if status_response.status_code == 200:
                if 'application/json' in status_response.headers.get("content-type", ""):
                    print('✅ Status endpoint returning JSON')
                    try:
                        json_data = status_response.json()
                        print(f'Response: {json_data}')
                    except:
                        print('❌ Invalid JSON response')
                else:
                    print('❌ Status endpoint returning HTML instead of JSON')
                    print(f'First 200 chars: {status_response.text[:200]}')
            else:
                print(f'❌ Status endpoint failed: {status_response.status_code}')
                
        else:
            print(f'Failed to get routes: {response.status_code}')
            
    except Exception as e:
        print(f'Error checking routes: {e}')

if __name__ == "__main__":
    check_routes() 
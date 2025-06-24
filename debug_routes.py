#!/usr/bin/env python3
"""Debug route registration"""

import requests

def check_routes():
    base_url = 'https://algoauto-9gx56.ondigitalocean.app'
    
    print('CHECKING ROUTE REGISTRATION')
    print('=' * 40)
    
    try:
        r = requests.get(base_url + '/api/routes')
        if r.status_code == 200:
            data = r.json()
            routes = data.get('api_routes', [])
            
            print(f'Total API routes: {len(routes)}')
            
            # Check for Zerodha routes
            zerodha_routes = [r for r in routes if 'zerodha' in r['path'].lower()]
            print(f'\nZerodha routes found: {len(zerodha_routes)}')
            for route in zerodha_routes:
                print(f'  {route["path"]} - {route["methods"]}')
            
            # Check for manual routes specifically
            manual_routes = [r for r in routes if 'manual' in r['path'].lower()]
            print(f'\nManual auth routes found: {len(manual_routes)}')
            for route in manual_routes:
                print(f'  {route["path"]} - {route["methods"]}')
                
            # Check if the specific path exists
            auth_url_route = [r for r in routes if 'zerodha-manual/auth-url' in r['path']]
            print(f'\nAuth URL route exists: {len(auth_url_route) > 0}')
            
        else:
            print(f'Routes endpoint returned: {r.status_code}')
    except Exception as e:
        print(f'Error checking routes: {e}')
    
    print('\nDIRECT ENDPOINT TEST')
    print('=' * 40)
    
    # Test the endpoint directly
    try:
        r = requests.get(base_url + '/zerodha-manual/auth-url')
        print(f'Status: {r.status_code}')
        print(f'Content-Type: {r.headers.get("content-type", "Unknown")}')
        
        if 'json' in r.headers.get('content-type', ''):
            print('✅ Returning JSON (correct)')
            data = r.json()
            print(f'Success flag: {data.get("success", False)}')
        else:
            print('❌ Returning HTML (incorrect)')
            print(f'Response preview: {r.text[:100]}...')
            
    except Exception as e:
        print(f'Error testing endpoint: {e}')

if __name__ == "__main__":
    check_routes() 
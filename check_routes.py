import requests
import json

def check_production_routes():
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/routes')
        data = response.json()
        
        print(f'Total routes: {len(data.get("api_routes", []))}')
        
        # Look for missing routes
        api_routes = data.get('api_routes', [])
        missing_endpoints = ['/api/v1/positions', '/api/v1/orders', '/api/v1/trades', '/ws']
        
        print('\nChecking for missing endpoints:')
        for endpoint in missing_endpoints:
            found = any(endpoint in route['path'] for route in api_routes)
            status = '✓' if found else '✗'
            print(f'{status} {endpoint}')
        
        # Show routes that contain our keywords
        print('\nRelevant routes found:')
        keywords = ['position', 'order', 'trade', 'ws']
        for route in api_routes:
            if any(keyword in route['path'].lower() for keyword in keywords):
                print(f'  {route["path"]} - {route["methods"]}')
                
        print('\nAll WebSocket routes:')
        ws_routes = [route for route in api_routes if 'ws' in route['path'].lower()]
        for route in ws_routes:
            print(f'  {route["path"]} - {route["methods"]}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_production_routes() 
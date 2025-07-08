#!/usr/bin/env python3
"""
Check Router Loading Status
"""

import requests
import json

def check_router_status():
    """Check if routers are loading properly"""
    try:
        # Check health endpoint
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/health', timeout=10)
        print(f'Health Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Routers loaded: {data.get("routers_loaded", "unknown")}')
            print(f'Total routers: {data.get("total_routers", "unknown")}')
        
        # Check if daily-auth specific routes exist
        routes_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/routes', timeout=10)
        if routes_response.status_code == 200:
            routes_data = routes_response.json()
            all_routes = routes_data.get('api_routes', [])
            
            daily_routes = [r for r in all_routes if 'daily-auth' in r.get('path', '')]
            print(f'\nDaily Auth Routes Found: {len(daily_routes)}')
            for route in daily_routes:
                print(f'  - {route.get("methods", [])} {route.get("path", "unknown")}')
            
            # Check if router loaded but not mounted
            if len(daily_routes) == 0:
                print('\n❌ No daily-auth routes found')
                print('🔍 Checking for router loading errors...')
                
                # Try to access the daily-auth page directly
                daily_response = requests.get('https://algoauto-9gx56.ondigitalocean.app/daily-auth/', timeout=10)
                print(f'Daily auth page direct access: {daily_response.status_code}')
                print(f'Content-Type: {daily_response.headers.get("content-type", "unknown")}')
                
                if daily_response.status_code == 404:
                    print('❌ Router not mounted - likely import error')
                elif 'text/html' in daily_response.headers.get("content-type", ""):
                    print('❌ Router returning HTML instead of API - catch-all issue')
                else:
                    print('✅ Router seems to be working')
        
    except Exception as e:
        print(f'Error checking router status: {e}')

if __name__ == "__main__":
    check_router_status() 
#!/usr/bin/env python3
"""
API Tester for Trading System
Uses Python requests library instead of curl to avoid Windows command hanging
"""

import requests
import json
from datetime import datetime
import sys

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'
ZERODHA_TOKEN = 'xXkTfIytomux6QZCEd0LOyHYWamtxtLH'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def test_endpoint(method, path, data=None, headers=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
        
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except requests.exceptions.Timeout:
        return 'TIMEOUT', None
    except Exception as e:
        return 'ERROR', str(e)

def print_result(name, status, data=None):
    """Print test result"""
    if status == 200:
        print(f"{Colors.GREEN}✓ {name}: {status}{Colors.RESET}")
        if data and isinstance(data, dict):
            for key in ['success', 'total_count', 'recommendations', 'components_ready_count']:
                if key in data:
                    print(f"    {key}: {data[key]}")
    elif status == 'TIMEOUT':
        print(f"{Colors.YELLOW}⏱ {name}: TIMEOUT{Colors.RESET}")
    elif status == 'ERROR':
        print(f"{Colors.RED}✗ {name}: ERROR - {data}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {name}: {status}{Colors.RESET}")

def test_backend_fixes():
    """Test all backend fixes"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== TESTING BACKEND FIXES ==={Colors.RESET}\n")
    
    # 1. Zerodha authentication
    print(f"{Colors.BOLD}1. Zerodha Authentication{Colors.RESET}")
    status, data = test_endpoint('POST', '/api/zerodha/submit-token', {
        'request_token': ZERODHA_TOKEN
    })
    print_result('Zerodha Auth', status, data)
    if status == 200 and data and data.get('success'):
        user = data.get('user', {})
        print(f"    Authenticated as: {user.get('name')} ({user.get('user_id')})")
    print()
    
    # 2. Elite recommendations
    print(f"{Colors.BOLD}2. Elite Recommendations{Colors.RESET}")
    status, data = test_endpoint('GET', '/api/v1/elite/')
    print_result('Elite Recommendations', status, data)
    print()
    
    # 3. Direct endpoints
    print(f"{Colors.BOLD}3. Direct Endpoints{Colors.RESET}")
    endpoints = [
        '/api/v1/positions',
        '/api/v1/orders',
        '/api/v1/holdings',
        '/api/v1/margins'
    ]
    for endpoint in endpoints:
        status, data = test_endpoint('GET', endpoint)
        print_result(endpoint, status)
    print()
    
    # 4. Market data
    print(f"{Colors.BOLD}4. Market Data{Colors.RESET}")
    status, data = test_endpoint('GET', '/api/v1/market-data')
    print_result('Market Data', status, data)
    print()
    
    # 5. System status
    print(f"{Colors.BOLD}5. System Status{Colors.RESET}")
    status, data = test_endpoint('GET', '/api/v1/autonomous/status')
    print_result('Autonomous Status', status, data)
    if status == 200 and data and data.get('data'):
        strategies = data['data'].get('active_strategies', [])
        print(f"    Active strategies: {len(strategies)}")
    print()
    
    # 6. Try to find orchestrator debug
    print(f"{Colors.BOLD}6. Looking for Orchestrator Debug{Colors.RESET}")
    debug_paths = [
        '/api/v1/orchestrator-debug',
        '/api/v1/debug/orchestrator-debug',
        '/api/v1/system/orchestrator-debug'
    ]
    for path in debug_paths:
        status, data = test_endpoint('GET', path)
        if status == 200:
            print_result(f'Found at {path}', status, data)
            break
    print()
    
    # 7. Try to find risk metrics
    print(f"{Colors.BOLD}7. Looking for Risk Metrics{Colors.RESET}")
    risk_paths = [
        '/api/v1/risk/metrics',
        '/api/v1/autonomous/risk',
        '/api/risk/metrics'
    ]
    for path in risk_paths:
        status, data = test_endpoint('GET', path)
        if status == 200:
            print_result(f'Found at {path}', status, data)
            break

def test_specific(path):
    """Test a specific endpoint"""
    print(f"\n{Colors.BOLD}Testing: {path}{Colors.RESET}")
    status, data = test_endpoint('GET', path)
    print_result(path, status, data)
    if data:
        print(f"\nResponse:\n{json.dumps(data, indent=2)}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Test specific endpoint
        test_specific(sys.argv[1])
    else:
        # Run all tests
        test_backend_fixes()
        
    print(f"\n{Colors.CYAN}Note: This uses Python requests library to avoid Windows cmd/curl hanging issues{Colors.RESET}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import requests
import json

def analyze_react_error():
    print('🔍 ANALYZING API RESPONSE CAUSING REACT ERROR #31')
    print('=' * 55)
    
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print('📊 ACTIVE_STRATEGIES STRUCTURE (causing React error):')
            active_strategies = trading_data.get('active_strategies', [])
            print(f'Type: {type(active_strategies)}')
            print(f'Length: {len(active_strategies)}')
            
            if active_strategies and len(active_strategies) > 0:
                print('\nFirst strategy object:')
                first_strategy = active_strategies[0]
                print(json.dumps(first_strategy, indent=2))
                print()
                print('🚨 PROBLEM: React is trying to render this object directly!')
                print('🔧 SOLUTION: Convert objects to strings or fix frontend handling')
            
            print('\n📋 FULL RESPONSE STRUCTURE:')
            for key, value in trading_data.items():
                if isinstance(value, list):
                    print(f'{key}: list[{len(value)}]')
                elif isinstance(value, dict):
                    print(f'{key}: dict with {len(value)} keys')
                else:
                    print(f'{key}: {type(value).__name__} = {value}')
        else:
            print(f'❌ API Error: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    analyze_react_error() 
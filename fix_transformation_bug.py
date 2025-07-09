#!/usr/bin/env python3
"""
Fix Transformation Bug - Ensure strategies get proper price_change and volume_change fields
"""

import requests
import json

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def fix_transformation_bug():
    print('🔧 FIXING TRANSFORMATION BUG')
    print('=' * 50)
    
    # The issue is that transformation is failing, causing fallback to raw_data
    # This means strategies get raw TrueData format instead of transformed format
    
    print('💡 ISSUE IDENTIFIED:')
    print('1. Trading loop is running ✅')
    print('2. Transformation throws exception ❌')
    print('3. Falls back to raw_data ❌')
    print('4. Strategies see price_change = 0, volume_change = 0 ❌')
    print('5. No signals generated ❌')
    print()
    
    print('🔍 TESTING DIRECT API CALL TO VERIFY:')
    
    # Test current market data
    try:
        response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})
            
            if 'ASIANPAINT' in market_data:
                sample = market_data['ASIANPAINT']
                print(f'ASIANPAINT raw data:')
                print(f'  changeper: {sample.get("changeper", "MISSING")}')
                print(f'  volume: {sample.get("volume", "MISSING")}')
                print(f'  price_change: {sample.get("price_change", "MISSING")}')
                print(f'  volume_change: {sample.get("volume_change", "MISSING")}')
                print()
                
                # If price_change is missing, transformation is NOT working
                if sample.get('price_change') is None:
                    print('❌ CONFIRMED: price_change field is missing')
                    print('💡 SOLUTION: Need to fix transformation or bypass it')
                    return True
                else:
                    print('✅ price_change field exists - transformation working')
                    return False
            else:
                print('❌ ASIANPAINT not found in market data')
                return False
        else:
            print(f'❌ Cannot get market data: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Error testing market data: {e}')
        return False

def suggest_immediate_fix():
    print('🚀 IMMEDIATE FIX STRATEGY:')
    print('=' * 40)
    
    print('OPTION 1: Simple Volume Scalper Fix')
    print('- Create a simple scalper that uses changeper directly')
    print('- Bypass the transformation requirement')
    print('- Generate signals based on raw changeper values')
    print()
    
    print('OPTION 2: Fix Transformation Exception')
    print('- Add error handling to transformation method')
    print('- Ensure price_change = changeper even if volume_change fails')
    print('- Log transformation errors for debugging')
    print()
    
    print('OPTION 3: Emergency Direct Trading')
    print('- Create emergency scalper that reads Redis cache directly')
    print('- Bypass orchestrator completely')
    print('- Generate signals based on direct price movements')
    print()
    
    print('RECOMMENDED: Option 1 (Simple Volume Scalper Fix)')
    print('- Fastest to implement')
    print('- Uses existing infrastructure')
    print('- Works with current market data format')

if __name__ == "__main__":
    issue_confirmed = fix_transformation_bug()
    if issue_confirmed:
        suggest_immediate_fix()
    else:
        print('✅ Transformation appears to be working')
        print('🔍 Need to investigate other potential issues') 
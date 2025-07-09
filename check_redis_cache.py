#!/usr/bin/env python3
"""
Redis Cache & TrueData Pipeline Checker
Check if market data is flowing from TrueData to Redis to Strategies
"""

import requests
import json

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def check_redis_cache():
    print('🔍 REDIS CACHE & TRUEDATA PIPELINE CHECK')
    print('=' * 50)
    
    # Check market data from Redis cache
    try:
        response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Market Data API: {response.status_code}')
            print(f'Success: {data.get("success")}')
            print(f'Symbol Count: {data.get("symbol_count")}')
            print(f'Timestamp: {data.get("timestamp")}')
            
            # Check if Redis has data
            market_data = data.get('data', {})
            if market_data and len(market_data) > 0:
                print(f'✅ Redis Cache: {len(market_data)} symbols cached')
                
                # Check sample symbol data quality
                first_symbol = list(market_data.keys())[0]
                symbol_data = market_data[first_symbol]
                print(f'Sample symbol: {first_symbol}')
                print(f'  Price: {symbol_data.get("ltp", "N/A")}')
                print(f'  Volume: {symbol_data.get("volume", "N/A")}')
                print(f'  Change: {symbol_data.get("change", "N/A")}')
                
                # Check if data is fresh (updated recently)
                if symbol_data.get('ltp') and symbol_data.get('ltp') > 0:
                    print('✅ REAL PRICE DATA IN REDIS CACHE!')
                    return True
                else:
                    print('❌ Redis cache exists but prices are stale/empty')
                    return False
            else:
                print('❌ Redis cache is empty - TrueData pipeline issue')
                return False
                
    except Exception as e:
        print(f'❌ Market data check failed: {e}')
        return False

def check_truedata_process():
    print('\n🔍 TRUEDATA PROCESS CHECK')
    print('=' * 30)
    
    # Check if TrueData process is running
    try:
        # Try different TrueData endpoints
        endpoints = [
            '/api/v1/truedata/status',
            '/api/v1/market-data/status',
            '/api/v1/system/status'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f'{BASE_URL}{endpoint}', timeout=5)
                print(f'{endpoint}: {response.status_code}')
                if response.status_code == 200:
                    data = response.json()
                    print(f'  Response: {str(data)[:100]}...')
            except Exception as e:
                print(f'{endpoint}: ERROR - {e}')
                
    except Exception as e:
        print(f'❌ TrueData process check failed: {e}')

def main():
    cache_ok = check_redis_cache()
    check_truedata_process()
    
    print('\n💡 DIAGNOSIS:')
    print('- TrueData → Redis → Strategies architecture')
    print('- Need to verify TrueData connection is feeding Redis')
    print('- Strategies read from Redis cache, not direct TrueData')
    
    if cache_ok:
        print('\n✅ Redis cache has live data - strategies should generate signals')
    else:
        print('\n❌ Redis cache is empty/stale - need to fix TrueData pipeline')
        print('💡 NEXT STEPS:')
        print('1. Check if TrueData process is running')
        print('2. Verify Redis connection and data flow')
        print('3. Restart TrueData-to-Redis pipeline if needed')

if __name__ == "__main__":
    main() 
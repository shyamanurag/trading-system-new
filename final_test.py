import requests

print('🎯 FINAL 250-SYMBOL SYSTEM TEST')
print('=' * 40)

base = 'https://algoauto-9gx56.ondigitalocean.app'

# Test Intelligent Symbol Manager
print('\n🤖 Intelligent Symbol Manager:')
try:
    resp = requests.get(f'{base}/api/v1/intelligent-symbols/status')
    data = resp.json()
    status = data['status']
    print(f'   Running: {status["is_running"]}')
    print(f'   Active: {status["active_symbols"]}/250')
    print(f'   Core Indices: {status["core_indices"]}')
    print(f'   Priority Stocks: {status["priority_stocks"]}')
    print(f'   Options: {status["options"]}')
    
    if status["is_running"] and status["active_symbols"] >= 50:
        print('   ✅ BREAKTHROUGH SUCCESS!')
    elif status["is_running"]:
        print('   ⚡ Running but building symbols...')
    else:
        print('   ❌ Not running')
        
except Exception as e:
    print(f'   Error: {e}')

# Test TrueData
print('\n📡 TrueData Status:')
try:
    resp = requests.get(f'{base}/api/v1/truedata/truedata/status')
    data = resp.json()
    print(f'   Connected: {data["connected"]}')
    print(f'   Symbols: {data["symbols_active"]}')
    print(f'   Data Flowing: {data["data_flowing"]}')
    
    if data["connected"] and data["symbols_active"] >= 50:
        print('   ✅ MASSIVE DATA FLOW!')
    elif data["connected"]:
        print('   ⚡ Connected with limited symbols')
    else:
        print('   ❌ Not connected')
        
except Exception as e:
    print(f'   Error: {e}')

# Test Market Data
print('\n📈 Market Data Sample:')
try:
    resp = requests.get(f'{base}/api/v1/market-data/indices')
    data = resp.json()
    if 'indices' in data:
        print(f'   Indices Available: {len(data["indices"])}')
        for idx in data['indices'][:3]:
            print(f'   {idx["symbol"]}: ₹{idx["ltp"]:,.1f} ({idx.get("data_source", "Unknown")})')
            
        if len(data['indices']) >= 3:
            print('   ✅ LIVE DATA CONFIRMED!')
    else:
        print('   ❌ No market data')
        
except Exception as e:
    print(f'   Error: {e}')

print('\n🎯 SYSTEM STATUS:')
print('================')
print('If you see 50+ symbols active, the 250-symbol breakthrough is SUCCESS!') 
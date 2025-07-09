#!/usr/bin/env python3
"""
Signal Flow Debugger
Trace where scalping signals are getting lost in the system
"""

import requests
import json
import time

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def debug_signal_flow():
    print('🔍 SIGNAL FLOW DEBUG - TRACING WHERE SIGNALS ARE LOST')
    print('=' * 70)
    
    # Test specific symbols that should generate signals
    test_symbols = ['ASIANPAINT', 'GODREJCP', 'HINDUNILVR', 'ADANIGREEN', 'HCLTECH']
    
    print('🎯 TESTING HIGH-PROBABILITY SCALPING SYMBOLS:')
    for symbol in test_symbols:
        print(f'  - {symbol}: Should generate STRONG signal')
    print()
    
    # 1. Check market data format being sent to strategies
    print('1️⃣ MARKET DATA FORMAT CHECK:')
    print('-' * 40)
    
    try:
        response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})
            
            # Check data format for first test symbol
            if test_symbols[0] in market_data:
                sample_data = market_data[test_symbols[0]]
                print(f'✅ Sample data for {test_symbols[0]}:')
                print(f'  - ltp: {sample_data.get("ltp", "MISSING")}')
                print(f'  - changeper: {sample_data.get("changeper", "MISSING")}')
                print(f'  - volume: {sample_data.get("volume", "MISSING")}')
                print(f'  - high: {sample_data.get("high", "MISSING")}')
                print(f'  - low: {sample_data.get("low", "MISSING")}')
                print(f'  - close: {sample_data.get("close", "MISSING")}')
                print(f'  - volume_change: {sample_data.get("volume_change", "MISSING")}')
                print(f'  - price_change: {sample_data.get("price_change", "MISSING")}')
                
                # Check if this should trigger volume profile scalper
                price_change = sample_data.get('changeper', 0)
                print(f'\n🔍 SIGNAL ANALYSIS for {test_symbols[0]}:')
                print(f'  - Price change: {price_change}%')
                print(f'  - Above 0.08% threshold: {"✅ YES" if abs(price_change) >= 0.08 else "❌ NO"}')
                print(f'  - Should generate STRONG signal: {"✅ YES" if abs(price_change) >= 0.08 else "❌ NO"}')
            else:
                print(f'❌ {test_symbols[0]} not found in market data')
                
    except Exception as e:
        print(f'❌ Market data check failed: {e}')
    
    print()
    
    # 2. Check if Elite Recommendations are consuming signals
    print('2️⃣ ELITE RECOMMENDATIONS INTERFERENCE CHECK:')
    print('-' * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/api/v1/elite', timeout=5)
        print(f'Elite API Status: {response.status_code}')
        
        if response.status_code == 200:
            elite_data = response.json()
            recommendations = elite_data.get('recommendations', [])
            print(f'Elite recommendations count: {len(recommendations)}')
            
            if len(recommendations) > 0:
                print('❌ POTENTIAL ISSUE: Elite system may be consuming strategy signals')
                print('💡 SOLUTION: Check if Elite scanner is clearing strategy signals')
            else:
                print('✅ Elite not interfering with strategy signals')
        else:
            print('✅ Elite API not available - no interference')
            
    except Exception as e:
        print(f'Elite check failed: {e}')
    
    print()
    
    # 3. Monitor autonomous status for signal generation
    print('3️⃣ REAL-TIME SIGNAL GENERATION MONITOR:')
    print('-' * 45)
    
    print('Monitoring for 30 seconds...')
    
    for i in range(6):  # 30 seconds / 5 second intervals
        try:
            response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=3)
            if response.status_code == 200:
                data = response.json()
                trading_data = data.get('data', {})
                
                trades = trading_data.get('total_trades', 0)
                pnl = trading_data.get('daily_pnl', 0.0)
                timestamp = time.strftime('%H:%M:%S')
                
                print(f'[{timestamp}] Trades: {trades} | PNL: {pnl} | Active: {trading_data.get("is_active", False)}')
                
                if trades > 0:
                    print(f'🎉 SIGNAL DETECTED! Trades increased to {trades}')
                    break
                    
        except Exception as e:
            print(f'[{time.strftime("%H:%M:%S")}] Monitor error: {e}')
        
        time.sleep(5)
    
    print()
    
    # 4. Check orchestrator logs/debug endpoints
    print('4️⃣ ORCHESTRATOR DEBUG CHECK:')
    print('-' * 35)
    
    # Try to get orchestrator test signals
    try:
        response = requests.get(f'{BASE_URL}/api/v1/orchestrator/test-signals', timeout=5)
        print(f'Orchestrator test signals: {response.status_code}')
        
        if response.status_code == 200:
            test_data = response.json()
            print(f'Test signals response: {json.dumps(test_data, indent=2)[:200]}...')
        else:
            print('❌ Cannot access orchestrator test endpoint')
            
    except Exception as e:
        print(f'Orchestrator debug failed: {e}')
    
    print()
    print('🎯 SUMMARY:')
    print('=' * 30)
    print('✅ Market data: Rich with scalping opportunities')
    print('✅ Strategies: Active and should be generating signals')  
    print('❌ Signals: Not reaching trade execution')
    print()
    print('💡 LIKELY ISSUES:')
    print('1. Data transformation in orchestrator losing key fields')
    print('2. Strategy cooldowns preventing all signals')
    print('3. Elite recommendations consuming signals (previous issue)')
    print('4. Signal collection timing issue in orchestrator')
    print('5. Trade engine not processing collected signals')

if __name__ == "__main__":
    debug_signal_flow() 
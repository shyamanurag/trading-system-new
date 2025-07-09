#!/usr/bin/env python3
"""
Strategy Signal Generation Debug Tool
Debug why strategies aren't generating signals despite live data
"""

import requests
import json
import sys
import os

# Add project root to path
sys.path.append('.')

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def debug_strategy_signals():
    print('🔍 STRATEGY SIGNAL GENERATION DEBUG')
    print('=' * 50)
    
    # Get market data that strategies are receiving
    try:
        response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})
            
            if market_data:
                print(f'✅ Market Data: {len(market_data)} symbols')
                
                # Check sample symbol data quality
                sample_symbol = list(market_data.keys())[0]
                sample_data = market_data[sample_symbol]
                
                print(f'\n📊 Sample Symbol: {sample_symbol}')
                print(f'  Price (ltp): {sample_data.get("ltp", "N/A")}')
                print(f'  Volume: {sample_data.get("volume", "N/A")}')
                print(f'  Change: {sample_data.get("change", "N/A")}')
                print(f'  Change%: {sample_data.get("changeper", "N/A")}')
                print(f'  High: {sample_data.get("high", "N/A")}')
                print(f'  Low: {sample_data.get("low", "N/A")}')
                print(f'  Open: {sample_data.get("open", "N/A")}')
                
                # Check if this data would trigger strategy signals
                print(f'\n🔍 SIGNAL GENERATION CONDITIONS:')
                
                # Check momentum surfer conditions
                price_change = sample_data.get('changeper', 0)
                volume_change = 0  # Would be calculated by orchestrator
                
                print(f'  Price Change: {price_change}%')
                print(f'  Volume Change: {volume_change}% (calculated by orchestrator)')
                
                # Check against momentum thresholds
                print(f'\n📈 MOMENTUM SURFER THRESHOLDS:')
                print(f'  Strong Positive: >0.10% (Current: {price_change}%)')
                print(f'  Moderate Positive: >0.06% (Current: {price_change}%)')
                print(f'  Strong Negative: <-0.10% (Current: {price_change}%)')
                print(f'  Moderate Negative: <-0.06% (Current: {price_change}%)')
                
                # Check volatility conditions
                current_price = sample_data.get('ltp', 0)
                high = sample_data.get('high', current_price)
                low = sample_data.get('low', current_price)
                
                if high > 0 and low > 0:
                    atr_ratio = (high - low) / current_price * 100
                    print(f'\n📊 VOLATILITY EXPLOSION ANALYSIS:')
                    print(f'  ATR Ratio: {atr_ratio:.2f}%')
                    print(f'  High: {high}, Low: {low}, Current: {current_price}')
                    print(f'  Volatility Threshold: Need >1.2x historical (simplified)')
                
                # Check why signals might not be generated
                print(f'\n🚨 POSSIBLE SIGNAL GENERATION ISSUES:')
                
                if abs(price_change) < 0.06:
                    print(f'  ❌ Price change too small ({price_change}% < 0.06%)')
                else:
                    print(f'  ✅ Price change sufficient ({price_change}% >= 0.06%)')
                
                if current_price == 0:
                    print(f'  ❌ No valid price data')
                else:
                    print(f'  ✅ Valid price data ({current_price})')
                
                if high == low:
                    print(f'  ❌ No intraday range (high=low={high})')
                else:
                    print(f'  ✅ Valid intraday range ({high}-{low})')
                
                print(f'\n💡 DIAGNOSIS:')
                print(f'1. Check if price movements meet strategy thresholds')
                print(f'2. Verify strategy cooldown periods aren\'t blocking signals')
                print(f'3. Ensure strategies have proper historical data for comparisons')
                print(f'4. Check if strategies are actually active (not just loaded)')
                
            else:
                print('❌ No market data available')
                
    except Exception as e:
        print(f'❌ Error: {e}')

def check_strategy_conditions():
    print(f'\n🔍 STRATEGY ACTIVATION CONDITIONS')
    print('=' * 40)
    
    # Check autonomous status
    try:
        response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            print(f'System Active: {trading_data.get("is_active", False)}')
            print(f'Market Status: {trading_data.get("market_status", "unknown")}')
            print(f'Active Strategies: {trading_data.get("active_strategies", [])}')
            
            if not trading_data.get("is_active", False):
                print(f'❌ CRITICAL: System not active')
            
            if trading_data.get("market_status") != "open":
                print(f'⚠️  Market may be closed')
                
    except Exception as e:
        print(f'❌ Error checking strategy status: {e}')

if __name__ == "__main__":
    debug_strategy_signals()
    check_strategy_conditions() 
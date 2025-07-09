#!/usr/bin/env python3
"""
All Symbols Scalping Analysis
Analyze all 51 symbols for scalping opportunities and check why no signals are generated
"""

import requests
import json

BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app'

def analyze_all_symbols_for_scalping():
    print('🔍 ALL SYMBOLS SCALPING ANALYSIS')
    print('=' * 60)
    
    try:
        response = requests.get(f'{BASE_URL}/api/v1/market-data', timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_data = data.get('data', {})
            
            if market_data:
                print(f'✅ Analyzing {len(market_data)} symbols for scalping opportunities')
                print()
                
                # Scalping thresholds (from volume profile scalper)
                scalping_thresholds = {
                    'price_weak': 0.03,      # 0.03% - VERY aggressive
                    'price_moderate': 0.05,  # 0.05% 
                    'price_strong': 0.08,    # 0.08%
                    'volume_low': 8,         # 8% volume increase
                    'volume_moderate': 15,   # 15% volume increase
                    'volume_high': 25        # 25% volume increase
                }
                
                # Analysis counters
                signals_found = 0
                weak_signals = 0
                moderate_signals = 0
                strong_signals = 0
                no_data_symbols = 0
                
                scalping_opportunities = []
                
                print('📊 SYMBOL-BY-SYMBOL SCALPING ANALYSIS:')
                print('-' * 60)
                
                for symbol, symbol_data in market_data.items():
                    price_change = symbol_data.get('changeper', 0)
                    volume = symbol_data.get('volume', 0)
                    current_price = symbol_data.get('ltp', 0)
                    high = symbol_data.get('high', current_price)
                    low = symbol_data.get('low', current_price)
                    
                    # Skip if no valid data
                    if not current_price or current_price == 0:
                        no_data_symbols += 1
                        continue
                    
                    # Calculate ATR ratio for volatility
                    atr_ratio = ((high - low) / current_price * 100) if current_price > 0 else 0
                    
                    # Check scalping signal conditions
                    abs_price_change = abs(price_change)
                    signal_strength = None
                    
                    if abs_price_change >= scalping_thresholds['price_strong']:
                        signal_strength = 'STRONG'
                        strong_signals += 1
                        signals_found += 1
                    elif abs_price_change >= scalping_thresholds['price_moderate']:
                        signal_strength = 'MODERATE'
                        moderate_signals += 1
                        signals_found += 1
                    elif abs_price_change >= scalping_thresholds['price_weak']:
                        signal_strength = 'WEAK'
                        weak_signals += 1
                        signals_found += 1
                    
                    # Record scalping opportunities
                    if signal_strength:
                        scalping_opportunities.append({
                            'symbol': symbol,
                            'price_change': price_change,
                            'atr_ratio': atr_ratio,
                            'signal_strength': signal_strength,
                            'current_price': current_price,
                            'volume': volume
                        })
                        
                        print(f'{symbol:12} | {price_change:+6.3f}% | ATR: {atr_ratio:5.2f}% | {signal_strength:8} | ₹{current_price:8.2f}')
                
                print()
                print('🎯 SCALPING ANALYSIS SUMMARY:')
                print('=' * 40)
                print(f'Total Symbols Analyzed: {len(market_data)}')
                print(f'Valid Data Symbols: {len(market_data) - no_data_symbols}')
                print(f'No Data Symbols: {no_data_symbols}')
                print()
                print(f'SCALPING OPPORTUNITIES FOUND: {signals_found}')
                print(f'  Strong Signals (≥0.08%): {strong_signals}')
                print(f'  Moderate Signals (≥0.05%): {moderate_signals}')
                print(f'  Weak Signals (≥0.03%): {weak_signals}')
                print()
                
                if signals_found > 0:
                    print('🚨 SCALPING SIGNALS SHOULD BE GENERATED!')
                    print('=' * 50)
                    print('Top scalping opportunities:')
                    
                    # Sort by absolute price change
                    scalping_opportunities.sort(key=lambda x: abs(x['price_change']), reverse=True)
                    
                    for i, opp in enumerate(scalping_opportunities[:10]):
                        direction = '📈 BUY ' if opp['price_change'] > 0 else '📉 SELL'
                        print(f'{i+1:2}. {opp["symbol"]:12} | {direction} | {opp["price_change"]:+6.3f}% | {opp["signal_strength"]}')
                    
                    print()
                    print('❌ PROBLEM: Scalping strategies should be generating signals!')
                    print('💡 POSSIBLE ISSUES:')
                    print('1. Scalping strategies not actually active')
                    print('2. Strategy cooldowns preventing signals')
                    print('3. Data transformation issues in orchestrator')
                    print('4. Elite recommendations consuming signals before orchestrator')
                    
                else:
                    print('❌ NO SCALPING OPPORTUNITIES FOUND')
                    print('All symbols below 0.03% movement threshold')
                    
                    # Show top movers even if below threshold
                    all_symbols = []
                    for symbol, symbol_data in market_data.items():
                        price_change = symbol_data.get('changeper', 0)
                        if abs(price_change) > 0:
                            all_symbols.append((symbol, price_change))
                    
                    all_symbols.sort(key=lambda x: abs(x[1]), reverse=True)
                    
                    print()
                    print('Top 10 movers (even if below threshold):')
                    for i, (symbol, change) in enumerate(all_symbols[:10]):
                        print(f'{i+1:2}. {symbol:12} | {change:+6.3f}%')
                
            else:
                print('❌ No market data available')
                
    except Exception as e:
        print(f'❌ Error: {e}')

def check_scalping_strategy_status():
    print(f'\n🔍 SCALPING STRATEGY STATUS CHECK')
    print('=' * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/api/v1/autonomous/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            trading_data = data.get('data', {})
            
            active_strategies = trading_data.get('active_strategies', [])
            
            # Check for scalping strategies
            scalping_strategies = [
                'volume_profile_scalper',
                'optimized_volume_scalper', 
                'news_impact_scalper'
            ]
            
            print('SCALPING STRATEGY STATUS:')
            for strategy in scalping_strategies:
                if strategy in active_strategies:
                    print(f'  ✅ {strategy}: ACTIVE')
                else:
                    print(f'  ❌ {strategy}: NOT ACTIVE')
            
            print(f'\nAll Active Strategies: {active_strategies}')
            
            # Check if any trades have been executed
            total_trades = trading_data.get('total_trades', 0)
            print(f'\nTotal Trades Executed: {total_trades}')
            
            if total_trades == 0 and len(active_strategies) > 0:
                print('❌ CRITICAL ISSUE: Active strategies but zero trades!')
                
    except Exception as e:
        print(f'❌ Error checking strategy status: {e}')

if __name__ == "__main__":
    analyze_all_symbols_for_scalping()
    check_scalping_strategy_status() 
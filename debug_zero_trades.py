#!/usr/bin/env python3
"""
Debug Zero Trades Issue
Comprehensive analysis of why trades aren't being generated
"""

import requests
import json
import time
from datetime import datetime

def debug_zero_trades():
    """Debug why trades aren't being generated"""
    
    print("🔍 DEBUG: ZERO TRADES ANALYSIS")
    print("=" * 60)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Step 1: Check autonomous trading status
    print("\n1️⃣ AUTONOMOUS TRADING STATUS")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/v1/autonomous/status", timeout=15)
        if response.status_code == 200:
            data = response.json()['data']
            print(f"✅ Active: {data.get('is_active', False)}")
            print(f"✅ Strategies: {len(data.get('active_strategies', []))}")
            print(f"✅ Total Trades: {data.get('total_trades', 0)}")
            print(f"✅ Market Status: {data.get('market_status', 'unknown')}")
            print(f"✅ System Ready: {data.get('system_ready', False)}")
            
            strategies = data.get('active_strategies', [])
            print(f"✅ Strategy List: {strategies}")
            
            if not data.get('is_active', False):
                print("❌ ISSUE: System not active")
                return
            
        else:
            print(f"❌ Autonomous API Error: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Autonomous Check Failed: {e}")
        return
    
    # Step 2: Check market data availability
    print("\n2️⃣ MARKET DATA AVAILABILITY")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=15)
        if response.status_code == 200:
            data = response.json()
            symbol_count = len(data)
            print(f"✅ Market Data API: 200 OK")
            print(f"✅ Symbols Available: {symbol_count}")
            
            if symbol_count > 0:
                print("\n📊 Sample Market Data:")
                for i, symbol in enumerate(data[:3]):
                    ltp = symbol.get('ltp', 0)
                    changeper = symbol.get('changeper', 0)
                    volume = symbol.get('volume', 0)
                    print(f"  {symbol.get('symbol', 'N/A')}: ₹{ltp:,.2f} | {changeper:+.2f}% | Vol: {volume:,}")
                
                # Check if data is fresh
                timestamp = data[0].get('timestamp', '')
                print(f"✅ Data Timestamp: {timestamp}")
                
                # Check for strong movers (scalping opportunities)
                strong_movers = [s for s in data if abs(s.get('changeper', 0)) >= 0.08]
                print(f"✅ Strong Movers (≥0.08%): {len(strong_movers)}")
                
                if len(strong_movers) > 0:
                    print("🎯 Strong Scalping Opportunities:")
                    for symbol in strong_movers[:5]:
                        print(f"  {symbol.get('symbol', 'N/A')}: {symbol.get('changeper', 0):+.2f}%")
                else:
                    print("⚠️ No strong market movements detected")
                    
            else:
                print("❌ ISSUE: No market data symbols")
                print("💡 TrueData not flowing data to Redis")
                
        else:
            print(f"❌ Market Data API Error: {response.status_code}")
            print("💡 Redis cache issues persist")
            
    except Exception as e:
        print(f"❌ Market Data Check Failed: {e}")
    
    # Step 3: Check TrueData connection
    print("\n3️⃣ TRUEDATA CONNECTION STATUS")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/v1/truedata/status", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ TrueData API: 200 OK")
            print(f"✅ Connected: {data.get('connected', False)}")
            print(f"✅ Symbols Active: {data.get('symbols_active', 0)}")
            print(f"✅ Data Flowing: {data.get('data_flowing', False)}")
            
            if not data.get('connected', False):
                print("❌ ISSUE: TrueData not connected")
                print("💡 This explains why no trades are being generated")
                
        else:
            print(f"❌ TrueData API Error: {response.status_code}")
            print("💡 TrueData connection issues")
            
    except Exception as e:
        print(f"❌ TrueData Check Failed: {e}")
    
    # Step 4: Check strategies endpoint
    print("\n4️⃣ STRATEGIES STATUS")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/v1/strategies", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategies API: 200 OK")
            
            # Check if strategies are loaded
            if isinstance(data, dict):
                strategy_count = len(data.get('strategies', []))
                print(f"✅ Strategies Loaded: {strategy_count}")
                
                if strategy_count > 0:
                    strategies = data.get('strategies', [])
                    for strategy in strategies:
                        name = strategy.get('name', 'Unknown')
                        status = strategy.get('status', 'Unknown')
                        print(f"  {name}: {status}")
                else:
                    print("❌ ISSUE: No strategies loaded")
                    
        else:
            print(f"❌ Strategies API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Strategies Check Failed: {e}")
    
    # Step 5: Summary and recommendations
    print("\n5️⃣ DIAGNOSIS & RECOMMENDATIONS")
    print("-" * 30)
    
    print("\n🎯 LIKELY CAUSES OF ZERO TRADES:")
    print("1. TrueData connection not established (404 error)")
    print("2. Market data not flowing from TrueData to Redis")
    print("3. Strategies not receiving market data")
    print("4. Low market volatility (need ≥0.08% movements)")
    
    print("\n💡 RECOMMENDED ACTIONS:")
    print("1. Wait 2-3 minutes for TrueData to connect")
    print("2. Check deployment logs for TrueData connection")
    print("3. Monitor market data API for symbol count > 0")
    print("4. Verify strong market movements are present")
    
    print("\n🔄 RE-RUN THIS SCRIPT IN 2-3 MINUTES TO MONITOR PROGRESS")

if __name__ == "__main__":
    debug_zero_trades() 
#!/usr/bin/env python3
"""
Quick Trade Execution Check
Simple test to verify trade execution readiness without complex imports
"""

import sys
import os
import asyncio
from datetime import datetime

print("🔍 QUICK TRADE EXECUTION CHECK")
print("=" * 40)

# Check 1: Environment Variables
print("\n1. ENVIRONMENT VARIABLES:")
print(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")
print(f"   REDIS_URL: {'✅ Set' if os.getenv('REDIS_URL') else '❌ Not set'}")
print(f"   DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'}")
print(f"   ZERODHA_API_KEY: {'✅ Set' if os.getenv('ZERODHA_API_KEY') else '❌ Not set'}")

# Check 2: Core modules availability
print("\n2. CORE MODULES:")
try:
    sys.path.append('src')
    from src.core.order_manager import OrderManager
    print("   ✅ OrderManager: Available")
except Exception as e:
    print(f"   ❌ OrderManager: {e}")

try:
    from src.core.trade_allocator import TradeAllocator
    print("   ✅ TradeAllocator: Available")
except Exception as e:
    print(f"   ❌ TradeAllocator: {e}")

try:
    from src.core.trade_engine import TradeEngine
    print("   ✅ TradeEngine: Available")
except Exception as e:
    print(f"   ❌ TradeEngine: {e}")

try:
    from brokers.zerodha import ZerodhaClient
    print("   ✅ ZerodhaClient: Available")
except Exception as e:
    print(f"   ❌ ZerodhaClient: {e}")

# Check 3: Strategy modules
print("\n3. STRATEGY MODULES:")
try:
    from strategies.momentum_surfer import EnhancedMomentumSurfer
    print("   ✅ MomentumSurfer: Available")
except Exception as e:
    print(f"   ❌ MomentumSurfer: {e}")

try:
    from strategies.volatility_explosion import EnhancedVolatilityExplosion
    print("   ✅ VolatilityExplosion: Available")
except Exception as e:
    print(f"   ❌ VolatilityExplosion: {e}")

# Check 4: Signal flow components
print("\n4. SIGNAL FLOW COMPONENTS:")
try:
    from src.core.risk_manager import RiskManager
    print("   ✅ RiskManager: Available")
except Exception as e:
    print(f"   ❌ RiskManager: {e}")

# Check 5: API endpoints
print("\n5. API ENDPOINTS TEST:")
try:
    import requests
    
    # Test if the app is running
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        print(f"   ✅ Health endpoint: {response.status_code}")
    except:
        print("   ❌ Health endpoint: Not accessible (app not running locally)")
    
    # Test deployed app
    try:
        response = requests.get('https://algoauto-9gx56.ondigitalocean.app/health', timeout=10)
        print(f"   ✅ Deployed health: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Deployed health: {e}")
        
except ImportError:
    print("   ⚠️ Requests not available - skipping API tests")

# Check 6: File structure
print("\n6. FILE STRUCTURE:")
required_files = [
    'src/core/orchestrator.py',
    'src/core/order_manager.py',
    'src/core/trade_engine.py',
    'src/core/trade_allocator.py',
    'strategies/momentum_surfer.py',
    'brokers/zerodha.py'
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ {file_path}")

print("\n" + "=" * 40)
print("📊 TRADE EXECUTION READINESS SUMMARY:")

# Based on your feedback
print("\n✅ CONFIRMED BY USER:")
print("   - App deployed successfully")
print("   - APIs and WebSocket working")
print("   - TrueData integration working")
print("   - System gets data from TrueData")

print("\n🔄 CURRENT SITUATION:")
print("   - Markets are closed")
print("   - No live market data flowing")
print("   - No trade execution (expected)")

print("\n🎯 ACTUAL ISSUE:")
print("   - Trade execution pipeline needs verification")
print("   - Signal → Order → Broker flow")
print("   - OrderManager integration")

print("\n💡 NEXT STEPS:")
print("   1. Fix any syntax errors in orchestrator.py")
print("   2. Verify OrderManager initialization")
print("   3. Test signal processing flow")
print("   4. Wait for market open for live testing")

print("\n🚀 CONCLUSION:")
print("   System is mostly working - just need to fix trade execution flow") 
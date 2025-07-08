#!/usr/bin/env python3
"""
Debug Deployed vs Local Strategy Loading
Find out why deployed system has 0 strategies vs local 6
"""

import requests
import json
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.orchestrator import get_orchestrator

# Deployed system URL
DEPLOYED_URL = "https://trading-system-new-production.onrender.com"

def test_deployed_api():
    """Test deployed system API endpoints"""
    print("🔍 DEBUGGING DEPLOYED vs LOCAL STRATEGY LOADING")
    print("=" * 60)
    
    endpoints_to_test = [
        "/api/v1/trading/status",
        "/api/v1/system/health",
        "/api/v1/strategies",
        "/api/v1/market-data"
    ]
    
    print(f"\n📡 DEPLOYED SYSTEM: {DEPLOYED_URL}")
    print("-" * 40)
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{DEPLOYED_URL}{endpoint}"
            print(f"\n🌐 Testing: {endpoint}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                
                # Specific analysis for trading status
                if endpoint == "/api/v1/trading/status":
                    print(f"   📊 Active Strategies: {data.get('active_strategies', 'N/A')}")
                    print(f"   📊 Total Strategies: {data.get('total_strategies', 'N/A')}")
                    print(f"   📊 System Ready: {data.get('system_ready', 'N/A')}")
                    print(f"   📊 Is Active: {data.get('is_active', 'N/A')}")
                    
                    if 'strategy_details' in data:
                        print(f"   📋 Strategy Details:")
                        for strategy in data['strategy_details']:
                            name = strategy.get('name', 'Unknown')
                            active = strategy.get('active', False)
                            status = strategy.get('status', 'Unknown')
                            print(f"      {name}: {status} ({'ACTIVE' if active else 'INACTIVE'})")
                
                elif endpoint == "/api/v1/market-data":
                    symbols = len(data) if isinstance(data, dict) else 0
                    print(f"   📈 Market Data Symbols: {symbols}")
                    
                elif endpoint == "/api/v1/system/health":
                    print(f"   🏥 System Health: {data.get('status', 'Unknown')}")
                    
                elif endpoint == "/api/v1/strategies":
                    if isinstance(data, list):
                        print(f"   🎯 Strategies Available: {len(data)}")
                        for strategy in data:
                            print(f"      - {strategy}")
                    else:
                        print(f"   🎯 Strategies Response: {data}")
                        
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout: {endpoint}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection Error: {endpoint}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_local_system():
    """Test local system orchestrator"""
    print(f"\n💻 LOCAL SYSTEM:")
    print("-" * 40)
    
    try:
        orchestrator = await get_orchestrator()
        
        if orchestrator:
            print(f"✅ Orchestrator obtained")
            print(f"   📊 Initialized: {orchestrator.is_initialized}")
            print(f"   📊 Running: {orchestrator.is_running}")
            print(f"   📊 Loaded Strategies: {len(orchestrator.strategies)}")
            print(f"   📊 Active Strategies: {len(orchestrator.active_strategies)}")
            
            print(f"   📋 Strategy Details:")
            for key, strategy_info in orchestrator.strategies.items():
                name = strategy_info.get('name', key)
                active = strategy_info.get('active', False)
                has_instance = 'instance' in strategy_info
                print(f"      {name}: {'ACTIVE' if active else 'INACTIVE'} ({'LOADED' if has_instance else 'NOT LOADED'})")
                
        else:
            print(f"❌ Failed to get orchestrator")
            
    except Exception as e:
        print(f"❌ Local system error: {e}")

def compare_systems():
    """Compare deployed vs local findings"""
    print(f"\n🔍 ANALYSIS: WHY 0 STRATEGIES ON DEPLOYED?")
    print("=" * 50)
    
    print(f"📝 POSSIBLE CAUSES:")
    print(f"1. 🚨 Orchestrator initialization failing on deployed system")
    print(f"2. 🚨 Strategy loading errors in deployed environment") 
    print(f"3. 🚨 Configuration differences (environment variables)")
    print(f"4. 🚨 Import errors in deployed Python environment")
    print(f"5. 🚨 Database/Redis connection issues affecting strategy loading")
    print(f"6. 🚨 Memory/resource constraints on deployed server")
    
    print(f"\n💡 DEBUGGING STEPS:")
    print(f"1. Check deployed system logs")
    print(f"2. Test strategy loading endpoint directly")
    print(f"3. Compare environment variables")
    print(f"4. Test orchestrator initialization on deployed system")

async def main():
    """Main debugging function"""
    # Test deployed system
    test_deployed_api()
    
    # Test local system  
    await test_local_system()
    
    # Compare findings
    compare_systems()

if __name__ == "__main__":
    asyncio.run(main()) 
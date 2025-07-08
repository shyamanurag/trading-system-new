#!/usr/bin/env python3
"""
Monitor Deployment Progress
==========================
Track deployment of orchestrator fixes and scalping optimizations
"""

import requests
import time
import json
from datetime import datetime

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_orchestrator_fix():
    """Test if orchestrator fix is deployed"""
    print("🔍 Testing Orchestrator Fix...")
    
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/debug/orchestrator-debug", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if get_status method error is gone
            if 'success' in data and data['success']:
                print("✅ Orchestrator Debug: Working")
                
                components = data.get('components', {})
                ready_count = data.get('components_ready_count', 0)
                total_count = data.get('total_components', 0)
                
                print(f"   📊 Components: {ready_count}/{total_count} ready")
                
                for component, status in components.items():
                    icon = "✅" if status else "❌"
                    print(f"   {icon} {component}: {status}")
                
                return ready_count > 0
            else:
                print("❌ Orchestrator Debug: Still has errors")
                return False
        else:
            print(f"❌ Orchestrator Debug: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator Debug: Error - {e}")
        return False

def test_force_initialize():
    """Test if force initialize is working"""
    print("\n🔧 Testing Force Initialize...")
    
    try:
        response = requests.post(f"{DEPLOYED_URL}/api/v1/debug/force-initialize", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success', False):
                print("✅ Force Initialize: Working")
                
                active_strategies = data.get('active_strategies', [])
                components_ready = data.get('components_ready', 0)
                
                print(f"   🎯 Active Strategies: {len(active_strategies)}")
                print(f"   📊 Components Ready: {components_ready}")
                
                return len(active_strategies) > 0
            else:
                print("❌ Force Initialize: Failed")
                error = data.get('error', 'Unknown error')
                print(f"   Error: {error}")
                return False
        else:
            print(f"❌ Force Initialize: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Force Initialize: Error - {e}")
        return False

def test_trading_status():
    """Test if trading status shows active strategies"""
    print("\n📊 Testing Trading Status...")
    
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                trading_data = data['data']
                active_strategies = trading_data.get('active_strategies', [])
                system_ready = trading_data.get('system_ready', False)
                
                print(f"✅ Trading Status: {len(active_strategies)} strategies active")
                print(f"   🎯 System Ready: {system_ready}")
                
                return len(active_strategies) > 0
            else:
                print("❌ Trading Status: No data field")
                return False
        else:
            print(f"❌ Trading Status: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Trading Status: Error - {e}")
        return False

def main():
    """Main monitoring function"""
    print("🚀 MONITORING DEPLOYMENT PROGRESS")
    print("=" * 50)
    print(f"URL: {DEPLOYED_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test orchestrator fix
    orchestrator_ok = test_orchestrator_fix()
    
    # Test force initialize
    initialize_ok = test_force_initialize()
    
    # Test trading status
    trading_ok = test_trading_status()
    
    print("\n🎯 DEPLOYMENT STATUS SUMMARY")
    print("=" * 30)
    
    if orchestrator_ok and initialize_ok and trading_ok:
        print("✅ ALL FIXES DEPLOYED SUCCESSFULLY!")
        print("✅ Orchestrator methods working")
        print("✅ Components initialized")
        print("✅ Strategies active")
        print("\n🎯 READY FOR LIVE TRADING!")
        
    elif orchestrator_ok and initialize_ok:
        print("✅ Orchestrator fixes deployed")
        print("⚠️  Trading status needs check")
        print("🔄 Deployment in progress...")
        
    elif orchestrator_ok:
        print("✅ Orchestrator debug working")
        print("⚠️  Initialize method needs check")
        print("🔄 Deployment in progress...")
        
    else:
        print("❌ Deployment still in progress")
        print("⏳ Methods not yet deployed")
        
    print(f"\n⏰ Next check recommended in 2-3 minutes")

if __name__ == "__main__":
    main() 
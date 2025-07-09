#!/usr/bin/env python3
"""
Test script to verify Zerodha connection fix
"""

import asyncio
import requests
import json
from datetime import datetime

async def test_zerodha_connection_fix():
    """Test the Zerodha connection fix"""
    print("🔧 Testing Zerodha Connection Fix...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Test 1: Check Zerodha status
    print("\n1. Checking Zerodha Status...")
    try:
        response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Zerodha Status: {status.get('authenticated', 'Unknown')}")
            print(f"   User ID: {status.get('user_id', 'Unknown')}")
            print(f"   Session: {status.get('session', {}).get('login_time', 'Unknown')}")
        else:
            print(f"❌ Zerodha Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Zerodha Status error: {e}")
    
    # Test 2: Check system status
    print("\n2. Checking System Status...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ System Active: {status.get('is_active', False)}")
            print(f"   Strategies: {status.get('total_strategies', 0)}")
            print(f"   Components Ready: {status.get('components_ready_count', 0)}")
        else:
            print(f"❌ System Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System Status error: {e}")
    
    # Test 3: Test signal generation
    print("\n3. Testing Signal Generation...")
    try:
        response = requests.get(f"{base_url}/api/v1/trading/signals", timeout=10)
        if response.status_code == 200:
            signals = response.json()
            print(f"✅ Active signals: {len(signals.get('signals', []))}")
            for signal in signals.get('signals', [])[:3]:  # Show first 3
                print(f"   Signal: {signal.get('symbol')} {signal.get('action')} "
                      f"Confidence: {signal.get('confidence', 0):.2f}")
        else:
            print(f"❌ Signals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signals error: {e}")
    
    # Test 4: Check deployment logs for connection status
    print("\n4. Checking Recent Deployment...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ System Health: {health.get('status', 'Unknown')}")
            print(f"   Deployment: {health.get('deployment_id', 'Unknown')}")
            print(f"   Timestamp: {health.get('timestamp', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed. Check results above.")
    print("🚀 If Zerodha shows 'authenticated: True', the fix should work!")
    
if __name__ == "__main__":
    asyncio.run(test_zerodha_connection_fix()) 
"""
Test script to verify Zerodha connection fix
"""

import asyncio
import requests
import json
from datetime import datetime

async def test_zerodha_connection_fix():
    """Test the Zerodha connection fix"""
    print("🔧 Testing Zerodha Connection Fix...")
    print("=" * 50)
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    # Test 1: Check Zerodha status
    print("\n1. Checking Zerodha Status...")
    try:
        response = requests.get(f"{base_url}/auth/zerodha/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Zerodha Status: {status.get('authenticated', 'Unknown')}")
            print(f"   User ID: {status.get('user_id', 'Unknown')}")
            print(f"   Session: {status.get('session', {}).get('login_time', 'Unknown')}")
        else:
            print(f"❌ Zerodha Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Zerodha Status error: {e}")
    
    # Test 2: Check system status
    print("\n2. Checking System Status...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ System Active: {status.get('is_active', False)}")
            print(f"   Strategies: {status.get('total_strategies', 0)}")
            print(f"   Components Ready: {status.get('components_ready_count', 0)}")
        else:
            print(f"❌ System Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System Status error: {e}")
    
    # Test 3: Test signal generation
    print("\n3. Testing Signal Generation...")
    try:
        response = requests.get(f"{base_url}/api/v1/trading/signals", timeout=10)
        if response.status_code == 200:
            signals = response.json()
            print(f"✅ Active signals: {len(signals.get('signals', []))}")
            for signal in signals.get('signals', [])[:3]:  # Show first 3
                print(f"   Signal: {signal.get('symbol')} {signal.get('action')} "
                      f"Confidence: {signal.get('confidence', 0):.2f}")
        else:
            print(f"❌ Signals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signals error: {e}")
    
    # Test 4: Check deployment logs for connection status
    print("\n4. Checking Recent Deployment...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ System Health: {health.get('status', 'Unknown')}")
            print(f"   Deployment: {health.get('deployment_id', 'Unknown')}")
            print(f"   Timestamp: {health.get('timestamp', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed. Check results above.")
    print("🚀 If Zerodha shows 'authenticated: True', the fix should work!")
    
if __name__ == "__main__":
    asyncio.run(test_zerodha_connection_fix()) 
#!/usr/bin/env python3
"""
Comprehensive orchestrator failure diagnosis
"""
import requests
import json
import traceback

DEPLOYED_URL = "https://algoauto-9gx56.ondigitalocean.app"

def test_orchestrator_failure():
    """Test orchestrator failure in detail"""
    print("🔍 DIAGNOSING ORCHESTRATOR FAILURE...")
    
    # Test 1: Try to start orchestrator
    print("\n1️⃣ Testing orchestrator start...")
    try:
        response = requests.post(f"{DEPLOYED_URL}/api/v1/autonomous/start", timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Start failed: {response.text}")
    except Exception as e:
        print(f"❌ Start request failed: {e}")
    
    # Test 2: Check current orchestrator status
    print("\n2️⃣ Testing orchestrator status...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/autonomous/status", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "fallback mode" in data.get("message", ""):
                print("❌ System is in FALLBACK mode - orchestrator not initialized")
            else:
                print("✅ Orchestrator status OK")
        else:
            print(f"❌ Status check failed: {response.text}")
    except Exception as e:
        print(f"❌ Status request failed: {e}")
    
    # Test 3: Test local dependency check
    print("\n3️⃣ Testing local dependencies...")
    try:
        print("Testing pydantic_settings...")
        from pydantic_settings import BaseSettings, SettingsConfigDict
        print("✅ pydantic_settings available locally")
    except ImportError as e:
        print(f"❌ pydantic_settings missing locally: {e}")
    
    try:
        print("Testing orchestrator import...")
        from src.core.orchestrator import TradingOrchestrator
        print("✅ TradingOrchestrator import successful")
    except Exception as e:
        print(f"❌ TradingOrchestrator import failed: {e}")
        print(traceback.format_exc())
    
    # Test 4: Test orchestrator creation locally
    print("\n4️⃣ Testing local orchestrator creation...")
    try:
        from src.core.orchestrator import TradingOrchestrator
        orchestrator = TradingOrchestrator()
        print("✅ Local orchestrator creation successful")
    except Exception as e:
        print(f"❌ Local orchestrator creation failed: {e}")
        print(traceback.format_exc())
    
    # Test 5: Test forced orchestrator start
    print("\n5️⃣ Testing forced orchestrator start...")
    try:
        response = requests.post(f"{DEPLOYED_URL}/api/v1/autonomous/force-activate", timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Force start failed: {e}")
    
    # Test 6: Check if broker is connected
    print("\n6️⃣ Testing broker connectivity...")
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/v1/zerodha/status", timeout=10)
        print(f"Broker status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Broker data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Broker check failed: {response.text}")
    except Exception as e:
        print(f"❌ Broker request failed: {e}")
    
    # Test 7: Check strategy endpoints
    print("\n7️⃣ Testing strategy endpoints...")
    strategy_endpoints = [
        "/api/v1/strategies",
        "/api/v1/strategies/status",
        "/api/v1/strategies/momentum_surfer",
        "/api/v1/strategies/volatility_explosion"
    ]
    
    for endpoint in strategy_endpoints:
        try:
            response = requests.get(f"{DEPLOYED_URL}{endpoint}", timeout=10)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Working")
            else:
                print(f"  ❌ Failed: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ {endpoint} failed: {e}")

if __name__ == "__main__":
    test_orchestrator_failure() 
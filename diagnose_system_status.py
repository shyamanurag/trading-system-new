#!/usr/bin/env python3
"""
System Status Diagnostic Tool
Checks all critical components for autonomous trading
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_system():
    """Comprehensive system diagnosis"""
    
    print("🔍 SYSTEM DIAGNOSIS STARTING...")
    print("=" * 50)
    
    issues = []
    
    # 1. Check Zerodha credentials
    print("\n1. 🔐 ZERODHA CREDENTIALS CHECK:")
    try:
        from src.api.trading_control import get_master_user
        master_user = get_master_user()
        if master_user:
            print(f"   ✅ Master user found: {master_user.get('user_id', 'Unknown')}")
            
            # Check for required fields
            required_fields = ['api_key', 'user_id']
            for field in required_fields:
                if master_user.get(field):
                    print(f"   ✅ {field}: Available")
                else:
                    print(f"   ❌ {field}: Missing")
                    issues.append(f"Missing {field} in master user")
        else:
            print("   ❌ No master user found")
            issues.append("No master user configured")
    except Exception as e:
        print(f"   ❌ Error checking master user: {e}")
        issues.append(f"Master user check failed: {e}")
    
    # 2. Check Redis access token
    print("\n2. 🔑 REDIS ACCESS TOKEN CHECK:")
    try:
        import redis
        import json
        
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print(f"   ✅ Redis connection successful")
        
        # Check for access tokens
        keys = redis_client.keys("zerodha_token:*")
        if keys:
            print(f"   ✅ Found {len(keys)} access token(s): {keys}")
            for key in keys:
                token_data = redis_client.get(key)
                if token_data:
                    try:
                        token_info = json.loads(token_data)
                        print(f"   ✅ Token {key}: Valid JSON structure")
                    except:
                        print(f"   ⚠️ Token {key}: Invalid JSON")
                else:
                    print(f"   ❌ Token {key}: Empty")
        else:
            print("   ❌ No access tokens found in Redis")
            issues.append("No Zerodha access tokens in Redis")
            
    except Exception as e:
        print(f"   ❌ Redis check failed: {e}")
        issues.append(f"Redis access failed: {e}")
    
    # 3. Check Zerodha client initialization
    print("\n3. 🔌 ZERODHA CLIENT INITIALIZATION:")
    try:
        from brokers.zerodha import ZerodhaIntegration
        
        # Try to create a basic config
        test_config = {
            'api_key': os.environ.get('ZERODHA_API_KEY', ''),
            'user_id': os.environ.get('ZERODHA_USER_ID', ''),
            'access_token': os.environ.get('ZERODHA_ACCESS_TOKEN', '')
        }
        
        if test_config['api_key'] and test_config['user_id']:
            print(f"   ✅ Basic config available")
            
            zerodha_client = ZerodhaIntegration(test_config)
            if zerodha_client:
                print(f"   ✅ ZerodhaIntegration object created")
                
                if zerodha_client.kite:
                    print(f"   ✅ Kite client initialized")
                else:
                    print(f"   ❌ Kite client is None")
                    issues.append("Kite client initialization failed")
            else:
                print(f"   ❌ ZerodhaIntegration creation failed")
                issues.append("ZerodhaIntegration creation failed")
        else:
            print(f"   ❌ Missing basic credentials")
            print(f"      API Key: {'✅' if test_config['api_key'] else '❌'}")
            print(f"      User ID: {'✅' if test_config['user_id'] else '❌'}")
            print(f"      Access Token: {'✅' if test_config['access_token'] else '❌'}")
            issues.append("Missing basic Zerodha credentials")
            
    except Exception as e:
        print(f"   ❌ Zerodha client check failed: {e}")
        issues.append(f"Zerodha client initialization failed: {e}")
    
    # 4. Check orchestrator initialization
    print("\n4. 🎭 ORCHESTRATOR INITIALIZATION:")
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator()
        print(f"   ✅ Orchestrator object created")
        
        # Try initialization
        init_result = await orchestrator.initialize()
        if init_result:
            print(f"   ✅ Orchestrator initialization successful")
            
            if hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                print(f"   ✅ Orchestrator has Zerodha client")
            else:
                print(f"   ❌ Orchestrator missing Zerodha client")
                issues.append("Orchestrator missing Zerodha client")
                
        else:
            print(f"   ❌ Orchestrator initialization failed")
            issues.append("Orchestrator initialization failed")
            
    except Exception as e:
        print(f"   ❌ Orchestrator check failed: {e}")
        issues.append(f"Orchestrator check failed: {e}")
    
    # 5. Check strategy loading
    print("\n5. 📈 STRATEGY LOADING:")
    try:
        from src.core.orchestrator import TradingOrchestrator
        
        orchestrator = TradingOrchestrator()
        await orchestrator._load_strategies()
        
        if orchestrator.strategies:
            print(f"   ✅ Loaded {len(orchestrator.strategies)} strategies:")
            for name, info in orchestrator.strategies.items():
                print(f"      - {name}: {'✅' if info.get('loaded') else '❌'}")
        else:
            print(f"   ❌ No strategies loaded")
            issues.append("No strategies loaded")
            
    except Exception as e:
        print(f"   ❌ Strategy loading check failed: {e}")
        issues.append(f"Strategy loading failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSIS SUMMARY:")
    
    if not issues:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("🚀 Autonomous trading should work properly")
    else:
        print(f"❌ FOUND {len(issues)} ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        if "No Zerodha access tokens in Redis" in str(issues):
            print("   1. Submit fresh Zerodha access token via /auth/zerodha endpoint")
        if "Missing basic Zerodha credentials" in str(issues):
            print("   2. Check environment variables: ZERODHA_API_KEY, ZERODHA_USER_ID")
        if "Orchestrator initialization failed" in str(issues):
            print("   3. Check orchestrator logs for detailed error messages")

if __name__ == "__main__":
    asyncio.run(diagnose_system())

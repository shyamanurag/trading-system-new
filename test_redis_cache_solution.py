#!/usr/bin/env python3
"""
Redis Cache Solution Test
Verifies that TrueData cross-process cache sharing works correctly
"""

import os
import sys
import time
import json
import redis
import requests
from datetime import datetime

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("🔍 TESTING REDIS CONNECTION...")
    
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_password = os.environ.get('REDIS_PASSWORD')
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        redis_client.ping()
        print(f"✅ Redis connected: {redis_host}:{redis_port}")
        
        # Test read/write operations
        test_key = "test:redis:connection"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        redis_client.set(test_key, json.dumps(test_data))
        retrieved_data = redis_client.get(test_key)
        
        if retrieved_data:
            parsed_data = json.loads(retrieved_data)
            print(f"✅ Redis read/write test successful: {parsed_data}")
        else:
            print("❌ Redis read/write test failed")
            return False
        
        # Clean up test key
        redis_client.delete(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_truedata_redis_cache():
    """Test TrueData Redis cache availability"""
    print("\n🔍 TESTING TRUEDATA REDIS CACHE...")
    
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_password = os.environ.get('REDIS_PASSWORD')
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Check TrueData cache
        cached_data = redis_client.hgetall("truedata:live_cache")
        
        if not cached_data:
            print("⚠️ No TrueData data in Redis cache")
            print("💡 This indicates TrueData client is not writing to Redis")
            print("🔧 Check if TrueData client has Redis integration enabled")
            return False
        
        # Parse and analyze cached data
        parsed_symbols = {}
        for symbol, data_json in cached_data.items():
            try:
                parsed_symbols[symbol] = json.loads(data_json)
            except json.JSONDecodeError:
                print(f"⚠️ Invalid JSON for symbol {symbol}")
                continue
        
        print(f"✅ TrueData Redis cache accessible: {len(parsed_symbols)} symbols")
        
        # Show sample data
        sample_symbols = list(parsed_symbols.keys())[:5]
        for symbol in sample_symbols:
            data = parsed_symbols[symbol]
            ltp = data.get('ltp', 'N/A')
            volume = data.get('volume', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            print(f"   📊 {symbol}: ₹{ltp} | Vol: {volume} | {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ TrueData Redis cache test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints with Redis cache"""
    print("\n🔍 TESTING API ENDPOINTS WITH REDIS CACHE...")
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    try:
        # Test market data endpoint
        print("📡 Testing market data API...")
        response = requests.get(f"{base_url}/api/v1/market-data", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            symbols_count = data.get('symbols_count', 0)
            source = data.get('source', 'unknown')
            
            print(f"✅ API Response: Success={success}, Symbols={symbols_count}, Source={source}")
            
            if symbols_count > 0:
                print("🎉 SUCCESS: API can access market data via Redis cache!")
                
                # Show sample symbols
                api_data = data.get('data', {})
                sample_symbols = list(api_data.keys())[:3]
                for symbol in sample_symbols:
                    symbol_data = api_data[symbol]
                    ltp = symbol_data.get('ltp', 'N/A')
                    print(f"   📊 API Symbol: {symbol} = ₹{ltp}")
                
                return True
            else:
                print("❌ API returned 0 symbols - Redis cache may be empty")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_orchestrator_cache_access():
    """Test if orchestrator can access Redis cache"""
    print("\n🔍 TESTING ORCHESTRATOR CACHE ACCESS...")
    
    try:
        # Import and test orchestrator Redis access
        sys.path.insert(0, 'src')
        from core.orchestrator import TradingOrchestrator
        
        # Create orchestrator instance
        orchestrator = TradingOrchestrator()
        
        # Test market data access
        import asyncio
        
        async def test_market_data():
            market_data = await orchestrator._get_market_data_from_api()
            return market_data
        
        # Run the test
        market_data = asyncio.run(test_market_data())
        
        if market_data:
            print(f"✅ Orchestrator can access market data: {len(market_data)} symbols")
            
            # Show sample data
            sample_symbols = list(market_data.keys())[:3]
            for symbol in sample_symbols:
                data = market_data[symbol]
                ltp = data.get('ltp', 'N/A')
                print(f"   📊 Orchestrator Symbol: {symbol} = ₹{ltp}")
            
            return True
        else:
            print("❌ Orchestrator returned empty market data")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator cache access test failed: {e}")
        return False

def test_process_isolation_solution():
    """Test the complete process isolation solution"""
    print("\n🔍 TESTING COMPLETE PROCESS ISOLATION SOLUTION...")
    
    try:
        # Test TrueData client writing to Redis
        print("1️⃣ Testing TrueData client Redis writing...")
        from data.truedata_client import get_truedata_status, live_market_data
        
        status = get_truedata_status()
        print(f"   TrueData Status: {status}")
        print(f"   Local Cache: {len(live_market_data)} symbols")
        
        # Test API reading from Redis
        print("2️⃣ Testing API Redis reading...")
        api_test = test_api_endpoints()
        
        # Test orchestrator reading from Redis
        print("3️⃣ Testing Orchestrator Redis reading...")
        orchestrator_test = test_orchestrator_cache_access()
        
        if api_test and orchestrator_test:
            print("🎉 PROCESS ISOLATION SOLUTION WORKING!")
            print("✅ TrueData → Redis → API ✅")
            print("✅ TrueData → Redis → Orchestrator ✅")
            return True
        else:
            print("❌ Process isolation solution incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Process isolation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 REDIS CACHE SOLUTION TESTING")
    print("=" * 50)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("TrueData Redis Cache", test_truedata_redis_cache),
        ("API Endpoints", test_api_endpoints),
        ("Complete Solution", test_process_isolation_solution)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Redis cache solution is working!")
        print("💡 The process isolation issue should now be resolved")
        print("🚀 Trading system should start generating trades")
    else:
        print("⚠️ Some tests failed - check Redis configuration")
        print("💡 Verify Redis is running and accessible")
        print("🔧 Check TrueData client has Redis integration enabled")

if __name__ == "__main__":
    main() 
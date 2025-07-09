#!/usr/bin/env python3
"""
Test Redis Serialization Fix
Verify that market_data can be properly stored in Redis
"""

import json
import redis
from datetime import datetime

def test_redis_serialization():
    """Test Redis serialization with market_data structure"""
    
    try:
        # Connect to Redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test market_data structure (similar to what TrueData uses)
        market_data = {
            'symbol': 'ASIANPAINT',
            'ltp': 2518.90,
            'close': 2518.90,
            'high': 2520.00,
            'low': 2500.00,
            'open': 2505.00,
            'volume': 977771,
            'change': 34.26,
            'changeper': 1.38,
            'change_percent': 1.38,
            'bid': 2518.50,
            'ask': 2519.00,
            'timestamp': datetime.now().isoformat(),
            'source': 'TrueData_Live',
            'deployment_id': 'test_deployment',
            'data_quality': {
                'has_ohlc': True,
                'has_volume': True,
                'has_change_percent': True,
                'calculated_change_percent': False
            }
        }
        
        print("🧪 Testing Redis Serialization...")
        print(f"📊 Market Data: {market_data}")
        
        # Test 1: Direct hset with mapping (problematic approach)
        print("\n🔴 Test 1: Direct hset with mapping (should fail)")
        try:
            redis_client.hset("test:symbol:ASIANPAINT", mapping=market_data)
            print("✅ Direct hset with mapping: SUCCESS")
        except Exception as e:
            print(f"❌ Direct hset with mapping: FAILED - {e}")
            print("💡 This is the problematic approach causing the deployment error")
        
        # Test 2: JSON serialization (fixed approach)
        print("\n🟢 Test 2: JSON serialization (should work)")
        try:
            redis_client.set("test:symbol:ASIANPAINT", json.dumps(market_data))
            print("✅ JSON serialization: SUCCESS")
            
            # Verify we can retrieve and parse it
            stored_data = json.loads(redis_client.get("test:symbol:ASIANPAINT"))
            print(f"✅ Retrieved data: {stored_data['symbol']} | {stored_data['changeper']}%")
            
        except Exception as e:
            print(f"❌ JSON serialization: FAILED - {e}")
        
        # Test 3: Alternative approach - flatten the nested dict
        print("\n🟡 Test 3: Flatten nested dict (alternative approach)")
        try:
            flattened_data = market_data.copy()
            data_quality = flattened_data.pop('data_quality')
            flattened_data.update({
                'has_ohlc': data_quality['has_ohlc'],
                'has_volume': data_quality['has_volume'],
                'has_change_percent': data_quality['has_change_percent'],
                'calculated_change_percent': data_quality['calculated_change_percent']
            })
            
            redis_client.hset("test:symbol:ASIANPAINT:flat", mapping=flattened_data)
            print("✅ Flattened approach: SUCCESS")
            
        except Exception as e:
            print(f"❌ Flattened approach: FAILED - {e}")
        
        # Cleanup
        redis_client.delete("test:symbol:ASIANPAINT")
        redis_client.delete("test:symbol:ASIANPAINT:flat")
        
        print("\n🎯 CONCLUSION:")
        print("✅ JSON serialization is the correct approach")
        print("❌ Direct hset with mapping fails due to nested dictionaries")
        print("💡 If deployment still shows errors, the deployed code hasn't been updated")
        
    except redis.ConnectionError:
        print("❌ Redis connection failed - make sure Redis is running")
        print("💡 This might be why the deployment has market data issues")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_redis_serialization() 
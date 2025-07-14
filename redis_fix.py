#!/usr/bin/env python3
"""
Redis Configuration Fix
Reverts complex Redis configurations back to simple, working versions
"""

import os
import redis

def test_simple_redis():
    """Test simple Redis configuration"""
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        
        # SIMPLE configuration that works everywhere
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        client.ping()
        print(f"✅ Simple Redis config works: {redis_url[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Simple Redis config failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing simple Redis configuration...")
    test_simple_redis() 
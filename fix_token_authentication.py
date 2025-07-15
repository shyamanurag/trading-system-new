#!/usr/bin/env python3
"""
Direct Token Authentication Fix
Fixes the token authentication issue by ensuring tokens are stored correctly
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import redis.asyncio as redis
from urllib.parse import urlparse

async def get_redis_client():
    """Get Redis client with SSL support"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Parse Redis URL
    parsed = urlparse(redis_url)
    
    config = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 6379,
        'password': parsed.password,
        'db': int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0,
        'decode_responses': True,
        'socket_timeout': 10,
        'socket_connect_timeout': 10,
        'retry_on_timeout': True
    }
    
    # Add SSL for DigitalOcean
    if 'ondigitalocean.com' in redis_url or redis_url.startswith('rediss://'):
        config.update({
            'ssl': True,
            'ssl_cert_reqs': None,
            'ssl_check_hostname': False
        })
    
    return redis.Redis(**config)

async def fix_token_authentication():
    """Fix token authentication issue"""
    print("🔧 FIXING TOKEN AUTHENTICATION ISSUE")
    print("=" * 50)
    
    # Get environment variables
    env_user_id = os.getenv('ZERODHA_USER_ID', 'PAPER_TRADER_001')
    print(f"Target User ID: {env_user_id}")
    
    # Connect to Redis
    client = await get_redis_client()
    await client.ping()
    print("✅ Redis connected")
    
    # Find all existing tokens
    all_keys = await client.keys("zerodha:token:*")
    print(f"Found {len(all_keys)} existing token keys")
    
    found_token = None
    source_key = None
    
    # Look for any valid token
    for key in all_keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        token = await client.get(key)
        if token and len(token) > 20:  # Valid token should be longer
            found_token = token
            source_key = key_str
            print(f"✅ Found valid token: {key_str} -> {token[:15]}...")
            break
    
    if not found_token:
        print("❌ No valid token found in Redis")
        print("   Please authenticate via frontend first:")
        print("   https://algoauto-9gx56.ondigitalocean.app/zerodha")
        await client.close()
        return False
    
    # Check if orchestrator can find the token
    orchestrator_keys = [
        f"zerodha:token:{env_user_id}",
        "zerodha:token:PAPER_TRADER_001",
        "zerodha:token:QSW899"
    ]
    
    orchestrator_can_find = False
    for key in orchestrator_keys:
        token = await client.get(key)
        if token:
            orchestrator_can_find = True
            print(f"✅ Orchestrator can find token at: {key}")
            break
    
    if not orchestrator_can_find:
        print("🔧 Orchestrator cannot find token - fixing...")
        
        # Copy token to expected keys
        target_keys = [
            f"zerodha:token:{env_user_id}",
            "zerodha:token:PAPER_TRADER_001",
            "zerodha:token:QSW899"
        ]
        
        for target_key in target_keys:
            await client.set(target_key, found_token)
            print(f"✅ Copied token to: {target_key}")
        
        # Copy expiry information if available
        source_user_id = source_key.replace('zerodha:token:', '')
        source_expiry = await client.get(f"zerodha:token_expiry:{source_user_id}")
        
        if source_expiry:
            for target_key in target_keys:
                target_user_id = target_key.replace('zerodha:token:', '')
                await client.set(f"zerodha:token_expiry:{target_user_id}", source_expiry)
                print(f"✅ Copied expiry to: zerodha:token_expiry:{target_user_id}")
        else:
            # Set default expiry (18 hours from now)
            default_expiry = datetime.now() + timedelta(hours=18)
            for target_key in target_keys:
                target_user_id = target_key.replace('zerodha:token:', '')
                await client.set(f"zerodha:token_expiry:{target_user_id}", default_expiry.isoformat())
                print(f"✅ Set default expiry for: zerodha:token_expiry:{target_user_id}")
    
    # Verify the fix
    print("\n🔍 VERIFICATION:")
    for key in orchestrator_keys:
        token = await client.get(key)
        status = "✅ FOUND" if token else "❌ NOT FOUND"
        print(f"   {key}: {status}")
    
    await client.close()
    
    print("\n🎉 TOKEN AUTHENTICATION FIX COMPLETED!")
    print("   The orchestrator should now be able to find the token.")
    print("   Please restart the autonomous trading system.")
    
    return True

if __name__ == "__main__":
    asyncio.run(fix_token_authentication()) 
#!/usr/bin/env python3
"""
Zerodha Token Issue Diagnostic Script
Diagnoses and fixes token authentication issues between frontend and backend
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import redis.asyncio as redis
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_redis_client():
    """Get Redis client with proper SSL configuration"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Parse Redis URL for connection details
        parsed = urlparse(redis_url)
        
        config = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
            'password': parsed.password,
            'db': int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0,
            'decode_responses': True,
            'socket_timeout': 10,
            'socket_connect_timeout': 10,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
        
        # Add SSL configuration for DigitalOcean
        if 'ondigitalocean.com' in redis_url or redis_url.startswith('rediss://'):
            config.update({
                'ssl': True,
                'ssl_cert_reqs': None,
                'ssl_check_hostname': False
            })
            logger.info("🔐 Using SSL connection for DigitalOcean Redis")
        
        client = redis.Redis(**config)
        await client.ping()  # Test connection
        logger.info("✅ Redis connection successful")
        return client
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return None

async def diagnose_token_issue():
    """Comprehensive token diagnostic"""
    print("🔍 ZERODHA TOKEN DIAGNOSTIC")
    print("=" * 50)
    
    # Check environment variables
    env_user_id = os.getenv('ZERODHA_USER_ID', 'NOT_SET')
    env_api_key = os.getenv('ZERODHA_API_KEY', 'NOT_SET')
    env_access_token = os.getenv('ZERODHA_ACCESS_TOKEN', 'NOT_SET')
    
    print(f"📋 Environment Variables:")
    print(f"   ZERODHA_USER_ID: {env_user_id}")
    print(f"   ZERODHA_API_KEY: {'SET' if env_api_key != 'NOT_SET' else 'NOT_SET'}")
    print(f"   ZERODHA_ACCESS_TOKEN: {'SET' if env_access_token != 'NOT_SET' else 'NOT_SET'}")
    print()
    
    # Connect to Redis
    client = await get_redis_client()
    if not client:
        print("❌ Cannot connect to Redis - token diagnostic impossible")
        return
    
    # Search for all zerodha tokens
    print("🔍 Searching for all Zerodha tokens in Redis...")
    all_token_keys = await client.keys("zerodha:token:*")
    all_expiry_keys = await client.keys("zerodha:token_expiry:*")
    
    print(f"📊 Found {len(all_token_keys)} token keys and {len(all_expiry_keys)} expiry keys")
    print()
    
    # Display all tokens
    if all_token_keys:
        print("🔑 All Tokens Found:")
        for key in all_token_keys:
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                token = await client.get(key)
                user_id = key_str.replace('zerodha:token:', '')
                
                if token:
                    print(f"   {key_str}: {token[:15]}... (length: {len(token)})")
                    
                    # Check expiry
                    expiry_key = f"zerodha:token_expiry:{user_id}"
                    expiry_time = await client.get(expiry_key)
                    if expiry_time:
                        try:
                            expiry_dt = datetime.fromisoformat(expiry_time)
                            is_expired = expiry_dt <= datetime.now()
                            status = "EXPIRED" if is_expired else "VALID"
                            print(f"      Expiry: {expiry_time} ({status})")
                        except Exception as e:
                            print(f"      Expiry: ERROR parsing {expiry_time}")
                    else:
                        print(f"      Expiry: NO EXPIRY INFO")
                else:
                    print(f"   {key_str}: NO TOKEN")
            except Exception as e:
                print(f"   {key}: ERROR - {e}")
        print()
    else:
        print("❌ No tokens found in Redis")
        print()
    
    # Check what orchestrator looks for
    print("🤖 Orchestrator Token Search Simulation:")
    orchestrator_keys = [
        f"zerodha:token:{env_user_id}",
        "zerodha:token:PAPER_TRADER_001",
        "zerodha:token:QSW899",
        "zerodha:token:PAPER_TRADER_MAIN"
    ]
    
    found_token = None
    for key in orchestrator_keys:
        try:
            token = await client.get(key)
            status = "✅ FOUND" if token else "❌ NOT FOUND"
            print(f"   {key}: {status}")
            if token and not found_token:
                found_token = token
        except Exception as e:
            print(f"   {key}: ERROR - {e}")
    
    print()
    
    # Diagnosis and recommendations
    print("🩺 DIAGNOSIS:")
    if not all_token_keys:
        print("❌ NO TOKENS FOUND - Need to authenticate via frontend")
        print("   Recommendation: Go to https://algoauto-9gx56.ondigitalocean.app/zerodha and authenticate")
    elif not found_token:
        print("❌ TOKENS EXIST BUT ORCHESTRATOR CAN'T FIND THEM")
        print("   Recommendation: Migrate token to expected key")
        
        # Find the first valid token
        for key in all_token_keys:
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                token = await client.get(key)
                if token:
                    source_user_id = key_str.replace('zerodha:token:', '')
                    target_user_id = env_user_id if env_user_id != 'NOT_SET' else 'PAPER_TRADER_001'
                    
                    print(f"   MIGRATION NEEDED: {source_user_id} → {target_user_id}")
                    
                    # Perform migration
                    print("🔧 PERFORMING AUTOMATIC MIGRATION...")
                    try:
                        # Copy token
                        await client.set(f"zerodha:token:{target_user_id}", token)
                        
                        # Copy expiry if exists
                        source_expiry = await client.get(f"zerodha:token_expiry:{source_user_id}")
                        if source_expiry:
                            await client.set(f"zerodha:token_expiry:{target_user_id}", source_expiry)
                        
                        print(f"✅ Token migrated successfully!")
                        print(f"   New key: zerodha:token:{target_user_id}")
                        
                        # Verify migration
                        migrated_token = await client.get(f"zerodha:token:{target_user_id}")
                        if migrated_token:
                            print(f"✅ Migration verified: {migrated_token[:15]}...")
                        else:
                            print("❌ Migration verification failed")
                            
                    except Exception as e:
                        print(f"❌ Migration failed: {e}")
                    
                    break
            except Exception as e:
                continue
    else:
        print("✅ TOKEN FOUND - Orchestrator should be able to access it")
        print(f"   Token: {found_token[:15]}...")
        print("   If still having issues, check Redis connection reliability")
    
    await client.close()
    print()
    print("🏁 Diagnostic complete!")

async def main():
    """Main function"""
    await diagnose_token_issue()

if __name__ == "__main__":
    asyncio.run(main()) 
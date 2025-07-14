#!/usr/bin/env python3
"""
Comprehensive User ID Alignment Fix

This script fixes the user ID mismatch causing zero trades:
- Frontend auth: PAPER_TRADER_001
- Environment: QSW899  
- User Management: MASTER_CLIENT_001
- Orchestrator search: zerodha:token:QSW899

Solution: Align everything to use PAPER_TRADER_001
"""

import asyncio
import os
import sys
from datetime import datetime

# Handle Redis import
try:
    import redis
except ImportError:
    print("❌ Redis module not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
    import redis

# Add src to path
sys.path.append('src')

async def main():
    print("🔧 User ID Alignment Fix - Starting...")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get Redis credentials from environment
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD')
    redis_url = os.getenv('REDIS_URL')
    
    print(f"🔌 Redis Configuration:")
    print(f"   Host: {redis_host}")
    print(f"   Port: {redis_port}")
    print(f"   Password: {'***' if redis_password else 'None'}")
    print(f"   URL: {'***' if redis_url else 'None'}")
    
    # Connect to Redis
    try:
        if redis_url:
            redis_client = redis.from_url(redis_url, decode_responses=True)
        else:
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True
            )
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Tip: Make sure Redis credentials are set in environment variables")
        return
    
    print("\n📊 Current Redis Token Analysis:")
    
    # Find all zerodha tokens
    try:
        token_keys = redis_client.keys('zerodha:token:*')
        print(f"Found {len(token_keys)} token keys:")
        
        for key in token_keys:
            token_value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            print(f"  🔑 {key}: {token_value[:20] if token_value else 'None'}... (TTL: {ttl}s)")
    except Exception as e:
        print(f"❌ Error listing token keys: {e}")
        return
    
    # Check for the specific user IDs we know about
    user_ids_to_check = [
        'PAPER_TRADER_001',
        'QSW899', 
        'MASTER_CLIENT_001',
        'PAPER_TRADER_MAIN'
    ]
    
    print(f"\n🔍 Checking specific user IDs:")
    active_token = None
    active_user_id = None
    
    for user_id in user_ids_to_check:
        token_key = f"zerodha:token:{user_id}"
        try:
            token = redis_client.get(token_key)
            if token:
                print(f"  ✅ {user_id}: Token found ({token[:20]}...)")
                if not active_token:  # Use first found token
                    active_token = token
                    active_user_id = user_id
            else:
                print(f"  ❌ {user_id}: No token found")
        except Exception as e:
            print(f"  ❌ {user_id}: Error checking token - {e}")
    
    if not active_token:
        print("\n❌ No active tokens found. Please authenticate via Zerodha frontend first.")
        return
    
    print(f"\n🎯 Active Token Found: {active_user_id}")
    print(f"   Token: {active_token[:30]}...")
    
    # The fix: Ensure token is available under PAPER_TRADER_001 (the authenticated user)
    target_user_id = 'PAPER_TRADER_001'
    target_key = f"zerodha:token:{target_user_id}"
    
    if active_user_id != target_user_id:
        print(f"\n🔄 Copying token from {active_user_id} to {target_user_id}")
        
        try:
            # Copy the token to the target user ID
            redis_client.set(target_key, active_token)
            
            # Copy TTL if it exists
            ttl = redis_client.ttl(f"zerodha:token:{active_user_id}")
            if ttl > 0:
                redis_client.expire(target_key, ttl)
            
            print(f"✅ Token copied successfully")
        except Exception as e:
            print(f"❌ Error copying token: {e}")
            return
    else:
        print(f"✅ Token already under correct user ID: {target_user_id}")
    
    # Verify the fix
    print(f"\n🔍 Verification:")
    try:
        final_token = redis_client.get(target_key)
        if final_token:
            print(f"✅ Token accessible at {target_key}")
            print(f"   Token: {final_token[:30]}...")
            
            # Test Zerodha connection with this token
            try:
                try:
                    from kiteconnect import KiteConnect
                except ImportError:
                    print("⚠️  kiteconnect module not found - cannot test Zerodha connection")
                    KiteConnect = None
                
                if KiteConnect:
                    api_key = os.getenv('ZERODHA_API_KEY')
                    if api_key:
                        kite = KiteConnect(api_key=api_key)
                        kite.set_access_token(final_token)
                        
                        # Test connection
                        profile = kite.profile()
                        print(f"✅ Zerodha connection test successful")
                        print(f"   User ID from Zerodha: {profile.get('user_id')}")
                        print(f"   User Name: {profile.get('user_name')}")
                        print(f"   Broker: {profile.get('broker')}")
                        
                    else:
                        print("⚠️  ZERODHA_API_KEY not found - cannot test connection")
                        
            except Exception as e:
                print(f"❌ Zerodha connection test failed: {e}")
        else:
            print(f"❌ Token not found at {target_key}")
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    
    print(f"\n📝 Summary:")
    print(f"   Target User ID: {target_user_id}")
    print(f"   Token Key: {target_key}")
    print(f"   Status: {'✅ Ready' if final_token else '❌ Failed'}")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Update app.yaml: ACTIVE_USER_ID={target_user_id}")
    print(f"   2. Update app.yaml: ZERODHA_USER_ID={target_user_id}")
    print(f"   3. Restart orchestrator to pick up aligned user ID")
    print(f"   4. Verify trades start flowing")

if __name__ == "__main__":
    asyncio.run(main()) 
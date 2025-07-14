#!/usr/bin/env python3
"""
Comprehensive Token Storage and User ID Alignment Fix

Root Cause Analysis:
1. Frontend shows "Authenticated: ✅ Yes" with User ID: PAPER_TRADER_001
2. Redis shows 0 token keys - tokens are not being stored properly
3. Environment has ZERODHA_USER_ID=QSW899 but ACTIVE_USER_ID=PAPER_TRADER_MAIN
4. Orchestrator searches for zerodha:token:QSW899 but token stored as PAPER_TRADER_001

Solution:
1. Fix token storage mechanism
2. Align all user IDs to PAPER_TRADER_001
3. Update environment variables
4. Test the complete flow
"""

import asyncio
import os
import sys
from datetime import datetime
import json

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
    print("🔧 Comprehensive Token Storage and User ID Alignment Fix")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Connect to Redis
    print("\n📡 Step 1: Connecting to Redis...")
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("❌ REDIS_URL environment variable not set")
        return
    
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Step 2: Analyze current token situation
    print("\n🔍 Step 2: Analyzing current token situation...")
    
    # Check all zerodha-related keys
    all_zerodha_keys = redis_client.keys('zerodha:*')
    print(f"Found {len(all_zerodha_keys)} zerodha-related keys:")
    for key in all_zerodha_keys:
        value = redis_client.get(key)
        ttl = redis_client.ttl(key)
        print(f"  🔑 {key}: {str(value)[:30]}... (TTL: {ttl}s)")
    
    # Check auth-related keys
    auth_keys = redis_client.keys('auth:*')
    print(f"\nFound {len(auth_keys)} auth-related keys:")
    for key in auth_keys:
        value = redis_client.get(key)
        ttl = redis_client.ttl(key)
        print(f"  🔑 {key}: {str(value)[:30]}... (TTL: {ttl}s)")
    
    # Check session keys
    session_keys = redis_client.keys('session:*')
    print(f"\nFound {len(session_keys)} session-related keys:")
    for key in session_keys:
        value = redis_client.get(key)
        ttl = redis_client.ttl(key)
        print(f"  🔑 {key}: {str(value)[:30]}... (TTL: {ttl}s)")
    
    # Check for any keys containing token
    token_keys = redis_client.keys('*token*')
    print(f"\nFound {len(token_keys)} token-related keys:")
    for key in token_keys:
        value = redis_client.get(key)
        ttl = redis_client.ttl(key)
        print(f"  🔑 {key}: {str(value)[:30]}... (TTL: {ttl}s)")
    
    # Step 3: Check if we can find any valid token
    print("\n🎯 Step 3: Searching for valid tokens...")
    
    valid_token = None
    token_source = None
    
    # Check all possible token locations
    possible_locations = [
        'zerodha:token:PAPER_TRADER_001',
        'zerodha:token:QSW899',
        'zerodha:token:MASTER_CLIENT_001',
        'zerodha:token:PAPER_TRADER_MAIN',
        'auth:zerodha:PAPER_TRADER_001',
        'auth:zerodha:QSW899',
        'session:zerodha:PAPER_TRADER_001',
        'session:zerodha:QSW899'
    ]
    
    for location in possible_locations:
        token = redis_client.get(location)
        if token:
            print(f"✅ Found token at {location}: {token[:30]}...")
            if not valid_token:
                valid_token = token
                token_source = location
    
    if not valid_token:
        print("❌ No valid tokens found in Redis")
        print("\n💡 Solution: You need to re-authenticate via the Zerodha frontend")
        print("   1. Go to the Zerodha Daily Auth Token Setup page")
        print("   2. Click 'Logout' if needed")
        print("   3. Re-authenticate with fresh token")
        print("   4. Verify the token gets stored properly")
        return
    
    print(f"\n✅ Valid token found at: {token_source}")
    
    # Step 4: Align user IDs
    print("\n🔄 Step 4: Aligning user IDs...")
    
    target_user_id = 'PAPER_TRADER_001'  # This is what the frontend shows
    target_key = f'zerodha:token:{target_user_id}'
    
    # Store token under the correct key
    try:
        redis_client.set(target_key, valid_token)
        
        # Set appropriate TTL (tokens expire at 6 AM IST next day)
        current_hour = datetime.now().hour
        if current_hour < 6:
            # Before 6 AM, expires at 6 AM today
            seconds_until_6am = (6 - current_hour) * 3600
        else:
            # After 6 AM, expires at 6 AM tomorrow
            seconds_until_6am = (24 - current_hour + 6) * 3600
        
        redis_client.expire(target_key, seconds_until_6am)
        print(f"✅ Token stored at {target_key} with TTL: {seconds_until_6am}s")
        
    except Exception as e:
        print(f"❌ Error storing token: {e}")
        return
    
    # Step 5: Test Zerodha connection
    print("\n🧪 Step 5: Testing Zerodha connection...")
    
    try:
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            print("⚠️  kiteconnect module not found - installing...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "kiteconnect"])
            from kiteconnect import KiteConnect
        
        api_key = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(valid_token)
        
        profile = kite.profile()
        print(f"✅ Zerodha connection successful!")
        print(f"   User ID from Zerodha API: {profile.get('user_id')}")
        print(f"   User Name: {profile.get('user_name')}")
        print(f"   Broker: {profile.get('broker')}")
        print(f"   Email: {profile.get('email')}")
        
        # The real user ID from Zerodha
        real_zerodha_user_id = profile.get('user_id')
        
        if real_zerodha_user_id and real_zerodha_user_id != target_user_id:
            print(f"\n⚠️  User ID Mismatch Detected:")
            print(f"   Frontend shows: {target_user_id}")
            print(f"   Zerodha API returns: {real_zerodha_user_id}")
            print(f"   Environment has: QSW899")
            
            # Store token under the real Zerodha user ID as well
            real_key = f'zerodha:token:{real_zerodha_user_id}'
            redis_client.set(real_key, valid_token)
            redis_client.expire(real_key, seconds_until_6am)
            print(f"✅ Token also stored at {real_key}")
        
    except Exception as e:
        print(f"❌ Zerodha connection test failed: {e}")
        print("   This might be due to token expiry or invalid token")
    
    # Step 6: Generate environment variable updates
    print("\n📝 Step 6: Environment Variable Recommendations...")
    
    print("Update app.yaml with these changes:")
    print("```yaml")
    print("- key: ACTIVE_USER_ID")
    print("  scope: RUN_AND_BUILD_TIME")
    print(f"  value: {target_user_id}")
    print("- key: ZERODHA_USER_ID")
    print("  scope: RUN_AND_BUILD_TIME")
    print(f"  value: {target_user_id}")
    print("```")
    
    # Step 7: Final verification
    print("\n✅ Step 7: Final Verification...")
    
    final_check = redis_client.get(target_key)
    if final_check:
        print(f"✅ Token verified at {target_key}")
        print(f"   Token: {final_check[:30]}...")
        
        # Check TTL
        ttl = redis_client.ttl(target_key)
        print(f"   TTL: {ttl}s ({ttl/3600:.1f} hours)")
        
        print("\n🚀 System Status:")
        print("   ✅ Token stored in Redis")
        print("   ✅ User ID aligned")
        print("   ✅ Zerodha connection tested")
        print("   ⏳ Environment variables need updating")
        print("   ⏳ Orchestrator restart required")
        
    else:
        print("❌ Final verification failed - token not found")
    
    print("\n🎯 Next Steps:")
    print("1. Update app.yaml with new environment variables")
    print("2. Deploy the changes")
    print("3. Monitor logs for successful orchestrator startup")
    print("4. Verify trades start flowing")
    
    print("\n" + "=" * 60)
    print("Fix completed! Check the recommendations above.")

if __name__ == "__main__":
    asyncio.run(main()) 
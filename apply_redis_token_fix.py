#!/usr/bin/env python3
"""
Apply Redis Token Storage Fix

This script directly fixes the token storage issue by adding Redis storage
to the zerodha_manual_auth.py file after the session storage.
"""

import os
import re

def apply_fix():
    file_path = "src/api/zerodha_manual_auth.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The fix code to insert after session storage
    redis_fix = """
        # CRITICAL FIX: Store token in Redis for orchestrator access
        try:
            import redis
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    password=os.getenv('REDIS_PASSWORD'),
                    decode_responses=True
                )
            
            redis_key = f"zerodha:token:{token_data.user_id}"
            
            # Store token with expiration (tokens expire at 6 AM IST next day)
            from datetime import datetime
            current_hour = datetime.now().hour
            if current_hour < 6:
                seconds_until_6am = (6 - current_hour) * 3600
            else:
                seconds_until_6am = (24 - current_hour + 6) * 3600
            
            redis_client.set(redis_key, access_token, ex=seconds_until_6am)
            logger.info(f"✅ Token stored in Redis at {redis_key} with TTL: {seconds_until_6am}s")
            
        except Exception as e:
            logger.error(f"⚠️  Failed to store token in Redis: {e}")
            # Don't fail the request, just log the error
"""
    
    # Find the line where session is stored and insert Redis fix after it
    pattern = r'(zerodha_sessions\[token_data\.user_id\] = session\s*)'
    
    if re.search(pattern, content):
        # Insert the Redis fix after the session storage
        new_content = re.sub(pattern, r'\1' + redis_fix, content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Redis token storage fix applied successfully!")
        return True
    else:
        print("❌ Could not find session storage line to patch")
        return False

if __name__ == "__main__":
    print("🔧 Applying Redis Token Storage Fix...")
    success = apply_fix()
    
    if success:
        print("\n🎯 Fix Summary:")
        print("   - Added Redis token storage to zerodha_manual_auth.py")
        print("   - Tokens now stored with proper expiration")
        print("   - Orchestrator can access tokens from Redis")
        print("   - Frontend authentication will now work with backend")
        
        print("\n🚀 Next Steps:")
        print("   1. Commit and deploy this fix")
        print("   2. Re-authenticate via Zerodha frontend")
        print("   3. Verify token appears in Redis")
        print("   4. Check if trades start flowing")
    else:
        print("\n❌ Fix failed - manual intervention required") 
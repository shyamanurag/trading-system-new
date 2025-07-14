#!/usr/bin/env python3
"""
Fix Token Storage Issue

This script patches the zerodha_manual_auth.py file to store tokens in Redis
instead of just in-memory dictionary.
"""

import os
import sys

def fix_token_storage():
    """Fix the token storage issue in zerodha_manual_auth.py"""
    
    file_path = "src/api/zerodha_manual_auth.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the token storage section
    old_code = """        # Store session
        zerodha_sessions[token_data.user_id] = session
        
        logger.info(f"✅ Authentication successful for user: {token_data.user_id}")"""
    
    new_code = """        # Store session in memory
        zerodha_sessions[token_data.user_id] = session
        
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
                # Before 6 AM, expires at 6 AM today
                seconds_until_6am = (6 - current_hour) * 3600
            else:
                # After 6 AM, expires at 6 AM tomorrow
                seconds_until_6am = (24 - current_hour + 6) * 3600
            
            redis_client.set(redis_key, access_token, ex=seconds_until_6am)
            logger.info(f"✅ Token stored in Redis at {redis_key} with TTL: {seconds_until_6am}s")
            
        except Exception as e:
            logger.error(f"⚠️  Failed to store token in Redis: {e}")
            # Don't fail the request, just log the error
        
        logger.info(f"✅ Authentication successful for user: {token_data.user_id}")"""
    
    if old_code in content:
        # Apply the fix
        new_content = content.replace(old_code, new_code)
        
        # Write the updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Token storage fix applied to {file_path}")
        return True
    else:
        print(f"❌ Could not find the target code section in {file_path}")
        print("The file may have been modified already or the structure changed.")
        return False

if __name__ == "__main__":
    print("🔧 Applying Token Storage Fix...")
    success = fix_token_storage()
    
    if success:
        print("\n✅ Fix applied successfully!")
        print("📝 Changes made:")
        print("   - Added Redis token storage to zerodha_manual_auth.py")
        print("   - Tokens now stored with proper expiration")
        print("   - Orchestrator can now access tokens from Redis")
        print("\n🚀 Next steps:")
        print("   1. Commit and deploy the fix")
        print("   2. Re-authenticate via Zerodha frontend")
        print("   3. Verify token appears in Redis")
        print("   4. Check if trades start flowing")
    else:
        print("\n❌ Fix failed. Manual intervention required.")
        sys.exit(1) 
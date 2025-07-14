#!/usr/bin/env python3
"""
Comprehensive Authentication Flow Test

This script tests the complete authentication flow:
1. Get fresh authorization URL
2. Guide user through token submission
3. Verify Redis storage
4. Test system integration
"""

import requests
import json
import os
import sys
from datetime import datetime
import webbrowser

# Add src to path
sys.path.append('src')

def test_complete_flow():
    """Test the complete authentication flow"""
    
    print("🔐 Comprehensive Authentication Flow Test")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "https://algoauto-9gx56.ondigitalocean.app"
    
    print(f"\n🌐 Step 1: Getting fresh authorization URL...")
    
    try:
        # Get the authorization URL
        auth_url_endpoint = f"{base_url}/auth/zerodha/auth-url"
        response = requests.get(auth_url_endpoint, timeout=10)
        
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data.get('auth_url')
            
            print(f"   ✅ Authorization URL retrieved")
            print(f"   URL: {auth_url}")
            
            print(f"\n📋 Step 2: Manual Authentication Required")
            print(f"   1. Copy this URL and open in browser:")
            print(f"      {auth_url}")
            print(f"   2. Login to Zerodha")
            print(f"   3. Authorize the application")
            print(f"   4. Copy the request token from the callback URL")
            print(f"   5. Use the frontend auth page to submit the token")
            
            # Try to open the URL automatically
            try:
                webbrowser.open(auth_url)
                print(f"   🌐 Browser opened automatically")
            except:
                print(f"   ⚠️  Could not open browser automatically")
            
        else:
            print(f"   ❌ Failed to get auth URL: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error getting auth URL: {e}")
        return False
    
    print(f"\n🔍 Step 3: Checking current system status...")
    
    # Check current system status
    try:
        status_url = f"{base_url}/api/v1/system/status"
        status_response = requests.get(status_url, timeout=10)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ System status retrieved")
            print(f"   System Ready: {status_data.get('system_ready', 'Unknown')}")
            print(f"   Active User: {status_data.get('active_user_id', 'Unknown')}")
            print(f"   Zerodha Status: {status_data.get('zerodha_status', 'Unknown')}")
            
            # Check if we're in demo mode
            if 'DEMO' in str(status_data.get('active_user_id', '')):
                print(f"   ⚠️  Currently in DEMO mode - needs real token")
            else:
                print(f"   ✅ Using real user ID")
                
        else:
            print(f"   ⚠️  System status: {status_response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  System status check failed: {e}")
    
    print(f"\n📊 Step 4: Checking Redis token storage...")
    
    # Check Redis for existing tokens
    try:
        os.environ['REDIS_URL'] = 'rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061'
        
        import redis
        redis_client = redis.from_url(os.environ['REDIS_URL'], decode_responses=True)
        redis_client.ping()
        print(f"   ✅ Redis connection successful")
        
        # Check for tokens
        token_keys = redis_client.keys('zerodha:token:*')
        print(f"   Found {len(token_keys)} token keys:")
        
        for key in token_keys:
            token_value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            print(f"     🔑 {key}: {token_value[:20] if token_value else 'None'}... (TTL: {ttl}s)")
        
        # Check specific user ID
        target_key = "zerodha:token:PAPER_TRADER_001"
        target_token = redis_client.get(target_key)
        
        if target_token:
            print(f"   ✅ Target token found: {target_key}")
            print(f"   Token: {target_token[:30]}...")
            
            # Test the token
            try:
                from kiteconnect import KiteConnect
                kite = KiteConnect(api_key='sylcoq492qz6f7ej')
                kite.set_access_token(target_token)
                profile = kite.profile()
                print(f"   ✅ Token is valid - User: {profile.get('user_name')}")
                
            except Exception as e:
                print(f"   ❌ Token validation failed: {e}")
                print(f"   Token may be expired - need fresh authentication")
                
        else:
            print(f"   ❌ No token found for PAPER_TRADER_001")
            print(f"   Need to authenticate via frontend")
            
    except ImportError:
        print(f"   ⚠️  Redis module not available for local testing")
    except Exception as e:
        print(f"   ❌ Redis check failed: {e}")
    
    print(f"\n🎯 Step 5: Testing authentication endpoint...")
    
    # Test the authentication status endpoint
    try:
        auth_status_url = f"{base_url}/auth/zerodha/status"
        auth_response = requests.get(auth_status_url, params={'user_id': 'PAPER_TRADER_001'}, timeout=10)
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            print(f"   ✅ Auth status retrieved")
            print(f"   Authenticated: {auth_data.get('authenticated', False)}")
            print(f"   User ID: {auth_data.get('user_id', 'Unknown')}")
            print(f"   Message: {auth_data.get('message', 'No message')}")
            
            if auth_data.get('authenticated'):
                print(f"   ✅ User is authenticated!")
            else:
                print(f"   ❌ User needs to authenticate")
                
        else:
            print(f"   ⚠️  Auth status: {auth_response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Auth status check failed: {e}")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Use the authorization URL above to get a fresh token")
    print(f"   2. Go to: {base_url}/auth/zerodha/")
    print(f"   3. Submit the fresh request token")
    print(f"   4. Verify authentication works")
    print(f"   5. Check that trades start flowing")
    
    print(f"\n📱 Frontend Authentication Page:")
    print(f"   {base_url}/auth/zerodha/")
    
    print(f"\n🔧 Our Fix Status:")
    print(f"   ✅ Redis token storage implemented")
    print(f"   ✅ User ID alignment completed")
    print(f"   ✅ Environment variables updated")
    print(f"   ⏳ Waiting for fresh token submission")
    
    return True

if __name__ == "__main__":
    test_complete_flow() 
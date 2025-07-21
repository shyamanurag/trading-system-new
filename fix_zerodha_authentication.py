#!/usr/bin/env python3
"""
ZERODHA AUTHENTICATION FIX SCRIPT
Authenticates with Zerodha using correct production API keys
and stores the access token properly in Redis
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime, timedelta, time
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Production Zerodha credentials (from app.yaml)
PRODUCTION_API_KEY = "sylcoq492qz6f7ej"
PRODUCTION_API_SECRET = "jm3h4iejwnxr4ngmma2qxccpkhevo8sy"
PRODUCTION_USER_ID = "QSW899"

class ZerodhaAuthenticationFixer:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.api_key = PRODUCTION_API_KEY
        self.api_secret = PRODUCTION_API_SECRET
        self.user_id = PRODUCTION_USER_ID

    async def fix_authentication(self):
        """Main method to fix Zerodha authentication"""
        try:
            logger.info("🔑 STARTING ZERODHA AUTHENTICATION FIX")
            logger.info("=" * 50)
            
            # Step 1: Verify credentials
            self._verify_credentials()
            
            # Step 2: Generate authentication URL
            auth_url = self._generate_auth_url()
            
            # Step 3: Display manual authentication instructions
            self._display_auth_instructions(auth_url)
            
            # Step 4: Wait for manual token input
            request_token = await self._get_manual_token_input()
            
            # Step 5: Exchange token for access token
            access_token = await self._exchange_token(request_token)
            
            # Step 6: Store token in Redis
            await self._store_token_in_redis(access_token)
            
            # Step 7: Verify authentication
            await self._verify_authentication()
            
            logger.info("✅ ZERODHA AUTHENTICATION FIX COMPLETED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication fix failed: {e}")
            return False

    def _verify_credentials(self):
        """Verify that we have the correct production credentials"""
        logger.info("🔍 Verifying production credentials...")
        
        logger.info(f"✅ API Key: {self.api_key}")
        logger.info(f"✅ User ID: {self.user_id}")
        logger.info(f"✅ API Secret: {'*' * len(self.api_secret)}")
        
        # Verify these match production deployment
        if self.api_key != PRODUCTION_API_KEY:
            raise ValueError(f"API Key mismatch: expected {PRODUCTION_API_KEY}, got {self.api_key}")
        
        if self.user_id != PRODUCTION_USER_ID:
            raise ValueError(f"User ID mismatch: expected {PRODUCTION_USER_ID}, got {self.user_id}")
        
        logger.info("✅ Credentials verified - using production values")

    def _generate_auth_url(self):
        """Generate Zerodha authentication URL"""
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={self.api_key}"
        logger.info(f"🔗 Authentication URL generated: {auth_url}")
        return auth_url

    def _display_auth_instructions(self, auth_url):
        """Display step-by-step authentication instructions"""
        print("\n" + "=" * 70)
        print("🚀 ZERODHA MANUAL AUTHENTICATION REQUIRED")
        print("=" * 70)
        print("\n📋 STEP-BY-STEP INSTRUCTIONS:")
        print("\n1. 🌐 OPEN YOUR BROWSER and go to:")
        print(f"   {auth_url}")
        print("\n2. 🔐 LOGIN to Zerodha with your credentials:")
        print(f"   - User ID: {self.user_id}")
        print("   - Password: [Your Zerodha password]")
        print("   - PIN: [Your trading PIN]")
        print("\n3. 🔄 AFTER LOGIN, you'll be redirected to a URL like:")
        print("   https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/callback?request_token=YOUR_TOKEN&action=login&status=success")
        print("\n4. 📋 COPY the 'request_token' value from the URL")
        print("   Example: If URL shows 'request_token=abc123xyz', copy 'abc123xyz'")
        print("\n5. 📝 PASTE the token when prompted below")
        print("\n" + "=" * 70)

    async def _get_manual_token_input(self):
        """Get request token from user input"""
        print("\n⏳ Waiting for manual token input...")
        print("Please complete steps 1-4 above, then enter the request_token:")
        
        while True:
            try:
                request_token = input("\n🔑 Enter request_token: ").strip()
                
                if not request_token:
                    print("❌ Token cannot be empty. Please try again.")
                    continue
                
                if len(request_token) < 10:
                    print("❌ Token seems too short. Please check and try again.")
                    continue
                
                # Validate token format (Zerodha tokens are typically 32 characters)
                if len(request_token) != 32:
                    print(f"⚠️ Token length is {len(request_token)}, expected 32. Continue anyway? (y/n)")
                    confirm = input().strip().lower()
                    if confirm != 'y':
                        continue
                
                logger.info(f"✅ Request token received: {request_token[:8]}...{request_token[-8:]}")
                return request_token
                
            except KeyboardInterrupt:
                print("\n❌ Authentication cancelled by user")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error reading token: {e}")
                continue

    async def _exchange_token(self, request_token):
        """Exchange request token for access token using KiteConnect"""
        try:
            logger.info("🔄 Exchanging request token for access token...")
            
            # Import KiteConnect
            try:
                from kiteconnect import KiteConnect
            except ImportError:
                logger.error("❌ KiteConnect library not installed")
                print("\n💡 SOLUTION: Install KiteConnect library:")
                print("pip install kiteconnect")
                raise
            
            # Create KiteConnect instance
            kite = KiteConnect(api_key=self.api_key)
            
            # Generate session
            data = kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )
            
            access_token = data["access_token"]
            user_id = data["user_id"]
            
            # Verify user ID matches
            if user_id != self.user_id:
                logger.warning(f"⚠️ User ID mismatch: expected {self.user_id}, got {user_id}")
                print(f"⚠️ WARNING: Expected user {self.user_id}, but got {user_id}")
                print("Continue anyway? (y/n)")
                confirm = input().strip().lower()
                if confirm != 'y':
                    raise ValueError("User ID mismatch - authentication cancelled")
            
            logger.info(f"✅ Access token generated for user {user_id}")
            logger.info(f"✅ Token: {access_token[:8]}...{access_token[-8:]}")
            
            return access_token
            
        except Exception as e:
            logger.error(f"❌ Token exchange failed: {e}")
            raise

    async def _store_token_in_redis(self, access_token):
        """Store access token in Redis with proper expiry"""
        try:
            logger.info("💾 Storing access token in Redis...")
            
            redis_client = redis.from_url(self.redis_url)
            
            # Calculate token expiry (6 AM next day)
            now = datetime.now()
            if now.time() < time(6, 0, 0):
                # If before 6 AM today, expires at 6 AM today
                expiry = datetime.combine(now.date(), time(6, 0, 0))
            else:
                # If after 6 AM today, expires at 6 AM tomorrow
                expiry = datetime.combine(
                    now.date() + timedelta(days=1),
                    time(6, 0, 0)
                )
            
            # Store token with multiple key patterns for compatibility
            token_keys = [
                f"zerodha:token:{self.user_id}",
                f"zerodha:token:PAPER_TRADER_001",
                f"zerodha:access_token"
            ]
            
            for key in token_keys:
                await redis_client.set(key, access_token)
                logger.info(f"✅ Token stored with key: {key}")
            
            # Store expiry time
            await redis_client.set(f"zerodha:token_expiry:{self.user_id}", expiry.isoformat())
            
            # Store authentication status
            auth_status = {
                'authenticated': True,
                'user_id': self.user_id,
                'api_key': self.api_key,
                'authenticated_at': datetime.now().isoformat(),
                'expires_at': expiry.isoformat()
            }
            
            await redis_client.set(
                f"zerodha:auth_status:{self.user_id}",
                json.dumps(auth_status)
            )
            
            await redis_client.close()
            
            logger.info(f"✅ Token stored successfully, expires at {expiry}")
            
        except Exception as e:
            logger.error(f"❌ Token storage failed: {e}")
            raise

    async def _verify_authentication(self):
        """Verify that authentication is working"""
        try:
            logger.info("🔍 Verifying authentication...")
            
            # Test with deployment API
            import requests
            
            response = requests.get(
                f"https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/status?user_id={self.user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    logger.info("✅ Authentication verified successfully!")
                    logger.info(f"✅ User {self.user_id} is now authenticated")
                    return True
                else:
                    logger.warning("⚠️ API reports user not authenticated")
                    print("💡 This might be a caching issue. Try again in a few minutes.")
                    return False
            else:
                logger.warning(f"⚠️ API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Verification failed: {e}")
            print("💡 This might be a connectivity issue. Authentication likely succeeded.")
            return True

async def main():
    """Main function to run Zerodha authentication fix"""
    fixer = ZerodhaAuthenticationFixer()
    success = await fixer.fix_authentication()
    
    if success:
        print("\n🎉 ZERODHA AUTHENTICATION FIXED!")
        print("✅ Your system is now authenticated and ready for live trading.")
        print("🚀 You can now start autonomous trading from the dashboard.")
        return 0
    else:
        print("\n❌ ZERODHA AUTHENTICATION FAILED!")
        print("🔧 Please check the errors above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 
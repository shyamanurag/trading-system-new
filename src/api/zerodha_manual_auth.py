"""
Zerodha Manual Token Authentication
For users who need to manually extract and paste tokens
"""

import logging
import os
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zerodha-manual", tags=["zerodha-manual"])

class ManualTokenRequest(BaseModel):
    """Manual token submission model"""
    request_token: str
    user_id: Optional[str] = "ZERODHA_DEFAULT"

class TokenStatus(BaseModel):
    """Token status response"""
    success: bool
    message: str
    authenticated: bool = False
    user_id: Optional[str] = None
    token_expires_at: Optional[str] = None
    access_token_preview: Optional[str] = None

@router.get("/auth-url")
async def get_manual_auth_url():
    """Get Zerodha authorization URL for manual token extraction"""
    try:
        api_key = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
        
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "instructions": [
                "1. Click the authorization URL",
                "2. Login to Zerodha with your credentials", 
                "3. After login, you'll be redirected to a URL",
                "4. Copy the 'request_token' parameter from the redirected URL",
                "5. Paste the token in the manual token entry below"
            ],
            "example_redirect": "https://yourapp.com/callback?request_token=YOUR_TOKEN_HERE&action=login&status=success",
            "note": "Extract only the request_token value, not the full URL"
        }
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-token", response_model=TokenStatus)
async def submit_manual_token(request: ManualTokenRequest, background_tasks: BackgroundTasks):
    """Submit manually extracted request token"""
    try:
        logger.info(f"Processing manual token for user: {request.user_id}")
        logger.info(f"Token preview: {request.request_token[:10]}...")
        
        # Validate token format
        if not request.request_token or len(request.request_token) < 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid request token format. Token should be at least 10 characters long."
            )
        
        # Get credentials
        api_key = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
        api_secret = os.getenv('ZERODHA_API_SECRET', 'jm3h4iejwnxr4ngmma2qxccpkhevo8sy')
        
        if not api_key or not api_secret:
            raise HTTPException(
                status_code=500,
                detail="Zerodha API credentials not configured"
            )
        
        # Process token in background
        background_tasks.add_task(process_manual_token, request.request_token, request.user_id)
        
        return TokenStatus(
            success=True,
            message="Token submitted successfully. Processing in background...",
            authenticated=False,
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Manual token submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_manual_token(request_token: str, user_id: str):
    """Process the manual token to get access token"""
    try:
        logger.info(f"Processing manual token for user: {user_id}")
        
        # Import KiteConnect
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            logger.error("kiteconnect library not installed")
            return False
        
        # Get credentials
        api_key = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
        api_secret = os.getenv('ZERODHA_API_SECRET', 'jm3h4iejwnxr4ngmma2qxccpkhevo8sy')
        
        # Create KiteConnect instance
        kite = KiteConnect(api_key=api_key)
        
        # Generate session using request token
        session_data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = session_data['access_token']
        zerodha_user_id = session_data['user_id']
        
        logger.info(f"Access token generated for Zerodha user: {zerodha_user_id}")
        
        # Store tokens in Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        # Store access token (expires daily at 6 AM)
        token_key = f"zerodha_manual:{user_id}:access_token"
        user_key = f"zerodha_manual:{user_id}:user_id"
        status_key = f"zerodha_manual:{user_id}:status"
        
        # Set tokens with expiration
        await redis_client.setex(token_key, timedelta(hours=24), access_token)
        await redis_client.setex(user_key, timedelta(hours=24), zerodha_user_id)
        
        # Set status
        status_data = {
            "authenticated": True,
            "user_id": zerodha_user_id,
            "token_generated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "method": "manual_token"
        }
        await redis_client.setex(status_key, timedelta(hours=24), str(status_data))
        
        await redis_client.close()
        
        logger.info(f"✅ Manual token processing completed for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Manual token processing failed: {e}")
        return False

@router.get("/status", response_model=TokenStatus)
async def get_manual_auth_status(user_id: str = "ZERODHA_DEFAULT"):
    """Get current authentication status for manual token"""
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        # Check stored status
        token_key = f"zerodha_manual:{user_id}:access_token"
        user_key = f"zerodha_manual:{user_id}:user_id"
        
        access_token = await redis_client.get(token_key)
        zerodha_user_id = await redis_client.get(user_key)
        
        await redis_client.close()
        
        if access_token and zerodha_user_id:
            return TokenStatus(
                success=True,
                message="Authenticated with manual token",
                authenticated=True,
                user_id=zerodha_user_id,
                token_expires_at="Daily at 6:00 AM IST",
                access_token_preview=f"{access_token[:8]}..."
            )
        else:
            return TokenStatus(
                success=True,
                message="Not authenticated. Please submit manual token.",
                authenticated=False,
                user_id=user_id
            )
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return TokenStatus(
            success=False,
            message=f"Status check failed: {str(e)}",
            authenticated=False
        )

@router.delete("/logout")
async def logout_manual_auth(user_id: str = "ZERODHA_DEFAULT"):
    """Logout and clear manual authentication"""
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        # Clear all stored data
        keys_to_delete = [
            f"zerodha_manual:{user_id}:access_token",
            f"zerodha_manual:{user_id}:user_id", 
            f"zerodha_manual:{user_id}:status"
        ]
        
        for key in keys_to_delete:
            await redis_client.delete(key)
        
        await redis_client.close()
        
        return {
            "success": True,
            "message": "Manual authentication cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-connection")
async def test_zerodha_connection(user_id: str = "ZERODHA_DEFAULT"):
    """Test Zerodha connection with stored token"""
    try:
        # Get stored token
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        token_key = f"zerodha_manual:{user_id}:access_token"
        access_token = await redis_client.get(token_key)
        
        await redis_client.close()
        
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="No access token found. Please authenticate first."
            )
        
        # Test connection
        from kiteconnect import KiteConnect
        api_key = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Get user profile to test connection
        profile = kite.profile()
        
        # Get a sample quote (slower than TrueData as mentioned)
        try:
            quote = kite.quote(['NSE:NIFTY 50'])
            sample_data = quote.get('NSE:NIFTY 50', {})
            ltp = sample_data.get('last_price', 'N/A')
        except:
            ltp = "Unable to fetch"
        
        return {
            "success": True,
            "message": "Zerodha connection successful",
            "profile": {
                "user_id": profile.get('user_id'),
                "user_name": profile.get('user_name'),
                "email": profile.get('email')
            },
            "sample_data": {
                "symbol": "NIFTY 50",
                "ltp": ltp,
                "note": "Zerodha data fetches slower than TrueData as expected"
            }
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to get access token for other parts of the system
async def get_manual_access_token(user_id: str = "ZERODHA_DEFAULT") -> Optional[str]:
    """Get stored access token for system use"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        token_key = f"zerodha_manual:{user_id}:access_token"
        access_token = await redis_client.get(token_key)
        
        await redis_client.close()
        return access_token
    except:
        return None 
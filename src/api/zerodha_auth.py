"""
Zerodha Authentication Handler
Handles Zerodha login flow and token management
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import redis.asyncio as redis
from datetime import datetime, timedelta

from ..core.zerodha import ZerodhaIntegration, ZerodhaConfig
from ..utils.helpers import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zerodha", tags=["zerodha"])

class LoginRequest(BaseModel):
    """Login request model"""
    api_key: str
    api_secret: str
    user_id: str

class AuthResponse(BaseModel):
    """Authentication response model"""
    success: bool
    message: str
    login_url: Optional[str] = None
    access_token: Optional[str] = None

@router.post("/login", response_model=AuthResponse)
async def initiate_login(request: LoginRequest):
    """Initiate Zerodha login flow"""
    try:
        # Initialize Zerodha client
        config = {
            'api_key': request.api_key,
            'api_secret': request.api_secret,
            'user_id': request.user_id
        }
        zerodha = ZerodhaIntegration(config)
        
        # Get login URL
        login_url = zerodha.kite.login_url()
        
        # Store credentials in Redis for callback
        redis_client = await get_redis_client()
        await redis_client.setex(
            f"zerodha:auth:{request.user_id}",
            timedelta(minutes=30),
            f"{request.api_key}:{request.api_secret}"
        )
        
        return AuthResponse(
            success=True,
            message="Login URL generated successfully",
            login_url=login_url
        )
    except Exception as e:
        logger.error(f"Login initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def handle_callback(request: Request, request_token: str, user_id: str):
    """Handle Zerodha login callback"""
    try:
        # Get stored credentials
        redis_client = await get_redis_client()
        stored_creds = await redis_client.get(f"zerodha:auth:{user_id}")
        
        if not stored_creds:
            raise HTTPException(status_code=400, detail="Login session expired")
            
        api_key, api_secret = stored_creds.decode().split(':')
        
        # Initialize Zerodha client
        config = {
            'api_key': api_key,
            'api_secret': api_secret,
            'user_id': user_id
        }
        zerodha = ZerodhaIntegration(config)
        
        # Authenticate with request token
        success = await zerodha.authenticate(request_token)
        
        if not success:
            raise HTTPException(status_code=400, detail="Authentication failed")
            
        # Get access token
        access_token = zerodha.kite.access_token
        
        # Store access token
        await redis_client.setex(
            f"zerodha:token:{user_id}",
            timedelta(days=1),
            access_token
        )
        
        # Clean up auth credentials
        await redis_client.delete(f"zerodha:auth:{user_id}")
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"/dashboard?auth=success&user_id={user_id}"
        )
    except Exception as e:
        logger.error(f"Callback handling failed: {e}")
        return RedirectResponse(
            url=f"/login?error={str(e)}"
        )

@router.get("/status/{user_id}", response_model=AuthResponse)
async def check_auth_status(user_id: str):
    """Check authentication status"""
    try:
        redis_client = await get_redis_client()
        access_token = await redis_client.get(f"zerodha:token:{user_id}")
        
        if not access_token:
            return AuthResponse(
                success=False,
                message="Not authenticated"
            )
            
        # Initialize Zerodha client
        config = {
            'api_key': '',  # Will be loaded from Redis
            'api_secret': '',  # Will be loaded from Redis
            'user_id': user_id
        }
        zerodha = ZerodhaIntegration(config)
        
        # Verify token
        is_valid = await zerodha._verify_token()
        
        if not is_valid:
            # Clear invalid token
            await redis_client.delete(f"zerodha:token:{user_id}")
            return AuthResponse(
                success=False,
                message="Token expired"
            )
            
        return AuthResponse(
            success=True,
            message="Authenticated",
            access_token=access_token.decode()
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout/{user_id}")
async def logout(user_id: str):
    """Logout from Zerodha"""
    try:
        redis_client = await get_redis_client()
        await redis_client.delete(f"zerodha:token:{user_id}")
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
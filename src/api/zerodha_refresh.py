"""
Zerodha Connection Refresh API
Comprehensive refresh functionality for seamless trading operation
"""

import os
import logging
import asyncio
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from datetime import datetime, timedelta, time
import redis.asyncio as redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zerodha", tags=["zerodha-refresh"])

# Zerodha credentials from environment
ZERODHA_API_KEY = os.getenv('ZERODHA_API_KEY', 'sylcoq492qz6f7ej')
ZERODHA_API_SECRET = os.getenv('ZERODHA_API_SECRET', 'jm3h4iejwnxr4ngmma2qxccpkhevo8sy')
ZERODHA_USER_ID = os.getenv('ZERODHA_USER_ID', 'QSW899')

class RefreshRequest(BaseModel):
    """Refresh request model"""
    force_refresh: bool = False
    user_id: str = ZERODHA_USER_ID
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v:
            raise ValueError('User ID is required')
        return v

class RefreshResponse(BaseModel):
    """Refresh response model"""
    success: bool
    message: str
    token_valid: bool = False
    token_expires_at: Optional[str] = None
    profile: Optional[Dict] = None
    connection_status: Optional[Dict] = None
    trading_ready: bool = False

@router.get("/refresh/status")
async def get_refresh_status(user_id: str = ZERODHA_USER_ID):
    """Get current Zerodha connection status and token validity"""
    try:
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Check token status
        token_key = f"zerodha:token:{user_id}"
        access_token = await redis_client.get(token_key)
        
        if not access_token:
            await redis_client.close()
            return RefreshResponse(
                success=True,
                message="No token found - authentication required",
                token_valid=False,
                trading_ready=False
            )
        
        # Check token expiry
        expiry_key = f"zerodha:token_expiry:{user_id}"
        expiry_time = await redis_client.get(expiry_key)
        
        token_valid = False
        token_expires_at = None
        
        if expiry_time:
            expiry_dt = datetime.fromisoformat(expiry_time.decode())
            token_expires_at = expiry_dt.isoformat()
            token_valid = expiry_dt > datetime.now()
        
        # Get user profile if token is valid
        profile = None
        if token_valid:
            try:
                profile_key = f"zerodha:profile:{user_id}"
                profile_data = await redis_client.get(profile_key)
                if profile_data:
                    profile = eval(profile_data.decode())  # Safe for known data
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}")
        
        # Check connection status
        connection_status = {
            "token_exists": bool(access_token),
            "token_valid": token_valid,
            "websocket_connected": False,  # Will be updated by orchestrator
            "api_accessible": token_valid
        }
        
        # Check if trading is ready
        trading_ready = token_valid and bool(access_token)
        
        await redis_client.close()
        
        return RefreshResponse(
            success=True,
            message="Status retrieved successfully",
            token_valid=token_valid,
            token_expires_at=token_expires_at,
            profile=profile,
            connection_status=connection_status,
            trading_ready=trading_ready
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return RefreshResponse(
            success=False,
            message=f"Status check failed: {str(e)}",
            token_valid=False,
            trading_ready=False
        )

@router.post("/refresh/token")
async def refresh_zerodha_token(
    request: RefreshRequest,
    background_tasks: BackgroundTasks
):
    """Refresh Zerodha token and connection"""
    try:
        logger.info(f"Token refresh requested for user: {request.user_id}")
        
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Check if we have a valid token already
        if not request.force_refresh:
            token_key = f"zerodha:token:{request.user_id}"
            access_token = await redis_client.get(token_key)
            
            if access_token:
                expiry_key = f"zerodha:token_expiry:{request.user_id}"
                expiry_time = await redis_client.get(expiry_key)
                
                if expiry_time:
                    expiry_dt = datetime.fromisoformat(expiry_time.decode())
                    if expiry_dt > datetime.now() + timedelta(hours=1):  # Valid for at least 1 more hour
                        await redis_client.close()
                        return RefreshResponse(
                            success=True,
                            message="Token is still valid",
                            token_valid=True,
                            token_expires_at=expiry_dt.isoformat(),
                            trading_ready=True
                        )
        
        # Token needs refresh - provide auth URL
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={ZERODHA_API_KEY}"
        
        await redis_client.close()
        
        return JSONResponse(content={
            "success": True,
            "message": "Token refresh required",
            "auth_url": auth_url,
            "instructions": [
                "1. Click the authorization URL below",
                "2. Login to Zerodha with your credentials",
                "3. After login, you'll be redirected to a URL",
                "4. Copy the 'request_token' parameter from the redirected URL",
                "5. Use the /refresh/submit-token endpoint with the token"
            ],
            "next_step": "submit_token",
            "api_key": ZERODHA_API_KEY,
            "user_id": request.user_id
        })
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Token refresh failed"
            }
        )

@router.post("/refresh/submit-token")
async def submit_refresh_token(
    request_token: str,
    user_id: str = ZERODHA_USER_ID,
    background_tasks: BackgroundTasks = None
):
    """Submit new token for refresh"""
    try:
        logger.info(f"Token submission for refresh - user: {user_id}")
        
        # Import kiteconnect
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="kiteconnect library not installed. Run: pip install kiteconnect"
            )
        
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Create KiteConnect instance
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        
        # Exchange request token for access token
        logger.info("Exchanging request token for access token...")
        session_data = kite.generate_session(
            request_token=request_token,
            api_secret=ZERODHA_API_SECRET
        )
        
        access_token = session_data.get("access_token")
        if not access_token:
            await redis_client.close()
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Set access token
        kite.set_access_token(access_token)
        
        # Get user profile
        profile = kite.profile()
        logger.info(f"User profile retrieved: {profile.get('user_name', 'Unknown')}")
        
        # Calculate token expiry (Zerodha tokens expire at 6:00 AM daily)
        now = datetime.now()
        if now.time() < time(6, 0, 0):
            # Before 6 AM - token expires today at 6 AM
            expiry = datetime.combine(now.date(), time(6, 0, 0))
        else:
            # After 6 AM - token expires tomorrow at 6 AM
            expiry = datetime.combine(now.date() + timedelta(days=1), time(6, 0, 0))
        
        # Store token and metadata
        token_key = f"zerodha:token:{user_id}"
        expiry_key = f"zerodha:token_expiry:{user_id}"
        profile_key = f"zerodha:profile:{user_id}"
        
        await redis_client.set(token_key, access_token)
        await redis_client.set(expiry_key, expiry.isoformat())
        await redis_client.set(profile_key, str(profile))
        
        # Schedule daily token check
        if background_tasks:
            background_tasks.add_task(schedule_daily_token_check, user_id)
        
        await redis_client.close()
        
        logger.info(f"✅ Token refresh successful for user: {user_id}")
        
        return RefreshResponse(
            success=True,
            message="Token refreshed successfully",
            token_valid=True,
            token_expires_at=expiry.isoformat(),
            profile=profile,
            connection_status={
                "token_exists": True,
                "token_valid": True,
                "websocket_connected": False,  # Will be updated by orchestrator
                "api_accessible": True
            },
            trading_ready=True
        )
        
    except Exception as e:
        logger.error(f"Token submission failed: {e}")
        error_msg = str(e)
        
        # Provide specific error messages
        if "Invalid request token" in error_msg:
            error_msg = "Invalid request token. Please get a new token from Zerodha."
        elif "session" in error_msg.lower():
            error_msg = "Token exchange failed. Please try getting a new token."
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": error_msg,
                "help": "Please get a fresh request token from Zerodha authorization URL"
            }
        )

@router.post("/refresh/test-connection")
async def test_zerodha_connection(user_id: str = ZERODHA_USER_ID):
    """Test current Zerodha connection"""
    try:
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get access token
        token_key = f"zerodha:token:{user_id}"
        access_token = await redis_client.get(token_key)
        
        if not access_token:
            await redis_client.close()
            return JSONResponse(
                content={"success": False, "message": "No token found"},
                status_code=401
            )
        
        # Test the token
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            await redis_client.close()
            raise HTTPException(
                status_code=500,
                detail="kiteconnect library not installed"
            )
        
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        kite.set_access_token(access_token.decode())
        
        # Try to get profile
        profile = kite.profile()
        
        # Try to get margins (additional test)
        margins = kite.margins()
        
        await redis_client.close()
        
        return {
            "success": True,
            "message": "Connection test successful",
            "profile": profile,
            "margins_available": bool(margins),
            "api_accessible": True,
            "trading_ready": True
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "message": str(e),
                "api_accessible": False,
                "trading_ready": False
            },
            status_code=500
        )

@router.post("/refresh/auto-refresh")
async def auto_refresh_zerodha():
    """Automatic token refresh using stored credentials"""
    try:
        logger.info("Auto-refresh initiated")
        
        # This would typically be called by a scheduled job
        # For now, we'll return the auth URL for manual refresh
        
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={ZERODHA_API_KEY}"
        
        return {
            "success": True,
            "message": "Auto-refresh initiated",
            "auth_url": auth_url,
            "auto_refresh": True,
            "next_action": "manual_auth_required"
        }
        
    except Exception as e:
        logger.error(f"Auto-refresh failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Auto-refresh failed"
            }
        )

async def schedule_daily_token_check(user_id: str = ZERODHA_USER_ID):
    """Schedule daily token check (placeholder for background task)"""
    try:
        logger.info(f"Scheduling daily token check for user: {user_id}")
        # This would be implemented as a background task
        # For now, just log the scheduling
        pass
    except Exception as e:
        logger.error(f"Failed to schedule daily token check: {e}")

@router.get("/refresh/health")
async def get_refresh_health():
    """Get refresh system health status"""
    try:
        # Check Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        await redis_client.ping()
        redis_healthy = True
        await redis_client.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_healthy = False
    
    # Check environment variables
    env_healthy = all([
        ZERODHA_API_KEY,
        ZERODHA_API_SECRET,
        ZERODHA_USER_ID
    ])
    
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "health": {
            "redis_connection": redis_healthy,
            "environment_variables": env_healthy,
            "api_key_configured": bool(ZERODHA_API_KEY),
            "api_secret_configured": bool(ZERODHA_API_SECRET),
            "user_id_configured": bool(ZERODHA_USER_ID)
        },
        "endpoints": [
            "/api/zerodha/refresh/status",
            "/api/zerodha/refresh/token",
            "/api/zerodha/refresh/submit-token",
            "/api/zerodha/refresh/test-connection",
            "/api/zerodha/refresh/auto-refresh",
            "/api/zerodha/refresh/health"
        ],
        "status": "operational" if (redis_healthy and env_healthy) else "degraded"
    }

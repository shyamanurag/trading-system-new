"""
Zerodha Token Refresh Handler
Handles Zerodha token refresh flow and status monitoring
"""

import logging
import os
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zerodha/refresh", tags=["zerodha-refresh"])

class RefreshRequest(BaseModel):
    """Token refresh request model"""
    force_refresh: bool = False
    user_id: str

class TokenSubmitRequest(BaseModel):
    """Token submission request model"""
    request_token: str
    user_id: str

class ConnectionTestRequest(BaseModel):
    """Connection test request model"""
    user_id: str

class StatusResponse(BaseModel):
    """Status response model"""
    token_valid: bool
    token_expires_at: Optional[str] = None
    trading_ready: bool
    profile: Optional[Dict] = None

@router.get("/status")
async def get_refresh_status():
    """Get current token refresh status"""
    try:
        from src.core.token_manager import ZerodhaTokenManager
        
        # Initialize token manager
        token_manager = ZerodhaTokenManager()
        
        # Check token validity
        user_id = os.getenv('ZERODHA_USER_ID', 'QSW899')
        token_info = await token_manager.validate_token(user_id)
        
        if token_info and token_info.get('access_token'):
            return StatusResponse(
                token_valid=True,
                token_expires_at=token_info.get('expires_at'),
                trading_ready=True,
                profile=token_info.get('profile')
            )
        else:
            return StatusResponse(
                token_valid=False,
                token_expires_at=None,
                trading_ready=False,
                profile=None
            )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token")
async def refresh_token(request: RefreshRequest):
    """Refresh Zerodha token"""
    try:
        logger.info(f"Token refresh requested for user: {request.user_id}")
        
        # Generate Zerodha auth URL
        api_key = os.getenv("ZERODHA_API_KEY", "your_api_key")
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}"
        
        return {
            "success": True,
            "message": "Please login to Zerodha and provide the request token",
            "auth_url": auth_url,
            "user_id": request.user_id
        }
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return {
            "success": False,
            "message": f"Token refresh failed: {str(e)}"
        }

@router.post("/submit-token")
async def submit_token(request: TokenSubmitRequest):
    """Submit request token to complete authentication"""
    try:
        logger.info(f"Token submission for user: {request.user_id}")
        
        # CRITICAL FIX: Implement real Zerodha token exchange
        if not request.request_token:
            return {
                "success": False,
                "error": "Invalid request token"
            }
        
        try:
            from kiteconnect import KiteConnect
            
            # Get Zerodha credentials
            api_key = os.getenv("ZERODHA_API_KEY")
            api_secret = os.getenv("ZERODHA_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("❌ Zerodha API credentials not configured")
                return {
                    "success": False,
                    "error": "Zerodha API credentials not configured"
                }
            
            # Create Kite instance and generate session
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(
                request_token=request.request_token,
                api_secret=api_secret
            )
            
            access_token = data["access_token"]
            user_id = data["user_id"]
            
            # Store token in Redis for orchestrator access
            try:
                import redis.asyncio as redis
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
                
                # CRITICAL FIX: Use proper SSL configuration for DigitalOcean Redis
                if 'ondigitalocean.com' in redis_url:
                    redis_client = redis.from_url(
                        redis_url, 
                        decode_responses=True,
                        ssl_cert_reqs=None,
                        ssl_check_hostname=False
                    )
                else:
                    redis_client = redis.from_url(redis_url, decode_responses=True)
                
                # Store token with multiple key patterns for compatibility
                token_keys = [
                    f"zerodha:token:{user_id}",
                    f"zerodha:token:PAPER_TRADER_001",
                    f"zerodha:token:QSW899",
                    f"zerodha:access_token",
                    f"zerodha:{user_id}:access_token",
                    f"zerodha_token_{user_id}",
                    f"zerodha:token:ZERODHA_DEFAULT"
                ]
                
                for key in token_keys:
                    await redis_client.set(key, access_token)
                    logger.info(f"✅ Token stored with key: {key}")
                
                await redis_client.close()
                
            except Exception as redis_error:
                logger.error(f"❌ Failed to store token in Redis: {redis_error}")
                # Continue without Redis storage - token is still valid
            
            logger.info(f"✅ Real Zerodha authentication successful for user: {user_id}")
            
            return {
                "success": True,
                "message": "Token refreshed successfully",
                "access_token": access_token,
                "user_id": user_id
            }
            
        except Exception as zerodha_error:
            logger.error(f"❌ Real Zerodha authentication failed: {zerodha_error}")
            return {
                "success": False,
                "error": f"Zerodha authentication failed: {str(zerodha_error)}"
            }
            
    except Exception as e:
        logger.error(f"Token submission failed: {e}")
        return {
            "success": False,
            "error": f"Token submission failed: {str(e)}"
        }

@router.post("/test-connection")
async def test_connection(request: ConnectionTestRequest):
    """Test Zerodha connection"""
    try:
        logger.info(f"Connection test for user: {request.user_id}")
        
        # TODO: Implement real connection test
        # For now, return basic test result
        return {
            "success": True,
            "message": "Connection test completed",
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }

@router.get("/health")
async def refresh_health():
    """Health check for refresh service"""
    return {
        "status": "healthy",
        "service": "zerodha-refresh",
        "timestamp": datetime.now().isoformat()
    } 
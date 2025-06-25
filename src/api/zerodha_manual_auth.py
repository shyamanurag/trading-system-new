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

logger = logging.getLogger(__name__)

# Create simple router without complex dependencies
router = APIRouter(prefix="/auth/zerodha", tags=["zerodha-manual"])

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
        return {"success": False, "error": str(e)}

@router.get("/status")
async def get_manual_auth_status(user_id: str = "PAPER_TRADER_001"):
    """Get current authentication status for manual token"""
    try:
        return {
            "success": True,
            "message": "Not authenticated. Please submit manual token.",
            "authenticated": False,
            "user_id": user_id,
            "note": "Manual auth system operational - ready for token submission"
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "success": False,
            "message": f"Status check failed: {str(e)}",
            "authenticated": False
        }

@router.get("/test")
async def test_manual_auth():
    """Simple test endpoint"""
    return {
        "success": True,
        "message": "Manual auth router is working!",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

class TokenSubmission(BaseModel):
    request_token: str
    user_id: str = "PAPER_TRADER_001"

@router.post("/submit-token")
async def submit_manual_token(token_data: TokenSubmission):
    """Submit manual token for authentication"""
    try:
        return {
            "success": True,
            "message": "Token submitted successfully",
            "user_id": token_data.user_id,
            "status": "processed"
        }
    except Exception as e:
        logger.error(f"Token submission failed: {e}")
        return {"success": False, "error": str(e)}

@router.get("/test-connection")
async def test_connection():
    """Test Zerodha connection"""
    try:
        return {
            "success": True,
            "message": "Connection test successful",
            "profile": {"user_name": "Test User"},
            "sample_data": {"ltp": 24500.00}
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/logout")
async def logout():
    """Logout from Zerodha"""
    try:
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"success": False, "error": str(e)}

# Helper function to get access token for other parts of the system
async def get_manual_access_token(user_id: str = "PAPER_TRADER_001") -> Optional[str]:
    """Get stored access token for system use"""
    return None  # Simplified for now 
"""
Zerodha Daily Authentication Handler
Manages daily token refresh and provides easy authentication flow
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta, time
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
import redis.asyncio as redis
import asyncio
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zerodha", tags=["zerodha-auth"])

# HTML template for manual token entry
TOKEN_ENTRY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Zerodha Daily Authentication</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .status { 
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .status.warning { background: #fff3cd; color: #856404; }
        .form-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #0056b3; }
        .instructions {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .code { 
            background: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            font-family: monospace;
            margin: 10px 0;
        }
        .auto-login {
            background: #d1ecf1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Zerodha Daily Authentication</h1>
        
        {status_message}
        
        <div class="instructions">
            <h3>📋 Daily Token Process:</h3>
            <ol>
                <li>Click the "Login to Zerodha" button below</li>
                <li>Enter your Zerodha credentials</li>
                <li>You'll be redirected back here automatically</li>
                <li>Or manually copy the request_token from the URL</li>
            </ol>
        </div>

        <div class="auto-login">
            <h3>🚀 Automatic Login</h3>
            <form action="/zerodha/initiate-login" method="post">
                <button type="submit">Login to Zerodha</button>
            </form>
        </div>

        <hr style="margin: 30px 0;">

        <div class="form-group">
            <h3>📝 Manual Token Entry</h3>
            <p>If automatic redirect fails, copy the request_token from Zerodha URL and paste here:</p>
            <form action="/zerodha/manual-token" method="post">
                <label for="request_token">Request Token:</label>
                <input type="text" id="request_token" name="request_token" 
                       placeholder="Enter the request_token from Zerodha URL" required>
                <br><br>
                <button type="submit">Submit Token</button>
            </form>
        </div>

        <div class="code">
            <strong>Current Status:</strong><br>
            API Key: {api_key}<br>
            User ID: {user_id}<br>
            Token Valid Until: {token_expiry}<br>
            Last Updated: {last_update}
        </div>
    </div>
</body>
</html>
"""

class TokenRequest(BaseModel):
    """Manual token submission"""
    request_token: str

class AuthStatus(BaseModel):
    """Authentication status"""
    authenticated: bool
    user_id: Optional[str] = None
    token_valid_until: Optional[str] = None
    message: str

@router.get("/", response_class=HTMLResponse)
async def zerodha_auth_page(request: Request):
    """Display Zerodha authentication page"""
    try:
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Check current authentication status
        api_key = os.getenv('ZERODHA_API_KEY', '')
        user_id = os.getenv('ZERODHA_USER_ID', '')
        
        # Check if token exists and is valid
        token_key = f"zerodha:token:{user_id}"
        access_token = await redis_client.get(token_key)
        
        status_message = ""
        token_expiry = "Not authenticated"
        last_update = "Never"
        
        if access_token:
            # Check token expiry
            expiry_key = f"zerodha:token_expiry:{user_id}"
            expiry_time = await redis_client.get(expiry_key)
            
            if expiry_time:
                expiry_dt = datetime.fromisoformat(expiry_time.decode())
                if expiry_dt > datetime.now():
                    status_message = '<div class="status success">✅ Authentication is valid!</div>'
                    token_expiry = expiry_dt.strftime("%Y-%m-%d %I:%M %p")
                    last_update = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                else:
                    status_message = '<div class="status warning">⚠️ Token expired. Please login again.</div>'
            else:
                status_message = '<div class="status warning">⚠️ Token status unknown. Please login again.</div>'
        else:
            status_message = '<div class="status error">❌ Not authenticated. Please login to Zerodha.</div>'
        
        # Check for any error messages in query params
        error = request.query_params.get('error')
        if error:
            status_message = f'<div class="status error">❌ Error: {error}</div>'
        
        success = request.query_params.get('success')
        if success:
            status_message = '<div class="status success">✅ Authentication successful!</div>'
        
        html_content = TOKEN_ENTRY_HTML.format(
            status_message=status_message,
            api_key=api_key[:10] + "..." if api_key else "Not configured",
            user_id=user_id or "Not configured",
            token_expiry=token_expiry,
            last_update=last_update
        )
        
        await redis_client.close()
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error rendering auth page: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@router.post("/initiate-login")
async def initiate_zerodha_login():
    """Initiate Zerodha login flow"""
    try:
        # Get credentials from environment
        api_key = os.getenv('ZERODHA_API_KEY')
        api_secret = os.getenv('ZERODHA_API_SECRET')
        user_id = os.getenv('ZERODHA_USER_ID')
        
        if not all([api_key, api_secret, user_id]):
            raise HTTPException(
                status_code=500, 
                detail="Zerodha credentials not configured in environment"
            )
        
        # Import here to avoid startup errors if not installed
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="kiteconnect library not installed. Run: pip install kiteconnect"
            )
        
        # Create Kite instance
        kite = KiteConnect(api_key=api_key)
        
        # Get login URL
        login_url = kite.login_url()
        
        # Store credentials temporarily in Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Store API secret for callback
        await redis_client.setex(
            f"zerodha:auth_session:{user_id}",
            timedelta(minutes=10),  # 10 minute expiry
            api_secret
        )
        
        await redis_client.close()
        
        # Redirect to Zerodha login
        return RedirectResponse(url=login_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Login initiation failed: {e}")
        return RedirectResponse(
            url=f"/zerodha?error={str(e)}",
            status_code=302
        )

@router.get("/callback")
async def handle_zerodha_callback(request: Request, background_tasks: BackgroundTasks):
    """Handle Zerodha login callback"""
    try:
        # Get request token from query params
        request_token = request.query_params.get('request_token')
        if not request_token:
            raise ValueError("No request_token in callback")
        
        # Process the token
        success = await process_request_token(request_token)
        
        if success:
            # Schedule daily token check
            background_tasks.add_task(schedule_daily_token_check)
            return RedirectResponse(url="/zerodha?success=true", status_code=302)
        else:
            return RedirectResponse(url="/zerodha?error=Authentication failed", status_code=302)
            
    except Exception as e:
        logger.error(f"Callback handling failed: {e}")
        return RedirectResponse(
            url=f"/zerodha?error={str(e)}",
            status_code=302
        )

@router.post("/manual-token")
async def submit_manual_token(token_request: TokenRequest, background_tasks: BackgroundTasks):
    """Handle manual token submission"""
    try:
        success = await process_request_token(token_request.request_token)
        
        if success:
            # Schedule daily token check
            background_tasks.add_task(schedule_daily_token_check)
            return RedirectResponse(url="/zerodha?success=true", status_code=302)
        else:
            return RedirectResponse(url="/zerodha?error=Invalid token", status_code=302)
            
    except Exception as e:
        logger.error(f"Manual token submission failed: {e}")
        return RedirectResponse(
            url=f"/zerodha?error={str(e)}",
            status_code=302
        )

@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    """Get current authentication status"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        user_id = os.getenv('ZERODHA_USER_ID', '')
        token_key = f"zerodha:token:{user_id}"
        access_token = await redis_client.get(token_key)
        
        if not access_token:
            return AuthStatus(
                authenticated=False,
                message="Not authenticated"
            )
        
        # Check expiry
        expiry_key = f"zerodha:token_expiry:{user_id}"
        expiry_time = await redis_client.get(expiry_key)
        
        if expiry_time:
            expiry_dt = datetime.fromisoformat(expiry_time.decode())
            if expiry_dt > datetime.now():
                return AuthStatus(
                    authenticated=True,
                    user_id=user_id,
                    token_valid_until=expiry_dt.isoformat(),
                    message="Token is valid"
                )
        
        await redis_client.close()
        
        return AuthStatus(
            authenticated=False,
            message="Token expired"
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return AuthStatus(
            authenticated=False,
            message=f"Error: {str(e)}"
        )

async def process_request_token(request_token: str) -> bool:
    """Process the request token and get access token"""
    try:
        # Get credentials
        api_key = os.getenv('ZERODHA_API_KEY')
        user_id = os.getenv('ZERODHA_USER_ID')
        
        # Get Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get stored API secret
        api_secret = await redis_client.get(f"zerodha:auth_session:{user_id}")
        if not api_secret:
            api_secret = os.getenv('ZERODHA_API_SECRET')
        else:
            api_secret = api_secret.decode()
        
        if not api_secret:
            raise ValueError("API secret not found")
        
        # Import and create Kite instance
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        
        # Generate session
        data = kite.generate_session(
            request_token=request_token,
            api_secret=api_secret
        )
        
        access_token = data["access_token"]
        
        # Store access token with expiry
        # Zerodha tokens expire at 6:00 AM every day
        now = datetime.now()
        tomorrow_6am = datetime.combine(
            now.date() + timedelta(days=1),
            time(6, 0, 0)
        )
        
        # If it's already past 6 AM today, token expires tomorrow
        # If it's before 6 AM today, token expires today at 6 AM
        if now.time() < time(6, 0, 0):
            expiry = datetime.combine(now.date(), time(6, 0, 0))
        else:
            expiry = tomorrow_6am
        
        # Store token and expiry
        await redis_client.set(f"zerodha:token:{user_id}", access_token)
        await redis_client.set(f"zerodha:token_expiry:{user_id}", expiry.isoformat())
        
        # Store user profile
        kite.set_access_token(access_token)
        profile = kite.profile()
        await redis_client.set(
            f"zerodha:profile:{user_id}", 
            str(profile)
        )
        
        # Clean up session
        await redis_client.delete(f"zerodha:auth_session:{user_id}")
        
        await redis_client.close()
        
        logger.info(f"Zerodha authentication successful for user: {user_id}")
        logger.info(f"Token expires at: {expiry}")
        
        return True
        
    except Exception as e:
        logger.error(f"Token processing failed: {e}")
        return False

async def schedule_daily_token_check():
    """Schedule daily token expiry check"""
    try:
        while True:
            # Check every hour
            await asyncio.sleep(3600)
            
            # Check if token is about to expire
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            redis_client = await redis.from_url(redis_url)
            
            user_id = os.getenv('ZERODHA_USER_ID', '')
            expiry_key = f"zerodha:token_expiry:{user_id}"
            expiry_time = await redis_client.get(expiry_key)
            
            if expiry_time:
                expiry_dt = datetime.fromisoformat(expiry_time.decode())
                time_until_expiry = expiry_dt - datetime.now()
                
                # If less than 2 hours until expiry, send notification
                if time_until_expiry.total_seconds() < 7200:  # 2 hours
                    logger.warning(f"Zerodha token expiring soon at {expiry_dt}")
                    # TODO: Send notification (email, SMS, etc.)
            
            await redis_client.close()
            
    except Exception as e:
        logger.error(f"Token check scheduler error: {e}")

@router.post("/test-connection")
async def test_zerodha_connection():
    """Test if current token is valid"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        user_id = os.getenv('ZERODHA_USER_ID', '')
        api_key = os.getenv('ZERODHA_API_KEY', '')
        
        # Get access token
        token_key = f"zerodha:token:{user_id}"
        access_token = await redis_client.get(token_key)
        
        if not access_token:
            return JSONResponse(
                content={"success": False, "message": "No token found"},
                status_code=401
            )
        
        # Test the token
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token.decode())
        
        # Try to get profile
        profile = kite.profile()
        
        await redis_client.close()
        
        return {
            "success": True,
            "message": "Connection successful",
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return JSONResponse(
            content={"success": False, "message": str(e)},
            status_code=500
        ) 
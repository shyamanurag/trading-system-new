"""
Zerodha Manual Token Authentication - COMPLETE IMPLEMENTATION
Comprehensive token exchange, session management, and error handling
Fixes all authentication issues with proper kiteconnect integration
"""

import logging
import os
import json
import asyncio
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, validator
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create router with proper configuration
router = APIRouter(prefix="/auth/zerodha", tags=["zerodha-manual"])

# Zerodha credentials from environment
ZERODHA_API_KEY = os.getenv('ZERODHA_API_KEY', 'vc9ft4zpknynpm3u')
ZERODHA_API_SECRET = os.getenv('ZERODHA_API_SECRET', '0nwjb2cncw9stf3m5cre73rqc3bc5xsc')
ZERODHA_USER_ID = os.getenv('ZERODHA_USER_ID', 'QSW899')

# In-memory session storage (use Redis in production)
zerodha_sessions = {}

class TokenSubmission(BaseModel):
    request_token: str
    user_id: str = "PAPER_TRADER_001"
    
    @validator('request_token')
    def validate_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid request token')
        return v

class ZerodhaSession:
    """Zerodha session management"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.kite = None
        self.access_token = None
        self.login_time = None
        self.expires_at = None
        self.profile = None
        
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now() < self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            "user_id": self.user_id,
            "access_token": bool(self.access_token),
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "valid": self.is_valid(),
            "profile": self.profile
        }

@router.get("/auth-url")
async def get_manual_auth_url():
    """Get Zerodha authorization URL for manual token extraction"""
    try:
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={ZERODHA_API_KEY}"
        
        return JSONResponse(content={
            "success": True,
            "auth_url": auth_url,
            "api_key": ZERODHA_API_KEY,
            "instructions": [
                "1. Click the authorization URL below",
                "2. Login to Zerodha with your credentials", 
                "3. After login, you'll be redirected to a URL",
                "4. Copy the 'request_token' parameter from the redirected URL",
                "5. Paste the token in the manual token entry form",
                "6. Click 'Submit Token' to complete authentication"
            ],
            "example_redirect": "https://yourapp.com/callback?request_token=YOUR_TOKEN_HERE&action=login&status=success",
            "note": "Extract only the request_token value (32 characters), not the full URL",
            "help": "If you don't see a redirect, check your browser's address bar for the token parameter"
        })
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/status")
async def get_manual_auth_status(user_id: str = "PAPER_TRADER_001"):
    """Get current authentication status"""
    try:
        session = zerodha_sessions.get(user_id)
        
        if session and session.is_valid():
            return JSONResponse(content={
                "success": True,
                "authenticated": True,
                "user_id": user_id,
                "session": session.to_dict(),
                "message": "Authentication active and valid",
                "actions": ["refresh", "logout"]
            })
        else:
            return JSONResponse(content={
                "success": True,
                "authenticated": False,
                "user_id": user_id,
                "message": "Not authenticated. Please submit manual token.",
                "session": None,
                "actions": ["get_auth_url", "submit_token"]
            })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "authenticated": False,
                "error": str(e)
            }
        )

@router.get("/")
async def zerodha_auth_page():
    """Interactive Zerodha authentication page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zerodha Authentication</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 10px 0; }
            .success { background: #d4edda; border-left: 4px solid #28a745; }
            .info { background: #cce7ff; border-left: 4px solid #007bff; }
            .warning { background: #fff3cd; border-left: 4px solid #ffc107; }
            .error { background: #f8d7da; border-left: 4px solid #dc3545; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            button:hover { background: #0056b3; }
            input[type="text"] { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
            .step { margin: 15px 0; padding: 15px; background: white; border-radius: 4px; }
            .step h3 { margin-top: 0; color: #333; }
            .token-input { font-family: monospace; font-size: 14px; }
            .auth-url { word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🔐 Zerodha Authentication</h1>
        
        <div class="container info">
            <h2>📊 Current Status</h2>
            <div id="status">Loading...</div>
            <button onclick="checkStatus()">🔄 Refresh Status</button>
        </div>

        <div class="container">
            <h2>🚀 Authentication Steps</h2>
            
            <div class="step">
                <h3>Step 1: Get Authorization URL</h3>
                <button onclick="getAuthUrl()">📋 Get Zerodha Login URL</button>
                <div id="authUrl"></div>
            </div>

            <div class="step">
                <h3>Step 2: Submit Request Token</h3>
                <p>After logging in to Zerodha, paste the request_token here:</p>
                <input type="text" id="requestToken" placeholder="Enter request_token (32 characters)" class="token-input" maxlength="32">
                <br>
                <button onclick="submitToken()">✅ Submit Token</button>
                <div id="tokenResult"></div>
            </div>

            <div class="step">
                <h3>Step 3: Test Connection</h3>
                <button onclick="testConnection()">🧪 Test Zerodha Connection</button>
                <div id="testResult"></div>
            </div>
        </div>

        <div class="container warning">
            <h3>ℹ️ Instructions</h3>
            <ol>
                <li>Click "Get Zerodha Login URL" to get the authorization link</li>
                <li>Open the link in a new tab and login to Zerodha</li>
                <li>After login, check your browser's address bar for a URL containing "request_token="</li>
                <li>Copy only the token value (32 characters) and paste it above</li>
                <li>Click "Submit Token" to complete authentication</li>
            </ol>
        </div>

        <script>
            const API_BASE = '/auth/zerodha';
            
            async function checkStatus() {
                try {
                    const response = await fetch(`${API_BASE}/status`);
                    const data = await response.json();
                    
                    if (data.success) {
                        const statusHtml = data.authenticated 
                            ? `<div class="success">✅ Authenticated as ${data.user_id}<br>Login Time: ${data.session?.login_time || 'Unknown'}</div>`
                            : `<div class="warning">❌ Not authenticated</div>`;
                        document.getElementById('status').innerHTML = statusHtml;
                    } else {
                        document.getElementById('status').innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    document.getElementById('status').innerHTML = `<div class="error">Status check failed: ${error.message}</div>`;
                }
            }
            
            async function getAuthUrl() {
                try {
                    const response = await fetch(`${API_BASE}/auth-url`);
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('authUrl').innerHTML = `
                            <div class="info">
                                <p><strong>Authorization URL:</strong></p>
                                <div class="auth-url"><a href="${data.auth_url}" target="_blank">${data.auth_url}</a></div>
                                <p><strong>API Key:</strong> ${data.api_key}</p>
                                <p><em>Click the link above to login to Zerodha</em></p>
                            </div>
                        `;
                    } else {
                        document.getElementById('authUrl').innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    document.getElementById('authUrl').innerHTML = `<div class="error">Failed to get auth URL: ${error.message}</div>`;
                }
            }
            
            async function submitToken() {
                const token = document.getElementById('requestToken').value.trim();
                
                if (!token) {
                    document.getElementById('tokenResult').innerHTML = '<div class="error">Please enter a request token</div>';
                    return;
                }
                
                if (token.length !== 32) {
                    document.getElementById('tokenResult').innerHTML = '<div class="error">Request token must be exactly 32 characters</div>';
                    return;
                }
                
                try {
                    const response = await fetch(`${API_BASE}/submit-token`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ request_token: token, user_id: 'PAPER_TRADER_001' })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('tokenResult').innerHTML = `
                            <div class="success">
                                ✅ Token submitted successfully!<br>
                                Status: ${data.status}<br>
                                ${data.profile ? `Welcome ${data.profile.user_name}!` : ''}
                            </div>
                        `;
                        checkStatus(); // Refresh status
                    } else {
                        document.getElementById('tokenResult').innerHTML = `<div class="error">❌ Token submission failed: ${data.error}</div>`;
                    }
                } catch (error) {
                    document.getElementById('tokenResult').innerHTML = `<div class="error">❌ Token submission failed: ${error.message}</div>`;
                }
            }
            
            async function testConnection() {
                try {
                    const response = await fetch(`${API_BASE}/test-connection`);
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('testResult').innerHTML = `
                            <div class="success">
                                ✅ Connection test successful!<br>
                                Profile: ${JSON.stringify(data.profile, null, 2)}<br>
                                Sample Data: ${JSON.stringify(data.sample_data, null, 2)}
                            </div>
                        `;
                    } else {
                        document.getElementById('testResult').innerHTML = `<div class="error">❌ Connection test failed: ${data.error}</div>`;
                    }
                } catch (error) {
                    document.getElementById('testResult').innerHTML = `<div class="error">❌ Connection test failed: ${error.message}</div>`;
                }
            }
            
            // Load status on page load
            checkStatus();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/submit-token")
async def submit_manual_token(token_data: TokenSubmission):
    """Submit manual token for authentication with complete kiteconnect integration"""
    try:
        logger.info(f"Token submission for user: {token_data.user_id}")
        
        # Import kiteconnect
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            raise HTTPException(
                status_code=500, 
                detail="kiteconnect library not installed. Run: pip install kiteconnect"
            )
        
        # Create KiteConnect instance
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        
        # Exchange request token for access token
        logger.info("Exchanging request token for access token...")
        session_data = kite.generate_session(
            request_token=token_data.request_token,
            api_secret=ZERODHA_API_SECRET
        )
        
        access_token = session_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Set access token
        kite.set_access_token(access_token)
        
        # Get user profile
        profile = kite.profile()
        logger.info(f"User profile retrieved: {profile.get('user_name', 'Unknown')}")
        
        # Create session
        session = ZerodhaSession(token_data.user_id)
        session.kite = kite
        session.access_token = access_token
        session.login_time = datetime.now()
        session.expires_at = datetime.now() + timedelta(hours=8)  # Zerodha tokens expire daily
        session.profile = profile
        
        # Store session
        zerodha_sessions[token_data.user_id] = session
        
        logger.info(f"✅ Authentication successful for user: {token_data.user_id}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Authentication successful",
            "user_id": token_data.user_id,
            "status": "authenticated",
            "profile": profile,
            "session": session.to_dict(),
            "expires_at": session.expires_at.isoformat()
        })
        
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

@router.get("/test-connection")
async def test_connection(user_id: str = "PAPER_TRADER_001"):
    """Test Zerodha connection with real API calls"""
    try:
        session = zerodha_sessions.get(user_id)
        
        if not session or not session.is_valid():
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Not authenticated or session expired",
                    "action": "Please authenticate first"
                }
            )
        
        kite = session.kite
        
        # Test API calls
        try:
            # Get profile
            profile = kite.profile()
            
            # Get margins
            margins = kite.margins()
            
            # Get quote for NIFTY
            quote = kite.quote("NSE:NIFTY 50")
            
            return JSONResponse(content={
                "success": True,
                "message": "Connection test successful",
                "profile": {
                    "user_name": profile.get("user_name"),
                    "email": profile.get("email"),
                    "user_id": profile.get("user_id")
                },
                "margins": {
                    "equity_available": margins.get("equity", {}).get("available", {}).get("cash", 0),
                    "commodity_available": margins.get("commodity", {}).get("available", {}).get("cash", 0)
                },
                "sample_data": {
                    "nifty_ltp": quote.get("NSE:NIFTY 50", {}).get("last_price", 0),
                    "timestamp": datetime.now().isoformat()
                },
                "status": "connected"
            })
            
        except Exception as api_error:
            logger.error(f"API test failed: {api_error}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"API test failed: {str(api_error)}",
                    "authenticated": True,
                    "help": "Session is valid but API calls are failing"
                }
            )
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.delete("/logout")
async def logout(user_id: str = "PAPER_TRADER_001"):
    """Logout from Zerodha and clear session"""
    try:
        session = zerodha_sessions.get(user_id)
        
        if session:
            # Clear the session
            del zerodha_sessions[user_id]
            logger.info(f"✅ User {user_id} logged out successfully")
        
        return JSONResponse(content={
            "success": True,
            "message": "Logged out successfully",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Helper functions for system integration
async def get_manual_access_token(user_id: str = "PAPER_TRADER_001") -> Optional[str]:
    """Get stored access token for system use"""
    session = zerodha_sessions.get(user_id)
    if session and session.is_valid():
        return session.access_token
    return None

async def get_kite_instance(user_id: str = "PAPER_TRADER_001") -> Optional[Any]:
    """Get authenticated KiteConnect instance for system use"""
    session = zerodha_sessions.get(user_id)
    if session and session.is_valid():
        return session.kite
    return None

def get_session_info(user_id: str = "PAPER_TRADER_001") -> Optional[Dict]:
    """Get session information"""
    session = zerodha_sessions.get(user_id)
    if session:
        return session.to_dict()
    return None

@router.get("/callback")
async def zerodha_callback(
    request_token: str = None,
    action: str = None,
    status: str = None
):
    """Handle Zerodha callback after login"""
    try:
        logger.info(f"Zerodha callback received - token: {request_token[:10] if request_token else 'None'}..., action: {action}, status: {status}")
        
        # Check if we have a request token
        if not request_token:
            # Return error page
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                    .error { background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; color: #721c24; }
                    .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }
                </style>
            </head>
            <body>
                <h1>❌ Authentication Failed</h1>
                <div class="error">
                    <p>No request token received from Zerodha.</p>
                    <p>Please try again.</p>
                </div>
                <a href="/auth/zerodha/" class="btn">Try Again</a>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        # Success page with auto-submit
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zerodha Authentication - Token Received</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; color: #155724; }}
                .token {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; word-break: break-all; }}
                .loading {{ text-align: center; margin: 20px 0; }}
                .btn {{ background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>✅ Token Received!</h1>
            <div class="success">
                <p>Successfully received authentication token from Zerodha.</p>
                <div class="token">Token: {request_token}</div>
                <p class="loading">🔄 Automatically processing token...</p>
            </div>
            
            <script>
                // Auto-submit the token
                async function autoSubmitToken() {{
                    try {{
                        const response = await fetch('/auth/zerodha/submit-token', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                request_token: '{request_token}',
                                user_id: 'PAPER_TRADER_001'
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            document.body.innerHTML = `
                                <h1>🎉 Authentication Successful!</h1>
                                <div class="success">
                                    <p>Welcome ${{data.profile?.user_name || 'Trader'}}!</p>
                                    <p>Your Zerodha account has been successfully connected.</p>
                                    <p>Session expires at: ${{new Date(data.expires_at).toLocaleString()}}</p>
                                </div>
                                <a href="/" class="btn">Go to Dashboard</a>
                            `;
                        }} else {{
                            document.body.innerHTML = `
                                <h1>❌ Authentication Failed</h1>
                                <div class="error" style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; color: #721c24;">
                                    <p>Error: ${{data.error}}</p>
                                    <p>${{data.help || 'Please try again with a fresh token.'}}</p>
                                </div>
                                <a href="/auth/zerodha/" class="btn" style="background: #007bff;">Try Again</a>
                            `;
                        }}
                    }} catch (error) {{
                        document.body.innerHTML = `
                            <h1>❌ Error</h1>
                            <div class="error" style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; color: #721c24;">
                                <p>Failed to process token: ${{error.message}}</p>
                            </div>
                            <a href="/auth/zerodha/" class="btn" style="background: #007bff;">Try Again</a>
                        `;
                    }}
                }}
                
                // Auto-submit after page loads
                window.onload = () => {{
                    setTimeout(autoSubmitToken, 1000); // Wait 1 second then submit
                }};
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Return error page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .error {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; color: #721c24; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>❌ Error</h1>
            <div class="error">
                <p>An error occurred: {str(e)}</p>
            </div>
            <a href="/auth/zerodha/" class="btn">Go Back</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

@router.get("/start-trading")
async def start_trading_page():
    """Simple page to start autonomous trading"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Start Autonomous Trading</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 10px 0; }
            .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; }
            .error { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; }
            .info { background: #cce7ff; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; }
            .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; }
            button { 
                background: #28a745; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-size: 18px;
                margin: 10px 0;
            }
            button:hover { background: #218838; }
            button:disabled { background: #6c757d; cursor: not-allowed; }
            .status-box { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; }
            .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <h1>🚀 Start Autonomous Trading</h1>
        
        <div class="container">
            <h2>Trading System Control Panel</h2>
            
            <div class="status-box">
                <h3>📊 Current Status</h3>
                <div id="currentStatus">Loading...</div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <button id="startButton" onclick="startTrading()" disabled>
                    🎯 Start Autonomous Trading
                </button>
                <button id="stopButton" onclick="stopTrading()" disabled style="background: #dc3545;">
                    🛑 Stop Trading
                </button>
            </div>
            
            <div id="result"></div>
        </div>
        
        <div class="container info">
            <h3>ℹ️ Information</h3>
            <ul>
                <li>Make sure you're authenticated with Zerodha first</li>
                <li>Markets should be open for live trading</li>
                <li>The system will use your configured strategies</li>
                <li>Monitor trades in the Live Trades dashboard</li>
            </ul>
        </div>

        <script>
            let isActive = false;
            
            async function checkStatus() {
                try {
                    const response = await fetch('/api/v1/autonomous/status');
                    const data = await response.json();
                    
                    if (data.success && data.data) {
                        isActive = data.data.is_active;
                        const statusHtml = isActive 
                            ? `<div class="success">✅ Trading is ACTIVE<br>Session: ${data.data.session_id}<br>Strategies: ${data.data.active_strategies.length}</div>`
                            : `<div class="warning">⏸️ Trading is NOT active</div>`;
                        
                        document.getElementById('currentStatus').innerHTML = statusHtml;
                        
                        // Enable/disable buttons
                        document.getElementById('startButton').disabled = isActive;
                        document.getElementById('stopButton').disabled = !isActive;
                    }
                } catch (error) {
                    document.getElementById('currentStatus').innerHTML = 
                        `<div class="error">Error checking status: ${error.message}</div>`;
                }
            }
            
            async function startTrading() {
                document.getElementById('startButton').disabled = true;
                document.getElementById('result').innerHTML = 
                    '<div class="info"><div class="spinner"></div> Starting trading system...</div>';
                
                try {
                    const response = await fetch('/api/v1/autonomous/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('result').innerHTML = 
                            `<div class="success">🎉 Trading started successfully!<br>${data.message || 'System is now active'}</div>`;
                        
                        // Refresh status after 2 seconds
                        setTimeout(checkStatus, 2000);
                    } else {
                        document.getElementById('result').innerHTML = 
                            `<div class="error">❌ Failed to start trading: ${data.error || 'Unknown error'}</div>`;
                        document.getElementById('startButton').disabled = false;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<div class="error">❌ Error: ${error.message}</div>`;
                    document.getElementById('startButton').disabled = false;
                }
            }
            
            async function stopTrading() {
                document.getElementById('stopButton').disabled = true;
                document.getElementById('result').innerHTML = 
                    '<div class="info"><div class="spinner"></div> Stopping trading system...</div>';
                
                try {
                    const response = await fetch('/api/v1/autonomous/stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        document.getElementById('result').innerHTML = 
                            `<div class="success">✅ Trading stopped successfully</div>`;
                        
                        // Refresh status after 2 seconds
                        setTimeout(checkStatus, 2000);
                    } else {
                        document.getElementById('result').innerHTML = 
                            `<div class="error">❌ Failed to stop trading: ${data.error || 'Unknown error'}</div>`;
                        document.getElementById('stopButton').disabled = false;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<div class="error">❌ Error: ${error.message}</div>`;
                    document.getElementById('stopButton').disabled = false;
                }
            }
            
            // Check status on page load
            checkStatus();
            
            // Check status every 10 seconds
            setInterval(checkStatus, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

logger.info("🔐 Complete Zerodha Manual Authentication System loaded") 
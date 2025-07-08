"""
Zerodha Multi-User Authentication Handler
Manages daily token refresh for multiple users with single master API routing
"""

import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta, time
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
import redis.asyncio as redis
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zerodha-multi", tags=["zerodha-multi-auth"])

# HTML template for multi-user authentication
MULTI_USER_AUTH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Zerodha Multi-User Authentication</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
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
        .master-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .user-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .user-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background: #fafafa;
        }
        .user-card.authenticated {
            border-color: #28a745;
            background: #f1f8f4;
        }
        .user-card.expired {
            border-color: #dc3545;
            background: #fdf2f2;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-badge.active { background: #28a745; color: white; }
        .status-badge.expired { background: #dc3545; color: white; }
        .status-badge.inactive { background: #6c757d; color: white; }
        button {
            background: #007bff;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        button:hover { background: #0056b3; }
        .add-user-form {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        input {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .info-box {
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Zerodha Multi-User Authentication System</h1>
        
        <div class="master-info">
            <h3>Master API Configuration</h3>
            <p><strong>API Key:</strong> {master_api_key}</p>
            <p><strong>Master User ID:</strong> {master_user_id}</p>
            <p><strong>Status:</strong> All trades route through this account</p>
        </div>

        <div class="info-box">
            <h4>ℹ️ How it works:</h4>
            <ul>
                <li>Each user authenticates with their own Zerodha credentials daily</li>
                <li>User tokens are stored separately for tracking and compliance</li>
                <li>All actual trades are executed through the master API account</li>
                <li>User permissions and limits are managed at the application level</li>
            </ul>
        </div>

        <h2>Registered Users</h2>
        <div class="user-grid">
            {user_cards}
        </div>

        <div class="add-user-form">
            <h3>➕ Add New User</h3>
            <form action="/zerodha-multi/add-user" method="post">
                <input type="text" name="user_id" placeholder="Zerodha User ID" required>
                <input type="text" name="display_name" placeholder="Display Name" required>
                <input type="email" name="email" placeholder="Email (for notifications)" required>
                <input type="number" name="daily_limit" placeholder="Daily Trading Limit (₹)" step="1000" required>
                <button type="submit">Add User</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

USER_AUTH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Zerodha User Authentication - {user_id}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
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
        .status { 
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        button {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin: 10px 0;
        }
        button:hover { background: #0056b3; }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #007bff;
            text-decoration: none;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Authenticate User: {user_id}</h1>
        
        {status_message}
        
        <div>
            <h3>User Details:</h3>
            <p><strong>Display Name:</strong> {display_name}</p>
            <p><strong>Daily Limit:</strong> ₹{daily_limit}</p>
            <p><strong>Token Status:</strong> {token_status}</p>
        </div>

        <form action="/zerodha-multi/user/{user_id}/login" method="post">
            <input type="text" name="api_key" placeholder="User's Zerodha API Key" required>
            <input type="password" name="api_secret" placeholder="User's Zerodha API Secret" required>
            <button type="submit">Login to Zerodha</button>
        </form>

        <hr style="margin: 30px 0;">

        <h3>Manual Token Entry</h3>
        <form action="/zerodha-multi/user/{user_id}/manual-token" method="post">
            <input type="text" name="request_token" placeholder="Enter request_token from Zerodha URL" required>
            <button type="submit">Submit Token</button>
        </form>

        <a href="/zerodha-multi" class="back-link">← Back to All Users</a>
    </div>
</body>
</html>
"""

class UserAccount(BaseModel):
    """User account model"""
    user_id: str
    display_name: str
    email: str
    daily_limit: float
    is_active: bool = True
    created_at: datetime = None

class UserAuthRequest(BaseModel):
    """User authentication request"""
    api_key: str
    api_secret: str

class TokenSubmission(BaseModel):
    """Manual token submission"""
    request_token: str

class MultiUserStatus(BaseModel):
    """Multi-user status response"""
    master_authenticated: bool
    total_users: int
    authenticated_users: int
    users: List[Dict]

@router.get("/", response_class=HTMLResponse)
async def multi_user_dashboard(request: Request):
    """Display multi-user authentication dashboard"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get master account info
        master_api_key = os.getenv('ZERODHA_API_KEY', '')
        master_user_id = os.getenv('ZERODHA_USER_ID', '')
        
        # Get all registered users
        users_key = "zerodha:multi:users"
        users_data = await redis_client.get(users_key)
        users = json.loads(users_data) if users_data else {}
        
        # Build user cards HTML
        user_cards_html = ""
        for user_id, user_info in users.items():
            # Check token status
            token_key = f"zerodha:multi:token:{user_id}"
            token_exists = await redis_client.exists(token_key)
            
            token_status = "inactive"
            card_class = ""
            
            if token_exists:
                # Check expiry
                expiry_key = f"zerodha:multi:token_expiry:{user_id}"
                expiry_time = await redis_client.get(expiry_key)
                if expiry_time:
                    expiry_dt = datetime.fromisoformat(expiry_time.decode())
                    if expiry_dt > datetime.now():
                        token_status = "active"
                        card_class = "authenticated"
                    else:
                        token_status = "expired"
                        card_class = "expired"
            
            status_badge_class = token_status
            
            user_cards_html += f"""
            <div class="user-card {card_class}">
                <h4>{user_info.get('display_name', user_id)}</h4>
                <p><strong>User ID:</strong> {user_id}</p>
                <p><strong>Email:</strong> {user_info.get('email', 'N/A')}</p>
                <p><strong>Daily Limit:</strong> ₹{user_info.get('daily_limit', 0):,.0f}</p>
                <p><strong>Status:</strong> <span class="status-badge {status_badge_class}">{token_status.upper()}</span></p>
                <a href="/zerodha-multi/user/{user_id}"><button>Authenticate</button></a>
            </div>
            """
        
        if not user_cards_html:
            user_cards_html = "<p>No users registered yet. Add users below.</p>"
        
        html_content = MULTI_USER_AUTH_HTML.format(
            master_api_key=master_api_key[:10] + "..." if master_api_key else "Not configured",
            master_user_id=master_user_id or "Not configured",
            user_cards=user_cards_html
        )
        
        await redis_client.close()
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error rendering multi-user dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@router.post("/add-user")
async def add_user(request: Request):
    """Add a new user to the system"""
    try:
        form_data = await request.form()
        user_id = form_data.get('user_id')
        display_name = form_data.get('display_name')
        email = form_data.get('email')
        daily_limit = float(form_data.get('daily_limit', 0))
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get existing users
        users_key = "zerodha:multi:users"
        users_data = await redis_client.get(users_key)
        users = json.loads(users_data) if users_data else {}
        
        # Add new user
        users[user_id] = {
            'display_name': display_name,
            'email': email,
            'daily_limit': daily_limit,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        # Save users
        await redis_client.set(users_key, json.dumps(users))
        
        await redis_client.close()
        
        return RedirectResponse(url="/zerodha-multi", status_code=302)
        
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return RedirectResponse(url=f"/zerodha-multi?error={str(e)}", status_code=302)

@router.get("/user/{user_id}", response_class=HTMLResponse)
async def user_auth_page(user_id: str, request: Request):
    """Display individual user authentication page"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get user info
        users_key = "zerodha:multi:users"
        users_data = await redis_client.get(users_key)
        users = json.loads(users_data) if users_data else {}
        
        if user_id not in users:
            return HTMLResponse(content="<h1>User not found</h1>")
        
        user_info = users[user_id]
        
        # Check token status
        token_key = f"zerodha:multi:token:{user_id}"
        token_exists = await redis_client.exists(token_key)
        
        token_status = "Not authenticated"
        status_message = ""
        
        if token_exists:
            expiry_key = f"zerodha:multi:token_expiry:{user_id}"
            expiry_time = await redis_client.get(expiry_key)
            if expiry_time:
                expiry_dt = datetime.fromisoformat(expiry_time.decode())
                if expiry_dt > datetime.now():
                    token_status = f"Valid until {expiry_dt.strftime('%Y-%m-%d %I:%M %p')}"
                    status_message = '<div class="status success">✅ Authentication is valid!</div>'
                else:
                    token_status = "Expired"
                    status_message = '<div class="status error">❌ Token expired. Please login again.</div>'
        else:
            status_message = '<div class="status error">❌ Not authenticated. Please login.</div>'
        
        # Check for messages
        error = request.query_params.get('error')
        if error:
            status_message = f'<div class="status error">❌ Error: {error}</div>'
        
        success = request.query_params.get('success')
        if success:
            status_message = '<div class="status success">✅ Authentication successful!</div>'
        
        html_content = USER_AUTH_HTML.format(
            user_id=user_id,
            display_name=user_info.get('display_name', user_id),
            daily_limit=f"{user_info.get('daily_limit', 0):,.0f}",
            token_status=token_status,
            status_message=status_message
        )
        
        await redis_client.close()
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error rendering user auth page: {e}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@router.post("/user/{user_id}/login")
async def user_login(user_id: str, request: Request):
    """Initiate login for a specific user"""
    try:
        form_data = await request.form()
        api_key = form_data.get('api_key')
        api_secret = form_data.get('api_secret')
        
        # Import Kite
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            return RedirectResponse(
                url=f"/zerodha-multi/user/{user_id}?error=kiteconnect not installed",
                status_code=302
            )
        
        # Create Kite instance for this user
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        
        # Store credentials temporarily
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        session_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'user_id': user_id
        }
        
        await redis_client.setex(
            f"zerodha:multi:session:{user_id}",
            timedelta(minutes=10),
            json.dumps(session_data)
        )
        
        await redis_client.close()
        
        # Redirect to Zerodha
        return RedirectResponse(url=login_url, status_code=302)
        
    except Exception as e:
        logger.error(f"User login initiation failed: {e}")
        return RedirectResponse(
            url=f"/zerodha-multi/user/{user_id}?error={str(e)}",
            status_code=302
        )

@router.get("/callback/{user_id}")
async def user_callback(user_id: str, request: Request):
    """Handle callback for specific user"""
    try:
        request_token = request.query_params.get('request_token')
        if not request_token:
            raise ValueError("No request_token in callback")
        
        # Process token for this user
        success = await process_user_token(user_id, request_token)
        
        if success:
            return RedirectResponse(
                url=f"/zerodha-multi/user/{user_id}?success=true",
                status_code=302
            )
        else:
            return RedirectResponse(
                url=f"/zerodha-multi/user/{user_id}?error=Authentication failed",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"User callback failed: {e}")
        return RedirectResponse(
            url=f"/zerodha-multi/user/{user_id}?error={str(e)}",
            status_code=302
        )

@router.post("/user/{user_id}/manual-token")
async def user_manual_token(user_id: str, request: Request):
    """Handle manual token submission for user"""
    try:
        form_data = await request.form()
        request_token = form_data.get('request_token')
        
        success = await process_user_token(user_id, request_token)
        
        if success:
            return RedirectResponse(
                url=f"/zerodha-multi/user/{user_id}?success=true",
                status_code=302
            )
        else:
            return RedirectResponse(
                url=f"/zerodha-multi/user/{user_id}?error=Invalid token",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"Manual token submission failed: {e}")
        return RedirectResponse(
            url=f"/zerodha-multi/user/{user_id}?error={str(e)}",
            status_code=302
        )

async def process_user_token(user_id: str, request_token: str) -> bool:
    """Process token for a specific user"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Get session data
        session_data = await redis_client.get(f"zerodha:multi:session:{user_id}")
        if not session_data:
            raise ValueError("Session expired")
        
        session = json.loads(session_data)
        api_key = session['api_key']
        api_secret = session['api_secret']
        
        # Generate access token
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        
        access_token = data["access_token"]
        
        # Calculate expiry
        now = datetime.now()
        tomorrow_6am = datetime.combine(
            now.date() + timedelta(days=1),
            time(6, 0, 0)
        )
        if now.time() < time(6, 0, 0):
            expiry = datetime.combine(now.date(), time(6, 0, 0))
        else:
            expiry = tomorrow_6am
        
        # Store user token (for tracking/compliance)
        await redis_client.set(f"zerodha:multi:token:{user_id}", access_token)
        await redis_client.set(f"zerodha:multi:token_expiry:{user_id}", expiry.isoformat())
        
        # Store user credentials (encrypted in production)
        user_creds = {
            'api_key': api_key,
            'api_secret': api_secret,
            'authenticated_at': datetime.now().isoformat()
        }
        await redis_client.set(f"zerodha:multi:creds:{user_id}", json.dumps(user_creds))
        
        # Clean up session
        await redis_client.delete(f"zerodha:multi:session:{user_id}")
        
        await redis_client.close()
        
        logger.info(f"User {user_id} authenticated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Token processing failed for user {user_id}: {e}")
        return False

@router.get("/status", response_model=MultiUserStatus)
async def get_multi_user_status():
    """Get status of all users"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Check master authentication
        master_user_id = os.getenv('ZERODHA_USER_ID', '')
        master_token = await redis_client.get(f"zerodha:token:{master_user_id}")
        master_authenticated = bool(master_token)
        
        # Get all users
        users_data = await redis_client.get("zerodha:multi:users")
        users = json.loads(users_data) if users_data else {}
        
        # Check each user's status
        user_statuses = []
        authenticated_count = 0
        
        for user_id, user_info in users.items():
            token_exists = await redis_client.exists(f"zerodha:multi:token:{user_id}")
            is_authenticated = False
            
            if token_exists:
                expiry_data = await redis_client.get(f"zerodha:multi:token_expiry:{user_id}")
                if expiry_data:
                    expiry_dt = datetime.fromisoformat(expiry_data.decode())
                    is_authenticated = expiry_dt > datetime.now()
            
            if is_authenticated:
                authenticated_count += 1
            
            user_statuses.append({
                'user_id': user_id,
                'display_name': user_info.get('display_name'),
                'is_authenticated': is_authenticated,
                'daily_limit': user_info.get('daily_limit', 0)
            })
        
        await redis_client.close()
        
        return MultiUserStatus(
            master_authenticated=master_authenticated,
            total_users=len(users),
            authenticated_users=authenticated_count,
            users=user_statuses
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-trade")
async def execute_trade_for_user(user_id: str, trade_params: Dict):
    """
    Execute trade for a user through master API
    This is where all trades are routed through the single master account
    """
    try:
        # Verify user is authenticated and has permissions
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = await redis.from_url(redis_url)
        
        # Check user authentication
        token_exists = await redis_client.exists(f"zerodha:multi:token:{user_id}")
        if not token_exists:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get user info and check limits
        users_data = await redis_client.get("zerodha:multi:users")
        users = json.loads(users_data) if users_data else {}
        
        if user_id not in users:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_info = users[user_id]
        daily_limit = user_info.get('daily_limit', 0)
        
        # Check daily usage (implement your logic)
        # ... 
        
        # Execute trade through master account
        master_api_key = os.getenv('ZERODHA_API_KEY')
        master_token = await redis_client.get(f"zerodha:token:{os.getenv('ZERODHA_USER_ID')}")
        
        if not master_token:
            raise HTTPException(status_code=503, detail="Master account not authenticated")
        
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=master_api_key)
        kite.set_access_token(master_token.decode())
        
        # Add user tracking to the order
        trade_params['tag'] = f"USER_{user_id}"
        
        # Place order through master account
        order_id = kite.place_order(
            variety=trade_params.get('variety', 'regular'),
            **trade_params
        )
        
        # Log the trade for this user
        trade_log = {
            'user_id': user_id,
            'order_id': order_id,
            'params': trade_params,
            'executed_at': datetime.now().isoformat(),
            'master_account': os.getenv('ZERODHA_USER_ID')
        }
        
        # Store trade log
        await redis_client.lpush(
            f"zerodha:multi:trades:{user_id}",
            json.dumps(trade_log)
        )
        
        await redis_client.close()
        
        return {
            'success': True,
            'order_id': order_id,
            'user_id': user_id,
            'message': 'Trade executed through master account'
        }
        
    except Exception as e:
        logger.error(f"Trade execution failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
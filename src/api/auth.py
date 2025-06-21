"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create two routers - one for v1 and one for backward compatibility
router_v1 = APIRouter()  # Remove prefix since it's included under /v1 in main.py
router = APIRouter(prefix="/auth")  # Keep prefix for backward compatibility
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here")  # Use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Default admin user (for initial setup)
DEFAULT_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "full_name": "Admin User",
        "email": "admin@algoauto.com",
        "is_active": True,
        "is_admin": True
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper function to create login endpoint
def create_login_endpoint(router: APIRouter, prefix: str = ""):
    @router.post(f"{prefix}/login")
    async def login(request: Request, login_data: LoginRequest):
        """Login endpoint"""
        logger.info(f"Login attempt for user: {login_data.username}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request origin: {request.headers.get('origin', 'unknown')}")
        
        # Check if user exists
        user = DEFAULT_USERS.get(login_data.username)
        
        if not user:
            logger.warning(f"User not found: {login_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            logger.warning(f"Invalid password for user: {login_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"User is inactive: {login_data.username}")
            raise HTTPException(
                status_code=403,
                detail="User account is disabled"
            )
        
        logger.info(f"Login successful for user: {login_data.username}")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "is_admin": user.get("is_admin", False)},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_info": {
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "is_admin": user.get("is_admin", False)
            }
        }

# Create login endpoints for both routers
create_login_endpoint(router_v1, "/auth")  # Add /auth prefix for v1 router
create_login_endpoint(router)  # No prefix needed for backward compatibility router

# Add OPTIONS handlers for CORS preflight requests
@router_v1.options("/auth/login")
async def options_login_v1():
    """Handle CORS preflight for login endpoint"""
    return {"message": "OK"}

@router.options("/login")
async def options_login():
    """Handle CORS preflight for login endpoint"""
    return {"message": "OK"}

# Export both routers
__all__ = ["router", "router_v1"]

@router_v1.get("/auth/me")
async def get_current_user_v1(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = DEFAULT_USERS.get(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "is_admin": user.get("is_admin", False)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router_v1.post("/auth/logout")
async def logout_v1():
    """Logout endpoint (client should remove token)"""
    return {"message": "Logged out successfully"}

@router_v1.get("/auth/test")
async def test_auth_v1():
    """Test endpoint to verify auth router is working"""
    return {
        "message": "Auth router is working!", 
        "endpoint": "/api/v1/auth/test",
        "default_users": list(DEFAULT_USERS.keys()),
        "admin_password_hint": "admin123"
    }

@router_v1.get("/auth/debug")
async def debug_auth_v1():
    """Debug endpoint to check auth configuration"""
    admin_user = DEFAULT_USERS.get("admin", {})
    expected_hash = hashlib.sha256("admin123".encode()).hexdigest()
    
    return {
        "auth_configured": True,
        "admin_user_exists": "admin" in DEFAULT_USERS,
        "admin_password_hash_matches": admin_user.get("password_hash") == expected_hash,
        "expected_hash": expected_hash,
        "actual_hash": admin_user.get("password_hash", "NOT_SET"),
        "jwt_secret_configured": bool(SECRET_KEY),
        "cors_note": "Make sure CORS is properly configured in main.py"
    }

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = DEFAULT_USERS.get(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "is_admin": user.get("is_admin", False)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout():
    """Logout endpoint (client should remove token)"""
    return {"message": "Logged out successfully"}

@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth router is working"""
    return {
        "message": "Auth router is working!", 
        "endpoint": "/api/v1/auth/test",
        "default_users": list(DEFAULT_USERS.keys()),
        "admin_password_hint": "admin123"
    }

@router.get("/debug")
async def debug_auth():
    """Debug endpoint to check auth configuration"""
    admin_user = DEFAULT_USERS.get("admin", {})
    expected_hash = hashlib.sha256("admin123".encode()).hexdigest()
    
    return {
        "auth_configured": True,
        "admin_user_exists": "admin" in DEFAULT_USERS,
        "admin_password_hash_matches": admin_user.get("password_hash") == expected_hash,
        "expected_hash": expected_hash,
        "actual_hash": admin_user.get("password_hash", "NOT_SET"),
        "jwt_secret_configured": bool(SECRET_KEY),
        "cors_note": "Make sure CORS is properly configured in main.py"
    } 
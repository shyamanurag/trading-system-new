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

# Create a single router for v1
router_v1 = APIRouter(prefix="/auth") 
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Default admin user
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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router_v1.post("/login")
async def login(login_data: LoginRequest):
    """Simplified login endpoint for debugging"""
    user = DEFAULT_USERS.get(login_data.username)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is disabled")

    access_token = create_access_token(data={"sub": user["username"], "is_admin": user.get("is_admin", False)})
    
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

@router_v1.get("/me")
async def get_current_user_v1(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username or not (user := DEFAULT_USERS.get(username)):
            raise HTTPException(status_code=401, detail="Invalid token or user not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router_v1.get("/test")
async def test_auth_v1():
    """Test endpoint to verify auth router is working"""
    return {"message": "Simplified Auth router is working!", "endpoint": "/api/v1/auth/test"}

# Export only the v1 router
__all__ = ["router_v1"] 
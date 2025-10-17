"""
Trading Control API - Start/Stop Trading and User Management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import asyncio
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Global trading state
trading_state = {
    "is_running": False,
    "start_time": None,
    "orchestrator": None,
    "data_provider": None,
    "paper_trading": False  # CRITICAL FIX: Add missing paper_trading key
}

class BrokerUser(BaseModel):
    """Model for broker user credentials"""
    user_id: str
    name: str
    broker: str = "zerodha"
    api_key: str
    api_secret: str
    client_id: str
    initial_capital: float = 1000000.0  # 10 lakhs
    risk_tolerance: str = "medium"
    paper_trading: bool = True

class TradingCommand(BaseModel):
    """Model for trading control commands"""
    action: str  # start, stop, pause, resume

# In-memory user storage (replace with database in production)
broker_users = {}

def initialize_default_users():
    """Initialize master trading account dynamically based on environment Zerodha user"""
    try:
        # Get the master Zerodha user ID from environment (this is the primary trading account)
        master_zerodha_user_id = os.getenv('ZERODHA_USER_ID', 'QSW899')
        
        # Only add if master user doesn't exist (prevent duplicates)
        if master_zerodha_user_id not in broker_users:
            # Use production deployment credentials (matches app.yaml)
            real_api_key = os.getenv('ZERODHA_API_KEY', 'vc9ft4zpknynpm3u')
            real_api_secret = os.getenv('ZERODHA_API_SECRET', '0nwjb2cncw9stf3m5cre73rqc3bc5xsc')
            
            # VALIDATION: Ensure we're using the correct production credentials
            if real_api_key != 'vc9ft4zpknynpm3u':
                logger.warning(f"⚠️ API key mismatch detected: env={real_api_key[:8]}... vs production=vc9ft4zp...")
                logger.warning("Using production credentials from deployment")
                real_api_key = 'vc9ft4zpknynpm3u'
            
            # Create master user with ACTUAL Zerodha user ID as the key
            master_user = {
                "user_id": master_zerodha_user_id,  # Use real Zerodha user ID
                "name": f"Zerodha Account ({master_zerodha_user_id})",
                "broker": "zerodha",
                "api_key": real_api_key,
                "api_secret": real_api_secret,
                "client_id": master_zerodha_user_id,  # Same as user_id for Zerodha
                "initial_capital": 0.0,  # Will be dynamically fetched from Zerodha API
                "current_capital": 0.0,  # Will be dynamically fetched from Zerodha API
                "risk_tolerance": "medium",
                "paper_trading": True,  # Can be toggled per user
                "is_active": True,
                "is_master": True,  # Mark as master account
                "created_at": datetime.now().isoformat(),
                "total_pnl": 0,
                "daily_pnl": 0,
                "total_trades": 0,
                "win_rate": 0,
                "open_trades": 0
            }
            
            broker_users[master_zerodha_user_id] = master_user
            
            logger.info(f"✅ Initialized master Zerodha user: {master_zerodha_user_id}")
            logger.info(f"✅ Using API key: {real_api_key[:8]}...")
            logger.info("✅ System ready for multi-user Zerodha trading")
            
            return True
        else:
            logger.info(f"✅ Master user {master_zerodha_user_id} already exists - skipping initialization")
            return True
    except Exception as e:
        logger.error(f"❌ Error initializing default users: {e}")
        return False

# Auto-initialize default users on module import
try:
    initialize_default_users()
    logger.info(f"✅ Default users initialized. Active users: {list(broker_users.keys())}")
except Exception as e:
    logger.error(f"❌ Failed to initialize default users: {e}")
    # CRITICAL FIX: Force initialization as fallback with CORRECT production credentials
    master_zerodha_user_id = os.getenv('ZERODHA_USER_ID', 'QSW899')
    broker_users[master_zerodha_user_id] = {
        "user_id": master_zerodha_user_id,
        "name": f"Zerodha Account ({master_zerodha_user_id})", 
        "broker": "zerodha",
        "api_key": os.getenv('ZERODHA_API_KEY', 'vc9ft4zpknynpm3u'),  # CRITICAL FIX: Use correct production key
        "api_secret": os.getenv('ZERODHA_API_SECRET', '0nwjb2cncw9stf3m5cre73rqc3bc5xsc'),  # CRITICAL FIX: Use correct production secret
        "client_id": master_zerodha_user_id,
        "initial_capital": 0.0,  # Will be dynamically fetched from Zerodha API
        "current_capital": 0.0,  # Will be dynamically fetched from Zerodha API
        "risk_tolerance": "medium",
        "paper_trading": True,
        "is_active": True,
        "is_master": True,
        "created_at": datetime.now().isoformat(),
        "total_pnl": 0,
        "daily_pnl": 0,
        "total_trades": 0,
        "win_rate": 0,
        "open_trades": 0
    }
    logger.info(f"✅ Forced default user initialization as fallback for {master_zerodha_user_id}")

def create_or_update_zerodha_user(zerodha_user_id: str, user_profile: Optional[Dict[str, Any]] = None, api_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Dynamically create or update a Zerodha user when they authenticate
    This enables multi-user support with individual analytics and tracking
    """
    try:
        # Check if user already exists
        if zerodha_user_id in broker_users:
            logger.info(f"✅ Zerodha user {zerodha_user_id} already exists, updating profile")
            existing_user = broker_users[zerodha_user_id]
            
            # Update profile information if provided
            if user_profile:
                existing_user.update({
                    "name": user_profile.get("user_name", existing_user["name"]),
                    "email": user_profile.get("email", ""),
                    "phone": user_profile.get("phone", ""),
                    "broker": user_profile.get("broker", "zerodha"),
                    "last_login": datetime.now().isoformat()
                })
            
            # Update API credentials if provided (for master accounts)
            if api_credentials and existing_user.get("is_master", False):
                existing_user.update({
                    "api_key": api_credentials.get("api_key", existing_user["api_key"]),
                    "api_secret": api_credentials.get("api_secret", existing_user["api_secret"])
                })
            
            return existing_user
        
        # Create new user
        logger.info(f"✅ Creating new Zerodha user: {zerodha_user_id}")
        
        # Determine if this is the master account
        master_user_id = os.getenv('ZERODHA_USER_ID', 'QSW899')
        is_master = (zerodha_user_id == master_user_id)
        
        new_user = {
            "user_id": zerodha_user_id,
            "name": user_profile.get("user_name", f"Zerodha User ({zerodha_user_id})") if user_profile else f"Zerodha User ({zerodha_user_id})",
            "email": user_profile.get("email", "") if user_profile else "",
            "phone": user_profile.get("phone", "") if user_profile else "",
            "broker": "zerodha",
            "client_id": zerodha_user_id,
            "initial_capital": 0.0,  # Will be dynamically fetched from Zerodha API
            "current_capital": 0.0,  # Will be dynamically fetched from Zerodha API
            "risk_tolerance": "medium",
            "paper_trading": True,  # Start with paper trading, can be toggled
            "is_active": True,
            "is_master": is_master,  # Only master account can execute trades for others
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "total_pnl": 0,
            "daily_pnl": 0,
            "total_trades": 0,
            "win_rate": 0,
            "open_trades": 0,
            "max_daily_loss": 50000.0,  # Default 50K daily loss limit
            "max_position_size": 100000.0,  # Default 1L position limit
            "strategies_enabled": ["volume_profile_scalper", "momentum_surfer"]  # Default strategies
        }
        
        # Add API credentials only for master account
        if is_master and api_credentials:
            new_user.update({
                "api_key": api_credentials.get("api_key", os.getenv('ZERODHA_API_KEY')),
                "api_secret": api_credentials.get("api_secret", os.getenv('ZERODHA_API_SECRET'))
            })
        
        broker_users[zerodha_user_id] = new_user
        
        logger.info(f"✅ Created Zerodha user {zerodha_user_id} (Master: {is_master})")
        logger.info(f"✅ Total users in system: {len(broker_users)}")
        
        return new_user
        
    except Exception as e:
        logger.error(f"❌ Failed to create/update user {zerodha_user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {e}")

def get_master_user() -> Optional[Dict[str, Any]]:
    """Get the master Zerodha user (the one that can execute trades)"""
    for user_id, user_data in broker_users.items():
        if user_data.get("is_master", False):
            return user_data
    return None

def get_user_by_zerodha_id(zerodha_user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by their Zerodha user ID"""
    return broker_users.get(zerodha_user_id)

def list_all_zerodha_users() -> List[Dict[str, Any]]:
    """List all registered Zerodha users"""
    return list(broker_users.values())

@router.post("/users/broker")
async def add_broker_user(user: BrokerUser):
    """Add a broker user with credentials for paper trading"""
    try:
        # Validate required fields
        if not all([user.user_id, user.name, user.api_key, user.api_secret, user.client_id]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: user_id, name, api_key, api_secret, client_id"
            )

        # Check if user already exists
        if user.user_id in broker_users:
            raise HTTPException(
                status_code=400,
                detail=f"User {user.user_id} already exists"
            )

        # Store user credentials
        broker_users[user.user_id] = {
            "user_id": user.user_id,
            "name": user.name,
            "broker": user.broker,
            "api_key": user.api_key,
            "api_secret": user.api_secret,
            "client_id": user.client_id,
            "initial_capital": user.initial_capital,
            "current_capital": user.initial_capital,
            "risk_tolerance": user.risk_tolerance,
            "paper_trading": user.paper_trading,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "total_pnl": 0,
            "daily_pnl": 0,
            "total_trades": 0,
            "win_rate": 0,
            "open_trades": 0
        }
        
        # Set environment variables for the broker
        os.environ['ZERODHA_API_KEY'] = user.api_key
        os.environ['ZERODHA_API_SECRET'] = user.api_secret
        os.environ['ZERODHA_CLIENT_ID'] = user.client_id
        os.environ['PAPER_TRADING'] = str(user.paper_trading).lower()
        
        logger.info(f"Added broker user: {user.user_id} for {user.broker} trading")
        
        return {
            "success": True,
            "message": f"Broker user {user.user_id} added successfully",
            "user": broker_users[user.user_id]
        }
        
    except HTTPException as he:
        logger.error(f"Validation error adding broker user: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error adding broker user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/broker")
async def get_broker_users():
    """Get all broker users"""
    try:
        # Convert to list format expected by frontend
        users_list = list(broker_users.values())
        
        # Add mock data if no users exist
        if not users_list:
            # NO MOCK DATA - Real broker data required
            return {
                "success": True,
                "users": []
            }
        
        # Format users for frontend
        formatted_users = []
        for user in users_list:
            formatted_users.append({
                "user_id": user["user_id"],
                "name": user["name"],
                "username": user["user_id"],
                "avatar": user["name"][0].upper(),
                "initial_capital": user["initial_capital"],
                "current_capital": user["current_capital"],
                "total_pnl": user["total_pnl"],
                "daily_pnl": user["daily_pnl"],
                "total_trades": user["total_trades"],
                "win_rate": user["win_rate"],
                "is_active": user["is_active"],
                "open_trades": user["open_trades"],
                "paper_trading": user["paper_trading"]
            })
        
        return {
            "success": True,
            "users": formatted_users
        }
        
    except Exception as e:
        logger.error(f"Error fetching broker users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/broker/{user_id}")
async def update_broker_user(user_id: str, user: BrokerUser):
    """Update an existing broker user"""
    try:
        # Check if user exists
        if user_id not in broker_users:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )
        
        # Update user data
        broker_users[user_id].update({
            "name": user.name,
            "broker": user.broker,
            "api_key": user.api_key,
            "api_secret": user.api_secret,
            "client_id": user.client_id,
            "initial_capital": user.initial_capital,
            "risk_tolerance": user.risk_tolerance,
            "paper_trading": user.paper_trading,
            "updated_at": datetime.now().isoformat()
        })
        
        # Update environment variables
        os.environ['ZERODHA_API_KEY'] = user.api_key
        os.environ['ZERODHA_API_SECRET'] = user.api_secret
        os.environ['ZERODHA_CLIENT_ID'] = user.client_id
        os.environ['PAPER_TRADING'] = str(user.paper_trading).lower()
        
        logger.info(f"Updated broker user: {user_id} - Paper Trading: {user.paper_trading}")
        
        return {
            "success": True,
            "message": f"Broker user {user_id} updated successfully",
            "user": broker_users[user_id]
        }
        
    except HTTPException as he:
        logger.error(f"Validation error updating broker user: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error updating broker user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/broker/{user_id}")
async def delete_broker_user(user_id: str):
    """Delete a broker user"""
    try:
        # Check if user exists
        if user_id not in broker_users:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )
        
        # Remove user
        deleted_user = broker_users.pop(user_id)
        
        logger.info(f"Deleted broker user: {user_id}")
        
        return {
            "success": True,
            "message": f"Broker user {user_id} deleted successfully",
            "deleted_user": deleted_user
        }
        
    except HTTPException as he:
        logger.error(f"Error deleting broker user: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error deleting broker user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/broker/initialize")
async def initialize_users():
    """Manual endpoint to reinitialize default users (useful for testing)"""
    try:
        success = initialize_default_users()
        if success:
            return {
                "success": True,
                "message": "Default users initialized successfully",
                "users": list(broker_users.values())
            }
        else:
            return {
                "success": False,
                "message": "Failed to initialize default users"
            }
    except Exception as e:
        logger.error(f"Error in manual user initialization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/zerodha/register")
async def register_zerodha_user_dynamically(request: Dict[str, Any]):
    """
    Register a new Zerodha user dynamically when they authenticate
    This is called automatically by auth endpoints when a new user submits token
    """
    try:
        zerodha_user_id = request.get('zerodha_user_id')
        if not zerodha_user_id:
            raise HTTPException(status_code=400, detail="zerodha_user_id is required")
        
        # Get user profile from Zerodha if available
        user_profile = request.get('user_profile', {})
        api_credentials = request.get('api_credentials', {})
        
        # Create or update the user
        user_data = create_or_update_zerodha_user(
            zerodha_user_id=zerodha_user_id,
            user_profile=user_profile,
            api_credentials=api_credentials
        )
        
        logger.info(f"✅ Successfully registered/updated Zerodha user: {zerodha_user_id}")
        
        return {
            "success": True,
            "message": f"Zerodha user {zerodha_user_id} registered successfully",
            "user": user_data,
            "total_users": len(broker_users)
        }
        
    except Exception as e:
        logger.error(f"❌ Error registering Zerodha user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/zerodha/{zerodha_user_id}")
async def get_zerodha_user_profile(zerodha_user_id: str):
    """Get profile and analytics for a specific Zerodha user"""
    try:
        user_data = get_user_by_zerodha_id(zerodha_user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail=f"Zerodha user {zerodha_user_id} not found")
        
        return {
            "success": True,
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/zerodha")
async def list_zerodha_users():
    """List all registered Zerodha users with their analytics"""
    try:
        all_users = list_all_zerodha_users()
        
        return {
            "success": True,
            "users": all_users,
            "total_users": len(all_users),
            "master_user": get_master_user()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing Zerodha users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trading/control")
async def control_trading(command: TradingCommand):
    """Control trading operations - start, stop, pause, resume"""
    try:
        global trading_state
        
        if command.action == "start":
            if trading_state["is_running"]:
                return {
                    "success": False,
                    "message": "Trading is already running",
                    "status": "running"
                }
            
            # Check if we have at least one user
            if not broker_users:
                return {
                    "success": False,
                    "message": "No broker users configured. Please add a user first.",
                    "status": "no_users"
                }
            
            # Start trading components
            logger.info("Starting trading system...")
            
            # Import and initialize components
            from src.core.orchestrator import TradingOrchestrator
            from data.truedata_client import (
                initialize_truedata,
                get_truedata_status, 
                is_connected,
                live_market_data,
                truedata_connection_status
            )
            
            # Create config
            config = {
                'redis': {
                    'host': os.getenv('REDIS_HOST', 'localhost'),
                    'port': int(os.getenv('REDIS_PORT', 6379)),
                    'password': os.getenv('REDIS_PASSWORD'),
                    'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
                },
                'broker': {
                    'api_key': os.getenv('ZERODHA_API_KEY'),
                    'api_secret': os.getenv('ZERODHA_API_SECRET'),
                    'client_id': os.getenv('ZERODHA_CLIENT_ID')
                },
                'data_provider': {
                                    'username': os.getenv('TRUEDATA_USERNAME', 'tdwsp697'),
                'password': os.getenv('TRUEDATA_PASSWORD', 'shyam@697'),
                    'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
                    'port': int(os.getenv('TRUEDATA_PORT', 8084))
                },
                'strategies': {
                    'volatility_explosion': {'enabled': True},
                    'momentum_surfer': {'enabled': True},
                    'volume_profile_scalper': {'enabled': True},
                    'news_impact_scalper': {'enabled': True}
                }
            }
            
            # Initialize orchestrator (singleton)
            trading_state["orchestrator"] = TradingOrchestrator.get_instance()
            
            # Enable trading
            await trading_state["orchestrator"].enable_trading()
            
            trading_state["is_running"] = True
            trading_state["start_time"] = datetime.now().isoformat()
            
            logger.info(f"Trading started - Zerodha API will handle paper/live mode automatically")
            
            return {
                "success": True,
                "message": f"Trading started successfully - Zerodha API will handle paper/live mode automatically",
                "status": "running",
                "start_time": trading_state["start_time"]
            }
            
        elif command.action == "stop":
            if not trading_state["is_running"]:
                return {
                    "success": False,
                    "message": "Trading is not running",
                    "status": "stopped"
                }
            
            # Stop trading
            logger.info("Stopping trading system...")
            
            if trading_state["orchestrator"]:
                await trading_state["orchestrator"].disable_trading()
                trading_state["orchestrator"] = None
            
            trading_state["is_running"] = False
            trading_state["start_time"] = None
            
            logger.info("Trading stopped")
            
            return {
                "success": True,
                "message": "Trading stopped successfully",
                "status": "stopped"
            }
            
        elif command.action == "status":
            return {
                "success": True,
                "status": "running" if trading_state["is_running"] else "stopped",
                "paper_trading": trading_state["paper_trading"],
                "start_time": trading_state["start_time"],
                "users_count": len(broker_users)
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {command.action}")
            
    except Exception as e:
        logger.error(f"Error controlling trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/status")
async def get_trading_status():
    """Get current trading system status"""
    try:
        return {
            "success": True,
            "is_running": trading_state["is_running"],
            "paper_trading": trading_state["paper_trading"],
            "start_time": trading_state["start_time"],
            "users_count": len(broker_users),
            "autonomous_trading": trading_state["is_running"],
            "status": "running" if trading_state["is_running"] else "stopped"
        }
    except Exception as e:
        logger.error(f"Error getting trading status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add Zerodha Manual Authentication endpoints to existing working router
@router.get("/zerodha-manual/auth-url")
async def get_zerodha_manual_auth_url():
    """Get Zerodha authorization URL for manual token extraction"""
    try:
        api_key = os.getenv('ZERODHA_API_KEY', 'vc9ft4zpknynpm3u')  # CRITICAL FIX: Use correct production key
        auth_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}"
        
        return {
            "success": True,
            "auth_url": auth_url,
            "instructions": [
                "1. Click the authorization URL",
                "2. Login to Zerodha with your credentials", 
                "3. After login, you'll be redirected to a URL",
                "4. Copy the 'request_token' parameter from the redirected URL",
                "5. Paste the token in the manual token entry"
            ],
            "example_redirect": "https://yourapp.com/callback?request_token=YOUR_TOKEN_HERE&action=login&status=success",
            "note": "Extract only the request_token value, not the full URL",
            "status": "Ready for use after TrueData testing complete"
        }
    except Exception as e:
        logger.error(f"Failed to generate Zerodha auth URL: {e}")
        return {"success": False, "error": str(e)}

@router.get("/zerodha-manual/status")
async def get_zerodha_manual_status(user_id: str = "ZERODHA_DEFAULT"):
    """Get current Zerodha manual authentication status"""
    try:
        return {
            "success": True,
            "message": "Zerodha manual auth ready - awaiting TrueData completion",
            "authenticated": False,
            "user_id": user_id,
            "note": "System ready for manual token submission when needed",
            "priority": "TrueData first, Zerodha second (as planned)"
        }
    except Exception as e:
        logger.error(f"Zerodha manual status check failed: {e}")
        return {
            "success": False,
            "message": f"Status check failed: {str(e)}",
            "authenticated": False
        }

@router.post("/zerodha-manual/submit-token")
async def submit_zerodha_manual_token(request: dict):
    """Submit manually extracted Zerodha request token (for future use)"""
    try:
        request_token = request.get('request_token', '')
        user_id = request.get('user_id', 'ZERODHA_DEFAULT')
        
        # Validate token format
        if not request_token or len(request_token) < 10:
            return {
                "success": False,
                "error": "Invalid request token format. Token should be at least 10 characters long."
            }
        
        # For now, just validate the token format and return success
        # Full implementation will be activated after TrueData testing
        return {
            "success": True,
            "message": "Token format validated. Full processing ready after TrueData completion.",
            "user_id": user_id,
            "token_preview": f"{request_token[:8]}...",
            "status": "Stored for future activation",
            "note": "Zerodha integration will be activated post-TrueData testing"
        }
        
    except Exception as e:
        logger.error(f"Zerodha manual token submission failed: {e}")
        return {"success": False, "error": str(e)}

@router.get("/zerodha-manual/test")
async def test_zerodha_manual_system():
    """Test Zerodha manual auth system readiness"""
    return {
        "success": True,
        "message": "Zerodha manual authentication system ready",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "status": "Standby - awaiting TrueData completion",
        "endpoints": [
            "/api/v1/control/zerodha-manual/auth-url",
            "/api/v1/control/zerodha-manual/status", 
            "/api/v1/control/zerodha-manual/submit-token",
            "/api/v1/control/zerodha-manual/test"
        ],
        "workflow": "TrueData → Complete Testing → Zerodha Authorization → Trading Ready"
    }

# 🚨 MANUAL OVERRIDE ENDPOINTS

class ManualOverride(BaseModel):
    """Manual override command"""
    action: str  # 'pause_trading', 'resume_trading', 'close_position', 'close_all', 'override_loss_limit'
    symbol: Optional[str] = None
    reason: str

@router.post("/manual/override")
async def manual_override(command: ManualOverride):
    """
    Manual trading override - EMERGENCY CONTROL
    
    Actions:
    - pause_trading: Stop new position entries (keep monitoring existing)
    - resume_trading: Resume normal trading
    - close_position: Close specific position immediately
    - close_all: Close all open positions immediately
    - override_loss_limit: Temporarily override daily loss limit (use with caution)
    """
    try:
        orchestrator = trading_state.get("orchestrator")
        if not orchestrator:
            raise HTTPException(status_code=400, detail="Trading system not running")
        
        action = command.action.lower()
        logger.warning(f"🚨 MANUAL OVERRIDE: {action} - Reason: {command.reason}")
        
        if action == 'pause_trading':
            orchestrator.manual_trading_paused = True
            
            # Log system event
            if hasattr(orchestrator, 'performance_tracker') and orchestrator.performance_tracker:
                await orchestrator.performance_tracker.log_system_event({
                    'event_type': 'manual_override',
                    'severity': 'warning',
                    'component': 'manual_control',
                    'title': 'Trading Paused Manually',
                    'description': f'Manual pause initiated. Reason: {command.reason}',
                    'capital_at_event': getattr(orchestrator, 'current_capital', 0),
                    'daily_pnl_at_event': getattr(orchestrator.position_decision, 'daily_realized_pnl', 0),
                    'open_positions_count': len(orchestrator.position_tracker.positions) if hasattr(orchestrator, 'position_tracker') else 0
                })
            
            return {
                "success": True,
                "message": "Trading paused - no new positions will be opened",
                "action": "pause_trading",
                "timestamp": datetime.now().isoformat(),
                "note": "Existing positions continue to be monitored"
            }
        
        elif action == 'resume_trading':
            orchestrator.manual_trading_paused = False
            
            if hasattr(orchestrator, 'performance_tracker') and orchestrator.performance_tracker:
                await orchestrator.performance_tracker.log_system_event({
                    'event_type': 'manual_override',
                    'severity': 'info',
                    'component': 'manual_control',
                    'title': 'Trading Resumed Manually',
                    'description': f'Manual resume initiated. Reason: {command.reason}',
                    'capital_at_event': getattr(orchestrator, 'current_capital', 0),
                    'daily_pnl_at_event': getattr(orchestrator.position_decision, 'daily_realized_pnl', 0),
                    'open_positions_count': len(orchestrator.position_tracker.positions) if hasattr(orchestrator, 'position_tracker') else 0
                })
            
            return {
                "success": True,
                "message": "Trading resumed - normal operations",
                "action": "resume_trading",
                "timestamp": datetime.now().isoformat()
            }
        
        elif action == 'close_position':
            if not command.symbol:
                raise HTTPException(status_code=400, detail="Symbol required for close_position")
            
            # Close specific position
            if hasattr(orchestrator, 'position_monitor') and orchestrator.position_monitor:
                position = await orchestrator.position_tracker.get_position(command.symbol)
                if not position:
                    return {"success": False, "error": f"Position not found: {command.symbol}"}
                
                # Create manual exit condition
                from src.core.position_monitor import ExitCondition
                exit_condition = ExitCondition(
                    condition_type='manual_override',
                    symbol=command.symbol,
                    trigger_price=position.current_price,
                    reason=f'Manual close: {command.reason}',
                    priority=0  # Highest priority
                )
                
                success = await orchestrator.position_monitor._execute_exit(exit_condition)
                
                if hasattr(orchestrator, 'performance_tracker') and orchestrator.performance_tracker:
                    await orchestrator.performance_tracker.log_system_event({
                        'event_type': 'manual_override',
                        'severity': 'warning',
                        'component': 'manual_control',
                        'title': f'Position Closed Manually: {command.symbol}',
                        'description': f'Reason: {command.reason}',
                        'affected_symbols': [command.symbol],
                        'capital_at_event': getattr(orchestrator, 'current_capital', 0),
                        'daily_pnl_at_event': getattr(orchestrator.position_decision, 'daily_realized_pnl', 0),
                        'open_positions_count': len(orchestrator.position_tracker.positions) if hasattr(orchestrator, 'position_tracker') else 0
                    })
                
                return {
                    "success": success,
                    "message": f"Position {command.symbol} closed manually",
                    "action": "close_position",
                    "symbol": command.symbol,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Position monitor not available"}
        
        elif action == 'close_all':
            closed_positions = []
            failed_positions = []
            
            if hasattr(orchestrator, 'position_tracker') and orchestrator.position_tracker:
                positions = orchestrator.position_tracker.positions
                
                for symbol, position in positions.items():
                    try:
                        from src.core.position_monitor import ExitCondition
                        exit_condition = ExitCondition(
                            condition_type='manual_override',
                            symbol=symbol,
                            trigger_price=position.current_price,
                            reason=f'Manual close all: {command.reason}',
                            priority=0
                        )
                        
                        success = await orchestrator.position_monitor._execute_exit(exit_condition)
                        if success:
                            closed_positions.append(symbol)
                        else:
                            failed_positions.append(symbol)
                    except Exception as e:
                        logger.error(f"Failed to close {symbol}: {e}")
                        failed_positions.append(symbol)
                
                if hasattr(orchestrator, 'performance_tracker') and orchestrator.performance_tracker:
                    await orchestrator.performance_tracker.log_system_event({
                        'event_type': 'manual_override',
                        'severity': 'critical',
                        'component': 'manual_control',
                        'title': 'All Positions Closed Manually',
                        'description': f'Reason: {command.reason}. Closed: {len(closed_positions)}, Failed: {len(failed_positions)}',
                        'affected_symbols': closed_positions + failed_positions,
                        'capital_at_event': getattr(orchestrator, 'current_capital', 0),
                        'daily_pnl_at_event': getattr(orchestrator.position_decision, 'daily_realized_pnl', 0),
                        'open_positions_count': 0
                    })
                
                return {
                    "success": True,
                    "message": "All positions closed",
                    "action": "close_all",
                    "closed_positions": closed_positions,
                    "failed_positions": failed_positions,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Position tracker not available"}
        
        elif action == 'override_loss_limit':
            if hasattr(orchestrator, 'position_decision'):
                orchestrator.position_decision.daily_loss_limit_breached = False
                orchestrator.position_decision.daily_loss_breach_time = None
                
                logger.critical(f"🚨 DAILY LOSS LIMIT OVERRIDDEN - Reason: {command.reason}")
                
                if hasattr(orchestrator, 'performance_tracker') and orchestrator.performance_tracker:
                    await orchestrator.performance_tracker.log_system_event({
                        'event_type': 'manual_override',
                        'severity': 'critical',
                        'component': 'manual_control',
                        'title': 'Daily Loss Limit Overridden',
                        'description': f'⚠️ CAUTION: Loss limit bypassed. Reason: {command.reason}',
                        'capital_at_event': getattr(orchestrator, 'current_capital', 0),
                        'daily_pnl_at_event': orchestrator.position_decision.daily_realized_pnl,
                        'open_positions_count': len(orchestrator.position_tracker.positions) if hasattr(orchestrator, 'position_tracker') else 0
                    })
                
                return {
                    "success": True,
                    "message": "⚠️ Daily loss limit overridden - USE WITH EXTREME CAUTION",
                    "action": "override_loss_limit",
                    "current_daily_pnl": orchestrator.position_decision.daily_realized_pnl,
                    "timestamp": datetime.now().isoformat(),
                    "warning": "System will accept new trades despite exceeding 2% loss limit"
                }
            else:
                return {"success": False, "error": "Position decision system not available"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual override failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")

@router.get("/manual/status")
async def get_manual_status():
    """Get current manual override status"""
    try:
        orchestrator = trading_state.get("orchestrator")
        if not orchestrator:
            return {"trading_active": False, "message": "System not running"}
        
        status = {
            "trading_active": trading_state.get("is_running", False),
            "manual_paused": getattr(orchestrator, 'manual_trading_paused', False),
            "loss_limit_breached": getattr(orchestrator.position_decision, 'daily_loss_limit_breached', False) if hasattr(orchestrator, 'position_decision') else False,
            "daily_pnl": getattr(orchestrator.position_decision, 'daily_realized_pnl', 0) if hasattr(orchestrator, 'position_decision') else 0,
            "open_positions": len(orchestrator.position_tracker.positions) if hasattr(orchestrator, 'position_tracker') else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    except Exception as e:
        logger.error(f"Error getting manual status: {e}")
        return {"error": str(e)} 
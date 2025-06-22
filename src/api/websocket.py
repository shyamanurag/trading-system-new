from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import logging
import json
import redis
from src.core.websocket_manager import get_websocket_manager, initialize_websocket_manager
from src.core.redis_client import get_redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_ws_manager():
    """Dependency to get WebSocket manager instance"""
    redis_client = get_redis_client()
    ws_manager = get_websocket_manager()
    if not ws_manager:
        ws_manager = await initialize_websocket_manager(redis_client)
    return ws_manager

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trade updates"""
    await websocket.accept()
    connection_id = None
    user_id = None
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connected. Please authenticate."
        })
        
        # Wait for authentication message
        auth_timeout = 30  # 30 seconds to authenticate
        try:
            # First message should be authentication
            data = await websocket.receive_json()
            
            if data.get("type") == "auth":
                user_id = data.get("userId", "anonymous")
                # In production, validate the token here
                # For now, accept any userId
                
                await websocket.send_json({
                    "type": "auth",
                    "status": "success",
                    "userId": user_id,
                    "message": f"Authenticated as {user_id}"
                })
                
                # Now handle regular messages
                while True:
                    data = await websocket.receive_json()
                    
                    # Echo back for now
                    await websocket.send_json({
                        "type": "echo",
                        "data": data,
                        "userId": user_id
                    })
                    
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "First message must be authentication"
                })
                await websocket.close()
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {user_id or 'unauthenticated'}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close() 
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import logging
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
async def websocket_endpoint(
    websocket: WebSocket,
    ws_manager = Depends(get_ws_manager)
):
    """WebSocket endpoint for real-time trade updates"""
    connection_id = None
    try:
        # For now, use a default user_id. In production, this would come from authentication
        user_id = "default_user"
        
        # Connect client with user_id
        connection_id = await ws_manager.connect(websocket, user_id)
        
        try:
            # Keep connection alive and handle messages
            while True:
                # Wait for any message from client
                data = await websocket.receive_json()
                
                # Handle client messages
                response = await ws_manager.handle_client_message(connection_id, data)
                if response:
                    await websocket.send_json(response)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup on disconnect
            if connection_id:
                await ws_manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close() 
from fastapi import APIRouter, WebSocket, Depends
from ..core.websocket_manager import WebSocketManager
from ..models import User
from ..auth import get_current_user_ws

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws)
):
    """WebSocket endpoint for real-time trade updates"""
    try:
        # Get WebSocket manager instance
        ws_manager = WebSocketManager(current_user.config['redis_url'])
        
        # Connect client
        await ws_manager.connect(websocket)
        
        try:
            # Keep connection alive and handle messages
            while True:
                # Wait for any message from client
                data = await websocket.receive_text()
                # Currently not handling any client messages
                # Could be used for filtering or specific requests
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            # Cleanup on disconnect
            ws_manager.disconnect(websocket)
            
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close() 
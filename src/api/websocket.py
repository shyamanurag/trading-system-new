"""
WebSocket API endpoints for real-time data streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
active_connections: Set[WebSocket] = set()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for any message from client
                data = await websocket.receive_text()
                
                # Echo back or process the message
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Process other messages if needed
                    await websocket.send_json({
                        "type": "echo",
                        "data": data
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Remove from active connections
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")

async def broadcast_message(message: dict):
    """Broadcast message to all connected clients"""
    if active_connections:
        # Create tasks for all connections
        tasks = []
        for connection in active_connections.copy():
            tasks.append(send_to_client(connection, message))
        
        # Wait for all sends to complete
        await asyncio.gather(*tasks, return_exceptions=True)

async def send_to_client(websocket: WebSocket, message: dict):
    """Send message to a specific client"""
    try:
        await websocket.send_json(message)
    except Exception as e:
        logger.error(f"Error sending to client: {e}")
        # Remove dead connection
        active_connections.discard(websocket) 
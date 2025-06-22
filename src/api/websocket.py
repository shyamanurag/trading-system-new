"""
WebSocket API endpoints for real-time data streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from typing import Set, Optional
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
active_connections: Set[WebSocket] = set()

@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """Main WebSocket endpoint for real-time updates"""
    # Accept all connections for now (authentication can be added later)
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
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(data)
                        await websocket.send_json({
                            "type": "echo",
                            "data": json_data
                        })
                    except json.JSONDecodeError:
                        # If not JSON, send as text
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

# Add a test page for WebSocket
@router.get("/test")
async def get_websocket_test():
    """Test page for WebSocket connection"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <button onclick="connectWS()">Connect</button>
        <button onclick="sendPing()">Send Ping</button>
        <button onclick="disconnectWS()">Disconnect</button>
        <div id="messages"></div>
        <script>
            let ws = null;
            const messages = document.getElementById('messages');
            
            function log(msg) {
                messages.innerHTML += '<p>' + msg + '</p>';
            }
            
            function connectWS() {
                const wsUrl = window.location.protocol === 'https:' 
                    ? 'wss://' + window.location.host + '/ws'
                    : 'ws://' + window.location.host + '/ws';
                    
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => log('Connected to WebSocket');
                ws.onmessage = (e) => log('Received: ' + e.data);
                ws.onerror = (e) => log('Error: ' + e.message);
                ws.onclose = () => log('Disconnected');
            }
            
            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                    log('Sent: ping');
                }
            }
            
            function disconnectWS() {
                if (ws) {
                    ws.close();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

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
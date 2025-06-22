"""
WebSocket API endpoints for real-time data streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
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
    # Accept the connection without any conditions
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected from {websocket.client}. Total connections: {len(active_connections)}")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive with ping/pong
        while True:
            try:
                # Set a timeout for receiving messages
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle different message types
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "heartbeat":
                    await websocket.send_json({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
                else:
                    # Echo back any other message
                    try:
                        json_data = json.loads(message)
                        await websocket.send_json({
                            "type": "message",
                            "data": json_data
                        })
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "message",
                            "data": message
                        })
                        
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
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
        disconnected = set()
        
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            active_connections.discard(conn)

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
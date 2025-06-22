"""
WebSocket API endpoints for real-time data streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Set, AsyncGenerator
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
active_connections: Set[WebSocket] = set()
sse_clients: Set[asyncio.Queue] = set()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    # Log the connection attempt
    logger.info(f"WebSocket connection attempt from {websocket.client}")
    logger.info(f"Headers: {websocket.headers}")
    
    try:
        # Accept the connection without any conditions
        await websocket.accept()
        active_connections.add(websocket)
        logger.info(f"WebSocket client connected from {websocket.client}. Total connections: {len(active_connections)}")
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
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
                    await websocket.send_json({
                        "type": "heartbeat", 
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    # Echo back any other message
                    try:
                        json_data = json.loads(message)
                        await websocket.send_json({
                            "type": "message",
                            "data": json_data,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "message",
                            "data": message,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
    finally:
        # Remove from active connections
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")

# Server-Sent Events as fallback
@router.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint as fallback for WebSocket"""
    logger.info(f"SSE connection from {request.client}")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()
        sse_clients.add(queue)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'message': 'SSE connection established', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            while True:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            sse_clients.discard(queue)
            logger.info(f"SSE client disconnected. Total SSE clients: {len(sse_clients)}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )

async def broadcast_message(message: dict):
    """Broadcast message to all connected clients (WebSocket and SSE)"""
    # Add timestamp if not present
    if 'timestamp' not in message:
        message['timestamp'] = datetime.utcnow().isoformat()
    
    # Broadcast to WebSocket clients
    if active_connections:
        disconnected = set()
        
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            active_connections.discard(conn)
    
    # Broadcast to SSE clients
    for queue in sse_clients:
        try:
            await queue.put(message)
        except Exception as e:
            logger.error(f"Error broadcasting to SSE client: {e}")

# Add a test page for both WebSocket and SSE
@router.get("/test")
async def get_websocket_test():
    """Test page for WebSocket and SSE connections"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket/SSE Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            button { margin: 5px; padding: 10px; }
            #messages { 
                border: 1px solid #ccc; 
                height: 300px; 
                overflow-y: auto; 
                padding: 10px; 
                margin-top: 20px;
                background: #f5f5f5;
            }
            .error { color: red; }
            .success { color: green; }
            .info { color: blue; }
        </style>
    </head>
    <body>
        <h1>Real-time Connection Test</h1>
        
        <h2>WebSocket Test</h2>
        <button onclick="connectWS()">Connect WebSocket</button>
        <button onclick="sendPing()">Send Ping</button>
        <button onclick="disconnectWS()">Disconnect WebSocket</button>
        
        <h2>SSE Test (Fallback)</h2>
        <button onclick="connectSSE()">Connect SSE</button>
        <button onclick="disconnectSSE()">Disconnect SSE</button>
        
        <div id="messages"></div>
        
        <script>
            let ws = null;
            let eventSource = null;
            const messages = document.getElementById('messages');
            
            function log(msg, type = 'info') {
                const timestamp = new Date().toLocaleTimeString();
                messages.innerHTML += '<p class="' + type + '">[' + timestamp + '] ' + msg + '</p>';
                messages.scrollTop = messages.scrollHeight;
            }
            
            function connectWS() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    log('WebSocket already connected', 'error');
                    return;
                }
                
                const wsUrl = window.location.protocol === 'https:' 
                    ? 'wss://' + window.location.host + '/ws'
                    : 'ws://' + window.location.host + '/ws';
                
                log('Connecting to WebSocket: ' + wsUrl);
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => log('WebSocket connected', 'success');
                ws.onmessage = (e) => log('WebSocket received: ' + e.data);
                ws.onerror = (e) => log('WebSocket error occurred', 'error');
                ws.onclose = (e) => log('WebSocket disconnected (code: ' + e.code + ')', 'error');
            }
            
            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                    log('Sent ping via WebSocket');
                } else {
                    log('WebSocket not connected', 'error');
                }
            }
            
            function disconnectWS() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function connectSSE() {
                if (eventSource) {
                    log('SSE already connected', 'error');
                    return;
                }
                
                const sseUrl = '/ws/sse';
                log('Connecting to SSE: ' + sseUrl);
                
                eventSource = new EventSource(sseUrl);
                
                eventSource.onopen = () => log('SSE connected', 'success');
                
                eventSource.onmessage = (e) => {
                    log('SSE received: ' + e.data);
                };
                
                eventSource.onerror = (e) => {
                    if (eventSource.readyState === EventSource.CLOSED) {
                        log('SSE disconnected', 'error');
                    } else {
                        log('SSE error occurred', 'error');
                    }
                };
            }
            
            function disconnectSSE() {
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    log('SSE disconnected');
                }
            }
            
            // Auto-connect SSE if WebSocket fails
            function autoFallback() {
                connectWS();
                setTimeout(() => {
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        log('WebSocket failed, falling back to SSE', 'info');
                        connectSSE();
                    }
                }, 3000);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html) 
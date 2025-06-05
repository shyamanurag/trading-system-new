from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from typing import List, Dict
import asyncio
from ..core.websocket_manager import WebSocketManager
from .order_routes import router as order_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Start WebSocket server on application startup"""
    asyncio.create_task(websocket_manager.start())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading data"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle different message types
                if message.get('type') == 'subscribe':
                    await websocket_manager.handle_subscription(websocket, message)
                elif message.get('type') == 'unsubscribe':
                    await websocket_manager.handle_unsubscription(websocket, message)
                else:
                    await websocket_manager.handle_other_messages(websocket, message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        await websocket.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Trading System API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "websocket_clients": len(websocket_manager.clients)
    }

# Add more API endpoints here as needed
app.include_router(order_router, prefix="/api") 
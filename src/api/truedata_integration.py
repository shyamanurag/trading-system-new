"""
TrueData Integration API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
import logging
from datetime import datetime
import asyncio

from src.data.truedata_client import get_truedata_client, init_truedata_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/truedata", tags=["truedata"])

@router.post("/connect")
async def connect_truedata(credentials: Dict):
    """Connect to TrueData live feed"""
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        # Initialize TrueData client
        client = await init_truedata_client(username, password)
        
        if client:
            return {
                "success": True,
                "message": "TrueData connected successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to TrueData")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to TrueData: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/subscribe")
async def subscribe_symbols(symbols: List[str]):
    """Subscribe to symbols for live data"""
    try:
        client = get_truedata_client()
        if not client:
            raise HTTPException(status_code=503, detail="TrueData client not connected")
        
        success = await client.subscribe_symbols(symbols)
        
        if success:
            return {
                "success": True,
                "message": f"Subscribed to {len(symbols)} symbols",
                "symbols": symbols,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to subscribe to symbols")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/unsubscribe")
async def unsubscribe_symbols(symbols: List[str]):
    """Unsubscribe from symbols"""
    try:
        client = get_truedata_client()
        if not client:
            raise HTTPException(status_code=503, detail="TrueData client not connected")
        
        success = await client.unsubscribe_symbols(symbols)
        
        if success:
            return {
                "success": True,
                "message": f"Unsubscribed from {len(symbols)} symbols",
                "symbols": symbols,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to unsubscribe from symbols")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from symbols: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status")
async def get_truedata_status():
    """Get TrueData connection status"""
    try:
        client = get_truedata_client()
        
        if not client:
            return {
                "connected": False,
                "message": "TrueData client not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "connected": client.is_connected,
            "subscribed_symbols": client.get_subscribed_symbols(),
            "total_symbols": len(client.get_subscribed_symbols()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting TrueData status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/data/{symbol}")
async def get_symbol_data(symbol: str):
    """Get latest market data for a specific symbol"""
    try:
        client = get_truedata_client()
        if not client:
            raise HTTPException(status_code=503, detail="TrueData client not connected")
        
        data = client.get_market_data(symbol)
        
        if data:
            return {
                "success": True,
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "symbol": symbol,
                "message": "No data available for symbol",
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbol data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/data")
async def get_all_market_data():
    """Get all market data"""
    try:
        client = get_truedata_client()
        if not client:
            raise HTTPException(status_code=503, detail="TrueData client not connected")
        
        data = client.get_all_market_data()
        
        return {
            "success": True,
            "data": data,
            "total_symbols": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/disconnect")
async def disconnect_truedata():
    """Disconnect from TrueData"""
    try:
        client = get_truedata_client()
        if not client:
            raise HTTPException(status_code=503, detail="TrueData client not connected")
        
        await client.disconnect()
        
        return {
            "success": True,
            "message": "TrueData disconnected successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting from TrueData: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# WebSocket integration for real-time data
@router.websocket("/ws/{symbol}")
async def truedata_websocket(websocket, symbol: str):
    """WebSocket endpoint for real-time TrueData"""
    try:
        client = get_truedata_client()
        if not client:
            await websocket.close(code=1011, reason="TrueData client not connected")
            return
        
        # Subscribe to symbol if not already subscribed
        if symbol not in client.get_subscribed_symbols():
            await client.subscribe_symbols([symbol])
        
        # Send initial data
        initial_data = client.get_market_data(symbol)
        if initial_data:
            await websocket.send_json({
                "type": "initial_data",
                "symbol": symbol,
                "data": initial_data
            })
        
        # Keep connection alive and send updates
        while True:
            # Get latest data
            data = client.get_market_data(symbol)
            if data:
                await websocket.send_json({
                    "type": "market_data",
                    "symbol": symbol,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error for symbol {symbol}: {e}")
        await websocket.close(code=1011, reason="Internal error") 
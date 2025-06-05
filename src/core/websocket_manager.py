"""
WebSocket manager for handling real-time connections and subscriptions
"""
from fastapi import WebSocket
from typing import Dict, Set, List, Optional
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        # Thread-safe storage with locks
        self._lock = asyncio.Lock()
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_channels: Dict[str, Set[str]] = {}
        self.user_symbols: Dict[str, Set[str]] = {}
        self.user_trade_types: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        async with self._lock:
            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            # Initialize user subscriptions
            if user_id not in self.user_channels:
                self.user_channels[user_id] = set()
            if user_id not in self.user_symbols:
                self.user_symbols[user_id] = set()
            if user_id not in self.user_trade_types:
                self.user_trade_types[user_id] = set()
                
        logger.info(f"WebSocket client connected for user {user_id}")
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client"""
        async with self._lock:
            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    
            # Clean up subscriptions
            if user_id in self.user_channels:
                del self.user_channels[user_id]
            if user_id in self.user_symbols:
                del self.user_symbols[user_id]
            if user_id in self.user_trade_types:
                del self.user_trade_types[user_id]
                
        logger.info(f"WebSocket client disconnected for user {user_id}")
        
    async def subscribe(self, websocket: WebSocket, user_id: str, channels: List[str]):
        """Subscribe to specific channels"""
        async with self._lock:
            if user_id not in self.user_channels:
                self.user_channels[user_id] = set()
                
            # Add channels to user's subscriptions
            self.user_channels[user_id].update(channels)
            
        # Send confirmation
        await websocket.send_json({
            "type": "subscription",
            "channels": channels,
            "status": "subscribed"
        })
        
        logger.info(f"User {user_id} subscribed to channels: {channels}")
        
    async def unsubscribe(self, websocket: WebSocket, user_id: str, channels: List[str]):
        """Unsubscribe from specific channels"""
        async with self._lock:
            if user_id in self.user_channels:
                # Remove channels from user's subscriptions
                self.user_channels[user_id].difference_update(channels)
                
        # Send confirmation
        await websocket.send_json({
            "type": "subscription",
            "channels": channels,
            "status": "unsubscribed"
        })
        
        logger.info(f"User {user_id} unsubscribed from channels: {channels}")
        
    async def subscribe_symbols(self, websocket: WebSocket, user_id: str, symbols: List[str]):
        """Subscribe to specific symbols"""
        async with self._lock:
            if user_id not in self.user_symbols:
                self.user_symbols[user_id] = set()
                
            # Add symbols to user's subscriptions
            self.user_symbols[user_id].update(symbols)
            
        # Send confirmation
        await websocket.send_json({
            "type": "symbol_subscription",
            "symbols": symbols,
            "status": "subscribed"
        })
        
        logger.info(f"User {user_id} subscribed to symbols: {symbols}")
        
    async def unsubscribe_symbols(self, websocket: WebSocket, user_id: str, symbols: List[str]):
        """Unsubscribe from specific symbols"""
        async with self._lock:
            if user_id in self.user_symbols:
                # Remove symbols from user's subscriptions
                self.user_symbols[user_id].difference_update(symbols)
                
        # Send confirmation
        await websocket.send_json({
            "type": "symbol_subscription",
            "symbols": symbols,
            "status": "unsubscribed"
        })
        
        logger.info(f"User {user_id} unsubscribed from symbols: {symbols}")
        
    async def subscribe_trade_types(self, websocket: WebSocket, user_id: str, trade_types: List[str]):
        """Subscribe to specific trade types"""
        if user_id not in self.user_trade_types:
            self.user_trade_types[user_id] = set()
            
        # Add trade types to user's subscriptions
        self.user_trade_types[user_id].update(trade_types)
        
        # Send confirmation
        await websocket.send_json({
            "type": "trade_type_subscription",
            "trade_types": trade_types,
            "status": "subscribed"
        })
        
        logger.info(f"User {user_id} subscribed to trade types: {trade_types}")
        
    async def unsubscribe_trade_types(self, websocket: WebSocket, user_id: str, trade_types: List[str]):
        """Unsubscribe from specific trade types"""
        if user_id in self.user_trade_types:
            # Remove trade types from user's subscriptions
            self.user_trade_types[user_id].difference_update(trade_types)
            
        # Send confirmation
        await websocket.send_json({
            "type": "trade_type_subscription",
            "trade_types": trade_types,
            "status": "unsubscribed"
        })
        
        logger.info(f"User {user_id} unsubscribed from trade types: {trade_types}")
        
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to all connections of a specific user"""
        async with self._lock:
            if user_id in self.active_connections:
                # Add timestamp to message
                message["timestamp"] = datetime.utcnow().isoformat()
                
                # Send to all user's connections
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                        
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to all users subscribed to a specific channel"""
        async with self._lock:
            # Add timestamp to message
            message["timestamp"] = datetime.utcnow().isoformat()
            
            # Find all users subscribed to the channel
            for user_id, channels in self.user_channels.items():
                if channel in channels:
                    await self.broadcast_to_user(user_id, message)
                    
    async def broadcast_market_data(self, symbol: str, data: dict):
        """Broadcast market data to users subscribed to the symbol"""
        message = {
            "type": "market_data",
            "symbol": symbol,
            "data": data
        }
        
        async with self._lock:
            # Find all users subscribed to the symbol
            for user_id, symbols in self.user_symbols.items():
                if symbol in symbols:
                    await self.broadcast_to_user(user_id, message)
                    
    async def broadcast_trade_update(self, user_id: str, trade_type: str, data: dict):
        """Broadcast trade update to user if subscribed to the trade type"""
        async with self._lock:
            if user_id in self.user_trade_types and trade_type in self.user_trade_types[user_id]:
                message = {
                    "type": "trade_update",
                    "trade_type": trade_type,
                    "data": data
                }
                await self.broadcast_to_user(user_id, message)
                
    async def broadcast_system_message(self, message: str, level: str = "info"):
        """Broadcast system message to all connected clients"""
        async with self._lock:
            system_message = {
                "type": "system_message",
                "message": message,
                "level": level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for user_id in self.active_connections:
                await self.broadcast_to_user(user_id, system_message)
                
    async def get_active_connections_count(self) -> int:
        """Get total number of active connections"""
        async with self._lock:
            return sum(len(connections) for connections in self.active_connections.values())
            
    async def get_user_subscriptions(self, user_id: str) -> Dict[str, List[str]]:
        """Get all subscriptions for a user"""
        async with self._lock:
            return {
                "channels": list(self.user_channels.get(user_id, set())),
                "symbols": list(self.user_symbols.get(user_id, set())),
                "trade_types": list(self.user_trade_types.get(user_id, set()))
            } 
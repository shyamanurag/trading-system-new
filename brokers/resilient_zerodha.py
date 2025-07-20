"""
Resilient Zerodha Connection
Manages resilient connection to Zerodha broker with automatic recovery
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import time
import sys
from pathlib import Path

# Ensure project root is in Python path for src imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.connection_manager import ResilientConnection
from .zerodha import ZerodhaIntegration

logger = logging.getLogger(__name__)

class ResilientZerodhaConnection(ResilientConnection):
    """Resilient connection wrapper for Zerodha broker"""
    
    def __init__(self, broker: ZerodhaIntegration, config: Dict):
        super().__init__("zerodha", config)
        self.broker = broker
        self._last_order_time = None
        self._order_rate_limit = config.get('order_rate_limit', 1.0)  # orders per second
        self._order_semaphore = asyncio.Semaphore(1)
        self._ws_reconnect_delay = config.get('ws_reconnect_delay', 5)
        self._ws_max_reconnect_attempts = config.get('ws_max_reconnect_attempts', 10)
        self._ws_reconnect_attempts = 0
        self._ws_last_reconnect = None
    
    async def _connect_impl(self) -> None:
        """Establish connection to Zerodha"""
        try:
            await self.broker.initialize()
            
            # Verify connection by fetching account details
            account_info = await self.broker.get_account_info()
            if not account_info:
                raise ConnectionError("Failed to fetch account information")
                
            # Set up WebSocket reconnection monitoring
            asyncio.create_task(self._monitor_websocket())
            
        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            raise
    
    async def _disconnect_impl(self) -> None:
        """Disconnect from Zerodha"""
        try:
            await self.broker.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
    
    async def _health_check_impl(self) -> bool:
        """Check Zerodha connection health"""
        try:
            # Check if we can fetch account info
            account_info = await self.broker.get_account_info()
            if not account_info:
                return False
                
            # Check WebSocket connection - handle missing attribute gracefully
            if not hasattr(self.broker, 'ticker_connected') or not self.broker.ticker_connected:
                logger.debug("WebSocket not connected or ticker_connected attribute missing")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def _monitor_websocket(self):
        """Monitor WebSocket connection and handle reconnection"""
        while True:
            try:
                if not hasattr(self.broker, 'ticker_connected'):
                    logger.debug("WebSocket monitoring disabled - ticker_connected attribute not available")
                    await asyncio.sleep(60)
                    continue
                
                if not self.broker.ticker_connected:
                    current_time = time.time()
                    if self._ws_last_reconnect is None or current_time - self._ws_last_reconnect >= self._ws_reconnect_delay:
                        if self._ws_reconnect_attempts < self._ws_max_reconnect_attempts:
                            logger.info(f"Attempting WebSocket reconnection (attempt {self._ws_reconnect_attempts + 1})")
                            await self.broker._initialize_websocket()
                            self._ws_reconnect_attempts += 1
                            self._ws_last_reconnect = current_time
                        else:
                            logger.error("Max WebSocket reconnection attempts reached")
                            await asyncio.sleep(self._ws_reconnect_delay * 2)
                            self._ws_reconnect_attempts = 0
                else:
                    self._ws_reconnect_attempts = 0
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in WebSocket monitoring: {e}")
                await asyncio.sleep(5)
    
    async def place_order(self, order_params: Dict) -> Dict:
        """Place order with rate limiting and retry"""
        async with self._order_semaphore:
            # Rate limiting
            if self._last_order_time:
                elapsed = time.time() - self._last_order_time
                if elapsed < self._order_rate_limit:
                    await asyncio.sleep(self._order_rate_limit - elapsed)
            
            try:
                order = await self.execute(
                    self.broker.place_order,
                    order_params
                )
                self._last_order_time = time.time()
                return order
            except Exception as e:
                logger.error(f"Failed to place order: {e}")
                raise
    
    async def modify_order(self, order_id: str, order_params: Dict) -> Dict:
        """Modify order with retry"""
        return await self.execute(
            self.broker.modify_order,
            order_id,
            order_params
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order with retry"""
        return await self.execute(
            self.broker.cancel_order,
            order_id
        )
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status with retry"""
        return await self.execute(
            self.broker.get_order_status,
            order_id
        )
    
    async def get_positions(self) -> Dict:
        """Get positions with retry"""
        return await self.execute(
            self.broker.get_positions
        )
    
    async def get_holdings(self) -> Dict:
        """Get holdings with retry"""
        return await self.execute(
            self.broker.get_holdings
        )
    
    async def get_margins(self) -> Dict:
        """Get margins with retry"""
        return await self.execute(
            self.broker.get_margins
        )
    
    @property
    def connection_status(self) -> Dict:
        """Get detailed connection status"""
        health = self.get_health()
        status = {
            'name': self.name,
            'state': health.state.value,
            'last_connected': health.last_connected.isoformat() if health.last_connected else None,
            'last_error': health.last_error,
            'reconnect_attempts': health.reconnect_attempts,
            'latency_ms': health.latency_ms,
            'uptime_seconds': health.uptime_seconds,
            'broker': 'zerodha',
            'order_rate_limit': self._order_rate_limit,
            'last_order_time': self._last_order_time,
            'ws_connected': self.broker.ticker_connected if hasattr(self.broker, 'ticker_connected') else False,
            'ws_reconnect_attempts': self._ws_reconnect_attempts,
            'ws_last_reconnect': self._ws_last_reconnect
        }
        return status
    
    @property
    def mock_mode(self) -> bool:
        """Get mock mode status from underlying broker"""
        return getattr(self.broker, 'mock_mode', False)

    async def execute(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        await self.ensure_connected()
        return await func(*args, **kwargs)

    # FIXED: Add missing initialize method that orchestrator expects
    async def initialize(self) -> bool:
        """Initialize the resilient Zerodha connection"""
        try:
            logger.info("🔄 Initializing ResilientZerodhaConnection...")
            await self.connect()
            logger.info("✅ ResilientZerodhaConnection initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ ResilientZerodhaConnection initialization failed: {e}")
            return False

    # Implement abstract methods from parent class
    async def _do_connect(self):
        """Actual connection logic"""
        await self._connect_impl()
    
    async def _do_disconnect(self):
        """Actual disconnection logic"""
        await self._disconnect_impl()
    
    async def _check_connection_alive(self) -> bool:
        """Check if connection is alive"""
        return await self._health_check_impl()
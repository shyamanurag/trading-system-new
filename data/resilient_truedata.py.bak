"""
Resilient TrueData Connection
Manages resilient connection to TrueData with automatic recovery
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import time

from core.connection_manager import ResilientConnection
from .truedata_provider import TrueDataProvider

logger = logging.getLogger(__name__)

class ResilientTrueDataConnection(ResilientConnection):
    """Resilient connection wrapper for TrueData provider"""
    
    def __init__(self, data_provider: TrueDataProvider, config: Dict):
        super().__init__("truedata", config)
        self.data_provider = data_provider
        self._last_data_time = None
        self._data_timeout = config.get('data_timeout', 60)  # seconds
        self._reconnect_delay = config.get('reconnect_delay', 5)
        self._max_reconnect_attempts = config.get('max_reconnect_attempts', 10)
        self._reconnect_attempts = 0
        self._last_reconnect = None
    
    async def execute(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        await self.ensure_connected()
        return await func(*args, **kwargs)
    
    async def _do_connect(self):
        """Actual connection logic"""
        await self._connect_impl()
    
    async def _do_disconnect(self):
        """Actual disconnection logic"""
        await self._disconnect_impl()
    
    async def _check_connection_alive(self) -> bool:
        """Check if connection is alive"""
        return await self._health_check_impl()
    
    async def _connect_impl(self) -> None:
        """Establish connection to TrueData"""
        try:
            # Connect to TrueData
            connected = await self.data_provider.connect()
            if not connected:
                raise ConnectionError("Failed to connect to TrueData")
            
            # Subscribe to default symbols
            default_symbols = self.config.get('default_symbols', ['NIFTY-I', 'BANKNIFTY-I'])
            subscribed = await self.data_provider.subscribe_market_data(default_symbols)
            if not subscribed:
                raise ConnectionError("Failed to subscribe to market data")
            
            logger.info("TrueData connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to establish TrueData connection: {e}")
            raise
    
    async def _disconnect_impl(self) -> None:
        """Disconnect from TrueData"""
        try:
            await self.data_provider.disconnect()
            logger.info("TrueData disconnected successfully")
        except Exception as e:
            logger.error(f"Error during TrueData disconnection: {e}")
    
    async def _health_check_impl(self) -> bool:
        """Check TrueData connection health"""
        try:
            # Check if we can get latest data
            latest_data = await self.data_provider.get_latest_data('NIFTY-I')
            
            # Check if data is fresh
            if latest_data:
                self._last_data_time = datetime.now()
                return True
            
            # Check if data is stale
            if self._last_data_time:
                time_since_last_data = (datetime.now() - self._last_data_time).total_seconds()
                if time_since_last_data > self._data_timeout:
                    logger.warning(f"TrueData data is stale ({time_since_last_data}s old)")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"TrueData health check failed: {e}")
            return False
    
    async def subscribe_market_data(self, symbols: list) -> bool:
        """Subscribe to market data with retry"""
        return await self.execute(
            self.data_provider.subscribe_market_data,
            symbols
        )
    
    async def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest data with retry"""
        return await self.execute(
            self.data_provider.get_latest_data,
            symbol
        )
    
    async def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime, bar_size: str = "1 min"):
        """Get historical data with retry"""
        return await self.execute(
            self.data_provider.get_historical_data,
            symbol,
            start_time,
            end_time,
            bar_size
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
            'provider': 'truedata',
            'data_timeout': self._data_timeout,
            'last_data_time': self._last_data_time.isoformat() if self._last_data_time else None,
            'subscribed_symbols': list(self.data_provider.subscribed_symbols) if hasattr(self.data_provider, 'subscribed_symbols') else []
        }
        return status 
"""
Connection Manager
Handles all external connections with automatic reconnection and health monitoring
"""
import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class ConnectionManager:
    """Manages all external connections with health monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connections = {}
        self.status_callbacks = []
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
    async def initialize_all_connections(self):
        """Initialize all required connections"""
        tasks = []
        
        # Zerodha connection
        tasks.append(self._initialize_zerodha())
        
        # TrueData connection
        tasks.append(self._initialize_truedata())
        
        # Database connection
        tasks.append(self._initialize_database())
        
        # Redis connection
        tasks.append(self._initialize_redis())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        all_connected = all(not isinstance(r, Exception) for r in results)
        
        if not all_connected:
            logger.error("Some connections failed to initialize")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Connection {i} failed: {result}")
        
        return all_connected
    
    async def _initialize_zerodha(self):
        """Initialize Zerodha connection with health check"""
        try:
            from .zerodha import ZerodhaIntegration
            
            zerodha = ZerodhaIntegration(self.config)
            await zerodha.initialize()
            
            # Set up health monitoring
            asyncio.create_task(self._monitor_connection('zerodha', zerodha))
            
            self.connections['zerodha'] = {
                'instance': zerodha,
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            
            logger.info("Zerodha connection initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Zerodha: {e}")
            self.connections['zerodha'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': str(e)
            }
            raise
    
    async def _initialize_truedata(self):
        """Initialize TrueData connection"""
        try:
            # Import TrueData client (you'll need to implement this)
            # from .truedata_client import TrueDataClient
            
            # For now, mock it
            logger.info("TrueData connection initialized (mock)")
            self.connections['truedata'] = {
                'instance': None,  # TrueDataClient would go here
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TrueData: {e}")
            raise
    
    async def _initialize_database(self):
        """Initialize database connection"""
        try:
            from .database import get_db_connection
            
            db = await get_db_connection()
            self.connections['database'] = {
                'instance': db,
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            
            logger.info("Database connection initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url(self.config.get('REDIS_URL'))
            await redis_client.ping()
            
            self.connections['redis'] = {
                'instance': redis_client,
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            
            logger.info("Redis connection initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def _monitor_connection(self, name: str, connection):
        """Monitor connection health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Perform health check
                is_healthy = await self._check_connection_health(name, connection)
                
                if not is_healthy:
                    logger.warning(f"{name} connection unhealthy, attempting reconnect")
                    await self._reconnect(name)
                else:
                    self.connections[name]['last_check'] = datetime.now()
                    self.reconnect_attempts[name] = 0
                    
            except Exception as e:
                logger.error(f"Error monitoring {name}: {e}")
    
    async def _check_connection_health(self, name: str, connection) -> bool:
        """Check if connection is healthy"""
        try:
            if name == 'zerodha':
                return await connection.is_connected()
            elif name == 'database':
                # Perform a simple query
                return True  # Implement actual check
            elif name == 'redis':
                await connection.instance.ping()
                return True
            elif name == 'truedata':
                return True  # Implement actual check
            return False
        except:
            return False
    
    async def _reconnect(self, name: str):
        """Attempt to reconnect a failed connection"""
        if name not in self.reconnect_attempts:
            self.reconnect_attempts[name] = 0
        
        self.reconnect_attempts[name] += 1
        
        if self.reconnect_attempts[name] > self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {name}")
            self.connections[name]['status'] = ConnectionStatus.ERROR
            await self._notify_connection_failure(name)
            return
        
        self.connections[name]['status'] = ConnectionStatus.RECONNECTING
        
        try:
            if name == 'zerodha':
                await self._initialize_zerodha()
            elif name == 'database':
                await self._initialize_database()
            elif name == 'redis':
                await self._initialize_redis()
            elif name == 'truedata':
                await self._initialize_truedata()
                
            logger.info(f"Successfully reconnected {name}")
            
        except Exception as e:
            logger.error(f"Reconnection failed for {name}: {e}")
            await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts[name])
            asyncio.create_task(self._reconnect(name))
    
    async def _notify_connection_failure(self, name: str):
        """Notify about connection failure"""
        for callback in self.status_callbacks:
            await callback(name, ConnectionStatus.ERROR)
    
    def get_connection(self, name: str):
        """Get a specific connection"""
        return self.connections.get(name, {}).get('instance')
    
    def get_status(self, name: str) -> ConnectionStatus:
        """Get connection status"""
        return self.connections.get(name, {}).get('status', ConnectionStatus.DISCONNECTED)
    
    def is_all_connected(self) -> bool:
        """Check if all critical connections are active"""
        critical = ['zerodha', 'truedata', 'database', 'redis']
        return all(
            self.get_status(name) == ConnectionStatus.CONNECTED 
            for name in critical
        )
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status updates"""
        self.status_callbacks.append(callback)
    
    async def shutdown(self):
        """Gracefully shutdown all connections"""
        for name, conn_info in self.connections.items():
            try:
                if conn_info['instance']:
                    if hasattr(conn_info['instance'], 'disconnect'):
                        await conn_info['instance'].disconnect()
                    elif hasattr(conn_info['instance'], 'close'):
                        await conn_info['instance'].close()
                logger.info(f"Disconnected {name}")
            except Exception as e:
                logger.error(f"Error disconnecting {name}: {e}") 
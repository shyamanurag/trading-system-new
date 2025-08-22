"""
Connection Manager
Handles all external connections with automatic reconnection and health monitoring
"""
import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import os

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class ConnectionHealth:
    """Health status of a connection"""
    def __init__(self):
        self.state = ConnectionStatus.DISCONNECTED
        self.last_connected = None
        self.last_error = None
        self.reconnect_attempts = 0
        self.latency_ms = 0
        self.uptime_seconds = 0

class ResilientConnection(ABC):
    """Base class for resilient connections with automatic retry and recovery"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.health = ConnectionHealth()
        self._retry_attempts = 0
        self._max_retry_attempts = config.get('max_retry_attempts', 3)
        self._retry_delay = config.get('retry_delay', 1.0)
        self._connection_timeout = config.get('connection_timeout', 30.0)
        self._health_check_interval = config.get('health_check_interval', 30.0)
        self._last_health_check = None
        self._is_monitoring = False
        
    async def connect(self) -> bool:
        """Connect with retry logic"""
        self.health.state = ConnectionStatus.CONNECTING
        self._retry_attempts = 0
        
        while self._retry_attempts < self._max_retry_attempts:
            try:
                await asyncio.wait_for(
                    self._do_connect(), 
                    timeout=self._connection_timeout
                )
                
                self.health.state = ConnectionStatus.CONNECTED
                self.health.last_connected = datetime.now()
                self.health.reconnect_attempts = self._retry_attempts
                self._retry_attempts = 0
                
                # Start health monitoring
                if not self._is_monitoring:
                    asyncio.create_task(self._health_monitor())
                    self._is_monitoring = True
                
                logger.info(f"Connected to {self.name}")
                return True
                
            except Exception as e:
                self._retry_attempts += 1
                self.health.last_error = str(e)
                logger.error(f"Connection attempt {self._retry_attempts} failed for {self.name}: {e}")
                
                if self._retry_attempts < self._max_retry_attempts:
                    await asyncio.sleep(self._retry_delay * self._retry_attempts)
        
        self.health.state = ConnectionStatus.ERROR
        logger.error(f"Failed to connect to {self.name} after {self._max_retry_attempts} attempts")
        return False
    
    async def disconnect(self):
        """Disconnect from service"""
        try:
            self.health.state = ConnectionStatus.DISCONNECTED
            await self._do_disconnect()
            logger.info(f"Disconnected from {self.name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")
    
    async def ensure_connected(self):
        """Ensure connection is established"""
        if self.health.state != ConnectionStatus.CONNECTED:
            await self.connect()
    
    async def execute(self, func, *args, **kwargs):
        """Execute function with retry on connection failure"""
        await self.ensure_connected()
        
        retry_count = 0
        while retry_count < self._max_retry_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retry_count += 1
                logger.warning(f"Execution failed for {self.name} (attempt {retry_count}): {e}")
                
                if retry_count < self._max_retry_attempts:
                    # Try to reconnect
                    await self.connect()
                    await asyncio.sleep(self._retry_delay)
                else:
                    raise
    
    async def _health_monitor(self):
        """Monitor connection health"""
        while self.health.state in [ConnectionStatus.CONNECTED, ConnectionStatus.RECONNECTING]:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                if await self._check_connection_alive():
                    self._last_health_check = datetime.now()
                    if self.health.last_connected:
                        self.health.uptime_seconds = (datetime.now() - self.health.last_connected).total_seconds()
                else:
                    logger.warning(f"Health check failed for {self.name}, reconnecting...")
                    await self._reconnect()
                    
            except Exception as e:
                logger.error(f"Error in health monitor for {self.name}: {e}")
    
    async def _reconnect(self):
        """Attempt to reconnect"""
        self.health.state = ConnectionStatus.RECONNECTING
        await self.connect()
    
    def get_health(self) -> ConnectionHealth:
        """Get current health status"""
        return self.health
    
    @abstractmethod
    async def _do_connect(self):
        """Implement actual connection logic"""
        pass
    
    @abstractmethod
    async def _do_disconnect(self):
        """Implement actual disconnection logic"""
        pass
    
    @abstractmethod
    async def _check_connection_alive(self) -> bool:
        """Check if connection is still alive"""
        pass

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
        """Initialize all required connections with error handling"""
        results = []
        
        # Initialize connections with better error handling
        try:
            # Zerodha connection (optional for autonomous mode)
            zerodha_result = await self._initialize_zerodha_safe()
            results.append(zerodha_result)
        except Exception as e:
            logger.warning(f"Zerodha initialization failed: {e}")
            results.append(False)
        
        try:
            # TrueData connection (optional)
            truedata_result = await self._initialize_truedata_safe() 
            results.append(truedata_result)
        except Exception as e:
            logger.warning(f"TrueData initialization failed: {e}")
            results.append(False)
        
        try:
            # Database connection (optional for trading)
            database_result = await self._initialize_database_safe()
            results.append(database_result)
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            results.append(False)
        
        try:
            # Redis connection (optional)
            redis_result = await self._initialize_redis_safe()
            results.append(redis_result)
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            # ELIMINATED: Mock Redis connection that could mislead users
            
            # SAFETY: Return proper error instead of fake connection
            logger.error("SAFETY: Mock Redis connection ELIMINATED to prevent fake data caching")
            self.connections['redis'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': f'SAFETY: Mock Redis disabled - real Redis required: {str(e)}'
            }
            return False
        
        # Check results - require at least basic connectivity
        successful_connections = sum(results)
        total_connections = len(results)
        
        logger.info(f"Connection results: {successful_connections}/{total_connections} successful")
        
        # For autonomous trading, we need at least 1 connection working
        # We can trade with paper mode even if some connections fail
        return successful_connections >= 1
    
    async def _initialize_zerodha_safe(self):
        """Safely initialize Zerodha connection"""
        try:
            logger.info("Initializing Zerodha connection...")
            
            # CRITICAL FIX: Check if orchestrator already has a working Zerodha client
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                    logger.info("✅ Using existing Zerodha client from orchestrator (prevents token conflicts)")
                    self.connections['zerodha'] = orchestrator.zerodha_client
                    return True
            except Exception as e:
                logger.debug(f"Could not get orchestrator client: {e}")
            
            # Import ZerodhaIntegration from the correct location
            from brokers.zerodha import ZerodhaIntegration
            
            # Get access token from environment or Redis
            access_token = os.getenv('ZERODHA_ACCESS_TOKEN')
            user_id = os.getenv('ZERODHA_USER_ID')
            
            # If no access token in environment, check Redis with multiple key patterns
            if not access_token and user_id:
                try:
                    import redis.asyncio as redis
                    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
                    redis_client = redis.from_url(redis_url)
                    
                    # CRITICAL FIX: Use EXACT SAME pattern as token submission in zerodha_manual_auth.py
                    # Token is stored at: zerodha:token:{actual_user_id} 
                    primary_user_id = os.getenv('ZERODHA_USER_ID', 'QSW899')
                    token_keys_to_check = [
                        f"zerodha:token:{primary_user_id}",  # PRIMARY: Matches zerodha_manual_auth.py storage
                        f"zerodha:token:{user_id}",  # Fallback: env user_id if different
                    ]
                    
                    for key in token_keys_to_check:
                        stored_token = await redis_client.get(key)
                        if stored_token:
                            access_token = stored_token.decode() if isinstance(stored_token, bytes) else stored_token
                            logger.info(f"✅ Found Zerodha token in Redis with key: {key}")
                            break
                    
                    # If still no token, check all zerodha:token:* keys
                    if not access_token:
                        logger.info("🔍 Searching all zerodha:token:* keys in Redis...")
                        all_keys = await redis_client.keys("zerodha:token:*")
                        for key in all_keys:
                            stored_token = await redis_client.get(key)
                            if stored_token:
                                access_token = stored_token.decode() if isinstance(stored_token, bytes) else stored_token
                                logger.info(f"✅ Found Zerodha token in Redis with key: {key}")
                                break
                    
                    await redis_client.close()
                    
                except Exception as redis_error:
                    logger.warning(f"Could not check Redis for stored token: {redis_error}")
            
            # Create config with real trading only
            api_key = os.getenv('ZERODHA_API_KEY')
            user_id = os.getenv('ZERODHA_USER_ID')
            
            # CRITICAL FIX: Allow initialization without access token
            has_api_credentials = all([api_key, user_id])
            
            zerodha_config = {
                'api_key': api_key,
                'user_id': user_id,
                'access_token': access_token,
                'allow_token_update': True,
                'max_retries': 3,
                'retry_delay': 5,
                'health_check_interval': 30,
                'order_rate_limit': 1.0
            }
            
            if not has_api_credentials:
                logger.error(f"❌ Missing Zerodha API credentials - cannot initialize")
                raise ValueError("Missing required Zerodha API credentials")
            
            zerodha = ZerodhaIntegration(zerodha_config)
            await zerodha.initialize()
            
            self.connections['zerodha'] = {
                'instance': zerodha,
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            
            logger.info("✅ Zerodha connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Zerodha: {e}")
            self.connections['zerodha'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': str(e)
            }
            return False
    
    async def _initialize_truedata_safe(self):
        """Check TrueData cache availability instead of connecting - FIXED"""
        try:
            # FIXED: Check existing TrueData cache instead of trying to connect
            # TrueData is already connected and flowing data in the main app
            from data.truedata_client import live_market_data, is_connected
            
            if live_market_data and len(live_market_data) > 0:
                logger.info(f"✅ TrueData cache available: {len(live_market_data)} symbols")
                self.connections['truedata'] = {
                    'instance': None,  # No direct instance - using cache
                    'status': ConnectionStatus.CONNECTED,
                    'cache_size': len(live_market_data),
                    'last_check': datetime.now()
                }
                return True
            else:
                logger.warning("⚠️ TrueData cache is empty - market data not available")
                self.connections['truedata'] = {
                    'instance': None,
                    'status': ConnectionStatus.ERROR,
                    'error': 'TrueData cache empty - check main app connection',
                    'last_check': datetime.now()
                }
                return False
            
        except Exception as e:
            logger.error(f"Failed to check TrueData cache: {e}")
            self.connections['truedata'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': f'TrueData cache check failed: {str(e)}',
                'last_check': datetime.now()
            }
            return False
    
    async def _initialize_database_safe(self):
        """Safely initialize database connection"""
        try:
            # Import the existing database manager
            from .database import db_manager
            
            if db_manager and db_manager.is_connected():
                self.connections['database'] = {
                    'instance': db_manager,
                    'status': ConnectionStatus.CONNECTED,
                    'last_check': datetime.now()
                }
                logger.info("Database connection initialized successfully")
                return True
            else:
                logger.warning("Database manager not available or not connected")
                self.connections['database'] = {
                    'instance': None,
                    'status': ConnectionStatus.ERROR,
                    'error': 'Database not connected'
                }
                return False
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.connections['database'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': str(e)
            }
            return False
    
    async def _initialize_redis_safe(self):
        """Safely initialize Redis connection"""
        try:
            import redis.asyncio as redis
            
            # Try different Redis URL sources
            redis_url = (
                os.getenv('REDIS_URL') or 
                os.getenv('REDIS_URI') or 
                self.config.get('REDIS_URL') or 
                'redis://localhost:6379'
            )
            
            redis_client = redis.from_url(redis_url)
            
            # Test connection
            await redis_client.ping()
            
            self.connections['redis'] = {
                'instance': redis_client,
                'status': ConnectionStatus.CONNECTED,
                'last_check': datetime.now()
            }
            
            logger.info("Redis connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            # ELIMINATED: Mock Redis connection that could mislead users
            
            # SAFETY: Return proper error instead of fake connection
            logger.error("SAFETY: Mock Redis connection ELIMINATED to prevent fake data caching")
            self.connections['redis'] = {
                'instance': None,
                'status': ConnectionStatus.ERROR,
                'error': f'SAFETY: Mock Redis disabled - real Redis required: {str(e)}'
            }
            return False
    
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
                await self._initialize_zerodha_safe()
            elif name == 'database':
                await self._initialize_database_safe()
            elif name == 'redis':
                await self._initialize_redis_safe()
            elif name == 'truedata':
                await self._initialize_truedata_safe()
                
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
    
    async def refresh_connections(self, force: bool = False):
        """Force refresh all connections - useful after authentication"""
        logger.info("Refreshing all connections...")
        
        if force:
            # Clear existing connections to force re-initialization
            self.connections.clear()
            self.reconnect_attempts.clear()
            logger.info("Cleared cached connections for fresh initialization")
        
        # Re-initialize all connections
        return await self.initialize_all_connections()
    
    async def refresh_zerodha_connection(self):
        """Force refresh only Zerodha connection - optimized for post-auth"""
        logger.info("Refreshing Zerodha connection...")
        
        # Clear only Zerodha connection
        if 'zerodha' in self.connections:
            del self.connections['zerodha']
        if 'zerodha' in self.reconnect_attempts:
            del self.reconnect_attempts['zerodha']
        
        # Re-initialize Zerodha connection
        return await self._initialize_zerodha_safe()
    
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

# Missing ResilientConnection base class for ResilientZerodhaConnection
from abc import ABC, abstractmethod

class ConnectionHealth:
    """Health status of a connection"""
    def __init__(self):
        self.state = ConnectionStatus.DISCONNECTED
        self.last_connected = None
        self.last_error = None
        self.reconnect_attempts = 0
        self.latency_ms = 0
        self.uptime_seconds = 0

class ResilientConnection(ABC):
    """Base class for resilient connections with automatic retry and recovery"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.health = ConnectionHealth()
        self._retry_attempts = 0
        self._max_retry_attempts = config.get("max_retry_attempts", 3)
        self._retry_delay = config.get("retry_delay", 1.0)
        self._connection_timeout = config.get("connection_timeout", 30.0)
        self._health_check_interval = config.get("health_check_interval", 30.0)
        self._last_health_check = None
        self._is_monitoring = False
        
    async def connect(self) -> bool:
        """Connect with retry logic"""
        self.health.state = ConnectionStatus.CONNECTING
        try:
            await self._do_connect()
            self.health.state = ConnectionStatus.CONNECTED
            self.health.last_connected = datetime.now()
            return True
        except Exception as e:
            self.health.state = ConnectionStatus.ERROR
            self.health.last_error = str(e)
            logger.error(f"Failed to connect to {self.name}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from service"""
        try:
            await self._do_disconnect()
            self.health.state = ConnectionStatus.DISCONNECTED
            logger.info(f"Disconnected from {self.name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")
    
    async def ensure_connected(self):
        """Ensure connection is established"""
        if self.health.state != ConnectionStatus.CONNECTED:
            await self.connect()
    
    async def execute(self, func, *args, **kwargs):
        """Execute function with retry on connection failure"""
        await self.ensure_connected()
        return await func(*args, **kwargs)
    
    def get_health(self) -> ConnectionHealth:
        """Get current health status"""
        return self.health
    
    @abstractmethod
    async def _do_connect(self):
        """Implement actual connection logic"""
        pass
    
    @abstractmethod
    async def _do_disconnect(self):
        """Implement actual disconnection logic"""
        pass
    
    @abstractmethod
    async def _check_connection_alive(self) -> bool:
        """Check if connection is still alive"""
        pass



# Missing ResilientConnection base class
from abc import ABC, abstractmethod

class ConnectionHealth:
    def __init__(self):
        self.state = ConnectionStatus.DISCONNECTED
        self.last_connected = None
        self.last_error = None
        self.reconnect_attempts = 0
        self.latency_ms = 0
        self.uptime_seconds = 0

class ResilientConnection(ABC):
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.health = ConnectionHealth()
        
    async def connect(self) -> bool:
        self.health.state = ConnectionStatus.CONNECTING
        try:
            await self._do_connect()
            self.health.state = ConnectionStatus.CONNECTED
            self.health.last_connected = datetime.now()
            return True
        except Exception as e:
            self.health.state = ConnectionStatus.ERROR
            self.health.last_error = str(e)
            return False
    
    async def disconnect(self):
        try:
            await self._do_disconnect()
            self.health.state = ConnectionStatus.DISCONNECTED
        except Exception as e:
            logger.error(f'Error disconnecting {self.name}: {e}')
    
    async def ensure_connected(self):
        if self.health.state != ConnectionStatus.CONNECTED:
            await self.connect()
    
    async def execute(self, func, *args, **kwargs):
        await self.ensure_connected()
        return await func(*args, **kwargs)
    
    def get_health(self) -> ConnectionHealth:
        return self.health
    
    @abstractmethod
    async def _do_connect(self):
        pass
    
    @abstractmethod
    async def _do_disconnect(self):
        pass
    
    @abstractmethod
    async def _check_connection_alive(self) -> bool:
        pass

# Global instance
connection_manager = None

def get_connection_manager():
    """Get the global connection manager instance"""
    global connection_manager
    if connection_manager is None:
        # Initialize with default config
        default_config = {
            'max_retry_attempts': 3,
            'retry_delay': 5,
            'connection_timeout': 30,
            'health_check_interval': 30
        }
        connection_manager = ConnectionManager(default_config)
    return connection_manager

async def initialize_connection_manager(config: dict = None):
    """Initialize the global connection manager"""
    global connection_manager
    if config is None:
        config = {
            'max_retry_attempts': 3,
            'retry_delay': 5,
            'connection_timeout': 30,
            'health_check_interval': 30
        }
    connection_manager = ConnectionManager(config)
    return connection_manager
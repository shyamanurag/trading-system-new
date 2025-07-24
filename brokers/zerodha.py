"""
Unified Zerodha Broker Integration
Handles trading operations with built-in resilience features
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time
import os
from enum import Enum

try:
    from kiteconnect import KiteConnect, KiteTicker
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("KiteConnect not available - running in mock mode")
    KiteConnect = None
    KiteTicker = None

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

class ZerodhaIntegration:
    """Unified Zerodha integration with built-in resilience features"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.user_id = config.get('user_id')
        self.access_token = config.get('access_token')
        self.pin = config.get('pin')
        
        # Configuration
        self.mock_mode = config.get('mock_mode', False)
        self.sandbox_mode = config.get('sandbox_mode', False)
        self.allow_token_update = config.get('allow_token_update', True)
        
        # Resilience configuration
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.health_check_interval = config.get('health_check_interval', 30)
        self.order_rate_limit = config.get('order_rate_limit', 1.0)  # orders per second
        self.ws_reconnect_delay = config.get('ws_reconnect_delay', 5)
        self.ws_max_reconnect_attempts = config.get('ws_max_reconnect_attempts', 10)
        
        # State tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.is_connected = False
        self.ticker_connected = False
        self.last_health_check = None
        self.last_error = None
        self.reconnect_attempts = 0
        
        # Rate limiting
        self.last_order_time = 0
        self.order_semaphore = asyncio.Semaphore(1)
        
        # WebSocket monitoring
        self.ws_reconnect_attempts = 0
        self.ws_last_reconnect = None
        self.ticker = None
        
        # Initialize KiteConnect for REAL trading
        if self.api_key and KiteConnect:
            self.kite = KiteConnect(api_key=self.api_key)
            logger.info("🔴 Zerodha initialized for REAL trading")
                
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                logger.info("✅ Zerodha access token set")
            else:
                logger.info("🔧 Zerodha initialized without token - awaiting frontend authentication")
        else:
            self.kite = None
            logger.warning("Zerodha API key not provided or KiteConnect not available")
            self.mock_mode = True  # Force mock mode if no API key
            
        # Start background monitoring
        asyncio.create_task(self._background_monitoring())
        
    async def initialize(self) -> bool:
        """Initialize the Zerodha connection with retries"""
        logger.info("🔄 Initializing Zerodha connection...")
        
        for attempt in range(self.max_retries):
            try:
                self.connection_state = ConnectionState.CONNECTING
                success = await self.connect()
                if success:
                    logger.info("✅ Zerodha connection initialized successfully")
                    return True
                else:
                    logger.warning(f"❌ Connection attempt {attempt + 1} failed")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        self.connection_state = ConnectionState.FAILED
        logger.error("❌ Zerodha connection initialization failed after all retries")
        return False

    async def connect(self) -> bool:
        """Connect to Zerodha API with health verification"""
        try:
            if not self.kite:
                logger.error("❌ Cannot connect: No valid API credentials")
                self.connection_state = ConnectionState.FAILED
                return False
            
            # Test the connection by fetching account info
            account_info = await self._async_api_call(self.kite.profile)
            if account_info:
                self.is_connected = True
                self.connection_state = ConnectionState.CONNECTED
                self.last_health_check = datetime.now()
                self.reconnect_attempts = 0
                
                # Initialize WebSocket
                await self._initialize_websocket()
                
                logger.info(f"✅ Connected to Zerodha - User: {account_info.get('user_name', 'Unknown')}")
                return True
            else:
                logger.error("❌ Connection test failed: No account info returned")
                self.connection_state = ConnectionState.FAILED
                return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Zerodha: {e}")
            self.is_connected = False
            self.connection_state = ConnectionState.FAILED
            self.last_error = str(e)
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Zerodha API"""
        try:
            self.is_connected = False
            self.ticker_connected = False
            self.connection_state = ConnectionState.DISCONNECTED
            
            if self.ticker:
                try:
                    self.ticker.close()
                except:
                    pass
                    
            logger.info("✅ Zerodha disconnected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error disconnecting from Zerodha: {e}")
            return False

    async def _health_check(self) -> bool:
        """Perform health check"""
        try:
            if not self.kite or not self.access_token:
                return False
                
            # Quick health check - fetch profile
            account_info = await self._async_api_call(self.kite.profile)
            health_ok = bool(account_info)
            
            if health_ok:
                self.last_health_check = datetime.now()
                if self.connection_state != ConnectionState.CONNECTED:
                    self.connection_state = ConnectionState.CONNECTED
                    self.is_connected = True
            else:
                self.is_connected = False
                if self.connection_state == ConnectionState.CONNECTED:
                    self.connection_state = ConnectionState.RECONNECTING
                    
            return health_ok
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.last_error = str(e)
            self.is_connected = False
            if self.connection_state == ConnectionState.CONNECTED:
                self.connection_state = ConnectionState.RECONNECTING
            return False

    async def _background_monitoring(self):
        """Background task for health monitoring and reconnection"""
        while True:
            try:
                # Health check
                if self.connection_state in [ConnectionState.CONNECTED, ConnectionState.RECONNECTING]:
                    health_ok = await self._health_check()
                    
                    if not health_ok and self.connection_state == ConnectionState.CONNECTED:
                        logger.warning("⚠️ Health check failed, attempting reconnection")
                        await self._attempt_reconnection()
                
                # WebSocket monitoring
                await self._monitor_websocket()
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _attempt_reconnection(self):
        """Attempt to reconnect with exponential backoff"""
        if self.connection_state == ConnectionState.RECONNECTING:
            return  # Already attempting
            
        self.connection_state = ConnectionState.RECONNECTING
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔄 Reconnection attempt {attempt + 1}/{self.max_retries}")
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
                success = await self.connect()
                if success:
                    logger.info("✅ Reconnection successful")
                    return
                    
            except Exception as e:
                logger.error(f"❌ Reconnection attempt {attempt + 1} failed: {e}")
        
        logger.error("❌ All reconnection attempts failed")
        self.connection_state = ConnectionState.FAILED

    async def _monitor_websocket(self):
        """Monitor WebSocket connection and handle reconnection"""
        try:
            if not self.ticker_connected and self.is_connected:
                current_time = time.time()
                if (self.ws_last_reconnect is None or 
                    current_time - self.ws_last_reconnect >= self.ws_reconnect_delay):
                    
                    if self.ws_reconnect_attempts < self.ws_max_reconnect_attempts:
                        logger.info(f"🔄 WebSocket reconnection attempt {self.ws_reconnect_attempts + 1}")
                        await self._initialize_websocket()
                        self.ws_reconnect_attempts += 1
                        self.ws_last_reconnect = current_time
                    else:
                        logger.error("❌ Max WebSocket reconnection attempts reached")
                        self.ws_reconnect_attempts = 0
            elif self.ticker_connected:
                self.ws_reconnect_attempts = 0
                
        except Exception as e:
            logger.error(f"Error in WebSocket monitoring: {e}")

    async def update_access_token(self, access_token: str):
        """Update access token after frontend authentication"""
        try:
            if self.kite and access_token:
                self.access_token = access_token
                self.kite.set_access_token(access_token)
                logger.info(f"✅ Zerodha access token updated: {access_token[:10]}...")
                
                # Verify connection
                success = await self.connect()
                if success:
                    # Automatically reinitialize WebSocket after token update
                    await self._initialize_websocket()
                    return True
                else:
                    logger.error("❌ Token update failed - connection verification failed")
                    return False
            else:
                logger.error("❌ Cannot update token - KiteConnect not initialized or token invalid")
                return False
        except Exception as e:
            logger.error(f"❌ Error updating Zerodha access token: {e}")
            return False

    async def place_order(self, order_params: Dict) -> Optional[str]:
        """Place order with built-in rate limiting and retry logic"""
        async with self.order_semaphore:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_order_time < self.order_rate_limit:
                wait_time = self.order_rate_limit - (current_time - self.last_order_time)
                logger.info(f"⏱️ Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    result = await self._place_order_impl(order_params)
                    if result:
                        self.last_order_time = time.time()
                        return result
                except Exception as e:
                    logger.error(f"❌ Order attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
            
            logger.error("❌ Order failed after all retries")
            return None

    async def _place_order_impl(self, order_params: Dict) -> Optional[str]:
        """Internal order placement implementation"""
        try:
            # Validate order parameters
            if not self._validate_order_params(order_params):
                logger.error("❌ Order validation failed")
                return None
            
            # Check connection
            if not self.kite or not self.access_token or not self.is_connected:
                logger.error("❌ Zerodha order rejected: No valid connection")
                return None
            
            # Map signal parameters to Zerodha API format
            action = self._get_transaction_type(order_params)
            symbol = order_params.get('symbol', '')
            quantity = int(order_params.get('quantity', 0))
            

            # Build Zerodha order parameters
            zerodha_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': self._get_exchange_for_symbol(symbol),
                'tradingsymbol': self._map_symbol_to_exchange(symbol),
                'transaction_type': action,
                'quantity': quantity,
                'product': order_params.get('product', self.kite.PRODUCT_CNC),  # CRITICAL FIX: Use CNC instead of MIS for SPECIALITY stocks
                'order_type': order_params.get('order_type', self.kite.ORDER_TYPE_MARKET),
                'validity': order_params.get('validity', self.kite.VALIDITY_DAY),
                'tag': order_params.get('tag', 'ALGO_TRADE')
            }
            
            # Add price for limit orders
            if zerodha_params['order_type'] != self.kite.ORDER_TYPE_MARKET:
                price = order_params.get('price') or order_params.get('entry_price')
                if price:
                    zerodha_params['price'] = float(price)
            
            # Add trigger price for stop loss orders
            trigger_price = order_params.get('trigger_price') or order_params.get('stop_loss')
            if trigger_price:
                zerodha_params['trigger_price'] = float(trigger_price)
            
            if self.sandbox_mode:
                logger.info(f"🧪 SANDBOX MODE: Placing order via real API (no NSE execution): {symbol} {action} {quantity}")
            else:
                logger.info(f"🔴 REAL MODE: Placing LIVE order: {symbol} {action} {quantity}")
                logger.warning(f"⚠️ REAL MONEY TRADE: This will use actual funds!")
            
            # Place the REAL order
            order_response = await self._async_api_call(
                self.kite.place_order,
                **zerodha_params
            )
            
            # CRITICAL FIX: Handle both string order ID and dict response formats
            if order_response:
                # Check if response is a direct order ID string
                if isinstance(order_response, str) and order_response.strip():
                    order_id = order_response.strip()
                    logger.info(f"✅ REAL Zerodha order placed successfully: {order_id}")
                    return order_id
                # Check if response is a dict with order_id key
                elif isinstance(order_response, dict) and 'order_id' in order_response:
                    order_id = order_response['order_id']
                    logger.info(f"✅ REAL Zerodha order placed successfully: {order_id}")
                    return order_id
                else:
                    logger.error(f"❌ Unexpected order response format: {order_response}")
                    return None
            else:
                logger.error(f"❌ Zerodha order failed: No response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing REAL order: {e}")
            raise  # Re-raise for retry logic

    async def _async_api_call(self, func, *args, **kwargs):
        """Execute synchronous API call in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def _get_transaction_type(self, order_params: Dict) -> str:
        """Extract transaction type from order parameters"""
        action = order_params.get('action', '').upper()
        if not action:
            action = order_params.get('transaction_type', '').upper()
        if not action:
            action = order_params.get('side', '').upper()
        if not action:
            action = 'BUY'  # Default to BUY if no action specified
        return action

    def _validate_order_params(self, order_params: Dict) -> bool:
        """Validate order parameters"""
        # Check for symbol
        if 'symbol' not in order_params:
            logger.error("Missing required field: symbol")
            return False
        
        # Check for quantity
        if 'quantity' not in order_params:
            logger.error("Missing required field: quantity")
            return False
            
        quantity = order_params['quantity']
        if quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}")
            return False
        
        # Check for transaction type
        action = self._get_transaction_type(order_params)
        if action not in ['BUY', 'SELL']:
            logger.error(f"Invalid transaction type: {action}")
            return False
        
        return True

    def _map_symbol_to_exchange(self, symbol: str) -> str:
        """Map internal symbol to exchange format"""
        if symbol.endswith('-I'):
            return symbol.replace('-I', '')  # NIFTY-I -> NIFTY
        return symbol

    def _get_exchange_for_symbol(self, symbol: str) -> str:
        """Get appropriate exchange for symbol"""
        if symbol.endswith('-I'):
            return 'NSE'  # Indices
        return 'NSE'  # Default to NSE for equities

    async def _initialize_websocket(self):
        """Initialize WebSocket connection for real-time data"""
        try:
            if self.mock_mode:
                self.ticker_connected = True
                logger.info("✅ Mock WebSocket connection established")
            else:
                if not KiteTicker or not self.api_key or not self.access_token:
                    logger.warning("⚠️ WebSocket unavailable - missing KiteTicker or credentials")
                    return
                    
                self.ticker = KiteTicker(self.api_key, self.access_token)
                self.ticker.on_ticks = self._on_ticks
                self.ticker.on_connect = self._on_connect
                self.ticker.on_close = self._on_close
                self.ticker.on_error = self._on_error
                
                # Connect in threaded mode
                self.ticker.connect(threaded=True)
                self.ticker_connected = True
                logger.info("✅ Real WebSocket connection established")
        except Exception as e:
            logger.error(f"❌ WebSocket initialization failed: {e}")
            self.ticker_connected = False

    def _on_ticks(self, ws, ticks):
        """Handle incoming WebSocket ticks"""
        logger.debug(f"📊 Received {len(ticks)} ticks")
        # Add tick processing logic here

    def _on_connect(self, ws, response):
        """Handle WebSocket connection"""
        logger.info("✅ WebSocket connected successfully")
        self.ticker_connected = True
        self.ws_reconnect_attempts = 0

    def _on_close(self, ws, code, reason):
        """Handle WebSocket disconnection"""
        logger.warning(f"⚠️ WebSocket disconnected: {code} - {reason}")
        self.ticker_connected = False

    def _on_error(self, ws, code, reason):
        """Handle WebSocket error"""
        logger.error(f"❌ WebSocket error: {code} - {reason}")
        self.ticker_connected = False

    # API Methods with retry logic
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status with retry"""
        for attempt in range(self.max_retries):
            try:
                if not self.kite or not self.access_token:
                    return None
                return await self._async_api_call(self.kite.order_history, order_id)
            except Exception as e:
                logger.error(f"❌ Get order status attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return None

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order with retry"""
        for attempt in range(self.max_retries):
            try:
                if not self.kite or not self.access_token:
                    return False
                result = await self._async_api_call(self.kite.cancel_order, 'regular', order_id)
                return bool(result)
            except Exception as e:
                logger.error(f"❌ Cancel order attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return False

    async def modify_order(self, order_id: str, order_params: Dict) -> Dict:
        """Modify order with retry"""
        for attempt in range(self.max_retries):
            try:
                if not self.kite or not self.access_token:
                    return {}
                # Implement modify order logic
                result = await self._async_api_call(self.kite.modify_order, 'regular', order_id, **order_params)
                return result or {}
            except Exception as e:
                logger.error(f"❌ Modify order attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {}

    async def get_positions(self) -> Dict:
        """Get positions with retry"""
        for attempt in range(self.max_retries):
            try:
                if self.mock_mode or not self.kite:
                    return {'net': [], 'day': []}
                return await self._async_api_call(self.kite.positions)
            except Exception as e:
                logger.error(f"❌ Get positions attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'net': [], 'day': []}

    async def get_holdings(self) -> Dict:
        """Get holdings with retry"""
        for attempt in range(self.max_retries):
            try:
                if self.mock_mode or not self.kite:
                    return {'holdings': []}
                return await self._async_api_call(self.kite.holdings)
            except Exception as e:
                logger.error(f"❌ Get holdings attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'holdings': []}

    async def get_margins(self) -> Dict:
        """Get margins with retry"""
        for attempt in range(self.max_retries):
            try:
                if self.mock_mode or not self.kite:
                    return {'equity': {'available': {'cash': 100000}}}
                return await self._async_api_call(self.kite.margins)
            except Exception as e:
                logger.error(f"❌ Get margins attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'equity': {'available': {'cash': 0}}}

    async def get_orders(self) -> List[Dict]:
        """Get orders with retry - CRITICAL for trade sync"""
        for attempt in range(self.max_retries):
            try:
                if self.mock_mode or not self.kite:
                    # Return mock orders for testing
                    return []
                return await self._async_api_call(self.kite.orders)
            except Exception as e:
                logger.error(f"❌ Get orders attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return []

    async def get_account_info(self) -> Dict:
        """Get account info with retry"""
        for attempt in range(self.max_retries):
            try:
                if not self.is_connected or not self.kite:
                    return {}
                
                if self.mock_mode:
                    return {
                        'user_id': self.user_id or 'MOCK_USER',
                        'broker': 'Zerodha',
                        'connection_status': 'connected'
                    }
                else:
                    profile = await self._async_api_call(self.kite.profile)
                    if profile:
                        return {
                            'user_id': profile.get('user_id', self.user_id),
                            'user_name': profile.get('user_name', ''),
                            'email': profile.get('email', ''),
                            'broker': 'Zerodha',
                            'exchanges': profile.get('exchanges', []),
                            'products': profile.get('products', ['CNC', 'MIS', 'NRML']),
                            'order_types': profile.get('order_types', ['MARKET', 'LIMIT', 'SL', 'SL-M']),
                            'last_updated': datetime.now().isoformat(),
                            'connection_status': 'connected'
                        }
                    return {}
            except Exception as e:
                logger.error(f"❌ Get account info attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {}

    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'name': 'zerodha',
            'state': self.connection_state.value,
            'is_connected': self.is_connected,
            'mock_mode': self.mock_mode,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_error': self.last_error,
            'reconnect_attempts': self.reconnect_attempts,
            'ws_connected': self.ticker_connected,
            'ws_reconnect_attempts': self.ws_reconnect_attempts,
            'order_rate_limit': self.order_rate_limit,
            'last_order_time': self.last_order_time
        }

    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        # Simple check - market open 9:15 AM to 3:30 PM on weekdays
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        
        return market_open <= now <= market_close
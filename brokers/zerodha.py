"""
Unified Zerodha Broker Integration
Handles trading operations with built-in resilience features
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
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
        self.kite = None
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.access_token = config.get('access_token')
        self.user_id = config.get('user_id')
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2
        
        # Rate limiting (ONLY add what's needed for order_semaphore error)
        self.order_semaphore = asyncio.Semaphore(1)
        self.last_order_time = 0
        self.order_rate_limit = 1.0  # Used in place_order method
        
        # WebSocket attributes (only if used in the code)
        self.ticker = None
        self.health_check_interval = 30
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        
        # Connection state tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.is_connected = False
        self.ticker_connected = False
        self.last_health_check = None
        self.last_error = None
        self.reconnect_attempts = 0
        self.ws_reconnect_attempts = 0
        self.ws_last_reconnect = None
        
        # 🚨 FIX: Add instruments caching to prevent rate limiting
        self._instruments_cache = {}
        self._cache_expiry = {}
        self._cache_duration = 600  # 10 minutes cache
        
        # Separate cache for different exchanges
        self._nfo_instruments = None
        self._nse_instruments = None
        self._instruments_last_fetched = {}
        self._instruments_cache_duration = 3600  # 1 hour cache for instruments
        
        # Circuit breaker for symbol validation to prevent rate limiting
        self._validation_circuit_breaker = {
            'failure_count': 0,
            'last_failure_time': 0,
            'circuit_open': False,
            'reset_timeout': 300  # 5 minutes
        }
        
        logger.info(f"🔴 Zerodha initialized for REAL trading")
        
        if self.api_key and self.access_token:
            logger.info("✅ Zerodha access token set")
            self._initialize_kite()
        else:
            logger.warning("⚠️ Zerodha credentials incomplete")

    def _initialize_kite(self):
        """Initialize KiteConnect instance"""
        try:
            from kiteconnect import KiteConnect
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            logger.info("✅ KiteConnect instance initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize KiteConnect: {e}")
            self.kite = None

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
        """Place order implementation with retries and proper error handling"""
        symbol = order_params.get('symbol', '')
        
        # 🔍 CRITICAL VALIDATION: Check if options symbol exists before placing order
        # FIXED: Only validate symbols that actually end with CE or PE (not just contain them)
        if symbol.endswith('CE') or symbol.endswith('PE'):
            logger.info(f"🔍 VALIDATING OPTIONS SYMBOL: {symbol}")
            symbol_exists = await self.validate_options_symbol(symbol)
            if not symbol_exists:
                logger.error(f"❌ SYMBOL VALIDATION FAILED: {symbol} does not exist in Zerodha NFO")
                return None
        
        for attempt in range(self.max_retries):
            try:
                if not self.kite:
                    logger.error("❌ Zerodha order rejected: KiteConnect not initialized")
                    return None
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
                # symbol = order_params.get('symbol', '') # This line is removed as symbol is now validated
                quantity = int(order_params.get('quantity', 0))
                

                # Build Zerodha order parameters
                # 🚨 CRITICAL FIX: Use LIMIT orders for stock options to avoid Zerodha blocking
                default_order_type = self.kite.ORDER_TYPE_MARKET
                if symbol and (symbol.endswith('CE') or symbol.endswith('PE')) and not any(index in symbol for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']):
                    default_order_type = self.kite.ORDER_TYPE_LIMIT
                    logger.info(f"🔧 Auto-switching to LIMIT order for stock option: {symbol}")
                
                zerodha_params = {
                    'variety': self.kite.VARIETY_REGULAR,
                    'exchange': self._get_exchange_for_symbol(symbol),
                    'tradingsymbol': self._map_symbol_to_exchange(symbol),
                    'transaction_type': action,
                    'quantity': quantity,
                    'product': self._get_product_type_for_symbol(symbol, order_params),  # FIXED: Dynamic product type
                    'order_type': order_params.get('order_type', default_order_type),
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
                error_msg = str(e)
                logger.error(f"❌ Error placing REAL order: {error_msg}")
                return None

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

    def _get_product_type_for_symbol(self, symbol: str, order_params: Dict) -> str:
        """Get appropriate product type for symbol - FIXED for short selling"""
        # Check if user explicitly specified product type
        if 'product' in order_params:
            return order_params['product']
        
        # Get transaction type to determine if it's a SELL order
        action = self._get_transaction_type(order_params)
        
        # 🔧 CRITICAL FIX: NFO options require NRML, not CNC
        if 'CE' in symbol or 'PE' in symbol:
            return 'NRML'  # Options must use NRML
        else:
            # 🚨 INTRADAY ONLY FIX: Use MIS for ALL equity orders (BUY and SELL)
            return 'MIS'  # Margin Intraday Square-off for ALL orders - auto square-off at 3:30 PM

    def _get_exchange_for_symbol(self, symbol: str) -> str:
        """Get appropriate exchange for symbol - FIXED for options"""
        # 🔧 CRITICAL FIX: Options contracts (CE/PE) trade on NFO, not NSE
        if 'CE' in symbol or 'PE' in symbol:
            return 'NFO'  # Options contracts
        elif symbol.endswith('-I'):
            return 'NSE'  # Indices on NSE
        else:
            return 'NSE'  # Default to NSE for equities

    async def _initialize_websocket(self):
        """Initialize WebSocket connection for real-time data"""
        try:
            if not self.kite:
                logger.warning("⚠️ WebSocket unavailable - KiteConnect not initialized")
                return
                
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
        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
            self._initialize_kite()
            if not self.kite:
                logger.error("❌ Zerodha kite client reinitialize failed")
                return {'net': [], 'day': []}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting positions from Zerodha (attempt {attempt + 1})")
                result = await self._async_api_call(self.kite.positions)
                logger.info(f"✅ Got positions: {len(result.get('net', []))} net, {len(result.get('day', []))} day")
                return result
            except Exception as e:
                logger.error(f"❌ Get positions attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'net': [], 'day': []}

    async def get_holdings(self) -> Dict:
        """Get holdings with retry"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting holdings from Zerodha (attempt {attempt + 1})")
                result = await self._async_api_call(self.kite.holdings)
                logger.info(f"✅ Got holdings: {len(result)} holdings")
                return {'holdings': result}
            except Exception as e:
                logger.error(f"❌ Get holdings attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'holdings': []}

    async def get_margins(self) -> Dict:
        """Get margins with retry"""
        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
            self._initialize_kite()
            if not self.kite:
                logger.error("❌ Zerodha kite client reinitialize failed")
                return {'equity': {'available': {'cash': 0}}}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting margins from Zerodha (attempt {attempt + 1})")
                result = await self._async_api_call(self.kite.margins)
                logger.info(f"✅ Got margins: ₹{result.get('equity', {}).get('available', {}).get('cash', 0)}")
                return result
            except Exception as e:
                logger.error(f"❌ Get margins attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'equity': {'available': {'cash': 0}}}

    async def get_orders(self) -> List[Dict]:
        """Get orders with retry - CRITICAL for trade sync"""
        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
            self._initialize_kite()
            if not self.kite:
                logger.error("❌ Zerodha kite client reinitialize failed")
                return []
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting orders from Zerodha (attempt {attempt + 1})")
                result = await self._async_api_call(self.kite.orders)
                logger.info(f"✅ Got {len(result)} orders")
                return result
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

    async def get_instruments(self, exchange: str = 'NFO') -> List[Dict]:
        """Get instruments with intelligent caching to prevent rate limiting"""
        try:
            # Check if we have cached data that's still valid
            cache_key = f"{exchange}_instruments"
            now = time.time()
            
            if (cache_key in self._instruments_last_fetched and 
                now - self._instruments_last_fetched[cache_key] < self._instruments_cache_duration):
                
                # Return cached data
                if exchange == 'NFO' and self._nfo_instruments:
                    logger.info(f"✅ Using cached {exchange} instruments ({len(self._nfo_instruments)} instruments)")
                    return self._nfo_instruments
                elif exchange == 'NSE' and self._nse_instruments:
                    logger.info(f"✅ Using cached {exchange} instruments ({len(self._nse_instruments)} instruments)")
                    return self._nse_instruments
            
            # Cache miss or expired - fetch fresh data with rate limit protection
            logger.info(f"🔄 Fetching fresh {exchange} instruments from Zerodha...")
            
            # Add delay to prevent rate limiting
            if hasattr(self, '_last_instruments_call'):
                time_since_last = now - self._last_instruments_call
                if time_since_last < 2:  # Minimum 2 seconds between calls
                    await asyncio.sleep(2 - time_since_last)
            
            self._last_instruments_call = now
            
            instruments = await self._async_api_call(self.kite.instruments, exchange)
            
            if instruments:
                # Cache the results
                self._instruments_last_fetched[cache_key] = now
                if exchange == 'NFO':
                    self._nfo_instruments = instruments
                elif exchange == 'NSE':
                    self._nse_instruments = instruments
                
                logger.info(f"✅ Cached {len(instruments)} {exchange} instruments for 1 hour")
                return instruments
            else:
                logger.warning(f"⚠️ No instruments returned from {exchange}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Get instruments attempt failed: {e}")
            
            # Return cached data if available, even if expired
            if exchange == 'NFO' and self._nfo_instruments:
                logger.info(f"🔄 Falling back to cached {exchange} data due to error")
                return self._nfo_instruments
            elif exchange == 'NSE' and self._nse_instruments:
                logger.info(f"🔄 Falling back to cached {exchange} data due to error") 
                return self._nse_instruments
            
            return []

    def _get_mock_instruments_data(self) -> List[Dict]:
        """Generate mock instruments data for testing"""
        today = datetime.now().date()
        instruments = []
        
        # Generate sample options for POWERGRID with various expiries
        underlying = "POWERGRID"
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # Generate next 8 weekly expiries
        current_date = today
        for weeks_ahead in range(8):
            # Find next Thursday
            days_ahead = (3 - current_date.weekday()) % 7  # Thursday = 3
            if days_ahead == 0 and current_date == today:
                days_ahead = 7
                
            thursday = current_date + timedelta(days=days_ahead)
            expiry_str = f"{thursday.day:02d}{month_names[thursday.month - 1]}{str(thursday.year)[-2:]}"
            
            # Generate options for different strikes around ATM (300)
            strikes = [250, 275, 300, 325, 350]
            
            for strike in strikes:
                for option_type in ['CE', 'PE']:
                    symbol = f"{underlying}{expiry_str}{strike}{option_type}"
                    
                    instruments.append({
                        'instrument_token': f"1234{weeks_ahead}{strike}{ord(option_type[0])}",
                        'exchange_token': f"567{weeks_ahead}{strike}",
                        'tradingsymbol': symbol,
                        'name': underlying,
                        'last_price': 50.0 if option_type == 'CE' else 25.0,
                        'expiry': thursday.strftime('%Y-%m-%d'),
                        'strike': float(strike),
                        'tick_size': 0.05,
                        'lot_size': 1,
                        'instrument_type': option_type,
                        'segment': 'NFO-OPT',
                        'exchange': 'NFO'
                    })
            
            current_date = thursday + timedelta(days=1)
        
        logger.info(f"🧪 Generated {len(instruments)} mock instruments for {underlying}")
        return instruments

    async def get_available_expiries_for_symbol(self, underlying_symbol: str, exchange: str = "NFO") -> List[Dict]:
        """
        Get available expiry dates for a specific underlying symbol
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Get all instruments for the exchange
            instruments = await self.get_instruments(exchange)
            
            if not instruments:
                logger.warning(f"⚠️ No instruments data available for {underlying_symbol}")
                return []
            
            # Filter options for the specific underlying
            options_contracts = []
            for instrument in instruments:
                trading_symbol = instrument.get('tradingsymbol', '')
                instrument_type = instrument.get('instrument_type', '')
                
                # Check if it's an option for our underlying
                if (underlying_symbol.upper() in trading_symbol.upper() and 
                    instrument_type in ['CE', 'PE'] and
                    instrument.get('expiry')):
                    
                    options_contracts.append(instrument)
            
            if not options_contracts:
                logger.warning(f"⚠️ No options contracts found for {underlying_symbol}")
                return []
            
            # Extract unique expiry dates
            expiry_dates = set()
            for contract in options_contracts:
                expiry_value = contract.get('expiry')
                if expiry_value:
                    try:
                        # Handle both string and datetime.date objects
                        if isinstance(expiry_value, str):
                            # Parse expiry date string (format: YYYY-MM-DD)
                            expiry_date = datetime.strptime(expiry_value, '%Y-%m-%d').date()
                        elif hasattr(expiry_value, 'date'):
                            # If it's a datetime object, get the date part
                            expiry_date = expiry_value.date()
                        elif isinstance(expiry_value, date):
                            # If it's already a date object, use directly
                            expiry_date = expiry_value
                        else:
                            # Try to convert to string first, then parse
                            expiry_date = datetime.strptime(str(expiry_value), '%Y-%m-%d').date()
                        
                        expiry_dates.add(expiry_date)
                    except (ValueError, AttributeError) as e:
                        logger.debug(f"⚠️ Could not parse expiry '{expiry_value}' for contract: {e}")
                        continue
            
            # Convert to list and sort
            sorted_expiries = sorted(list(expiry_dates))
            
            # Format for strategy use
            formatted_expiries = []
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            for expiry_date in sorted_expiries:
                # Format for Zerodha: 31JUL25
                formatted = f"{expiry_date.day:02d}{month_names[expiry_date.month - 1]}{str(expiry_date.year)[-2:]}"
                
                # Determine if it's monthly (last Thursday of month)
                next_week = expiry_date + timedelta(days=7)
                is_monthly = next_week.month != expiry_date.month
                
                formatted_expiries.append({
                    'date': expiry_date,
                    'formatted': formatted,
                    'is_weekly': True,
                    'is_monthly': is_monthly
                })
            
            logger.info(f"📅 Found {len(formatted_expiries)} expiries for {underlying_symbol}: {[e['formatted'] for e in formatted_expiries[:3]]}...")
            return formatted_expiries
            
        except Exception as e:
            logger.error(f"❌ Error getting expiries for {underlying_symbol}: {e}")
            return []

    async def validate_options_symbol(self, options_symbol: str) -> bool:
        """Validate if options symbol exists in Zerodha instruments with circuit breaker for rate limiting"""
        try:
            # Circuit breaker check - if too many failures, temporarily skip validation
            now = time.time()
            if self._validation_circuit_breaker['circuit_open']:
                if now - self._validation_circuit_breaker['last_failure_time'] > self._validation_circuit_breaker['reset_timeout']:
                    # Reset circuit breaker
                    self._validation_circuit_breaker['circuit_open'] = False
                    self._validation_circuit_breaker['failure_count'] = 0
                    logger.info("🔄 Circuit breaker reset - resuming symbol validation")
                else:
                    # Circuit is still open - skip validation to prevent rate limiting
                    logger.warning(f"⚠️ Circuit breaker OPEN - skipping validation for {options_symbol} to prevent rate limiting")
                    return True  # Assume valid to allow trading
            
            # Get all NFO instruments with caching
            instruments = await self.get_instruments("NFO")
            
            if not instruments:
                # Increment failure count
                self._validation_circuit_breaker['failure_count'] += 1
                self._validation_circuit_breaker['last_failure_time'] = now
                
                # Open circuit breaker if too many failures
                if self._validation_circuit_breaker['failure_count'] >= 3:
                    self._validation_circuit_breaker['circuit_open'] = True
                    logger.warning("🚨 Circuit breaker OPENED - too many instrument fetch failures")
                
                logger.warning("⚠️ No NFO instruments available for validation")
                return True  # Assume valid to allow trading when validation fails
            
            # 🔍 DEBUG: Log BANKNIFTY specific symbols for format analysis
            logger.info(f"🔍 DEBUG: Searching for BANKNIFTY options symbols in {len(instruments)} NFO instruments")
            banknifty_symbols = []
            nifty_symbols = []
            options_count = 0
            
            for instrument in instruments:
                trading_symbol = instrument.get('tradingsymbol', '')
                
                # Collect BANKNIFTY examples
                if 'BANKNIFTY' in trading_symbol and ('CE' in trading_symbol or 'PE' in trading_symbol):
                    banknifty_symbols.append(f"{trading_symbol} (Strike: {instrument.get('strike')}, Expiry: {instrument.get('expiry')})")
                
                # Collect NIFTY examples for comparison
                if 'NIFTY' in trading_symbol and 'BANKNIFTY' not in trading_symbol and ('CE' in trading_symbol or 'PE' in trading_symbol):
                    nifty_symbols.append(f"{trading_symbol} (Strike: {instrument.get('strike')}, Expiry: {instrument.get('expiry')})")
                
                options_count += 1
                if len(banknifty_symbols) >= 10 and len(nifty_symbols) >= 5:
                    break
            
            # Log actual Zerodha symbol formats
            logger.info(f"🔍 DEBUG: Found {len(banknifty_symbols)} BANKNIFTY options:")
            for i, symbol in enumerate(banknifty_symbols[:10]):
                logger.info(f"   BANKNIFTY #{i+1}: {symbol}")
            
            logger.info(f"🔍 DEBUG: Found {len(nifty_symbols)} NIFTY options for comparison:")
            for i, symbol in enumerate(nifty_symbols[:5]):
                logger.info(f"   NIFTY #{i+1}: {symbol}")
            
            logger.info(f"🔍 DEBUG: Looking for our symbol: {options_symbol}")
            
            # Check if our options symbol exists
            for instrument in instruments:
                trading_symbol = instrument.get('tradingsymbol', '')
                if trading_symbol == options_symbol:
                    logger.info(f"✅ VALIDATED: {options_symbol} exists in Zerodha NFO")
                    logger.info(f"   Details: Strike={instrument.get('strike')}, Expiry={instrument.get('expiry')}")
                    return True
            
            # If not found, log similar symbols for debugging
            logger.error(f"❌ SYMBOL NOT FOUND: {options_symbol}")
            
            # Extract base symbol to find similar ones - FIXED for dynamic expiry detection
            import re
            # Extract symbol name (everything before the date pattern)
            date_match = re.search(r'(\d{1,2}[A-Z]{3})', options_symbol)
            if date_match:
                date_start = date_match.start()
                base_symbol = options_symbol[:date_start]
            else:
                # Fallback: extract symbol before strike (assume CE/PE is at the end)
                ce_pe_match = re.search(r'(CE|PE)$', options_symbol)
                if ce_pe_match:
                    # Work backwards to find the symbol part
                    symbol_part = re.sub(r'\d+[A-Z]{3}\d*(CE|PE)$', '', options_symbol)
                    base_symbol = symbol_part if symbol_part else options_symbol[:6]
                else:
                    base_symbol = options_symbol[:6]  # Conservative fallback
            
            logger.info(f"🔍 Extracted base symbol: '{base_symbol}' from '{options_symbol}'")
            similar_symbols = []
            
            for instrument in instruments:
                trading_symbol = instrument.get('tradingsymbol', '')
                if base_symbol in trading_symbol and ('CE' in trading_symbol or 'PE' in trading_symbol):
                    similar_symbols.append(f"{trading_symbol} (Strike: {instrument.get('strike')})")
                    if len(similar_symbols) >= 10:
                        break
            
            if similar_symbols:
                logger.warning(f"⚠️ Found {len(similar_symbols)} similar symbols for {base_symbol}:")
                for i, sym in enumerate(similar_symbols[:10]):
                    logger.warning(f"   Similar #{i+1}: {sym}")
            else:
                logger.warning(f"⚠️ NO SIMILAR SYMBOLS FOUND for {base_symbol}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating options symbol {options_symbol}: {e}")
            return False
    
    async def get_options_ltp(self, options_symbol: str) -> Optional[float]:
        """Get real-time LTP for options symbol from Zerodha"""
        try:
            if not self.kite or not self.is_connected:
                logger.warning("⚠️ Zerodha not connected - cannot get options LTP")
                return None
            
            # Get quotes for the options symbol
            exchange = self._get_exchange_for_symbol(options_symbol)
            full_symbol = f"{exchange}:{options_symbol}"
            
            quotes = self.kite.quote([full_symbol])
            
            if quotes and full_symbol in quotes:
                quote_data = quotes[full_symbol]
                ltp = quote_data.get('last_price', 0)
                
                if ltp and ltp > 0:
                    logger.info(f"✅ ZERODHA LTP: {options_symbol} = ₹{ltp}")
                    return float(ltp)
            
            logger.warning(f"⚠️ No LTP data from Zerodha for {options_symbol}")

            # Fallback 1: Resolve instrument token from cached NFO instruments and fetch via token
            try:
                # Ensure NFO instruments are cached
                if self._nfo_instruments is None:
                    await self.get_instruments('NFO')
                instruments = self._nfo_instruments or []

                instrument_token = None
                for inst in instruments:
                    if inst.get('tradingsymbol') == options_symbol:
                        instrument_token = inst.get('instrument_token') or inst.get('token')
                        break

                if instrument_token:
                    # Fetch LTP by instrument token
                    ltp_resp = await self._async_api_call(self.kite.ltp, [instrument_token])
                    if ltp_resp:
                        # Response can be keyed by instrument token; extract first entry
                        for _, data in ltp_resp.items():
                            token_ltp = data.get('last_price') or data.get('last_traded_price') or 0
                            if token_ltp and token_ltp > 0:
                                logger.info(f"✅ ZERODHA LTP (token): {options_symbol} = ₹{token_ltp}")
                                return float(token_ltp)
            except Exception as fallback_err:
                logger.warning(f"⚠️ Token-based LTP fallback failed for {options_symbol}: {fallback_err}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha LTP for {options_symbol}: {e}")
            return None
    
    async def get_options_volume(self, options_symbol: str) -> Optional[int]:
        """Get real-time volume for options symbol from Zerodha"""
        try:
            if not self.kite or not self.is_connected:
                logger.warning("⚠️ Zerodha not connected - cannot get options volume")
                return None
            
            # Get quotes for the options symbol
            exchange = self._get_exchange_for_symbol(options_symbol)
            full_symbol = f"{exchange}:{options_symbol}"
            
            quotes = self.kite.quote([full_symbol])
            
            if quotes and full_symbol in quotes:
                quote_data = quotes[full_symbol]
                volume = quote_data.get('volume', 0)
                
                if volume:
                    logger.info(f"✅ ZERODHA VOLUME: {options_symbol} = {volume:,}")
                    return int(volume)
            
            logger.warning(f"⚠️ No volume data from Zerodha for {options_symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha volume for {options_symbol}: {e}")
            return None
    
    async def get_multiple_options_quotes(self, options_symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time quotes for multiple options symbols from Zerodha"""
        try:
            if not self.kite or not self.is_connected:
                logger.warning("⚠️ Zerodha not connected - cannot get options quotes")
                return {}
            
            if not options_symbols:
                return {}
            
            # Prepare full symbols for Zerodha API
            full_symbols = []
            symbol_mapping = {}
            
            for symbol in options_symbols:
                exchange = self._get_exchange_for_symbol(symbol)
                full_symbol = f"{exchange}:{symbol}"
                full_symbols.append(full_symbol)
                symbol_mapping[full_symbol] = symbol
            
            # Get quotes in batch
            quotes = self.kite.quote(full_symbols)
            
            result = {}
            if quotes:
                for full_symbol, quote_data in quotes.items():
                    original_symbol = symbol_mapping.get(full_symbol, full_symbol)
                    
                    ltp = quote_data.get('last_price', 0)
                    volume = quote_data.get('volume', 0)
                    oi = quote_data.get('oi', 0)  # Open Interest
                    
                    result[original_symbol] = {
                        'ltp': float(ltp) if ltp else 0,
                        'volume': int(volume) if volume else 0,
                        'oi': int(oi) if oi else 0,
                        'bid': quote_data.get('depth', {}).get('buy', [{}])[0].get('price', 0),
                        'ask': quote_data.get('depth', {}).get('sell', [{}])[0].get('price', 0)
                    }
                
                logger.info(f"✅ ZERODHA QUOTES: Retrieved data for {len(result)} options symbols")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha quotes for options: {e}")
            return {}

    async def get_nearby_atm_options_ltp(self, underlying_symbol: str, atm_strike: int, expiry: str, option_type: str = 'CE', band: int = 2) -> Dict[str, float]:
        """Rate-limited batch fetch of nearby strikes to find first tradable LTP.
        Returns mapping of symbol->ltp for those with non-zero LTP.
        """
        try:
            # Build candidate symbols within +/- band strikes
            candidates = []
            for k in range(-band, band + 1):
                strike = atm_strike + (k * 50)
                if strike <= 0:
                    continue
                sym = f"{underlying_symbol}{expiry}{strike}{option_type}"
                candidates.append(sym)

            # Respect simple client-side rate limit: batch in one call
            quotes = await self.get_multiple_options_quotes(candidates)
            tradables = {sym: data.get('ltp', 0) for sym, data in quotes.items() if data.get('ltp', 0) > 0}
            return tradables
        except Exception as e:
            logger.error(f"❌ Error in nearby ATM options LTP fetch: {e}")
            return {}
        
    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'name': 'zerodha',
            'state': self.connection_state.value,
            'is_connected': self.is_connected,
            'mock_mode': False, # REMOVED mock_mode
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
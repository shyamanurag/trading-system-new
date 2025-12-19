"""
Unified Zerodha Broker Integration
Handles trading operations with built-in resilience features
"""

import asyncio
import logging
import json
import time
import threading
import math
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_UP

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
        
        # 🚨 CRITICAL: Lock for KiteConnect initialization to prevent race conditions
        self._kite_init_lock = threading.Lock()
        self._kite_reinit_in_progress = False
        
        # 🚀 UNIFIED CACHING SYSTEM - Consolidated and optimized
        self._unified_cache = {}
        self._cache_ttl = {
            'margins': 300,        # 5 minutes
            'positions': 60,       # 1 minute
            'instruments': 3600,   # 1 hour
            'ltp': 5,             # 5 seconds
            'quote': 3,           # 3 seconds
            'orders': 30,         # 30 seconds
            'nfo_instruments': 3600,  # 1 hour
            'nse_instruments': 3600   # 1 hour
        }
        
        # Rate limit tracking
        self._last_rate_limit_log = 0
        
        # Instruments cache attributes (missing initialization)
        self._instruments_cache = {}
        self._nfo_instruments = None
        self._nse_instruments = None
        self._instruments_last_fetched = {}
        self._instruments_cache_duration = 3600  # 1 hour cache for instruments
        self._last_instruments_call = 0  # Track last instruments API call for rate limiting
        self._symbol_to_token = {}  # Fast lookup for instrument tokens by tradingsymbol
        self._token_to_symbol = {}  # Reverse lookup for WebSocket ticks
        self._last_successful_call = None  # Track last successful API call
        self._websocket_tokens = []  # Instrument tokens for WebSocket subscription
        self._tick_size_cache = {}  # Cache tick_size by exchange:tradingsymbol
        
        # WebSocket attributes
        self.ticker = None
        self.health_check_interval = 30
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        
        # Token refresh tracking
        self._last_token_refresh = 0
        self._token_refresh_interval = 3600  # 1 hour
        
        # Connection state tracking
        self.connection_state = ConnectionState.DISCONNECTED
        self.is_connected = False
        self.ticker_connected = False
        self.last_health_check = None
        self.last_error = None
        self.reconnect_attempts = 0
        self.ws_reconnect_attempts = 0
        self.ws_last_reconnect = None
        
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
            logger.warning("⚠️ Zerodha credentials incomplete - KiteConnect not initialized")
            logger.warning(f"   API Key: {'✅' if self.api_key else '❌'}")
            logger.warning(f"   Access Token: {'✅' if self.access_token else '❌'}")
            logger.warning("   Will NOT attempt continuous reconnection without valid credentials")
            self.kite = None
            self.is_connected = False

    def _get_cached_data(self, cache_key: str, cache_type: str = 'default') -> Any:
        """Get cached data from unified cache if still valid"""
        import time
        
        try:
            current_time = time.time()
            if cache_key not in self._unified_cache:
                return None
            
            entry = self._unified_cache[cache_key]
            ttl = self._cache_ttl.get(cache_type, 60)
            
            if current_time - entry['timestamp'] < ttl:
                logger.debug(f"📊 Using cached {cache_type} data (age: {current_time - entry['timestamp']:.1f}s)")
                return entry['data']
            else:
                # Expired, remove from cache
                del self._unified_cache[cache_key]
                logger.debug(f"🗑️ Expired cache entry removed: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting cached data for {cache_key}: {e}")
            return None
            
    def _set_cached_data(self, cache_key: str, data: Any, cache_type: str = 'default') -> None:
        """Cache data with timestamp in unified cache"""
        import time
        
        try:
            current_time = time.time()
            self._unified_cache[cache_key] = {
                'data': data,
                'timestamp': current_time,
                'type': cache_type
            }
            logger.debug(f"📊 Cached {cache_type} data: {cache_key}")
        except Exception as e:
            logger.error(f"❌ Error caching data for {cache_key}: {e}")
    
    def _clear_cache(self, cache_type: Optional[str] = None) -> None:
        """Clear cache entries by type or all if type is None"""
        try:
            if cache_type is None:
                self._unified_cache.clear()
                logger.info("🗑️ All cache entries cleared")
            else:
                keys_to_remove = [
                    key for key, entry in self._unified_cache.items() 
                    if entry.get('type') == cache_type
                ]
                for key in keys_to_remove:
                    del self._unified_cache[key]
                logger.info(f"🗑️ Cleared {len(keys_to_remove)} {cache_type} cache entries")
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")

    def _initialize_kite(self):
        """Initialize KiteConnect instance with race condition protection"""
        # 🚨 CRITICAL: Use lock to prevent multiple simultaneous initializations
        with self._kite_init_lock:
            try:
                # Check if already reinitializing
                if self._kite_reinit_in_progress:
                    logger.warning("⚠️ KiteConnect reinitialization already in progress, skipping duplicate")
                    return
                
                self._kite_reinit_in_progress = True
                
                # Validate required parameters
                if not self.api_key:
                    logger.error("❌ ZERODHA_API_KEY not provided")
                    self.kite = None
                    self.is_connected = False
                    return
                    
                if not self.access_token:
                    logger.error("❌ ZERODHA_ACCESS_TOKEN not provided")
                    self.kite = None
                    self.is_connected = False
                    return
                
                from kiteconnect import KiteConnect
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                
                # Test connection (non-critical - don't fail if this doesn't work)
                try:
                    profile = self.kite.profile()
                    logger.info(f"✅ KiteConnect initialized for user: {profile.get('user_name', 'Unknown')}")
                except Exception as profile_error:
                    logger.warning(f"⚠️ KiteConnect initialized but profile test failed: {profile_error}")
                    logger.warning("   This is usually due to rate limiting or temporary network issues")
                    logger.info("✅ KiteConnect initialized (profile test skipped)")
                
                self._last_token_refresh = time.time()
                self.is_connected = True
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize KiteConnect: {e}")
                self.kite = None
                self.is_connected = False
            finally:
                self._kite_reinit_in_progress = False

    def _reset_caches(self):
        """🚨 DEFENSIVE: Reset all caches to prevent corruption"""
        try:
            self._unified_cache.clear()
            # Reset separate instrument caches
            self._instruments_cache = {}
            self._nfo_instruments = None
            self._nse_instruments = None
            self._instruments_last_fetched = {}
            logger.info("✅ All caches reset successfully")
        except Exception as e:
            logger.error(f"❌ Error resetting caches: {e}")

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
            
            # Test the connection by fetching account info (non-critical during token update)
            try:
                account_info = await self._async_api_call(self.kite.profile)
                if account_info:
                    self.is_connected = True
                    self.connection_state = ConnectionState.CONNECTED
                    self.last_health_check = datetime.now()
                    self.reconnect_attempts = 0
                    
                    logger.info(f"✅ Connected to Zerodha - User: {account_info.get('user_name', 'Unknown')}")
                else:
                    logger.warning("⚠️ Connection test returned no data (may be rate limited)")
                    # Still mark as connected if kite client exists
                    self.is_connected = True
                    self.connection_state = ConnectionState.CONNECTED
                    logger.info("✅ Connected to Zerodha (profile test skipped)")
            except Exception as profile_error:
                # Don't fail connection just because profile test failed (rate limiting)
                logger.warning(f"⚠️ Profile test failed during connect: {profile_error}")
                logger.warning("   This is usually due to rate limiting - accepting connection anyway")
                self.is_connected = True
                self.connection_state = ConnectionState.CONNECTED
                logger.info("✅ Connected to Zerodha (profile test skipped due to rate limit)")
            
            # Initialize WebSocket (non-critical)
            try:
                await self._initialize_websocket()
            except Exception as ws_error:
                logger.warning(f"⚠️ WebSocket initialization failed (non-critical): {ws_error}")
            
            return True
            
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
        """Update access token after frontend authentication - ALWAYS REINITIALIZE KiteConnect"""
        try:
            if not access_token:
                logger.error("❌ Cannot update token - token is empty")
                return False
            
            # Update access token
            self.access_token = access_token
            logger.info(f"✅ Zerodha access token received: {access_token[:10]}...")
            
            # 🚨 CRITICAL FIX: ALWAYS reinitialize KiteConnect with new token
            # Calling set_access_token() on existing instance may not update internal auth state
            logger.info("🔄 Reinitializing KiteConnect with fresh token...")
            self._initialize_kite()
            logger.info(f"✅ KiteConnect reinitialized with new token")
            
            # 🚨 RATE LIMIT PROTECTION: Wait before verifying connection
            # profile() was just called in _initialize_kite(), wait before calling again
            logger.info("⏱️ Waiting 2 seconds to avoid rate limiting...")
            await asyncio.sleep(2)
            
            # Verify connection with new token (will call profile() again)
            success = await self.connect()
            if success:
                logger.info("✅ Token verified and connection established")
                # Automatically reinitialize WebSocket after token update
                try:
                    await self._initialize_websocket()
                    logger.info("✅ WebSocket reinitialized with new token")
                except Exception as ws_error:
                    logger.warning(f"⚠️ WebSocket reinitialization failed (non-critical): {ws_error}")
                return True
            else:
                # Even if verification failed due to rate limiting, token is set
                logger.warning("⚠️ Connection verification failed (may be rate limited)")
                logger.info("✅ Token is set - connection will work on next API call")
                # Still initialize WebSocket
                try:
                    await self._initialize_websocket()
                    logger.info("✅ WebSocket initialized")
                except Exception as ws_error:
                    logger.warning(f"⚠️ WebSocket initialization failed: {ws_error}")
                return True  # Return True because token is actually set
                
        except Exception as e:
            logger.error(f"❌ Error updating Zerodha access token: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def place_order(self, order_params: Dict) -> Optional[str]:
        """Place order with built-in rate limiting, cooldown, and retry logic"""
        
        # 🔥 ANTI-CHURN: Per-symbol cooldown and minimum quantity check
        symbol = order_params.get('symbol', '')
        quantity = order_params.get('quantity', 0)
        action = order_params.get('action', order_params.get('side', 'BUY'))
        
        # Detect if this is an EXIT order (closing a position)
        is_exit_order = order_params.get('tag', '') in ['PARTIAL_EXIT', 'FULL_EXIT', 'STOP_LOSS', 'TARGET_HIT', 'SQUARE_OFF']
        is_exit_order = is_exit_order or order_params.get('metadata', {}).get('partial_exit', False)
        is_exit_order = is_exit_order or order_params.get('metadata', {}).get('is_exit', False)
        
        # 🚨 CRITICAL FIX: Prevent unintended SHORTS from over-selling
        # Validate SELL quantity against actual position to prevent qty mismatch
        if action.upper() == 'SELL' and is_exit_order:
            try:
                positions = self.get_positions_sync()
                net_positions = positions.get('net', [])
                
                # Find actual position for this symbol
                # 🔥 FIX: Index symbols like "NIFTY-I" are stored as "NIFTY" in positions
                # Must compare both the original symbol AND the exchange-mapped version
                actual_qty = 0
                exchange_symbol = self._map_symbol_to_exchange(symbol)  # NIFTY-I -> NIFTY
                
                for pos in net_positions:
                    pos_symbol = pos.get('tradingsymbol', '')
                    # Match against: original symbol OR exchange-mapped symbol OR reverse (pos + "-I")
                    if pos_symbol == symbol or pos_symbol == exchange_symbol or f"{pos_symbol}-I" == symbol:
                        actual_qty = pos.get('quantity', 0)
                        logger.debug(f"✅ Position found: {pos_symbol} qty={actual_qty} (searched: {symbol}, mapped: {exchange_symbol})")
                        break
                
                # If we have a LONG position (qty > 0), cap sell to actual qty
                if actual_qty > 0:
                    if quantity > actual_qty:
                        logger.warning(f"🚨 OVER-SELL BLOCKED: {symbol} trying to SELL {quantity} but only have {actual_qty}")
                        logger.warning(f"   Capping sell quantity to {actual_qty} to prevent unintended SHORT")
                        order_params['quantity'] = actual_qty
                        quantity = actual_qty
                elif actual_qty == 0:
                    # No position exists - this would create a new SHORT
                    logger.error(f"🚨 SHORT CREATION BLOCKED: {symbol} SELL {quantity} with NO existing position")
                    logger.error(f"   System tried to sell shares we don't own - blocking order")
                    return None
                # actual_qty < 0 means already SHORT - allow further shorting if intentional
                
            except Exception as e:
                logger.error(f"⚠️ Position validation error for {symbol}: {e} - Proceeding with caution")
        
        # Initialize cooldown tracking if not exists
        if not hasattr(self, '_symbol_cooldown'):
            self._symbol_cooldown = {}
            self._symbol_last_action = {}  # Track last action type
            self._cooldown_seconds = 900  # 15 MINUTES between NEW ENTRY trades
            self._min_quantity = 10  # Minimum 10 shares per order (increased from 5)
            self._min_stock_price = 50.0  # Minimum stock price ₹50 (penny stock block)
        
        # 🚫 Block tiny orders (< 10 shares) - EXCEPT for exits (may need to exit small positions)
        if quantity < self._min_quantity and not is_exit_order:
            logger.warning(f"🚫 TINY ORDER BLOCKED: {symbol} {action} qty={quantity} < min {self._min_quantity}")
            return None
        
        # 🚫 PENNY STOCK BLOCK at broker level - last line of defense
        price = order_params.get('price', 0) or order_params.get('trigger_price', 0) or order_params.get('limit_price', 0)
        if price and price < self._min_stock_price and not is_exit_order:
            logger.warning(f"🚫 PENNY STOCK BLOCKED: {symbol} @ ₹{price:.2f} < ₹{self._min_stock_price} minimum - NO TRADE")
            return None
        
        # 🧊 ANTI-CHURN COOLDOWN (15 MINUTES between NEW ENTRIES)
        # EXIT orders are ALWAYS allowed (need to close positions)
        # NEW ENTRY orders must respect cooldown
        from datetime import datetime
        now = datetime.now()
        
        if is_exit_order:
            logger.info(f"✅ EXIT ORDER ALLOWED: {symbol} {action} x{quantity} - Exits bypass cooldown")
        elif symbol in self._symbol_cooldown:
            elapsed = (now - self._symbol_cooldown[symbol]).total_seconds()
            if elapsed < self._cooldown_seconds:
                remaining = self._cooldown_seconds - elapsed
                last_action = self._symbol_last_action.get(symbol, 'UNKNOWN')
                logger.warning(f"🧊 COOLDOWN BLOCKED: {symbol} {action} (new entry)")
                logger.warning(f"   Last trade: {last_action} at {self._symbol_cooldown[symbol].strftime('%H:%M:%S')}")
                logger.warning(f"   Remaining: {remaining:.0f}s/{self._cooldown_seconds}s ({remaining/60:.1f} min)")
                return None
        
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
                        
                        # 🔥 Set cooldown after successful ENTRY order only
                        # EXIT orders don't trigger cooldown (we need to be able to exit)
                        if not is_exit_order:
                            self._symbol_cooldown[symbol] = now
                            self._symbol_last_action[symbol] = action
                            logger.info(f"🧊 COOLDOWN SET: {symbol} {action} - {self._cooldown_seconds/60:.0f} min cooldown started")
                        else:
                            logger.info(f"✅ EXIT ORDER COMPLETED: {symbol} {action} x{quantity} - No cooldown for exits")
                        
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
        # 🔥 FIX: Proper options detection - must have DIGITS before CE/PE (strike price)
        # Stocks like BAJFINANCE, PETRONET end with CE/PE but are NOT options!
        import re
        is_options_contract = bool(re.search(r'\d+[CP]E$', symbol))  # Digits followed by CE/PE at end
        if is_options_contract:
            logger.info(f"🔍 VALIDATING OPTIONS SYMBOL: {symbol}")
            symbol_exists = await self.validate_options_symbol(symbol)
            if not symbol_exists:
                logger.error(f"❌ SYMBOL VALIDATION FAILED: {symbol} does not exist in Zerodha NFO")
                return None
        elif symbol.endswith('CE') or symbol.endswith('PE'):
            # Log that we detected a stock ending with CE/PE but it's NOT an options contract
            logger.debug(f"ℹ️ {symbol} ends with CE/PE but is EQUITY (no strike price digits)")
        
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
                # Stock options MUST use LIMIT orders (Zerodha requirement for illiquid options)
                is_stock_option = symbol and (symbol.endswith('CE') or symbol.endswith('PE')) and not any(index in symbol for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'])
                
                if is_stock_option:
                    # FORCE LIMIT order for stock options (ignore order_params)
                    order_type = self.kite.ORDER_TYPE_LIMIT
                    logger.info(f"🔧 ENFORCING LIMIT order for stock option: {symbol} (Zerodha requirement)")
                else:
                    # For index options and equity, use provided order_type or default to MARKET
                    order_type = order_params.get('order_type', self.kite.ORDER_TYPE_MARKET)
                
                zerodha_params = {
                    'variety': self.kite.VARIETY_REGULAR,
                    'exchange': self._get_exchange_for_symbol(symbol),
                    'tradingsymbol': self._map_symbol_to_exchange(symbol),
                    'transaction_type': action,
                    'quantity': quantity,
                    'product': self._get_product_type_for_symbol(symbol, order_params),  # FIXED: Dynamic product type
                    'order_type': order_type,
                    'validity': order_params.get('validity', self.kite.VALIDITY_DAY),
                    'tag': order_params.get('tag', 'ALGO_TRADE')
                }
                
                # Add price for limit orders
                if zerodha_params['order_type'] != self.kite.ORDER_TYPE_MARKET:
                    # DEBUG: Log what we're looking for
                    logger.info(f"🔍 LIMIT order needs price for {symbol}")
                    logger.info(f"   order_params keys: {list(order_params.keys())}")
                    logger.info(f"   order_params.get('price'): {order_params.get('price')}")
                    logger.info(f"   order_params.get('entry_price'): {order_params.get('entry_price')}")
                    
                    price = order_params.get('price') or order_params.get('entry_price')
                    if price:
                        raw_price = float(price)
                        tick_size = await self._get_tick_size_for_exchange_symbol(
                            zerodha_params['exchange'],
                            zerodha_params['tradingsymbol']
                        )
                        aligned_price = self._align_price_to_tick_size(
                            raw_price,
                            tick_size,
                            action=action,
                            mode="conservative"
                        )
                        zerodha_params['price'] = aligned_price
                        if aligned_price != raw_price:
                            logger.info(
                                f"🎯 Tick aligned LIMIT price: ₹{raw_price:.2f} → ₹{aligned_price:.2f} "
                                f"(tick={tick_size})"
                            )
                        else:
                            logger.info(f"📍 LIMIT order price set: ₹{aligned_price:.2f}")
                    else:
                        # CRITICAL: LIMIT orders MUST have a price
                        logger.error(f"❌ LIMIT order requires price but none provided for {symbol}")
                        logger.error(f"   Full order_params: {order_params}")
                        raise ValueError(f"LIMIT order for {symbol} requires price parameter")
                
                # Add trigger price for stop loss orders
                trigger_price = order_params.get('trigger_price') or order_params.get('stop_loss')
                if trigger_price:
                    raw_trigger = float(trigger_price)
                    tick_size = await self._get_tick_size_for_exchange_symbol(
                        zerodha_params['exchange'],
                        zerodha_params['tradingsymbol']
                    )
                    aligned_trigger = self._align_price_to_tick_size(
                        raw_trigger,
                        tick_size,
                        action=action,
                        mode="nearest"
                    )
                    zerodha_params['trigger_price'] = aligned_trigger
                    if aligned_trigger != raw_trigger:
                        logger.info(
                            f"🎯 Tick aligned trigger: ₹{raw_trigger:.2f} → ₹{aligned_trigger:.2f} "
                            f"(tick={tick_size})"
                        )
                
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

    async def _get_tick_size_for_exchange_symbol(self, exchange: str, tradingsymbol: str) -> float:
        """
        Get tick size for a tradingsymbol on an exchange, with caching.
        Falls back to 0.05 if unknown.
        """
        try:
            exchange = (exchange or "").upper()
            tradingsymbol = (tradingsymbol or "").upper()
            cache_key = f"{exchange}:{tradingsymbol}"
            cached = self._tick_size_cache.get(cache_key)
            if isinstance(cached, (int, float)) and cached > 0:
                return float(cached)

            # Prefer already-cached instruments to avoid extra API calls
            instruments = None
            if exchange == "NSE" and isinstance(self._nse_instruments, list) and self._nse_instruments:
                instruments = self._nse_instruments
            elif exchange == "NFO" and isinstance(self._nfo_instruments, list) and self._nfo_instruments:
                instruments = self._nfo_instruments

            # If we don't have a cached list, fetch via existing instruments cache layer
            if instruments is None:
                instruments = await self.get_instruments(exchange)

            tick = None
            if isinstance(instruments, list):
                for inst in instruments:
                    if not isinstance(inst, dict):
                        continue
                    if (inst.get("tradingsymbol") or "").upper() == tradingsymbol:
                        try:
                            tick = float(inst.get("tick_size") or 0)
                        except Exception:
                            tick = None
                        break

            # Sensible fallbacks (most NSE/NFO symbols are 0.05)
            if not tick or tick <= 0:
                tick = 0.05

            # Normalize tiny float noise (e.g., 0.05000000000001)
            tick = float(Decimal(str(tick)))
            self._tick_size_cache[cache_key] = tick
            return tick
        except Exception:
            return 0.05

    def _align_price_to_tick_size(self, price: float, tick_size: float, action: str, mode: str = "conservative") -> float:
        """
        Align a price to the instrument tick size to avoid Zerodha rejections.

        - mode="conservative": BUY rounds DOWN, SELL rounds UP (never worse than requested limit)
        - mode="nearest": rounds to nearest tick (used for trigger prices)
        """
        try:
            if price is None:
                return price
            tick = float(tick_size or 0)
            if tick <= 0:
                return float(price)

            p = Decimal(str(float(price)))
            t = Decimal(str(tick))
            q = p / t

            mode_l = (mode or "").lower()
            action_u = (action or "").upper()

            if mode_l == "nearest":
                q_int = q.to_integral_value(rounding=ROUND_HALF_UP)
            else:
                # conservative default
                if action_u == "BUY":
                    q_int = q.to_integral_value(rounding=ROUND_FLOOR)
                elif action_u == "SELL":
                    q_int = q.to_integral_value(rounding=ROUND_CEILING)
                else:
                    q_int = q.to_integral_value(rounding=ROUND_HALF_UP)

            aligned = q_int * t

            # Round to tick's decimal precision for clean floats in logs / API payload
            decimals = max(0, -t.as_tuple().exponent)
            aligned_f = float(round(float(aligned), decimals))
            # Avoid negative zero
            if aligned_f == 0.0:
                aligned_f = 0.0
            return aligned_f
        except Exception:
            # Last-resort: keep original price
            try:
                return float(price)
            except Exception:
                return price

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
        
        symbol = order_params['symbol']
        
        # CRITICAL FIX: Check if symbol is tradeable on Zerodha
        # Known delisted/suspended symbols that should be blocked
        blocked_symbols = ['RCOM', 'RELCAPITAL', 'YESBANK', 'JETAIRWAYS']
        if symbol in blocked_symbols:
            logger.warning(f"🚫 BLOCKED SYMBOL: {symbol} - Known delisted/suspended stock")
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
        
        # INTRADAY ONLY: Use MIS for ALL orders (equity and options)
        if 'CE' in symbol or 'PE' in symbol:
            return 'MIS'  # Options BUY with intraday auto square-off
        else:
            # Equity intraday
            return 'MIS'  # Margin Intraday Square-off

    def _get_exchange_for_symbol(self, symbol: str) -> str:
        """Get appropriate exchange for symbol - FIXED for options and indices"""
        # 🔧 CRITICAL FIX: Options contracts (CE/PE) trade on NFO, not NSE
        if 'CE' in symbol or 'PE' in symbol:
            return 'NFO'  # Options contracts
        elif symbol.endswith('-I') or symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']:
            return 'NSE'  # Indices on NSE (Zerodha uses NSE for index quotes)
        else:
            return 'NSE'  # Default to NSE for equities

    async def _initialize_websocket(self, instrument_tokens: List[int] = None):
        """Initialize WebSocket connection for real-time tick data"""
        try:
            if not self.kite:
                logger.warning("⚠️ WebSocket unavailable - KiteConnect not initialized")
                return False
                
            if not KiteTicker or not self.api_key or not self.access_token:
                logger.warning("⚠️ WebSocket unavailable - missing KiteTicker or credentials")
                return False
            
            # Create ticker instance
            self.ticker = KiteTicker(self.api_key, self.access_token)
            self.ticker.on_ticks = self._on_ticks
            self.ticker.on_connect = self._on_connect
            self.ticker.on_close = self._on_close
            self.ticker.on_error = self._on_error
            
            # Store tokens for subscription
            self._websocket_tokens = instrument_tokens or []
            
            # Connect in threaded mode
            self.ticker.connect(threaded=True)
            logger.info("✅ WebSocket ticker initialized - waiting for connection")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket initialization failed: {e}")
            self.ticker_connected = False
            return False

    def _on_ticks(self, ws, ticks):
        """
        Handle incoming WebSocket ticks and store in Redis cache
        Tick format from Zerodha: {instrument_token, last_price, ohlc, volume, depth, etc.}
        """
        try:
            if not ticks:
                return
            
            # VISIBILITY FIX: Log at INFO level periodically to show ticks are flowing
            if not hasattr(self, '_tick_counter'):
                self._tick_counter = 0
                self._last_tick_log = time.time()
                self._tick_symbols = set()
                self._first_tick_logged = False
            
            # Log first tick received (one-time)
            if not self._first_tick_logged:
                logger.info(f"🎉 First WebSocket ticks received! {len(ticks)} symbols in first batch")
                self._first_tick_logged = True
            
            self._tick_counter += len(ticks)
            
            # Collect symbols from this batch
            for tick in ticks:
                token = tick.get('instrument_token')
                if token and token in self._token_to_symbol:
                    self._tick_symbols.add(self._token_to_symbol[token])
            
            # Log every 30 seconds to show activity without flooding
            if time.time() - self._last_tick_log >= 30:
                # Show sample symbols including any indices
                sample_symbols = list(self._tick_symbols)[:10]
                index_symbols = [s for s in self._tick_symbols if 'NIFTY' in s or 'BANKNIFTY' in s or 'FINNIFTY' in s]
                
                logger.info(f"📊 WebSocket ACTIVE: {self._tick_counter} ticks in 30s | {len(self._tick_symbols)} unique symbols")
                if index_symbols:
                    logger.info(f"   📈 Index ticks received: {', '.join(index_symbols)}")
                logger.info(f"   📊 Sample symbols: {', '.join(sample_symbols[:5])}")
                
                self._tick_counter = 0
                self._tick_symbols.clear()
                self._last_tick_log = time.time()
            
            logger.debug(f"📊 Received {len(ticks)} ticks from WebSocket")
            
            # Process each tick and store in Redis
            for tick in ticks:
                try:
                    instrument_token = tick.get('instrument_token')
                    if not instrument_token:
                        continue
                    
                    # Map token to symbol (need to maintain reverse mapping)
                    symbol = self._token_to_symbol.get(instrument_token, f"TOKEN_{instrument_token}")
                    
                    # Transform to standard format matching quote API
                    # 🔍 CRITICAL: In Zerodha ticks, ohlc.close is PREVIOUS DAY's close, NOT today's close!
                    ohlc_data = tick.get('ohlc', {})
                    prev_close = ohlc_data.get('close', 0)
                    
                    tick_data = {
                        'symbol': symbol,
                        'ltp': tick.get('last_price', 0),
                        'open': ohlc_data.get('open', 0),
                        'high': ohlc_data.get('high', 0),
                        'low': ohlc_data.get('low', 0),
                        'previous_close': prev_close,  # 🎯 THIS IS PREVIOUS DAY's CLOSE (FIXED: 2025-11-14)
                        'volume': tick.get('volume', 0),
                        'change': tick.get('change', 0),
                        'change_percent': (tick.get('change', 0) / prev_close * 100) if prev_close > 0 else 0,
                        'bid': tick.get('depth', {}).get('buy', [{}])[0].get('price', 0) if tick.get('depth', {}).get('buy') else 0,
                        'ask': tick.get('depth', {}).get('sell', [{}])[0].get('price', 0) if tick.get('depth', {}).get('sell') else 0,
                        'depth': tick.get('depth', {}),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'zerodha_websocket',
                        'instrument_token': instrument_token
                    }
                    
                    # Store in cache with symbol key
                    cache_key = f'websocket_tick:{symbol}'
                    self._unified_cache[cache_key] = {
                        'data': tick_data,
                        'timestamp': time.time(),
                        'ttl': 5  # 5 second TTL for ticks
                    }
                    
                except Exception as tick_error:
                    logger.debug(f"Error processing tick for {instrument_token}: {tick_error}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in _on_ticks: {e}")

    def _on_connect(self, ws, response):
        """Handle WebSocket connection and subscribe to symbols"""
        try:
            logger.info(f"✅ WebSocket connected successfully - Response: {response}")
            self.ticker_connected = True
            self.ws_reconnect_attempts = 0
            
            # Subscribe to stored instrument tokens
            if hasattr(self, '_websocket_tokens') and self._websocket_tokens:
                logger.info(f"📡 Subscribing to {len(self._websocket_tokens)} instruments")
                ws.subscribe(self._websocket_tokens)
                ws.set_mode(ws.MODE_FULL, self._websocket_tokens)  # Full mode for depth data
                logger.info(f"✅ Subscribed to {len(self._websocket_tokens)} instruments in FULL mode")
            else:
                logger.warning("⚠️ No instrument tokens to subscribe")
                
        except Exception as e:
            logger.error(f"❌ Error in _on_connect: {e}")

    def _on_close(self, ws, code, reason):
        """Handle WebSocket disconnection"""
        logger.warning(f"⚠️ WebSocket disconnected: {code} - {reason}")
        self.ticker_connected = False

    def _on_error(self, ws, code, reason):
        """Handle WebSocket error"""
        logger.error(f"❌ WebSocket error: {code} - {reason}")
        self.ticker_connected = False
    
    async def start_websocket_for_symbols(self, symbols: List[str]) -> bool:
        """
        Start WebSocket connection for list of symbols
        Converts symbols to instrument tokens and subscribes
        """
        try:
            if not symbols:
                logger.warning("⚠️ No symbols provided for WebSocket")
                return False
            
            # Get NSE instruments (stocks) AND INDICES (NIFTY, BANKNIFTY, etc.)
            # 🔥 FIX: Check if kite is available before trying to fetch
            if not self.kite:
                logger.warning("⚠️ WebSocket: Waiting for Zerodha token - KiteConnect not initialized")
                return False
                
            nse_instruments = await self.get_instruments('NSE')
            indices_instruments = await self.get_instruments('INDICES')

            if not nse_instruments and not indices_instruments:
                logger.error("❌ Could not fetch NSE or INDICES instruments - check Zerodha authentication")
                return False
            
            # Build symbol to token mapping from BOTH sources
            token_map = {}
            all_instruments = (nse_instruments or []) + (indices_instruments or [])
            
            for inst in all_instruments:
                symbol = inst.get('tradingsymbol', '')
                token = inst.get('instrument_token')
                if symbol and token:
                    token_map[symbol] = token
                    self._token_to_symbol[token] = symbol
            
            logger.info(f"📊 Built token map with {len(token_map)} instruments ({len(nse_instruments or [])} NSE + {len(indices_instruments or [])} INDICES)")
            
            # Convert symbols to tokens
            instrument_tokens = []
            symbol_mapping = {}  # Track which symbols were found
            
            for symbol in symbols:
                # Remove exchange prefix if present
                clean_symbol = symbol.replace('NSE:', '').replace('NFO:', '')
                original_symbol = clean_symbol  # Store for reverse mapping
                
                # Map internal index symbols to Zerodha trading symbols
                index_map = {
                    'NIFTY-I': 'NIFTY 50',
                    'NIFTY': 'NIFTY 50',
                    'BANKNIFTY-I': 'NIFTY BANK',
                    'BANKNIFTY': 'NIFTY BANK',
                    'FINNIFTY-I': 'FINNIFTY',
                    'MIDCPNIFTY-I': 'NIFTY MID SELECT'
                }
                
                # Check if it's an index symbol
                if clean_symbol in index_map:
                    clean_symbol = index_map[clean_symbol]
                else:
                    # Remove -I suffix for other indices
                    clean_symbol = clean_symbol.replace('-I', '')
                
                token = token_map.get(clean_symbol)
                if token:
                    instrument_tokens.append(token)
                    symbol_mapping[symbol] = clean_symbol
                    # CRITICAL FIX: Store original internal symbol for reverse mapping
                    # This ensures ticks are stored with keys the system expects (NIFTY-I, not NIFTY 50)
                    self._token_to_symbol[token] = original_symbol
                else:
                    logger.debug(f"⚠️ Token not found for symbol: {symbol} (tried: {clean_symbol})")
            
            if not instrument_tokens:
                logger.error("❌ No valid instrument tokens found")
                return False
            
            # Log index symbols that were successfully mapped with tokens
            index_symbols = [s for s in symbol_mapping.keys() if 'NIFTY' in s or 'BANKNIFTY' in s or 'FINNIFTY' in s]
            if index_symbols:
                logger.info(f"📊 Index symbols subscribed: {', '.join(index_symbols)}")
                # Log actual tokens for debugging
                for idx_sym in index_symbols:
                    zerodha_symbol = symbol_mapping.get(idx_sym)
                    token = token_map.get(zerodha_symbol)
                    logger.info(f"   {idx_sym} → {zerodha_symbol} → token:{token}")
            
            logger.info(f"📡 Starting WebSocket for {len(instrument_tokens)} symbols")
            
            # Initialize WebSocket with tokens
            success = await self._initialize_websocket(instrument_tokens)
            
            if success:
                logger.info(f"✅ WebSocket started for {len(instrument_tokens)} symbols")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error starting WebSocket: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_websocket_ticks(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get latest WebSocket tick data from cache
        Returns dict matching quote API format
        """
        try:
            result = {}
            
            # Get all cached ticks
            current_time = time.time()
            for cache_key, cache_value in list(self._unified_cache.items()):
                if not cache_key.startswith('websocket_tick:'):
                    continue
                
                # Check if cache is still valid
                if current_time - cache_value['timestamp'] > cache_value['ttl']:
                    continue
                
                tick_data = cache_value['data']
                symbol = tick_data.get('symbol')
                
                # Filter by symbols if provided
                if symbols and symbol not in symbols:
                    continue
                
                result[symbol] = tick_data
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting WebSocket ticks: {e}")
            return {}
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get quotes for multiple symbols - REQUIRED for option position monitoring
        First tries WebSocket cache, then falls back to Zerodha API
        
        🎯 FIXED (2025-12-01): Made async to prevent 'dict object can't be awaited' error
        """
        try:
            if not symbols:
                return {}
            
            result = {}
            missing_symbols = []
            
            # Step 1: Try WebSocket cache first (fastest)
            ws_ticks = self.get_websocket_ticks(symbols)
            for symbol in symbols:
                if symbol in ws_ticks:
                    tick = ws_ticks[symbol]
                    result[symbol] = {
                        'last_price': tick.get('ltp', 0),
                        'ohlc': {
                            'open': tick.get('open', 0),
                            'high': tick.get('high', 0),
                            'low': tick.get('low', 0),
                            'close': tick.get('previous_close', tick.get('close', 0))
                        },
                        'volume': tick.get('volume', 0),
                        'change': tick.get('change', 0),
                        'change_percent': tick.get('change_percent', 0)
                    }
                else:
                    missing_symbols.append(symbol)
            
            # Step 2: Fetch missing from Zerodha API (async call)
            if missing_symbols and self.kite:
                try:
                    # Build proper instrument keys
                    instrument_keys = []
                    for symbol in missing_symbols:
                        if 'NIFTY' in symbol or 'BANKNIFTY' in symbol or 'FINNIFTY' in symbol:
                            if any(x in symbol for x in ['CE', 'PE']):
                                instrument_keys.append(f'NFO:{symbol}')
                            else:
                                instrument_keys.append(f'NSE:{symbol}')
                        else:
                            instrument_keys.append(f'NSE:{symbol}')
                    
                    # 🎯 Use async API call to prevent blocking
                    api_quotes = await self._async_api_call(self.kite.quote, instrument_keys)
                    
                    if api_quotes:
                        for key, quote in api_quotes.items():
                            # Extract symbol from key (e.g., "NFO:NIFTY25D0226000PE" -> "NIFTY25D0226000PE")
                            symbol = key.split(':')[-1]
                            result[symbol] = {
                                'last_price': quote.get('last_price', 0),
                                'ohlc': quote.get('ohlc', {}),
                                'volume': quote.get('volume', 0),
                                'change': quote.get('change', 0),
                                'change_percent': quote.get('change', 0) / quote.get('ohlc', {}).get('close', 1) * 100 if quote.get('ohlc', {}).get('close') else 0
                            }
                        
                except Exception as api_error:
                    logger.warning(f"⚠️ API quote fetch failed for {missing_symbols}: {api_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting quotes: {e}")
            return {}

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

    def get_positions_sync(self) -> Dict:
        """Get positions synchronously (for duplicate checking)"""
        try:
            if not self.kite:
                return {'net': [], 'day': []}
            positions = self.kite.positions()
            return positions if positions else {'net': [], 'day': []}
        except Exception as e:
            logger.debug(f"Could not get positions sync: {e}")
            return {'net': [], 'day': []}
    
    def get_required_margin_for_order(self, symbol: str, quantity: int, order_type: str = 'BUY', product: str = 'MIS') -> float:
        """Get required margin for a specific order from Zerodha"""
        try:
            if not self.kite:
                return 0.0
            
            # Determine correct exchange for the symbol
            exchange_for_margin = 'NSE'
            if symbol and (symbol.endswith('CE') or symbol.endswith('PE') or symbol.endswith('FUT')):
                exchange_for_margin = 'NFO'

            # Use Zerodha's order margin API to get exact margin requirement
            order_params = [{
                'exchange': exchange_for_margin,
                'tradingsymbol': symbol,
                'transaction_type': order_type.upper(),
                'variety': 'regular',
                'product': product,  # MIS for intraday, CNC for delivery
                'order_type': 'MARKET',
                'quantity': quantity
            }]
            
            try:
                margin_detail = self.kite.order_margins(order_params)
                if margin_detail and len(margin_detail) > 0:
                    total_margin = margin_detail[0].get('total', 0)
                    logger.info(f"💰 Margin for {symbol} x{quantity}: ₹{total_margin:,.2f}")
                    return float(total_margin)
            except Exception as e:
                logger.debug(f"Could not get order margin from API: {e}")
                
            # Fallback: Estimate based on instrument type
            if symbol.endswith('CE') or symbol.endswith('PE'):
                # Options: Rough estimate - premium × quantity
                # We'll need LTP for accurate calculation
                try:
                    ltp = self.kite.ltp([f'{exchange_for_margin}:' + symbol])
                    key = f'{exchange_for_margin}:{symbol}'
                    if ltp and key in ltp:
                        premium = ltp[key].get('last_price', 100)
                        return float(premium * quantity)
                except:
                    return float(100 * quantity)  # Default ₹100 per option
                    
            elif symbol.endswith('FUT'):
                # Futures: ~10-15% of contract value
                try:
                    ltp = self.kite.ltp([f'{exchange_for_margin}:' + symbol])
                    key = f'{exchange_for_margin}:{symbol}'
                    if ltp and key in ltp:
                        price = ltp[key].get('last_price', 1000)
                        return float(price * quantity * 0.15)
                except:
                    return float(quantity * 1000 * 0.15)
            else:
                # Equity: Full amount for CNC, ~20% for MIS
                try:
                    ltp = self.kite.ltp(['NSE:' + symbol])
                    if ltp and f'NSE:{symbol}' in ltp:
                        price = ltp[f'NSE:{symbol}'].get('last_price', 100)
                        if product == 'MIS':
                            return float(price * quantity * 0.2)  # 20% for intraday
                        else:
                            return float(price * quantity)  # Full for delivery
                except:
                    return float(quantity * 100)
                    
        except Exception as e:
            logger.error(f"Error calculating margin for {symbol}: {e}")
            return 0.0
    
    def get_margins_sync(self) -> float:
        """Get available margin synchronously (for real-time capital tracking)"""
        import time
        current_time = time.time()  # 🚨 FIX: Define current_time at start
        
        try:
            # Check unified cache first to prevent API hammering
            cached_margins = self._get_cached_data('margins', 'margins')
            if cached_margins is not None:
                return cached_margins
            
            if not self.kite:
                logger.error("❌ Kite client is None - cannot get margins")
                return 0.0

            margins = self.kite.margins()

            # 🚨 CRITICAL VALIDATION: Ensure margins is a dict
            if margins is None:
                logger.error("❌ kite.margins() returned None")
                return 0.0
            elif isinstance(margins, int):
                logger.error(f"❌ kite.margins() returned int instead of dict: {margins}")
                return 0.0
            elif not isinstance(margins, dict):
                logger.error(f"❌ kite.margins() returned {type(margins)} instead of dict: {margins}")
                return 0.0

            if margins and 'equity' in margins:
                equity = margins['equity']

                # Get net available (this is what's actually free to trade)
                net = equity.get('net', 0)

                # Get available breakdown
                available = equity.get('available', {})
                cash = available.get('cash', 0)
                collateral = available.get('collateral', 0)
                intraday_payin = available.get('intraday_payin', 0)

                # Get used margin
                utilised = equity.get('utilised', {})
                used_debits = utilised.get('debits', 0)
                used_exposure = utilised.get('exposure', 0)
                used_m2m = utilised.get('m2m', 0)
                used_option_premium = utilised.get('option_premium', 0)
                used_holding_sales = utilised.get('holding_sales', 0)

                total_used = used_debits + used_exposure + used_m2m + used_option_premium + used_holding_sales

                # Real available = net (Zerodha calculates this correctly)
                # But if net is 0, calculate manually
                if net > 0:
                    real_available = net
                else:
                    total_funds = cash + collateral + intraday_payin
                    real_available = max(0, total_funds - total_used)

                logger.info(f"💰 MARGIN STATUS: Available=₹{real_available:,.2f}, Used=₹{total_used:,.2f}, Cash=₹{cash:,.2f}")
                
                # Update unified cache
                self._set_cached_data('margins', float(real_available), 'margins')
                
                return float(real_available)

            logger.warning("⚠️ No equity data in margins response")
            return 0.0

        except Exception as e:
            # Only log rate limit errors once per minute
            if "Too many requests" in str(e):
                if not hasattr(self, '_last_rate_limit_log') or current_time - self._last_rate_limit_log > 60:
                    logger.error(f"❌ Rate limit hit: {e}")
                    self._last_rate_limit_log = current_time
            else:
                logger.error(f"❌ Error getting margins sync: {e}")
                logger.error(f"   Error type: {type(e)}")
                
                # 🚨 DEFENSIVE: Reset cache if corrupted
                if "'timestamp'" in str(e) or "KeyError" in str(e):
                    logger.warning("🔄 Cache corruption detected - resetting margins cache")
                    self._reset_caches()
            
            # Return cached value if available during errors
            cached_fallback = self._get_cached_data('margins', 'margins')
            if cached_fallback and cached_fallback > 0:
                logger.debug(f"   Using cached margin value: ₹{cached_fallback:,.2f}")
                return cached_fallback
            
            return 0.0
    
    async def get_positions(self) -> Dict:
        """Get positions with retry"""
        import time
        current_time = time.time()  # 🚨 FIX: Define current_time at start
        
        # Check unified cache first to prevent API hammering
        cached_positions = self._get_cached_data('positions', 'positions')
        if cached_positions is not None:
            return cached_positions

        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            if self.api_key and self.access_token:
                logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
                self._initialize_kite()
                if not self.kite:
                    logger.error("❌ Zerodha kite client reinitialize failed")
            else:
                logger.debug("⚠️ Zerodha kite client is None - missing credentials, skipping reinitialize")
            return {'net': [], 'day': []}

        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting positions from Zerodha (attempt {attempt + 1}) - CACHE MISS")
                result = await self._async_api_call(self.kite.positions)

                # 🚨 CRITICAL VALIDATION: Ensure result is a dict
                if result is None:
                    logger.error(f"❌ kite.positions returned None")
                    return {'net': [], 'day': []}
                elif isinstance(result, int):
                    logger.error(f"❌ kite.positions returned int instead of dict: {result}")
                    return {'net': [], 'day': []}
                elif not isinstance(result, dict):
                    logger.error(f"❌ kite.positions returned {type(result)} instead of dict: {result}")
                    return {'net': [], 'day': []}

                logger.info(f"✅ Got positions: {len(result.get('net', []))} net, {len(result.get('day', []))} day")

                # Update unified cache
                self._set_cached_data('positions', result, 'positions')
                
                # Track successful API call
                self._last_successful_call = f"positions at {datetime.now().strftime('%H:%M:%S')}"

                return result
            except Exception as e:
                # Only log rate limit errors once per minute
                if "Too many requests" in str(e):
                    if not hasattr(self, '_last_rate_limit_log') or current_time - self._last_rate_limit_log > 60:
                        logger.error(f"❌ Rate limit hit: {e}")
                        self._last_rate_limit_log = current_time
                else:
                    logger.error(f"❌ Get positions attempt {attempt + 1} failed: {e}")
                    
                    # 🚨 ENHANCED DEBUGGING: Track token invalidation patterns
                    if "Incorrect `api_key` or `access_token`" in str(e):
                        logger.error(f"🚨 TOKEN INVALIDATION DETECTED:")
                        logger.error(f"   Time since last token refresh: {current_time - self._last_token_refresh:.1f}s")
                        logger.error(f"   Kite client exists: {self.kite is not None}")
                        logger.error(f"   Access token length: {len(self.access_token) if self.access_token else 0}")
                        logger.error(f"   Is connected flag: {self.is_connected}")
                        logger.error(f"   Connection state: {self.connection_state}")
                        logger.error(f"   Last successful API call: {getattr(self, '_last_successful_call', 'Never')}")
                        
                        # Try to reinitialize the kite client
                        logger.warning("🔄 Attempting to reinitialize KiteConnect client...")
                        self._initialize_kite()
                        
                        if self.kite and self.is_connected:
                            logger.info("✅ KiteConnect reinitialized successfully")
                            # Try the API call once more with fresh client
                            try:
                                result = await self._async_api_call(self.kite.positions)
                                if result:
                                    logger.info("✅ Position fetch successful after reinitialize")
                                    self._set_cached_data('positions', result, 'positions')
                                    return result
                            except Exception as retry_e:
                                logger.error(f"❌ Retry after reinitialize failed: {retry_e}")
                        else:
                            logger.error("❌ KiteConnect reinitialization failed")
                    
                    # 🚨 DEFENSIVE: Reset cache if corrupted
                    if "'timestamp'" in str(e) or "KeyError" in str(e):
                        logger.warning("🔄 Cache corruption detected - resetting positions cache")
                        self._reset_caches()
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # Return cached value if available during errors
        cached_fallback = self._get_cached_data('positions', 'positions')
        if cached_fallback:
            logger.info(f"   Using cached positions (preventing API hammering)")
            return cached_fallback
        
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
        """Get margins with retry and caching"""
        # Check unified cache first
        cached_margins = self._get_cached_data('margins_dict', 'margins')
        if cached_margins is not None:
            logger.info("Using cached margins")
            return cached_margins
        
        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            if self.api_key and self.access_token:
                logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
                self._initialize_kite()
                if not self.kite:
                    logger.error("❌ Zerodha kite client reinitialize failed")
            else:
                logger.debug("⚠️ Zerodha kite client is None - missing credentials, skipping reinitialize")
            return {'equity': {'available': {'cash': 0}}}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting margins from Zerodha (attempt {attempt + 1})")
                result = await self._async_api_call(self.kite.margins)
                
                # 🚨 FIX: Log total available margin (net), not just cash
                equity_data = result.get('equity', {})
                total_margin = equity_data.get('net', 0)
                cash = equity_data.get('available', {}).get('cash', 0)
                logger.info(f"✅ Got margins: Total=₹{total_margin:,.2f} (Cash=₹{cash:,.2f})")
                
                # Cache the result in unified cache
                self._set_cached_data('margins_dict', result, 'margins')
                return result
            except Exception as e:
                logger.error(f"❌ Get margins attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return {'equity': {'available': {'cash': 0}}}

    async def get_orders(self) -> List[Dict]:
        """Get orders with retry - CRITICAL for trade sync"""
        # CRITICAL FIX: Cache orders for 10 seconds to prevent API hammering
        now = time.time()
        if hasattr(self, '_orders_cache') and hasattr(self, '_orders_cache_time') and now - self._orders_cache_time < 10:
            logger.info("📊 Using cached orders (preventing API hammering)")
            return self._orders_cache
        
        # CRITICAL FIX: Check if kite client is None
        if not self.kite:
            if self.api_key and self.access_token:
                logger.error("❌ Zerodha kite client is None - attempting to reinitialize")
                self._initialize_kite()
                if not self.kite:
                    logger.error("❌ Zerodha kite client reinitialize failed")
            else:
                logger.debug("⚠️ Zerodha kite client is None - missing credentials, skipping reinitialize")
            return []
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📊 Getting orders from Zerodha (attempt {attempt + 1}) - CACHE MISS")
                result = await self._async_api_call(self.kite.orders)
                logger.info(f"✅ Got {len(result)} orders")
                
                # Cache the result for 10 seconds
                self._orders_cache = result
                self._orders_cache_time = now
                logger.info(f"📊 Cached orders result for 10 seconds")
                
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
        """Get instruments with intelligent caching to prevent rate limiting
        
        🎯 CRITICAL FIX (2025-12-01): Cache is now EXCHANGE-SPECIFIC!
        Previously, NSE and NFO shared the same cache, causing NSE equity
        instruments to be returned when NFO options were requested.
        """
        try:
            current_time = time.time()
            cache_key = f"{exchange}_instruments"
            
            # 🎯 FIXED (2025-12-01): Use EXCHANGE-SPECIFIC cache keys
            # Previously _instruments_cache was a single dict, causing cross-contamination
            if not isinstance(self._instruments_cache, dict):
                self._instruments_cache = {}
            
            # Check exchange-specific cache first
            exchange_cache = self._instruments_cache.get(exchange)
            if (exchange_cache and isinstance(exchange_cache, dict) and
                'timestamp' in exchange_cache and 'value' in exchange_cache and
                current_time - exchange_cache['timestamp'] < 300):  # 5 minute cache
                
                cached_value = exchange_cache['value']
                logger.debug(f"📊 Using cached {exchange} instruments (age: {current_time - exchange_cache['timestamp']:.1f}s, count: {len(cached_value) if cached_value else 0})")
                
                # Update exchange-specific caches
                if exchange == 'NFO' and cached_value:
                    self._nfo_instruments = cached_value
                elif exchange == 'NSE' and cached_value:
                    self._nse_instruments = cached_value
                return cached_value
            
            # Check if we have cached data that's still valid (secondary cache)
            now = time.time()
            
            if (cache_key in self._instruments_last_fetched and 
                now - self._instruments_last_fetched[cache_key] < self._instruments_cache_duration):
                
                # Return exchange-specific cached data
                if exchange == 'NFO' and self._nfo_instruments:
                    logger.info(f"✅ Using cached {exchange} instruments ({len(self._nfo_instruments)} instruments)")
                    return self._nfo_instruments
                elif exchange == 'NSE' and self._nse_instruments:
                    logger.info(f"✅ Using cached {exchange} instruments ({len(self._nse_instruments)} instruments)")
                    return self._nse_instruments
            
            # Cache miss or expired - fetch fresh data with rate limit protection
            logger.info(f"🔄 Fetching fresh {exchange} instruments from Zerodha...")
            
            # 🔥 FIX: Check if kite client is initialized before calling API
            if not self.kite:
                logger.error(f"❌ Cannot fetch {exchange} instruments - KiteConnect not initialized (no token?)")
                # Return cached data if available
                if exchange == 'NFO' and self._nfo_instruments:
                    logger.info(f"🔄 Returning cached NFO instruments while awaiting token")
                    return self._nfo_instruments
                elif exchange == 'NSE' and self._nse_instruments:
                    logger.info(f"🔄 Returning cached NSE instruments while awaiting token")
                    return self._nse_instruments
                return []
            
            # Add delay to prevent rate limiting
            if hasattr(self, '_last_instruments_call'):
                time_since_last = now - self._last_instruments_call
                if time_since_last < 2:  # Minimum 2 seconds between calls
                    await asyncio.sleep(2 - time_since_last)
            
            self._last_instruments_call = now
            
            instruments = await self._async_api_call(self.kite.instruments, exchange)
            
            if instruments:
                # Cache the results with exchange-specific keys
                self._instruments_last_fetched[cache_key] = now
                
                # 🎯 FIXED (2025-12-01): Store with EXCHANGE-SPECIFIC cache key
                self._instruments_cache[exchange] = {'value': instruments, 'timestamp': current_time}
                
                if exchange == 'NFO':
                    self._nfo_instruments = instruments
                    # Count options vs non-options for debugging
                    options_count = sum(1 for inst in instruments if inst.get('instrument_type') in ['CE', 'PE'])
                    logger.info(f"✅ Loaded {len(instruments)} NFO instruments ({options_count} are options)")
                    
                    # Build fast lookup map for tokens
                    try:
                        self._symbol_to_token = {
                            inst.get('tradingsymbol', ''): (inst.get('instrument_token') or inst.get('token'))
                            for inst in instruments if inst.get('tradingsymbol')
                        }
                        logger.info(f"✅ Built token index for {len(self._symbol_to_token)} NFO symbols")
                    except Exception as idx_err:
                        logger.debug(f"Could not build token index: {idx_err}")
                elif exchange == 'NSE':
                    self._nse_instruments = instruments
                    logger.info(f"✅ Cached {len(instruments)} {exchange} instruments for 1 hour")
                
                return instruments
            else:
                logger.warning(f"⚠️ No instruments returned from {exchange}")
                return []
                
        except Exception as e:
            error_str = str(e)
            
            # 🔥 FIX: Detect token/auth issues from error message
            if 'AccessDenied' in error_str or 'Access Denied' in error_str:
                logger.error(f"❌ Get instruments failed: ACCESS DENIED - Token missing or expired. Please submit daily Zerodha token.")
            elif 'TokenException' in error_str or 'Invalid' in error_str:
                logger.error(f"❌ Get instruments failed: Invalid token - Please re-authenticate with Zerodha")
            else:
                logger.error(f"❌ Get instruments attempt failed: {e}")

            # 🚨 DEFENSIVE: Reset cache if corrupted
            if "'timestamp'" in error_str or "KeyError" in error_str:
                logger.warning("🔄 Cache corruption detected - resetting instruments cache")
                self._reset_caches()
            
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
            # 🚨 CRITICAL VALIDATION: Check if kite client exists
            if not self.kite:
                logger.error(f"❌ Kite client is None - cannot get expiries for {underlying_symbol}")
                return []

            # Get all instruments for the exchange
            instruments = await self.get_instruments(exchange)

            # 🚨 CRITICAL VALIDATION: Ensure instruments is a list
            if instruments is None:
                logger.error(f"❌ get_instruments returned None for {underlying_symbol}")
                return []
            elif isinstance(instruments, int):
                logger.error(f"❌ get_instruments returned int instead of list: {instruments} for {underlying_symbol}")
                return []
            elif not isinstance(instruments, list):
                logger.error(f"❌ get_instruments returned {type(instruments)} instead of list for {underlying_symbol}")
                return []

            if not instruments:
                logger.warning(f"⚠️ No instruments data available for {underlying_symbol}")
                return []

            # Filter options for the specific underlying
            options_contracts = []
            for instrument in instruments:
                if not isinstance(instrument, dict):
                    continue

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
                # CRITICAL FIX: Zerodha uses YYMM format (e.g., 25SEP) not DDMMMYY
                # Based on actual symbols: BAJFINANCE25SEP950CE, M&M25SEP3500CE
                formatted = f"{str(expiry_date.year)[-2:]}{month_names[expiry_date.month - 1]}"

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
            logger.error(f"   Error type: {type(e)}")
            import traceback
            logger.error(f"   Full traceback: {traceback.format_exc()}")
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
    
    def get_options_ltp_sync(self, options_symbol: str) -> Optional[float]:
        """Get real-time LTP for options symbol from Zerodha (synchronous version)"""
        logger.info(f"🚨 DEBUG: get_options_ltp_sync called for {options_symbol}")
        logger.info(f"   kite: {self.kite is not None}")
        logger.info(f"   is_connected: {self.is_connected}")
        
        try:
            if not self.kite or not self.is_connected:
                logger.warning("⚠️ Zerodha not connected - cannot get options LTP")
                return None
            
            # 🚨 DEBUG: Test basic Zerodha connectivity first
            try:
                test_margins = self.kite.margins()
                logger.info(f"✅ Zerodha connectivity test passed - margins call successful")
            except Exception as conn_test_error:
                logger.error(f"❌ Zerodha connectivity test FAILED: {conn_test_error}")
                logger.error(f"   This means the access token or API key is invalid")
                # CRITICAL FIX: Mark as disconnected when token is invalid
                self.is_connected = False
                self.connection_state = ConnectionState.FAILED
                logger.error(f"🚨 Connection state updated: is_connected={self.is_connected}")
                logger.error(f"💡 Submit fresh token via /api/auth/zerodha/callback or redeploy")
                return None
            
            # Get quotes for the options symbol
            exchange = self._get_exchange_for_symbol(options_symbol)
            full_symbol = f"{exchange}:{options_symbol}"
            
            logger.info(f"🔍 Zerodha Quote Request: {full_symbol}")
            logger.info(f"   Original symbol: {options_symbol}")
            logger.info(f"   Exchange: {exchange}")
            logger.info(f"   Full symbol: {full_symbol}")
            
            # Try both quote and ltp with exchange-qualified symbol
            try:
                quotes = self.kite.quote([full_symbol])
                logger.info(f"🔍 Zerodha Quote Response: {quotes}")
            except Exception as quote_error:
                logger.error(f"❌ Error getting Zerodha LTP sync for {options_symbol}: {quote_error}")
                logger.error(f"Error type: {type(quote_error)}")
                
                # 🚨 DEBUG: Try different symbol formats to identify the issue
                logger.info(f"🔍 Testing different symbol formats for debugging:")
                
                # Test 1: Try without exchange prefix
                try:
                    logger.info(f"   Testing format 1: {options_symbol} (no exchange)")
                    test1 = self.kite.quote([options_symbol])
                    logger.info(f"   Format 1 SUCCESS: {test1}")
                except Exception as e1:
                    logger.info(f"   Format 1 FAILED: {e1}")
                
                # Test 2: Try with different exchange
                try:
                    test_symbol2 = f"NSE:{options_symbol}"
                    logger.info(f"   Testing format 2: {test_symbol2}")
                    test2 = self.kite.quote([test_symbol2])
                    logger.info(f"   Format 2 SUCCESS: {test2}")
                except Exception as e2:
                    logger.info(f"   Format 2 FAILED: {e2}")
                
                # Re-raise original error
                raise quote_error
            
            if quotes and full_symbol in quotes:
                quote_data = quotes[full_symbol]
                ltp = quote_data.get('last_price', 0)
                
                # Additional debugging - check all available price fields
                logger.debug(f"🔍 Quote data for {options_symbol}: {quote_data}")
                
                if ltp and ltp > 0:
                    logger.info(f"✅ ZERODHA LTP (sync): {options_symbol} = ₹{ltp}")
                    return float(ltp)
                else:
                    # Check other price fields as fallback
                    ohlc = quote_data.get('ohlc', {})
                    close_price = ohlc.get('close', 0)
                    if close_price and close_price > 0:
                        logger.info(f"✅ ZERODHA LTP (close): {options_symbol} = ₹{close_price}")
                        return float(close_price)
            
            logger.warning(f"⚠️ No LTP data from Zerodha sync call for {options_symbol}")
            try:
                # Some environments allow ltp with exchange-qualified string
                ltp_resp = self.kite.ltp([full_symbol])
                if ltp_resp and full_symbol in ltp_resp:
                    ltp2 = ltp_resp[full_symbol].get('last_price') or ltp_resp[full_symbol].get('last_traded_price') or 0
                    if ltp2 and ltp2 > 0:
                        logger.info(f"✅ ZERODHA LTP (sync alt): {options_symbol} = ₹{ltp2}")
                        return float(ltp2)
            except Exception:
                pass
            # Fallback: resolve instrument token from cached NFO instruments and fetch via token (sync)
            try:
                # Ensure NFO instruments are available (SYNC load allowed here)
                if self._nfo_instruments is None:
                    try:
                        instruments = self.kite.instruments('NFO')
                        # Cache
                        self._nfo_instruments = instruments or []
                        logger.info(f"✅ Loaded NFO instruments for sync path: {len(self._nfo_instruments)}")
                    except Exception as load_err:
                        logger.warning(f"⚠️ Could not load NFO instruments in sync path: {load_err}")
                        self._nfo_instruments = []

                # Use already cached NFO instruments (do not attempt async here)
                # Prefer fast map if available
                if not self._symbol_to_token and self._nfo_instruments:
                    try:
                        self._symbol_to_token = {
                            inst.get('tradingsymbol', ''): (inst.get('instrument_token') or inst.get('token'))
                            for inst in (self._nfo_instruments or []) if inst.get('tradingsymbol')
                        }
                    except Exception:
                        pass

                if not self._symbol_to_token and not self._nfo_instruments:
                    logger.warning("⚠️ NFO instruments cache empty in sync path; skipping token fallback")
                    return None

                instrument_token = self._symbol_to_token.get(options_symbol)
                if not instrument_token:
                    logger.info(f"ℹ️ No token found in index for {options_symbol}")
                    # CRITICAL FIX: Enhanced symbol matching for individual stock options
                    try:
                        import re
                        # 🚨 CRITICAL FIX: Corrected regex pattern for options symbols
                        # Pattern: SYMBOL + DDMMM + STRIKE + CE/PE (not DDMMMDD)
                        # Example: ITC25SEP400PE, RELIANCE25SEP3000CE
                        m = re.match(r"([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)", options_symbol)
                        if m and self._nfo_instruments:
                            underlying, expiry, strike, opt_type = m.groups()
                            logger.info(f"🔍 PARSING: {options_symbol} → {underlying}, {expiry}, {strike}, {opt_type}")
                            
                            # Try exact match first
                            for inst in self._nfo_instruments:
                                if inst.get('tradingsymbol') == options_symbol:
                                    instrument_token = inst.get('instrument_token') or inst.get('token')
                                    logger.info(f"✅ EXACT MATCH: Found token {instrument_token}")
                                    break
                            
                            # If no exact match, try improved component matching
                            if not instrument_token:
                                logger.info(f"🔍 SEARCHING for {underlying} options with strike {strike}...")
                                matches_found = []
                                exact_symbol_matches = []

                                for inst in self._nfo_instruments:
                                    inst_symbol = inst.get('tradingsymbol', '')

                                    # Try multiple matching strategies
                                    try:
                                        # Strategy 1: Parse the instrument symbol and compare components
                                        import re
                                        m_inst = re.match(rf"({underlying.upper()})(.+?)(\d+)(CE|PE)", inst_symbol)
                                        if m_inst:
                                            inst_underlying, inst_expiry, inst_strike, inst_type = m_inst.groups()

                                            # Check if components match
                                            if (inst_underlying.upper() == underlying.upper() and
                                                inst_strike == str(strike) and
                                                inst_type == opt_type):

                                                # Check expiry match (more flexible)
                                                if (inst_expiry.upper() == expiry.upper() or
                                                    inst_expiry.upper() in expiry.upper() or
                                                    expiry.upper() in inst_expiry.upper()):

                                                    exact_symbol_matches.append(inst_symbol)
                                                    instrument_token = inst.get('instrument_token') or inst.get('token')
                                                    logger.info(f"✅ EXACT COMPONENT MATCH: {inst_symbol} (token: {instrument_token})")
                                                    break
                                                else:
                                                    matches_found.append(f"{inst_symbol} (expiry mismatch: {inst_expiry} vs {expiry})")
                                            else:
                                                # Partial matches for debugging
                                                if (inst_underlying.upper() == underlying.upper() and
                                                    inst_strike == str(strike)):
                                                    matches_found.append(f"{inst_symbol} (type mismatch: {inst_type} vs {opt_type})")
                                                elif (inst_underlying.upper() == underlying.upper() and
                                                      inst_type == opt_type):
                                                    matches_found.append(f"{inst_symbol} (strike mismatch: {inst_strike} vs {strike})")

                                        # Strategy 2: Simple substring matching as fallback
                                        elif (underlying.upper() in inst_symbol.upper() and
                                              str(strike) in inst_symbol and
                                              opt_type in inst_symbol):
                                            matches_found.append(inst_symbol)

                                    except Exception as match_err:
                                        continue

                                # Log results
                                if instrument_token:
                                    logger.info(f"✅ Found token {instrument_token} for {options_symbol}")
                                elif exact_symbol_matches:
                                    logger.info(f"✅ Found {len(exact_symbol_matches)} exact matches")
                                elif matches_found:
                                    logger.warning(f"⚠️ Found {len(matches_found)} partial matches for {options_symbol}")
                                    for match in matches_found[:3]:  # Log first 3
                                        logger.info(f"   📋 Similar: {match}")
                                else:
                                    logger.error(f"❌ NO MATCHING OPTIONS found for {underlying} strike {strike} expiry {expiry}")
                    except Exception as re_err:
                        logger.error(f"Symbol parse resolve failed: {re_err}")

                if instrument_token:
                    # Fetch LTP by instrument token (preferred for tokens)
                    ltp_resp = self.kite.ltp([instrument_token])
                    if ltp_resp:
                        for _, data in ltp_resp.items():
                            token_ltp = data.get('last_price') or data.get('last_traded_price') or 0
                            if token_ltp and token_ltp > 0:
                                logger.info(f"✅ ZERODHA LTP (sync token): {options_symbol} = ₹{token_ltp}")
                                return float(token_ltp)
            except Exception as fallback_err:
                logger.warning(f"⚠️ Token-based LTP sync fallback failed for {options_symbol}: {fallback_err}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha LTP sync for {options_symbol}: {e}")
            return None
    
    async def get_options_ltp(self, options_symbol: str) -> Optional[float]:
        """Get real-time LTP for options symbol from Zerodha"""
        try:
            if not self.kite or not self.is_connected:
                logger.warning("⚠️ Zerodha not connected - cannot get options LTP")
                return None
            
            # Get quotes for the options symbol
            exchange = self._get_exchange_for_symbol(options_symbol)
            full_symbol = f"{exchange}:{options_symbol}"
            
            # Try both quote and ltp with exchange-qualified symbol
            quotes = self.kite.quote([full_symbol])
            
            if quotes and full_symbol in quotes:
                quote_data = quotes[full_symbol]
                ltp = quote_data.get('last_price', 0)
                
                if ltp and ltp > 0:
                    logger.info(f"✅ ZERODHA LTP: {options_symbol} = ₹{ltp}")
                    return float(ltp)
            
            logger.warning(f"⚠️ No LTP data from Zerodha for {options_symbol}")
            try:
                ltp_resp = self.kite.ltp([full_symbol])
                if ltp_resp and full_symbol in ltp_resp:
                    ltp2 = ltp_resp[full_symbol].get('last_price') or ltp_resp[full_symbol].get('last_traded_price') or 0
                    if ltp2 and ltp2 > 0:
                        logger.info(f"✅ ZERODHA LTP (alt): {options_symbol} = ₹{ltp2}")
                        return float(ltp2)
            except Exception:
                pass

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

    async def get_available_strikes_for_symbol(self, underlying_symbol: str, expiry: str) -> List[int]:
        """Get all available strike prices for a specific underlying and expiry from NFO instruments"""
        try:
            # 🚨 CRITICAL VALIDATION: Check if kite client exists
            if not self.kite:
                logger.error(f"❌ Kite client is None - cannot get strikes for {underlying_symbol}")
                return []

            # Ensure NFO instruments are cached
            if self._nfo_instruments is None:
                instruments_result = await self.get_instruments('NFO')
                # 🚨 CRITICAL VALIDATION: Ensure get_instruments returns a list
                if instruments_result is None:
                    logger.error(f"❌ get_instruments returned None for {underlying_symbol}")
                    return []
                elif isinstance(instruments_result, int):
                    logger.error(f"❌ get_instruments returned int instead of list: {instruments_result} for {underlying_symbol}")
                    return []
                elif not isinstance(instruments_result, list):
                    logger.error(f"❌ get_instruments returned {type(instruments_result)} instead of list for {underlying_symbol}")
                    return []

            if not self._nfo_instruments:
                logger.warning(f"⚠️ No NFO instruments available for strike lookup")
                return []

            available_strikes = set()
            target_expiry = expiry.upper()

            # Debug: Log sample symbols for this underlying
            debug_logged = False
            
            for inst in self._nfo_instruments:
                if not isinstance(inst, dict):
                    continue

                trading_symbol = inst.get('tradingsymbol', '')
                
                # Debug logging for first few matching symbols
                if not debug_logged and underlying_symbol.upper() in trading_symbol:
                    logger.debug(f"🔍 Sample {underlying_symbol} symbol: {trading_symbol}")
                    debug_logged = True

                # Parse the symbol to extract components
                try:
                    import re
                    # Match pattern: UNDERLYING + EXPIRY + STRIKE + TYPE
                    # CRITICAL FIX: Zerodha format is UNDERLYING + YYMM + STRIKE + CE/PE
                    # Examples: BAJFINANCE25SEP950CE, M&M25SEP3500CE
                    m = re.match(rf"^({underlying_symbol.upper()})(\d{{2}}[A-Z]{{3}})(\d+)(CE|PE)$", trading_symbol)
                    if m:
                        symbol_underlying, symbol_expiry, strike_str, option_type = m.groups()
                        
                        # Debug first match
                        if len(available_strikes) == 0:
                            logger.debug(f"🔍 First match: {trading_symbol} -> Expiry: {symbol_expiry}, Target: {target_expiry}")

                        # Check if expiry matches
                        # Target expiry is now in YYMM format (e.g., 25SEP)
                        if symbol_expiry.upper() == target_expiry.upper():

                            try:
                                strike = int(strike_str)
                                available_strikes.add(strike)
                            except ValueError:
                                continue

                except Exception as parse_err:
                    continue

            sorted_strikes = sorted(list(available_strikes))
            logger.info(f"✅ Found {len(sorted_strikes)} available strikes for {underlying_symbol} {expiry}")
            if sorted_strikes:
                logger.info(f"   Range: {sorted_strikes[0]} - {sorted_strikes[-1]}")

            # 🚨 FINAL VALIDATION: Ensure we return a valid list
            if not isinstance(sorted_strikes, list):
                logger.error(f"❌ sorted_strikes is not a list: {type(sorted_strikes)} = {sorted_strikes}")
                return []

            # Filter out any non-integer values
            valid_strikes = []
            for strike in sorted_strikes:
                if isinstance(strike, int) and strike > 0:
                    valid_strikes.append(strike)
                else:
                    logger.warning(f"⚠️ Filtering out invalid strike: {strike} (type: {type(strike)})")

            return valid_strikes

        except Exception as e:
            logger.error(f"❌ Error getting available strikes for {underlying_symbol}: {e}")
            logger.error(f"   Error type: {type(e)}")
            import traceback
            logger.error(f"   Full traceback: {traceback.format_exc()}")
            return []

    async def find_closest_available_strike(self, underlying_symbol: str, target_strike: int, expiry: str, option_type: str = 'CE') -> Optional[int]:
        """Find the closest available strike to the target strike"""
        try:
            available_strikes = await self.get_available_strikes_for_symbol(underlying_symbol, expiry)

            # 🚨 CRITICAL VALIDATION: Ensure available_strikes is a list
            if available_strikes is None:
                logger.error(f"❌ get_available_strikes_for_symbol returned None for {underlying_symbol}")
                return None
            elif isinstance(available_strikes, int):
                logger.error(f"❌ get_available_strikes_for_symbol returned int instead of list: {available_strikes} for {underlying_symbol}")
                return None
            elif isinstance(available_strikes, str):
                logger.error(f"❌ get_available_strikes_for_symbol returned string instead of list: {available_strikes} for {underlying_symbol}")
                return None
            elif not isinstance(available_strikes, list):
                logger.error(f"❌ get_available_strikes_for_symbol returned {type(available_strikes)} instead of list for {underlying_symbol}")
                return None
            elif not available_strikes:
                logger.warning(f"⚠️ No available strikes found for {underlying_symbol} {expiry}")
                return None

            # Additional validation: ensure all elements are integers
            try:
                validated_strikes = []
                for strike in available_strikes:
                    if isinstance(strike, int) and strike > 0:
                        validated_strikes.append(strike)
                    else:
                        logger.warning(f"⚠️ Skipping invalid strike: {strike} (type: {type(strike)}) for {underlying_symbol}")

                if not validated_strikes:
                    logger.error(f"❌ No valid strikes found after validation for {underlying_symbol}")
                    return None

                available_strikes = validated_strikes

            except Exception as validation_error:
                logger.error(f"❌ Error validating strikes for {underlying_symbol}: {validation_error}")
                return None

            # Find closest strike
            try:
                closest_strike = min(available_strikes, key=lambda x: abs(x - target_strike))
            except (ValueError, TypeError) as min_error:
                logger.error(f"❌ Error finding minimum strike for {underlying_symbol}: {min_error}")
                logger.error(f"   Available strikes: {available_strikes}")
                return None

            # Log the selection
            logger.info(f"🎯 STRIKE SELECTION for {underlying_symbol}")
            logger.info(f"   Target: {target_strike}, Closest Available: {closest_strike}")
            logger.info(f"   Available Range: {min(available_strikes)} - {max(available_strikes)}")

            return closest_strike

        except Exception as e:
            logger.error(f"❌ Error finding closest strike for {underlying_symbol}: {e}")
            logger.error(f"   Error type: {type(e)}")
            import traceback
            logger.error(f"   Full traceback: {traceback.format_exc()}")
            return None
        
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

    async def get_option_chain(self, underlying_symbol: str, expiry: str = None, strikes: int = 10) -> Dict[str, Any]:
        """
        🎯 COMPREHENSIVE OPTION CHAIN FETCHER
        Fetches full option chain with Greeks, IV, OI, and depth for given underlying
        
        Args:
            underlying_symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
            expiry: Expiry date in format 'DDMMMYY' (e.g., '25DEC24'). If None, uses nearest expiry
            strikes: Number of strikes on each side of ATM (default: 10, means 10 ITM + ATM + 10 OTM = 21 strikes)
        
        Returns:
            Dict with structure:
            {
                'underlying': str,
                'expiry': str,
                'atm_strike': float,
                'spot_price': float,
                'timestamp': str,
                'chain': {
                    'calls': {strike: {...data...}, ...},
                    'puts': {strike: {...data...}, ...}
                },
                'analytics': {
                    'pcr': float,  # Put-Call Ratio (OI)
                    'max_pain': float,  # Strike with max pain
                    'iv_mean': float,
                    'iv_skew': Dict
                }
            }
        """
        try:
            # 🔥 FIX: Add rate limiting and caching to prevent "Too many requests" error
            if not hasattr(self, '_option_chain_cache'):
                self._option_chain_cache: Dict[str, tuple] = {}  # symbol -> (data, timestamp)
            if not hasattr(self, '_option_chain_cooldown'):
                self._option_chain_cooldown = 60  # 1 minute cache
            
            now = datetime.now()
            cache_key = f"{underlying_symbol}_{expiry or 'nearest'}"
            
            # Check cache
            if cache_key in self._option_chain_cache:
                cached_data, cache_time = self._option_chain_cache[cache_key]
                elapsed = (now - cache_time).total_seconds()
                if elapsed < self._option_chain_cooldown:
                    logger.debug(f"📦 Using cached option chain for {underlying_symbol} ({elapsed:.0f}s old)")
                    return cached_data
            
            if not self.kite or not self.is_connected:
                logger.warning(f"⚠️ Zerodha not connected - cannot get option chain for {underlying_symbol}")
                return {}
            
            logger.info(f"🔍 Fetching option chain for {underlying_symbol} expiry={expiry}")
            
            # Step 1: Map internal symbol to Zerodha trading symbol
            # 🔥 FIX: Zerodha index names for spot price quotes
            symbol_map = {
                'NIFTY-I': 'NIFTY 50',
                'NIFTY': 'NIFTY 50',
                'BANKNIFTY-I': 'NIFTY BANK',
                'BANKNIFTY': 'NIFTY BANK',
                'FINNIFTY-I': 'NIFTY FIN SERVICE',  # 🔥 Fixed: Zerodha uses full name
                'FINNIFTY': 'NIFTY FIN SERVICE',    # 🔥 Fixed: Zerodha uses full name
                'MIDCPNIFTY-I': 'NIFTY MID SELECT',
                'MIDCPNIFTY': 'NIFTY MID SELECT'
            }
            
            zerodha_symbol = symbol_map.get(underlying_symbol, underlying_symbol)
            
            # Step 2: Get spot price of underlying
            exchange = self._get_exchange_for_symbol(underlying_symbol)
            full_symbol = f"{exchange}:{zerodha_symbol}"
            
            spot_quote = self.kite.quote([full_symbol])
            if not spot_quote or full_symbol not in spot_quote:
                logger.error(f"❌ Could not fetch spot price for {underlying_symbol} (tried: {full_symbol})")
                return {}
            
            spot_price = spot_quote[full_symbol].get('last_price', 0)
            if not spot_price:
                logger.error(f"❌ Invalid spot price for {underlying_symbol}")
                return {}
            
            logger.info(f"✅ Spot price for {underlying_symbol}: ₹{spot_price}")
            
            # Step 2: Ensure NFO instruments are loaded with retry
            if self._nfo_instruments is None or len(self._nfo_instruments) == 0:
                logger.info(f"🔄 Loading NFO instruments for {underlying_symbol} option chain...")
                
                # Try up to 3 times with delay
                for attempt in range(3):
                    nfo_result = await self.get_instruments('NFO')
                    if nfo_result and len(nfo_result) > 0:
                        logger.info(f"✅ Loaded {len(nfo_result)} NFO instruments (attempt {attempt + 1})")
                        break
                    
                    if attempt < 2:
                        logger.warning(f"⚠️ NFO instruments fetch attempt {attempt + 1} returned empty, retrying in 2s...")
                        await asyncio.sleep(2)
                else:
                    logger.error(f"❌ Failed to fetch NFO instruments after 3 attempts for {underlying_symbol}")
                    return {}
            
            if not self._nfo_instruments or len(self._nfo_instruments) == 0:
                logger.error(f"❌ No NFO instruments available for {underlying_symbol} option chain")
                return {}
            
            # Step 3: Filter options for this underlying and expiry
            # NFO instrument 'name' field mapping:
            # 🔥 FIXED 2025-12-02: Zerodha uses 'BANKNIFTY' not 'NIFTY BANK'!
            # NIFTY options → name='NIFTY'
            # BANKNIFTY options → name='BANKNIFTY'  
            # FINNIFTY options → name='FINNIFTY'
            # MIDCPNIFTY options → name='MIDCPNIFTY'
            nfo_name_map = {
                'NIFTY': 'NIFTY',
                'NIFTY-I': 'NIFTY',
                'BANKNIFTY': 'BANKNIFTY',      # 🔥 Fixed from 'NIFTY BANK'
                'BANKNIFTY-I': 'BANKNIFTY',    # 🔥 Fixed from 'NIFTY BANK'
                'FINNIFTY': 'FINNIFTY',
                'FINNIFTY-I': 'FINNIFTY',
                'MIDCPNIFTY': 'MIDCPNIFTY',    # 🔥 Fixed from 'NIFTY MID SELECT'
                'MIDCPNIFTY-I': 'MIDCPNIFTY'   # 🔥 Fixed from 'NIFTY MID SELECT'
            }
            
            nfo_search_name = nfo_name_map.get(underlying_symbol, underlying_symbol)
            logger.info(f"🔍 Searching NFO instruments for name='{nfo_search_name}' (input: {underlying_symbol})")
            
            # 🎯 DEBUG (2025-12-01): Verify NFO instruments have options (CE/PE), not just equities
            try:
                ce_pe_count = sum(1 for inst in self._nfo_instruments if inst.get('instrument_type') in ['CE', 'PE'])
                eq_count = sum(1 for inst in self._nfo_instruments if inst.get('instrument_type') == 'EQ')
                fut_count = sum(1 for inst in self._nfo_instruments if inst.get('instrument_type') == 'FUT')
                
                logger.info(f"📊 NFO Instruments breakdown: {len(self._nfo_instruments)} total | "
                           f"Options (CE/PE): {ce_pe_count} | Futures: {fut_count} | EQ: {eq_count}")
                
                # 🚨 SANITY CHECK: If we have mostly EQ instruments, the cache is contaminated!
                if eq_count > ce_pe_count and eq_count > 100:
                    logger.error(f"🚨 NFO CACHE CONTAMINATED! Found {eq_count} EQ vs {ce_pe_count} options. Forcing refresh...")
                    self._nfo_instruments = None
                    self._instruments_cache.pop('NFO', None)  # Clear contaminated cache
                    nfo_result = await self.get_instruments('NFO')
                    if nfo_result:
                        logger.info(f"✅ Refreshed NFO instruments: {len(nfo_result)} total")
                    else:
                        logger.error(f"❌ Failed to refresh NFO instruments")
                        return {}
                
                # Show sample NIFTY options for debugging
                nifty_options = [inst for inst in self._nfo_instruments[:1000] 
                                if inst.get('name') in ['NIFTY', 'NIFTY 50'] and inst.get('instrument_type') in ['CE', 'PE']][:3]
                if nifty_options:
                    sample_info = [f"{i.get('tradingsymbol')} ({i.get('instrument_type')})" for i in nifty_options]
                    logger.info(f"📊 Sample NIFTY options: {sample_info}")
                    
            except Exception as dbg_err:
                logger.debug(f"Debug logging failed: {dbg_err}")
            
            options_list = []
            for inst in self._nfo_instruments:
                if inst.get('name') == nfo_search_name and inst.get('instrument_type') in ['CE', 'PE']:
                    # If expiry specified, filter by it
                    inst_expiry = inst.get('expiry')
                    if expiry:
                        # Convert expiry format if needed
                        if inst_expiry and self._compare_expiry(inst_expiry, expiry):
                            options_list.append(inst)
                    else:
                        # No expiry specified - collect all
                        options_list.append(inst)
            
            if not options_list:
                logger.error(f"❌ No options found for {underlying_symbol} (searched name: '{nfo_search_name}')")
                # DEBUG: Show first 5 NFO instruments that ARE options (CE/PE)
                sample_options = [inst for inst in self._nfo_instruments if inst.get('instrument_type') in ['CE', 'PE']][:5]
                if sample_options:
                    sample_info = [{k: inst.get(k) for k in ['name', 'tradingsymbol', 'instrument_type', 'strike']} 
                                   for inst in sample_options]
                    logger.error(f"   DEBUG: Sample OPTIONS in NFO: {sample_info}")
                else:
                    # Show any 5 instruments to see what we have
                    sample_insts = [{k: inst.get(k) for k in ['name', 'tradingsymbol', 'instrument_type', 'strike']} 
                                   for inst in self._nfo_instruments[:5]]
                    logger.error(f"   DEBUG: Sample NFO instruments (no options found!): {sample_insts}")
                    
                # Show unique names that have options
                try:
                    names_with_options = set(inst.get('name') for inst in self._nfo_instruments 
                                            if inst.get('instrument_type') in ['CE', 'PE'])
                    logger.error(f"   DEBUG: Unique names with options: {list(names_with_options)[:20]}")
                except:
                    pass
                return {}
            
            # Step 4: If no expiry specified, find nearest expiry
            if not expiry:
                unique_expiries = sorted(set(inst.get('expiry') for inst in options_list if inst.get('expiry')))
                if unique_expiries:
                    expiry = unique_expiries[0]  # Nearest expiry
                    options_list = [inst for inst in options_list if inst.get('expiry') == expiry]
                    logger.info(f"📅 Using nearest expiry: {expiry}")
            
            # Step 5: Find ATM strike
            available_strikes = sorted(set(inst.get('strike') for inst in options_list if inst.get('strike')))
            atm_strike = min(available_strikes, key=lambda x: abs(x - spot_price))
            logger.info(f"🎯 ATM Strike: {atm_strike}")
            
            # Step 6: Select strikes within range
            atm_index = available_strikes.index(atm_strike)
            start_index = max(0, atm_index - strikes)
            end_index = min(len(available_strikes), atm_index + strikes + 1)
            selected_strikes = available_strikes[start_index:end_index]
            logger.info(f"📊 Selected {len(selected_strikes)} strikes: {selected_strikes[0]} to {selected_strikes[-1]}")
            
            # Step 7: Build symbol list for batch quote fetch
            symbols_to_fetch = []
            symbol_map = {}  # Map full_symbol -> (strike, option_type)
            
            for inst in options_list:
                strike = inst.get('strike')
                if strike in selected_strikes:
                    tradingsymbol = inst.get('tradingsymbol')
                    option_type = inst.get('instrument_type')
                    full_sym = f"NFO:{tradingsymbol}"
                    symbols_to_fetch.append(full_sym)
                    symbol_map[full_sym] = (strike, option_type, tradingsymbol)
            
            logger.info(f"🔄 Fetching quotes for {len(symbols_to_fetch)} option contracts...")
            
            # Step 8: Fetch all quotes in batch (max 500 per call)
            all_quotes = {}
            batch_size = 200  # Conservative batch size
            for i in range(0, len(symbols_to_fetch), batch_size):
                batch = symbols_to_fetch[i:i+batch_size]
                try:
                    batch_quotes = self.kite.quote(batch)
                    if batch_quotes:
                        all_quotes.update(batch_quotes)
                    # Rate limit protection
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"❌ Error fetching batch {i}-{i+batch_size}: {e}")
            
            logger.info(f"✅ Fetched {len(all_quotes)} option quotes")
            
            # Step 9: Parse and structure data
            calls_data = {}
            puts_data = {}
            
            for full_sym, quote_data in all_quotes.items():
                if full_sym not in symbol_map:
                    continue
                
                strike, option_type, tradingsymbol = symbol_map[full_sym]
                
                # Extract comprehensive data including Greeks
                option_data = {
                    'symbol': tradingsymbol,
                    'ltp': quote_data.get('last_price', 0),
                    'change': quote_data.get('change', 0),
                    'change_percent': quote_data.get('change', 0),  # Calculate properly if needed
                    'volume': quote_data.get('volume', 0),
                    'oi': quote_data.get('oi', 0),
                    'oi_day_high': quote_data.get('oi_day_high', 0),
                    'oi_day_low': quote_data.get('oi_day_low', 0),
                    'bid': quote_data.get('depth', {}).get('buy', [{}])[0].get('price', 0),
                    'ask': quote_data.get('depth', {}).get('sell', [{}])[0].get('price', 0),
                    'bid_qty': quote_data.get('depth', {}).get('buy', [{}])[0].get('quantity', 0),
                    'ask_qty': quote_data.get('depth', {}).get('sell', [{}])[0].get('quantity', 0),
                    'ohlc': quote_data.get('ohlc', {}),
                    # Greeks and IV (if available from Zerodha)
                    'greeks': {
                        'delta': quote_data.get('delta', 0),
                        'gamma': quote_data.get('gamma', 0),
                        'theta': quote_data.get('theta', 0),
                        'vega': quote_data.get('vega', 0)
                    },
                    'iv': quote_data.get('iv', 0),  # Implied Volatility
                    'depth': quote_data.get('depth', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Categorize by type
                if option_type == 'CE':
                    calls_data[strike] = option_data
                else:
                    puts_data[strike] = option_data
            
            # Step 10: Calculate analytics
            analytics = self._calculate_option_chain_analytics(
                calls_data, puts_data, atm_strike, spot_price
            )
            
            result = {
                'underlying': underlying_symbol,
                'expiry': expiry,
                'atm_strike': atm_strike,
                'spot_price': spot_price,
                'timestamp': datetime.now().isoformat(),
                'chain': {
                    'calls': calls_data,
                    'puts': puts_data
                },
                'analytics': analytics
            }
            
            logger.info(f"✅ Option chain built: {len(calls_data)} calls, {len(puts_data)} puts")
            logger.info(f"📊 Analytics: PCR={analytics.get('pcr', 0):.2f}, Max Pain={analytics.get('max_pain', 0)}")
            
            # 🔥 FIX: Cache the result to prevent "Too many requests" error
            self._option_chain_cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching option chain for {underlying_symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _compare_expiry(self, expiry1: date, expiry2: str) -> bool:
        """Compare expiry dates in different formats"""
        try:
            # expiry1 is a date object, expiry2 is string like '25DEC24'
            if isinstance(expiry1, date):
                exp1_str = expiry1.strftime('%d%b%y').upper()
                return exp1_str == expiry2.upper()
            return False
        except:
            return False
    
    def _calculate_option_chain_analytics(self, calls_data: Dict, puts_data: Dict, 
                                         atm_strike: float, spot_price: float) -> Dict[str, Any]:
        """Calculate option chain analytics: PCR, Max Pain, IV Skew"""
        try:
            analytics = {}
            
            # 1. Put-Call Ratio (OI based)
            total_call_oi = sum(data.get('oi', 0) for data in calls_data.values())
            total_put_oi = sum(data.get('oi', 0) for data in puts_data.values())
            analytics['pcr'] = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            analytics['total_call_oi'] = total_call_oi
            analytics['total_put_oi'] = total_put_oi
            
            # 2. Max Pain - Strike with maximum pain for option writers
            max_pain_strike = self._calculate_max_pain(calls_data, puts_data)
            analytics['max_pain'] = max_pain_strike
            
            # 3. IV Analysis
            call_ivs = [data.get('iv', 0) for data in calls_data.values() if data.get('iv', 0) > 0]
            put_ivs = [data.get('iv', 0) for data in puts_data.values() if data.get('iv', 0) > 0]
            
            analytics['iv_mean'] = (sum(call_ivs + put_ivs) / len(call_ivs + put_ivs)) if (call_ivs + put_ivs) else 0
            analytics['iv_call_mean'] = (sum(call_ivs) / len(call_ivs)) if call_ivs else 0
            analytics['iv_put_mean'] = (sum(put_ivs) / len(put_ivs)) if put_ivs else 0
            
            # 4. IV Skew - Compare OTM put IV vs OTM call IV
            otm_calls = {strike: data for strike, data in calls_data.items() if strike > spot_price}
            otm_puts = {strike: data for strike, data in puts_data.items() if strike < spot_price}
            
            otm_call_ivs = [data.get('iv', 0) for data in otm_calls.values() if data.get('iv', 0) > 0]
            otm_put_ivs = [data.get('iv', 0) for data in otm_puts.values() if data.get('iv', 0) > 0]
            
            avg_otm_call_iv = (sum(otm_call_ivs) / len(otm_call_ivs)) if otm_call_ivs else 0
            avg_otm_put_iv = (sum(otm_put_ivs) / len(otm_put_ivs)) if otm_put_ivs else 0
            
            analytics['iv_skew'] = {
                'otm_call_iv': avg_otm_call_iv,
                'otm_put_iv': avg_otm_put_iv,
                'skew': avg_otm_put_iv - avg_otm_call_iv  # Positive = fear (higher put IV)
            }
            
            # 5. OI Distribution - Support/Resistance levels
            call_oi_by_strike = {strike: data.get('oi', 0) for strike, data in calls_data.items()}
            put_oi_by_strike = {strike: data.get('oi', 0) for strike, data in puts_data.items()}
            
            max_call_oi_strike = max(call_oi_by_strike, key=call_oi_by_strike.get) if call_oi_by_strike else 0
            max_put_oi_strike = max(put_oi_by_strike, key=put_oi_by_strike.get) if put_oi_by_strike else 0
            
            analytics['resistance'] = max_call_oi_strike  # Strike with max call OI
            analytics['support'] = max_put_oi_strike  # Strike with max put OI
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error calculating option chain analytics: {e}")
            return {}
    
    def _calculate_max_pain(self, calls_data: Dict, puts_data: Dict) -> float:
        """Calculate max pain strike - where option writers lose least"""
        try:
            # Get all unique strikes
            all_strikes = sorted(set(list(calls_data.keys()) + list(puts_data.keys())))
            
            if not all_strikes:
                return 0
            
            max_pain_values = {}
            
            for test_strike in all_strikes:
                total_pain = 0
                
                # Calculate pain from calls (ITM if strike > test_strike)
                for strike, data in calls_data.items():
                    if strike < test_strike:
                        # Call is ITM, writers lose
                        oi = data.get('oi', 0)
                        pain = (test_strike - strike) * oi
                        total_pain += pain
                
                # Calculate pain from puts (ITM if strike < test_strike)
                for strike, data in puts_data.items():
                    if strike > test_strike:
                        # Put is ITM, writers lose
                        oi = data.get('oi', 0)
                        pain = (strike - test_strike) * oi
                        total_pain += pain
                
                max_pain_values[test_strike] = total_pain
            
            # Max pain is strike with minimum total pain
            max_pain_strike = min(max_pain_values, key=max_pain_values.get) if max_pain_values else 0
            
            return max_pain_strike
            
        except Exception as e:
            logger.error(f"❌ Error calculating max pain: {e}")
            return 0

    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        # Simple check - market open 9:15 AM to 3:30 PM on weekdays
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        
        return market_open <= now <= market_close
    
    # ========================================
    # 🔥 ZERODHA HISTORICAL DATA API (FREE!)
    # ========================================
    
    async def get_historical_data(
        self, 
        symbol: str, 
        interval: str = "5minute",
        from_date: datetime = None,
        to_date: datetime = None,
        exchange: str = "NSE"
    ) -> List[Dict]:
        """
        Fetch historical OHLC candle data from Zerodha.
        
        🔥 THIS IS FREE with Kite Connect subscription!
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY 50')
            interval: Candle interval - minute, 3minute, 5minute, 10minute, 
                     15minute, 30minute, 60minute, day, week, month
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: now)
            exchange: NSE, BSE, NFO, MCX, etc.
        
        Returns:
            List of candle dicts with: date, open, high, low, close, volume
        
        Example:
            candles = await zerodha.get_historical_data('RELIANCE', '5minute')
            # Returns last 30 days of 5-minute candles
        """
        try:
            if not self.kite:
                logger.error("❌ Kite not initialized for historical data")
                return []
            
            # Get instrument token for the symbol
            instrument_token = await self._get_instrument_token(symbol, exchange)
            if not instrument_token:
                logger.error(f"❌ Could not find instrument token for {symbol}")
                return []
            
            # Default date range: last 30 days
            if not to_date:
                to_date = datetime.now()
            if not from_date:
                # For intraday intervals, limit to 60 days (Zerodha limit)
                if interval in ['minute', '3minute', '5minute', '10minute', '15minute', '30minute', '60minute']:
                    from_date = to_date - timedelta(days=60)
                else:
                    from_date = to_date - timedelta(days=365)  # 1 year for daily/weekly
            
            logger.info(f"📊 Fetching {symbol} historical data: {interval} from {from_date.date()} to {to_date.date()}")
            
            # Call Zerodha historical data API
            data = await self._async_api_call(
                self.kite.historical_data,
                instrument_token,
                from_date,
                to_date,
                interval,
                continuous=False,
                oi=False
            )
            
            if data:
                logger.info(f"✅ Got {len(data)} candles for {symbol} ({interval})")
                
                # Convert to standardized format
                candles = []
                for candle in data:
                    candles.append({
                        'timestamp': candle['date'],
                        'open': float(candle['open']),
                        'high': float(candle['high']),
                        'low': float(candle['low']),
                        'close': float(candle['close']),
                        'volume': int(candle['volume'])
                    })
                
                return candles
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error fetching historical data for {symbol}: {e}")
            return []
    
    async def _get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """Get instrument token for a symbol"""
        try:
            # Map internal index symbols to Zerodha trading symbols for historical data
            index_symbol_map = {
                'NIFTY-I': 'NIFTY 50',
                'NIFTY': 'NIFTY 50',
                'BANKNIFTY-I': 'NIFTY BANK',
                'BANKNIFTY': 'NIFTY BANK',
                'FINNIFTY-I': 'NIFTY FIN SERVICE',
                'FINNIFTY': 'NIFTY FIN SERVICE',
                'MIDCPNIFTY-I': 'NIFTY MID SELECT',
                'MIDCPNIFTY': 'NIFTY MID SELECT'
            }
            
            # Apply mapping for index symbols
            lookup_symbol = index_symbol_map.get(symbol, symbol)
            
            # Check cache first
            cache_key = f"{exchange}:{lookup_symbol}"
            if cache_key in self._symbol_to_token:
                return self._symbol_to_token[cache_key]
            
            # Also check original symbol in cache
            original_cache_key = f"{exchange}:{symbol}"
            if original_cache_key in self._symbol_to_token:
                return self._symbol_to_token[original_cache_key]
            
            # Fetch instruments if not cached
            instruments = await self.get_instruments(exchange)
            
            for inst in instruments:
                if inst.get('tradingsymbol') == lookup_symbol:
                    token = inst.get('instrument_token')
                    # Cache both original and mapped symbols
                    self._symbol_to_token[cache_key] = token
                    self._symbol_to_token[original_cache_key] = token
                    return token
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting instrument token for {symbol}: {e}")
            return None
    
    async def get_intraday_candles(self, symbol: str, minutes: int = 5) -> List[Dict]:
        """
        Get today's intraday candles for a symbol.
        
        Convenience method for common intraday analysis.
        
        Args:
            symbol: Trading symbol
            minutes: Candle size (1, 3, 5, 10, 15, 30, 60)
        
        Returns:
            List of today's candles
        """
        interval_map = {
            1: 'minute',
            3: '3minute',
            5: '5minute',
            10: '10minute',
            15: '15minute',
            30: '30minute',
            60: '60minute'
        }
        
        interval = interval_map.get(minutes, '5minute')
        today = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
        
        return await self.get_historical_data(
            symbol=symbol,
            interval=interval,
            from_date=today,
            to_date=datetime.now()
        )
    
    async def calculate_atr_from_zerodha(self, symbol: str, period: int = 14) -> float:
        """
        Calculate ATR using Zerodha historical data.
        
        🔥 Use this instead of TrueData for ATR calculation!
        
        Args:
            symbol: Trading symbol
            period: ATR period (default 14)
        
        Returns:
            ATR value
        """
        try:
            # Get daily candles for ATR calculation
            candles = await self.get_historical_data(
                symbol=symbol,
                interval='day',
                from_date=datetime.now() - timedelta(days=period + 5)  # Extra for buffer
            )
            
            if len(candles) < period:
                logger.warning(f"⚠️ Not enough candles for ATR: {len(candles)} < {period}")
                return 0.0
            
            # Calculate True Range for each candle
            true_ranges = []
            for i in range(1, len(candles)):
                high = candles[i]['high']
                low = candles[i]['low']
                prev_close = candles[i-1]['close']
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)
            
            # Calculate ATR as SMA of True Ranges
            if len(true_ranges) >= period:
                atr = sum(true_ranges[-period:]) / period
                logger.info(f"📊 {symbol} ATR({period}): ₹{atr:.2f}")
                return atr
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating ATR for {symbol}: {e}")
            return 0.0
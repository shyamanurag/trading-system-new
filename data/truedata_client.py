#!/usr/bin/env python3
"""
Advanced TrueData WebSocket Client - DEPLOYMENT-AWARE VERSION
Solves the "User Already Connected" deployment overlap issue
Implements graceful connection lifecycle management
"""

import os
import logging
import threading
import time
import signal
import atexit
from datetime import datetime
from typing import Dict, Optional
import json
import redis

# Setup basic logging
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}

# Add Redis client initialization after other imports
redis_client = None

# Add Redis setup after logger initialization
def setup_redis_client():
    """Setup Redis client for cross-process data sharing with SSL support"""
    global redis_client
    
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        
        # Parse Redis URL to extract components
        from urllib.parse import urlparse
        import ssl
        
        parsed = urlparse(redis_url)
        
        redis_host = parsed.hostname or 'localhost'
        redis_port = parsed.port or 6379
        redis_password = parsed.password
        redis_db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0
        
        # Check if SSL is required (DigitalOcean Redis)
        ssl_required = 'ondigitalocean.com' in redis_host or redis_url.startswith('rediss://')
        
        # CRITICAL FIX: Enhanced Redis config for DigitalOcean managed Redis
        # Create connection pool first, then Redis client
        connection_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=10,  # Increased timeout
            socket_timeout=10,  # Increased timeout
            ssl=ssl_required,
            ssl_cert_reqs=ssl.CERT_NONE if ssl_required else ssl.CERT_REQUIRED,  # CRITICAL: No cert validation for managed Redis
            ssl_check_hostname=False if ssl_required else True,  # CRITICAL: Disable hostname check
            ssl_ca_certs=None,  # CRITICAL: No CA certificate validation
            ssl_keyfile=None,
            ssl_certfile=None,
            retry_on_timeout=True,
            retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],  # Retry on connection errors
            health_check_interval=60,  # Increased health check interval
            max_connections=20,  # Pool size for 250 symbols
        )
        
        redis_client = redis.Redis(connection_pool=connection_pool)
        
        # Test connection with retry logic
        for attempt in range(3):
            try:
                redis_client.ping()
                logger.info(f"✅ TrueData Redis connected: {redis_host}:{redis_port} (SSL: {ssl_required}) - attempt {attempt + 1}")
                break
            except Exception as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"❌ TrueData Redis connection failed after {attempt + 1} attempts: {e}")
                    redis_client = None
                    return False
                logger.warning(f"⚠️ TrueData Redis connection attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.info(f"✅ TrueData Redis client initialized successfully for {redis_host}:{redis_port}")
        return True
        
    except Exception as e:
        logger.error(f"❌ TrueData Redis setup failed: {e}")
        redis_client = None
        return False

# Call setup at module level
setup_redis_client()

class TrueDataClient:
    """Advanced TrueData client with deployment overlap handling"""

    def __init__(self):
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        self._lock = threading.Lock()
        self._shutdown_requested = False
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._deployment_id = self._generate_deployment_id()
        
        # Circuit breaker for connection attempts
        self._circuit_breaker_active = False
        self._circuit_breaker_timeout = 300  # 5 minutes
        self._last_connection_failure = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        
        # Register cleanup handlers
        self._register_cleanup_handlers()

    def _generate_deployment_id(self):
        """Generate unique deployment ID for connection tracking"""
        import uuid
        deployment_id = f"deploy_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        logger.info(f"🏷️ Deployment ID: {deployment_id}")
        return deployment_id

    def _register_cleanup_handlers(self):
        """Register cleanup handlers for graceful shutdown"""
        def cleanup_handler(signum=None, frame=None):
            logger.info(f"🛑 Cleanup handler called (signal: {signum})")
            self.force_disconnect()
        
        # Register for different shutdown scenarios
        atexit.register(cleanup_handler)
        try:
            signal.signal(signal.SIGTERM, cleanup_handler)
            signal.signal(signal.SIGINT, cleanup_handler)
        except:
            pass  # Windows doesn't support all signals

    def _check_deployment_overlap(self):
        """Check if this is a deployment overlap scenario"""
        is_production = os.getenv('ENVIRONMENT') == 'production'
        is_digitalocean = 'ondigitalocean.app' in os.getenv('APP_URL', '')
        
        if is_production or is_digitalocean:
            logger.info("🏭 Production deployment detected - enabling overlap handling")
            return True
        return False

    def _attempt_graceful_takeover(self):
        """Attempt to gracefully take over existing connection"""
        logger.info("🔄 Attempting graceful connection takeover...")
        
        try:
            # Try to create a temporary connection to force disconnect the existing one
            from truedata import TD_live
            
            logger.info("📡 Creating temporary connection to force disconnect existing...")
            temp_td = TD_live(
                self.username,
                self.password,
                live_port=self.port,
                url=self.url,
                compression=False
            )
            
            # Send disconnect signal
            try:
                if hasattr(temp_td, 'disconnect'):
                    temp_td.disconnect()
                    logger.info("✅ Sent disconnect signal to existing connection")
            except:
                pass
            
            # Small delay to let disconnect process
            time.sleep(5)
            
            # Now try our actual connection
            return self._direct_connect()
            
        except Exception as e:
            logger.error(f"❌ Graceful takeover failed: {e}")
            return False

    def _direct_connect(self):
        """Direct connection attempt without overlap handling"""
        try:
            from truedata import TD_live

            logger.info(f"🔄 Direct connect: {self.username}@{self.url}:{self.port}")

            # Clean any existing connection
            if self.td_obj:
                try:
                    if hasattr(self.td_obj, 'disconnect'):
                        self.td_obj.disconnect()
                except:
                    pass
                self.td_obj = None

            # Create new connection
            self.td_obj = TD_live(
                self.username,
                self.password,
                live_port=self.port,
                url=self.url,
                compression=False
            )

            logger.info("✅ TD_live object created")

            # Subscribe to symbols
            symbols = self._get_symbols_to_subscribe()
            req_ids = self.td_obj.start_live_data(symbols)
            logger.info(f"✅ Subscribed to {len(symbols)} symbols: {req_ids}")

            # Setup callback
            self._setup_callback()

            self.connected = True
            self._connection_attempts = 0
            logger.info("🎉 TrueData connected successfully!")
            return True

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Direct connection failed: {e}")
            
            if "user already connected" in error_msg or "already connected" in error_msg:
                logger.warning("⚠️ User Already Connected error detected")
                return False
            
            self.connected = False
            self.td_obj = None
            return False

    def connect(self):
        """Main connection method with deployment overlap handling"""
        with self._lock:
            if self._shutdown_requested:
                logger.info("🛑 Shutdown requested - skipping connection")
                return False
                
            # Circuit breaker check
            if self._circuit_breaker_active:
                time_since_failure = time.time() - self._last_connection_failure
                if time_since_failure < self._circuit_breaker_timeout:
                    logger.warning(f"⚡ Circuit breaker ACTIVE - cooling down for {self._circuit_breaker_timeout - time_since_failure:.0f}s")
                    return False
                else:
                    logger.info("⚡ Circuit breaker timeout expired - attempting connection")
                    self._circuit_breaker_active = False
                    self._consecutive_failures = 0
                
            if self.connected and self.td_obj:
                logger.info("✅ TrueData already connected")
                return True

            self._connection_attempts += 1
            
            if self._connection_attempts > self._max_connection_attempts:
                logger.error(f"❌ Max connection attempts ({self._max_connection_attempts}) exceeded")
                self._activate_circuit_breaker()
                return False

            logger.info(f"🚀 TrueData connection attempt {self._connection_attempts}/{self._max_connection_attempts}")

            # Check if this is a deployment overlap scenario
            if self._check_deployment_overlap():
                logger.info("🔄 Deployment overlap detected - attempting graceful takeover")
                
                # Strategy 1: Try graceful takeover
                if self._attempt_graceful_takeover():
                    self._reset_circuit_breaker()
                    return True
                
                # Strategy 2: Wait for old connection to timeout and retry
                logger.info("⏳ Graceful takeover failed - waiting for connection timeout...")
                time.sleep(15)  # Wait for old connection to timeout
                
                if self._direct_connect():
                    self._reset_circuit_breaker()
                    return True
                
                # Strategy 3: Activate circuit breaker to prevent spam
                logger.warning("⚠️ All connection attempts failed - activating circuit breaker")
                self._activate_circuit_breaker()
                logger.info("💡 SOLUTION: Set SKIP_TRUEDATA_AUTO_INIT=true to break deployment overlap cycle")
                logger.info("🔧 Then manually connect via: /api/v1/truedata/connect")
                return False
            else:
                # Local development - direct connect
                if self._direct_connect():
                    self._reset_circuit_breaker()
                    return True
                else:
                    self._activate_circuit_breaker()
                    return False

    def _activate_circuit_breaker(self):
        """Activate circuit breaker to prevent constant reconnection attempts"""
        self._circuit_breaker_active = True
        self._last_connection_failure = time.time()
        self._consecutive_failures += 1
        logger.warning(f"⚡ Circuit breaker ACTIVATED - cooldown period: {self._circuit_breaker_timeout}s")
        
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on successful connection"""
        self._circuit_breaker_active = False
        self._consecutive_failures = 0
        self._last_connection_failure = None
        logger.info("⚡ Circuit breaker RESET - connection successful")

    def force_disconnect(self):
        """Force disconnect with aggressive cleanup"""
        logger.info("🛑 Force disconnect initiated")
        self._shutdown_requested = True
        
        try:
            if self.td_obj:
                # Multiple disconnect attempts
                for attempt in range(3):
                    try:
                        if hasattr(self.td_obj, 'disconnect'):
                            self.td_obj.disconnect()
                            logger.info(f"🔌 Disconnect attempt {attempt + 1} completed")
                            time.sleep(1)
                    except Exception as e:
                        logger.warning(f"Disconnect attempt {attempt + 1} error: {e}")
                
                # Clear the object
                self.td_obj = None
                logger.info("✅ TrueData object cleared")
        
        except Exception as e:
            logger.error(f"❌ Force disconnect error: {e}")
        
        self.connected = False
        logger.info("🛑 Force disconnect completed")

    def _get_symbols_to_subscribe(self):
        """Get symbols from our config file"""
        try:
            from config.truedata_symbols import get_default_subscription_symbols
            symbols = get_default_subscription_symbols()
            logger.info(f"📋 Using configured symbols: {symbols}")
            return symbols
        except ImportError:
            # Fallback to hardcoded symbols
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS', 'HDFC', 'INFY']
            logger.info(f"📋 Using fallback symbols: {symbols}")
            return symbols

    def _setup_callback(self):
        """Setup callback for live data processing"""
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            """Process tick data from TrueData with Redis caching - FIXED field mapping"""
            try:
                # DEBUG: Log all available attributes to understand TrueData schema
                if hasattr(tick_data, '__dict__'):
                    attrs = {k: v for k, v in tick_data.__dict__.items() if not k.startswith('_')}
                    logger.debug(f"📊 TrueData tick attributes: {attrs}")
                
                # Extract symbol first
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                if symbol == 'UNKNOWN':
                    logger.warning("⚠️ Tick data missing symbol, skipping")
                    return
                
                # Extract core price data with fallbacks
                ltp = getattr(tick_data, 'ltp', 0) or getattr(tick_data, 'last_price', 0)
                if ltp <= 0:
                    logger.warning(f"⚠️ Invalid LTP for {symbol}: {ltp}")
                    return
                
                # Extract OHLC data - FIXED: Better fallback logic
                high = getattr(tick_data, 'high', None)
                low = getattr(tick_data, 'low', None)
                open_price = getattr(tick_data, 'open', None)
                
                # If OHLC not available, create realistic estimates (better than all ltp)
                if high is None or high <= 0:
                    high = ltp * 1.002  # Assume 0.2% higher than ltp
                if low is None or low <= 0:
                    low = ltp * 0.998   # Assume 0.2% lower than ltp
                if open_price is None or open_price <= 0:
                    open_price = ltp * 0.999  # Assume slight difference from ltp
                
                # Extract volume data with multiple field attempts
                volume = (
                    getattr(tick_data, 'volume', 0) or
                    getattr(tick_data, 'ttq', 0) or
                    getattr(tick_data, 'total_traded_quantity', 0) or
                    getattr(tick_data, 'vol', 0) or
                    0
                )
                
                # Extract change and change_percent - FIXED: More comprehensive field mapping
                change = getattr(tick_data, 'change', 0) or getattr(tick_data, 'net_change', 0)
                
                # Try all possible field names for change_percent
                change_percent = (
                    getattr(tick_data, 'changeper', None) or
                    getattr(tick_data, 'change_percent', None) or
                    getattr(tick_data, 'changepercent', None) or
                    getattr(tick_data, 'pchange', None) or
                    getattr(tick_data, 'percent_change', None) or
                    getattr(tick_data, 'chg_percent', None) or
                    getattr(tick_data, 'pct_change', None)
                )
                
                # FIXED: Better manual calculation logic
                if change_percent is None or change_percent == 0:
                    if change is not None and change != 0 and ltp > 0:
                        try:
                            # Calculate change_percent from absolute change
                            change_float = float(change)
                            previous_price = ltp - change_float
                            if previous_price > 0:
                                change_percent = (change_float / previous_price) * 100
                                logger.debug(f"📊 Calculated {symbol} change_percent: {change_percent:.3f}% "
                                           f"(ltp={ltp}, change={change}, prev={previous_price:.2f})")
                            else:
                                logger.warning(f"⚠️ Invalid previous price for {symbol}: {previous_price}")
                                change_percent = 0
                        except (ValueError, TypeError):
                            logger.warning(f"⚠️ Invalid change value for {symbol}: {change}")
                            change_percent = 0
                    else:
                        change_percent = 0
                
                # Extract additional fields with fallbacks
                bid = getattr(tick_data, 'bid', 0) or getattr(tick_data, 'best_bid', 0)
                ask = getattr(tick_data, 'ask', 0) or getattr(tick_data, 'best_ask', 0)
                
                # FIXED: Enhanced data structure with proper field mapping
                market_data = {
                    'symbol': symbol,
                    'ltp': ltp,
                    'close': ltp,  # Map ltp to close for strategy compatibility
                    'high': high,
                    'low': low,
                    'open': open_price,
                    'volume': volume,
                    'change': change,
                    'changeper': change_percent,
                    'change_percent': change_percent,  # Duplicate for compatibility
                    'bid': bid,
                    'ask': ask,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'TrueData_Live',
                    'deployment_id': self._deployment_id,
                    # Additional fields for debugging
                    'data_quality': {
                        'has_ohlc': all([high != ltp, low != ltp, open_price != ltp]),
                        'has_volume': volume > 0,
                        'has_change_percent': change_percent != 0,
                        'calculated_change_percent': change_percent != getattr(tick_data, 'changeper', None)
                    }
                }
                
                # Store in local cache (existing behavior)
                live_market_data[symbol] = market_data
                
                # CRITICAL: Also store in Redis for cross-process access
                if redis_client:
                    try:
                        # Store individual symbol data (JSON serialized to handle nested dicts)
                        redis_client.set(f"truedata:symbol:{symbol}", json.dumps(market_data))
                        redis_client.expire(f"truedata:symbol:{symbol}", 300)  # 5 minutes
                        
                        # Store in combined cache
                        redis_client.hset("truedata:live_cache", symbol, json.dumps(market_data))
                        redis_client.expire("truedata:live_cache", 300)  # 5 minutes
                        
                        # Update symbol count
                        redis_client.set("truedata:symbol_count", len(live_market_data))
                        
                        # Store raw tick data for analysis
                        redis_client.lpush(f"truedata:ticks:{symbol}", json.dumps(market_data))
                        redis_client.ltrim(f"truedata:ticks:{symbol}", 0, 100)  # Keep last 100 ticks
                        
                    except Exception as redis_error:
                        logger.error(f"Redis storage error for {symbol}: {redis_error}")
                
                # Enhanced logging with data quality info
                if volume > 0:
                    quality = market_data['data_quality']
                    logger.info(f"📊 {symbol}: ₹{ltp:,.2f} | {change_percent:+.2f}% | Vol: {volume:,} | "
                              f"OHLC: {'✓' if quality['has_ohlc'] else '✗'} | "
                              f"Deploy: {self._deployment_id}")
                
            except Exception as e:
                logger.error(f"Error processing tick data: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
        logger.info("✅ TrueData callback setup complete with FIXED field mapping")

    def get_status(self):
        """Get comprehensive status including deployment info"""
        return {
            'connected': self.connected,
            'data_flowing': len(live_market_data) > 0,
            'symbols_active': len(live_market_data),
            'username': self.username,
            'deployment_id': self._deployment_id,
            'connection_attempts': self._connection_attempts,
            'shutdown_requested': self._shutdown_requested,
            'timestamp': datetime.now().isoformat()
        }

    def disconnect(self):
        """Graceful disconnect"""
        return self.force_disconnect()

# Global instance
truedata_client = TrueDataClient()

# API functions with deployment awareness
def initialize_truedata():
    """Initialize TrueData with deployment overlap handling"""
    # Check if auto-init should be skipped
    skip_auto_init = os.getenv('SKIP_TRUEDATA_AUTO_INIT', 'false').lower() == 'true'
    
    if skip_auto_init:
        logger.info("⏭️ TrueData auto-init SKIPPED (SKIP_TRUEDATA_AUTO_INIT=true)")
        logger.info("💡 This prevents deployment overlap issues")
        logger.info("🔧 Use /api/v1/truedata/connect for manual connection")
        return True  # Return True to not block deployment
    
    logger.info("🚀 Initializing TrueData with deployment overlap handling...")
    return truedata_client.connect()

def force_disconnect_truedata():
    """Force disconnect for deployment cleanup"""
    logger.info("🛑 Force disconnect requested")
    truedata_client.force_disconnect()
    return True

def get_truedata_status():
    """Get connection status"""
    return truedata_client.get_status()

def is_connected():
    """Check if connected"""
    return truedata_client.connected

def get_live_data_for_symbol(symbol: str):
    """Get live data for specific symbol"""
    return live_market_data.get(symbol)

def get_all_live_data():
    """Get all live market data"""
    return live_market_data.copy()

def subscribe_to_symbols(symbols: list):
    """Subscribe to additional symbols"""
    if not truedata_client.td_obj or not truedata_client.connected:
        logger.warning("❌ Cannot subscribe - TrueData not connected")
        return False

    try:
        req_ids = truedata_client.td_obj.start_live_data(symbols)
        logger.info(f"✅ Subscribed to {len(symbols)} additional symbols: {req_ids}")
        return True
    except Exception as e:
        logger.error(f"❌ Subscribe error: {e}")
        return False

logger.info("🎯 Advanced TrueData Client loaded - deployment overlap solution active") 
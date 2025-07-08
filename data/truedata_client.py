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
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            ssl=ssl_required,
            ssl_cert_reqs=ssl.CERT_NONE if ssl_required else ssl.CERT_REQUIRED,
            ssl_check_hostname=False if ssl_required else True,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        redis_client.ping()
        logger.info(f"✅ TrueData Redis connected: {redis_host}:{redis_port} (SSL: {ssl_required})")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
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
            """Process tick data from TrueData with Redis caching"""
            try:
                # Extract symbol and data
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                ltp = getattr(tick_data, 'ltp', 0)
                volume = getattr(tick_data, 'volume', 0) or getattr(tick_data, 'ttq', 0)
                
                # Enhanced data structure for strategies
                market_data = {
                    'symbol': symbol,
                    'ltp': ltp,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat(),
                    'open': getattr(tick_data, 'open', ltp),
                    'high': getattr(tick_data, 'high', ltp),
                    'low': getattr(tick_data, 'low', ltp),
                    'close': ltp,
                    'change': getattr(tick_data, 'change', 0),
                    'changeper': getattr(tick_data, 'changeper', 0),
                    'change_percent': getattr(tick_data, 'changeper', 0),
                    'bid': getattr(tick_data, 'bid', 0),
                    'ask': getattr(tick_data, 'ask', 0),
                    'source': 'TrueData_Live',
                    'deployment_id': self._deployment_id
                }
                
                # Store in local cache (existing behavior)
                live_market_data[symbol] = market_data
                
                # CRITICAL: Also store in Redis for cross-process access
                if redis_client:
                    try:
                        # Store individual symbol data
                        redis_client.hset(f"truedata:symbol:{symbol}", mapping=market_data)
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
                
                # Log with deployment ID for debugging
                if volume > 0:
                    print(f"📊 {symbol}: ₹{ltp:,.2f} | Vol: {volume:,} | Deploy: {self._deployment_id}")
                
            except Exception as e:
                logger.error(f"Error processing tick data: {e}")
                
        logger.info("✅ TrueData callback setup complete with Redis caching")

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
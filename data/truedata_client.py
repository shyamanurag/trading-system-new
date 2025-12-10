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
from typing import Dict, Optional, List
import json
import redis

# Setup basic logging
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}

# Add connection status tracking
truedata_connection_status = {
    'connected': False,
    'last_connected': None,
    'error': None,
    'retry_disabled': False,
    'permanent_block': False,
    'deployment_id': os.environ.get('DEPLOYMENT_ID', 'unknown'),
    'connection_attempts': 0
}

# Add Redis client initialization after other imports
redis_client = None

# Add Redis setup after logger initialization
def setup_redis_client():
    """Setup Redis client for cross-process data sharing with simple config"""
    global redis_client
    
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        
        # Simple Redis client that works with all versions
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        # Test connection
        if redis_client:
            redis_client.ping()
            logger.info(f"✅ TrueData Redis connected: {redis_url[:50]}...")
        else:
            logger.warning("⚠️ Redis client is None")
        
    except Exception as e:
        logger.warning(f"⚠️ TrueData Redis connection failed: {e}")
        redis_client = None
        return False
    
    return True

# Call setup at module level
setup_redis_client()

def safe_json_serialize(obj, _depth=0, _seen=None):
    """Safely serialize objects to JSON with recursion and circular reference protection"""
    # CRITICAL FIX: Prevent infinite recursion
    MAX_DEPTH = 10
    if _depth > MAX_DEPTH:
        logger.warning(f"⚠️ Max serialization depth ({MAX_DEPTH}) exceeded")
        return str(obj)[:100]  # Truncate to prevent memory issues
    
    # CRITICAL FIX: Track seen objects to prevent circular references
    if _seen is None:
        _seen = set()
    
    try:
        # Handle datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        
        # Handle numeric types
        if isinstance(obj, (int, float)):
            return obj
        
        # Handle strings
        if isinstance(obj, str):
            return obj
        
        # Handle None
        if obj is None:
            return None
        
        # Handle lists and tuples
        if isinstance(obj, (list, tuple)):
            obj_id = id(obj)
            if obj_id in _seen:
                return "[CIRCULAR_REFERENCE]"
            _seen.add(obj_id)
            result = [safe_json_serialize(item, _depth + 1, _seen) for item in obj]
            _seen.discard(obj_id)
            return result
        
        # Handle dictionaries
        if isinstance(obj, dict):
            obj_id = id(obj)
            if obj_id in _seen:
                return {"error": "CIRCULAR_REFERENCE"}
            _seen.add(obj_id)
            result = {str(k): safe_json_serialize(v, _depth + 1, _seen) for k, v in obj.items()}
            _seen.discard(obj_id)
            return result
        
        # For other objects, convert to string representation
        return str(obj)[:200]  # Truncate long strings
        
    except RecursionError as re:
        logger.error(f"❌ RECURSION ERROR in safe_json_serialize: {re}")
        return "[RECURSION_ERROR]"
    except Exception as e:
        logger.warning(f"⚠️ JSON serialization error: {e}")
        return str(obj)[:100]

def create_safe_market_data(market_data):
    """Create a safe version of market data for Redis storage"""
    try:
        # Create a clean copy with only serializable data
        safe_data = {
            'symbol': str(market_data.get('symbol', '')),
            'truedata_symbol': str(market_data.get('truedata_symbol', '')),
            'ltp': float(market_data.get('ltp', 0)),
            'close': float(market_data.get('close', 0)),
            'previous_close': float(market_data.get('previous_close', 0)),  # 🎯 ADDED: Critical for dual-timeframe
            'high': float(market_data.get('high', 0)),
            'low': float(market_data.get('low', 0)),
            'open': float(market_data.get('open', 0)),
            'volume': float(market_data.get('volume', 0)),
            'change': float(market_data.get('change', 0)),
            'changeper': float(market_data.get('changeper', 0)),
            'change_percent': float(market_data.get('change_percent', 0)),
            'bid': float(market_data.get('bid', 0)),
            'ask': float(market_data.get('ask', 0)),
            'timestamp': str(market_data.get('timestamp', '')),
            'source': str(market_data.get('source', '')),
            'deployment_id': str(market_data.get('deployment_id', '')),
            'data_quality': {
                'has_ohlc': bool(market_data.get('data_quality', {}).get('has_ohlc', False)),
                'has_volume': bool(market_data.get('data_quality', {}).get('has_volume', False)),
                'has_change_percent': bool(market_data.get('data_quality', {}).get('has_change_percent', False)),
                'has_previous_close': bool(market_data.get('data_quality', {}).get('has_previous_close', False)),
                'calculated_change_percent': bool(market_data.get('data_quality', {}).get('calculated_change_percent', False))
            }
        }
        
        return safe_data
        
    except Exception as e:
        logger.error(f"❌ Error creating safe market data: {e}")
        # Return minimal safe data
        return {
            'symbol': str(market_data.get('symbol', '')),
            'ltp': 0.0,
            'timestamp': datetime.now().isoformat(),
            'error': 'Data serialization failed'
        }

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
        
        # Circuit breaker for connection attempts - IMPROVED for market closure
        self._circuit_breaker_active = False
        self._circuit_breaker_timeout = 60  # REDUCED: 1 minute during market closure instead of 5
        self._last_connection_failure = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3  # REDUCED: Be more aggressive about stopping attempts
        
        # Register cleanup handlers
        self._register_cleanup_handlers()

        # Background health monitor flags
        self._health_thread = None
        self._stop_health = threading.Event()

    def _generate_deployment_id(self):
        """Generate unique deployment ID for connection tracking"""
        import uuid
        deployment_id = f"deploy_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        logger.info(f"🏷️ Deployment ID: {deployment_id}")
        return deployment_id

    def _register_cleanup_handlers(self):
        """Register cleanup handlers for graceful shutdown - FIXED to not disconnect during market closure"""
        def cleanup_handler(signum=None, frame=None):
            logger.info(f"🛑 Cleanup handler called (signal: {signum})")
            
            # CRITICAL FIX: Only disconnect on actual shutdown signals, not during normal operation
            if signum in [signal.SIGTERM, signal.SIGINT] or frame is None:
                logger.info("🛑 Actual shutdown signal detected - disconnecting TrueData")
                self.force_disconnect()
            else:
                logger.info("ℹ️ Non-shutdown signal - maintaining TrueData connection for market closure")
        
        # Register for different shutdown scenarios
        atexit.register(cleanup_handler)
        try:
            signal.signal(signal.SIGTERM, cleanup_handler)
            signal.signal(signal.SIGINT, cleanup_handler)
        except:
            pass  # Windows doesn't support all signals

    def _check_deployment_overlap(self):
        """Check if this is a deployment overlap scenario - FIXED to reduce false positives"""
        is_production = os.getenv('ENVIRONMENT') == 'production'
        is_digitalocean = 'ondigitalocean.app' in os.getenv('APP_URL', '')
        
        # CRITICAL FIX: Only enable overlap handling during actual deployments, not normal operation
        skip_auto_init = os.getenv('SKIP_TRUEDATA_AUTO_INIT', 'false').lower() == 'true'
        
        if skip_auto_init:
            logger.info("⏭️ Deployment overlap handling DISABLED (SKIP_TRUEDATA_AUTO_INIT=true)")
            return False
        
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

            # Create new connection - CRITICAL FIX: Remove unsupported compression parameter
            self.td_obj = TD_live(
                self.username,
                self.password,
                live_port=self.port,
                url=self.url
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
            # Start health monitor after successful connect
            self._start_health_monitor()
            return True

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Direct connection failed: {e}")
            
            # 🚨 CRITICAL FIX: Detect subscription expired error and block further attempts
            if "subscription expired" in error_msg or "user subscription expired" in error_msg or "subscription" in error_msg:
                logger.error("❌ SUBSCRIPTION EXPIRED - Blocking reconnection attempts for 1 hour")
                logger.error("💡 Please renew your TrueData subscription")
                logger.error(f"📅 Subscription validity ended: Check TrueData portal")
                logger.error("🔄 System will use Zerodha-only mode for market data")
                # Set permanent block flag (will be auto-reset after timeout)
                truedata_connection_status['permanent_block'] = True
                truedata_connection_status['error'] = 'SUBSCRIPTION_EXPIRED'
                truedata_connection_status['retry_disabled'] = True
                self._circuit_breaker_active = True
                self._circuit_breaker_timeout = 3600  # 1 hour cooldown (will auto-retry after renewal)
                self.connected = False
                self.td_obj = None
                # Immediately disconnect to prevent recursion
                try:
                    if self.td_obj:
                        self.td_obj.disconnect()
                except:
                    pass
                return False
            
            if "user already connected" in error_msg or "already connected" in error_msg:
                logger.warning("⚠️ User Already Connected error detected - activating circuit breaker")
                logger.info("💡 TIP: This usually means another instance is connected. Wait 60s for auto-disconnect.")
                # Activate circuit breaker to prevent rapid reconnection attempts
                self._circuit_breaker_active = True
                self._circuit_breaker_timeout = 60  # 60 second cooldown
                self._last_connection_failure = time.time()
                self._consecutive_failures += 1
                truedata_connection_status['error'] = 'USER_ALREADY_CONNECTED'
                truedata_connection_status['retry_disabled'] = True
                return False
            
            self.connected = False
            self.td_obj = None
            return False

    def connect(self):
        """Main connection method with optimized deployment overlap handling"""
        with self._lock:
            if self._shutdown_requested:
                logger.info("🛑 Shutdown requested - skipping connection")
                return False
            
            # 🚨 CRITICAL: Check for permanent block (subscription expired)
            if truedata_connection_status.get('permanent_block', False):
                # Check if circuit breaker timeout has expired (subscription may be renewed)
                if self._circuit_breaker_active and self._last_connection_failure is not None:
                    time_since_failure = time.time() - self._last_connection_failure
                    if time_since_failure >= self._circuit_breaker_timeout:
                        logger.info("🔄 Circuit breaker timeout expired - attempting reconnection after potential subscription renewal")
                        # Reset block flags to allow retry
                        truedata_connection_status['permanent_block'] = False
                        truedata_connection_status['retry_disabled'] = False
                        self._circuit_breaker_active = False
                        self._consecutive_failures = 0
                    else:
                        logger.warning(f"❌ TrueData connection blocked - Subscription expired (retry in {(self._circuit_breaker_timeout - time_since_failure)/60:.0f} min)")
                        logger.info("💡 System using Zerodha-only mode for market data")
                        return False
                else:
                    logger.error("❌ TrueData connection BLOCKED - Subscription expired")
                    logger.error("💡 SOLUTION: Renew your TrueData subscription")
                    return False
                
            # Circuit breaker check
            if self._circuit_breaker_active:
                if self._last_connection_failure is not None:
                    time_since_failure = time.time() - self._last_connection_failure
                    if time_since_failure < self._circuit_breaker_timeout:
                        logger.warning(f"⚡ Circuit breaker ACTIVE - cooling down for {self._circuit_breaker_timeout - time_since_failure:.0f}s")
                        return False
                    else:
                        logger.info("⚡ Circuit breaker timeout expired - attempting connection")
                        self._circuit_breaker_active = False
                        self._consecutive_failures = 0
                else:
                    # If _last_connection_failure is None, reset circuit breaker
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
                logger.info("🔄 Deployment overlap detected - using optimized graceful takeover")
                
                # OPTIMIZED Strategy 1: Quick graceful takeover with shorter waits
                if self._attempt_optimized_takeover():
                    self._reset_circuit_breaker()
                    return True
                
                # OPTIMIZED Strategy 2: Reduced wait time for connection timeout
                logger.info("⏳ Quick takeover failed - waiting for connection timeout (optimized)...")
                time.sleep(5)  # Reduced from 15 seconds
                
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

    def _attempt_optimized_takeover(self):
        """Optimized graceful takeover with faster timeouts"""
        logger.info("🔄 Attempting optimized graceful connection takeover...")
        
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
            
            # OPTIMIZED: Shorter delay for faster takeover
            time.sleep(2)  # Reduced from 5 seconds
            
            # Now try our actual connection
            return self._direct_connect()
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Optimized graceful takeover failed: {e}")
            
            # 🚨 CRITICAL: Check for subscription expired during takeover
            if "subscription expired" in error_msg or "user subscription expired" in error_msg:
                logger.error("❌ SUBSCRIPTION EXPIRED detected during takeover")
                truedata_connection_status['permanent_block'] = True
                truedata_connection_status['error'] = 'SUBSCRIPTION_EXPIRED'
                self._circuit_breaker_active = True
                self._circuit_breaker_timeout = 3600  # 1 hour cooldown
            
            return False

    def _activate_circuit_breaker(self):
        """Activate circuit breaker to prevent constant reconnection attempts"""
        self._circuit_breaker_active = True
        self._last_connection_failure = time.time()
        self._consecutive_failures += 1
        
        # CRITICAL FIX: Shorter circuit breaker timeout during market closure
        current_hour = datetime.now().hour
        is_market_hours = 9 <= current_hour <= 15  # Approximate market hours
        
        if is_market_hours:
            timeout = self._circuit_breaker_timeout  # 5 minutes during market hours
        else:
            timeout = 60  # 1 minute during market closure
            logger.info("📊 Market closed - using shorter circuit breaker timeout")
        
        logger.warning(f"⚡ Circuit breaker ACTIVATED - cooldown period: {timeout}s")
        self._circuit_breaker_timeout = timeout
        
    def reset_circuit_breaker_manual(self):
        """Manual circuit breaker reset for market closure periods"""
        self._circuit_breaker_active = False
        self._consecutive_failures = 0
        self._last_connection_failure = None
        self._connection_attempts = 0
        logger.info("⚡ Circuit breaker MANUALLY RESET - connection attempts cleared")
        return True

    def _reset_circuit_breaker(self):
        """Reset circuit breaker state"""
        self._circuit_breaker_active = False
        self._consecutive_failures = 0
        self._last_connection_failure = None
        logger.info("⚡ Circuit breaker RESET - connection attempts enabled")

    def manual_circuit_breaker_reset(self):
        """Manually reset circuit breaker - useful during market closure or health checks"""
        logger.info("🔧 MANUAL circuit breaker reset requested")
        self._reset_circuit_breaker()
        return True

    def get_detailed_status(self):
        """Get detailed status including circuit breaker state"""
        current_time = time.time()
        circuit_breaker_remaining = 0
        
        if self._circuit_breaker_active and self._last_connection_failure:
            circuit_breaker_remaining = max(0, self._circuit_breaker_timeout - (current_time - self._last_connection_failure))
        
        return {
            'connected': self.connected,
            'data_flowing': len(live_market_data) > 0,
            'symbols_active': len(live_market_data),
            'username': self.username,
            'deployment_id': self._deployment_id,
            'connection_attempts': self._connection_attempts,
            'shutdown_requested': self._shutdown_requested,
            'circuit_breaker_active': self._circuit_breaker_active,
            'circuit_breaker_remaining_seconds': circuit_breaker_remaining,
            'consecutive_failures': self._consecutive_failures,
            'last_failure_time': self._last_connection_failure,
            'market_data_symbols': list(live_market_data.keys())[:10],  # First 10 symbols
            'timestamp': datetime.now().isoformat()
        }

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
        # Stop health monitor
        try:
            self._stop_health.set()
        except Exception:
            pass
        logger.info("🛑 Force disconnect completed")

    def _start_health_monitor(self):
        """
        🎯 IMPROVED Health Monitor for TrueData
        - Better detection of ping/pong timeout issues
        - Exponential backoff for reconnection attempts
        - Separate handling for different failure types
        - Reduced logging noise
        """
        try:
            if self._health_thread and self._health_thread.is_alive():
                return
            self._stop_health.clear()

            def _monitor():
                last_ok = time.time()
                last_reconnect_attempt = 0
                reconnect_cooldown = 90  # 90 seconds base cooldown
                consecutive_silent_checks = 0
                max_silent_before_reconnect = 5  # 5 checks = ~15 seconds silence

                logger.info("🏥 TrueData Health Monitor started")

                while not self._stop_health.is_set():
                    try:
                        current_time = time.time()
                        current_hour = datetime.now().hour
                        in_market = 9 <= current_hour <= 15
                        
                        # Consider data healthy if ticks updated in last 10 seconds
                        recent_tick = False
                        try:
                            for symbol, data in live_market_data.items():
                                if isinstance(data, dict):
                                    ts = data.get('timestamp', '')
                                    if ts:
                                        try:
                                            tick_time = datetime.fromisoformat(ts).timestamp()
                                            if (current_time - tick_time) < 10:
                                                recent_tick = True
                                                break
                                        except:
                                            pass
                        except Exception:
                            pass
                        
                        if recent_tick:
                            last_ok = current_time
                            consecutive_silent_checks = 0
                        else:
                            if in_market:
                                consecutive_silent_checks += 1
                        
                        # Log health status every 5 minutes during market hours
                        if in_market and int(current_time) % 300 == 0:
                            symbols_count = len(live_market_data)
                            silence_secs = int(current_time - last_ok)
                            logger.info(f"🏥 TrueData Health: {symbols_count} symbols, last tick {silence_secs}s ago")
                        
                        # Handle tick silence during market hours
                        if (in_market and 
                            consecutive_silent_checks >= max_silent_before_reconnect and
                            (current_time - last_reconnect_attempt) > reconnect_cooldown):

                            silence_duration = int(current_time - last_ok)
                            logger.warning(f"⚠️ TrueData TICK SILENCE: {silence_duration}s - attempting recovery")
                            
                            try:
                                last_reconnect_attempt = current_time
                                
                                # Step 1: Try to refresh subscription first (less disruptive)
                                if self.td_obj and hasattr(self.td_obj, 'get_symbol_list'):
                                    logger.info("🔄 Attempting subscription refresh...")
                                    try:
                                        symbols = self._get_symbols_to_subscribe()
                                        if symbols and hasattr(self.td_obj, 'set_symbolslist'):
                                            self.td_obj.set_symbolslist(symbols)
                                            logger.info(f"✅ Subscription refreshed with {len(symbols)} symbols")
                                            time.sleep(5)
                                            consecutive_silent_checks = 0
                                            continue
                                    except Exception as refresh_err:
                                        logger.warning(f"⚠️ Subscription refresh failed: {refresh_err}")
                                
                                # Step 2: Full reconnection only if refresh failed
                                if not self.connected or silence_duration > 60:
                                    logger.info("🔌 Full reconnection required...")
                                    self._activate_circuit_breaker()
                                    time.sleep(3)
                                    self._reset_circuit_breaker()
                                    success = self._direct_connect()
                                    if success:
                                        last_ok = time.time()
                                        consecutive_silent_checks = 0
                                        # Increase cooldown after successful reconnect
                                        reconnect_cooldown = min(reconnect_cooldown * 1.5, 300)
                                        logger.info(f"✅ Reconnected! Next attempt cooldown: {int(reconnect_cooldown)}s")
                                    else:
                                        # Increase cooldown after failed attempt
                                        reconnect_cooldown = min(reconnect_cooldown * 2, 600)
                                        logger.warning(f"❌ Reconnect failed! Next attempt in {int(reconnect_cooldown)}s")
                                else:
                                    logger.info("✅ TrueData still connected, waiting for ticks...")

                            except Exception as re_err:
                                logger.error(f"❌ Health monitor recovery error: {re_err}")
                                reconnect_cooldown = min(reconnect_cooldown * 2, 600)
                                time.sleep(10)
                        
                        # Reset cooldown gradually if data is flowing
                        if recent_tick and reconnect_cooldown > 90:
                            reconnect_cooldown = max(90, reconnect_cooldown * 0.95)

                        time.sleep(3)

                    except Exception as mon_err:
                        logger.debug(f"Health monitor error: {mon_err}")
                        time.sleep(5)

            self._health_thread = threading.Thread(target=_monitor, name="TDHealth", daemon=True)
            self._health_thread.start()
            logger.info("🏥 TrueData Health Monitor thread started")

        except Exception as e:
            logger.warning(f"⚠️ Could not start TrueData health monitor: {e}")

    def _get_symbols_to_subscribe(self):
        """Get symbols from autonomous configuration - FULLY AUTONOMOUS SELECTION"""
        try:
            from config.truedata_symbols import get_complete_fo_symbols, get_autonomous_symbol_status
            
            # Get autonomous symbol selection based on market conditions
            symbols = get_complete_fo_symbols()
            status = get_autonomous_symbol_status()
            
            logger.info(f"🤖 AUTONOMOUS SYMBOL SELECTION:")
            logger.info(f"   Strategy: {status['current_strategy']}")
            logger.info(f"   Symbols: {len(symbols)} (limit: 250)")
            logger.info(f"   Decision: Fully autonomous based on market conditions")
            
            # Log autonomous decision details
            current_hour = datetime.now().hour
            if 7 <= current_hour < 9:
                logger.info(f"   📈 PRE-MARKET: Strategy optimized for indices and futures")
            elif 9 <= current_hour < 11:
                logger.info(f"   ⚡ MARKET OPENING: Strategy optimized for options volatility")
            elif 11 <= current_hour < 13:
                logger.info(f"   📊 MID-DAY: Strategy optimized for balanced trading")
            elif 13 <= current_hour < 15:
                logger.info(f"   🎯 AFTERNOON: Strategy optimized for options expiry effects")
            else:
                logger.info(f"   🔍 POST-MARKET: Strategy optimized for analysis")
            
            # 🎯 CRITICAL FIX: Add options symbols for real-time options data
            options_symbols = self._get_dynamic_options_symbols(symbols)
            all_symbols = symbols + options_symbols
            
            logger.info(f"📊 FINAL SUBSCRIPTION LIST:")
            logger.info(f"   Underlying: {len(symbols)} symbols")
            logger.info(f"   Options: {len(options_symbols)} symbols") 
            logger.info(f"   Total: {len(all_symbols)} symbols (TrueData limit: 250)")
            
            return all_symbols
            
        except ImportError:
            logger.warning("⚠️ Autonomous symbol config not found, using intelligent fallback")
            # Enhanced fallback with autonomous logic
            current_hour = datetime.now().hour
            
            if 9 <= current_hour < 11 or 13 <= current_hour < 15:
                # High volatility periods - options focus
                symbols = [
                    # Core indices
                    'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
                    # Top liquid F&O stocks
                    'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
                    'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
                    'POWERGRID', 'NTPC', 'COALINDIA', 'TECHM', 'MARUTI', 'ASIANPAINT'
                ]
                logger.info(f"🤖 AUTONOMOUS FALLBACK: Options-focused ({len(symbols)} symbols)")
            else:
                # Lower volatility - underlying focus
                symbols = [
                    # Core indices
                    'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
                    # Extended F&O stocks for analysis
                    'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
                    'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
                    'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
                    'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND',
                    'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA'
                ]
                logger.info(f"🤖 AUTONOMOUS FALLBACK: Underlying-focused ({len(symbols)} symbols)")
            
            # 🎯 CRITICAL FIX: Add options symbols for real-time options data
            options_symbols = self._get_dynamic_options_symbols(symbols)
            all_symbols = symbols + options_symbols
            
            logger.info(f"📊 FINAL SUBSCRIPTION LIST:")
            logger.info(f"   Underlying: {len(symbols)} symbols")
            logger.info(f"   Options: {len(options_symbols)} symbols") 
            logger.info(f"   Total: {len(all_symbols)} symbols (TrueData limit: 250)")
            
            # Ensure we don't exceed TrueData limits
            if len(all_symbols) > 250:
                logger.warning(f"⚠️ Symbol count ({len(all_symbols)}) exceeds TrueData limit (250)")
                # Keep underlying symbols + top liquid options
                priority_options = self._get_priority_options_symbols(symbols[:50])  # Top 50 underlying
                all_symbols = symbols + priority_options
                logger.info(f"✂️ TRIMMED: {len(symbols)} underlying + {len(priority_options)} priority options = {len(all_symbols)}")
            
            return all_symbols
    
    def _get_dynamic_options_symbols(self, underlying_symbols: List[str]) -> List[str]:
        """Generate options symbols for real-time trading based on strategy needs"""
        try:
            options_symbols = []
            current_time = datetime.now()
            
            # Focus on most liquid underlying symbols for options
            priority_underlyings = [
                'NIFTY', 'BANKNIFTY', 'FINNIFTY',  # Indices (most liquid)
                'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY',  # Top stocks
                'BHARTIARTL', 'KOTAKBANK', 'SBIN', 'AXISBANK', 'WIPRO'
            ]
            
            for symbol in underlying_symbols:
                # Remove suffix for comparison
                clean_symbol = symbol.replace('-I', '')
                
                # Only generate options for priority symbols during market hours
                if clean_symbol in priority_underlyings and 9 <= current_time.hour <= 15:
                    symbol_options = self._generate_options_chain(clean_symbol)
                    options_symbols.extend(symbol_options)
                    
                    if len(options_symbols) > 150:  # Limit options to 150 max
                        break
            
            return options_symbols[:150]  # Hard cap at 150 options
            
        except Exception as e:
            logger.error(f"Error generating dynamic options symbols: {e}")
            return []
    
    def _generate_options_chain(self, underlying: str) -> List[str]:
        """Generate options chain for an underlying symbol"""
        try:
            options = []
            
            # Get current week and next week expiry in TrueData format
            expiries = self._get_current_expiries()
            
            # Generate strikes around ATM for each expiry
            for expiry in expiries[:2]:  # Current + next expiry only
                strikes = self._get_atm_strikes(underlying)
                
                for strike in strikes:
                    # Generate CE and PE using proper TrueData format
                    from config.options_symbol_mapping import get_truedata_options_format
                    
                    ce_symbol = get_truedata_options_format(underlying, expiry, strike, 'CE')
                    pe_symbol = get_truedata_options_format(underlying, expiry, strike, 'PE')
                    options.extend([ce_symbol, pe_symbol])
                    
                    logger.debug(f"   Generated: {ce_symbol}, {pe_symbol}")
            
            logger.debug(f"📊 Generated {len(options)} options for {underlying}")
            return options
            
        except Exception as e:
            logger.error(f"Error generating options chain for {underlying}: {e}")
            return []
    
    def _get_current_expiries(self) -> List[str]:
        """Get current and next expiry in TrueData format"""
        try:
            # Use the same logic as base_strategy but in TrueData format
            from datetime import datetime, timedelta
            
            today = datetime.now().date()
            expiries = []
            
            # Find current Thursday and next Thursday
            days_to_thursday = (3 - today.weekday()) % 7
            if days_to_thursday == 0:
                days_to_thursday = 7  # If today is Thursday, get next Thursday
            
            current_thursday = today + timedelta(days=days_to_thursday)
            next_thursday = current_thursday + timedelta(days=7)
            
            # Format in TrueData format (need to check TrueData's exact format)
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            
            # TrueData might use different format - this needs testing
            current_exp = f"{current_thursday.day:02d}{month_names[current_thursday.month - 1]}"
            next_exp = f"{next_thursday.day:02d}{month_names[next_thursday.month - 1]}"
            
            return [current_exp, next_exp]
            
        except Exception as e:
            logger.error(f"Error getting current expiries: {e}")
            return ['07AUG', '14AUG']  # Fallback
    
    def _get_atm_strikes(self, underlying: str) -> List[int]:
        """Get DYNAMIC ATM strikes based on current market price"""
        try:
            # 🎯 CRITICAL FIX: Get real-time price and calculate ATM dynamically
            # Use self.live_market_data instead of importing
            
            # Try to get current market price for dynamic ATM calculation
            current_price = None
            underlying_symbol = underlying if underlying not in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else f"{underlying}-I"
            
            if hasattr(self, 'live_market_data') and self.live_market_data and underlying_symbol in self.live_market_data:
                current_price = self.live_market_data[underlying_symbol].get('ltp', 0)
                logger.info(f"📊 DYNAMIC ATM: {underlying} current price = ₹{current_price}")
            
            if current_price and current_price > 0:
                # Calculate ATM dynamically based on current price
                if underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                    # Index strikes (100-point intervals)
                    interval = 100 if underlying == 'NIFTY' else 100
                    atm_strike = round(current_price / interval) * interval
                    strikes = [atm_strike - 200, atm_strike - 100, atm_strike, atm_strike + 100, atm_strike + 200]
                else:
                    # Stock strikes (50-point intervals typically)
                    interval = 50
                    atm_strike = round(current_price / interval) * interval
                    strikes = [atm_strike - 100, atm_strike - 50, atm_strike, atm_strike + 50, atm_strike + 100]
                
                logger.info(f"✅ DYNAMIC STRIKES for {underlying}: ATM={atm_strike}, Range={strikes}")
                return strikes
            
            # Fallback to static strikes if no real-time price available
            logger.warning(f"⚠️ No real-time price for {underlying}, using static strikes")
            
            if underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index strikes (wider range, 100-point intervals)
                base_strikes = {
                    'NIFTY': [24800, 24850, 24900, 24950, 25000],
                    'BANKNIFTY': [55500, 55600, 55700, 55800, 55900],
                    'FINNIFTY': [23000, 23100, 23200, 23300, 23400]
                }
                return base_strikes.get(underlying, [25000])
            else:
                # Stock strikes (50-point intervals typically) - UPDATED with recent ranges
                base_prices = {
                    'RELIANCE': [1350, 1400, 1450, 1500, 1550],      # Updated for current levels
                    'TCS': [2950, 3000, 3050, 3100, 3150],           # Current levels good
                    'HDFCBANK': [1950, 2000, 2050, 2100, 2150],      # Current levels good
                    'ICICIBANK': [1400, 1450, 1500, 1550, 1600],     # Current levels good
                    'INFY': [1750, 1800, 1850, 1900, 1950]           # Current levels good
                }
                return base_prices.get(underlying, [1000, 1050, 1100, 1150, 1200])
                
        except Exception as e:
            logger.error(f"Error getting ATM strikes for {underlying}: {e}")
            return [1000]
    
    def _get_priority_options_symbols(self, underlying_symbols: List[str]) -> List[str]:
        """Get priority options symbols when we need to trim"""
        try:
            priority_options = []
            
            # Focus on NIFTY and BANKNIFTY options only for space efficiency
            for symbol in ['NIFTY', 'BANKNIFTY']:
                if any(symbol in u for u in underlying_symbols):
                    symbol_options = self._generate_options_chain(symbol)
                    priority_options.extend(symbol_options[:20])  # Top 20 per index
            
            return priority_options
            
        except Exception as e:
            logger.error(f"Error getting priority options: {e}")
            return []
    
    def _setup_callback(self):
        """Setup callback for live data processing"""
        if not self.td_obj:
            logger.error("❌ TrueData object is None - cannot setup callback")
            return
        
        # CRITICAL FIX: Track callback execution to prevent recursion loops
        callback_execution_count = {'count': 0, 'last_reset': time.time()}
        MAX_CALLBACKS_PER_SECOND = 1000  # Reasonable limit for high-frequency data
            
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            """Process tick data from TrueData with Redis caching - OPTIONS PREMIUM AWARE"""
            # CRITICAL FIX: Rate limit callback execution to prevent runaway recursion
            current_time = time.time()
            if current_time - callback_execution_count['last_reset'] > 1.0:
                callback_execution_count['count'] = 0
                callback_execution_count['last_reset'] = current_time
            
            callback_execution_count['count'] += 1
            if callback_execution_count['count'] > MAX_CALLBACKS_PER_SECOND:
                logger.error(f"❌ CALLBACK RATE LIMIT EXCEEDED: {callback_execution_count['count']}/sec - Dropping tick")
                return  # Drop this tick to prevent system overload
            
            try:
                # DEBUG: Log all available attributes to understand TrueData schema
                if hasattr(tick_data, '__dict__'):
                    attrs = {k: v for k, v in tick_data.__dict__.items() if not k.startswith('_')}
                    logger.debug(f"📊 TrueData tick attributes: {attrs}")
                
                # Extract symbol first
                truedata_symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                if truedata_symbol == 'UNKNOWN':
                    logger.warning("⚠️ Tick data missing symbol, skipping")
                    return
                
                # 🎯 CRITICAL FIX: Convert TrueData symbol to Zerodha format for strategy compatibility
                try:
                    from config.truedata_symbols import _is_options_symbol
                    from config.options_symbol_mapping import convert_truedata_to_zerodha_options
                    
                    if _is_options_symbol(truedata_symbol):
                        # Convert options symbol: TCS2408143000CE → TCS14AUG253000CE
                        symbol = convert_truedata_to_zerodha_options(truedata_symbol)
                        logger.debug(f"🔄 Symbol conversion: {truedata_symbol} → {symbol}")
                    else:
                        # Keep underlying symbols as-is
                        symbol = truedata_symbol
                        
                except Exception as conv_error:
                    logger.warning(f"⚠️ Symbol conversion failed for {truedata_symbol}: {conv_error}")
                    symbol = truedata_symbol  # Fallback to original
                
                # Extract core price data with fallbacks
                ltp = getattr(tick_data, 'ltp', 0) or getattr(tick_data, 'last_price', 0)
                if ltp <= 0:
                    logger.warning(f"⚠️ Invalid LTP for {symbol}: {ltp}")
                    return
                
                # TEMPORARILY SIMPLIFIED OPTIONS PROCESSING - RESTORE DATA FLOW
                try:
                    from config.truedata_symbols import _is_options_symbol, validate_options_premium
                    
                    is_options = _is_options_symbol(symbol)
                    
                    if is_options:
                        # SIMPLIFIED: Only basic validation, don't block on validation failures
                        try:
                            if validate_options_premium(symbol, ltp):
                                logger.debug(f"✅ OPTIONS DATA: {symbol} = ₹{ltp}")
                            else:
                                logger.debug(f"⚠️ Unusual options premium: {symbol} = ₹{ltp} (but allowing)")
                        except:
                            logger.debug(f"📊 OPTIONS (unvalidated): {symbol} = ₹{ltp}")
                    else:
                        logger.debug(f"📊 UNDERLYING PRICE: {symbol} = ₹{ltp}")
                        
                except ImportError:
                    logger.debug(f"📊 MARKET DATA: {symbol} = ₹{ltp} (no validation)")
                
                # Extract OHLC data - 🔥 FIX: Do NOT synthesize fake OHLC!
                # Use real TrueData values or 0 (let strategies handle missing data)
                high = getattr(tick_data, 'high', None) or getattr(tick_data, 'day_high', None) or 0
                low = getattr(tick_data, 'low', None) or getattr(tick_data, 'day_low', None) or 0
                open_price = getattr(tick_data, 'open', None) or getattr(tick_data, 'day_open', None) or 0
                
                # 🔥 CRITICAL: Mark if OHLC is real or missing (don't fake it!)
                ohlc_available = (
                    high > 0 and low > 0 and open_price > 0 and
                    high != low  # Sanity check: range must exist
                )
                
                # If OHLC truly not available from TrueData, use 0 (strategies will handle)
                if not ohlc_available:
                    # Set to 0 so strategies know data is missing - DON'T FAKE IT!
                    high = 0
                    low = 0
                    open_price = 0
                    logger.debug(f"⚠️ {symbol}: No real OHLC from TrueData - marked as unavailable")
                
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
                
                # 🎯 CRITICAL FIX (2025-12-01): Calculate PREVIOUS_CLOSE from change data
                # This is essential for dual-timeframe analysis
                previous_close = 0.0
                
                # Method 1: Calculate from ltp and change (most reliable)
                if change is not None and change != 0 and ltp > 0:
                    try:
                        change_float = float(change)
                        previous_close = ltp - change_float
                        if previous_close > 0:
                            # Also calculate change_percent if not available
                            if change_percent is None or change_percent == 0:
                                change_percent = (change_float / previous_close) * 100
                            logger.debug(f"📊 Calculated {symbol} previous_close: ₹{previous_close:.2f} "
                                       f"(ltp={ltp}, change={change}, change%={change_percent:.3f}%)")
                        else:
                            logger.warning(f"⚠️ Invalid previous_close for {symbol}: {previous_close}")
                            previous_close = ltp  # Fallback to LTP
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Invalid change value for {symbol}: {change}")
                        previous_close = ltp
                
                # Method 2: Try 'close' field from TrueData (it's often previous close)
                if previous_close <= 0:
                    raw_close = getattr(tick_data, 'close', None) or getattr(tick_data, 'prev_close', None)
                    if raw_close and raw_close > 0 and raw_close != ltp:
                        previous_close = raw_close
                        if change_percent is None or change_percent == 0:
                            change_percent = ((ltp - previous_close) / previous_close) * 100 if previous_close > 0 else 0
                        logger.debug(f"📊 Used raw close for {symbol}: ₹{previous_close:.2f}")
                
                # Fallback: Use LTP if nothing else works
                if previous_close <= 0:
                    previous_close = ltp
                    logger.debug(f"⚠️ Using LTP as previous_close fallback for {symbol}")
                
                # Ensure change_percent is set
                if change_percent is None:
                    change_percent = 0
                
                # Extract additional fields with fallbacks
                bid = getattr(tick_data, 'bid', 0) or getattr(tick_data, 'best_bid', 0)
                ask = getattr(tick_data, 'ask', 0) or getattr(tick_data, 'best_ask', 0)
                
                # 🎯 ENHANCED: Extract Open Interest (OI) for F&O analysis
                oi = (
                    getattr(tick_data, 'oi', 0) or
                    getattr(tick_data, 'open_interest', 0) or
                    getattr(tick_data, 'OI', 0) or
                    0
                )
                oi_change = (
                    getattr(tick_data, 'oi_change', 0) or
                    getattr(tick_data, 'oichange', 0) or
                    getattr(tick_data, 'oi_day_change', 0) or
                    0
                )
                
                # 🎯 ENHANCED (2025-12-01): Data structure with PREVIOUS_CLOSE for dual-timeframe analysis
                market_data = {
                    'symbol': symbol,  # Zerodha format for strategy compatibility
                    'truedata_symbol': truedata_symbol,  # Original TrueData symbol for debugging
                    'ltp': ltp,
                    'close': previous_close,  # 🎯 FIXED: This is PREVIOUS DAY's close, NOT current LTP!
                    'previous_close': previous_close,  # 🎯 Explicit field for clarity
                    'high': high,
                    'low': low,
                    'open': open_price,
                    'volume': volume,
                    'change': change if change else (ltp - previous_close),  # Calculate if missing
                    'changeper': change_percent,
                    'change_percent': change_percent,  # Duplicate for compatibility
                    'bid': bid,
                    'ask': ask,
                    'oi': oi,  # 🎯 Open Interest for F&O analysis
                    'oi_change': oi_change,  # 🎯 OI change for institutional tracking
                    'timestamp': datetime.now().isoformat(),
                    'source': 'TrueData_Live',
                    'deployment_id': self._deployment_id,
                    'ohlc_available': ohlc_available,  # 🔥 NEW: Flag for strategies to check
                    # Additional fields for debugging
                    'data_quality': {
                        'has_ohlc': ohlc_available,  # 🔥 Use real flag, not fake check
                        'has_volume': volume > 0,
                        'has_change_percent': change_percent != 0,
                        'has_previous_close': previous_close > 0 and previous_close != ltp,
                        'calculated_change_percent': change_percent != getattr(tick_data, 'changeper', None),
                        'has_oi': oi > 0  # 🎯 NEW: Flag for OI availability
                    }
                }
                
                # Store in local cache (existing behavior)
                live_market_data[symbol] = market_data
                
                # CRITICAL: Also store in Redis for cross-process access
                if redis_client:
                    try:
                        # Create safe version of market data for Redis storage
                        safe_market_data = create_safe_market_data(market_data)
                        
                        # CRITICAL FIX: Use safe_json_serialize to pre-process, then json.dumps on the safe result
                        # This prevents recursion errors from json.dumps on complex nested structures
                        safe_json = safe_json_serialize(safe_market_data)
                        safe_json_str = json.dumps(safe_json) if isinstance(safe_json, (dict, list)) else str(safe_json)
                        
                        # Store individual symbol data (JSON serialized to handle nested dicts)
                        redis_client.set(f"truedata:symbol:{symbol}", safe_json_str)
                        redis_client.expire(f"truedata:symbol:{symbol}", 300)  # 5 minutes
                        
                        # Store in combined cache
                        redis_client.hset("truedata:live_cache", symbol, safe_json_str)
                        redis_client.expire("truedata:live_cache", 300)  # 5 minutes
                        
                        # Update symbol count
                        redis_client.set("truedata:symbol_count", len(live_market_data))
                        
                        # Store raw tick data for analysis
                        redis_client.lpush(f"truedata:ticks:{symbol}", safe_json_str)
                        redis_client.ltrim(f"truedata:ticks:{symbol}", 0, 100)  # Keep last 100 ticks
                        
                    except RecursionError as re:
                        logger.error(f"Redis recursion error for {symbol}: {re} - Data dropped")
                        # Skip Redis storage for this tick
                        pass
                    except Exception as redis_error:
                        logger.error(f"Redis storage error for {symbol}: {redis_error}")
                
                # Enhanced logging with data quality info
                if volume > 0:
                    quality = market_data['data_quality']
                    logger.info(f"📊 {symbol}: ₹{ltp:,.2f} | {change_percent:+.2f}% | Vol: {volume:,} | "
                              f"OHLC: {'✓' if quality['has_ohlc'] else '✗'} | "
                              f"Deploy: {self._deployment_id}")
                
            except RecursionError as re:
                # CRITICAL FIX: Catch recursion errors specifically to prevent cascading failures
                logger.error(f"❌ RECURSION ERROR in tick callback: {re}")
                logger.error("🚨 This tick will be dropped to prevent system crash")
                # DO NOT re-raise - let the tick be dropped silently
                return
            except Exception as e:
                # CRITICAL FIX: Never let exceptions propagate from callback
                # This prevents TrueData library from retrying and creating recursion loops
                logger.error(f"❌ Error processing tick data (CONTAINED): {e}")
                try:
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                except:
                    pass  # Even traceback logging shouldn't crash
                # DO NOT re-raise - absorb all errors to prevent callback recursion
                return
                
        logger.info("✅ TrueData callback setup complete with RECURSION PROTECTION")

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

def reset_circuit_breaker():
    """API function to manually reset TrueData circuit breaker"""
    return truedata_client.manual_circuit_breaker_reset()

def get_connection_status():
    """Get TrueData connection status for health checks"""
    return {
        'connected': truedata_client.connected,
        'circuit_breaker_active': truedata_client._circuit_breaker_active,
        'consecutive_failures': truedata_client._consecutive_failures,
        'deployment_id': truedata_client._deployment_id,
        'can_attempt_connection': not truedata_client._circuit_breaker_active
    }

def get_truedata_connection_status():
    """Get detailed TrueData connection status including deployment ID"""
    return truedata_connection_status

logger.info("🎯 Advanced TrueData Client loaded - deployment overlap solution active") 
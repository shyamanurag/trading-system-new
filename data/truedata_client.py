#!/usr/bin/env python3
"""
Advanced TrueData WebSocket Client - DEPLOYMENT-AWARE VERSION
Solves the "User Already Connected" deployment overlap issue
Implements graceful connection lifecycle management
"""

import os
import sys
import logging
import threading
import time
import signal
import atexit
from datetime import datetime
from typing import Dict, Optional, List
import json
import redis
import queue

# 🔧 FIX: Increase recursion limit to prevent RecursionError in TrueData library's reconnection
# The TrueData library has internal reconnection logic that can hit Python's default limit (1000)
try:
    current_limit = sys.getrecursionlimit()
    if current_limit < 3000:
        sys.setrecursionlimit(3000)
        logging.getLogger(__name__).debug(f"Increased recursion limit from {current_limit} to 3000")
except Exception:
    pass

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
        
        # 🚀 STARTUP GRACE PERIOD: Suppress tick logging for first 60s to not block health checks
        self._startup_time = time.time()
        self._startup_log_grace_period = 60  # seconds
        
        # Circuit breaker for connection attempts - IMPROVED for market closure
        self._circuit_breaker_active = False
        self._circuit_breaker_timeout = 60  # REDUCED: 1 minute during market closure instead of 5
        self._last_connection_failure = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3  # REDUCED: Be more aggressive about stopping attempts
        
        # 🚨 KILL SWITCH for "User Already Connected" - prevents ALL reconnection attempts
        self._killed = False
        
        # Register cleanup handlers
        self._register_cleanup_handlers()

        # Background health monitor flags
        self._health_thread = None
        self._stop_health = threading.Event()
        # Provide instance-level view for helpers that expect self.live_market_data
        self.live_market_data = live_market_data

        # Tick processing decoupling (prevents websocket ping/pong starvation)
        # Heavy work (Redis, symbol conversion, logging) must NOT run on the websocket thread.
        self._tick_queue: "queue.Queue" = queue.Queue(
            maxsize=int(os.getenv('TRUEDATA_TICK_QUEUE_SIZE', '20000'))
        )
        self._tick_worker_stop = threading.Event()
        self._tick_worker_threads: List[threading.Thread] = []
        self._tick_workers_started = False
        # 🚨 2025-12-19 FIX: Increased from 2 to 4 workers for better throughput
        self._tick_worker_count = int(os.getenv('TRUEDATA_TICK_WORKERS', '4'))
        self._tick_processor = None  # set in _setup_callback()

    def _start_tick_workers(self):
        """Start background tick workers (idempotent)."""
        if self._tick_workers_started:
            return
        self._tick_worker_stop.clear()

        def _worker_loop(worker_idx: int):
            while not self._tick_worker_stop.is_set():
                try:
                    tick = self._tick_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                try:
                    processor = self._tick_processor
                    if processor is not None:
                        processor(tick)
                except Exception as e:
                    # Never let worker errors kill the thread
                    logger.error(f"❌ TrueData tick worker error: {e}")
                    try:
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                    except Exception:
                        pass
                finally:
                    try:
                        self._tick_queue.task_done()
                    except Exception:
                        pass

        for i in range(max(1, self._tick_worker_count)):
            t = threading.Thread(
                target=_worker_loop,
                args=(i + 1,),
                name=f"TDTickWorker-{i + 1}",
                daemon=True
            )
            t.start()
            self._tick_worker_threads.append(t)

        self._tick_workers_started = True
        logger.info(f"🧵 TrueData tick workers started: {len(self._tick_worker_threads)}")

    def _stop_tick_workers(self):
        """Stop tick workers and drain queue (best-effort)."""
        try:
            self._tick_worker_stop.set()
        except Exception:
            pass
        # Drain queue to release memory quickly
        try:
            while True:
                self._tick_queue.get_nowait()
                try:
                    self._tick_queue.task_done()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self._tick_worker_threads = []
        self._tick_workers_started = False

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
        """Check if this is a deployment overlap scenario - DISABLED (broken logic removed)"""
        # CRITICAL FIX: The "graceful takeover" logic was BROKEN - it created MORE failed connections
        # instead of fixing the problem. Now we just fail fast and let circuit breaker handle it.
        # The old logic tried to create a temp TD_live connection to "force disconnect" the existing
        # one, but TrueData doesn't work that way - you can't force-disconnect another user's session.
        return False  # Always return False - no special overlap handling needed

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
        # 🚨 CRITICAL: Check KILL flag before any connection attempt
        if self._killed:
            logger.debug("🛑 TrueData KILLED - _direct_connect blocked")
            return False
            
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
                logger.warning("⚠️ User Already Connected - FAST FAIL (no retry loop)")
                logger.info("💡 Another instance is connected. System will use Zerodha for market data.")
                logger.info("💡 TrueData will auto-retry after 2 minutes")
                # CRITICAL: Activate circuit breaker with LONG timeout to prevent deployment loops
                self._circuit_breaker_active = True
                self._circuit_breaker_timeout = 120  # 2 minute cooldown - enough for old deployment to die
                self._last_connection_failure = time.time()
                self._consecutive_failures += 1
                truedata_connection_status['error'] = 'USER_ALREADY_CONNECTED'
                truedata_connection_status['permanent_block'] = True  # Block all retries
                truedata_connection_status['retry_disabled'] = True
                
                # Set flags to prevent our code from retrying
                self._killed = True
                self._shutdown_requested = True
                self.connected = False
                
                # Stop health monitor to prevent our reconnection attempts
                self._stop_health.set()
                
                # Simple cleanup - don't be aggressive, just mark as disconnected
                # The TrueData library's internal reconnect may still log errors,
                # but that's better than crashing or making things worse
                if self.td_obj:
                    try:
                        self.td_obj.disconnect()
                    except Exception:
                        pass  # Ignore errors during cleanup
                    self.td_obj = None
                
                logger.info("🛑 TrueData marked as disconnected - using Zerodha fallback")
                
                return False
            
            self.connected = False
            self.td_obj = None
            return False

    def connect(self):
        """Main connection method - FAST FAIL on 'User Already Connected' to prevent deployment loops"""
        with self._lock:
            if self._shutdown_requested:
                logger.info("🛑 Shutdown requested - skipping connection")
                return False
            
            # 🚨 CRITICAL: Check KILL flag (set when "User Already Connected" detected)
            if self._killed:
                logger.debug("🛑 TrueData KILLED - connection blocked (User Already Connected detected earlier)")
                return False
            
            # 🚨 CRITICAL: Check for permanent block (subscription expired or user already connected)
            if truedata_connection_status.get('permanent_block', False):
                error_type = truedata_connection_status.get('error', 'UNKNOWN')
                # Check if circuit breaker timeout has expired
                if self._circuit_breaker_active and self._last_connection_failure is not None:
                    time_since_failure = time.time() - self._last_connection_failure
                    if time_since_failure >= self._circuit_breaker_timeout:
                        logger.info(f"🔄 Circuit breaker timeout expired ({error_type}) - allowing retry")
                        # Reset block flags to allow retry
                        truedata_connection_status['permanent_block'] = False
                        truedata_connection_status['retry_disabled'] = False
                        self._circuit_breaker_active = False
                        self._consecutive_failures = 0
                    else:
                        remaining = int(self._circuit_breaker_timeout - time_since_failure)
                        logger.warning(f"⚡ TrueData blocked ({error_type}) - retry in {remaining}s")
                        return False
                else:
                    logger.warning(f"⚡ TrueData connection blocked: {error_type}")
                    return False
                
            # Circuit breaker check - FAST FAIL
            if self._circuit_breaker_active:
                if self._last_connection_failure is not None:
                    time_since_failure = time.time() - self._last_connection_failure
                    if time_since_failure < self._circuit_breaker_timeout:
                        remaining = int(self._circuit_breaker_timeout - time_since_failure)
                        logger.warning(f"⚡ Circuit breaker ACTIVE - cooling down for {remaining}s")
                        return False
                    else:
                        logger.info("⚡ Circuit breaker timeout expired - attempting connection")
                        self._circuit_breaker_active = False
                        self._consecutive_failures = 0
                else:
                    self._circuit_breaker_active = False
                    self._consecutive_failures = 0
                
            if self.connected and self.td_obj:
                logger.info("✅ TrueData already connected")
                return True

            # SINGLE ATTEMPT - no retry loop during deployment
            logger.info("🚀 TrueData connection attempt (single try, no retry loop)")
            
            # Direct connect - no "graceful takeover" attempts (those create MORE failed connections)
            if self._direct_connect():
                self._reset_circuit_breaker()
                return True
            else:
                # CRITICAL FIX: Activate circuit breaker for general failures too
                # _direct_connect() only activates CB for specific errors (subscription expired, user already connected)
                # For network errors, timeouts, auth issues, etc., we need to activate it here
                if not self._circuit_breaker_active:
                    self._activate_circuit_breaker()
                    logger.info("🛡️ Circuit breaker activated for general connection failure")
                logger.warning("⚠️ TrueData connection failed - will use Zerodha fallback")
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
        # Stop tick workers
        try:
            self._stop_tick_workers()
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
                        # 🚨 CRITICAL: Check KILLED flag before any reconnection attempt
                        if self._killed:
                            # Don't log every 3 seconds, just once per 5 minutes
                            if int(current_time) % 300 == 0:
                                logger.info("🛑 TrueData KILLED (User Already Connected) - skipping reconnection")
                            time.sleep(3)
                            continue
                        
                        # 🚨 FIX: DISABLE our reconnection logic entirely
                        # TrueData library has its OWN internal reconnection that we can't edit
                        # Having both running creates a "connection storm" with race conditions
                        # Let TrueData's internal logic handle ALL reconnections
                        if (in_market and 
                            consecutive_silent_checks >= max_silent_before_reconnect):
                            
                            silence_duration = int(current_time - last_ok)
                            
                            # Just log the issue - don't try to reconnect ourselves
                            if (current_time - last_reconnect_attempt) > 60:  # Log once per minute
                                logger.warning(f"⚠️ TrueData TICK SILENCE: {silence_duration}s")
                                logger.info("💡 TrueData library's internal reconnection is handling this")
                                logger.info("💡 Using Zerodha Redis fallback for live data")
                                last_reconnect_attempt = current_time
                            
                            # Don't call _direct_connect() - let TrueData's internal logic handle it
                            # Our reconnection attempts conflict with theirs, causing "User Already Connected"
                        
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
        # 🚨 CRITICAL: TrueData subscription limit - user has 250 symbol plan
        TRUEDATA_SYMBOL_LIMIT = 250
        
        try:
            from config.truedata_symbols import get_complete_fo_symbols, get_autonomous_symbol_status
            
            # Get autonomous symbol selection based on market conditions
            all_fo_symbols = get_complete_fo_symbols()
            status = get_autonomous_symbol_status()
            
            logger.info(f"🤖 AUTONOMOUS SYMBOL SELECTION:")
            logger.info(f"   Strategy: {status['current_strategy']}")
            logger.info(f"   Available F&O Symbols: {len(all_fo_symbols)}")
            logger.info(f"   TrueData Subscription Limit: {TRUEDATA_SYMBOL_LIMIT}")
            
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
            
            # 🚨 PRIORITY-BASED SYMBOL SELECTION to stay within 250 limit
            # Priority 1: Indices (most important for market direction)
            indices = [s for s in all_fo_symbols if s.endswith('-I')]
            
            # Priority 2: Top liquid stocks (sorted by typical F&O volume)
            top_liquid_stocks = [
                'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'SBIN', 'BHARTIARTL',
                'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'WIPRO', 'TITAN', 'BAJFINANCE',
                'TECHM', 'SUNPHARMA', 'HCLTECH', 'TATAMOTORS', 'INDUSINDBK', 'ADANIPORTS',
                'ASIANPAINT', 'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA', 'DRREDDY', 'CIPLA',
                'NESTLEIND', 'ULTRACEMCO', 'HINDUNILVR', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO',
                'VEDL', 'ITC', 'BRITANNIA', 'IOC', 'BPCL', 'GAIL', 'M&M', 'BAJAJ-AUTO',
                'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'APOLLOHOSP', 'BANDHANBNK', 'PNB',
                'FEDERALBNK', 'IDFCFIRSTB', 'BIOCON', 'LUPIN'
            ]
            
            # Priority 3: Other F&O stocks
            other_stocks = [s for s in all_fo_symbols if s not in indices and s not in top_liquid_stocks]
            
            # Build prioritized list - indices first, then top liquid, then others
            prioritized_symbols = indices + [s for s in top_liquid_stocks if s in all_fo_symbols]
            remaining_slots = TRUEDATA_SYMBOL_LIMIT - len(prioritized_symbols) - 50  # Reserve 50 for options
            
            if remaining_slots > 0:
                prioritized_symbols.extend(other_stocks[:remaining_slots])
            
            # Calculate how many slots for options (max 50 during market hours)
            options_budget = min(50, TRUEDATA_SYMBOL_LIMIT - len(prioritized_symbols))
            
            # 🎯 Add options symbols only during market hours and within budget
            options_symbols = []
            if 9 <= current_hour <= 15 and options_budget > 0:
                options_symbols = self._get_dynamic_options_symbols(prioritized_symbols)[:options_budget]
            
            all_symbols = prioritized_symbols + options_symbols
            
            # 🚨 FINAL SAFETY CHECK: Ensure we never exceed 250
            if len(all_symbols) > TRUEDATA_SYMBOL_LIMIT:
                logger.warning(f"⚠️ Symbol count {len(all_symbols)} exceeds limit {TRUEDATA_SYMBOL_LIMIT}, trimming...")
                all_symbols = all_symbols[:TRUEDATA_SYMBOL_LIMIT]
            
            logger.info(f"📊 FINAL SUBSCRIPTION LIST (within {TRUEDATA_SYMBOL_LIMIT} limit):")
            logger.info(f"   Indices: {len(indices)} symbols")
            logger.info(f"   Underlying Stocks: {len(prioritized_symbols) - len(indices)} symbols")
            logger.info(f"   Options: {len(options_symbols)} symbols") 
            logger.info(f"   Total: {len(all_symbols)} symbols ✅")
            
            return all_symbols
            
        except ImportError:
            logger.warning("⚠️ Autonomous symbol config not found, using intelligent fallback")
            # Enhanced fallback with autonomous logic
            current_hour = datetime.now().hour
            
            # Core symbols always included
            symbols = [
                # Core indices (5)
                'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
                # Top liquid F&O stocks for fallback (195 max to leave room for options)
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'ITC',
                'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK', 'WIPRO', 'MARUTI',
                'POWERGRID', 'NTPC', 'COALINDIA', 'TECHM', 'ASIANPAINT', 'HCLTECH',
                'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND', 'TITAN',
                'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA', 'HINDUNILVR',
                'ONGC', 'BPCL', 'IOC', 'GAIL', 'VEDL', 'HINDALCO', 'JSWSTEEL',
                'TATASTEEL', 'APOLLOHOSP', 'INDUSINDBK', 'BANDHANBNK', 'PNB'
            ]
            logger.info(f"🤖 AUTONOMOUS FALLBACK: {len(symbols)} core symbols")
            
            # Calculate options budget (max 50, only during market hours)
            options_budget = min(50, TRUEDATA_SYMBOL_LIMIT - len(symbols))
            options_symbols = []
            
            if 9 <= current_hour <= 15 and options_budget > 0:
                options_symbols = self._get_dynamic_options_symbols(symbols)[:options_budget]
            
            all_symbols = symbols + options_symbols
            
            # 🚨 FINAL SAFETY CHECK
            if len(all_symbols) > TRUEDATA_SYMBOL_LIMIT:
                all_symbols = all_symbols[:TRUEDATA_SYMBOL_LIMIT]
            
            logger.info(f"📊 FALLBACK SUBSCRIPTION LIST (within {TRUEDATA_SYMBOL_LIMIT} limit):")
            logger.info(f"   Underlying: {len(symbols)} symbols")
            logger.info(f"   Options: {len(options_symbols)} symbols") 
            logger.info(f"   Total: {len(all_symbols)} symbols ✅")
            
            return all_symbols
    
    def _get_dynamic_options_symbols(self, underlying_symbols: List[str]) -> List[str]:
        """Generate options symbols for real-time trading based on strategy needs"""
        # 🚨 CRITICAL: Limit options to 50 max to stay within 250 symbol TrueData limit
        OPTIONS_LIMIT = 50
        
        try:
            options_symbols = []
            current_time = datetime.now()
            
            # Focus on ONLY the most liquid index options (indices have highest options volume)
            priority_underlyings = [
                'NIFTY', 'BANKNIFTY',  # Top 2 index options (most liquid)
                'FINNIFTY',  # Expiry on specific days
            ]
            
            for symbol in underlying_symbols:
                # Remove suffix for comparison
                clean_symbol = symbol.replace('-I', '')
                
                # Only generate options for priority symbols during market hours
                if clean_symbol in priority_underlyings and 9 <= current_time.hour <= 15:
                    symbol_options = self._generate_options_chain(clean_symbol)
                    options_symbols.extend(symbol_options)
                    
                    if len(options_symbols) >= OPTIONS_LIMIT:
                        break
            
            return options_symbols[:OPTIONS_LIMIT]  # Hard cap at 50 options
            
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

        # Move heavy processing off the websocket thread to avoid ping/pong timeouts.
        def _process_tick_data(tick_data):
            """Process tick data from TrueData with Redis caching - OPTIONS PREMIUM AWARE"""
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
                        except Exception:
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
                            logger.debug(
                                f"📊 Calculated {symbol} previous_close: ₹{previous_close:.2f} "
                                f"(ltp={ltp}, change={change}, change%={change_percent:.3f}%)"
                            )
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

                # CRITICAL: Store in Redis for cross-process access
                # 🚨 2025-12-19 FIX: Reduced from 7 Redis calls to 2 (was causing slowdown)
                if redis_client:
                    try:
                        # Create safe version of market data for Redis storage
                        safe_market_data = create_safe_market_data(market_data)
                        safe_json = safe_json_serialize(safe_market_data)
                        safe_json_str = json.dumps(safe_json) if isinstance(safe_json, (dict, list)) else str(safe_json)

                        # 🚨 OPTIMIZED: Only 2 Redis calls instead of 7
                        # 1. Store in hash (most efficient for bulk symbol data)
                        redis_client.hset("truedata:live_cache", symbol, safe_json_str)
                        
                        # 2. Update symbol count only every 100 ticks (not every tick!)
                        if not hasattr(self, '_redis_count_ticker'):
                            self._redis_count_ticker = 0
                        self._redis_count_ticker += 1
                        if self._redis_count_ticker >= 100:
                            redis_client.set("truedata:symbol_count", len(live_market_data))
                            redis_client.expire("truedata:live_cache", 300)  # Refresh TTL periodically
                            self._redis_count_ticker = 0
                        
                        # 🚨 2025-12-31: DATA FRESHNESS TRACKING
                        # Store last tick timestamp so orchestrator can detect stale data
                        # Update every 10 ticks to avoid Redis overhead
                        if self._redis_count_ticker % 10 == 0:
                            redis_client.set("truedata:last_tick_time", str(time.time()))

                    except Exception as redis_error:
                        # Silent fail - Redis errors shouldn't block tick processing
                        pass

                # RATE-LIMITED logging to prevent stdout flooding during startup
                # Skip logging entirely during startup grace period (first 60s)
                # Then log at most 1 tick per symbol every 30 seconds
                if volume > 0:
                    current_time = time.time()
                    
                    # 🚀 STARTUP GRACE: Skip ALL tick logging for first 60 seconds
                    time_since_startup = current_time - self._startup_time
                    if time_since_startup < self._startup_log_grace_period:
                        pass  # Silent during startup - let health checks pass
                    else:
                        last_log_key = f"_last_log_{symbol}"
                        last_log_time = getattr(self, last_log_key, 0)
                        
                        # Only log if 30 seconds have passed since last log for this symbol
                        if current_time - last_log_time > 30:
                            setattr(self, last_log_key, current_time)
                            quality = market_data['data_quality']
                            logger.info(
                                f"📊 {symbol}: ₹{ltp:,.2f} | {change_percent:+.2f}% | Vol: {volume:,} | "
                                f"OHLC: {'✓' if quality['has_ohlc'] else '✗'} | "
                                f"Deploy: {self._deployment_id}"
                            )

            except RecursionError as re:
                # CRITICAL FIX: Catch recursion errors specifically to prevent cascading failures
                logger.error(f"❌ RECURSION ERROR in tick callback: {re}")
                logger.error("🚨 This tick will be dropped to prevent system crash")
                return
            except Exception as e:
                # CRITICAL FIX: Never let exceptions propagate from callback
                # This prevents TrueData library from retrying and creating recursion loops
                logger.error(f"❌ Error processing tick data (CONTAINED): {e}")
                try:
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                except Exception:
                    pass  # Even traceback logging shouldn't crash
                return

        # Set processor and ensure workers are running
        self._tick_processor = _process_tick_data
        self._start_tick_workers()
        
        # CRITICAL FIX: Track callback execution to prevent recursion loops
        callback_execution_count = {'count': 0, 'last_reset': time.time()}
        MAX_CALLBACKS_PER_SECOND = 1000  # Reasonable limit for high-frequency data
            
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            """FAST PATH: enqueue tick for background processing (keeps websocket responsive)."""
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
                self._tick_queue.put_nowait(tick_data)
            except queue.Full:
                # Drop tick if we're saturated; better than blocking websocket thread.
                return
            except Exception:
                # Never let callback throw.
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
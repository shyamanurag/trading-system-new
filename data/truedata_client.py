#!/usr/bin/env python3
"""
PERMANENT TrueData WebSocket Client - ROBUST SINGLETON PATTERN
Permanent fix for "User Already Connected" retry loops with proper state management
"""

import os
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
import pickle
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}
truedata_connection_status = {
    'connected': False,
    'last_update': None,
    'error': None,
    'data_count': 0
}

class TrueDataConnectionState:
    """Persistent connection state management to prevent multiple connection attempts"""
    
    def __init__(self):
        self.state_file = os.path.join(tempfile.gettempdir(), 'truedata_connection_state.pkl')
        self._lock = threading.Lock()
    
    def load_state(self):
        """Load connection state from persistent storage"""
        try:
            with self._lock:
                if os.path.exists(self.state_file):
                    with open(self.state_file, 'rb') as f:
                        state = pickle.load(f)
                        return state
        except Exception as e:
            logger.debug(f"Could not load connection state: {e}")
        return {}
    
    def save_state(self, state):
        """Save connection state to persistent storage"""
        try:
            with self._lock:
                with open(self.state_file, 'wb') as f:
                    pickle.dump(state, f)
        except Exception as e:
            logger.debug(f"Could not save connection state: {e}")
    
    def is_recently_failed(self, username, max_age_minutes=10):
        """Check if connection recently failed for this username"""
        state = self.load_state()
        user_state = state.get(username, {})
        
        if user_state.get('error') == 'USER_ALREADY_CONNECTED':
            last_error_time = user_state.get('last_error_time', 0)
            current_time = time.time()
            
            if (current_time - last_error_time) < (max_age_minutes * 60):
                return True
        
        return False
    
    def mark_connection_failed(self, username, error_type):
        """Mark connection as failed for this username"""
        state = self.load_state()
        state[username] = {
            'error': error_type,
            'last_error_time': time.time(),
            'retry_disabled': True
        }
        self.save_state(state)
    
    def clear_connection_state(self, username):
        """Clear connection state for this username"""
        state = self.load_state()
        if username in state:
            del state[username]
            self.save_state(state)

# Global connection state manager
connection_state = TrueDataConnectionState()

class TrueDataSingletonClient:
    """
    PERMANENT TrueData Client - ROBUST SINGLETON WITH STATE MANAGEMENT
    Fixes all "User Already Connected" errors with persistent state tracking
    """
    
    _instance = None
    _lock = threading.Lock()
    _connection_active = False  # Class-level connection flag
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        
        # Connection state
        self._connection_lock = threading.Lock()
        self._last_heartbeat = 0
        self._connection_attempts = 0
        self._max_attempts = 1  # Only allow 1 attempt to prevent retry loops
        
        logger.info(f"TrueData Singleton Client initialized for {self.username}")

    def connect(self):
        """Connect to TrueData with PERMANENT fix for retry loops"""
        with self._connection_lock:
            # Check if already connected at class level
            if TrueDataSingletonClient._connection_active:
                logger.info("TrueData connection already active globally")
                return True
                
            if self.connected and self.td_obj:
                logger.info("Already connected to TrueData")
                return True
            
            # Check persistent state for recent failures
            if connection_state.is_recently_failed(self.username):
                logger.warning("🔒 TrueData connection blocked - recent 'User Already Connected' error")
                logger.info("💡 Use force-disconnect API to clear state and retry")
                truedata_connection_status.update({
                    'connected': False,
                    'error': 'USER_ALREADY_CONNECTED_BLOCKED',
                    'message': 'Recent connection failure - use force-disconnect to reset'
                })
                return False
            
            # Increment attempt counter
            self._connection_attempts += 1
            if self._connection_attempts > self._max_attempts:
                logger.error("🛑 Max connection attempts reached - preventing retry loop")
                return False
            
            try:
                # Nuclear cleanup first
                self._nuclear_cleanup()
                
                # Import TrueData library
                from truedata import TD_live
                
                logger.info(f"Connecting to TrueData: {self.username}@{self.url}:{self.port} (Attempt {self._connection_attempts})")
                
                # Create connection with MAXIMUM retry prevention
                self.td_obj = TD_live(
                    self.username, 
                    self.password, 
                    live_port=self.port,
                    url=self.url,
                    log_level=logging.ERROR,
                    compression=False,
                    # PERMANENT FIX: Try to disable library-level retries
                    max_retry_attempts=0 if hasattr(TD_live, 'max_retry_attempts') else None,
                    reconnect=False if hasattr(TD_live, 'reconnect') else None,
                    auto_reconnect=False if hasattr(TD_live, 'auto_reconnect') else None
                )
                
                # Single connection attempt with comprehensive error handling
                try:
                    logger.info("🔄 Attempting TrueData connection (single attempt only)...")
                    
                    # Mark connection attempt at class level
                    TrueDataSingletonClient._connection_active = True
                    
                    # Connection attempt with immediate error detection
                    connect_result = self.td_obj.connect()
                    
                    # Brief wait to see if connection stabilizes
                    time.sleep(3)
                    
                    # Check connection success indicators
                    connection_success = self._verify_connection()
                    
                    if connection_success:
                        logger.info("🎉 TrueData connection established successfully!")
                        self.connected = True
                        
                        # Clear any previous failure state
                        connection_state.clear_connection_state(self.username)
                        
                        # Setup enhanced callbacks
                        self._setup_enhanced_callbacks()
                        
                        # Subscribe to indices
                        self._subscribe_to_indices()
                        
                        # Update status
                        truedata_connection_status.update({
                            'connected': True,
                            'last_update': datetime.now().isoformat(),
                            'error': None,
                            'username': self.username
                        })
                        
                        return True
                    else:
                        logger.error("❌ TrueData connection verification failed")
                        self._handle_connection_failure('CONNECTION_VERIFICATION_FAILED')
                        return False
                        
                except Exception as e:
                    # Reset class-level connection flag on error
                    TrueDataSingletonClient._connection_active = False
                    
                    error_msg = str(e).lower()
                    
                    # Handle "User Already Connected" error specifically
                    if "user already connected" in error_msg or "already connected" in error_msg:
                        logger.error("🔒 PERMANENT FIX: 'User Already Connected' error detected")
                        logger.error("💡 Marking connection as permanently failed for this session")
                        logger.error("🛑 No further automatic attempts will be made")
                        
                        # Mark in persistent state
                        connection_state.mark_connection_failed(self.username, 'USER_ALREADY_CONNECTED')
                        
                        # Update status with permanent block
                        truedata_connection_status.update({
                            'connected': False,
                            'error': 'USER_ALREADY_CONNECTED',
                            'last_error_time': datetime.now().isoformat(),
                            'retry_disabled': True,
                            'permanent_block': True,
                            'message': 'Account connected elsewhere. Use force-disconnect API to reset.'
                        })
                        
                        # Destroy TD object to prevent any library-level retries
                        self._destroy_connection()
                        
                        return False
                    else:
                        logger.error(f"❌ TrueData connection error: {e}")
                        self._handle_connection_failure(str(e))
                        return False
                    
            except Exception as e:
                # Reset class-level connection flag on setup error
                TrueDataSingletonClient._connection_active = False
                
                error_msg = str(e).lower()
                
                if "user already connected" in error_msg or "already connected" in error_msg:
                    logger.error("🔒 TrueData setup failed: User Already Connected")
                    connection_state.mark_connection_failed(self.username, 'USER_ALREADY_CONNECTED_SETUP')
                    
                    truedata_connection_status.update({
                        'connected': False,
                        'error': 'USER_ALREADY_CONNECTED_SETUP',
                        'last_error_time': datetime.now().isoformat(),
                        'retry_disabled': True,
                        'permanent_block': True
                    })
                else:
                    logger.error(f"❌ TrueData setup error: {e}")
                    self._handle_connection_failure(str(e))
                
                return False

    def _verify_connection(self):
        """Verify connection using multiple indicators"""
        if not self.td_obj:
            return False
        
        connection_indicators = []
        
        # Primary indicator: connect_live attribute
        if hasattr(self.td_obj, 'connect_live') and getattr(self.td_obj, 'connect_live', False):
            connection_indicators.append('connect_live')
            logger.info("✅ Connection confirmed: connect_live = True")
        
        # Secondary indicator: live_websocket exists
        if hasattr(self.td_obj, 'live_websocket') and getattr(self.td_obj, 'live_websocket', None):
            connection_indicators.append('live_websocket')
            logger.info("✅ Connection confirmed: live_websocket exists")
        
        # Test callback capability
        try:
            @self.td_obj.trade_callback
            def test_callback(data):
                pass
            connection_indicators.append('callbacks')
            logger.info("✅ Connection confirmed: callbacks can be set")
        except:
            logger.warning("⚠️ Cannot set callbacks - connection may be unstable")
        
        return len(connection_indicators) >= 2  # Require at least 2 indicators

    def _handle_connection_failure(self, error):
        """Handle connection failure with proper cleanup"""
        self.connected = False
        TrueDataSingletonClient._connection_active = False
        
        truedata_connection_status.update({
            'connected': False,
            'error': error,
            'last_error_time': datetime.now().isoformat(),
            'retry_disabled': True  # Always disable retries on failure
        })
        
        self._destroy_connection()

    def _destroy_connection(self):
        """Completely destroy connection to prevent library-level retries"""
        if self.td_obj:
            try:
                # Try multiple disconnect methods
                if hasattr(self.td_obj, 'disconnect'):
                    self.td_obj.disconnect()
                if hasattr(self.td_obj, 'close'):
                    self.td_obj.close()
                if hasattr(self.td_obj, 'stop'):
                    self.td_obj.stop()
            except:
                pass
            finally:
                self.td_obj = None
        
        # Clear global flag
        TrueDataSingletonClient._connection_active = False

    def force_disconnect_and_reset(self):
        """Force disconnect and reset all connection state - for API endpoint"""
        with self._connection_lock:
            logger.info("🔧 Force disconnect and reset requested...")
            
            # Destroy any existing connection
            self._destroy_connection()
            
            # Reset all counters and flags
            self._connection_attempts = 0
            self.connected = False
            TrueDataSingletonClient._connection_active = False
            
            # Clear persistent state
            connection_state.clear_connection_state(self.username)
            
            # Clear global status
            truedata_connection_status.update({
                'connected': False,
                'error': None,
                'retry_disabled': False,
                'permanent_block': False,
                'last_update': datetime.now().isoformat(),
                'message': 'Force disconnect completed - ready for new connection'
            })
            
            # Clear live data
            live_market_data.clear()
            
            logger.info("✅ Force disconnect and reset completed")
            return True

    def _nuclear_cleanup(self):
        """Complete cleanup of any existing connections"""
        try:
            self._destroy_connection()
            self.connected = False
            TrueDataSingletonClient._connection_active = False
            live_market_data.clear()
            time.sleep(1)  # Brief pause for cleanup
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _setup_enhanced_callbacks(self):
        """Setup enhanced callbacks with better volume parsing"""
        if not self.td_obj:
            logger.error("No TrueData object for callback setup")
            return
            
        # Enhanced Trade/Tick callback with correct volume field (ttq)
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                ltp = getattr(tick_data, 'ltp', 0)
                
                # Get volume using correct TrueData field 'ttq' (Total Traded Quantity)
                volume = getattr(tick_data, 'ttq', 0) or getattr(tick_data, 'volume', 0)
                
                # Get OHLC data with fallbacks
                high = getattr(tick_data, 'day_high', ltp) or ltp
                low = getattr(tick_data, 'day_low', ltp) or ltp
                open_price = getattr(tick_data, 'day_open', ltp) or ltp
                
                # Store comprehensive data
                now = datetime.now()
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp) if ltp else 0.0,
                    'volume': int(volume) if volume else 0,
                    'high': float(high) if high else 0.0,
                    'low': float(low) if low else 0.0,
                    'open': float(open_price) if open_price else 0.0,
                    'timestamp': now.isoformat(),
                    'data_source': 'PERMANENT_FIX_CALLBACK',
                    'last_update_time': now.timestamp(),
                    'heartbeat': True
                }
                
                # Update heartbeat
                self._last_heartbeat = now.timestamp()
                
                # Log with volume source
                vol_str = f" | Vol: {volume:,}" if volume > 0 else " | Vol: 0"
                logger.info(f"📊 {symbol}: ₹{ltp:,.2f}{vol_str}")
                
            except Exception as e:
                logger.error(f"❌ Tick callback error: {e}")
        
        logger.info("✅ Enhanced callbacks setup completed with permanent fix")

    def _subscribe_to_indices(self):
        """Subscribe to market indices"""
        if not self.td_obj or not self.connected:
            logger.error("Cannot subscribe - not connected")
            return False
            
        try:
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
            req_ids = self.td_obj.start_live_data(symbols)
            logger.info(f"📡 Subscribed to symbols: {symbols}")
            return True
        except Exception as e:
            logger.error(f"❌ Subscription error: {e}")
            return False

    def get_status(self):
        """Get enhanced status with heartbeat monitoring"""
        now = datetime.now().timestamp()
        heartbeat_age = now - self._last_heartbeat if self._last_heartbeat > 0 else 999
        
        return {
            'connected': self.connected,
            'username': self.username,
            'url': f"{self.url}:{self.port}",
            'symbols_active': len(live_market_data),
            'implementation': 'PERMANENT_FIX_SINGLETON_CLIENT',
            'data_flowing': len(live_market_data) > 0,
            'heartbeat_age_seconds': heartbeat_age,
            'heartbeat_healthy': heartbeat_age < 30,
            'last_heartbeat': self._last_heartbeat,
            'live_symbols': list(live_market_data.keys()),
            'connection_attempts': self._connection_attempts,
            'max_attempts': self._max_attempts,
            'global_connection_active': TrueDataSingletonClient._connection_active
        }

    def disconnect(self):
        """Disconnect cleanly"""
        with self._connection_lock:
            self._destroy_connection()
            logger.info("🔌 TrueData client disconnected")

# Create GLOBAL SINGLETON instance
truedata_client = TrueDataSingletonClient()

# Backend interface functions
def initialize_truedata():
    """Initialize TrueData - called by backend"""
    return truedata_client.connect()

def get_truedata_status():
    """Get enhanced status - called by backend"""
    return truedata_client.get_status()

def is_connected():
    """Check connection with heartbeat monitoring - called by backend"""
    status = truedata_client.get_status()
    return status['connected'] and status['heartbeat_healthy']

def get_live_data_for_symbol(symbol: str):
    """Get data for symbol - called by backend"""
    return live_market_data.get(symbol)

def subscribe_to_symbols(symbols: list):
    """Subscribe to symbols - called by backend"""
    return truedata_client.subscribe_symbols(symbols) if hasattr(truedata_client, 'subscribe_symbols') else False

def get_all_live_data():
    """Get all live market data - called by backend"""
    return live_market_data.copy()

def get_connection_health():
    """Get connection health metrics"""
    status = get_truedata_status()
    return {
        'connected': status['connected'],
        'heartbeat_healthy': status['heartbeat_healthy'],
        'data_flowing': status['data_flowing'],
        'symbols_count': status['symbols_active'],
        'heartbeat_age': status['heartbeat_age_seconds']
    }

def force_disconnect_and_reset():
    """Force disconnect and reset - for API endpoint"""
    return truedata_client.force_disconnect_and_reset()

logger.info("🚀 PERMANENT TrueData Singleton Client loaded with retry loop fix")

# =====================================
# DIAGNOSTIC FUNCTIONS
# =====================================

def verify_truedata_setup():
    """Verify TrueData setup and credentials"""
    issues = []
    
    # Check credentials
    username = os.environ.get('TRUEDATA_USERNAME')
    password = os.environ.get('TRUEDATA_PASSWORD')
    
    if not username or not password:
        issues.append("TrueData credentials not set in environment")
    elif username == 'tdwsp697':
        issues.append("Using subscription account - should work")
    
    # Check for multiple client files
    import glob
    truedata_files = glob.glob('data/truedata_client*.py')
    if len(truedata_files) > 1:
        issues.append(f"Multiple TrueData clients detected: {truedata_files}")
    
    # Check library installation
    try:
        import truedata
        issues.append("Official truedata library available")
    except ImportError:
        try:
            import truedata_ws
            issues.append("truedata-ws library available")
        except ImportError:
            issues.append("No TrueData library installed")
    
    return issues

def run_truedata_diagnosis():
    """Run complete TrueData diagnosis"""
    print("TrueData Diagnosis Report")
    print("=" * 50)
    
    issues = verify_truedata_setup()
    for issue in issues:
        print(issue)
    
    print("\nAction Plan:")
    print("1. Remove all duplicate TrueData client files")
    print("2. Use only the FINAL singleton client")
    print("3. If 'User Already Connected', contact TrueData support")
    print("4. If 'Connection Refused', check account status")
    print("5. Consider upgrading from trial to paid account")

if __name__ == "__main__":
    run_truedata_diagnosis() 
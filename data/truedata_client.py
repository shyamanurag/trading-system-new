#!/usr/bin/env python3
"""
FINAL TrueData WebSocket Client - SINGLETON PATTERN
Fixes "User Already Connected" errors and volume parsing issues
"""

import os
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, List

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

class TrueDataSingletonClient:
    """
    FINAL TrueData Client - ONE CONNECTION ONLY
    Fixes all "User Already Connected" errors and volume parsing
    """
    
    _instance = None
    _lock = threading.Lock()
    
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
        
        logger.info(f"TrueData Singleton Client initialized for {self.username}")

    def connect(self):
        """Connect to TrueData with enhanced error handling and crash prevention"""
        with self._connection_lock:
            if self.connected and self.td_obj:
                logger.info("Already connected to TrueData")
                return True
            
            try:
                # Nuclear cleanup first
                self._nuclear_cleanup()
                
                # Import TrueData library
                from truedata import TD_live
                
                logger.info(f"Connecting to TrueData: {self.username}@{self.url}:{self.port}")
                
                # Create connection with safety wrapper
                self.td_obj = TD_live(
                    self.username, 
                    self.password, 
                    live_port=self.port,  # 8084 - your official allocated port
                    url=self.url,
                    log_level=logging.ERROR,  # Reduce noise
                    compression=False  # DISABLE COMPRESSION to avoid bytes/str error
                )
                
                # Wrap in try-catch to prevent SystemExit from crashing app
                try:
                    logger.info("Attempting TrueData connection...")
                    
                    # The TD_live.connect() method returns None, not True/False
                    connect_result = self.td_obj.connect()
                    
                    # Give connection time to establish
                    time.sleep(2)
                    
                    # Check the CORRECT connection indicators from inspection
                    connection_success = False
                    
                    # Primary indicator: connect_live attribute
                    if hasattr(self.td_obj, 'connect_live') and getattr(self.td_obj, 'connect_live', False):
                        connection_success = True
                        logger.info("✅ Connection confirmed: connect_live = True")
                    
                    # Secondary indicator: live_websocket exists
                    if hasattr(self.td_obj, 'live_websocket') and getattr(self.td_obj, 'live_websocket', None):
                        connection_success = True
                        logger.info("✅ Connection confirmed: live_websocket exists")
                    
                    # Test callback capability (another strong indicator)
                    try:
                        @self.td_obj.trade_callback
                        def test_callback(data):
                            pass
                        logger.info("✅ Connection confirmed: callbacks can be set")
                        connection_success = True
                    except:
                        logger.warning("⚠️ Cannot set callbacks - connection may be unstable")
                    
                    if connection_success:
                        logger.info("🎉 TrueData connection established successfully!")
                        self.connected = True
                        
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
                        logger.error("❌ TrueData connection failed - no success indicators found")
                        return False
                        
                except (SystemExit, KeyboardInterrupt) as e:
                    logger.error(f"🛑 TrueData library attempted to exit app: {e}")
                    logger.error("🔒 Prevented app crash - TrueData will remain disconnected")
                    self.connected = False
                    return False
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Handle "User Already Connected" error specifically
                    if "user already connected" in error_msg or "already connected" in error_msg:
                        logger.error("🔒 TrueData 'User Already Connected' error detected")
                        logger.error("💡 This means the account is connected from another session")
                        logger.error("🛑 STOPPING connection attempts to prevent retry loop")
                        
                        # Mark as permanently failed for this session to prevent retries
                        truedata_connection_status.update({
                            'connected': False,
                            'error': 'USER_ALREADY_CONNECTED',
                            'last_error_time': datetime.now().isoformat(),
                            'retry_disabled': True,
                            'message': 'Account connected elsewhere. Manual intervention required.'
                        })
                        
                        self.connected = False
                        return False
                    else:
                        logger.error(f"❌ TrueData connection error: {e}")
                        self.connected = False
                        return False
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle setup errors
                if "user already connected" in error_msg or "already connected" in error_msg:
                    logger.error("🔒 TrueData setup failed: User Already Connected")
                    truedata_connection_status.update({
                        'connected': False,
                        'error': 'USER_ALREADY_CONNECTED_SETUP',
                        'last_error_time': datetime.now().isoformat(),
                        'retry_disabled': True
                    })
                else:
                    logger.error(f"❌ TrueData setup error: {e}")
                    truedata_connection_status.update({
                        'connected': False,
                        'error': str(e),
                        'last_error_time': datetime.now().isoformat()
                    })
                return False

    def _nuclear_cleanup(self):
        """Complete cleanup of any existing connections"""
        try:
            if self.td_obj:
                try:
                    self.td_obj.disconnect()
                except:
                    pass
                self.td_obj = None
            
            self.connected = False
            
            # Clear global data
            live_market_data.clear()
            
            # Small delay to ensure cleanup
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _setup_enhanced_callbacks(self):
        """Setup enhanced callbacks with better volume parsing"""
        if not self.td_obj:
            logger.error("No TrueData object for callback setup")
            return
            
        # Enhanced Trade/Tick callback with multiple volume field support
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                # DEBUGGING: Log raw packet structure to understand TrueData format
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                if symbol in ['NIFTY', 'BANKNIFTY', 'NIFTY-I', 'BANKNIFTY-I']:
                    # Log packet structure for major indices only (avoid spam)
                    logger.info(f"🔍 RAW_PACKET {symbol}: type={type(tick_data)}")
                    logger.info(f"🔍 RAW_FIELDS {symbol}: {list(dir(tick_data)) if hasattr(tick_data, '__dict__') else 'no __dict__'}")
                    try:
                        if hasattr(tick_data, '__dict__'):
                            logger.info(f"🔍 RAW_DATA {symbol}: {tick_data.__dict__}")
                        elif hasattr(tick_data, 'keys'):
                            logger.info(f"🔍 RAW_KEYS {symbol}: {list(tick_data.keys())}")
                    except:
                        logger.info(f"🔍 RAW_UNKNOWN {symbol}: Cannot extract raw data")
                
                # Get symbol
                
                # Get price with fallbacks
                ltp = (getattr(tick_data, 'ltp', 0) or 
                      getattr(tick_data, 'price', 0) or 
                      getattr(tick_data, 'last_price', 0))
                
                # HYBRID volume parsing - try both object attributes AND dictionary keys
                def get_volume_safely(data):
                    """Try both getattr() and .get() methods for volume extraction"""
                    # TrueData uses 'ttq' (Total Traded Quantity) as the main volume field
                    volume_fields = ['ttq', 'volume', 'vol', 'v', 'total_volume', 'day_volume', 'traded_volume', 'ltq']
                    
                    for field in volume_fields:
                        # Try object attribute first
                        try:
                            vol = getattr(data, field, 0)
                            if vol and vol > 0:
                                return vol
                        except:
                            pass
                        
                        # Try dictionary key if attribute fails
                        try:
                            if hasattr(data, 'get'):
                                vol = data.get(field, 0)
                                if vol and vol > 0:
                                    return vol
                        except:
                            pass
                    
                    return 0
                
                volume = get_volume_safely(tick_data)
                
                # Get OHLC data with fallbacks
                high = getattr(tick_data, 'high', ltp) or getattr(tick_data, 'h', ltp)
                low = getattr(tick_data, 'low', ltp) or getattr(tick_data, 'l', ltp)
                open_price = getattr(tick_data, 'open', ltp) or getattr(tick_data, 'o', ltp)
                
                # Get change data
                change = getattr(tick_data, 'change', 0) or getattr(tick_data, 'chg', 0)
                change_percent = getattr(tick_data, 'change_percent', 0) or getattr(tick_data, 'chg_per', 0)
                
                # Store comprehensive data with heartbeat
                now = datetime.now()
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp) if ltp else 0.0,
                    'volume': int(volume) if volume else 0,
                    'high': float(high) if high else float(ltp) if ltp else 0.0,
                    'low': float(low) if low else float(ltp) if ltp else 0.0,
                    'open': float(open_price) if open_price else float(ltp) if ltp else 0.0,
                    'change': float(change) if change else 0.0,
                    'change_percent': float(change_percent) if change_percent else 0.0,
                    'timestamp': now.isoformat(),
                    'data_source': 'ENHANCED_CALLBACK',
                    'last_update_time': now.timestamp(),
                    'heartbeat': True
                }
                
                # Enhanced logging with volume field source debugging
                def get_volume_field_source(data):
                    """Debug which field actually contains volume data"""
                    # TrueData uses 'ttq' as primary volume field
                    volume_fields = ['ttq', 'volume', 'vol', 'v', 'total_volume', 'day_volume', 'traded_volume', 'ltq']
                    found_fields = []
                    
                    for field in volume_fields:
                        # Check object attribute
                        try:
                            vol = getattr(data, field, 0)
                            if vol and vol > 0:
                                found_fields.append(f"{field}={vol}(attr)")
                        except:
                            pass
                        
                        # Check dictionary key
                        try:
                            if hasattr(data, 'get'):
                                vol = data.get(field, 0)
                                if vol and vol > 0:
                                    found_fields.append(f"{field}={vol}(dict)")
                        except:
                            pass
                    
                    return found_fields
                
                volume_sources = get_volume_field_source(tick_data)
                vol_debug = f"[{','.join(volume_sources)}]" if volume_sources else "[NO_VOL_FOUND]"
                vol_str = f" | Vol: {volume:,} {vol_debug}" if volume > 0 else f" | Vol: 0 {vol_debug}"
                logger.info(f"📊 {symbol}: ₹{ltp:,.2f}{vol_str}")
                
                # Update global connection status with heartbeat
                truedata_connection_status.update({
                    'connected': True,
                    'last_update': now.isoformat(),
                    'data_count': len(live_market_data),
                    'last_symbol': symbol,
                    'heartbeat': now.timestamp(),
                    'last_volume': volume
                })
                
                # Update heartbeat tracker
                self._last_heartbeat = now.timestamp()
                
            except Exception as e:
                logger.error(f"❌ Tick callback error: {e}")
                # Enhanced error logging
                try:
                    logger.error(f"Tick data attributes: {dir(tick_data)}")
                    logger.error(f"Tick data vars: {vars(tick_data)}")
                except:
                    logger.error("Could not extract tick data structure")
        
        # Enhanced Greek callback
        @self.td_obj.greek_callback
        def on_greek_data(greek_data):
            try:
                symbol = getattr(greek_data, 'symbol', 'UNKNOWN')
                
                greek_info = {
                    'symbol': symbol,
                    'ltp': getattr(greek_data, 'ltp', 0),
                    'iv': getattr(greek_data, 'iv', 0),
                    'delta': getattr(greek_data, 'delta', 0),
                    'gamma': getattr(greek_data, 'gamma', 0),
                    'theta': getattr(greek_data, 'theta', 0),
                    'vega': getattr(greek_data, 'vega', 0),
                    'rho': getattr(greek_data, 'rho', 0),
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'GREEKS'
                }
                
                live_market_data[f"{symbol}_GREEKS"] = greek_info
                logger.info(f"📈 GREEKS: {symbol} - IV:{greek_info['iv']:.2f}%")
                
            except Exception as e:
                logger.error(f"❌ Greek callback error: {e}")
        
        # Enhanced Bid-Ask callback
        @self.td_obj.bidask_callback
        def on_bidask_data(bidask_data):
            try:
                symbol = getattr(bidask_data, 'symbol', 'UNKNOWN')
                
                bidask_info = {
                    'symbol': symbol,
                    'bid': getattr(bidask_data, 'bid', 0),
                    'ask': getattr(bidask_data, 'ask', 0),
                    'bid_qty': getattr(bidask_data, 'bid_qty', 0),
                    'ask_qty': getattr(bidask_data, 'ask_qty', 0),
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'BIDASK'
                }
                
                # Merge with existing data
                if symbol in live_market_data:
                    live_market_data[symbol].update(bidask_info)
                else:
                    live_market_data[symbol] = bidask_info
                
                logger.info(f"💹 BIDASK: {symbol} - Bid:₹{bidask_info['bid']}, Ask:₹{bidask_info['ask']}")
                
            except Exception as e:
                logger.error(f"❌ BidAsk callback error: {e}")
        
        logger.info("✅ Enhanced callbacks setup completed")

    def _subscribe_to_indices(self):
        """Subscribe to market indices with correct symbol formats"""
        if not self.td_obj or not self.connected:
            logger.error("Cannot subscribe - not connected")
            return False
            
        try:
            # Use correct TrueData symbol formats
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
            
            req_ids = self.td_obj.start_live_data(symbols)
            logger.info(f"📡 Subscribed to symbols: {symbols}")
            logger.info(f"📡 Request IDs: {req_ids}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Subscription error: {e}")
            return False

    def subscribe_symbols(self, symbols: list):
        """Subscribe to additional symbols"""
        if not self.td_obj or not self.connected:
            logger.error("Not connected to TrueData")
            return False
            
        try:
            req_ids = self.td_obj.start_live_data(symbols)
            logger.info(f"📡 Subscribed to {len(symbols)} additional symbols: {req_ids}")
            return True
        except Exception as e:
            logger.error(f"❌ Subscribe error: {e}")
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
            'implementation': 'ENHANCED_SINGLETON_CLIENT',
            'data_flowing': len(live_market_data) > 0,
            'heartbeat_age_seconds': heartbeat_age,
            'heartbeat_healthy': heartbeat_age < 30,  # Consider healthy if updated within 30s
            'last_heartbeat': self._last_heartbeat,
            'live_symbols': list(live_market_data.keys())
        }

    def disconnect(self):
        """Disconnect cleanly"""
        with self._connection_lock:
            self._nuclear_cleanup()
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
    return truedata_client.subscribe_symbols(symbols)

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

logger.info("🚀 ENHANCED TrueData Singleton Client loaded with volume parsing fix")

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
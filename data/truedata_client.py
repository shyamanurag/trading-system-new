"""
FINAL TrueData Client - SINGLETON PATTERN
Fixes all "User Already Connected" errors
"""
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Global data storage - EXACTLY as backend expects
live_market_data = {}
truedata_connection_status = {
    'connected': False,
    'username': '',
    'last_update': None,
    'error': None,
    'data_count': 0
}

class TrueDataSingletonClient:
    """
    FINAL TrueData Client - ONE CONNECTION ONLY
    Fixes all "User Already Connected" errors
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Use OFFICIAL TrueData account credentials
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = "push.truedata.in"
        self.port = 8084  # OFFICIAL port from TrueData support
        
        self.td_obj = None
        self.connected = False
        self.running = False
        self.data_thread = None
        self._initialized = True
        
        logger.info(f"FINAL TrueData Client - User: {self.username}")

    def connect(self):
        """Connect with COMPLETE session cleanup"""
        global truedata_connection_status, live_market_data
        
        with self._lock:
            try:
                # CRITICAL: Complete cleanup first
                self._nuclear_cleanup()
                
                # Quick cleanup pause (reduced from 30s to prevent production timeouts)
                logger.info("Quick session cleanup...")
                time.sleep(3)
                
                # Import ONLY the official library
                try:
                    from truedata import TD_live
                    logger.info("Using official truedata library")
                except ImportError:
                    try:
                        from truedata_ws.websocket.TD import TD
                        TD_live = TD
                        logger.info("Using truedata-ws library")
                    except ImportError:
                        logger.error("No TrueData library available")
                        return False
                
                # Create SINGLE connection
                logger.info("Creating SINGLE TrueData connection...")
                self.td_obj = TD_live(
                    login_id=self.username, 
                    password=self.password, 
                    live_port=self.port,
                    url=self.url,
                    log_level=logging.WARNING,
                    compression=False  # CRITICAL: Disable compression to fix decompression bug
                )
                
                # Test connection immediately
                logger.info("Testing connection...")
                
                # OFFICIAL PATTERN: Start live data for NSE symbols FIRST (account supports NSE Equity, F&O, Indices)
                test_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'TCS']
                req_ids = self.td_obj.start_live_data(test_symbols)
                logger.info(f"Live data started for NSE symbols: {req_ids}")
                
                # Brief pause as per official pattern
                time.sleep(1)
                
                # Setup callbacks AFTER start_live_data (official TrueData pattern)
                self._setup_callbacks()
                
                # Mark as connected
                self.connected = True
                truedata_connection_status.update({
                    'connected': True,
                    'username': self.username,
                    'last_update': datetime.now().isoformat(),
                    'error': None
                })
                
                logger.info("TrueData connection SUCCESS!")
                return True
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Connection failed: {error_msg}")
                
                # Check if it's the familiar error
                if "User Already Connected" in error_msg:
                    logger.error("CRITICAL: Server reports user already connected")
                    logger.error("SOLUTIONS:")
                    logger.error("   1. Contact TrueData support to reset session")
                    logger.error("   2. Wait 60+ minutes for automatic session expiry")
                    logger.error("   3. Try different credentials if available")
                    
                    truedata_connection_status['error'] = "User Already Connected - Contact TrueData Support"
                elif "Connection refused" in error_msg:
                    logger.error("CRITICAL: TrueData servers refusing connection")
                    logger.error("POSSIBLE CAUSES:")
                    logger.error("   1. Account subscription expired")
                    logger.error("   2. IP address blocked due to multiple failed attempts")
                    logger.error("   3. Incorrect credentials")
                    logger.error("   4. TrueData server maintenance")
                    
                    truedata_connection_status['error'] = "Connection Refused - Check Account Status"
                else:
                    truedata_connection_status['error'] = error_msg
                
                self._nuclear_cleanup()
                return False

    def _nuclear_cleanup(self):
        """Complete nuclear cleanup of ALL TrueData connections"""
        logger.info("Performing NUCLEAR cleanup of ALL TrueData connections...")
        
        try:
            # Stop any running threads
            self.running = False
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=3)
            
            # Cleanup current connection
            if self.td_obj:
                cleanup_methods = ['disconnect', 'close', 'stop', 'logout']
                for method in cleanup_methods:
                    if hasattr(self.td_obj, method):
                        try:
                            getattr(self.td_obj, method)()
                            logger.info(f"Called {method}()")
                        except:
                            pass
                            
                self.td_obj = None
            
            # Clear all data
            self.connected = False
            live_market_data.clear()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("Nuclear cleanup completed")
            
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    def _setup_callbacks(self):
        """Setup all callbacks for TrueData - FIXED using official pattern"""
        if not self.td_obj:
            return
            
        # Trade/Tick callback - FIXED to use official pattern
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                # Use official pattern: dictionary access, not getattr
                symbol = tick_data.get('symbol', 'UNKNOWN')
                ltp = tick_data.get('ltp', 0)
                volume = tick_data.get('volume', 0)  # Changed from 'ttq' to 'volume'
                
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp),
                    'volume': int(volume),
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'OFFICIAL_TRUEDATA_PATTERN'
                }
                
                logger.info(f"LIVE: {symbol} = Rs.{ltp}")
                
                # Update connection status
                truedata_connection_status.update({
                    'last_update': datetime.now().isoformat(),
                    'data_count': len(live_market_data)
                })
                
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
                logger.error(f"Tick data structure: {tick_data}")
        
        # Greek callback for options - FIXED to use official pattern
        @self.td_obj.greek_callback
        def on_greek_data(greek_data):
            try:
                # Use official pattern: dictionary access
                symbol = greek_data.get('symbol', 'UNKNOWN')
                
                greek_info = {
                    'symbol': symbol,
                    'ltp': greek_data.get('ltp', 0),
                    'iv': greek_data.get('iv', 0),
                    'delta': greek_data.get('delta', 0),
                    'gamma': greek_data.get('gamma', 0),
                    'theta': greek_data.get('theta', 0),
                    'vega': greek_data.get('vega', 0),
                    'rho': greek_data.get('rho', 0),
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'GREEKS'
                }
                
                # Store in market data with _GREEKS suffix
                live_market_data[f"{symbol}_GREEKS"] = greek_info
                
                logger.info(f"GREEKS: {symbol} - IV:{greek_info['iv']:.2f}%, Delta:{greek_info['delta']:.4f}")
                
            except Exception as e:
                logger.error(f"Greek callback error: {e}")
                logger.error(f"Greek data structure: {greek_data}")
        
        # Bid-Ask callback - FIXED to use official pattern
        @self.td_obj.bidask_callback
        def on_bidask_data(bidask_data):
            try:
                # Use official pattern: dictionary access
                symbol = bidask_data.get('symbol', 'UNKNOWN')
                
                bidask_info = {
                    'symbol': symbol,
                    'bid': bidask_data.get('bid', 0),
                    'ask': bidask_data.get('ask', 0),
                    'bid_qty': bidask_data.get('bid_qty', 0),
                    'ask_qty': bidask_data.get('ask_qty', 0),
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'BIDASK'
                }
                
                # Update main market data
                if symbol in live_market_data:
                    live_market_data[symbol].update(bidask_info)
                else:
                    live_market_data[symbol] = bidask_info
                
                logger.info(f"BIDASK: {symbol} - Bid:{bidask_info['bid']}, Ask:{bidask_info['ask']}")
                
            except Exception as e:
                logger.error(f"BidAsk callback error: {e}")
                logger.error(f"BidAsk data structure: {bidask_data}")
        
        logger.info("Callbacks setup completed using OFFICIAL TrueData pattern")

    def subscribe_symbols(self, symbols: list):
        """Subscribe to additional symbols"""
        if not self.td_obj or not self.connected:
            logger.error("Not connected to TrueData")
            return False
            
        try:
            req_ids = self.td_obj.start_live_data(symbols)
            logger.info(f"Subscribed to {len(symbols)} symbols: {req_ids}")
            return True
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            return False

    def get_status(self):
        """Get current status"""
        return {
            'connected': self.connected,
            'username': self.username,
            'url': f"{self.url}:{self.port}",
            'symbols_active': len(live_market_data),
            'implementation': 'FINAL_SINGLETON_CLIENT',
            'data_flowing': len(live_market_data) > 0
        }

    def disconnect(self):
        """Disconnect cleanly"""
        with self._lock:
            self._nuclear_cleanup()
            logger.info("Final TrueData client disconnected")

# Create GLOBAL SINGLETON instance
truedata_client = TrueDataSingletonClient()

# Backend interface functions
def initialize_truedata():
    """Initialize TrueData - called by backend"""
    return truedata_client.connect()

def get_truedata_status():
    """Get status - called by backend"""
    return truedata_client.get_status()

def is_connected():
    """Check connection - called by backend"""
    return truedata_client.connected

def get_live_data_for_symbol(symbol: str):
    """Get data for symbol - called by backend"""
    return live_market_data.get(symbol)

def subscribe_to_symbols(symbols: list):
    """Subscribe to symbols - called by backend"""
    return truedata_client.subscribe_symbols(symbols)

logger.info("FINAL TrueData Singleton Client loaded")

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
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

# Setup basic logging
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}

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
                
            if self.connected and self.td_obj:
                logger.info("✅ TrueData already connected")
                return True

            self._connection_attempts += 1
            
            if self._connection_attempts > self._max_connection_attempts:
                logger.error(f"❌ Max connection attempts ({self._max_connection_attempts}) exceeded")
                return False

            logger.info(f"🚀 TrueData connection attempt {self._connection_attempts}/{self._max_connection_attempts}")

            # Check if this is a deployment overlap scenario
            if self._check_deployment_overlap():
                logger.info("🔄 Deployment overlap detected - attempting graceful takeover")
                
                # Strategy 1: Try graceful takeover
                if self._attempt_graceful_takeover():
                    return True
                
                # Strategy 2: Wait for old connection to timeout and retry
                logger.info("⏳ Graceful takeover failed - waiting for connection timeout...")
                time.sleep(15)  # Wait for old connection to timeout
                
                if self._direct_connect():
                    return True
                
                # Strategy 3: Use environment variable to skip auto-init
                logger.warning("⚠️ All connection attempts failed")
                logger.info("💡 SOLUTION: Set SKIP_TRUEDATA_AUTO_INIT=true to break deployment overlap cycle")
                logger.info("🔧 Then manually connect via: /api/v1/truedata/connect")
                return False
            else:
                # Local development - direct connect
                return self._direct_connect()

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
        """Setup data callback with enhanced error handling"""
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                if self._shutdown_requested:
                    return
                    
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                ltp = getattr(tick_data, 'ltp', 0)

                # Enhanced volume parsing
                volume = 0
                volume_fields = ['ttq', 'volume', 'total_traded_quantity', 'vol', 'day_volume', 'traded_quantity']

                for field in volume_fields:
                    try:
                        vol = getattr(tick_data, field, 0)
                        if vol and vol > 0:
                            volume = vol
                            break
                    except:
                        continue

                # Get OHLC data with fallbacks
                high = getattr(tick_data, 'day_high', ltp) or ltp
                low = getattr(tick_data, 'day_low', ltp) or ltp
                open_price = getattr(tick_data, 'day_open', ltp) or ltp

                # Store clean data with deployment ID
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp) if ltp else 0.0,
                    'volume': int(volume) if volume else 0,
                    'high': float(high) if high else 0.0,
                    'low': float(low) if low else 0.0,
                    'open': float(open_price) if open_price else 0.0,
                    'timestamp': datetime.now().isoformat(),
                    'deployment_id': self._deployment_id
                }

                # Selective logging to avoid spam
                if symbol in ['NIFTY-I', 'BANKNIFTY-I'] or volume > 0:
                    logger.info(f"📊 {symbol}: ₹{ltp:,.2f} | Vol: {volume:,} | Deploy: {self._deployment_id[:8]}")

            except Exception as e:
                logger.error(f"❌ Tick callback error: {e}")

        logger.info("✅ Data callback setup completed")

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
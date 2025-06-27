#!/usr/bin/env python3
"""
Simplified TrueData WebSocket Client - WORKING VERSION
Based on commit 8c1fd40 that connected perfectly with 130 lines
Removes all over-engineering while keeping autonomous functionality
"""

import os
import logging
import threading
from datetime import datetime
from typing import Dict, Optional

# Setup basic logging
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}

class TrueDataClient:
    """Simple TrueData client - WORKING VERSION with minimal complexity"""

    def __init__(self):
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        self._lock = threading.Lock()
        self.connection_attempts = 0
        self.last_error = None
        self.last_attempt_time = None

    def _get_dynamic_symbols(self):
        """Get symbols from Intelligent Symbol Manager or fall back to defaults"""
        try:
            # Try to get symbols from Intelligent Symbol Manager
            from src.core.intelligent_symbol_manager import get_active_symbols, get_intelligent_symbol_status
            
            # Check if intelligent manager is running
            status = get_intelligent_symbol_status()
            if status.get('is_running', False):
                active_symbols = get_active_symbols()
                if active_symbols and len(active_symbols) > 0:
                    logger.info(f"🤖 Using {len(active_symbols)} symbols from Intelligent Symbol Manager")
                    return active_symbols
                else:
                    logger.info("🤖 Intelligent Symbol Manager running but no symbols yet, using defaults")
            else:
                logger.info("🤖 Intelligent Symbol Manager not running yet, using defaults")
        except Exception as e:
            logger.info(f"🤖 Intelligent Symbol Manager not available: {e}")
        
        # Fall back to default symbols
        try:
            from config.truedata_symbols import get_default_subscription_symbols
            symbols = get_default_subscription_symbols()
            logger.info(f"📋 Using configured DEFAULT_SYMBOLS: {symbols}")
            return symbols
        except ImportError:
            # Ultimate fallback
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS', 'HDFC', 'INFY']
            logger.info(f"📋 Using hardcoded fallback symbols: {symbols}")
            return symbols

    def connect(self):
        """Connect to TrueData - Simple working version"""
        with self._lock:
            if self.connected and self.td_obj:
                logger.info("TrueData already connected")
                return True

            self.connection_attempts += 1
            self.last_attempt_time = datetime.now()

            try:
                from truedata import TD_live

                logger.info(f"🔄 TrueData connection attempt #{self.connection_attempts}")
                logger.info(f"Connecting to TrueData: {self.username}@{self.url}:{self.port}")

                # Simple cleanup if needed
                if self.td_obj:
                    try:
                        if hasattr(self.td_obj, 'disconnect'):
                            self.td_obj.disconnect()
                    except:
                        pass
                    self.td_obj = None

                # Direct connection (same as working debug script)
                self.td_obj = TD_live(
                    self.username,
                    self.password,
                    live_port=self.port,
                    url=self.url,
                    compression=False
                )

                logger.info("✅ TD_live object created")

                # Subscribe to symbols FIRST, then set callback
                # Get symbols from Intelligent Symbol Manager if available, otherwise use defaults
                symbols = self._get_dynamic_symbols()
                logger.info(f"📊 Subscribing to {len(symbols)} symbols: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")
                
                req_ids = self.td_obj.start_live_data(symbols)
                logger.info(f"✅ Subscribed to {len(symbols)} symbols: {req_ids}")

                # Setup callback AFTER subscription
                self._setup_callback()

                # Mark as connected ONLY after successful setup
                self.connected = True
                self.last_error = None
                logger.info("✅ TrueData connected successfully (simple version)")
                return True

            except Exception as e:
                error_msg = str(e).lower()
                self.last_error = str(e)
                logger.error(f"TrueData connection failed: {e}")

                if "user already connected" in error_msg or "already connected" in error_msg:
                    logger.warning("⚠️ TrueData: User Already Connected (deployment overlap)")
                    logger.info("🤖 Will retry automatically on next API call - no action needed")

                self.connected = False
                self.td_obj = None
                return False

    def _setup_callback(self):
        """Setup callback - WORKING VERSION"""
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                ltp = getattr(tick_data, 'ltp', 0)

                # VOLUME FIX: Try multiple volume fields
                volume = 0
                volume_fields = ['ttq', 'volume', 'total_traded_quantity', 'vol', 'day_volume']

                for field in volume_fields:
                    try:
                        vol = getattr(tick_data, field, 0)
                        if vol and vol > 0:
                            volume = vol
                            break
                    except:
                        pass

                # Get OHLC
                high = getattr(tick_data, 'day_high', ltp) or ltp
                low = getattr(tick_data, 'day_low', ltp) or ltp
                open_price = getattr(tick_data, 'day_open', ltp) or ltp

                # Store data
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp) if ltp else 0.0,
                    'volume': int(volume) if volume else 0,
                    'high': float(high) if high else 0.0,
                    'low': float(low) if low else 0.0,
                    'open': float(open_price) if open_price else 0.0,
                    'timestamp': datetime.now().isoformat()
                }

                # Log data received (every 10th tick to avoid spam)
                if len(live_market_data) % 10 == 0 or volume > 0:
                    logger.info(f"📊 {symbol}: ₹{ltp:,.2f} | Vol: {volume:,}")

            except Exception as e:
                logger.error(f"Tick callback error: {e}")

        logger.info("✅ Callback setup completed")

    def should_retry(self):
        """Simple retry logic - allow retry after 30 seconds"""
        if not self.last_attempt_time:
            return True
        
        time_since_last = (datetime.now() - self.last_attempt_time).total_seconds()
        return time_since_last > 30

    def get_status(self):
        """Get simple status"""
        return {
            'connected': self.connected,
            'username': self.username,
            'symbols_active': len(live_market_data),
            'data_flowing': len(live_market_data) > 0,
            'connection_attempts': self.connection_attempts,
            'last_error': self.last_error,
            'autonomous_mode': True,
            'last_attempt': self.last_attempt_time.isoformat() if self.last_attempt_time else None,
            'can_retry': self.should_retry()
        }

    def disconnect(self):
        """Simple disconnect"""
        if self.td_obj:
            try:
                if hasattr(self.td_obj, 'disconnect'):
                    self.td_obj.disconnect()
                logger.info("🔌 TrueData disconnected cleanly")
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
        self.connected = False
        self.td_obj = None

# Create single instance
truedata_client = TrueDataClient()

# Backend interface functions
def initialize_truedata():
    """Initialize TrueData - Simple autonomous version"""
    return truedata_client.connect()

def get_truedata_status():
    """Get status"""
    return truedata_client.get_status()

def is_connected():
    """Check if connected"""
    return truedata_client.connected

def get_live_data_for_symbol(symbol: str):
    """Get data for symbol"""
    return live_market_data.get(symbol)

def get_all_live_data():
    """Get all live data"""
    return live_market_data.copy()

def subscribe_to_symbols(symbols: list):
    """Subscribe to additional symbols"""
    if not truedata_client.td_obj or not truedata_client.connected:
        logger.error("Not connected to TrueData")
        return False

    try:
        req_ids = truedata_client.td_obj.start_live_data(symbols)
        logger.info(f"Subscribed to {len(symbols)} symbols: {req_ids}")
        return True
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        return False

def update_symbols_from_intelligent_manager():
    """Update symbol subscriptions from Intelligent Symbol Manager"""
    if not truedata_client.connected:
        logger.warning("TrueData not connected - cannot update symbols")
        return False
    
    try:
        # Get latest symbols from intelligent manager
        symbols = truedata_client._get_dynamic_symbols()
        
        # Subscribe to new symbols (TrueData SDK handles duplicates)
        if symbols:
            return subscribe_to_symbols(symbols)
        else:
            logger.warning("No symbols received from intelligent manager")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update symbols from intelligent manager: {e}")
        return False

logger.info("Simplified TrueData Client loaded - intelligence over complexity") 
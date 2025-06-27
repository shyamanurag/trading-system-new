#!/usr/bin/env python3
"""
Simple TrueData WebSocket Client - WORKING VERSION
Based on yesterday's successful implementation
Removes complex retry logic - focuses on clean connection and data parsing
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
    """Simple TrueData client - WORKING VERSION from yesterday"""

    def __init__(self):
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        self._lock = threading.Lock()

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

    def connect(self):
        """Connect to TrueData - SIMPLE WORKING VERSION"""
        with self._lock:
            if self.connected and self.td_obj:
                logger.info("✅ TrueData already connected")
                return True

            try:
                from truedata import TD_live

                logger.info(f"🔄 Connecting to TrueData: {self.username}@{self.url}:{self.port}")

                # Clean disconnect if needed
                if self.td_obj:
                    try:
                        if hasattr(self.td_obj, 'disconnect'):
                            self.td_obj.disconnect()
                    except:
                        pass
                    self.td_obj = None

                # Simple direct connection (same as working version)
                self.td_obj = TD_live(
                    self.username,
                    self.password,
                    live_port=self.port,
                    url=self.url,
                    compression=False
                )

                logger.info("✅ TD_live object created successfully")

                # Get symbols from config and subscribe
                symbols = self._get_symbols_to_subscribe()
                logger.info(f"📊 Subscribing to {len(symbols)} symbols: {symbols}")
                
                req_ids = self.td_obj.start_live_data(symbols)
                logger.info(f"✅ Subscribed successfully: {req_ids}")

                # Setup callback AFTER subscription
                self._setup_callback()

                # Mark as connected
                self.connected = True
                logger.info("🎉 TrueData connected and streaming!")
                return True

            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"❌ TrueData connection failed: {e}")

                # Handle "user already connected" gracefully (no retry loops)
                if "user already connected" in error_msg or "already connected" in error_msg:
                    logger.warning("⚠️ TrueData: User Already Connected (deployment overlap)")
                    logger.info("💡 This happens during deployments - no action needed")
                    logger.info("🔄 Will work automatically once old container stops")

                self.connected = False
                self.td_obj = None
                return False

    def _setup_callback(self):
        """Setup data callback - WORKING VERSION with proper parsing"""
        @self.td_obj.trade_callback
        def on_tick_data(tick_data):
            try:
                symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
                ltp = getattr(tick_data, 'ltp', 0)

                # Enhanced volume parsing - try multiple fields
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

                # Store clean data
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(ltp) if ltp else 0.0,
                    'volume': int(volume) if volume else 0,
                    'high': float(high) if high else 0.0,
                    'low': float(low) if low else 0.0,
                    'open': float(open_price) if open_price else 0.0,
                    'timestamp': datetime.now().isoformat()
                }

                # Log data received (selective to avoid spam)
                if symbol in ['NIFTY-I', 'BANKNIFTY-I'] or volume > 0:
                    logger.info(f"📊 {symbol}: ₹{ltp:,.2f} | Vol: {volume:,}")

            except Exception as e:
                logger.error(f"❌ Tick callback error: {e}")

        logger.info("✅ Data callback setup completed")

    def get_status(self):
        """Get simple status"""
        return {
            'connected': self.connected,
            'data_flowing': len(live_market_data) > 0,
            'symbols_active': len(live_market_data),
            'username': self.username,
            'timestamp': datetime.now().isoformat()
        }

    def disconnect(self):
        """Simple clean disconnect"""
        try:
            if self.td_obj and hasattr(self.td_obj, 'disconnect'):
                self.td_obj.disconnect()
                logger.info("🔌 TrueData disconnected cleanly")
        except Exception as e:
            logger.error(f"❌ Disconnect error: {e}")
        
        self.connected = False
        self.td_obj = None

# Create global instance
truedata_client = TrueDataClient()

# Backend interface functions
def initialize_truedata():
    """Initialize TrueData - Simple autonomous version"""
    logger.info("🚀 Initializing TrueData...")
    return truedata_client.connect()

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

logger.info("🎯 Simple TrueData Client loaded - working version restored") 
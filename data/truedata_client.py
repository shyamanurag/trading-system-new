#!/usr/bin/env python3
"""
Simple TrueData WebSocket Client - WORKING VERSION
Based on successful direct connection test
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
    """Simple TrueData client - WORKING VERSION"""
    
    def __init__(self):
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        self._lock = threading.Lock()
    
    def connect(self):
        """Connect to TrueData - WORKING VERSION"""
        with self._lock:
            if self.connected and self.td_obj:
                return True
            
            try:
                from truedata import TD_live
                
                logger.info(f"Connecting to TrueData: {self.username}@{self.url}:{self.port}")
                
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
                symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
                req_ids = self.td_obj.start_live_data(symbols)
                logger.info(f"✅ Subscribed to {len(symbols)} symbols: {req_ids}")
                
                # Setup callback AFTER subscription
                self._setup_callback()
                
                # Mark as connected ONLY after successful setup
                self.connected = True
                logger.info("✅ TrueData connected successfully")
                return True
                
            except Exception as e:
                logger.error(f"TrueData connection failed: {e}")
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
    
    def get_status(self):
        """Get simple status"""
        return {
            'connected': self.connected,
            'username': self.username,
            'symbols_active': len(live_market_data),
            'data_flowing': len(live_market_data) > 0
        }
    
    def disconnect(self):
        """Disconnect cleanly"""
        if self.td_obj:
            try:
                if hasattr(self.td_obj, 'disconnect'):
                    self.td_obj.disconnect()
            except:
                pass
        self.connected = False
        self.td_obj = None

# Create single instance
truedata_client = TrueDataClient()

# Backend interface functions
def initialize_truedata():
    """Initialize TrueData"""
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
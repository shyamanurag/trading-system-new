#!/usr/bin/env python3
"""
Simple TrueData WebSocket Client - AUTONOMOUS VERSION
Handles deployment overlaps gracefully while remaining fully autonomous
"""

import os
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

# Setup basic logging
logger = logging.getLogger(__name__)

# Global data storage
live_market_data: Dict[str, Dict] = {}

class TrueDataClient:
    """Autonomous TrueData client with smart deployment overlap handling"""
    
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
    
    def connect(self):
        """Connect to TrueData - AUTONOMOUS with deployment overlap handling"""
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
                
                # Create TD_live object
                self.td_obj = TD_live(
                    self.username, 
                    self.password, 
                    live_port=self.port,
                    url=self.url,
                    compression=False
                )
                
                logger.info("✅ TD_live object created")
                
                # Try to start live data subscription
                try:
                    symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
                    req_ids = self.td_obj.start_live_data(symbols)
                    logger.info(f"✅ Subscribed to {len(symbols)} symbols: {req_ids}")
                    
                    # Setup callback AFTER subscription
                    self._setup_callback()
                    
                    # Mark as connected ONLY after successful setup
                    self.connected = True
                    logger.info("✅ TrueData connected successfully (autonomous)")
                    return True
                    
                except Exception as sub_error:
                    error_msg = str(sub_error).lower()
                    if "user already connected" in error_msg or "already connected" in error_msg:
                        logger.warning("⚠️ TrueData: User Already Connected (deployment overlap)")
                        logger.info("🤖 AUTONOMOUS: Will retry automatically - no human intervention needed")
                        logger.info("💡 This is normal during deployments and will resolve automatically")
                        
                        # Clean disconnect but don't disable - remain autonomous
                        self._clean_disconnect()
                        return False
                    else:
                        # Re-raise other errors
                        raise sub_error
                
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"TrueData connection failed: {e}")
                
                error_msg = str(e).lower()
                if "user already connected" in error_msg or "already connected" in error_msg:
                    logger.info("🤖 AUTONOMOUS: System will handle this automatically")
                
                self.connected = False
                self.td_obj = None
                return False
    
    def _clean_disconnect(self):
        """Clean disconnect to prevent SDK issues"""
        if self.td_obj:
            try:
                if hasattr(self.td_obj, 'close'):
                    self.td_obj.close()
                if hasattr(self.td_obj, 'disconnect'):
                    self.td_obj.disconnect()
            except:
                pass
            finally:
                self.td_obj = None
        
        self.connected = False
    
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
        """Determine if connection should be retried (autonomous logic)"""
        if not self.last_attempt_time:
            return True
        
        # Allow retry after 30 seconds (deployment overlap should resolve by then)
        time_since_last = (datetime.now() - self.last_attempt_time).total_seconds()
        return time_since_last > 30
    
    def get_status(self):
        """Get comprehensive status"""
        status = {
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
        
        return status
    
    def disconnect(self):
        """Disconnect cleanly"""
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
    """Initialize TrueData - Autonomous version"""
    return truedata_client.connect()

def get_truedata_status():
    """Get comprehensive status"""
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
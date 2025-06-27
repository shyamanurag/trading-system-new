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

# Connection state management
class ConnectionState:
    def __init__(self):
        self.is_blocked = False
        self.block_reason = ""
        self.last_attempt = None
        
connection_state = ConnectionState()

class TrueDataClient:
    """Simple TrueData client - WORKING VERSION with retry loop prevention"""
    
    def __init__(self):
        self.td_obj = None
        self.connected = False
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = 'push.truedata.in'
        self.port = 8084
        self._lock = threading.Lock()
        self._connection_blocked = False
        self._block_reason = ""
    
    def connect(self):
        """Connect to TrueData - WORKING VERSION with enhanced blocking"""
        with self._lock:
            # Check if connection is blocked due to "User Already Connected"
            if self._connection_blocked:
                logger.info(f"🚫 TrueData connection blocked: {self._block_reason}")
                logger.info("💡 To retry, restart the application or wait for timeout")
                return False
                
            if self.connected and self.td_obj:
                return True
            
            try:
                from truedata import TD_live
                
                logger.info(f"Connecting to TrueData: {self.username}@{self.url}:{self.port}")
                
                # Create TD_live object with custom settings to minimize auto-retry
                self.td_obj = TD_live(
                    self.username, 
                    self.password, 
                    live_port=self.port,
                    url=self.url,
                    compression=False,
                    log_level=logging.WARNING,  # Reduce SDK log spam
                )
                
                logger.info("✅ TD_live object created")
                
                # CRITICAL: Wrap subscription to catch "User Already Connected"
                try:
                    symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
                    req_ids = self.td_obj.start_live_data(symbols)
                    logger.info(f"✅ Subscribed to {len(symbols)} symbols: {req_ids}")
                    
                    # Setup callback AFTER successful subscription
                    self._setup_callback()
                    
                    # Mark as connected ONLY after successful setup
                    self.connected = True
                    logger.info("✅ TrueData connected successfully")
                    return True
                    
                except Exception as sub_error:
                    error_msg = str(sub_error).lower()
                    if "user already connected" in error_msg or "already connected" in error_msg:
                        logger.warning("⚠️ TrueData: Account already connected elsewhere")
                        logger.info("🚫 BLOCKING further connection attempts to prevent retry loop")
                        
                        # BLOCK future connection attempts
                        self._connection_blocked = True
                        self._block_reason = "User Already Connected - Account in use elsewhere"
                        connection_state.is_blocked = True
                        connection_state.block_reason = self._block_reason
                        connection_state.last_attempt = datetime.now()
                        
                        self._force_disconnect()
                        return False
                    else:
                        # Re-raise other errors
                        raise sub_error
                
            except Exception as e:
                error_msg = str(e).lower()
                if "user already connected" in error_msg:
                    logger.warning("⚠️ TrueData: User Already Connected (connection phase)")
                    logger.info("🚫 BLOCKING connection to prevent retry loop")
                    
                    # BLOCK future attempts
                    self._connection_blocked = True
                    self._block_reason = "User Already Connected - Connection rejected"
                    connection_state.is_blocked = True
                    connection_state.block_reason = self._block_reason
                    connection_state.last_attempt = datetime.now()
                else:
                    logger.error(f"TrueData connection failed: {e}")
                
                self._force_disconnect()
                return False
    
    def _force_disconnect(self):
        """Force disconnect and prevent SDK auto-retry"""
        if self.td_obj:
            try:
                # Try multiple disconnection methods to stop auto-retry
                if hasattr(self.td_obj, 'stop_live_data'):
                    try:
                        self.td_obj.stop_live_data()
                        logger.info("📴 Stopped live data subscription")
                    except:
                        pass
                
                if hasattr(self.td_obj, 'close'):
                    try:
                        self.td_obj.close()
                        logger.info("📴 Called close() on TD object")
                    except:
                        pass
                
                if hasattr(self.td_obj, 'disconnect'):
                    try:
                        self.td_obj.disconnect()
                        logger.info("📴 Called disconnect() on TD object")
                    except:
                        pass
                
                # Force cleanup connection
                if hasattr(self.td_obj, '_websocket_client'):
                    try:
                        self.td_obj._websocket_client = None
                    except:
                        pass
                        
            except Exception as cleanup_error:
                logger.error(f"Cleanup error: {cleanup_error}")
            finally:
                self.td_obj = None
        
        self.connected = False
        logger.info("🔌 TrueData forcibly disconnected (retry loop prevented)")
    
    def _clean_disconnect(self):
        """Clean disconnect to prevent retry loops"""
        if self.td_obj:
            try:
                # Force close connection to prevent library retry
                if hasattr(self.td_obj, 'close'):
                    self.td_obj.close()
                if hasattr(self.td_obj, 'disconnect'):
                    self.td_obj.disconnect()
            except:
                pass
            finally:
                self.td_obj = None
        
        self.connected = False
        logger.info("🔌 TrueData disconnected cleanly (retry loop prevented)")
    
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
        """Get comprehensive status including block state"""
        return {
            'connected': self.connected,
            'username': self.username,
            'symbols_active': len(live_market_data),
            'data_flowing': len(live_market_data) > 0,
            'connection_blocked': self._connection_blocked,
            'block_reason': self._block_reason,
            'last_attempt': connection_state.last_attempt.isoformat() if connection_state.last_attempt else None
        }
    
    def reset_connection_block(self):
        """Reset connection block (for manual retry)"""
        with self._lock:
            self._connection_blocked = False
            self._block_reason = ""
            connection_state.is_blocked = False
            connection_state.block_reason = ""
            logger.info("🔄 Connection block reset - retry now possible")
    
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
    """Initialize TrueData with blocking prevention"""
    return truedata_client.connect()

def get_truedata_status():
    """Get comprehensive status"""
    return truedata_client.get_status()

def is_connected():
    """Check if connected"""
    return truedata_client.connected

def reset_connection_block():
    """Reset connection block for manual retry"""
    return truedata_client.reset_connection_block()

def get_live_data_for_symbol(symbol: str):
    """Get data for symbol"""
    return live_market_data.get(symbol)

def get_all_live_data():
    """Get all live data"""
    return live_market_data.copy() 
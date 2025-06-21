"""
TrueData Live Market Data Client
Using Official TrueData Python SDK
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import json
import os

try:
    from truedata import TD_live
except ImportError:
    logging.warning("TrueData library not installed. Install with: pip install truedata")
    TD_live = None

logger = logging.getLogger(__name__)

class TrueDataClient:
    """TrueData live market data client using official SDK"""
    
    def __init__(self, username: str, password: str, port: int = 8084, 
                 url: str = "push.truedata.in", compression: bool = False):
        self.username = username
        self.password = password
        self.port = port
        self.url = url
        self.compression = compression
        
        self.td_obj = None
        self.is_connected = False
        self.subscribed_symbols = set()
        self.callbacks = {
            'tick': [],
            'bidask': [],
            'greek': [],
            'one_min_bar': [],
            'five_min_bar': []
        }
        
        # Market data cache
        self.market_data = {}
        self.last_update = {}
        
        # Keep alive thread
        self.keep_alive_task = None
        
    async def connect(self) -> bool:
        """Connect to TrueData live feed using official SDK"""
        if not TD_live:
            logger.error("TrueData library not available")
            return False
            
        try:
            logger.info(f"Connecting to TrueData: {self.url}:{self.port}")
            
            # Initialize TrueData client using official SDK
            self.td_obj = TD_live(
                self.username, 
                self.password, 
                live_port=self.port,
                log_level=logging.WARNING,
                url=self.url,
                compression=self.compression
            )
            
            # Set up callbacks using official SDK decorators
            self._setup_callbacks()
            
            self.is_connected = True
            logger.info("✅ TrueData connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ TrueData connection failed: {e}")
            return False
    
    def _setup_callbacks(self):
        """Set up TrueData callbacks using official SDK decorators"""
        if not self.td_obj:
            return
            
        # Use official SDK decorators
        @self.td_obj.trade_callback
        def tick_data_callback(tick_data):
            """Handle tick data using official SDK"""
            try:
                self._process_tick_data(tick_data)
            except Exception as e:
                logger.error(f"Error processing tick data: {e}")
        
        @self.td_obj.bidask_callback
        def bidask_callback(bidask_data):
            """Handle bid-ask data using official SDK"""
            try:
                self._process_bidask_data(bidask_data)
            except Exception as e:
                logger.error(f"Error processing bid-ask data: {e}")
        
        @self.td_obj.greek_callback
        def greek_callback(greek_data):
            """Handle greek data for options using official SDK"""
            try:
                self._process_greek_data(greek_data)
            except Exception as e:
                logger.error(f"Error processing greek data: {e}")
        
        @self.td_obj.one_min_bar_callback
        def one_min_bar_callback(bar_data):
            """Handle 1-minute bar data using official SDK"""
            try:
                self._process_bar_data(bar_data, '1min')
            except Exception as e:
                logger.error(f"Error processing 1-min bar data: {e}")
        
        @self.td_obj.five_min_bar_callback
        def five_min_bar_callback(bar_data):
            """Handle 5-minute bar data using official SDK"""
            try:
                self._process_bar_data(bar_data, '5min')
            except Exception as e:
                logger.error(f"Error processing 5-min bar data: {e}")
    
    def _process_tick_data(self, tick_data):
        """Process incoming tick data"""
        try:
            symbol = tick_data.get('symbol', 'UNKNOWN')
            timestamp = datetime.now().isoformat()
            
            # Update market data cache
            self.market_data[symbol] = {
                'type': 'tick',
                'data': tick_data,
                'timestamp': timestamp
            }
            self.last_update[symbol] = timestamp
            
            # Notify callbacks
            for callback in self.callbacks['tick']:
                try:
                    callback(symbol, tick_data)
                except Exception as e:
                    logger.error(f"Error in tick callback: {e}")
                    
            logger.debug(f"Tick data for {symbol}: {tick_data}")
            
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
    
    def _process_bidask_data(self, bidask_data):
        """Process bid-ask data"""
        try:
            symbol = bidask_data.get('symbol', 'UNKNOWN')
            timestamp = datetime.now().isoformat()
            
            # Update market data cache
            self.market_data[symbol] = {
                'type': 'bidask',
                'data': bidask_data,
                'timestamp': timestamp
            }
            self.last_update[symbol] = timestamp
            
            # Notify callbacks
            for callback in self.callbacks['bidask']:
                try:
                    callback(symbol, bidask_data)
                except Exception as e:
                    logger.error(f"Error in bidask callback: {e}")
                    
            logger.debug(f"Bid-Ask data for {symbol}: {bidask_data}")
            
        except Exception as e:
            logger.error(f"Error processing bid-ask data: {e}")
    
    def _process_greek_data(self, greek_data):
        """Process greek data for options"""
        try:
            symbol = greek_data.get('symbol', 'UNKNOWN')
            timestamp = datetime.now().isoformat()
            
            # Update market data cache
            self.market_data[symbol] = {
                'type': 'greek',
                'data': greek_data,
                'timestamp': timestamp
            }
            self.last_update[symbol] = timestamp
            
            # Notify callbacks
            for callback in self.callbacks['greek']:
                try:
                    callback(symbol, greek_data)
                except Exception as e:
                    logger.error(f"Error in greek callback: {e}")
                    
            logger.debug(f"Greek data for {symbol}: {greek_data}")
            
        except Exception as e:
            logger.error(f"Error processing greek data: {e}")
    
    def _process_bar_data(self, bar_data, interval):
        """Process bar data"""
        try:
            symbol = bar_data.get('symbol', 'UNKNOWN')
            timestamp = datetime.now().isoformat()
            
            # Update market data cache
            cache_key = f"{symbol}_{interval}"
            self.market_data[cache_key] = {
                'type': f'bar_{interval}',
                'data': bar_data,
                'timestamp': timestamp
            }
            self.last_update[cache_key] = timestamp
            
            # Notify callbacks
            callback_key = f'{interval}_bar'
            if callback_key in self.callbacks:
                for callback in self.callbacks[callback_key]:
                    try:
                        callback(symbol, bar_data)
                    except Exception as e:
                        logger.error(f"Error in {interval} bar callback: {e}")
                        
            logger.debug(f"{interval} bar data for {symbol}: {bar_data}")
            
        except Exception as e:
            logger.error(f"Error processing {interval} bar data: {e}")
    
    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to symbols for live data using official SDK"""
        if not self.is_connected or not self.td_obj:
            logger.error("Not connected to TrueData")
            return False
            
        try:
            logger.info(f"Subscribing to symbols: {symbols}")
            
            # Use official SDK method to start live data
            req_ids = self.td_obj.start_live_data(symbols)
            
            # Add to subscribed symbols
            self.subscribed_symbols.update(symbols)
            
            # Wait for connection to establish
            await asyncio.sleep(1)
            
            logger.info(f"✅ Subscribed to {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to symbols: {e}")
            return False
    
    async def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from symbols"""
        if not self.is_connected or not self.td_obj:
            return False
            
        try:
            # Remove from subscribed symbols
            self.subscribed_symbols.difference_update(symbols)
            
            # Clear from cache
            for symbol in symbols:
                self.market_data.pop(symbol, None)
                self.last_update.pop(symbol, None)
            
            logger.info(f"✅ Unsubscribed from {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe from symbols: {e}")
            return False
    
    def add_callback(self, data_type: str, callback: Callable):
        """Add a callback for specific data type"""
        if data_type in self.callbacks:
            self.callbacks[data_type].append(callback)
            logger.info(f"Added {data_type} callback")
        else:
            logger.warning(f"Unknown data type: {data_type}")
    
    def remove_callback(self, data_type: str, callback: Callable):
        """Remove a callback"""
        if data_type in self.callbacks and callback in self.callbacks[data_type]:
            self.callbacks[data_type].remove(callback)
            logger.info(f"Removed {data_type} callback")
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get latest market data for a symbol"""
        return self.market_data.get(symbol)
    
    def get_all_market_data(self) -> Dict:
        """Get all market data"""
        return self.market_data.copy()
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscribed_symbols)
    
    async def keep_alive(self):
        """Keep the TrueData connection alive as per official SDK"""
        try:
            while self.is_connected:
                await asyncio.sleep(120)  # Sleep for 2 minutes as per official example
                logger.debug("💓 TrueData keep-alive ping")
        except Exception as e:
            logger.error(f"Error in keep-alive: {e}")
    
    async def start_keep_alive(self):
        """Start the keep-alive task"""
        if self.keep_alive_task is None:
            self.keep_alive_task = asyncio.create_task(self.keep_alive())
            logger.info("✅ Started TrueData keep-alive task")
    
    async def stop_keep_alive(self):
        """Stop the keep-alive task"""
        if self.keep_alive_task:
            self.keep_alive_task.cancel()
            try:
                await self.keep_alive_task
            except asyncio.CancelledError:
                pass
            self.keep_alive_task = None
            logger.info("✅ Stopped TrueData keep-alive task")
    
    async def disconnect(self):
        """Disconnect from TrueData"""
        try:
            # Stop keep-alive task
            await self.stop_keep_alive()
            
            if self.td_obj:
                # Clean up subscriptions
                self.subscribed_symbols.clear()
                self.market_data.clear()
                self.last_update.clear()
                
                # Clear callbacks
                for callback_list in self.callbacks.values():
                    callback_list.clear()
                
                self.is_connected = False
                logger.info("✅ TrueData disconnected")
                
        except Exception as e:
            logger.error(f"Error disconnecting from TrueData: {e}")

# Global TrueData client instance
truedata_client: Optional[TrueDataClient] = None

async def init_truedata_client(username: Optional[str] = None, password: Optional[str] = None) -> Optional[TrueDataClient]:
    """Initialize TrueData client with credentials from environment or parameters"""
    global truedata_client
    
    try:
        # Use provided credentials or load from environment
        if not username:
            username = os.getenv('TRUEDATA_USERNAME')
        if not password:
            password = os.getenv('TRUEDATA_PASSWORD')
        
        if not username or not password:
            logger.error("❌ TrueData credentials not found!")
            logger.error("Please set environment variables or provide credentials:")
            logger.error("  TRUEDATA_USERNAME=your_username")
            logger.error("  TRUEDATA_PASSWORD=your_password")
            return None
        
        # At this point, username and password are guaranteed to be strings
        truedata_client = TrueDataClient(str(username), str(password))
        success = await truedata_client.connect()
        
        if success:
            # Start keep-alive task
            await truedata_client.start_keep_alive()
            logger.info("✅ TrueData client initialized successfully")
            return truedata_client
        else:
            logger.error("❌ Failed to initialize TrueData client")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error initializing TrueData client: {e}")
        return None

def get_truedata_client() -> Optional[TrueDataClient]:
    """Get the global TrueData client instance"""
    return truedata_client 
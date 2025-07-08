"""
TrueData provider for market data and WebSocket integration
Updated for TrueData library version 7.0.x
"""
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import asyncio
import redis
import time
from src.core.websocket_manager import WebSocketManager

# Import TrueData package with better error handling
TRUEDATA_AVAILABLE = False
try:
    from truedata import TD_live
    TRUEDATA_AVAILABLE = True
except ImportError:
    logging.warning("TrueData package not installed. Please install with: pip install truedata")
    logging.info("For manual installation, visit: https://pypi.org/project/truedata/")
    # Create mock classes for development
    class TD_live:
        def __init__(self, *args, **kwargs):
            raise ImportError("TrueData not installed. Please install with: pip install truedata")

logger = logging.getLogger(__name__)

class TrueDataProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_sandbox = config.get('is_sandbox', False)
        
        # Check if TrueData is available
        if not TRUEDATA_AVAILABLE:
            logger.error("TrueData is not available. Please install it first:")
            logger.error("pip install truedata")
            logger.error("Or visit: https://pypi.org/project/truedata/")
            raise ImportError("TrueData package not available")
        
        # Initialize TrueData client with latest API
        try:
            self.live_client = TD_live(
                config['username'],
                config['password'],
                live_port=config.get('live_port', 8084),  # Updated to 8084 as per TrueData support
                url=config.get('url', 'push.truedata.in'),
                log_level=config.get('log_level', logging.WARNING),
                compression=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize TrueData client: {e}")
            raise
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            decode_responses=True
        )
        
        # Initialize WebSocket manager with Redis client
        self.ws_manager = WebSocketManager(self.redis_client)
        
        self.subscribed_symbols = set()
        self.option_chains = {}
        self.data_queue = asyncio.Queue()
        self.callbacks = {}
        self.connection_attempts = 0
        self.max_connection_attempts = config.get('max_connection_attempts', 3)
        self.req_ids = []
        
        # Set up callbacks
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """Set up TrueData callbacks for different data types"""
        
        @self.live_client.trade_callback
        def trade_callback(tick_data):
            """Handle trade/tick data"""
            asyncio.create_task(self._process_trade_data(tick_data))
        
        @self.live_client.bidask_callback
        def bidask_callback(bidask_data):
            """Handle bid/ask data"""
            asyncio.create_task(self._process_bidask_data(bidask_data))
        
        @self.live_client.one_min_bar_callback
        def one_min_bar_callback(bar_data):
            """Handle 1-minute bar data"""
            asyncio.create_task(self._process_bar_data(bar_data, '1min'))
        
        @self.live_client.five_min_bar_callback
        def five_min_bar_callback(bar_data):
            """Handle 5-minute bar data"""
            asyncio.create_task(self._process_bar_data(bar_data, '5min'))
        
        @self.live_client.greek_callback
        def greek_callback(greek_data):
            """Handle greek data for options"""
            asyncio.create_task(self._process_greek_data(greek_data))
    
    async def _process_trade_data(self, tick_data):
        """Process incoming trade data"""
        try:
            # Store in Redis for real-time access
            symbol = tick_data.get('symbol', 'unknown')
            self.redis_client.setex(
                f"tick_data:{symbol}",
                300,  # 5 minutes TTL
                str(tick_data)
            )
            
            # Add to queue for processing
            await self.data_queue.put({
                'type': 'trade',
                'data': tick_data,
                'timestamp': datetime.now()
            })
            
            logger.debug(f"Processed trade data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing trade data: {e}")
    
    async def _process_bidask_data(self, bidask_data):
        """Process incoming bid/ask data"""
        try:
            symbol = bidask_data.get('symbol', 'unknown')
            self.redis_client.setex(
                f"bidask_data:{symbol}",
                300,
                str(bidask_data)
            )
            
            await self.data_queue.put({
                'type': 'bidask',
                'data': bidask_data,
                'timestamp': datetime.now()
            })
            
            logger.debug(f"Processed bid/ask data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing bid/ask data: {e}")
    
    async def _process_bar_data(self, bar_data, bar_type):
        """Process incoming bar data"""
        try:
            symbol = bar_data.get('symbol', 'unknown')
            self.redis_client.setex(
                f"bar_data:{symbol}:{bar_type}",
                600,  # 10 minutes TTL
                str(bar_data)
            )
            
            await self.data_queue.put({
                'type': f'bar_{bar_type}',
                'data': bar_data,
                'timestamp': datetime.now()
            })
            
            logger.debug(f"Processed {bar_type} bar data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing bar data: {e}")
    
    async def _process_greek_data(self, greek_data):
        """Process incoming greek data"""
        try:
            symbol = greek_data.get('symbol', 'unknown')
            self.redis_client.setex(
                f"greek_data:{symbol}",
                300,
                str(greek_data)
            )
            
            await self.data_queue.put({
                'type': 'greek',
                'data': greek_data,
                'timestamp': datetime.now()
            })
            
            logger.debug(f"Processed greek data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing greek data: {e}")
        
    async def connect(self):
        """Connect to TrueData services"""
        try:
            # The connection is established when TD_live is initialized
            # We just need to verify it's working
            logger.info("TrueData client initialized and ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to TrueData: {e}")
            return False
            
    async def subscribe_market_data(self, symbols: List[str]):
        """Subscribe to market data for symbols"""
        try:
            # Start live data for symbols using the new API
            result = self.live_client.start_live_data(symbols)
            if isinstance(result, list):
                self.req_ids.extend(result)
                logger.info(f"Request IDs: {result}")
            elif isinstance(result, bool):
                if not result:
                    logger.error("TrueData start_live_data returned False (subscription failed)")
                    return False
                # If True, no req_ids to store
            else:
                logger.warning(f"Unexpected return type from start_live_data: {type(result)}")
            
            # Update subscribed symbols
            self.subscribed_symbols.update(symbols)
            
            logger.info(f"Subscribed to market data for symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to market data: {e}")
            return False
            
    async def get_historical_data(self, 
                                symbol: str,
                                start_time: datetime,
                                end_time: datetime,
                                bar_size: str = "1 min") -> pd.DataFrame:
        """Get historical data for symbol"""
        try:
            # Note: Historical data API has changed in version 7.0.x
            # This would need to be implemented based on the new API
            logger.warning("Historical data API has changed in TrueData 7.0.x")
            logger.warning("Please implement based on the new API documentation")
            
            # For now, return empty DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
            
    async def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """Get option chain for symbol"""
        try:
            # Note: Option chain API has changed in version 7.0.x
            # This would need to be implemented based on the new API
            logger.warning("Option chain API has changed in TrueData 7.0.x")
            logger.warning("Please implement based on the new API documentation")
            
            # For now, return empty DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to get option chain: {e}")
            return pd.DataFrame()
    
    async def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest data for a symbol from Redis cache"""
        try:
            data = {}
            
            # Get tick data
            tick_data = self.redis_client.get(f"tick_data:{symbol}")
            if tick_data:
                data['tick'] = eval(tick_data)
            
            # Get bid/ask data
            bidask_data = self.redis_client.get(f"bidask_data:{symbol}")
            if bidask_data:
                data['bidask'] = eval(bidask_data)
            
            # Get bar data
            bar_1min = self.redis_client.get(f"bar_data:{symbol}:1min")
            if bar_1min:
                data['bar_1min'] = eval(bar_1min)
            
            bar_5min = self.redis_client.get(f"bar_data:{symbol}:5min")
            if bar_5min:
                data['bar_5min'] = eval(bar_5min)
            
            # Get greek data
            greek_data = self.redis_client.get(f"greek_data:{symbol}")
            if greek_data:
                data['greek'] = eval(greek_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get latest data for {symbol}: {e}")
            return {}
            
    async def disconnect(self):
        """Disconnect from TrueData services"""
        try:
            # Stop live data subscriptions
            if self.req_ids:
                for req_id in self.req_ids:
                    try:
                        self.live_client.stop_live_data(req_id)
                    except Exception as e:
                        logger.warning(f"Failed to stop request {req_id}: {e}")
            
            logger.info("Disconnected from TrueData services")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from TrueData: {e}")
            return False

# Example usage
if __name__ == "__main__":
    config = {
        'username': 'tdwsp697',
        'password': 'shyam@697',
        'live_port': 8084,  # Updated port as per TrueData support
        'log_level': logging.WARNING,
        'url': 'push.truedata.in',
        'data_timeout': 60,
        'retry_attempts': 3,
        'retry_delay': 5,
    }
    
    async def main():
        try:
            provider = TrueDataProvider(config)
            
            # Connect
            await provider.connect()
            
            # Subscribe to symbols
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE']
            await provider.subscribe_market_data(symbols)
            
            # Keep the connection alive and process data
            print("Connected to TrueData. Press Ctrl+C to stop...")
            
            while True:
                # Process any queued data
                try:
                    while not provider.data_queue.empty():
                        data = await provider.data_queue.get()
                        print(f"Received data: {data}")
                except asyncio.QueueEmpty:
                    pass
                
                await asyncio.sleep(1)
                
        except ImportError as e:
            print(f"TrueData not available: {e}")
            print("Please install TrueData with: pip install truedata")
        except KeyboardInterrupt:
            print("\nStopping TrueData provider...")
            await provider.disconnect()
        except Exception as e:
            print(f"Error running TrueData provider: {e}")
    
    asyncio.run(main()) 
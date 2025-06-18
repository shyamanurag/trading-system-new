"""
TrueData provider for market data and WebSocket integration
"""
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import asyncio
import redis
from src.core.websocket_manager import WebSocketManager

# Import TrueData package with better error handling
TRUEDATA_AVAILABLE = False
try:
    from truedata import TD_live, TD_hist
    TRUEDATA_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import
        from truedata_ws import TD_live, TD_hist
        TRUEDATA_AVAILABLE = True
    except ImportError:
        logging.warning("TrueData package not installed. Please install with: pip install truedata-ws")
        logging.info("For manual installation, visit: https://pypi.org/project/truedata-ws/")
        # Create mock classes for development
        class TD_live:
            def __init__(self, *args, **kwargs):
                raise ImportError("TrueData not installed. Please install with: pip install truedata-ws")
        
        class TD_hist:
            def __init__(self, *args, **kwargs):
                raise ImportError("TrueData not installed. Please install with: pip install truedata-ws")

logger = logging.getLogger(__name__)

class TrueDataProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_sandbox = config.get('is_sandbox', False)
        
        # Check if TrueData is available
        if not TRUEDATA_AVAILABLE:
            logger.error("TrueData is not available. Please install it first:")
            logger.error("pip install truedata-ws")
            logger.error("Or visit: https://pypi.org/project/truedata-ws/")
            raise ImportError("TrueData package not available")
        
        # Initialize TrueData clients
        try:
            self.live_client = TD_live(
                config['username'],
                config['password'],
                live_port=config.get('live_port', 8086),
                url=config.get('url', 'push.truedata.in'),
                log_level=config.get('log_level', logging.INFO),
                log_format="%(asctime)s - %(levelname)s - %(message)s"
            )
            
            self.hist_client = TD_hist(
                config['username'],
                config['password'],
                url=config.get('url', 'push.truedata.in')
            )
        except Exception as e:
            logger.error(f"Failed to initialize TrueData clients: {e}")
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
        
    async def connect(self):
        """Connect to TrueData services"""
        try:
            # Start live data connection
            self.live_client.connect()
            
            # Verify connection
            if not self.live_client.is_connected():
                raise ConnectionError("Failed to connect to TrueData live feed")
                
            logger.info("Connected to TrueData services")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to TrueData: {e}")
            return False
            
    async def subscribe_market_data(self, symbols: List[str]):
        """Subscribe to market data for symbols"""
        try:
            # Start live data for symbols
            self.live_client.start_live_data(symbols)
            
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
            # Get historical data
            data = self.hist_client.get_historical_data(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                bar_size=bar_size
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
            
    async def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """Get option chain for symbol"""
        try:
            # Get option chain
            chain = self.live_client.get_option_chain(symbol)
            
            # Store in cache
            self.option_chains[symbol] = {
                'data': chain,
                'timestamp': datetime.now()
            }
            
            return chain
            
        except Exception as e:
            logger.error(f"Failed to get option chain: {e}")
            return pd.DataFrame()
            
    async def disconnect(self):
        """Disconnect from TrueData services"""
        try:
            # Disconnect live client
            self.live_client.disconnect()
            
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
        'live_port': 8084,  # Updated port
        'log_level': logging.INFO,
        'url': 'push.truedata.in',  # Production URL
        'data_timeout': 60,  # 60 seconds timeout for data freshness
        'retry_attempts': 3,  # Number of retry attempts for failed operations
        'retry_delay': 5,    # Delay between retries in seconds
    }
    
    async def main():
        try:
            provider = TrueDataProvider(config)
            
            # Connect
            await provider.connect()
            
            # Subscribe to symbols
            symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE']
            await provider.subscribe_market_data(symbols)
            
            # Get market data
            data = await provider.get_historical_data('NIFTY-I', datetime.now() - timedelta(days=1), datetime.now())
            print(f"Market data: {data}")
            
            # Get option chain
            chain = await provider.get_option_chain('NIFTY')
            print(f"Option chain: {chain}")
            
        except ImportError as e:
            print(f"TrueData not available: {e}")
            print("Please install TrueData with: pip install truedata-ws")
        except Exception as e:
            print(f"Error running TrueData provider: {e}")
    
    asyncio.run(main()) 
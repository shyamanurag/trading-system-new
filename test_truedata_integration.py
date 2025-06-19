#!/usr/bin/env python3
"""
Test script for TrueData integration with version 7.0.x
"""
import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.truedata_provider import TrueDataProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_truedata_connection():
    """Test TrueData connection and basic functionality"""
    
    # Configuration
    config = {
        'username': 'tdwsp697',
        'password': 'shyam@697',
        'live_port': 8084,  # Updated port as per TrueData support
        'log_level': logging.INFO,
        'url': 'push.truedata.in',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0,
    }
    
    provider = None
    
    try:
        logger.info("Initializing TrueData provider...")
        provider = TrueDataProvider(config)
        
        logger.info("Connecting to TrueData...")
        connected = await provider.connect()
        
        if not connected:
            logger.error("Failed to connect to TrueData")
            return False
        
        logger.info("Successfully connected to TrueData!")
        
        # Test subscription to symbols
        test_symbols = ['NIFTY-I', 'BANKNIFTY-I']
        logger.info(f"Subscribing to symbols: {test_symbols}")
        
        subscribed = await provider.subscribe_market_data(test_symbols)
        
        if not subscribed:
            logger.error("Failed to subscribe to market data")
            return False
        
        logger.info("Successfully subscribed to market data!")
        
        # Keep connection alive for a few seconds to receive data
        logger.info("Waiting for data (10 seconds)...")
        
        for i in range(10):
            # Check for any received data
            try:
                while not provider.data_queue.empty():
                    data = await provider.data_queue.get()
                    logger.info(f"Received data: {data['type']} for symbol: {data['data'].get('symbol', 'unknown')}")
            except Exception as e:
                logger.debug(f"No data in queue: {e}")
            
            await asyncio.sleep(1)
        
        # Test getting latest data from cache
        for symbol in test_symbols:
            latest_data = await provider.get_latest_data(symbol)
            if latest_data:
                logger.info(f"Latest data for {symbol}: {list(latest_data.keys())}")
            else:
                logger.info(f"No cached data for {symbol}")
        
        logger.info("TrueData integration test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"TrueData not available: {e}")
        logger.error("Please install TrueData with: pip install truedata>=7.0.0")
        return False
        
    except Exception as e:
        logger.error(f"Error during TrueData test: {e}")
        return False
        
    finally:
        if provider:
            logger.info("Disconnecting from TrueData...")
            await provider.disconnect()

def main():
    """Main function to run the test"""
    logger.info("Starting TrueData integration test...")
    
    # Check if TrueData is available
    try:
        import truedata
        logger.info(f"TrueData version: {truedata.__version__}")
    except ImportError:
        logger.error("TrueData package not found!")
        logger.error("Please install with: pip install truedata>=7.0.0")
        return False
    
    # Run the async test
    success = asyncio.run(test_truedata_connection())
    
    if success:
        logger.info("✅ TrueData integration test PASSED")
        return True
    else:
        logger.error("❌ TrueData integration test FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
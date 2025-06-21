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

from data.truedata_client import (
    initialize_truedata,
    get_truedata_status, 
    is_connected,
    live_market_data,
    truedata_connection_status
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_truedata_connection():
    """Test TrueData connection and basic functionality"""
    
    try:
        logger.info("Initializing TrueData singleton client...")
        
        # Initialize the singleton client
        success = initialize_truedata()
        
        if not success:
            logger.error("Failed to initialize TrueData singleton client")
            return False
        
        logger.info("Successfully initialized TrueData singleton client!")
        
        # Check connection status
        status = get_truedata_status()
        logger.info(f"TrueData status: {status}")
        
        # Check if connected
        if not is_connected():
            logger.error("TrueData singleton client is not connected")
            return False
        
        logger.info("TrueData singleton client is connected!")
        
        # Wait for data to start flowing
        logger.info("Waiting for data to start flowing (10 seconds)...")
        
        for i in range(10):
            # Check connection status
            connection_status = truedata_connection_status
            logger.info(f"Connection status: {connection_status}")
            
            # Check live market data
            if live_market_data:
                logger.info(f"Live symbols: {list(live_market_data.keys())}")
                for symbol, data in live_market_data.items():
                    logger.info(f"Live data for {symbol}: {data}")
            else:
                logger.info("No live market data yet...")
            
            await asyncio.sleep(1)
        
        logger.info("TrueData integration test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"TrueData not available: {e}")
        logger.error("Please install TrueData with: pip install truedata>=7.0.0")
        return False
        
    except Exception as e:
        logger.error(f"Error during TrueData test: {e}")
        return False

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
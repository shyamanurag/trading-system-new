#!/usr/bin/env python3
"""
Test script for the new singleton TrueData client
"""
import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_singleton_client():
    """Test the singleton TrueData client"""
    
    try:
        logger.info("🧪 Testing singleton TrueData client...")
        
        # Import the singleton client
        from data.truedata_client import (
            initialize_truedata,
            get_truedata_status, 
            is_connected,
            live_market_data,
            truedata_connection_status,
            run_truedata_diagnosis
        )
        
        logger.info("✅ Singleton client imported successfully")
        
        # Run diagnosis
        logger.info("🔍 Running TrueData diagnosis...")
        run_truedata_diagnosis()
        
        # Test initialization
        logger.info("🚀 Testing initialization...")
        success = initialize_truedata()
        
        if success:
            logger.info("✅ Singleton client initialized successfully")
            
            # Check status
            status = get_truedata_status()
            logger.info(f"📊 Status: {status}")
            
            # Check connection
            if is_connected():
                logger.info("✅ Singleton client is connected")
                
                # Wait for data
                logger.info("⏳ Waiting for data (5 seconds)...")
                await asyncio.sleep(5)
                
                # Check live data
                if live_market_data:
                    logger.info(f"📈 Live symbols: {list(live_market_data.keys())}")
                    for symbol, data in live_market_data.items():
                        logger.info(f"   {symbol}: {data}")
                else:
                    logger.info("⚠️ No live data received yet")
                
                # Check connection status
                logger.info(f"🔗 Connection status: {truedata_connection_status}")
                
            else:
                logger.warning("⚠️ Singleton client is not connected")
                
        else:
            logger.error("❌ Failed to initialize singleton client")
            return False
        
        logger.info("🎉 Singleton client test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during singleton client test: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting singleton TrueData client test...")
    
    # Run the test
    success = asyncio.run(test_singleton_client())
    
    if success:
        logger.info("✅ Singleton client test PASSED")
        return True
    else:
        logger.error("❌ Singleton client test FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
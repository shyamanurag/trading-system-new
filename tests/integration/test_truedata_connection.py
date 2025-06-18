"""
Integration tests for TrueData connection
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from data.truedata_provider import TrueDataProvider
from config.truedata_config import TrueDataConfig

logger = logging.getLogger(__name__)

async def test_connection(provider: TrueDataProvider) -> bool:
    """Test TrueData connection"""
    try:
        connected = await provider.connect()
        if connected:
            logger.info("✅ Connection test passed")
            return True
        else:
            logger.error("❌ Connection test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Connection test failed with error: {e}")
        return False

async def test_symbol_subscription(provider: TrueDataProvider, symbols: list) -> bool:
    """Test symbol subscription"""
    try:
        success = await provider.subscribe_market_data(symbols)
        if success:
            logger.info(f"✅ Subscription test passed for symbols: {symbols}")
            return True
        else:
            logger.error("❌ Subscription test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Subscription test failed with error: {e}")
        return False

async def test_market_data(provider: TrueDataProvider, symbol: str) -> bool:
    """Test market data retrieval"""
    try:
        data = await provider.get_historical_data(
            symbol=symbol,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            bar_size='1 day'
        )
        
        if not data.empty:
            logger.info(f"✅ Market data test passed for {symbol}")
            return True
        else:
            logger.error("❌ Market data test failed - no data received")
            return False
    except Exception as e:
        logger.error(f"❌ Market data test failed with error: {e}")
        return False

async def test_option_chain(provider: TrueDataProvider, symbol: str) -> bool:
    """Test option chain retrieval"""
    try:
        chain = await provider.get_option_chain(symbol)
        
        if not chain.empty:
            logger.info(f"✅ Option chain test passed for {symbol}")
            return True
        else:
            logger.error("❌ Option chain test failed - no data received")
            return False
    except Exception as e:
        logger.error(f"❌ Option chain test failed with error: {e}")
        return False

async def test_real_time_data(provider: TrueDataProvider, symbol: str) -> bool:
    """Test real-time data callback"""
    try:
        data_received = False
        
        def callback(data):
            nonlocal data_received
            logger.info(f"Received real-time data for {symbol}: {data}")
            data_received = True
        
        await provider.subscribe_market_data([symbol])
        
        # Wait for data
        for _ in range(10):  # Try for 10 seconds
            if data_received:
                logger.info(f"✅ Real-time data test passed for {symbol}")
                return True
            await asyncio.sleep(1)
        
        logger.error("❌ Real-time data test failed - no data received")
        return False
    except Exception as e:
        logger.error(f"❌ Real-time data test failed with error: {e}")
        return False

async def run_tests():
    """Run all tests"""
    # Get configuration
    config = TrueDataConfig.get_connection_config()
    
    # Initialize provider
    provider = TrueDataProvider(config)
    
    # Run tests
    tests = [
        ("Connection Test", test_connection(provider)),
        ("Symbol Subscription Test", test_symbol_subscription(provider, ['NIFTY-I', 'BANKNIFTY-I'])),
        ("Market Data Test", test_market_data(provider, 'NIFTY-I')),
        ("Option Chain Test", test_option_chain(provider, 'NIFTY')),
        ("Real-time Data Test", test_real_time_data(provider, 'NIFTY-I'))
    ]
    
    # Print results
    print("\n=== Test Results ===")
    for test_name, result in tests:
        status = "✅ PASSED" if await result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Cleanup
    await provider.disconnect()

if __name__ == "__main__":
    asyncio.run(run_tests()) 
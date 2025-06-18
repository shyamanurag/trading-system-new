#!/usr/bin/env python3
"""
TrueData Integration Test Script
Tests TrueData integration with the trading system
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_truedata_provider_import():
    """Test TrueData provider import"""
    print("🔍 Testing TrueData provider import...")
    
    try:
        from data.truedata_provider import TrueDataProvider
        print("✅ TrueData provider imported successfully")
        return True
    except ImportError as e:
        print(f"❌ TrueData provider import failed: {e}")
        return False

def test_config_import():
    """Test configuration import"""
    print("🔍 Testing configuration import...")
    
    try:
        from config.truedata_config import get_config, validate_config, DEFAULT_SYMBOLS
        print("✅ Configuration imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False

async def test_provider_initialization(config: Dict[str, Any]):
    """Test TrueData provider initialization"""
    print("🔍 Testing TrueData provider initialization...")
    
    try:
        from data.truedata_provider import TrueDataProvider
        
        # Initialize provider
        provider = TrueDataProvider(config)
        print("✅ TrueData provider initialized successfully")
        return True, provider
        
    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        return False, None

async def test_provider_connection(provider):
    """Test TrueData provider connection"""
    print("🔍 Testing TrueData provider connection...")
    
    try:
        # Connect to TrueData
        success = await provider.connect()
        
        if success:
            print("✅ TrueData provider connection successful")
            return True
        else:
            print("❌ TrueData provider connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Provider connection failed: {e}")
        return False

async def test_market_data_subscription(provider, symbols: list):
    """Test market data subscription"""
    print(f"🔍 Testing market data subscription for {symbols}...")
    
    try:
        # Subscribe to market data
        success = await provider.subscribe_market_data(symbols)
        
        if success:
            print(f"✅ Market data subscription successful for {symbols}")
            return True
        else:
            print(f"❌ Market data subscription failed for {symbols}")
            return False
            
    except Exception as e:
        print(f"❌ Market data subscription failed: {e}")
        return False

async def test_historical_data_retrieval(provider, symbol: str):
    """Test historical data retrieval"""
    print(f"🔍 Testing historical data retrieval for {symbol}...")
    
    try:
        # Get historical data
        data = await provider.get_historical_data(
            symbol=symbol,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            bar_size="1 min"
        )
        
        if data is not None and len(data) > 0:
            print(f"✅ Historical data retrieved for {symbol}: {len(data)} records")
            return True
        else:
            print(f"⚠️  No historical data for {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Historical data retrieval failed: {e}")
        return False

async def test_options_chain_retrieval(provider, symbol: str):
    """Test options chain retrieval"""
    print(f"🔍 Testing options chain retrieval for {symbol}...")
    
    try:
        # Get options chain
        chain = await provider.get_option_chain(symbol)
        
        if chain is not None and len(chain) > 0:
            print(f"✅ Options chain retrieved for {symbol}: {len(chain)} records")
            return True
        else:
            print(f"⚠️  No options chain data for {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Options chain retrieval failed: {e}")
        return False

async def test_redis_integration(provider):
    """Test Redis integration"""
    print("🔍 Testing Redis integration...")
    
    try:
        # Test Redis connection
        redis_client = provider.redis_client
        redis_client.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis integration failed: {e}")
        return False

async def test_websocket_manager_integration(provider):
    """Test WebSocket manager integration"""
    print("🔍 Testing WebSocket manager integration...")
    
    try:
        # Test WebSocket manager
        ws_manager = provider.ws_manager
        print("✅ WebSocket manager integration successful")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket manager integration failed: {e}")
        return False

async def test_provider_disconnection(provider):
    """Test provider disconnection"""
    print("🔍 Testing provider disconnection...")
    
    try:
        # Disconnect from TrueData
        success = await provider.disconnect()
        
        if success:
            print("✅ TrueData provider disconnection successful")
            return True
        else:
            print("❌ TrueData provider disconnection failed")
            return False
            
    except Exception as e:
        print(f"❌ Provider disconnection failed: {e}")
        return False

async def main():
    """Main integration test function"""
    print("🧪 TrueData Integration Test with Trading System")
    print("=" * 60)
    
    # Test 1: Import tests
    provider_import = test_truedata_provider_import()
    config_import = test_config_import()
    
    if not provider_import or not config_import:
        print("\n❌ Import tests failed. Check your installation.")
        return
    
    # Get configuration
    try:
        from config.truedata_config import get_config, DEFAULT_SYMBOLS, OPTIONS_SYMBOLS
        
        # Use sandbox config for testing
        config = get_config(is_sandbox=True)
        
        # Override with environment variables if available
        username = os.getenv('TRUEDATA_USERNAME')
        password = os.getenv('TRUEDATA_PASSWORD')
        
        if username and password:
            config['username'] = username
            config['password'] = password
            config['is_sandbox'] = False  # Use production if credentials provided
        
        print(f"📋 Using configuration: {'Sandbox' if config['is_sandbox'] else 'Production'}")
        
    except Exception as e:
        print(f"❌ Configuration setup failed: {e}")
        return
    
    # Test 2: Provider initialization
    init_success, provider = await test_provider_initialization(config)
    if not init_success:
        print("\n❌ Provider initialization failed.")
        return
    
    # Test 3: Connection
    connection_success = await test_provider_connection(provider)
    if not connection_success:
        print("\n❌ Provider connection failed.")
        return
    
    # Test 4: Market data subscription
    symbols = DEFAULT_SYMBOLS[:3]  # Test with first 3 symbols
    subscription_success = await test_market_data_subscription(provider, symbols)
    
    # Test 5: Historical data
    historical_success = await test_historical_data_retrieval(provider, 'NIFTY-I')
    
    # Test 6: Options chain
    options_success = await test_options_chain_retrieval(provider, 'NIFTY')
    
    # Test 7: Redis integration
    redis_success = await test_redis_integration(provider)
    
    # Test 8: WebSocket manager integration
    ws_success = await test_websocket_manager_integration(provider)
    
    # Test 9: Disconnection
    disconnection_success = await test_provider_disconnection(provider)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Integration Test Results Summary:")
    print(f"   ✅ Provider Import: {provider_import}")
    print(f"   ✅ Config Import: {config_import}")
    print(f"   ✅ Provider Init: {init_success}")
    print(f"   ✅ Connection: {connection_success}")
    print(f"   ✅ Market Data: {subscription_success}")
    print(f"   ✅ Historical Data: {historical_success}")
    print(f"   ✅ Options Chain: {options_success}")
    print(f"   ✅ Redis Integration: {redis_success}")
    print(f"   ✅ WebSocket Manager: {ws_success}")
    print(f"   ✅ Disconnection: {disconnection_success}")
    
    success_count = sum([
        provider_import, config_import, init_success, connection_success,
        subscription_success, historical_success, options_success,
        redis_success, ws_success, disconnection_success
    ])
    total_tests = 10
    
    print(f"\n🎯 Overall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All integration tests passed! TrueData is fully integrated.")
    elif success_count >= 7:
        print("⚠️  Most integration tests passed. TrueData is mostly integrated.")
    else:
        print("❌ Many integration tests failed. Check TrueData setup.")
    
    print("\n💡 Next steps:")
    print("   1. Configure TrueData credentials in .env file")
    print("   2. Test with your actual trading symbols")
    print("   3. Monitor system performance")
    print("   4. Set up error handling and logging")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Integration test interrupted by user")
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc() 
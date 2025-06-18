#!/usr/bin/env python3
"""
TrueData Basic Test Script
Tests TrueData installation and basic functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_truedata_import():
    """Test TrueData package import"""
    print("🔍 Testing TrueData package import...")
    
    # Try different import methods
    import_methods = [
        ("truedata_ws", "TD_live, TD_hist"),
        ("truedata", "TD_live, TD_hist"),
        ("truedata_ws", "TD_live"),
        ("truedata", "TD_live")
    ]
    
    for package, classes in import_methods:
        try:
            if classes == "TD_live, TD_hist":
                from truedata_ws import TD_live, TD_hist
                print(f"✅ Successfully imported {classes} from {package}")
                return True, package, "TD_live, TD_hist"
            elif classes == "TD_live":
                from truedata_ws import TD_live
                print(f"✅ Successfully imported {classes} from {package}")
                return True, package, "TD_live"
        except ImportError:
            try:
                if classes == "TD_live, TD_hist":
                    from truedata import TD_live, TD_hist
                    print(f"✅ Successfully imported {classes} from {package}")
                    return True, package, "TD_live, TD_hist"
                elif classes == "TD_live":
                    from truedata import TD_live
                    print(f"✅ Successfully imported {classes} from {package}")
                    return True, package, "TD_live"
            except ImportError:
                continue
    
    print("❌ Failed to import TrueData packages")
    print("💡 Install with: pip install truedata-ws")
    return False, None, None

def test_basic_connection(username: str, password: str, package: str):
    """Test basic TrueData connection"""
    print(f"\n🔗 Testing TrueData connection with {package}...")
    
    try:
        if package == "truedata_ws":
            from truedata_ws import TD_live
        else:
            from truedata import TD_live
        
        # Initialize client
        live_client = TD_live(
            username=username,
            password=password,
            live_port=8084
        )
        
        print("✅ TrueData client initialized")
        
        # Try to connect
        try:
            live_client.connect()
            print("✅ TrueData connection successful")
            return True, live_client
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False, None
            
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False, None

def test_historical_data(username: str, password: str, package: str):
    """Test historical data retrieval"""
    print(f"\n📊 Testing historical data with {package}...")
    
    try:
        if package == "truedata_ws":
            from truedata_ws import TD_hist
        else:
            from truedata import TD_hist
        
        # Initialize historical client
        hist_client = TD_hist(
            username=username,
            password=password
        )
        
        print("✅ Historical client initialized")
        
        # Get historical data
        try:
            data = hist_client.get_historical_data(
                symbol='NIFTY-I',
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now(),
                bar_size='1 min'
            )
            
            if data is not None and len(data) > 0:
                print(f"✅ Historical data retrieved: {len(data)} records")
                print(f"   Sample data: {data.head() if hasattr(data, 'head') else data[:5]}")
                return True
            else:
                print("⚠️  No historical data returned")
                return False
                
        except Exception as e:
            print(f"❌ Historical data retrieval failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Historical client initialization failed: {e}")
        return False

def test_live_data_subscription(live_client, symbols: list):
    """Test live data subscription"""
    print(f"\n📡 Testing live data subscription...")
    
    try:
        # Subscribe to symbols
        live_client.start_live_data(symbols)
        print(f"✅ Live data subscription successful for: {symbols}")
        return True
        
    except Exception as e:
        print(f"❌ Live data subscription failed: {e}")
        return False

def test_options_chain(live_client, symbol: str):
    """Test options chain retrieval"""
    print(f"\n📋 Testing options chain for {symbol}...")
    
    try:
        # Get options chain
        chain = live_client.get_option_chain(symbol)
        
        if chain is not None:
            print(f"✅ Options chain retrieved for {symbol}")
            print(f"   Chain data: {len(chain)} records")
            return True
        else:
            print(f"⚠️  No options chain data for {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Options chain retrieval failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 TrueData Installation and Connection Test")
    print("=" * 50)
    
    # Get credentials from environment or user input
    username = os.getenv('TRUEDATA_USERNAME')
    password = os.getenv('TRUEDATA_PASSWORD')
    
    if not username or not password:
        print("⚠️  TrueData credentials not found in environment variables")
        print("💡 Set TRUEDATA_USERNAME and TRUEDATA_PASSWORD environment variables")
        print("💡 Or enter credentials manually:")
        
        username = input("Enter TrueData username: ").strip()
        password = input("Enter TrueData password: ").strip()
        
        if not username or not password:
            print("❌ No credentials provided. Exiting.")
            return
    
    # Test 1: Import
    import_success, package, classes = test_truedata_import()
    if not import_success:
        print("\n❌ TrueData package not installed or not working")
        print("💡 Install with: pip install truedata-ws")
        return
    
    # Test 2: Basic Connection
    connection_success, live_client = test_basic_connection(username, password, package)
    if not connection_success:
        print("\n❌ TrueData connection failed")
        print("💡 Check your credentials and network connection")
        return
    
    # Test 3: Historical Data
    historical_success = test_historical_data(username, password, package)
    
    # Test 4: Live Data Subscription
    symbols = ['NIFTY-I', 'BANKNIFTY-I']
    live_success = test_live_data_subscription(live_client, symbols)
    
    # Test 5: Options Chain
    options_success = test_options_chain(live_client, 'NIFTY')
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   ✅ Import: {import_success}")
    print(f"   ✅ Connection: {connection_success}")
    print(f"   ✅ Historical Data: {historical_success}")
    print(f"   ✅ Live Data: {live_success}")
    print(f"   ✅ Options Chain: {options_success}")
    
    success_count = sum([import_success, connection_success, historical_success, live_success, options_success])
    total_tests = 5
    
    print(f"\n🎯 Overall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! TrueData is working correctly.")
    elif success_count >= 3:
        print("⚠️  Most tests passed. TrueData is partially working.")
    else:
        print("❌ Many tests failed. Check TrueData installation and credentials.")
    
    print("\n💡 Next steps:")
    print("   1. Configure TrueData in your trading system")
    print("   2. Test with your actual symbols")
    print("   3. Monitor for any issues")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 
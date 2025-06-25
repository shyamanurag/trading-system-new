#!/usr/bin/env python3
"""
Check TrueData Live Connection
Test the TrueData connection that was working yesterday
"""
import os
import time
import logging
from datetime import datetime
from truedata import TD_live

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_truedata_connection():
    """Test TrueData connection with the working credentials from yesterday"""
    print("🔍 Testing TrueData Connection (Market Hours)")
    print("=" * 50)
    
    # Use the working credentials from yesterday
    username = "tdwsp697"
    password = "shyam@697"
    
    print(f"Credentials: {username} / {password}")
    print(f"Testing during market hours: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        print("\n📡 Initializing TrueData client...")
        
        # Initialize exactly as working yesterday
        td_obj = TD_live(
            username,
            password,
            live_port=8084,
            log_level=logging.WARNING,
            url="push.truedata.in",
            compression=False
        )
        
        print("✅ TrueData client initialized successfully")
        
        # Test symbols (using simple ones first)
        test_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE"]
        
        # Set up callback to capture data
        received_data = []
        
        @td_obj.trade_callback
        def capture_tick_data(tick_data):
            """Capture tick data for testing"""
            received_data.append({
                'type': 'tick',
                'data': tick_data,
                'timestamp': datetime.now().isoformat()
            })
            symbol = tick_data.get('symbol', 'UNKNOWN') if isinstance(tick_data, dict) else str(tick_data)
            print(f"   📊 Live Tick: {symbol} -> {tick_data}")
        
        print(f"\n📡 Subscribing to symbols: {test_symbols}")
        
        # Subscribe to symbols
        req_ids = td_obj.start_live_data(test_symbols)
        print(f"✅ Subscription request sent, IDs: {req_ids}")
        
        print("\n⏳ Waiting 15 seconds for live data...")
        start_time = time.time()
        
        while time.time() - start_time < 15:
            time.sleep(1)
            if received_data:
                print(f"   Data received: {len(received_data)} packets")
        
        # Results
        if received_data:
            print(f"\n🎉 SUCCESS: Received {len(received_data)} live data packets!")
            print("   TrueData connection is working during market hours")
            
            # Show sample data
            for i, data in enumerate(received_data[:3]):
                print(f"   Sample {i+1}: {data}")
            
            return True
        else:
            print(f"\n⚠️  No live data received")
            print("   Possible reasons:")
            print("   - Market might be closed")
            print("   - Subscription limit reached")
            print("   - Network connectivity issues")
            print("   - Symbol subscription issues")
            
            return False
        
    except Exception as e:
        print(f"\n❌ TrueData connection failed: {e}")
        return False

def check_environment_variables():
    """Check if TrueData environment variables are set"""
    print("\n🔧 Checking Environment Variables:")
    
    env_vars = {
        'TRUEDATA_USERNAME': os.getenv('TRUEDATA_USERNAME'),
        'TRUEDATA_PASSWORD': os.getenv('TRUEDATA_PASSWORD'),
        'TRUEDATA_IS_SANDBOX': os.getenv('TRUEDATA_IS_SANDBOX')
    }
    
    for var, value in env_vars.items():
        status = "✅ SET" if value else "❌ NOT SET"
        print(f"   {var}: {status} ({value})")
    
    return env_vars

if __name__ == "__main__":
    print("🚀 TrueData Live Connection Test")
    print("Testing the configuration that worked yesterday")
    print("=" * 60)
    
    # Check environment
    env_vars = check_environment_variables()
    
    # Test connection
    success = test_truedata_connection()
    
    print("\n" + "=" * 60)
    print("📊 CONNECTION TEST RESULTS")
    print(f"TrueData Connection: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 TrueData is working correctly!")
        print("   Live market data is flowing from your subscription")
        print("   The issue with 'market closed' might be in the app's market status logic")
    else:
        print("\n⚠️  TrueData connection issues detected")
        print("   This could explain why the app shows 'market closed'")
        
    print("\n🔄 Next Steps:")
    if success:
        print("   1. TrueData is working - check app's market status API")
        print("   2. Verify timezone fixes are deployed")
        print("   3. Check if app is connecting to TrueData properly")
    else:
        print("   1. Check TrueData subscription status")
        print("   2. Verify credentials are correct")
        print("   3. Check network connectivity")
        print("   4. Contact TrueData support if needed") 
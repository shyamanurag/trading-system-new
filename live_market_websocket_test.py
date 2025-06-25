#!/usr/bin/env python3
"""
Live Market WebSocket Test - Test TrueData WebSocket SDK during market hours
Using the correct TrueData WebSocket SDK approach
"""
import os
import time
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from truedata import TD_live
    TRUEDATA_AVAILABLE = True
    print("✅ TrueData library found")
except ImportError as e:
    TRUEDATA_AVAILABLE = False
    print(f"❌ TrueData library not available: {e}")
    print("   Install with: pip install truedata")

def check_market_timing():
    """Check if market should be open"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    print(f"\n⏰ Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Weekday: {weekday} (0=Mon, 6=Sun)")
    
    # Market hours: 9:15 AM to 3:30 PM, Monday to Friday
    if weekday < 5:  # Monday to Friday
        if (hour == 9 and minute >= 15) or (10 <= hour <= 14) or (hour == 15 and minute <= 30):
            print("   📈 Market should be OPEN")
            return True
        else:
            print("   📉 Market should be CLOSED")
            return False
    else:
        print("   📅 Weekend - Market CLOSED")
        return False

def test_truedata_websocket():
    """Test TrueData WebSocket connection with live credentials"""
    if not TRUEDATA_AVAILABLE:
        print("❌ Cannot test - TrueData library not available")
        return False
    
    print("\n🔍 Testing TrueData WebSocket Connection")
    
    # Use your actual credentials
    username = "tdwsp697" 
    password = "shyam@697"
    
    # Test symbols
    test_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]
    
    try:
        print(f"   Connecting with user: {username}")
        
        # Initialize TrueData WebSocket client
        td_obj = TD_live(
            username=username,
            password=password,
            live_port=8084,
            url="push.truedata.in",
            log_level=logging.WARNING
        )
        print("   ✅ TrueData client initialized")
        
        # Set up data handlers
        received_data = {}
        
        @td_obj.trade_callback
        def trade_callback(tick_data):
            """Handle live tick data"""
            symbol = tick_data[0] if isinstance(tick_data, list) and tick_data else "UNKNOWN"
            received_data[symbol] = {
                'type': 'tick',
                'data': tick_data,
                'timestamp': datetime.now().isoformat()
            }
            print(f"   📊 Live Data: {symbol} -> {tick_data}")
        
        # Subscribe to test symbols
        print(f"   📡 Subscribing to symbols: {test_symbols}")
        for symbol in test_symbols:
            td_obj.subscribe_symbol(symbol)
            print(f"   ✓ Subscribed to {symbol}")
        
        # Wait for data
        print("   ⏳ Waiting for live data (10 seconds)...")
        time.sleep(10)
        
        # Check results
        if received_data:
            print(f"\n   ✅ SUCCESS: Received data for {len(received_data)} symbols")
            for symbol, data in received_data.items():
                print(f"      📈 {symbol}: {data['data']}")
            return True
        else:
            print("\n   ⚠️  No live data received")
            print("      Possible reasons:")
            print("      - Market is closed")
            print("      - Subscription not active")
            print("      - Network issues")
            return False
            
    except Exception as e:
        print(f"   ❌ TrueData connection failed: {e}")
        return False

def test_production_app_direct():
    """Test production app with a simple GET request to root"""
    print("\n🏭 Testing Production App")
    
    import requests
    
    base_urls = [
        "https://trading-system-new-latest-8yvfj.ondigitalocean.app",
        "https://trading-system-new-app-8yvfj.ondigitalocean.app",  # Alternative URL
    ]
    
    for url in base_urls:
        try:
            print(f"   Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ App is accessible")
                return True
            else:
                print(f"   ⚠️  Status: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout accessing {url}")
        except Exception as e:
            print(f"   ❌ Error accessing {url}: {e}")
    
    print("   ❌ Production app not accessible")
    return False

def main():
    """Main test function"""
    print("🚀 Live Market WebSocket Test")
    print("=" * 60)
    
    # Check market timing
    market_open = check_market_timing()
    
    # Test TrueData WebSocket
    truedata_success = test_truedata_websocket()
    
    # Test production app
    app_success = test_production_app_direct()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print(f"   Market Status: {'OPEN' if market_open else 'CLOSED'}")
    print(f"   TrueData: {'✅ Working' if truedata_success else '❌ Failed'}")
    print(f"   Production App: {'✅ Accessible' if app_success else '❌ Failed'}")
    
    if market_open and not truedata_success:
        print("\n🚨 CRITICAL: Market is open but TrueData not working!")
        print("   Recommendations:")
        print("   1. Check TrueData subscription status")
        print("   2. Verify credentials")
        print("   3. Check network connectivity")
        print("   4. Contact TrueData support if needed")
    
    if not app_success:
        print("\n🚨 CRITICAL: Production app not accessible!")
        print("   Recommendations:")
        print("   1. Check DigitalOcean deployment status")
        print("   2. Verify app domain/URL")
        print("   3. Check app logs")
    
    print("\n🏁 Test Complete")

if __name__ == "__main__":
    main() 
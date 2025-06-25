#!/usr/bin/env python3
"""
TrueData Last Traded Price Test
Tests TrueData connection and fetches last traded prices for major symbols
"""

import asyncio
import time
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from truedata import TD_live
    TRUEDATA_AVAILABLE = True
    print("✅ TrueData library found")
except ImportError as e:
    TRUEDATA_AVAILABLE = False
    print(f"❌ TrueData library not available: {e}")

class TrueDataLTPTest:
    def __init__(self):
        self.td_client = None
        self.symbols_data = {}
        
        # Real subscription credentials
        self.username = "tdwsp697"
        self.password = "shyam@697"
        self.port = 8084
        
        # Major symbols to test
        self.test_symbols = [
            'RELIANCE',
            'TCS', 
            'HDFC',
            'INFY',
            'ICICIBANK',
            'HDFCBANK',
            'ITC',
            'NIFTY',
            'BANKNIFTY',
            'FINNIFTY'
        ]
        
    def connect_truedata(self):
        """Connect to TrueData service"""
        if not TRUEDATA_AVAILABLE:
            print("❌ Cannot connect - TrueData library not available")
            return False
            
        try:
            print(f"🔄 Connecting to TrueData...")
            print(f"   Username: {self.username}")
            print(f"   Port: {self.port}")
            
            # Initialize TrueData client
            self.td_client = TD_live(
                login_id=self.username,
                password=self.password,
                live_port=self.port,
                compression=False  # Avoid decompression bugs
            )
            
            print("✅ TrueData connection established")
            return True
            
        except Exception as e:
            print(f"❌ TrueData connection failed: {e}")
            return False
    
    def trade_callback(self, tick_data):
        """Callback for trade data"""
        try:
            symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
            ltp = getattr(tick_data, 'ltp', 0)
            volume = getattr(tick_data, 'volume', 0)
            timestamp = getattr(tick_data, 'timestamp', None)
            
            # Store latest data
            self.symbols_data[symbol] = {
                'ltp': ltp,
                'volume': volume,
                'timestamp': timestamp,
                'last_updated': datetime.now()
            }
            
            print(f"📊 {symbol}: LTP ₹{ltp:,.2f}, Volume: {volume:,}")
            
        except Exception as e:
            print(f"❌ Error in trade callback: {e}")
    
    def subscribe_symbols(self):
        """Subscribe to test symbols"""
        if not self.td_client:
            print("❌ No TrueData client available")
            return False
            
        try:
            print(f"🔄 Subscribing to {len(self.test_symbols)} symbols...")
            
            # Subscribe to NSE symbols
            for symbol in self.test_symbols:
                try:
                    self.td_client.subscribe_symbol(
                        exchange="NSE",
                        symbol=symbol,
                        callback=self.trade_callback
                    )
                    print(f"   ✅ {symbol} subscribed")
                    time.sleep(0.1)  # Small delay between subscriptions
                    
                except Exception as e:
                    print(f"   ❌ {symbol} subscription failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Subscription failed: {e}")
            return False
    
    def get_ltp_data(self, wait_time=10):
        """Get last traded prices and wait for data"""
        if not self.subscribe_symbols():
            return False
            
        print(f"⏳ Waiting {wait_time} seconds for data...")
        
        start_time = time.time()
        while time.time() - start_time < wait_time:
            time.sleep(1)
            
            # Show progress
            elapsed = int(time.time() - start_time)
            remaining = wait_time - elapsed
            print(f"⏱️  {remaining}s remaining... ({len(self.symbols_data)} symbols received data)")
        
        return True
    
    def display_results(self):
        """Display final results"""
        print("\n" + "="*60)
        print("📈 LAST TRADED PRICES SUMMARY")
        print("="*60)
        
        if not self.symbols_data:
            print("❌ No data received from any symbols")
            return
            
        print(f"✅ Received data from {len(self.symbols_data)} symbols:")
        print()
        
        # Sort by symbol name
        for symbol in sorted(self.symbols_data.keys()):
            data = self.symbols_data[symbol]
            ltp = data['ltp']
            volume = data['volume']
            last_updated = data['last_updated'].strftime("%H:%M:%S")
            
            print(f"📊 {symbol:12} | LTP: ₹{ltp:>10,.2f} | Volume: {volume:>12,} | Time: {last_updated}")
        
        print()
        print(f"🕒 Data captured at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show market status
        current_time = datetime.now().time()
        if current_time.hour >= 9 and current_time.hour < 16:
            print("📈 Market Status: OPEN (Live Data)")
        else:
            print("📉 Market Status: CLOSED (Last Traded Prices)")
    
    def run_test(self):
        """Run the complete test"""
        print("🚀 TrueData Last Traded Price Test")
        print("="*50)
        
        # Connect
        if not self.connect_truedata():
            return False
        
        # Get data
        if not self.get_ltp_data(wait_time=15):
            return False
        
        # Show results
        self.display_results()
        
        # Cleanup
        try:
            if self.td_client:
                # No explicit disconnect method in some versions
                print("\n✅ Test completed successfully")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        return True

def main():
    """Main function"""
    test = TrueDataLTPTest()
    
    try:
        success = test.run_test()
        if success:
            print("\n🎉 TrueData LTP test completed successfully!")
        else:
            print("\n❌ TrueData LTP test failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
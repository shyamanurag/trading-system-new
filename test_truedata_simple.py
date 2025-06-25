#!/usr/bin/env python3
"""
Simple TrueData Connection Test
Tests essential TrueData functionality only
"""

def test_truedata_connection():
    """Test TrueData connection and data flow"""
    print("🚀 TrueData Simple Connection Test")
    print("=" * 50)
    
    try:
        # Test imports
        from data.truedata_client import truedata_client, live_market_data
        from config.truedata_symbols import get_default_subscription_symbols, DISPLAY_NAMES
        
        print("✅ Imports successful")
        
        # Check connection status
        if truedata_client.connected:
            print("✅ TrueData already connected")
        else:
            print("🔄 Connecting to TrueData...")
            if truedata_client.connect():
                print("✅ TrueData connected successfully")
            else:
                print("❌ TrueData connection failed")
                return False
        
        # Get default symbols
        symbols = get_default_subscription_symbols()
        print(f"📊 Testing {len(symbols)} symbols: {symbols}")
        
        # Check live data
        print("\n📈 LIVE DATA STATUS:")
        print("-" * 30)
        
        for symbol in symbols:
            data = live_market_data.get(symbol, {})
            if data:
                display_name = DISPLAY_NAMES.get(symbol, symbol)
                ltp = data.get('ltp', 0)
                volume = data.get('volume', 0)
                timestamp = data.get('timestamp', 'No timestamp')
                
                print(f"{display_name:15} | ₹{ltp:>10,.2f} | Vol: {volume:>8,} | {timestamp}")
            else:
                print(f"{symbol:15} | NO DATA")
        
        print("\n✅ TrueData test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_truedata_connection() 
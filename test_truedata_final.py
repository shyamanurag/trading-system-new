#!/usr/bin/env python3
"""
Final TrueData Last Traded Price Test
Parses TrueData array format correctly to extract LTP data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def parse_truedata_response(data):
    """Parse TrueData response format"""
    if not data or not isinstance(data, list):
        return {}
        
    results = {}
    
    for item in data:
        if isinstance(item, list) and len(item) >= 6:
            # TrueData format: [symbol, token, timestamp, prev_close, change, ltp, volume, high, low, open, close, ...]
            symbol = item[0]
            timestamp = item[2] 
            prev_close = float(item[3]) if item[3] else 0
            ltp = float(item[5]) if item[5] else 0  # LTP is at index 5
            volume = int(item[6]) if item[6] else 0
            high = float(item[7]) if item[7] else 0
            low = float(item[8]) if item[8] else 0
            open_price = float(item[9]) if item[9] else 0
            
            results[symbol] = {
                'ltp': ltp,
                'prev_close': prev_close,
                'volume': volume,
                'high': high,
                'low': low,
                'open': open_price,
                'timestamp': timestamp,
                'change': ltp - prev_close if ltp and prev_close else 0,
                'change_percent': ((ltp - prev_close) / prev_close * 100) if ltp and prev_close else 0
            }
    
    return results

def test_truedata_ltp():
    """Test TrueData last traded prices with proper parsing"""
    
    print("🚀 TrueData Final LTP Test")
    print("="*60)
    
    try:
        print("🔧 Importing TrueData client...")
        from data.truedata_client import truedata_client
        
        print("✅ TrueData client imported successfully")
        
        # Connect to TrueData
        print("🔧 Connecting to TrueData...")
        
        if hasattr(truedata_client, 'connect'):
            result = truedata_client.connect()
            if result:
                print("✅ TrueData connected successfully")
            else:
                print("❌ TrueData connection failed")
                return False
        else:
            print("⚠️  No connect method found, assuming already connected")
        
        # Test symbols
        test_symbols = [
            'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 
            'HDFCBANK', 'ITC', 'NIFTY', 'BANKNIFTY', 'FINNIFTY'
        ]
        
        print(f"\n🔍 Requesting data for {len(test_symbols)} symbols...")
        
        # Get raw data from TrueData
        raw_data = None
        
        if hasattr(truedata_client, 'get_data_for_symbols'):
            raw_data = truedata_client.get_data_for_symbols(test_symbols)
        elif hasattr(truedata_client, 'get_live_data'):
            raw_data = truedata_client.get_live_data(test_symbols)
        else:
            # Try to get data using available methods
            methods = [m for m in dir(truedata_client) if not m.startswith('_') and 'get' in m.lower()]
            print(f"🔧 Available get methods: {methods}")
            
            # Try the most likely method
            if hasattr(truedata_client, 'get_quotes'):
                raw_data = truedata_client.get_quotes(test_symbols)
        
        print(f"🔧 Raw data type: {type(raw_data)}")
        
        if raw_data:
            print(f"✅ Received raw data: {len(str(raw_data))} characters")
            
            # Parse the data
            parsed_data = parse_truedata_response(raw_data)
            
            if parsed_data:
                print(f"\n✅ Successfully parsed data for {len(parsed_data)} symbols")
                
                # Display results
                print("\n" + "="*80)
                print("📈 LAST TRADED PRICES (Market Closed)")
                print("="*80)
                
                print(f"{'Symbol':<12} | {'LTP':<10} | {'Change':<8} | {'Change%':<8} | {'Volume':<12} | {'Time'}")
                print("-" * 80)
                
                for symbol in sorted(parsed_data.keys()):
                    data = parsed_data[symbol]
                    ltp = data['ltp']
                    change = data['change']
                    change_pct = data['change_percent']
                    volume = data['volume']
                    timestamp = data['timestamp']
                    
                    # Format change with + or - sign
                    change_str = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
                    change_pct_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
                    
                    print(f"{symbol:<12} | ₹{ltp:<9.2f} | {change_str:<8} | {change_pct_str:<8} | {volume:<12,} | {timestamp}")
                
                print("\n" + "="*80)
                print(f"🕒 Data captured at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("📉 Market Status: CLOSED (Last Traded Prices from TrueData)")
                print("✅ TrueData subscription active and working!")
                
                return True
                
            else:
                print("❌ Failed to parse TrueData response")
                print(f"🔧 Raw data sample: {str(raw_data)[:200]}...")
                
        else:
            print("❌ No data received from TrueData")
            
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_truedata_ltp()
    
    if success:
        print("\n🎉 TrueData LTP test completed successfully!")
        print("💡 You now have access to last traded prices even when markets are closed!")
    else:
        print("\n❌ TrueData LTP test failed!")
        print("🔧 Check TrueData connection and subscription status") 
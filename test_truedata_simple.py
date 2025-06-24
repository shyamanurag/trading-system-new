#!/usr/bin/env python3
"""
Simple TrueData Test using existing working functions
Tests getting last traded prices using proven working methods
"""

import sys
from pathlib import Path
from datetime import datetime

print("🔧 Starting TrueData Simple Test...")
print(f"🔧 Python version: {sys.version}")
print(f"🔧 Current directory: {Path.cwd()}")

# Add src to path for imports
src_path = str(Path(__file__).parent / "src")
parent_path = str(Path(__file__).parent)
sys.path.insert(0, src_path)
sys.path.insert(0, parent_path)

print(f"🔧 Added to path: {src_path}")
print(f"🔧 Added to path: {parent_path}")

def test_truedata_ltp():
    """Test TrueData last traded prices using existing functions"""
    
    print("🚀 TrueData Simple LTP Test")
    print("="*50)
    
    try:
        print("🔧 Attempting imports...")
        
        # Import existing working functions
        from data.truedata_client import get_live_data_for_symbol, truedata_client
        
        print("✅ TrueData client functions imported successfully")
        
        # Test symbols
        test_symbols = [
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
        
        print(f"🔍 Testing {len(test_symbols)} symbols...")
        print()
        
        results = {}
        
        # Get data for each symbol
        for symbol in test_symbols:
            try:
                print(f"📊 Getting data for {symbol}...", end=" ")
                
                # Use the existing working function
                data = get_live_data_for_symbol(symbol)
                
                if data and isinstance(data, dict):
                    # Extract LTP and other data
                    ltp = data.get('ltp', 0) or data.get('last_price', 0)
                    volume = data.get('volume', 0) or data.get('total_volume', 0)
                    timestamp = data.get('timestamp', datetime.now())
                    
                    results[symbol] = {
                        'ltp': ltp,
                        'volume': volume,
                        'timestamp': timestamp,
                        'raw_data': data
                    }
                    
                    print(f"✅ LTP: ₹{ltp:,.2f}")
                    
                else:
                    print(f"❌ No data (got: {type(data)})")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
        print()
        print("="*60)
        print("📈 LAST TRADED PRICES SUMMARY")
        print("="*60)
        
        if not results:
            print("❌ No data received from any symbols")
            return False
            
        print(f"✅ Received data from {len(results)} symbols:")
        print()
        
        # Display results in a nice format
        for symbol in sorted(results.keys()):
            data = results[symbol]
            ltp = data['ltp']
            volume = data['volume']
            
            print(f"📊 {symbol:12} | LTP: ₹{ltp:>10,.2f} | Volume: {volume:>12,}")
        
        print()
        print(f"🕒 Data captured at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show market status
        current_time = datetime.now().time()
        if current_time.hour >= 9 and current_time.hour < 16:
            print("📈 Market Status: OPEN (Live Data)")
        else:
            print("📉 Market Status: CLOSED (Last Traded Prices)")
            
        print()
        print("🎉 TrueData Simple LTP test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Checking if truedata_client.py exists...")
        
        # Check if file exists
        truedata_path = Path(__file__).parent / "data" / "truedata_client.py"
        if truedata_path.exists():
            print(f"✅ File exists: {truedata_path}")
        else:
            print(f"❌ File not found: {truedata_path}")
            
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Script starting...")
    result = test_truedata_ltp()
    print(f"🔧 Test result: {result}")
    print("🔧 Script completed.") 
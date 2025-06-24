#!/usr/bin/env python3
"""
Direct TrueData Connection Test
Checks TrueData status and connects if needed, then gets LTP data
"""

import sys
from pathlib import Path
from datetime import datetime

print("🔧 Starting Direct TrueData Test...")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def test_truedata_direct():
    """Test TrueData with direct connection management"""
    
    print("🚀 TrueData Direct Connection Test")
    print("="*50)
    
    try:
        print("🔧 Importing TrueData client...")
        from data.truedata_client import truedata_client, get_live_data_for_symbol
        
        print("✅ TrueData client imported successfully")
        
        # Check client status
        print("🔧 Checking TrueData client status...")
        
        if hasattr(truedata_client, 'client') and truedata_client.client:
            print("✅ TrueData client is initialized")
        else:
            print("❌ TrueData client not initialized - attempting to connect...")
            
            # Try to connect
            try:
                # Call connect method if available
                if hasattr(truedata_client, 'connect'):
                    result = truedata_client.connect()
                    print(f"🔧 Connection result: {result}")
                elif hasattr(truedata_client, 'initialize'):
                    result = truedata_client.initialize()
                    print(f"🔧 Initialize result: {result}")
                else:
                    print("🔧 Looking for connection methods...")
                    methods = [m for m in dir(truedata_client) if not m.startswith('_')]
                    print(f"🔧 Available methods: {methods}")
                    
            except Exception as e:
                print(f"❌ Connection failed: {e}")
        
        # Test a few key symbols
        test_symbols = ['RELIANCE', 'TCS', 'NIFTY', 'BANKNIFTY']
        
        print(f"\n🔍 Testing {len(test_symbols)} key symbols...")
        
        results = {}
        
        for symbol in test_symbols:
            try:
                print(f"📊 {symbol}...", end=" ")
                
                # Get data using the existing function
                data = get_live_data_for_symbol(symbol) 
                
                if data:
                    print(f"✅ Got data: {type(data)}")
                    
                    # Try to extract LTP from different possible fields
                    ltp = None
                    if isinstance(data, dict):
                        ltp = (data.get('ltp') or 
                               data.get('last_price') or 
                               data.get('close') or 
                               data.get('last_traded_price', 0))
                        
                        if ltp and ltp > 0:
                            results[symbol] = ltp
                            print(f"   💰 LTP: ₹{ltp:,.2f}")
                        else:
                            print(f"   ⚠️  No valid LTP found in data: {list(data.keys())}")
                    else:
                        print(f"   ⚠️  Unexpected data type: {type(data)}")
                        
                else:
                    print("❌ No data")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        # Show results
        print("\n" + "="*50)
        print("📈 RESULTS SUMMARY")
        print("="*50)
        
        if results:
            print(f"✅ Successfully got LTP for {len(results)} symbols:")
            for symbol, ltp in results.items():
                print(f"📊 {symbol:12}: ₹{ltp:>10,.2f}")
        else:
            print("❌ No LTP data retrieved")
            
            # Try to diagnose the issue
            print("\n🔧 DIAGNOSIS:")
            print("1. Check if TrueData subscription is active")
            print("2. Check if TrueData service is running")  
            print("3. Check network connectivity")
            print("4. Verify credentials in config")
        
        print(f"\n🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(results) > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_truedata_direct()
    print(f"\n🎯 Test {'PASSED' if success else 'FAILED'}") 
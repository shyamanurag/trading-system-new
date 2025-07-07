#!/usr/bin/env python3
"""
Initialize Shared TrueData Connection
====================================
Connects the autonomous trading system to existing TrueData connection
to solve the "User Already Connected" error.
"""

import logging
import sys
import os
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_shared_truedata_connection():
    """Initialize shared TrueData connection for autonomous trading"""
    
    print("🚀 INITIALIZING SHARED TRUEDATA CONNECTION")
    print("=" * 60)
    
    try:
        # Step 1: Import shared TrueData manager
        print("STEP 1: Importing shared TrueData manager...")
        from src.core.shared_truedata_manager import get_shared_truedata_manager, initialize_shared_truedata
        
        manager = get_shared_truedata_manager()
        print("✅ Shared TrueData manager imported successfully")
        
        # Step 2: Check if there's already an existing TrueData connection
        print("\\nSTEP 2: Checking for existing TrueData connections...")
        
        # Method 1: Check for existing truedata_client
        try:
            from data.truedata_client import live_market_data, get_truedata_status
            
            status = get_truedata_status()
            print(f"TrueData client status: {status}")
            
            if status.get('connected', False):
                print("✅ Found existing TrueData connection!")
                
                # Register the existing connection with shared manager
                print("\\nSTEP 3: Registering existing connection with shared manager...")
                
                connection_data = {
                    'live_data': live_market_data,
                    'source': 'existing_truedata_client',
                    'timestamp': datetime.now().isoformat()
                }
                
                success = manager.register_existing_connection(connection_data)
                
                if success:
                    print("✅ Successfully registered existing TrueData connection")
                    
                    # Verify the connection
                    shared_status = manager.get_connection_status()
                    print(f"\\nShared connection status:")
                    print(f"  - Connected: {shared_status.get('connected', False)}")
                    print(f"  - Symbols: {shared_status.get('symbols_count', 0)}")
                    print(f"  - Data source: {shared_status.get('data_source', 'unknown')}")
                    
                    # Test data retrieval
                    print("\\nSTEP 4: Testing data retrieval...")
                    test_data = manager.get_market_data()
                    print(f"Retrieved {len(test_data)} symbols from shared connection")
                    
                    if len(test_data) > 0:
                        # Show sample data
                        sample_symbols = list(test_data.keys())[:3]
                        for symbol in sample_symbols:
                            data = test_data[symbol]
                            ltp = data.get('ltp', 'N/A')
                            print(f"  - {symbol}: LTP = {ltp}")
                    
                    print("\\n🎉 SHARED TRUEDATA CONNECTION INITIALIZED SUCCESSFULLY!")
                    print("The autonomous trading system can now access market data")
                    print("without creating duplicate connections.")
                    
                    return True
                    
                else:
                    print("❌ Failed to register existing connection")
                    return False
                    
            else:
                print("❌ Existing TrueData connection not found or not connected")
                return False
                
        except Exception as e:
            print(f"❌ Error checking existing TrueData connection: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing shared TrueData connection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autonomous_system_access():
    """Test if autonomous system can now access market data"""
    
    print("\\n🧪 TESTING AUTONOMOUS SYSTEM ACCESS")
    print("=" * 50)
    
    try:
        # Test market data API
        from src.api.market_data import get_all_live_market_data, is_connected
        
        print("Testing market data API...")
        
        # Check connection
        connected = is_connected()
        print(f"Market data API connected: {connected}")
        
        if connected:
            # Get market data
            market_data = get_all_live_market_data()
            print(f"Market data retrieved: {len(market_data)} symbols")
            
            if len(market_data) > 0:
                print("✅ Autonomous system can access market data!")
                return True
            else:
                print("❌ No market data available to autonomous system")
                return False
        else:
            print("❌ Autonomous system cannot connect to market data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing autonomous system access: {e}")
        return False

def main():
    """Main initialization function"""
    
    print("🎯 AUTONOMOUS TRADING SYSTEM - TRUEDATA CONNECTION FIX")
    print("=" * 70)
    print("This script connects the autonomous trading system to your existing")
    print("TrueData connection to solve the 'User Already Connected' error.")
    print()
    
    # Initialize shared connection
    init_success = initialize_shared_truedata_connection()
    
    if init_success:
        # Test autonomous system access
        test_success = test_autonomous_system_access()
        
        if test_success:
            print("\\n🎉 SUCCESS! Autonomous trading system is now connected to TrueData!")
            print("\\nNext steps:")
            print("1. The autonomous trading system should now receive market data")
            print("2. Strategies should start generating signals")
            print("3. Orders should be placed automatically")
            
            return True
        else:
            print("\\n❌ Connection established but autonomous system access failed")
            return False
    else:
        print("\\n❌ Failed to initialize shared TrueData connection")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
Quick TrueData Connection Test - No Infinite Loops
Tests connection, gets sample data, and exits cleanly
"""

from truedata import TD_live
import time
import logging
import os
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables to store results
connection_status = {"connected": False, "error": None}
sample_data = {"tick_count": 0, "symbols_received": set(), "last_tick": None}
test_complete = False

def test_truedata_connection():
    """Test TrueData connection and get sample data"""
    global connection_status, sample_data, test_complete
    
    logger.info("🧪 Quick TrueData Connection Test")
    logger.info("=" * 50)
    
    # Get credentials
    username = os.getenv('TRUEDATA_USERNAME', '')
    password = os.getenv('TRUEDATA_PASSWORD', '')
    
    if not username or not password:
        logger.error("❌ TrueData credentials not found in environment!")
        connection_status["error"] = "Missing credentials"
        return
    
    logger.info(f"📋 Username: {username}")
    logger.info(f"📋 Password: {'*' * len(password)}")
    
    try:
        # Initialize TrueData client
        logger.info("🔌 Connecting to TrueData...")
        td_obj = TD_live(
            username, 
            password, 
            live_port=8084,
            log_level=logging.ERROR,  # Reduce noise
            url="push.truedata.in",
            compression=False
        )
        
        # Test symbols
        symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS']
        
        logger.info(f"📡 Subscribing to symbols: {symbols}")
        req_ids = td_obj.start_live_data(symbols)
        
        connection_status["connected"] = True
        logger.info("✅ TrueData connection successful!")
        
        # Set up callback to capture data
        @td_obj.trade_callback
        def capture_tick_data(tick_data):
            global sample_data
            sample_data["tick_count"] += 1
            
            # Extract symbol safely - tick_data is an object, not dict
            symbol = getattr(tick_data, 'symbol', 'UNKNOWN')
            price = getattr(tick_data, 'ltp', 0)
            volume = getattr(tick_data, 'volume', 0)
            
            sample_data["symbols_received"].add(symbol)
            sample_data["last_tick"] = {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 TICK: {symbol} - Price: ₹{price}, Volume: {volume:,}")
        
        logger.info("⏱️ Collecting data for 10 seconds...")
        
        # Wait for data for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.5)
            if sample_data["tick_count"] > 0:
                break
        
        test_complete = True
        
    except Exception as e:
        logger.error(f"❌ TrueData connection failed: {e}")
        connection_status["error"] = str(e)
        connection_status["connected"] = False

def print_results():
    """Print test results"""
    global connection_status, sample_data
    
    print("\n" + "=" * 60)
    print("🧪 TRUEDATA CONNECTION TEST RESULTS")
    print("=" * 60)
    
    # Connection status
    if connection_status["connected"]:
        print("✅ CONNECTION STATUS: SUCCESSFUL")
    else:
        print("❌ CONNECTION STATUS: FAILED")
        if connection_status["error"]:
            print(f"   Error: {connection_status['error']}")
    
    # Data received
    print(f"📊 TICKS RECEIVED: {sample_data['tick_count']}")
    print(f"📈 SYMBOLS WITH DATA: {len(sample_data['symbols_received'])}")
    
    if sample_data["symbols_received"]:
        print(f"   Symbols: {', '.join(sample_data['symbols_received'])}")
    
    # Last tick data
    if sample_data["last_tick"]:
        last = sample_data["last_tick"]
        print(f"🎯 LAST TICK:")
        print(f"   Symbol: {last['symbol']}")
        print(f"   Price: ₹{last['price']}")
        print(f"   Volume: {last['volume']:,}")
        print(f"   Time: {last['timestamp']}")
    
    # Diagnosis
    print("\n🔍 DIAGNOSIS:")
    if connection_status["connected"] and sample_data["tick_count"] > 0:
        print("✅ TrueData is working perfectly!")
        print("   - Connection successful")
        print("   - Live data flowing")
        print("   - Ready for trading system integration")
    elif connection_status["connected"] and sample_data["tick_count"] == 0:
        print("⚠️ TrueData connected but no data received")
        print("   - Check if markets are open")
        print("   - Verify symbol subscriptions")
        print("   - Check TrueData account permissions")
    else:
        print("❌ TrueData connection failed")
        print("   - Check credentials")
        print("   - Check internet connection")
        print("   - Check TrueData account status")
    
    print("=" * 60)

def main():
    """Main test function"""
    # Run test in a thread so we can control timing
    test_thread = threading.Thread(target=test_truedata_connection)
    test_thread.daemon = True
    test_thread.start()
    
    # Wait for test to complete or timeout
    test_thread.join(timeout=15)  # 15 second maximum
    
    # Print results
    print_results()
    
    # Exit cleanly
    logger.info("🏁 Test completed. Exiting...")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Standalone TrueData Live Market Data Script
Using Official TrueData Python SDK
Usage: python truedata_standalone.py
"""

from truedata import TD_live
import time
import logging
import json
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_credentials():
    """Load TrueData credentials from environment or config"""
    username = os.getenv('TRUEDATA_USERNAME', '')
    password = os.getenv('TRUEDATA_PASSWORD', '')
    
    if not username or not password:
        logger.error("❌ TrueData credentials not found!")
        logger.error("Please set environment variables:")
        logger.error("  TRUEDATA_USERNAME=your_username")
        logger.error("  TRUEDATA_PASSWORD=your_password")
        return None, None
    
    return username, password

def main():
    """Main function to run TrueData live data using official SDK"""
    logger.info("🚀 Starting TrueData Live Market Data (Official SDK)")
    logger.info("=" * 60)
    
    # Load credentials
    username, password = load_credentials()
    if not username or not password:
        return
    
    # Configuration (using official SDK defaults)
    port = 8084
    url = "push.truedata.in"
    
    # Symbols to subscribe to (as per your original script)
    symbols = [
        'CRUDEOIL2506165300CE',  # Crude Oil Call Option
        'CRUDEOIL2506165300PE',  # Crude Oil Put Option
        'NIFTY',                 # Nifty Index
        'BANKNIFTY',             # Bank Nifty Index
        'RELIANCE',              # Reliance Industries
        'TCS',                   # Tata Consultancy Services
        'HDFC',                  # HDFC Bank
        'INFY'                   # Infosys
    ]
    
    try:
        logger.info(f"Connecting to TrueData: {url}:{port}")
        logger.info(f"Username: {username}")
        logger.info(f"Symbols: {symbols}")
        
        # Initialize TrueData client using official SDK (exactly as in your script)
        td_obj = TD_live(
            username, 
            password, 
            live_port=port,
            log_level=logging.WARNING,
            url=url,
            compression=False
        )
        
        logger.info("✅ TrueData client initialized")
        
        # Start live data using official SDK method
        logger.info("Starting live data subscription...")
        req_ids = td_obj.start_live_data(symbols)
        logger.info(f"✅ Subscribed to {len(symbols)} symbols")
        
        # Wait for connection to establish (as per official SDK)
        time.sleep(1)
        
        # Set up callbacks using official SDK decorators (exactly as in your script)
        @td_obj.trade_callback
        def my_tick_data(tick_data):
            """Handle tick data using official SDK with enhanced volume parsing"""
            try:
                symbol = tick_data.get('symbol', 'UNKNOWN')
                price = tick_data.get('ltp', 0)
                
                # Enhanced volume parsing - try multiple field names like TrueData client
                volume = (tick_data.get('volume', 0) or 
                         tick_data.get('vol', 0) or 
                         tick_data.get('v', 0) or 
                         tick_data.get('total_volume', 0) or
                         tick_data.get('day_volume', 0) or
                         tick_data.get('traded_volume', 0))
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Enhanced logging shows which field contained volume
                vol_source = "none"
                if tick_data.get('volume', 0): vol_source = "volume"
                elif tick_data.get('vol', 0): vol_source = "vol"
                elif tick_data.get('v', 0): vol_source = "v"
                elif tick_data.get('total_volume', 0): vol_source = "total_volume"
                elif tick_data.get('day_volume', 0): vol_source = "day_volume"
                elif tick_data.get('traded_volume', 0): vol_source = "traded_volume"
                
                print(f"[{timestamp}] TICK: {symbol} - Price: {price}, Volume: {volume} (from: {vol_source})")
                
                # Save to file for analysis
                with open('tick_data.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'type': 'tick',
                        'data': tick_data
                    }) + '\n')
                    
            except Exception as e:
                logger.error(f"Error processing tick data: {e}")
        
        @td_obj.bidask_callback
        def new_bidask(bidask_data):
            """Handle bid-ask data using official SDK"""
            try:
                symbol = bidask_data.get('symbol', 'UNKNOWN')
                bid = bidask_data.get('bid', 0)
                ask = bidask_data.get('ask', 0)
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{timestamp}] BID-ASK: {symbol} - Bid: {bid}, Ask: {ask}")
                
                # Save to file for analysis
                with open('bidask_data.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'type': 'bidask',
                        'data': bidask_data
                    }) + '\n')
                    
            except Exception as e:
                logger.error(f"Error processing bid-ask data: {e}")
        
        @td_obj.greek_callback
        def mygreek_bidask(greek_data):
            """Handle greek data for options using official SDK"""
            try:
                symbol = greek_data.get('symbol', 'UNKNOWN')
                delta = greek_data.get('delta', 0)
                gamma = greek_data.get('gamma', 0)
                theta = greek_data.get('theta', 0)
                vega = greek_data.get('vega', 0)
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{timestamp}] GREEK: {symbol} - Δ:{delta:.4f}, Γ:{gamma:.4f}, Θ:{theta:.4f}, ν:{vega:.4f}")
                
                # Save to file for analysis
                with open('greek_data.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'type': 'greek',
                        'data': greek_data
                    }) + '\n')
                    
            except Exception as e:
                logger.error(f"Error processing greek data: {e}")
        
        @td_obj.one_min_bar_callback
        def new_min_bar_data(bar_data):
            """Handle 1-minute bar data using official SDK"""
            try:
                symbol = bar_data.get('symbol', 'UNKNOWN')
                open_price = bar_data.get('open', 0)
                high = bar_data.get('high', 0)
                low = bar_data.get('low', 0)
                close = bar_data.get('close', 0)
                volume = bar_data.get('volume', 0)
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{timestamp}] 1MIN: {symbol} - O:{open_price}, H:{high}, L:{low}, C:{close}, V:{volume}")
                
                # Save to file for analysis
                with open('one_min_bars.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'type': '1min_bar',
                        'data': bar_data
                    }) + '\n')
                    
            except Exception as e:
                logger.error(f"Error processing 1-min bar data: {e}")
        
        @td_obj.five_min_bar_callback
        def new_five_min_bar(bar_data):
            """Handle 5-minute bar data using official SDK"""
            try:
                symbol = bar_data.get('symbol', 'UNKNOWN')
                open_price = bar_data.get('open', 0)
                high = bar_data.get('high', 0)
                low = bar_data.get('low', 0)
                close = bar_data.get('close', 0)
                volume = bar_data.get('volume', 0)
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{timestamp}] 5MIN: {symbol} - O:{open_price}, H:{high}, L:{low}, C:{close}, V:{volume}")
                
                # Save to file for analysis
                with open('five_min_bars.json', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'type': '5min_bar',
                        'data': bar_data
                    }) + '\n')
                    
            except Exception as e:
                logger.error(f"Error processing 5-min bar data: {e}")
        
        logger.info("✅ All callbacks set up successfully using official SDK")
        logger.info("📊 Receiving live market data...")
        logger.info("💾 Data is being saved to JSON files for analysis")
        logger.info("⏹️  Press Ctrl+C to stop")
        
        # Keep your thread alive (exactly as in your original script)
        try:
            while True:
                time.sleep(120)  # Sleep for 2 minutes as per official SDK
                logger.info("💓 Still running... (Press Ctrl+C to stop)")
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping TrueData client...")
            logger.info("✅ Data collection completed")
            logger.info("📁 Check the JSON files for collected data:")
            logger.info("   - tick_data.json")
            logger.info("   - bidask_data.json") 
            logger.info("   - greek_data.json")
            logger.info("   - one_min_bars.json")
            logger.info("   - five_min_bars.json")
    
    except Exception as e:
        logger.error(f"❌ Error in TrueData script: {e}")
        logger.error("💡 Check your credentials and internet connection")

if __name__ == "__main__":
    main() 
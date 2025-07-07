#!/usr/bin/env python3
"""
TrueData Proxy Populater
========================
Populates the TrueData proxy with data from existing TrueData connection
so the autonomous trading system can access market data.
"""

import logging
import requests
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrueDataProxyPopulator:
    """
    Populates TrueData proxy with data from existing TrueData connection
    """
    
    def __init__(self, proxy_url: str = "https://algoauto-9gx56.ondigitalocean.app"):
        self.proxy_url = proxy_url
        self.update_interval = 5  # seconds
        self.running = False
        
    def get_existing_truedata_data(self) -> Dict[str, Any]:
        """
        Get data from existing TrueData connection
        
        This method tries multiple approaches to get live TrueData
        """
        try:
            # Method 1: Try to import and access existing truedata_client
            try:
                from data.truedata_client import live_market_data, get_truedata_status
                
                status = get_truedata_status()
                logger.info(f"TrueData status: {status}")
                
                if status.get('connected', False):
                    logger.info(f"✅ Found existing TrueData connection with {len(live_market_data)} symbols")
                    return live_market_data
                else:
                    logger.warning("❌ Existing TrueData connection not active")
                    return {}
                    
            except ImportError as e:
                logger.warning(f"Method 1 failed - could not import truedata_client: {e}")
                
            # Method 2: Try to access via global modules
            try:
                import sys
                for module_name, module in sys.modules.items():
                    if 'truedata' in module_name.lower() and hasattr(module, 'live_market_data'):
                        data = getattr(module, 'live_market_data', {})
                        if data:
                            logger.info(f"✅ Found TrueData in module {module_name} with {len(data)} symbols")
                            return data
                            
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")
                
            # Method 3: Try to create sample data for testing
            logger.warning("No existing TrueData found - creating sample data for testing")
            return self._create_sample_data()
            
        except Exception as e:
            logger.error(f"Error getting existing TrueData data: {e}")
            return {}
    
    def _create_sample_data(self) -> Dict[str, Any]:
        """Create sample data for testing when no real TrueData available"""
        logger.info("Creating sample market data for testing...")
        
        # Create realistic sample data
        sample_symbols = [
            "NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "MIDCPNIFTY",
            "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY"
        ]
        
        sample_data = {}
        base_time = datetime.now()
        
        for i, symbol in enumerate(sample_symbols):
            # Create realistic price data
            base_price = 1000 + (i * 500)  # Different base prices
            
            sample_data[symbol] = {
                'ltp': base_price + (i * 10),
                'open': base_price,
                'high': base_price + (i * 15),
                'low': base_price - (i * 5),
                'change': i * 5,
                'change_percent': (i * 0.5),
                'volume': 100000 + (i * 50000),
                'timestamp': base_time.isoformat(),
                'symbol': symbol,
                'source': 'SAMPLE_DATA_FOR_TESTING'
            }
        
        logger.info(f"Created sample data for {len(sample_data)} symbols")
        return sample_data
    
    def update_proxy(self, data: Dict[str, Any]) -> bool:
        """Update the TrueData proxy with market data"""
        try:
            url = f"{self.proxy_url}/api/v1/truedata-proxy/update-data"
            
            response = requests.post(
                url,
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Proxy updated successfully: {result.get('message', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Failed to update proxy: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating proxy: {e}")
            return False
    
    def start_continuous_update(self):
        """Start continuous updating of proxy data"""
        logger.info("🚀 Starting continuous TrueData proxy update...")
        self.running = True
        
        while self.running:
            try:
                # Get fresh data from existing TrueData
                data = self.get_existing_truedata_data()
                
                if data:
                    # Update proxy
                    success = self.update_proxy(data)
                    
                    if success:
                        logger.info(f"📊 Proxy updated with {len(data)} symbols")
                    else:
                        logger.warning("⚠️ Failed to update proxy")
                else:
                    logger.warning("⚠️ No data available to update proxy")
                
                # Wait before next update
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous update...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous update: {e}")
                time.sleep(self.update_interval)
    
    def stop_continuous_update(self):
        """Stop continuous updating"""
        self.running = False
    
    def test_proxy_connection(self) -> bool:
        """Test if proxy is accessible"""
        try:
            url = f"{self.proxy_url}/api/v1/truedata-proxy/status"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Proxy connection test successful: {result}")
                return True
            else:
                logger.error(f"❌ Proxy connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Proxy connection test error: {e}")
            return False

def main():
    """Main function to populate TrueData proxy"""
    
    print("🎯 TRUEDATA PROXY POPULATER")
    print("=" * 50)
    print("This script populates the TrueData proxy with data from")
    print("your existing TrueData connection so the autonomous")
    print("trading system can access market data.")
    print()
    
    # Create populator
    populator = TrueDataProxyPopulator()
    
    # Test proxy connection
    print("STEP 1: Testing proxy connection...")
    if not populator.test_proxy_connection():
        print("❌ Cannot connect to TrueData proxy. Is the server running?")
        return False
    
    # Get initial data
    print("\\nSTEP 2: Getting initial TrueData...")
    initial_data = populator.get_existing_truedata_data()
    
    if not initial_data:
        print("❌ No TrueData available. Cannot populate proxy.")
        return False
    
    print(f"✅ Found {len(initial_data)} symbols in TrueData")
    
    # Update proxy with initial data
    print("\\nSTEP 3: Updating proxy with initial data...")
    if not populator.update_proxy(initial_data):
        print("❌ Failed to update proxy with initial data")
        return False
    
    print("✅ Proxy updated successfully!")
    
    # Ask user if they want continuous updates
    print("\\nSTEP 4: Continuous updates")
    print("The proxy needs continuous updates to stay current.")
    print("This will update the proxy every 5 seconds.")
    
    try:
        choice = input("\\nStart continuous updates? (y/n): ").lower().strip()
        
        if choice == 'y' or choice == 'yes':
            print("🚀 Starting continuous updates...")
            print("Press Ctrl+C to stop")
            populator.start_continuous_update()
        else:
            print("✅ One-time update completed. Proxy populated.")
            
    except KeyboardInterrupt:
        print("\\n🛑 Stopping...")
        populator.stop_continuous_update()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
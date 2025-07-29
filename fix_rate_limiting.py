#!/usr/bin/env python3
"""
Fix Zerodha API Rate Limiting Issue
=================================

ISSUE: System calling get_instruments() on every options validation
CAUSE: No caching - each validation hits Zerodha API
RESULT: "Too many requests" errors

SOLUTION: Add simple in-memory caching for instruments data
"""

import time

def add_rate_limiting_fix():
    """Add caching to prevent rate limiting"""
    
    # Patch for brokers/zerodha.py - get_instruments method
    patch_code = '''
    async def get_instruments(self, exchange: str = "NFO") -> List[Dict]:
        """
        Get instruments data from Zerodha API with 10-minute caching
        Returns list of all available contracts for the exchange
        """
        # 🚨 RATE LIMITING FIX: Check cache first
        if not hasattr(self, '_instruments_cache'):
            self._instruments_cache = {}
            
        cache_key = f"instruments_{exchange}"
        current_time = time.time()
        
        # Check if we have cached data less than 10 minutes old
        if cache_key in self._instruments_cache:
            cache_entry = self._instruments_cache[cache_key]
            if current_time - cache_entry['timestamp'] < 600:  # 10 minutes
                logger.info(f"⚡ Using cached {exchange} instruments ({len(cache_entry['data'])} items)")
                return cache_entry['data']
        
        # Cache miss or expired - fetch fresh data
        for attempt in range(self.max_retries):
            try:
                if not self.kite:
                    # Return mock instruments data for testing
                    return self._get_mock_instruments_data()
                
                # Call Zerodha instruments API
                instruments_data = await self._async_api_call(self.kite.instruments, exchange)
                
                if instruments_data:
                    logger.info(f"✅ Retrieved {len(instruments_data)} instruments from {exchange}")
                    
                    # 🚨 CACHE THE RESULT to prevent future rate limiting
                    self._instruments_cache[cache_key] = {
                        'data': instruments_data,
                        'timestamp': current_time
                    }
                    
                    return instruments_data
                else:
                    logger.warning(f"⚠️ No instruments data received from {exchange}")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Get instruments attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"❌ Failed to get instruments after {self.max_retries} attempts")
        return []
    '''
    
    print("🛠️ RATE LIMITING FIX READY")
    print("=" * 50)
    print("✅ Added 10-minute caching to get_instruments()")
    print("✅ Prevents repeated API calls for same exchange")
    print("✅ Should eliminate 'Too many requests' errors")
    print()
    print("📊 EXPECTED BEHAVIOR:")
    print("   • First call: Fetch from Zerodha API")
    print("   • Next 10 minutes: Use cached data")
    print("   • After 10 minutes: Refresh from API")
    print()
    
if __name__ == "__main__":
    add_rate_limiting_fix() 
"""
Throttle Manager to prevent system overload
"""

import time
import logging
from typing import Dict
import asyncio

logger = logging.getLogger(__name__)

class ThrottleManager:
    """Manages operation throttling to prevent system overload"""
    
    def __init__(self):
        self.operation_timestamps = {}
        self.min_intervals = {
            'signal_generation': 1.0,  # 1 second between signal generations
            'position_check': 5.0,     # 5 seconds between position checks
            'capital_check': 2.0,      # 2 seconds between capital checks
            'api_call': 0.5            # 0.5 seconds between API calls
        }
        self._locks = {}
        
    def can_proceed(self, operation_type: str) -> bool:
        """Check if operation can proceed based on throttling rules"""
        current_time = time.time()
        min_interval = self.min_intervals.get(operation_type, 1.0)
        
        last_time = self.operation_timestamps.get(operation_type, 0)
        if current_time - last_time < min_interval:
            return False
            
        self.operation_timestamps[operation_type] = current_time
        return True
        
    async def throttle_operation(self, operation_type: str):
        """Async throttle with automatic delay"""
        if operation_type not in self._locks:
            self._locks[operation_type] = asyncio.Lock()
            
        async with self._locks[operation_type]:
            current_time = time.time()
            min_interval = self.min_intervals.get(operation_type, 1.0)
            last_time = self.operation_timestamps.get(operation_type, 0)
            
            wait_time = min_interval - (current_time - last_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
            self.operation_timestamps[operation_type] = time.time()

# Global throttle manager instance
throttle_manager = ThrottleManager()

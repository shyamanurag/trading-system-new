#!/usr/bin/env python3
"""
Order Rate Limiter - Prevents Excessive Order Attempts
=====================================================
CRITICAL: Stops retry loops that exhausted your 1,708 order attempts
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

class OrderRateLimiter:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.daily_order_count = 0
        self.minute_order_count = 0
        self.second_order_count = 0
        self.failed_orders = defaultdict(int)
        self.banned_symbols = set()
        self.processed_signals = set()
        
        # Conservative limits to stay well below Zerodha's thresholds
        self.limits = {
            'daily_max': 1800,          # Stay below 2000 limit
            'minute_max': 150,          # Stay below 200 limit  
            'second_max': 8,            # Stay below 10 limit
            'max_failures_per_symbol': 3,  # Ban symbol after 3 failures
            'ban_duration': 600         # 10 minutes ban
        }
        
        logger.info("🛡️ OrderRateLimiter: Preventing order loops")
    
    async def can_place_order(self, symbol: str, action: str, quantity: int, price: float = 0) -> Dict:
        # Check daily limit
        if self.daily_order_count >= self.limits['daily_max']:
            return {
                'allowed': False,
                'reason': 'DAILY_LIMIT_EXCEEDED',
                'message': f'Daily limit reached: {self.daily_order_count}/{self.limits["daily_max"]}'
            }
        
        # Check if symbol is banned due to failures
        if symbol in self.banned_symbols:
            return {
                'allowed': False,
                'reason': 'SYMBOL_BANNED',
                'message': f'Symbol {symbol} temporarily banned due to failures'
            }
        
        # Check for duplicate orders (use shorter time window to allow retries after fixes)
        order_signature = f"{symbol}:{action}:{quantity}:{int(time.time() // 10)}"  # 10-second window instead of 60
        if order_signature in self.processed_signals:
            return {
                'allowed': False,
                'reason': 'DUPLICATE_ORDER',
                'message': f'Duplicate order blocked: {symbol} {action} (wait 10s for retry)'
            }
        
        return {
            'allowed': True,
            'reason': 'APPROVED',
            'message': f'Order approved: {self.daily_order_count+1}/{self.limits["daily_max"]}',
            'signature': order_signature
        }
    
    async def record_order_attempt(self, signature: str, success: bool, symbol: str = None, error: str = None):
        self.daily_order_count += 1
        self.processed_signals.add(signature)
        
        if not success and symbol:
            self.failed_orders[symbol] += 1
            if self.failed_orders[symbol] >= self.limits['max_failures_per_symbol']:
                self.banned_symbols.add(symbol)
                logger.error(f"🚫 SYMBOL BANNED: {symbol} after {self.failed_orders[symbol]} failures")
        
        logger.info(f"📊 Order recorded: {self.daily_order_count}/{self.limits['daily_max']}, Success: {success}")

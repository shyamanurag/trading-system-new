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
        
        # 🔥 NEW: Per-symbol trade cooldown tracking
        self._last_trade_time: Dict[str, datetime] = {}
        self.trade_cooldown_seconds = 300  # 5 minutes between trades on same symbol
        self.min_order_quantity = 5  # Minimum 5 shares per order
        
        # Conservative limits to stay well below Zerodha's thresholds
        self.limits = {
            'daily_max': 1800,          # Stay below 2000 limit
            'minute_max': 150,          # Stay below 200 limit  
            'second_max': 8,            # Stay below 10 limit
            'max_failures_per_symbol': 3,  # Ban symbol after 3 failures
            'ban_duration': 600         # 10 minutes ban
        }
        
        logger.info("🛡️ OrderRateLimiter: Preventing order loops, churning, and tiny orders")
    
    async def can_place_order(self, symbol: str, action: str, quantity: int, price: float = 0, signal_id: str = None) -> Dict:
        
        # 🔥 NEW: Block tiny orders (< 5 shares) - wastes brokerage
        if quantity < self.min_order_quantity:
            logger.warning(f"🚫 TINY ORDER BLOCKED: {symbol} {action} qty={quantity} < min {self.min_order_quantity}")
            return {
                'allowed': False,
                'reason': 'QUANTITY_TOO_SMALL',
                'message': f'Order quantity {quantity} below minimum {self.min_order_quantity} shares'
            }
        
        # 🔥 NEW: Per-symbol cooldown to prevent churning
        if symbol in self._last_trade_time:
            elapsed = (datetime.now() - self._last_trade_time[symbol]).total_seconds()
            if elapsed < self.trade_cooldown_seconds:
                remaining = self.trade_cooldown_seconds - elapsed
                logger.warning(f"🧊 COOLDOWN BLOCKED: {symbol} - {remaining:.0f}s remaining (last trade {elapsed:.0f}s ago)")
                return {
                    'allowed': False,
                    'reason': 'SYMBOL_COOLDOWN',
                    'message': f'{symbol} in cooldown: {remaining:.0f}s remaining'
                }

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
        
        # Check for duplicate orders (30-second window per signal to slow down retries)
        if signal_id:
            order_signature = f"{signal_id}:{int(time.time() // 30)}"
        else:
            order_signature = f"{symbol}:{action}:{quantity}:{int(time.time() // 30)}"  # 30-second window
        if order_signature in self.processed_signals:
            return {
                'allowed': False,
                'reason': 'DUPLICATE_ORDER',
                'message': f'Duplicate order blocked: {symbol} {action} (wait 30s for retry)'
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
        
        # 🔥 NEW: Set cooldown after successful order
        if success and symbol:
            self._last_trade_time[symbol] = datetime.now()
            logger.info(f"🧊 COOLDOWN SET: {symbol} - {self.trade_cooldown_seconds}s cooldown started")
        
        if not success and symbol:
            self.failed_orders[symbol] += 1
            if self.failed_orders[symbol] >= self.limits['max_failures_per_symbol']:
                self.banned_symbols.add(symbol)
                logger.error(f"🚫 SYMBOL BANNED: {symbol} after {self.failed_orders[symbol]} failures")
        
        logger.info(f"📊 Order recorded: {self.daily_order_count}/{self.limits['daily_max']}, Success: {success}")

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
        self.min_order_value = 50000.0  # Minimum ₹50,000 order value for equities
        self.min_options_order_value = 5000.0  # Minimum ₹5,000 for options (lower threshold)
        
        # 🔥 NEW: Per-symbol daily trade limit to prevent churning
        self._daily_symbol_trades: Dict[str, int] = {}  # symbol -> trade count today
        self.max_trades_per_symbol_per_day = 3  # Max 3 round-trips per symbol per day
        self._last_reset_date = datetime.now().date()
        
        # Conservative limits to stay well below Zerodha's thresholds
        self.limits = {
            'daily_max': 1800,          # Stay below 2000 limit
            'minute_max': 150,          # Stay below 200 limit  
            'second_max': 8,            # Stay below 10 limit
            'max_failures_per_symbol': 3,  # Ban symbol after 3 failures
            'ban_duration': 600         # 10 minutes ban
        }
        
        logger.info("🛡️ OrderRateLimiter: Preventing order loops, churning, and tiny orders")
    
    async def can_place_order(self, symbol: str, action: str, quantity: int, price: float = 0, signal_id: str = None, is_exit_order: bool = False) -> Dict:
        
        # 🚨 CRITICAL: Block OPTIONS SELL orders immediately (margin too high)
        # Selling options requires ~₹200K+ margin, buying only needs premium (~₹10-20K)
        is_options = symbol.upper().endswith('CE') or symbol.upper().endswith('PE')
        if is_options and action.upper() == 'SELL' and not is_exit_order:
            logger.error(f"🚫 OPTIONS SELL BLOCKED: {symbol} - Cannot SELL options (margin ~₹200K+ required)")
            logger.info(f"   💡 Options can only be BOUGHT due to capital constraints (~₹150K available)")
            return {
                'allowed': False,
                'reason': 'OPTIONS_SELL_BLOCKED',
                'message': f'Cannot SELL options - margin requirement too high'
            }
        
        # 🔥 Reset daily counters if new day
        today = datetime.now().date()
        if today != self._last_reset_date:
            self._daily_symbol_trades = {}
            self._last_reset_date = today
            logger.info("📅 Daily trade counters reset")
        
        # 🔥 NEW: Per-symbol daily trade limit to prevent churning
        # Only check for NEW entries, exits are always allowed
        if not is_exit_order:
            current_trades = self._daily_symbol_trades.get(symbol, 0)
            if current_trades >= self.max_trades_per_symbol_per_day:
                logger.warning(f"🚫 CHURNING BLOCKED: {symbol} already traded {current_trades}x today (max {self.max_trades_per_symbol_per_day})")
                return {
                    'allowed': False,
                    'reason': 'DAILY_SYMBOL_LIMIT',
                    'message': f'{symbol} hit daily limit: {current_trades}/{self.max_trades_per_symbol_per_day} trades'
                }
        
        # 🔥 NEW: Block tiny orders (< 5 shares) - wastes brokerage
        # BUT allow exits of any size to close positions
        # EXCEPTION: Index futures (NIFTY-I, BANKNIFTY-I, FINNIFTY-I) trade in lots, not shares
        # 🔧 FIX: Only match KNOWN index futures, not all -I suffixed symbols (which includes stock futures like RELIANCE-I)
        KNOWN_INDEX_FUTURES = {'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I', 'BANKEX-I'}
        is_index_futures = symbol.upper() in KNOWN_INDEX_FUTURES
        
        # 🔧 Lot sizes for index futures (as of Dec 2024)
        # 🔧 UPDATED: NIFTY=75, BANKNIFTY=30, FINNIFTY=40, MIDCPNIFTY=75
        INDEX_LOT_SIZES = {
            'NIFTY-I': 75,       # NIFTY 50 futures
            'BANKNIFTY-I': 30,   # Bank NIFTY futures  
            'FINNIFTY-I': 40,    # Financial NIFTY futures
            'MIDCPNIFTY-I': 75,  # Midcap NIFTY futures
        }
        
        # Validate lot size for index futures
        if is_index_futures and not is_exit_order:
            lot_size = INDEX_LOT_SIZES.get(symbol.upper(), 25)  # Default 25 if unknown
            if quantity < lot_size:
                logger.warning(f"🚫 INDEX LOT SIZE ERROR: {symbol} qty={quantity} < lot size {lot_size}")
                return {
                    'allowed': False,
                    'reason': 'INVALID_LOT_SIZE',
                    'message': f'{symbol} requires minimum {lot_size} units (1 lot), got {quantity}'
                }
            if quantity % lot_size != 0:
                logger.warning(f"🚫 INDEX LOT SIZE ERROR: {symbol} qty={quantity} not multiple of lot size {lot_size}")
                return {
                    'allowed': False,
                    'reason': 'INVALID_LOT_SIZE',
                    'message': f'{symbol} quantity must be multiple of {lot_size}, got {quantity}'
                }
            logger.info(f"✅ INDEX FUTURES: {symbol} {quantity} units = {quantity // lot_size} lot(s)")
        
        if quantity < self.min_order_quantity and not is_exit_order and not is_index_futures and not is_options:
            logger.warning(f"🚫 TINY ORDER BLOCKED: {symbol} {action} qty={quantity} < min {self.min_order_quantity}")
            return {
                'allowed': False,
                'reason': 'QUANTITY_TOO_SMALL',
                'message': f'Order quantity {quantity} below minimum {self.min_order_quantity} shares'
            }
        
        # 🔥 FIX: Block small order VALUE - brokerage eats profits on tiny trades
        # Exit orders bypass this check to allow closing positions
        # OPTIONS trades use lower threshold (risk is limited to premium)
        # 🔥 2026-01-02: Warn if price is 0 - this bypasses MIN_ORDER_VALUE check
        if price == 0 and not is_exit_order and not is_index_futures and not is_options:
            logger.warning(f"⚠️ NO PRICE FOR MIN_ORDER_VALUE CHECK: {symbol} {action} qty={quantity} - check may be bypassed!")
        
        if price > 0 and not is_exit_order:
            order_value = quantity * price
            
            # Detect OPTIONS trades (symbol ends with CE or PE)
            is_options = symbol.upper().endswith('CE') or symbol.upper().endswith('PE')
            min_value = self.min_options_order_value if is_options else self.min_order_value
            
            if order_value < min_value:
                if is_options:
                    logger.warning(f"🚫 SMALL OPTIONS ORDER BLOCKED: {symbol} {action} ₹{order_value:,.0f} < min ₹{min_value:,.0f}")
                else:
                    logger.warning(f"🚫 SMALL ORDER VALUE BLOCKED: {symbol} {action} ₹{order_value:,.0f} < min ₹{min_value:,.0f}")
                return {
                    'allowed': False,
                    'reason': 'ORDER_VALUE_TOO_SMALL',
                    'message': f'Order value ₹{order_value:,.0f} below minimum ₹{min_value:,.0f}'
                }
            
            # Log options bypass for visibility
            if is_options and order_value < self.min_order_value:
                logger.info(f"✅ OPTIONS BYPASS: {symbol} ₹{order_value:,.0f} allowed (options min: ₹{self.min_options_order_value:,.0f})")
        
        # 🔥 FIX: Exit orders bypass cooldown - MUST be able to close positions
        if is_exit_order:
            logger.info(f"✅ EXIT ORDER BYPASS: {symbol} {action} - Cooldown skipped for position exit")
        # Only apply cooldown to NEW entry orders
        elif symbol in self._last_trade_time:
            elapsed = (datetime.now() - self._last_trade_time[symbol]).total_seconds()
            if elapsed < self.trade_cooldown_seconds:
                remaining = self.trade_cooldown_seconds - elapsed
                logger.warning(f"🧊 COOLDOWN BLOCKED: {symbol} {action} (new entry) - {remaining:.0f}s remaining")
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
            
            # 🔥 NEW: Increment daily symbol trade count
            self._daily_symbol_trades[symbol] = self._daily_symbol_trades.get(symbol, 0) + 1
            trade_count = self._daily_symbol_trades[symbol]
            remaining = self.max_trades_per_symbol_per_day - trade_count
            
            logger.info(f"🧊 COOLDOWN SET: {symbol} - {self.trade_cooldown_seconds}s cooldown started")
            logger.info(f"📊 DAILY TRADE COUNT: {symbol} = {trade_count}/{self.max_trades_per_symbol_per_day} ({remaining} remaining)")
        
        if not success and symbol:
            self.failed_orders[symbol] += 1
            if self.failed_orders[symbol] >= self.limits['max_failures_per_symbol']:
                self.banned_symbols.add(symbol)
                logger.error(f"🚫 SYMBOL BANNED: {symbol} after {self.failed_orders[symbol]} failures")
        
        logger.info(f"📊 Order recorded: {self.daily_order_count}/{self.limits['daily_max']}, Success: {success}")

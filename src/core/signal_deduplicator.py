"""
Signal Deduplication and Quality Filtering System
=================================================
Prevents multiple signals for the same symbol at the same timestamp
Implements signal quality scoring and filtering
Includes 5-minute signal expiry and 30-second execution throttling
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class SignalDeduplicator:
    """Handles signal deduplication and quality filtering"""
    
    def __init__(self):
        self.recent_signals = defaultdict(list)  # symbol -> list of recent signals
        self.signal_history = {}  # signal_id -> signal data
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.now()
        
        # Quality thresholds - BALANCED FOR PRODUCTION TRADING
        self.min_confidence_threshold = 0.65  # Slightly lowered to capture 0.65 confidence signals
        self.max_signals_per_symbol = 20  # TEMPORARY FIX: Increased from 5 to 20 to allow signals through
        self.deduplication_window = 300  # 5 minutes

        # 🚨 CRITICAL FIX: Redis persistence for executed signals across deploys
        self.redis_client = None
        self._init_redis_connection()
        
        # 🚨 DEPLOYMENT CACHE CLEARING: Clear old signals after deployment
        # Don't create async task during init - will be called manually when event loop is ready
        self._startup_cleanup_pending = True

        # Post-exit cooldown seconds (prevent immediate re-entry churn)
        self.post_exit_cooldown_seconds = 600
        
        # 🔥 NEW: Trade cooldown to prevent rapid back-and-forth trading
        self.trade_cooldown_minutes = 5  # 5 minutes cooldown after any trade
        self._last_trade_time: Dict[str, datetime] = {}  # symbol -> last trade time

        # Per-signal attempt tracking and TTL control
        self.max_attempts_per_signal = 10
        self.retry_window_seconds = 30
        self._attempts_memory = {}
        self._last_try_memory = {}
        
        # 🚨 NEW: Signal expiry and execution throttling
        from src.core.signal_expiry_manager import signal_expiry_manager
        self.expiry_manager = signal_expiry_manager
        logger.info("✅ Signal expiry and throttling manager integrated")

    async def _clear_signal_cache_on_startup(self):
        """Clear deployment cache on startup to prevent duplicate signals"""
        try:
            # Wait a bit for Redis connection to be ready
            await asyncio.sleep(2)
            
            if not self.redis_client:
                logger.warning("⚠️ No Redis client - cannot clear deployment cache")
                return
            
            # Check if this is a fresh deployment (no cache clearing in last 5 minutes)
            cache_clear_key = "last_cache_clear"
            last_clear = await self.redis_client.get(cache_clear_key)
            
            if last_clear:
                import time
                time_since_clear = time.time() - float(last_clear)
                if time_since_clear < 300:  # 5 minutes
                    logger.info(f"⏭️ Skipping cache clear - last cleared {time_since_clear:.0f}s ago")
                    return
            
            logger.info("🧹 DEPLOYMENT STARTUP: Clearing signal execution cache (preserving order tracking)")
            
            # Clear ONLY executed signals deduplication cache for today
            today = datetime.now().strftime('%Y-%m-%d')
            pattern = f"executed_signals:{today}:*"
            
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"✅ Cleared {deleted} signal execution cache entries (not order tracking)")
                logger.info("🔒 Order tracking & position data preserved for square-off trades")
            else:
                logger.info("ℹ️ No signal execution cache found - clean slate confirmed")
            
            # Mark cache as cleared
            import time
            await self.redis_client.set(cache_clear_key, str(time.time()), ex=3600)  # 1 hour expiry
            
            logger.info("🚀 Signal processing cache cleared - ready for fresh signals")
            
        except Exception as e:
            logger.error(f"❌ Error clearing deployment cache: {e}")

    async def ensure_startup_cleanup(self):
        """Ensure startup cleanup is run when event loop is available"""
        if getattr(self, '_startup_cleanup_pending', False):
            self._startup_cleanup_pending = False
            await self._clear_signal_cache_on_startup()

    async def clear_all_executed_signals(self):
        """Clear all executed signals cache - can be called manually"""
        try:
            if not self.redis_client:
                logger.error("❌ No Redis client available")
                return 0
            
            # Clear executed signals for last 3 days
            total_cleared = 0
            for days_back in range(3):
                date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                pattern = f"executed_signals:{date}:*"
                
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_cleared += deleted
                    logger.info(f"🧹 Cleared {deleted} executed signals for {date}")
                
                # Also clear quantity tracking
                qty_pattern = f"executed_qty:{date}:*"
                qty_keys = await self.redis_client.keys(qty_pattern)
                if qty_keys:
                    deleted = await self.redis_client.delete(*qty_keys)
                    total_cleared += deleted
            
            logger.info(f"✅ Total executed signals cleared: {total_cleared}")
            return total_cleared
            
        except Exception as e:
            logger.error(f"❌ Error clearing executed signals: {e}")
            return 0
    
    async def clear_symbol_execution(self, symbol: str, action: str = None):
        """
        Clear executed signal cache for a specific symbol
        Use this to allow re-trading a symbol (e.g., after position sizing fix)
        
        Args:
            symbol: Stock symbol (e.g., 'SBIN')
            action: Optional - 'BUY' or 'SELL'. If None, clears both.
        """
        try:
            if not self.redis_client:
                logger.error("❌ No Redis client available")
                return False
            
            today = datetime.now().strftime('%Y-%m-%d')
            cleared_keys = []
            
            actions = [action] if action else ['BUY', 'SELL']
            
            for act in actions:
                # Clear execution count
                exec_key = f"executed_signals:{today}:{symbol}:{act}"
                qty_key = f"executed_qty:{today}:{symbol}:{act}"
                
                await self.redis_client.delete(exec_key)
                await self.redis_client.delete(qty_key)
                cleared_keys.extend([exec_key, qty_key])
            
            logger.info(f"🧹 CLEARED EXECUTION CACHE: {symbol} {action or 'BUY/SELL'}")
            logger.info(f"   Deleted keys: {cleared_keys}")
            logger.info(f"   ✅ {symbol} can now be traded again with fresh quantity")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error clearing symbol execution for {symbol}: {e}")
            return False
    
    async def get_executed_positions_summary(self) -> Dict:
        """Get summary of all executed positions today (for debugging)"""
        try:
            if not self.redis_client:
                return {'error': 'No Redis client'}
            
            today = datetime.now().strftime('%Y-%m-%d')
            pattern = f"executed_signals:{today}:*"
            
            keys = await self.redis_client.keys(pattern)
            
            positions = {}
            for key in keys:
                # Parse key: executed_signals:YYYY-MM-DD:SYMBOL:ACTION
                parts = key.split(':')
                if len(parts) >= 4:
                    symbol = parts[2]
                    action = parts[3]
                    count = await self.redis_client.get(key)
                    
                    qty_key = f"executed_qty:{today}:{symbol}:{action}"
                    qty = await self.redis_client.get(qty_key)
                    
                    positions[f"{symbol}:{action}"] = {
                        'symbol': symbol,
                        'action': action,
                        'execution_count': int(count) if count else 0,
                        'total_quantity': int(qty) if qty else 0
                    }
            
            return {
                'date': today,
                'total_positions': len(positions),
                'positions': positions
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting executed positions summary: {e}")
            return {'error': str(e)}

    async def purge_signal_everywhere(self, signal_id: str, symbol: Optional[str] = None):
        """Remove a signal from all in-memory stores and Redis tracking."""
        try:
            # In-memory history
            if signal_id in self.signal_history:
                del self.signal_history[signal_id]
            # In-memory recent per-symbol
            if symbol and symbol in self.recent_signals:
                self.recent_signals[symbol] = [s for s in self.recent_signals[symbol] if s.get('signal_id') != signal_id]
                if not self.recent_signals[symbol]:
                    del self.recent_signals[symbol]
            # Redis: attempts and throttles
            if self.redis_client:
                try:
                    await self.redis_client.delete(f"signal_attempts:{signal_id}")
                    await self.redis_client.delete(f"signal_last_try:{signal_id}")
                except Exception:
                    pass
            logger.info(f"🧹 Purged signal from caches: {signal_id}")
        except Exception as e:
            logger.error(f"❌ Error purging signal {signal_id}: {e}")
        
    def _init_redis_connection(self):
        """Initialize Redis connection for persistent signal tracking"""
        try:
            import redis.asyncio as redis
            import os
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(
                    redis_url, 
                    decode_responses=True,
                    ssl_cert_reqs=None,
                    ssl_check_hostname=False
                )
                logger.info("✅ Signal deduplicator Redis connection initialized")
                logger.info(f"🔗 Redis URL configured: {redis_url[:20]}...")  # Log first 20 chars for debugging
            else:
                logger.warning("⚠️ No REDIS_URL - signal deduplication will be memory-only")
                logger.warning("🚨 CRITICAL: Without Redis, duplicate signals across deployments CANNOT be prevented!")
        except Exception as e:
            logger.error(f"❌ Failed to init Redis for signal deduplication: {e}")
            logger.error("🚨 CRITICAL: Redis connection failed - duplicate execution protection disabled!")
        
    def set_position_tracker(self, position_tracker):
        """Set position tracker reference for active position checking"""
        self.position_tracker = position_tracker
        logger.info("✅ Position tracker connected to signal deduplicator")
    
    def _parse_options_symbol(self, symbol: str) -> tuple:
        """Parse options symbol to extract: (underlying, option_type, strike)"""
        if not symbol:
            return ('', 'EQUITY', None)
        
        symbol = symbol.upper().strip()
        
        if not (symbol.endswith('CE') or symbol.endswith('PE')):
            return (symbol, 'EQUITY', None)
        
        option_type = 'CE' if symbol.endswith('CE') else 'PE'
        base = symbol[:-2]
        
        import re
        strike_match = re.search(r'(\d+)$', base)
        if not strike_match:
            return (symbol, option_type, None)
        
        strike = int(strike_match.group(1))
        remaining = base[:strike_match.start()]
        underlying = re.sub(r'\d{2}[A-Z0-9]*$', '', remaining)
        underlying = re.sub(r'\d+$', '', underlying)
        
        return (underlying, option_type, strike)
    
    async def _check_pending_order(self, symbol: str, zerodha_client) -> tuple:
        """Check if there's a pending order for this symbol or underlying+type."""
        try:
            underlying, option_type, _ = self._parse_options_symbol(symbol)
            
            orders = await zerodha_client.get_orders()
            if not orders:
                return False, None
            
            for order in orders:
                status = order.get('status', '').upper()
                
                if status not in ['PENDING', 'OPEN', 'TRIGGER PENDING', 'AMO REQ RECEIVED']:
                    continue
                
                order_symbol = order.get('tradingsymbol', '')
                order_underlying, order_type, _ = self._parse_options_symbol(order_symbol)
                
                # Block if same underlying + same type has pending order
                if order_underlying == underlying and order_type == option_type:
                    return True, order.get('order_id')
            
            return False, None
            
        except Exception as e:
            logger.debug(f"Pending order check error: {e}")
            return False, None
    
    async def check_trade_cooldown(self, symbol: str) -> tuple[bool, str]:
        """
        🔥 Check if symbol is in trade cooldown period.
        Prevents rapid back-and-forth trading (churning).
        
        Returns:
            (is_blocked, reason): True if blocked, with reason
        """
        try:
            if not self.redis_client:
                # Fallback to local memory
                if symbol in self._last_trade_time:
                    elapsed = (datetime.now() - self._last_trade_time[symbol]).total_seconds() / 60
                    if elapsed < self.trade_cooldown_minutes:
                        return True, f"Trade cooldown: {self.trade_cooldown_minutes - elapsed:.1f} min remaining"
                return False, ""
            
            # Check Redis for last trade time
            today = datetime.now().strftime('%Y-%m-%d')
            cooldown_key = f"trade_cooldown:{today}:{symbol}"
            
            last_trade = await self.redis_client.get(cooldown_key)
            if last_trade:
                last_trade_time = datetime.fromisoformat(last_trade)
                elapsed = (datetime.now() - last_trade_time).total_seconds() / 60
                
                if elapsed < self.trade_cooldown_minutes:
                    remaining = self.trade_cooldown_minutes - elapsed
                    return True, f"Trade cooldown: {remaining:.1f} min remaining (last trade {elapsed:.1f} min ago)"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"❌ Error checking trade cooldown: {e}")
            return False, ""
    
    async def set_trade_cooldown(self, symbol: str):
        """Set trade cooldown after executing a trade"""
        try:
            now = datetime.now()
            self._last_trade_time[symbol] = now
            
            if self.redis_client:
                today = now.strftime('%Y-%m-%d')
                cooldown_key = f"trade_cooldown:{today}:{symbol}"
                await self.redis_client.set(cooldown_key, now.isoformat(), ex=self.trade_cooldown_minutes * 60)
                logger.info(f"🧊 TRADE COOLDOWN SET: {symbol} - {self.trade_cooldown_minutes} min cooldown started")
        except Exception as e:
            logger.error(f"❌ Error setting trade cooldown: {e}")

    async def _check_signal_already_executed(self, signal: Dict) -> bool:
        """
        Check if this signal should be blocked based on ACTIVE POSITIONS only.
        
        CRITICAL LOGIC:
        - Blocks only if there's an ACTIVE/OPEN position for the same symbol + action
        - Does NOT block based on previous signals that were just recorded
        - Manually squared-off positions should NOT block new signals
        - 🚨 NEW: Also blocks if there's a PENDING order for same symbol
        """
        try:
            # 🎯 BYPASS DEDUPLICATION FOR POSITION MANAGEMENT ACTIONS
            is_management_action = signal.get('management_action', False)
            is_closing_action = signal.get('closing_action', False)
            is_size_correction = signal.get('size_correction', False)
            is_scaling_action = signal.get('scaling_action', False)
            
            if is_management_action or is_closing_action or is_size_correction or is_scaling_action:
                logger.info(f"🎯 MANAGEMENT ACTION BYPASS: {signal.get('symbol')} {signal.get('action')} - skipping duplicate check")
                return False
            
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            # 🚨 FIX: Check for PENDING orders - if order is pending, don't resend
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                    is_pending, pending_order_id = await self._check_pending_order(symbol, orchestrator.zerodha_client)
                    if is_pending:
                        logger.warning(f"🚫 PENDING ORDER BLOCKS SIGNAL: {symbol} {action} - order {pending_order_id} still pending")
                        return True  # Block the signal
            except Exception as pending_err:
                logger.debug(f"Pending order check skipped: {pending_err}")
            
            # 🔥 NEW: Check trade cooldown to prevent churning
            is_blocked, cooldown_reason = await self.check_trade_cooldown(symbol)
            if is_blocked:
                logger.warning(f"🧊 COOLDOWN BLOCKED: {symbol} {action} - {cooldown_reason}")
                return True
            
            # 🎯 CRITICAL FIX: Check position tracker for ACTIVE positions, not Redis execution history
            if hasattr(self, 'position_tracker') and self.position_tracker:
                positions = getattr(self.position_tracker, 'positions', {})
                
                if symbol in positions:
                    position = positions[symbol]
                    position_qty = getattr(position, 'quantity', 0)
                    
                    if position_qty != 0:
                        logger.warning(f"🚫 DUPLICATE BLOCKED: {symbol} has ACTIVE position (qty: {position_qty})")
                        logger.warning(f"   💡 Close the position first to allow new signals")
                        return True  # Block - active position exists
                    else:
                        logger.info(f"✅ {symbol} position closed (qty=0) - allowing new signal")
                        return False  # Allow - position was closed
                else:
                    # 🎯 CRITICAL: No position in tracker = position was closed or never opened
                    # DO NOT check Redis in this case - manually squared-off positions should allow re-entry
                    logger.info(f"✅ SIGNAL ALLOWED: {symbol} {action} - no active position in tracker")
                    return False  # Allow - no position
            
            # Only use Redis fallback if position tracker is NOT available at all
            if not self.redis_client:
                logger.warning(f"🚨 NO POSITION TRACKER OR REDIS: Cannot check for duplicate signal {signal.get('symbol')} - allowing execution")
                return False
                
            new_quantity = signal.get('quantity', 0)
            
            # Check if signal was executed in last 24 hours
            today = datetime.now().strftime('%Y-%m-%d')
            executed_key = f"executed_signals:{today}:{symbol}:{action}"
            executed_qty_key = f"executed_qty:{today}:{symbol}:{action}"
            
            logger.info(f"🔍 CHECKING DUPLICATE (Redis fallback): {executed_key}")
            executed_count = await self.redis_client.get(executed_key)
            
            if executed_count and int(executed_count) > 0:
                # 🎯 NEW: Check if this is a SCALING opportunity (larger quantity for same direction)
                executed_qty = await self.redis_client.get(executed_qty_key)
                executed_qty = int(executed_qty) if executed_qty else 0
                
                # If new signal has significantly more quantity (>20% more), allow scaling
                if new_quantity > 0 and executed_qty > 0:
                    qty_increase_pct = ((new_quantity - executed_qty) / executed_qty) * 100
                    
                    if qty_increase_pct >= 20:  # At least 20% more quantity
                        logger.info(f"📈 POSITION SCALING ALLOWED: {symbol} {action}")
                        logger.info(f"   Previous: {executed_qty} shares → New: {new_quantity} shares (+{qty_increase_pct:.0f}%)")
                        logger.info(f"   🎯 This will ADD {new_quantity - executed_qty} shares to existing position")
                        
                        # Mark this as a scaling action in the signal
                        signal['scaling_action'] = True
                        signal['additional_quantity'] = new_quantity - executed_qty
                        signal['original_executed_qty'] = executed_qty
                        return False  # Allow execution
                
                logger.warning(f"🚫 DUPLICATE SIGNAL BLOCKED (Redis): {symbol} {action} already executed {executed_count} times today (qty: {executed_qty})")
                logger.warning(f"🔑 Redis key: {executed_key}")
                return True
            else:
                logger.info(f"✅ SIGNAL ALLOWED (Redis): {symbol} {action} - no previous executions found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking executed signals: {e}")
            logger.error(f"🚨 CHECK FAILED for {signal.get('symbol')} - ALLOWING execution (risky)")
            return False
    
    async def try_claim_signal(self, signal: Dict) -> bool:
        """
        🚨 ATOMIC CLAIM: Try to claim exclusive rights to execute a signal.
        Uses Redis SETNX to atomically check and claim in ONE operation.
        
        Returns:
            True if claimed successfully (this caller should execute)
            False if already claimed by another caller (should NOT execute)
        """
        try:
            if not self.redis_client:
                logger.warning(f"⚠️ No Redis client - cannot do atomic claim for {signal.get('symbol')}")
                return True  # Allow execution but risky
            
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            # Use a short-lived claim key (30 seconds TTL)
            # This prevents race conditions when multiple signals arrive simultaneously
            today = datetime.now().strftime('%Y-%m-%d')
            claim_key = f"signal_claim:{today}:{symbol}:{action}"
            
            # ATOMIC SETNX: Only one caller can succeed
            # NX = set only if Not eXists, EX = expire after 30 seconds
            claimed = await self.redis_client.set(claim_key, "1", nx=True, ex=30)
            
            if claimed:
                logger.info(f"🔒 SIGNAL CLAIMED: {symbol} {action} - This caller has exclusive rights to execute")
                return True
            else:
                logger.warning(f"🚫 SIGNAL ALREADY CLAIMED: {symbol} {action} - Another process is executing, rejecting duplicate")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in atomic claim: {e}")
            return False  # BLOCK on error - quality over quantity
    
    async def mark_signal_executed(self, signal: Dict):
        """Mark signal as executed to prevent future duplicates"""
        try:
            if not self.redis_client:
                logger.error(f"🚨 NO REDIS CLIENT: Cannot mark signal {signal.get('symbol')} as executed - DUPLICATE RISK!")
                return
                
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            quantity = signal.get('quantity', 0)
            
            # Increment execution count for today
            today = datetime.now().strftime('%Y-%m-%d')
            executed_key = f"executed_signals:{today}:{symbol}:{action}"
            executed_qty_key = f"executed_qty:{today}:{symbol}:{action}"
            
            logger.info(f"📝 MARKING AS EXECUTED: {executed_key} (qty: {quantity})")
            current_count = await self.redis_client.incr(executed_key)
            await self.redis_client.expire(executed_key, 86400)  # 24 hours
            
            # 🎯 Track total executed quantity for position scaling logic
            if signal.get('scaling_action'):
                # This is a scaling order - ADD to existing quantity
                additional_qty = signal.get('additional_quantity', quantity)
                current_qty = await self.redis_client.get(executed_qty_key)
                current_qty = int(current_qty) if current_qty else 0
                new_total_qty = current_qty + additional_qty
                await self.redis_client.set(executed_qty_key, str(new_total_qty), ex=86400)
                logger.info(f"📈 POSITION SCALED: {symbol} {action} - Total qty now: {new_total_qty} (added: {additional_qty})")
            else:
                # Regular order - set the executed quantity
                await self.redis_client.set(executed_qty_key, str(quantity), ex=86400)
            
            logger.info(f"✅ Marked signal as executed: {symbol} {action} (count: {current_count}, qty: {quantity})")
            
            # 🔥 Set trade cooldown to prevent immediate re-entry/reversal
            await self.set_trade_cooldown(symbol)
            
            if current_count > 1 and not signal.get('scaling_action'):
                logger.warning(f"⚠️ MULTIPLE EXECUTIONS DETECTED: {symbol} {action} now executed {current_count} times today!")
            
        except Exception as e:
            logger.error(f"❌ Error marking signal as executed in Redis: {e}")
            logger.error(f"🚨 FAILED TO MARK {signal.get('symbol')} as executed - FUTURE DUPLICATES POSSIBLE!")
    
    async def process_signals(self, signals: List[Dict]) -> List[Dict]:
        """Process and deduplicate signals, return only high-quality unique signals"""
        if not signals:
            return []
        
        # 🚨 CRITICAL FIX: Check for already executed signals first
        filtered_signals = []
        for signal in signals:
            if await self._check_signal_already_executed(signal):
                continue  # Skip this signal - already executed
            filtered_signals.append(signal)
        
        if len(filtered_signals) < len(signals):
            logger.info(f"🚫 BLOCKED {len(signals) - len(filtered_signals)} duplicate signals from previous executions")
        
        # Continue with normal processing
        signals = filtered_signals
        
        # Clean up old signals periodically
        self._cleanup_old_signals()

        # Enforce 5-minute TTL on generated signals before they reach execution
        ttl_filtered = []
        now_ts = datetime.now()
        for s in signals:
            gen_at = s.get('generated_at')
            if isinstance(gen_at, str):
                try:
                    from datetime import datetime as _dt
                    gen_at = _dt.fromisoformat(gen_at)
                except Exception:
                    gen_at = now_ts
            if not gen_at:
                gen_at = now_ts
            age_sec = (now_ts - gen_at).total_seconds()
            if age_sec <= 300:
                ttl_filtered.append(s)
            else:
                logger.info(f"🗑️ Dropping expired signal (>5m): {s.get('symbol')} {s.get('action')} id={s.get('signal_id')}")
                # Also purge any cached attempt counters for this signal
                if s.get('signal_id'):
                    await self.purge_signal_everywhere(s['signal_id'], s.get('symbol'))
        signals = ttl_filtered
        
        # Filter by quality first
        quality_signals = self._filter_by_quality(signals)
        logger.debug(f"🔍 QUALITY FILTER: {len(signals)} → {len(quality_signals)} signals passed")
        
        # Deduplicate by symbol
        deduplicated_signals = self._deduplicate_by_symbol(quality_signals)
        logger.debug(f"🔍 SYMBOL DEDUP: {len(quality_signals)} → {len(deduplicated_signals)} signals passed")
        
        # Check for timestamp collisions and resolve
        final_signals = self._resolve_timestamp_collisions(deduplicated_signals)
        logger.debug(f"🔍 TIMESTAMP RESOLVE: {len(deduplicated_signals)} → {len(final_signals)} signals passed")
        
        # Update signal history
        self._update_signal_history(final_signals)
        
        logger.info(f"📊 Signal Processing: {len(signals)} → {len(quality_signals)} → {len(final_signals)}")
        
        return final_signals
    
    def _filter_by_quality(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals by quality thresholds"""
        logger.info(f"🔍 QUALITY FILTER: Processing {len(signals)} signals")
        quality_signals = []
        rejection_stats = {
            'low_confidence': 0,
            'missing_fields': 0,
            'invalid_prices': 0,
            'invalid_quantity': 0,
            'poor_risk_reward': 0
        }
        
        for signal in signals:
            # 🎯 BYPASS QUALITY FILTERING FOR POSITION MANAGEMENT ACTIONS
            is_management_action = signal.get('management_action', False)
            is_closing_action = signal.get('closing_action', False)
            
            if is_management_action or is_closing_action:
                logger.info(f"🎯 QUALITY BYPASS: {signal.get('symbol')} {signal.get('action')} - management action approved")
                quality_signals.append(signal)
                continue
            
            confidence = signal.get('confidence', 0)
            
            # Check minimum confidence
            if confidence < self.min_confidence_threshold:
                rejection_stats['low_confidence'] += 1
                logger.info(f"❌ Signal rejected - low confidence: {signal['symbol']} ({confidence:.2f} < {self.min_confidence_threshold})")
                continue
            
            # Check for required fields
            required_fields = ['symbol', 'action', 'entry_price', 'stop_loss', 'target']
            if not all(field in signal for field in required_fields):
                rejection_stats['missing_fields'] += 1
                logger.info(f"❌ Signal rejected - missing fields: {signal.get('symbol', 'UNKNOWN')} - Missing: {[f for f in required_fields if f not in signal]}")
                continue
            
            # 🚨 CRITICAL: Check for valid quantity (must be > 0)
            quantity = signal.get('quantity', 0)
            if quantity <= 0:
                rejection_stats['invalid_quantity'] += 1
                logger.info(f"❌ Signal rejected - invalid quantity: {signal['symbol']} (quantity: {quantity}) - Cannot trade zero or negative quantity")
                continue
            
            # Check for reasonable price levels
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            target = signal.get('target', 0)
            
            if not all([entry_price > 0, stop_loss > 0, target > 0]):
                rejection_stats['invalid_prices'] += 1
                logger.info(f"❌ Signal rejected - invalid prices: {signal['symbol']} - Entry: ₹{entry_price}, SL: ₹{stop_loss}, Target: ₹{target}")
                continue
            
            # Check risk-reward ratio
            if signal['action'] == 'BUY':
                risk = entry_price - stop_loss
                reward = target - entry_price
            else:  # SELL
                risk = stop_loss - entry_price
                reward = entry_price - target
            
            if risk <= 0 or reward <= 0:
                rejection_stats['invalid_prices'] += 1
                logger.info(f"❌ Signal rejected - invalid risk/reward calculation: {signal['symbol']} - Risk: ₹{risk:.2f}, Reward: ₹{reward:.2f}")
                continue
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 1.5:  # ADJUSTED: Minimum 1.5:1 profit-to-loss ratio for current market
                rejection_stats['poor_risk_reward'] += 1
                logger.info(f"❌ Signal rejected - poor risk/reward: {signal['symbol']} ({risk_reward_ratio:.2f} < 1.5) - Entry: ₹{entry_price}, SL: ₹{stop_loss}, Target: ₹{target}")
                continue
            
            quality_signals.append(signal)
        
        # Log summary of rejections
        if any(rejection_stats.values()):
            logger.info(f"📊 Quality Filter Results: {len(quality_signals)} passed, {sum(rejection_stats.values())} rejected")
            for reason, count in rejection_stats.items():
                if count > 0:
                    logger.info(f"   - {reason}: {count} signals")
        
        return quality_signals
    
    def _deduplicate_by_symbol(self, signals: List[Dict]) -> List[Dict]:
        """Remove duplicate signals for the same symbol, keep highest confidence"""
        symbol_signals = defaultdict(list)
        management_signals = []  # Management actions bypass symbol deduplication
        
        # Separate management actions from regular signals
        for signal in signals:
            is_management_action = signal.get('management_action', False)
            is_closing_action = signal.get('closing_action', False)
            
            if is_management_action or is_closing_action:
                logger.info(f"🎯 SYMBOL DEDUP BYPASS: {signal.get('symbol')} {signal.get('action')} - management action")
                management_signals.append(signal)
            else:
                symbol = signal['symbol']
                symbol_signals[symbol].append(signal)
        
        deduplicated = []
        
        for symbol, symbol_signal_list in symbol_signals.items():
            # TEMPORARY FIX: Disable in-memory recent signals check - rely only on Redis executed signals
            # The in-memory check counts generated signals, not executed ones, causing false blocks
            recent_count = len([s for s in self.recent_signals[symbol] 
                              if (datetime.now() - s['timestamp']).total_seconds() < self.deduplication_window])
            
            # DISABLED: Only use Redis-based executed signal check, not in-memory generated signal count
            if False and recent_count >= self.max_signals_per_symbol:
                logger.info(f"❌ Signal rejected - too many recent signals: {symbol} ({recent_count} >= {self.max_signals_per_symbol})")
                continue
            
            # If multiple signals for same symbol, keep the highest confidence
            if len(symbol_signal_list) > 1:
                best_signal = max(symbol_signal_list, key=lambda s: s.get('confidence', 0))
                logger.info(f"🔄 Deduplication: {symbol} - kept best of {len(symbol_signal_list)} signals")
                deduplicated.append(best_signal)
            else:
                deduplicated.append(symbol_signal_list[0])
        
        # Add all management signals (no deduplication)
        deduplicated.extend(management_signals)
        
        return deduplicated
    
    def _resolve_timestamp_collisions(self, signals: List[Dict]) -> List[Dict]:
        """Resolve timestamp collisions by adding microsecond precision and random suffix"""
        resolved_signals = []
        
        for i, signal in enumerate(signals):
            # Generate unique signal ID with microsecond precision
            timestamp = datetime.now()
            unique_id = f"{signal['symbol']}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}_{i:03d}"
            
            # Add unique identifiers
            signal['signal_id'] = unique_id
            signal['generated_at'] = timestamp
            signal['deduplication_rank'] = i + 1
            
            resolved_signals.append(signal)
        
        return resolved_signals
    
    def _update_signal_history(self, signals: List[Dict]):
        """Update signal history and recent signals tracking"""
        for signal in signals:
            symbol = signal['symbol']
            signal_id = signal['signal_id']
            
            # Add to signal history
            self.signal_history[signal_id] = signal
            
            # Add to recent signals for this symbol
            self.recent_signals[symbol].append({
                'signal_id': signal_id,
                'timestamp': signal['generated_at'],
                'confidence': signal['confidence']
            })
    
    def _cleanup_old_signals(self):
        """Clean up old signals from memory"""
        if (datetime.now() - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.cleanup_interval)
        
        # Clean up recent signals
        for symbol in list(self.recent_signals.keys()):
            self.recent_signals[symbol] = [
                s for s in self.recent_signals[symbol] 
                if s['timestamp'] > cutoff_time
            ]
            
            # Remove empty entries
            if not self.recent_signals[symbol]:
                del self.recent_signals[symbol]
        
        # Clean up signal history
        old_signal_ids = [
            signal_id for signal_id, signal in self.signal_history.items()
            if signal['generated_at'] < cutoff_time
        ]
        
        for signal_id in old_signal_ids:
            del self.signal_history[signal_id]
        
        self.last_cleanup = datetime.now()
        logger.debug(f"🧹 Cleaned up {len(old_signal_ids)} old signals")

    async def register_signal_attempt(self, signal_id: str, symbol: Optional[str] = None) -> Dict:
        """Enforce 30s spacing and max 10 attempts per signal. Returns dict with allowed flag and reason."""
        try:
            now = time.time()
            # Redis-backed enforcement preferred
            if self.redis_client:
                last_key = f"signal_last_try:{signal_id}"
                att_key = f"signal_attempts:{signal_id}"
                # Check last try spacing
                last_try = await self.redis_client.get(last_key)
                if last_try:
                    elapsed = now - float(last_try)
                    if elapsed < self.retry_window_seconds:
                        wait = int(self.retry_window_seconds - elapsed)
                        return { 'allowed': False, 'reason': 'WAIT_WINDOW', 'retry_after_seconds': wait }
                # Increment attempts
                attempts = await self.redis_client.incr(att_key)
                # Set TTL for attempts key to 1 trading day if first time
                if attempts == 1:
                    await self.redis_client.expire(att_key, 86400)
                # Update last try timestamp
                await self.redis_client.set(last_key, str(now), ex=3600)
                if attempts > self.max_attempts_per_signal:
                    # Purge caches and block
                    await self.purge_signal_everywhere(signal_id, symbol)
                    return { 'allowed': False, 'reason': 'MAX_ATTEMPTS_REACHED' }
                return { 'allowed': True, 'reason': 'OK', 'attempts': attempts }
            
            # In-memory fallback
            last_try = self._last_try_memory.get(signal_id)
            if last_try:
                elapsed = now - last_try
                if elapsed < self.retry_window_seconds:
                    wait = int(self.retry_window_seconds - elapsed)
                    return { 'allowed': False, 'reason': 'WAIT_WINDOW', 'retry_after_seconds': wait }
            attempts = self._attempts_memory.get(signal_id, 0) + 1
            self._attempts_memory[signal_id] = attempts
            self._last_try_memory[signal_id] = now
            if attempts > self.max_attempts_per_signal:
                await self.purge_signal_everywhere(signal_id, symbol)
                return { 'allowed': False, 'reason': 'MAX_ATTEMPTS_REACHED' }
            return { 'allowed': True, 'reason': 'OK', 'attempts': attempts }
        except Exception as e:
            logger.error(f"❌ register_signal_attempt error for {signal_id}: {e}")
            return { 'allowed': False, 'reason': 'ERROR_BLOCKED' }  # Block on error
    
    def get_signal_stats(self) -> Dict:
        """Get statistics about signal processing"""
        total_recent = sum(len(signals) for signals in self.recent_signals.values())
        
        return {
            'total_recent_signals': total_recent,
            'symbols_with_signals': len(self.recent_signals),
            'signal_history_size': len(self.signal_history),
            'last_cleanup': self.last_cleanup.isoformat(),
            'min_confidence_threshold': self.min_confidence_threshold,
            'deduplication_window': self.deduplication_window
        }

# Global instance
signal_deduplicator = SignalDeduplicator()

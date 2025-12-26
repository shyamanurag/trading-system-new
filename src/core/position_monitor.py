"""
Position Monitor Service - Continuous Auto Square-Off Monitoring
==============================================================

This service provides continuous monitoring of positions for auto square-off
conditions, integrating seamlessly with the existing trading infrastructure.

Key Features:
- Continuous monitoring of positions against exit conditions
- Time-based exits (3:15 PM IST and 3:30 PM market close)
- Stop loss and target monitoring
- Risk-based emergency exits
- Integration with existing cache system and components
- Non-disruptive background operation

Safety Features:
- Uses existing TrueData cache system
- Respects orchestrator synchronization
- Integrates with existing risk manager
- Maintains all existing component relationships
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pytz
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExitCondition:
    """Represents an exit condition for a position"""
    condition_type: str  # 'time_based', 'stop_loss', 'target', 'risk_based'
    symbol: str
    trigger_price: Optional[float] = None
    trigger_time: Optional[datetime] = None
    reason: str = ""
    priority: int = 1  # 1=highest (emergency), 2=high, 3=normal

class PositionMonitor:
    """
    Continuous Position Monitor for Auto Square-Off
    ==============================================
    
    Monitors positions continuously and executes auto square-off based on:
    - Time-based exits (3:15 PM and 3:30 PM IST)
    - Stop loss conditions
    - Target conditions
    - Risk-based emergency exits
    - Hard stop conditions
    """
    
    def __init__(self, orchestrator, position_tracker, risk_manager, order_manager):
        self.orchestrator = orchestrator
        self.position_tracker = position_tracker
        self.risk_manager = risk_manager
        self.order_manager = order_manager
        # Optional Redis for cooldown signaling
        self.redis_client = None
        try:
            import os
            import redis.asyncio as redis
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True, ssl_cert_reqs=None, ssl_check_hostname=False)
        except Exception:
            self.redis_client = None
        
        # IST timezone for accurate time-based exits
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        
        # Monitoring configuration
        self.monitoring_interval = 5  # seconds
        self.is_running = False
        self.monitor_task = None
        
        # Exit conditions tracking
        self.pending_exits: Dict[str, List[ExitCondition]] = {}
        self.executed_exits: Dict[str, datetime] = {}
        # Local fallback cooldown tracking
        self._local_exit_cooldown: Dict[str, datetime] = {}
        
        # Time-based exit configuration
        self.intraday_exit_time = time(15, 15)  # 3:15 PM IST - Start aggressive square-off
        self.mandatory_close_time = time(15, 20)  # 3:20 PM IST - MUST close ALL positions
        self.market_close_time = time(15, 30)   # 3:30 PM IST - Market close
        
        # Safety flags
        self.emergency_stop_active = False
        self.market_close_initiated = False
        
        logger.info("✅ Position Monitor initialized")
    
    async def start_monitoring(self):
        """Start continuous position monitoring"""
        if self.is_running:
            logger.warning("Position monitor already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🚀 Position Monitor started - continuous auto square-off active")
    
    async def stop_monitoring(self):
        """Stop position monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        logger.info("🛑 Position Monitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Position monitoring loop started")
        
        while self.is_running:
            try:
                # Get current time in IST
                now_ist = datetime.now(self.ist_timezone)
                current_time = now_ist.time()
                
                # Skip monitoring outside market hours (but allow some buffer)
                if not self._is_monitoring_hours(current_time):
                    await asyncio.sleep(30)  # Check every 30 seconds when market closed
                    continue
                
                # Get current positions
                positions = await self.position_tracker.get_all_positions()
                
                if not positions:
                    await asyncio.sleep(self.monitoring_interval)
                    continue
                
                # Get market data for price updates
                market_data = await self._get_market_data()
                
                # Update position prices
                if market_data:
                    await self.position_tracker.update_market_prices(market_data)
                    logger.debug(f"📊 Updated market prices for {len(market_data)} symbols")
                
                # Log current position status for debugging
                for symbol, position in positions.items():
                    if position.side == 'long':
                        pnl = (position.current_price - position.average_price) * position.quantity
                        pnl_percent = ((position.current_price - position.average_price) / position.average_price) * 100
                    else:
                        pnl = (position.average_price - position.current_price) * position.quantity
                        pnl_percent = ((position.average_price - position.current_price) / position.average_price) * 100
                    
                    logger.debug(f"📊 {symbol}: ₹{position.current_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_percent:.1f}%) | SL: ₹{getattr(position, 'stop_loss', 'N/A')} | TGT: ₹{getattr(position, 'target', 'N/A')} | TS: ₹{getattr(position, 'trailing_stop', 'N/A')}")
                
                # Check exit conditions for all positions
                exit_conditions = await self._evaluate_exit_conditions(positions, now_ist)
                
                # Execute exits based on priority
                await self._execute_exits(exit_conditions)
                
                # Log monitoring status with details
                if positions:
                    positions_with_stops = sum(1 for p in positions.values() if hasattr(p, 'stop_loss') and p.stop_loss and p.stop_loss > 0)
                    positions_with_targets = sum(1 for p in positions.values() if hasattr(p, 'target') and p.target and p.target > 0)
                    logger.info(f"📊 POSITION MONITOR: Tracking {len(positions)} positions at {current_time.strftime('%H:%M:%S')} IST")
                    logger.info(f"   ✅ {positions_with_stops}/{len(positions)} have stop loss | {positions_with_targets}/{len(positions)} have targets")
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("🛑 Position monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in position monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
        
        logger.info("🛑 Position monitoring loop stopped")
    
    async def _update_realized_pnl_on_exit(self, condition, exit_signal: Dict):
        """
        🚨 CRITICAL: Update realized P&L when position exits
        Integrates with daily loss limit tracking AND signal performance feedback
        """
        try:
            symbol = condition.symbol
            position = await self.position_tracker.get_position(symbol)
            
            if not position:
                logger.warning(f"⚠️ Cannot update P&L: Position not found for {symbol}")
                return
            
            # Calculate realized P&L
            entry_price = float(position.average_price)
            exit_price = float(condition.trigger_price or position.current_price)
            quantity = int(position.quantity)
            side = position.side
            
            if side == 'long':
                pnl = (exit_price - entry_price) * quantity
            else:  # short
                pnl = (entry_price - exit_price) * quantity
            
            # Update position_opening_decision system
            if hasattr(self.orchestrator, 'position_decision'):
                self.orchestrator.position_decision.update_realized_pnl(pnl, symbol)
                logger.info(f"📊 Updated daily realized P&L: {symbol} → {'Profit' if pnl > 0 else 'Loss'} ₹{abs(pnl):,.2f}")
            else:
                # Fallback: Import directly
                from src.core.position_opening_decision import position_decision_system
                position_decision_system.update_realized_pnl(pnl, symbol)
                logger.info(f"📊 Updated daily realized P&L (fallback): {symbol} → {'Profit' if pnl > 0 else 'Loss'} ₹{abs(pnl):,.2f}")
            
            # 🎯 NEW: FEEDBACK LOOP - Update signal performance tracking!
            # This allows the system to LEARN from trade outcomes
            try:
                from src.core.signal_enhancement import signal_enhancer
                
                # Get strategy name from position metadata
                strategy_name = getattr(position, 'strategy', None) or 'unknown'
                signal_id = f"{symbol}_{position.entry_time.strftime('%Y%m%d_%H%M%S') if hasattr(position, 'entry_time') and position.entry_time else 'unknown'}"
                
                was_profitable = pnl > 0
                signal_enhancer.update_signal_outcome(signal_id, strategy_name, was_profitable, pnl)
                
                logger.info(f"🎯 FEEDBACK LOOP: {strategy_name} {symbol} → {'WIN' if was_profitable else 'LOSS'} ₹{pnl:,.2f}")
                
            except Exception as feedback_err:
                logger.warning(f"⚠️ Feedback loop update failed: {feedback_err}")
                
        except Exception as e:
            logger.error(f"❌ Error updating realized P&L for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _execute_partial_exit(self, symbol: str, side: str, quantity: int, 
                                    current_price: float, reason: str) -> bool:
        """
        Execute partial exit order (book profits on portion of position)
        
        Args:
            symbol: Trading symbol
            side: Position side ('long' or 'short')
            quantity: Quantity to exit
            current_price: Current market price
            reason: Exit reason for logging
            
        Returns:
            bool: True if order placed successfully
        """
        try:
            # 🚨 CRITICAL: Validate exit quantity against actual position
            # This prevents selling more than we hold (which creates unintended shorts)
            actual_position_qty = await self._get_actual_position_quantity(symbol)
            
            if actual_position_qty is None:
                logger.error(f"❌ PARTIAL EXIT BLOCKED: {symbol} - Cannot verify actual position")
                return False
            
            if quantity > actual_position_qty:
                logger.warning(f"🚫 PARTIAL EXIT QUANTITY CAPPED: {symbol}")
                logger.warning(f"   Requested: {quantity} | Actual Position: {actual_position_qty}")
                logger.warning(f"   Capping exit to actual position size to prevent short creation")
                quantity = actual_position_qty
                
                if quantity <= 0:
                    logger.error(f"❌ PARTIAL EXIT BLOCKED: {symbol} - No position to exit")
                    return False
            
            # Determine exit action (opposite of position side)
            exit_action = 'SELL' if side == 'long' else 'BUY'
            
            logger.info(f"📤 EXECUTING PARTIAL EXIT: {symbol} {exit_action} x{quantity}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Price: ₹{current_price:.2f}")
            logger.info(f"   Verified Position: {actual_position_qty} → Exiting: {quantity}")
            
            # Create exit order parameters
            exit_order = {
                'symbol': symbol,
                'action': exit_action,
                'quantity': quantity,
                'order_type': 'MARKET',  # Use MARKET for quick exit
                'product': 'MIS',  # Intraday
                'tag': 'PARTIAL_EXIT',
                'metadata': {
                    'exit_reason': reason,
                    'partial_exit': True,
                    'original_side': side
                }
            }
            
            # Place order through orchestrator's zerodha client
            if hasattr(self.orchestrator, 'zerodha_client') and self.orchestrator.zerodha_client:
                order_id = await self.orchestrator.zerodha_client.place_order(exit_order)
                
                if order_id:
                    logger.info(f"✅ PARTIAL EXIT ORDER PLACED: {symbol} - Order ID: {order_id}")
                    logger.info(f"   Exited {quantity} qty at ~₹{current_price:.2f}")
                    return True
                else:
                    logger.error(f"❌ PARTIAL EXIT FAILED: {symbol} - Order placement returned None")
                    return False
            else:
                logger.error(f"❌ PARTIAL EXIT FAILED: {symbol} - Zerodha client not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing partial exit for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _get_actual_position_quantity(self, symbol: str) -> Optional[int]:
        """
        Get actual position quantity from Zerodha to prevent over-selling.
        
        Returns:
            int: Actual position quantity (positive for long, negative for short)
            None: If unable to verify position
        """
        try:
            if not hasattr(self.orchestrator, 'zerodha_client') or not self.orchestrator.zerodha_client:
                logger.warning(f"⚠️ Cannot verify position for {symbol} - Zerodha client not available")
                return None
            
            # Fetch positions from Zerodha
            positions_data = await self.orchestrator.zerodha_client.get_positions()
            
            if not positions_data:
                logger.warning(f"⚠️ No positions data from Zerodha for {symbol}")
                return None
            
            # Check both net and day positions
            for pos_type in ['net', 'day']:
                positions = positions_data.get(pos_type, [])
                for pos in positions:
                    pos_symbol = pos.get('tradingsymbol', '')
                    if pos_symbol == symbol:
                        quantity = pos.get('quantity', 0)
                        logger.info(f"📊 VERIFIED POSITION: {symbol} qty={quantity} (from Zerodha {pos_type})")
                        return abs(quantity)  # Return absolute value
            
            # Symbol not found in positions
            logger.warning(f"⚠️ Position not found in Zerodha for {symbol}")
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error getting actual position for {symbol}: {e}")
            return None
    
    def _is_monitoring_hours(self, current_time: time) -> bool:
        """Check if we should monitor positions (market hours + buffer)"""
        # Monitor from 9:00 AM to 4:00 PM IST (with buffer)
        monitor_start = time(9, 0)
        monitor_end = time(16, 0)
        
        return monitor_start <= current_time <= monitor_end
    
    async def _get_market_data(self) -> Dict[str, float]:
        """Get current market data using existing cache system + OPTIONS from Zerodha"""
        try:
            # Use orchestrator's market data method (respects existing cache system)
            market_data = await self.orchestrator._get_market_data_from_api()
            
            if not market_data or not market_data.get('data'):
                return {}
            
            # Extract current prices for symbols
            price_data = {}
            for symbol, data in market_data['data'].items():
                if isinstance(data, dict) and 'ltp' in data:
                    price_data[symbol] = data['ltp']
            
            # CRITICAL FIX: Fetch OPTIONS prices from Zerodha (TrueData doesn't have them)
            # Options symbols like "TCS25OCT2940CE" need live prices for P&L calculation
            try:
                positions = await self.orchestrator.position_tracker.get_all_positions()
                options_symbols = [
                    symbol for symbol in positions.keys() 
                    if symbol.endswith('CE') or symbol.endswith('PE')
                ]
                
                if options_symbols and self.orchestrator.zerodha_client:
                    logger.debug(f"📊 Fetching live prices for {len(options_symbols)} options contracts")
                    
                    # Fetch options prices from Zerodha in batch
                    options_prices = await self._fetch_options_prices_from_zerodha(options_symbols)
                    
                    # Merge options prices into price_data
                    price_data.update(options_prices)
                    
                    if options_prices:
                        logger.info(f"✅ Updated {len(options_prices)} options prices from Zerodha")
                    
            except Exception as options_err:
                logger.warning(f"⚠️ Could not fetch options prices: {options_err}")
            
            return price_data
            
        except Exception as e:
            logger.error(f"❌ Error getting market data for position monitoring: {e}")
            return {}
    
    async def _fetch_options_prices_from_zerodha(self, symbols: list) -> Dict[str, float]:
        """Fetch options prices from Zerodha quote API"""
        try:
            if not symbols:
                return {}
            
            # Build exchange:symbol format for Zerodha
            zerodha_symbols = [f"NFO:{symbol}" for symbol in symbols]
            
            # Fetch quotes from Zerodha
            quotes = await self.orchestrator.zerodha_client.get_quote(zerodha_symbols)
            
            if not quotes or not isinstance(quotes, dict):
                return {}
            
            # Extract LTP for each symbol
            prices = {}
            for zerodha_symbol, quote_data in quotes.items():
                if isinstance(quote_data, dict) and 'last_price' in quote_data:
                    # Remove "NFO:" prefix to get clean symbol
                    clean_symbol = zerodha_symbol.replace('NFO:', '')
                    prices[clean_symbol] = float(quote_data['last_price'])
                    logger.debug(f"📊 {clean_symbol}: ₹{prices[clean_symbol]:.2f}")
            
            return prices
            
        except Exception as e:
            logger.error(f"❌ Error fetching options prices from Zerodha: {e}")
            return {}
    
    async def _evaluate_exit_conditions(self, positions: Dict, now_ist: datetime) -> List[ExitCondition]:
        """Evaluate all exit conditions for current positions"""
        exit_conditions = []
        current_time = now_ist.time()
        
        for symbol, position in positions.items():
            # Skip if position already has pending exit
            if symbol in self.executed_exits:
                continue
            
            # 1. Time-based exits (HIGHEST PRIORITY)
            time_exit = self._check_time_based_exit(symbol, position, current_time)
            if time_exit:
                exit_conditions.append(time_exit)
                continue  # Time exits override other conditions
            
            # 🚨 SANITY CHECK: Verify position.side matches SL/Target setup
            # If SL < entry < target → should be LONG
            # If SL > entry > target → should be SHORT
            entry = position.average_price
            sl = getattr(position, 'stop_loss', None)
            tgt = getattr(position, 'target', None)
            if sl and tgt and entry:
                expected_side = 'long' if sl < entry < tgt else 'short' if sl > entry > tgt else position.side
                if expected_side != position.side:
                    logger.error(f"🚨 DATA INTEGRITY: {symbol} has side='{position.side}' but SL/Target suggests '{expected_side}'")
                    logger.error(f"   Entry: ₹{entry:.2f}, SL: ₹{sl:.2f}, Target: ₹{tgt:.2f}")
                    # FIX the side to match the SL/Target setup
                    position.side = expected_side
                    logger.info(f"   ✅ Auto-corrected side to '{expected_side}'")
            
            # 2. 🎯 SCALP TIME-BASED EXIT - Quick in/out for choppy markets
            scalp_exit = self._check_scalp_time_exit(symbol, position)
            if scalp_exit:
                exit_conditions.append(scalp_exit)
                continue  # Scalp timeout takes priority
            
            # 3. Stop loss conditions
            stop_loss_exit = self._check_stop_loss_exit(symbol, position)
            if stop_loss_exit:
                exit_conditions.append(stop_loss_exit)
                continue  # 🚨 FIX: Don't also check target if SL is triggered
            
            # 4. Target conditions
            target_exit = await self._check_target_exit(symbol, position)
            if target_exit:
                exit_conditions.append(target_exit)
                continue  # 🚨 FIX: Don't also check trailing if target is hit
            
            # 4. Trailing stop conditions
            trailing_exit = self._check_trailing_stop_exit(symbol, position)
            if trailing_exit:
                exit_conditions.append(trailing_exit)
            
            # 5. Risk-based emergency exits
            risk_exit = await self._check_risk_based_exit(symbol, position)
            if risk_exit:
                exit_conditions.append(risk_exit)
        
        return exit_conditions
    
    def _check_time_based_exit(self, symbol: str, position, current_time: time) -> Optional[ExitCondition]:
        """Check time-based exit conditions"""
        
        # Market close exit (3:30 PM IST) - EMERGENCY (should never have positions here)
        if current_time >= self.market_close_time:
            if not self.market_close_initiated:
                self.market_close_initiated = True
                logger.error(f"🚨🚨 MARKET CLOSE EMERGENCY: Positions still open at 3:30 PM! Force square-off!")
            
            return ExitCondition(
                condition_type='time_based',
                symbol=symbol,
                trigger_time=datetime.now(self.ist_timezone),
                reason=f'EMERGENCY market close at {current_time.strftime("%H:%M:%S")} IST',
                priority=0  # EMERGENCY priority
            )
        
        # 🔥 MANDATORY CLOSE (3:20 PM IST) - MUST close ALL positions by this time
        if current_time >= self.mandatory_close_time:
            if not hasattr(self, '_mandatory_close_initiated') or not self._mandatory_close_initiated:
                self._mandatory_close_initiated = True
                logger.warning(f"🚨 MANDATORY 3:20 PM CLOSE: ALL positions MUST close NOW!")
            
            return ExitCondition(
                condition_type='time_based',
                symbol=symbol,
                trigger_time=datetime.now(self.ist_timezone),
                reason=f'MANDATORY close at {current_time.strftime("%H:%M:%S")} IST - ALL positions must close by 3:20 PM',
                priority=1  # Highest priority
            )
        
        # Intraday exit window (3:15-3:20 PM IST) - Aggressive square-off
        if current_time >= self.intraday_exit_time:
            return ExitCondition(
                condition_type='time_based',
                symbol=symbol,
                trigger_time=datetime.now(self.ist_timezone),
                reason=f'Intraday square-off at {current_time.strftime("%H:%M:%S")} IST (3:15-3:20 window)',
                priority=2  # High priority
            )
        
        return None
    
    def _check_scalp_time_exit(self, symbol: str, position) -> Optional[ExitCondition]:
        """
        🎯 SCALP TIME-BASED EXIT - Quick in/out for choppy markets (Hybrid Approach)
        
        For SCALP mode trades (MTF 0-1/3), exit after max_hold_minutes regardless of P&L.
        This prevents being stuck in choppy markets.
        """
        try:
            # Check if this is a SCALP trade
            metadata = getattr(position, 'metadata', {}) or {}
            hybrid_mode = metadata.get('hybrid_mode', 'SWING')
            max_hold_minutes = metadata.get('max_hold_minutes', 0)
            
            # Only apply to SCALP trades with time limit
            if hybrid_mode != 'SCALP' or max_hold_minutes <= 0:
                return None
            
            # Calculate time in position
            entry_time = getattr(position, 'entry_time', None) or getattr(position, 'created_at', None)
            if not entry_time:
                return None
            
            # Handle different datetime formats
            if isinstance(entry_time, str):
                try:
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                except:
                    return None
            
            now = datetime.now(self.ist_timezone)
            if entry_time.tzinfo is None:
                entry_time = self.ist_timezone.localize(entry_time)
            
            time_in_position = (now - entry_time).total_seconds() / 60  # minutes
            
            # Check if exceeded max hold time
            if time_in_position >= max_hold_minutes:
                current_price = position.current_price
                entry_price = position.average_price
                pnl_pct = ((current_price - entry_price) / entry_price) * 100 if position.side == 'long' else \
                          ((entry_price - current_price) / entry_price) * 100
                
                # 🔥 FIX: Only exit on timeout if in PROFIT or after EXTENDED timeout (2x)
                # This prevents locking in losses due to slippage
                MIN_PROFIT_FOR_TIMEOUT_EXIT = 0.1  # Need at least 0.1% profit to exit on timeout
                EXTENDED_TIMEOUT_MULTIPLIER = 2.0  # Wait 2x longer if in loss
                
                if pnl_pct >= MIN_PROFIT_FOR_TIMEOUT_EXIT:
                    # In profit - exit now
                    logger.info(f"⚡ SCALP TIMEOUT (PROFIT): {symbol} held {time_in_position:.1f}min | P&L: {pnl_pct:+.2f}%")
                    return ExitCondition(
                        condition_type='scalp_timeout',
                        symbol=symbol,
                        trigger_time=now,
                        reason=f'SCALP timeout with profit after {time_in_position:.1f}min | P&L: {pnl_pct:+.2f}%',
                        priority=2
                    )
                elif time_in_position >= max_hold_minutes * EXTENDED_TIMEOUT_MULTIPLIER:
                    # Extended timeout - exit even at loss (to limit exposure)
                    logger.warning(f"⚡ SCALP EXTENDED TIMEOUT: {symbol} held {time_in_position:.1f}min (2x max) | P&L: {pnl_pct:+.2f}%")
                    return ExitCondition(
                        condition_type='scalp_timeout',
                        symbol=symbol,
                        trigger_time=now,
                        reason=f'SCALP extended timeout after {time_in_position:.1f}min | P&L: {pnl_pct:+.2f}%',
                        priority=2
                    )
                else:
                    # In loss but not extended timeout - wait longer
                    logger.info(f"⏳ SCALP HOLD: {symbol} in loss ({pnl_pct:+.2f}%) - waiting for recovery or extended timeout")
            
            return None
            
        except Exception as e:
            logger.debug(f"Scalp time check error for {symbol}: {e}")
            return None
    
    def _check_stop_loss_exit(self, symbol: str, position) -> Optional[ExitCondition]:
        """Check stop loss conditions with TRAILING STOP-LOSS and enhanced logging"""
        if not hasattr(position, 'stop_loss') or not position.stop_loss:
            return None
        
        current_price = position.current_price
        stop_loss_price = position.stop_loss
        entry_price = position.average_price
        
        # Ensure we have valid prices
        if not current_price or current_price <= 0:
            return None
        
        # Calculate current P&L
        if position.side == 'long':
            current_pnl = (current_price - entry_price) * position.quantity
            current_pnl_percent = ((current_price - entry_price) / entry_price) * 100
        else:
            current_pnl = (entry_price - current_price) * position.quantity
            current_pnl_percent = ((entry_price - current_price) / entry_price) * 100
        
        # 🚨 CRITICAL FIX: TRAILING STOP-LOSS
        # If position is in profit >= 2% (aligned with max 2% risk per trade), lock profit
        if current_pnl_percent >= 2.0:
            # Calculate trailing stop to lock in 50% of current profit
            if position.side == 'long':
                profit_from_entry = current_price - entry_price
                trailing_stop = entry_price + (profit_from_entry * 0.5)  # Lock 50% profit
                
                # Update stop-loss if trailing stop is higher than current stop
                if trailing_stop > stop_loss_price:
                    protected_profit_pct = ((trailing_stop - entry_price) / entry_price) * 100
                    logger.info(f"📈 TRAILING STOP ACTIVATED - {symbol}:")
                    logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                    logger.info(f"   Current Profit: {current_pnl_percent:.1f}% (₹{current_pnl:.2f})")
                    logger.info(f"   OLD Stop: ₹{stop_loss_price:.2f} → NEW Trailing Stop: ₹{trailing_stop:.2f}")
                    logger.info(f"   Protected Profit: {protected_profit_pct:.1f}% (₹{(trailing_stop - entry_price) * position.quantity:.2f})")
                    
                    # Update the position's stop-loss
                    position.stop_loss = trailing_stop
                    stop_loss_price = trailing_stop
            else:  # short position
                profit_from_entry = entry_price - current_price
                trailing_stop = entry_price - (profit_from_entry * 0.5)  # Lock 50% profit
                
                if trailing_stop < stop_loss_price:
                    protected_profit_pct = ((entry_price - trailing_stop) / entry_price) * 100
                    logger.info(f"📈 TRAILING STOP ACTIVATED - {symbol}:")
                    logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                    logger.info(f"   Current Profit: {current_pnl_percent:.1f}% (₹{current_pnl:.2f})")
                    logger.info(f"   OLD Stop: ₹{stop_loss_price:.2f} → NEW Trailing Stop: ₹{trailing_stop:.2f}")
                    logger.info(f"   Protected Profit: {protected_profit_pct:.1f}% (₹{(entry_price - trailing_stop) * position.quantity:.2f})")
                    
                    position.stop_loss = trailing_stop
                    stop_loss_price = trailing_stop
        
        # Check if stop loss is triggered
        if position.side == 'long' and current_price <= stop_loss_price:
            logger.warning(f"🚨 STOP LOSS TRIGGERED - {symbol}:")
            logger.warning(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
            logger.warning(f"   Stop Loss: ₹{stop_loss_price:.2f}")
            logger.warning(f"   P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
            
            return ExitCondition(
                condition_type='stop_loss',
                symbol=symbol,
                trigger_price=current_price,
                reason=f'Stop loss triggered: {current_price:.2f} <= {stop_loss_price:.2f} (P&L: ₹{current_pnl:.2f})',
                priority=2  # High priority
            )
        elif position.side == 'short' and current_price >= stop_loss_price:
            logger.warning(f"🚨 STOP LOSS TRIGGERED - {symbol}:")
            logger.warning(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
            logger.warning(f"   Stop Loss: ₹{stop_loss_price:.2f}")
            logger.warning(f"   P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
            
            return ExitCondition(
                condition_type='stop_loss',
                symbol=symbol,
                trigger_price=current_price,
                reason=f'Stop loss triggered: {current_price:.2f} >= {stop_loss_price:.2f} (P&L: ₹{current_pnl:.2f})',
                priority=2  # High priority
            )
        
        return None
    
    async def _check_target_exit(self, symbol: str, position) -> Optional[ExitCondition]:
        """Check target conditions with PARTIAL PROFIT BOOKING and enhanced logging"""
        if not hasattr(position, 'target') or not position.target:
            return None
        
        current_price = position.current_price
        target_price = position.target
        entry_price = position.average_price
        
        # Ensure we have valid prices
        if not current_price or current_price <= 0:
            return None
        
        # Calculate current P&L
        if position.side == 'long':
            current_pnl = (current_price - entry_price) * position.quantity
            current_pnl_percent = ((current_price - entry_price) / entry_price) * 100
        else:
            current_pnl = (entry_price - current_price) * position.quantity
            current_pnl_percent = ((entry_price - current_price) / entry_price) * 100
        
        # 🚨 CRITICAL FIX: PARTIAL PROFIT BOOKING
        # Track if we've already booked partial profit for this position
        if not hasattr(position, 'partial_profit_booked'):
            position.partial_profit_booked = False
        
        # Check if target is achieved
        if position.side == 'long' and current_price >= target_price:
            if not position.partial_profit_booked:
                # First time hitting target - BOOK 50% PROFIT, keep 50% running
                logger.info(f"🎯 TARGET ACHIEVED (1st time) - {symbol}: BOOKING 50% PROFIT")
                logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.info(f"   Target: ₹{target_price:.2f}")
                logger.info(f"   Total Profit: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                # Calculate partial exit quantity (50%)
                # 🚨 FIX: Handle small positions (qty=1 should do FULL exit, not 0 qty partial)
                # 🔥 FIX: Minimum quantity for partial exits to avoid tiny trades
                MIN_PARTIAL_EXIT_QTY = 10  # Minimum 10 shares for partial exit
                
                # 🚨 OPTIONS FIX: Options can only be traded in lot sizes (75 for NIFTY, 30 for BANKNIFTY)
                # Partial exits don't work for options - always do FULL exit
                is_options = any(x in symbol.upper() for x in ['CE', 'PE'])
                if is_options:
                    logger.info(f"   📋 OPTIONS POSITION: {symbol} - Lot-size constraint, doing FULL EXIT")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit for options (lot-size constraint) (Profit: ₹{current_pnl:.2f})',
                        priority=3
                    )
                
                if position.quantity <= MIN_PARTIAL_EXIT_QTY:
                    logger.info(f"   ℹ️ Small position (qty={position.quantity} <= {MIN_PARTIAL_EXIT_QTY}) - Doing FULL EXIT instead of partial")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit for small position (Profit: ₹{current_pnl:.2f})',
                        priority=3
                    )
                
                partial_exit_qty = position.quantity // 2
                remaining_qty = position.quantity - partial_exit_qty
                
                # Extra safety check - don't place tiny orders
                if partial_exit_qty < MIN_PARTIAL_EXIT_QTY:
                    logger.warning(f"   ⚠️ Partial qty {partial_exit_qty} < min {MIN_PARTIAL_EXIT_QTY} - Full exit instead")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit (partial qty too small)',
                        priority=3
                    )
                
                if partial_exit_qty <= 0:
                    logger.warning(f"   ⚠️ Calculated partial qty is 0 - Skipping partial, will do full exit later")
                    return None
                
                logger.info(f"   Action: Book 50% ({partial_exit_qty} qty), Keep 50% ({remaining_qty} qty) running")
                
                # 🚨 CRITICAL FIX: Execute partial exit order
                exit_success = await self._execute_partial_exit(
                    symbol=symbol,
                    side=position.side,
                    quantity=partial_exit_qty,
                    current_price=current_price,
                    reason='Target Hit - Partial Profit Booking'
                )
                
                if exit_success:
                    # Update position quantity
                    position.quantity = remaining_qty
                    position.partial_profit_booked = True
                    
                    # Move trailing stop to protect 30% of remaining profit
                    profit_from_entry = current_price - entry_price
                    new_trailing_stop = entry_price + (profit_from_entry * 0.3)
                    position.stop_loss = max(position.stop_loss, new_trailing_stop)
                    
                    logger.info(f"✅ PARTIAL EXIT SUCCESSFUL: Sold {partial_exit_qty}, Remaining {remaining_qty}")
                    logger.info(f"   Updated trailing stop to ₹{position.stop_loss:.2f} (30% profit locked)")
                else:
                    logger.error(f"❌ PARTIAL EXIT FAILED for {symbol} - will retry on next cycle")
                
                return None  # Don't full exit yet, keep remaining position running
            else:
                # Second time hitting target (price came back and re-hit target) - FULL EXIT
                logger.info(f"🎯🎯 TARGET RE-ACHIEVED - {symbol}: FULL EXIT")
                logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.info(f"   Profit: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                return ExitCondition(
                    condition_type='target',
                    symbol=symbol,
                    trigger_price=current_price,
                    reason=f'Target re-achieved: Full exit at {current_price:.2f} (Profit: ₹{current_pnl:.2f})',
                    priority=3  # Normal priority
                )
        elif position.side == 'short' and current_price <= target_price:
            if not position.partial_profit_booked:
                logger.info(f"🎯 TARGET ACHIEVED (1st time) - {symbol}: BOOKING 50% PROFIT")
                logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.info(f"   Target: ₹{target_price:.2f}")
                logger.info(f"   Total Profit: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                # 🔥 FIX: Minimum quantity for partial exits to avoid tiny trades
                MIN_PARTIAL_EXIT_QTY = 10  # Minimum 10 shares for partial exit
                
                # 🚨 OPTIONS FIX: Options can only be traded in lot sizes
                # Partial exits don't work for options - always do FULL exit
                is_options = any(x in symbol.upper() for x in ['CE', 'PE'])
                if is_options:
                    logger.info(f"   📋 OPTIONS POSITION: {symbol} - Lot-size constraint, doing FULL EXIT")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit for options (lot-size constraint) (Profit: ₹{current_pnl:.2f})',
                        priority=3
                    )
                
                if position.quantity <= MIN_PARTIAL_EXIT_QTY:
                    logger.info(f"   ℹ️ Small position (qty={position.quantity} <= {MIN_PARTIAL_EXIT_QTY}) - Doing FULL EXIT instead of partial")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit for small position (Profit: ₹{current_pnl:.2f})',
                        priority=3
                    )
                
                partial_exit_qty = position.quantity // 2
                remaining_qty = position.quantity - partial_exit_qty
                
                # Extra safety check - don't place tiny orders
                if partial_exit_qty < MIN_PARTIAL_EXIT_QTY:
                    logger.warning(f"   ⚠️ Partial qty {partial_exit_qty} < min {MIN_PARTIAL_EXIT_QTY} - Full exit instead")
                    return ExitCondition(
                        condition_type='target',
                        symbol=symbol,
                        trigger_price=current_price,
                        reason=f'Target achieved: Full exit (partial qty too small)',
                        priority=3
                    )
                
                if partial_exit_qty <= 0:
                    logger.warning(f"   ⚠️ Calculated partial qty is 0 - Skipping partial, will do full exit later")
                    return None
                
                logger.info(f"   Action: Book 50% ({partial_exit_qty} qty), Keep 50% ({remaining_qty} qty) running")
                
                # 🚨 CRITICAL FIX: Execute partial exit order
                exit_success = await self._execute_partial_exit(
                    symbol=symbol,
                    side=position.side,
                    quantity=partial_exit_qty,
                    current_price=current_price,
                    reason='Target Hit - Partial Profit Booking'
                )
                
                if exit_success:
                    # Update position quantity
                    position.quantity = remaining_qty
                    position.partial_profit_booked = True
                    
                    # Move trailing stop to protect 30% of remaining profit
                    profit_from_entry = entry_price - current_price
                    new_trailing_stop = entry_price - (profit_from_entry * 0.3)
                    position.stop_loss = min(position.stop_loss, new_trailing_stop)
                    
                    logger.info(f"✅ PARTIAL EXIT SUCCESSFUL: Covered {partial_exit_qty}, Remaining {remaining_qty}")
                    logger.info(f"   Updated trailing stop to ₹{position.stop_loss:.2f} (30% profit locked)")
                else:
                    logger.error(f"❌ PARTIAL EXIT FAILED for {symbol} - will retry on next cycle")
                
                return None  # Keep remaining position running
            else:
                logger.info(f"🎯🎯 TARGET RE-ACHIEVED - {symbol}: FULL EXIT")
                logger.info(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.info(f"   Profit: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                return ExitCondition(
                    condition_type='target',
                    symbol=symbol,
                    trigger_price=current_price,
                    reason=f'Target re-achieved: Full exit at {current_price:.2f} (Profit: ₹{current_pnl:.2f})',
                    priority=3  # Normal priority
                )
        
        return None
    
    def _check_trailing_stop_exit(self, symbol: str, position) -> Optional[ExitCondition]:
        """Check trailing stop conditions - ENHANCED IMPLEMENTATION"""
        if not hasattr(position, 'trailing_stop') or not position.trailing_stop:
            return None
        
        current_price = position.current_price
        entry_price = position.average_price
        trailing_stop_price = position.trailing_stop
        
        # Ensure we have valid prices
        if not current_price or current_price <= 0:
            logger.warning(f"⚠️ Invalid current price for {symbol}: {current_price}")
            return None
        
        # Calculate current P&L for position
        if position.side == 'long':
            current_pnl = (current_price - entry_price) * position.quantity
            current_pnl_percent = ((current_price - entry_price) / entry_price) * 100
        else:
            current_pnl = (entry_price - current_price) * position.quantity
            current_pnl_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Update trailing stop if position is profitable (at least 1% profit)
        if position.side == 'long':
            # For long positions, trail stop upwards as price rises
            if current_price > entry_price and current_pnl_percent > 1.0:  # At least 1% profit
                # Calculate new trailing stop - more conservative approach
                profit = current_price - entry_price
                # Trail 40% behind current price for better protection
                new_trailing_stop = current_price - (profit * 0.4)
                
                # Ensure new stop is at least 1% above entry to lock in some profit
                min_profitable_stop = entry_price * 1.01
                new_trailing_stop = max(new_trailing_stop, min_profitable_stop)
                
                # Only update if new stop is higher than current
                if new_trailing_stop > trailing_stop_price:
                    old_trailing_stop = trailing_stop_price
                    position.trailing_stop = new_trailing_stop
                    trailing_stop_price = new_trailing_stop
                    
                    logger.info(f"📈 TRAILING STOP UPDATED - {symbol}:")
                    logger.info(f"   Current Price: ₹{current_price:.2f}")
                    logger.info(f"   P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                    logger.info(f"   Trailing Stop: ₹{old_trailing_stop:.2f} → ₹{new_trailing_stop:.2f}")
            
            # Check if trailing stop is triggered
            if current_price <= trailing_stop_price:
                logger.warning(f"🚨 TRAILING STOP TRIGGERED - {symbol}:")
                logger.warning(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.warning(f"   Trailing Stop: ₹{trailing_stop_price:.2f}")
                logger.warning(f"   Final P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                return ExitCondition(
                    condition_type='trailing_stop',
                    symbol=symbol,
                    trigger_price=current_price,
                    reason=f'Trailing stop triggered: {current_price:.2f} <= {trailing_stop_price:.2f} (P&L: {current_pnl:.2f})',
                    priority=2  # High priority
                )
        
        elif position.side == 'short':
            # For short positions, trail stop downwards as price falls
            if current_price < entry_price and current_pnl_percent > 1.0:  # At least 1% profit
                # Calculate new trailing stop
                profit = entry_price - current_price
                new_trailing_stop = current_price + (profit * 0.4)  # Trail 40% above current price
                
                # Ensure new stop is at least 1% below entry to lock in some profit
                max_profitable_stop = entry_price * 0.99
                new_trailing_stop = min(new_trailing_stop, max_profitable_stop)
                
                # Only update if new stop is lower than current
                if new_trailing_stop < trailing_stop_price:
                    old_trailing_stop = trailing_stop_price
                    position.trailing_stop = new_trailing_stop
                    trailing_stop_price = new_trailing_stop
                    
                    logger.info(f"📉 TRAILING STOP UPDATED - {symbol}:")
                    logger.info(f"   Current Price: ₹{current_price:.2f}")
                    logger.info(f"   P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                    logger.info(f"   Trailing Stop: ₹{old_trailing_stop:.2f} → ₹{new_trailing_stop:.2f}")
            
            # Check if trailing stop is triggered
            if current_price >= trailing_stop_price:
                logger.warning(f"🚨 TRAILING STOP TRIGGERED - {symbol}:")
                logger.warning(f"   Entry: ₹{entry_price:.2f} → Current: ₹{current_price:.2f}")
                logger.warning(f"   Trailing Stop: ₹{trailing_stop_price:.2f}")
                logger.warning(f"   Final P&L: ₹{current_pnl:.2f} ({current_pnl_percent:.1f}%)")
                
                return ExitCondition(
                    condition_type='trailing_stop',
                    symbol=symbol,
                    trigger_price=current_price,
                    reason=f'Trailing stop triggered: {current_price:.2f} >= {trailing_stop_price:.2f} (P&L: {current_pnl:.2f})',
                    priority=2  # High priority
                )
        
        return None
    
    async def _check_risk_based_exit(self, symbol: str, position) -> Optional[ExitCondition]:
        """Check risk-based emergency exit conditions"""
        try:
            # Check if risk manager indicates emergency stop
            if hasattr(self.risk_manager, 'emergency_stop_triggered') and self.risk_manager.emergency_stop_triggered:
                return ExitCondition(
                    condition_type='risk_based',
                    symbol=symbol,
                    reason='Risk manager emergency stop triggered',
                    priority=1  # Highest priority
                )
            
            # Check daily loss limits
            if hasattr(self.risk_manager, 'daily_pnl') and hasattr(self.risk_manager, 'risk_limits'):
                daily_pnl = self.risk_manager.daily_pnl
                max_daily_loss = self.risk_manager.risk_limits.get('max_daily_loss_percent', 0.02)
                total_capital = self.position_tracker.capital
                
                if daily_pnl < -total_capital * max_daily_loss:
                    return ExitCondition(
                        condition_type='risk_based',
                        symbol=symbol,
                        reason=f'Daily loss limit exceeded: {daily_pnl:.2f}',
                        priority=1  # Highest priority
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking risk-based exit for {symbol}: {e}")
            return None
    
    async def _execute_exits(self, exit_conditions: List[ExitCondition]):
        """Execute exits based on priority"""
        if not exit_conditions:
            return
        
        # Sort by priority (1=highest, 3=lowest)
        exit_conditions.sort(key=lambda x: x.priority)
        
        for condition in exit_conditions:
            try:
                # Skip if already executed
                if condition.symbol in self.executed_exits:
                    continue
                
                # Execute the exit
                success = await self._execute_single_exit(condition)
                
                if success:
                    # Mark as executed
                    self.executed_exits[condition.symbol] = datetime.now(self.ist_timezone)
                    
                    # Purge symbol state from all strategies so they decide fresh
                    try:
                        for key, meta in getattr(self.orchestrator, 'strategies', {}).items():
                            inst = meta.get('instance') if isinstance(meta, dict) else None
                            if inst and hasattr(inst, 'purge_symbol_state'):
                                inst.purge_symbol_state(condition.symbol)
                        logger.info(f"🧹 Purged symbol state across strategies for {condition.symbol}")
                    except Exception as purge_err:
                        logger.debug(f"Purge across strategies failed for {condition.symbol}: {purge_err}")
                    
                    # Log the exit
                    logger.info(f"✅ AUTO SQUARE-OFF: {condition.symbol} - {condition.reason}")
                else:
                    logger.error(f"❌ Failed to execute auto square-off for {condition.symbol}")
                
            except Exception as e:
                logger.error(f"❌ Error executing exit for {condition.symbol}: {e}")
    
    async def _execute_single_exit(self, condition: ExitCondition) -> bool:
        """Execute a single position exit"""
        try:
            # Get current position
            position = await self.position_tracker.get_position(condition.symbol)
            if not position:
                logger.warning(f"⚠️ Position not found for exit: {condition.symbol}")
                return False
            
            # Create exit signal
            exit_signal = {
                'symbol': condition.symbol,
                'action': 'EXIT',
                'quantity': abs(position.quantity),
                'reason': condition.reason,
                'condition_type': condition.condition_type,
                'priority': condition.priority,
                'timestamp': datetime.now(self.ist_timezone).isoformat()
            }
            
            # Execute through order manager if available
            if self.order_manager:
                try:
                    # Use order manager to place exit order
                    placed_orders = await self.order_manager.place_strategy_order('position_monitor', exit_signal)
                    
                    if placed_orders:
                        logger.info(f"✅ Exit order placed through OrderManager for {condition.symbol}")
                        
                        # 🚨 CRITICAL: Update realized P&L for daily loss limit tracking
                        await self._update_realized_pnl_on_exit(condition, exit_signal)
                        
                        # 🚪 SET EXIT COOLDOWN to prevent immediate re-entry after profit booking
                        try:
                            if hasattr(self, 'orchestrator') and self.orchestrator:
                                if hasattr(self.orchestrator, 'signal_deduplicator') and self.orchestrator.signal_deduplicator:
                                    await self.orchestrator.signal_deduplicator.set_exit_cooldown(condition.symbol)
                                    logger.info(f"🚪 Exit cooldown set for {condition.symbol} via signal deduplicator")
                        except Exception as cooldown_err:
                            logger.warning(f"⚠️ Could not set exit cooldown for {condition.symbol}: {cooldown_err}")
                        
                        return True
                    else:
                        logger.warning(f"⚠️ OrderManager returned no orders for {condition.symbol}")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ OrderManager exit failed for {condition.symbol}: {e}")
                    return False
            
            # Fallback: Close position directly through position tracker
            exit_price = condition.trigger_price or position.current_price
            realized_pnl = await self.position_tracker.close_position(condition.symbol, exit_price)
            
            if realized_pnl is not None:
                logger.info(f"✅ Position closed directly for {condition.symbol}, PnL: {realized_pnl:.2f}")
                
                # 🚪 SET EXIT COOLDOWN to prevent immediate re-entry after profit booking
                try:
                    if hasattr(self, 'orchestrator') and self.orchestrator:
                        if hasattr(self.orchestrator, 'signal_deduplicator') and self.orchestrator.signal_deduplicator:
                            await self.orchestrator.signal_deduplicator.set_exit_cooldown(condition.symbol)
                            logger.info(f"🚪 Exit cooldown set for {condition.symbol} (direct close)")
                except Exception as cooldown_err:
                    logger.warning(f"⚠️ Could not set exit cooldown for {condition.symbol}: {cooldown_err}")
                
                return True
            else:
                logger.error(f"❌ Failed to close position directly for {condition.symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing single exit for {condition.symbol}: {e}")
            return False

    async def _set_post_exit_cooldown(self, symbol: str, cooldown_seconds: int = 600):
        """Set a post-exit cooldown marker to block immediate re-entry signals."""
        try:
            now = datetime.now(self.ist_timezone)
            self._local_exit_cooldown[symbol] = now
            if self.redis_client:
                date_str = now.strftime('%Y-%m-%d')
                key = f"post_exit_cooldown:{date_str}:{symbol}"
                await self.redis_client.set(key, now.isoformat(), ex=cooldown_seconds)
                logger.info(f"🧊 Post-exit cooldown set for {symbol} ({cooldown_seconds}s)")
            else:
                logger.info(f"🧊 Post-exit cooldown set locally for {symbol} ({cooldown_seconds}s)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set post-exit cooldown for {symbol}: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        try:
            positions = await self.position_tracker.get_all_positions()
            
            return {
                'is_running': self.is_running,
                'positions_monitored': len(positions),
                'pending_exits': len(self.pending_exits),
                'executed_exits': len(self.executed_exits),
                'emergency_stop_active': self.emergency_stop_active,
                'market_close_initiated': self.market_close_initiated,
                'monitoring_interval': self.monitoring_interval,
                'current_time_ist': datetime.now(self.ist_timezone).strftime('%H:%M:%S'),
                'intraday_exit_time': self.intraday_exit_time.strftime('%H:%M'),
                'market_close_time': self.market_close_time.strftime('%H:%M'),
                'timestamp': datetime.now(self.ist_timezone).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting monitoring status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e),
                'timestamp': datetime.now(self.ist_timezone).isoformat()
            }
    
    async def force_square_off_all(self, reason: str = "Manual square-off") -> Dict[str, Any]:
        """Force square-off all positions immediately"""
        try:
            logger.warning(f"🚨 FORCE SQUARE-OFF: {reason}")
            
            positions = await self.position_tracker.get_all_positions()
            
            if not positions:
                return {
                    'success': True,
                    'message': 'No positions to square-off',
                    'positions_closed': 0
                }
            
            # Create exit conditions for all positions
            exit_conditions = []
            for symbol, position in positions.items():
                exit_conditions.append(ExitCondition(
                    condition_type='manual',
                    symbol=symbol,
                    reason=reason,
                    priority=1  # Highest priority
                ))
            
            # Execute all exits
            await self._execute_exits(exit_conditions)
            
            return {
                'success': True,
                'message': f'Square-off initiated for {len(positions)} positions',
                'positions_closed': len(exit_conditions),
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"❌ Error in force square-off: {e}")
            return {
                'success': False,
                'error': str(e),
                'reason': reason
            } 
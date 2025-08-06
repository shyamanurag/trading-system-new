"""
Base Strategy Class - SCALPING OPTIMIZED
Common functionality for all trading strategies with proper ATR calculation and SCALPING risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
import numpy as np
import pytz  # Add timezone support
import time as time_module # Added for time.time() - avoid conflict with datetime.time

logger = logging.getLogger(__name__)

class BaseStrategy:
    """Base class for all trading strategies with SCALPING-OPTIMIZED timing and risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "BaseStrategy"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)
        
        # CRITICAL: Signal rate limiting to prevent flooding
        self.max_signals_per_hour = 50  # Maximum 50 signals per hour (manageable)
        self.max_signals_per_strategy = 10  # Maximum 10 signals per strategy per hour
        self.signals_generated_this_hour = 0
        self.strategy_signals_this_hour = 0
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        self.hour_start_time = datetime.now(ist)
        
        # Enhanced cooldown control
        self.scalping_cooldown = 30  # 30 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
        # CRITICAL: Position Management System
        self.active_positions = {}  # symbol -> position data with strategy linkage
        self.position_metadata = {}  # symbol -> strategy-specific position data
        self.trailing_stops = {}  # symbol -> trailing stop data
        self.position_entry_times = {}  # symbol -> entry timestamp
        
        # Position deduplication and management flags
        self.max_position_age_hours = 24  # Auto-close positions after 24 hours
        self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
        self.profit_lock_percentage = 1.0  # Lock profit at 1%
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        time_since_last = (current_time_ist - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
    def _check_signal_rate_limits(self) -> bool:
        """Check if signal generation is allowed based on rate limits"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        # Reset hourly counters if hour has passed
        if (current_time - self.hour_start_time).total_seconds() >= 3600:
            self.signals_generated_this_hour = 0
            self.strategy_signals_this_hour = 0
            self.hour_start_time = current_time
        
        # Check global hourly limit
        if self.signals_generated_this_hour >= self.max_signals_per_hour:
            logger.debug(f"⚠️ Hourly signal limit reached: {self.signals_generated_this_hour}/{self.max_signals_per_hour}")
            return False
        
        # Check strategy-specific hourly limit
        if self.strategy_signals_this_hour >= self.max_signals_per_strategy:
            logger.debug(f"⚠️ Strategy signal limit reached: {self.strategy_signals_this_hour}/{self.max_signals_per_strategy}")
            return False
        
        return True
    
    def _check_capital_affordability(self, symbol: str, quantity: int, price: float, available_capital: float) -> bool:
        """Check if signal is affordable with available capital - CRITICAL FIX for 1,237 failures"""
        required_capital = price * quantity
        
        if required_capital > available_capital:
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} needs ₹{required_capital:,.0f} > available ₹{available_capital:,.0f}")
            return False
        
        # Also check if it's more than 80% of available capital (risk management)
        if required_capital > (available_capital * 0.8):
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} uses {required_capital/available_capital:.1%} of capital (>80% limit)")
            return False
        
        return True
    
    def _increment_signal_counters(self):
        """Increment signal counters when a signal is generated"""
        self.signals_generated_this_hour += 1
        self.strategy_signals_this_hour += 1
    
    # ========================================
    # CRITICAL: POSITION MANAGEMENT SYSTEM
    # ========================================
    
    def has_existing_position(self, symbol: str) -> bool:
        """Check if strategy already has active position in symbol with phantom cleanup"""
        if symbol in self.active_positions:
            # Check for phantom positions (older than 30 minutes)
            position_data = self.active_positions[symbol]
            if isinstance(position_data, dict):
                timestamp = position_data.get('timestamp', 0)
                current_time = time_module.time()
                age_minutes = (current_time - timestamp) / 60
                
                if age_minutes > 30:  # 30 minutes
                    logger.warning(f"🧹 CLEARING PHANTOM POSITION: {symbol} (age: {age_minutes:.1f} min)")
                    del self.active_positions[symbol]
                    return False
            
            logger.info(f"🚫 {self.strategy_name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
            return True
        return False
    
    async def manage_existing_positions(self, market_data: Dict):
        """Manage all existing positions with trailing stops and exit logic"""
        try:
            positions_to_exit = []
            
            for symbol, position in self.active_positions.items():
                if symbol not in market_data:
                    continue
                    
                current_price = market_data[symbol].get('ltp', 0)
                if current_price == 0:
                    continue
                
                # Check if position should be exited
                exit_decision = await self.should_exit_position(symbol, current_price, position)
                
                if exit_decision['should_exit']:
                    positions_to_exit.append({
                        'symbol': symbol,
                        'reason': exit_decision['reason'],
                        'current_price': current_price,
                        'position': position
                    })
                else:
                    # Update trailing stop if position is profitable
                    await self.update_trailing_stop(symbol, current_price, position)
                    
            # Execute position exits
            for exit_data in positions_to_exit:
                await self.exit_position(exit_data['symbol'], exit_data['current_price'], exit_data['reason'])
                
        except Exception as e:
            logger.error(f"Error managing existing positions: {e}")
    
    async def should_exit_position(self, symbol: str, current_price: float, position: Dict) -> Dict:
        """Determine if position should be exited based on trailing stops, targets, time"""
        try:
            entry_price = position.get('entry_price', 0)
            action = position.get('action', 'BUY')
            stop_loss = position.get('stop_loss', 0)
            target = position.get('target', 0)
            
            # CRITICAL FIX: Handle None values for stop_loss and target
            if stop_loss is None:
                stop_loss = 0
            if target is None:
                target = 0
            
            # Check stop loss (only if not zero)
            if stop_loss > 0:
                if action == 'BUY' and current_price <= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
                elif action == 'SELL' and current_price >= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
            
            # Check target (only if not zero)
            if target > 0:
                if action == 'BUY' and current_price >= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
                elif action == 'SELL' and current_price <= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
            
            # Check trailing stop
            if symbol in self.trailing_stops:
                trailing_stop = self.trailing_stops[symbol]['stop_price']
                if action == 'BUY' and current_price <= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
                elif action == 'SELL' and current_price >= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
            
            # Check position age (auto-close old positions)
            entry_time = self.position_entry_times.get(symbol)
            if entry_time:
                age_hours = (datetime.now() - entry_time).total_seconds() / 3600
                if age_hours > self.max_position_age_hours:
                    return {'should_exit': True, 'reason': 'POSITION_EXPIRED'}
            
            return {'should_exit': False, 'reason': 'HOLD'}
            
        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")
            return {'should_exit': False, 'reason': 'ERROR'}
    
    async def update_trailing_stop(self, symbol: str, current_price: float, position: Dict):
        """Update trailing stop for profitable positions"""
        try:
            action = position.get('action', 'BUY')
            entry_price = position.get('entry_price', 0)
            
            # Calculate profit percentage
            if action == 'BUY':
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Only set trailing stop if position is profitable
            if profit_pct > self.profit_lock_percentage:
                
                # Calculate trailing stop price
                if action == 'BUY':
                    trailing_stop_price = current_price * (1 - self.trailing_stop_percentage / 100)
                else:
                    trailing_stop_price = current_price * (1 + self.trailing_stop_percentage / 100)
                
                # Update trailing stop if it's better than current
                if symbol not in self.trailing_stops:
                    self.trailing_stops[symbol] = {
                        'stop_price': trailing_stop_price,
                        'last_update': datetime.now(),
                        'highest_profit': profit_pct
                    }
                    logger.info(f"🎯 {self.name}: Set trailing stop for {symbol} at ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                else:
                    current_trailing = self.trailing_stops[symbol]
                    
                    # Update if new trailing stop is better
                    if ((action == 'BUY' and trailing_stop_price > current_trailing['stop_price']) or
                        (action == 'SELL' and trailing_stop_price < current_trailing['stop_price'])):
                        
                        self.trailing_stops[symbol].update({
                            'stop_price': trailing_stop_price,
                            'last_update': datetime.now(),
                            'highest_profit': max(profit_pct, current_trailing['highest_profit'])
                        })
                        logger.info(f"🎯 {self.name}: Updated trailing stop for {symbol} to ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                        
        except Exception as e:
            logger.error(f"Error updating trailing stop for {symbol}: {e}")
    
    async def exit_position(self, symbol: str, exit_price: float, reason: str):
        """Exit position and clean up tracking data"""
        try:
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                entry_price = position.get('entry_price', 0)
                action = position.get('action', 'BUY')
                
                # Calculate realized P&L
                if action == 'BUY':
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                
                # Log position exit
                logger.info(f"🚪 {self.name}: EXITING {symbol} at ₹{exit_price:.2f} | "
                           f"Entry: ₹{entry_price:.2f} | P&L: {pnl_pct:.2f}% | Reason: {reason}")
                
                # Clean up position tracking
                del self.active_positions[symbol]
                if symbol in self.position_metadata:
                    del self.position_metadata[symbol]
                if symbol in self.trailing_stops:
                    del self.trailing_stops[symbol]
                if symbol in self.position_entry_times:
                    del self.position_entry_times[symbol]
                
                # Create exit signal for execution
                exit_signal = {
                    'symbol': symbol,
                    'action': 'SELL' if action == 'BUY' else 'BUY',  # Opposite action to close
                    'entry_price': exit_price,
                    'stop_loss': 0,  # No stop loss for exit signal
                    'target': exit_price,
                    'confidence': 10.0,  # High confidence for exits
                    'quantity': position.get('quantity', 1),
                    'strategy': self.name,
                    'signal_type': 'POSITION_EXIT',
                    'exit_reason': reason,
                    'original_entry_price': entry_price,
                    'realized_pnl_pct': pnl_pct,
                    'metadata': {
                        'position_exit': True,
                        'exit_reason': reason,
                        'holding_time_hours': (datetime.now() - self.position_entry_times.get(symbol, datetime.now())).total_seconds() / 3600
                    }
                }
                
                # Store exit signal for orchestrator collection
                self.current_positions[f"{symbol}_EXIT"] = exit_signal
                
        except Exception as e:
            logger.error(f"Error exiting position for {symbol}: {e}")
    
    def record_position_entry(self, symbol: str, signal: Dict):
        """Record position entry for tracking and management"""
        try:
            # Store active position data
            self.active_positions[symbol] = {
                'entry_price': signal.get('entry_price', 0),
                'action': signal.get('action', 'BUY'),
                'stop_loss': signal.get('stop_loss', 0),
                'target': signal.get('target', 0),
                'confidence': signal.get('confidence', 0),
                'quantity': signal.get('quantity', 1),
                'strategy': self.name,
                'entry_time': datetime.now()
            }
            
            # Store entry time for age tracking
            self.position_entry_times[symbol] = datetime.now()
            
            # Store strategy-specific metadata
            self.position_metadata[symbol] = signal.get('metadata', {})
            
            logger.info(f"📈 {self.name}: POSITION ENTERED {symbol} {signal.get('action')} at ₹{signal.get('entry_price', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Error recording position entry for {symbol}: {e}")
    
    def _is_symbol_scalping_cooldown_passed(self, symbol: str, cooldown_seconds: int = 30) -> bool:
        """Check if symbol-specific SCALPING cooldown has passed"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= cooldown_seconds
    
    def _update_symbol_cooldown(self, symbol: str):
        """Update symbol-specific cooldown timestamp"""
        if not hasattr(self, 'symbol_cooldowns'):
            self.symbol_cooldowns = {}
        self.symbol_cooldowns[symbol] = datetime.now()
        
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours - FIXED: Now uses IST timezone"""
        try:
            # Get current time in IST (same as orchestrator)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # NSE trading hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                logger.info(f"🚫 SAFETY: Trading blocked on weekend. Current day: {now.strftime('%A')}")
                return False
            
            is_trading_time = market_open <= current_time <= market_close
            
            if not is_trading_time:
                logger.info(f"🚫 SAFETY: Trading blocked outside market hours. Current IST time: {current_time} "
                           f"(Market: {market_open} - {market_close})")
            else:
                logger.info(f"✅ TRADING HOURS: Market open. Current IST time: {current_time}")
            
            return is_trading_time
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFETY: If timezone check fails, default to False (safer)
            return False
    
    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """Calculate True Range - the foundation of proper ATR calculation"""
        try:
            if prev_close <= 0:
                return high - low  # First calculation or invalid previous close
            
            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            range1 = high - low
            range2 = abs(high - prev_close)
            range3 = abs(low - prev_close)
            
            return max(range1, range2, range3)
            
        except Exception as e:
            logger.error(f"Error calculating True Range: {e}")
            return high - low if high > low else 0.01  # Fallback
    
    def calculate_atr(self, symbol: str, current_high: float, current_low: float, 
                     current_close: float, period: int = 14) -> float:
        """Calculate Average True Range - PROPER IMPLEMENTATION"""
        try:
            # Store current data
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            # Add current data point
            data_point = {
                'high': current_high,
                'low': current_low,
                'close': current_close,
                'timestamp': datetime.now()
            }
            
            self.historical_data[symbol].append(data_point)
            
            # Trim history if needed
            if len(self.historical_data[symbol]) > self.max_history:
                self.historical_data[symbol].pop(0)
            
            # Calculate ATR
            history = self.historical_data[symbol]
            if len(history) < 2:
                # Not enough data for ATR - use simple range
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # Calculate True Range for recent periods
            true_ranges = []
            for i in range(1, len(history)):
                prev_close = history[i-1]['close']
                current_data = history[i]
                tr = self.calculate_true_range(
                    current_data['high'], 
                    current_data['low'], 
                    prev_close
                )
                true_ranges.append(tr)
            
            # Calculate ATR as average of True Ranges
            if len(true_ranges) == 0:
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # Use available data or period, whichever is smaller
            atr_period = min(period, len(true_ranges))
            recent_trs = true_ranges[-atr_period:]
            
            atr = np.mean(recent_trs)
            
            # Ensure minimum ATR (0.1% of price) and reasonable maximum (10% of price)
            min_atr = current_close * 0.001
            max_atr = current_close * 0.1
            
            return max(min_atr, min(atr, max_atr))
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {e}")
            # Fallback to simple range calculation
            return current_high - current_low if current_high > current_low else current_close * 0.01
    
    def calculate_dynamic_stop_loss(self, entry_price: float, atr: float, action: str, 
                                   multiplier: float = 2.0, min_percent: float = 0.5, 
                                   max_percent: float = 5.0) -> float:
        """Calculate dynamic stop loss based on ATR with SCALPING-OPTIMIZED bounds"""
        try:
            # Calculate ATR-based stop loss distance
            atr_distance = atr * multiplier
            
            # Convert to percentage
            atr_percent = (atr_distance / entry_price) * 100
            
            # Apply SCALPING-OPTIMIZED bounds (tighter than original)
            bounded_percent = max(min_percent, min(atr_percent, max_percent))
            bounded_distance = (bounded_percent / 100) * entry_price
            
            # Calculate stop loss based on action
            if action.upper() == 'BUY':
                stop_loss = entry_price - bounded_distance
            else:  # SELL
                stop_loss = entry_price + bounded_distance
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            # Fallback to percentage-based stop loss
            fallback_percent = 0.5  # 0.5% fallback for scalping
            if action.upper() == 'BUY':
                return entry_price * (1 - fallback_percent / 100)
            else:
                return entry_price * (1 + fallback_percent / 100)
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                risk_reward_ratio: float = 1.5) -> float:
        """Calculate dynamic target with SCALPING-OPTIMIZED risk/reward ratio"""
        try:
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            
            # Calculate reward distance
            reward_distance = risk_distance * risk_reward_ratio
            
            # Calculate target based on entry vs stop loss relationship
            if stop_loss < entry_price:  # BUY trade
                target = entry_price + reward_distance
            else:  # SELL trade
                target = entry_price - reward_distance
            
            return round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target: {e}")
            # DYNAMIC fallback percentage target based on volatility
            try:
                # Use simple percentage-based target without symbol dependency
                target_percent = 0.015  # 1.5% conservative fallback
            except:
                target_percent = 0.015  # 1.5% conservative fallback
                
            if stop_loss < entry_price:  # BUY trade
                return entry_price * (1 + target_percent)  # Dynamic target for scalping
            else:  # SELL trade
                return entry_price * (1 - target_percent)  # Dynamic target for scalping
    
    def validate_signal_levels(self, entry_price: float, stop_loss: float, 
                              target: float, action: str) -> bool:
        """Validate that signal levels make logical sense"""
        try:
            if action.upper() == 'BUY':
                # For BUY: stop_loss < entry_price < target
                if not (stop_loss < entry_price < target):
                    logger.warning(f"Invalid BUY signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
            else:  # SELL
                # For SELL: target < entry_price < stop_loss
                if not (target < entry_price < stop_loss):
                    logger.warning(f"Invalid SELL signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
            
            # Check risk/reward ratio is reasonable (0.5:1 to 5:1)
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            
            if risk <= 0:
                logger.warning(f"Zero or negative risk: {risk}")
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 0.5 or risk_reward_ratio > 5.0:
                logger.warning(f"Unreasonable risk/reward ratio: {risk_reward_ratio}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal levels: {e}")
            return False
    
    async def create_standard_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, 
                              metadata: Dict) -> Optional[Dict]:
        """Create standardized signal format - SUPPORTS EQUITY, FUTURES & OPTIONS"""
        try:
            # ========================================
            # CRITICAL: POSITION DEDUPLICATION CHECK
            # ========================================
            if self.has_existing_position(symbol):
                logger.info(f"🚫 {self.name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
                return None
            
            # ========================================
            # CRITICAL: CONFIDENCE FILTERING
            # ========================================
            if confidence < 9.0:
                logger.info(f"🗑️ {self.name}: LOW CONFIDENCE SIGNAL SCRAPPED for {symbol} - Confidence: {confidence:.1f}/10")
                return None
            
            # 🎯 INTELLIGENT SIGNAL TYPE SELECTION based on market conditions and symbol
            signal_type = self._determine_optimal_signal_type(symbol, entry_price, confidence, metadata)
            
            if signal_type == 'OPTIONS':
                # Convert to options signal
                return await self._create_options_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            elif signal_type == 'FUTURES':
                # Create futures signal (if available)
                return self._create_futures_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            else:
                # Create equity signal (default)
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
                
        except Exception as e:
            logger.error(f"Error creating signal for {symbol}: {e}")
            return None
    
    def _determine_optimal_signal_type(self, symbol: str, entry_price: float, confidence: float, metadata: Dict) -> str:
        """Determine the best signal type based on market conditions and F&O availability"""
        try:
            # 🚨 CRITICAL: Check F&O availability first
            from config.truedata_symbols import is_fo_enabled, should_use_equity_only
            
            # Force equity for known cash-only stocks
            if should_use_equity_only(symbol):
                logger.info(f"🎯 CASH-ONLY STOCK: {symbol} → EQUITY (no F&O available)")
                return 'EQUITY'
            
            # Check if F&O is available for this symbol
            if not is_fo_enabled(symbol):
                logger.info(f"🎯 NO F&O AVAILABLE: {symbol} → EQUITY (no options trading)")
                return 'EQUITY'
            
            # Factors for signal type selection (F&O enabled symbols)
            is_index = symbol.endswith('-I') or symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
            is_high_confidence = confidence >= 0.8
            is_scalping = metadata.get('risk_type', '').startswith('SCALPING')
            volatility_score = metadata.get('volume_score', 0)
            
            # 🎯 DECISION LOGIC FOR F&O ENABLED SYMBOLS (BALANCED APPROACH):
            # 1. Index symbols → OPTIONS (standard)
            # 2. Very high confidence (0.85+) + Scalping → OPTIONS (leverage)
            # 3. High volatility stocks + Very high confidence → OPTIONS
            # 4. Medium-High confidence (0.65-0.84) → EQUITY (balanced approach)
            # 5. Low confidence → EQUITY (safest)
            
            if is_index:
                logger.info(f"🎯 INDEX SIGNAL: {symbol} → OPTIONS (F&O enabled)")
                return 'OPTIONS'
            elif is_high_confidence and confidence >= 0.85 and is_scalping:  # Only very high confidence scalping
                logger.info(f"🎯 VERY HIGH CONFIDENCE SCALPING: {symbol} → OPTIONS (F&O enabled)")
                return 'OPTIONS'
            elif volatility_score >= 0.9 and confidence >= 0.85:  # Higher thresholds for options
                logger.info(f"🎯 VERY HIGH VOLATILITY: {symbol} → OPTIONS (F&O enabled)")
                return 'OPTIONS'
            elif confidence >= 0.65:
                logger.info(f"🎯 MEDIUM+ CONFIDENCE: {symbol} → EQUITY (balanced trading)")
                return 'EQUITY'
            else:
                logger.info(f"🎯 LOW CONFIDENCE: {symbol} → EQUITY (safest)")
                return 'EQUITY'
                
        except Exception as e:
            logger.error(f"Error determining signal type: {e}")
            return 'EQUITY'  # Safest fallback
    
    async def _create_options_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Dict:
        """Create standardized signal format for options"""
        try:
            # 🎯 CRITICAL FIX: Convert to options symbol and force BUY action
            options_symbol, option_type = await self._convert_to_options_symbol(symbol, entry_price, action)
            
            # 🚨 CRITICAL: Check if signal was rejected (e.g., MIDCPNIFTY, SENSEX)
            if options_symbol is None or option_type == 'REJECTED':
                logger.warning(f"⚠️ OPTIONS SIGNAL REJECTED: {symbol} - cannot be traded")
                return None
            
            # 🎯 FALLBACK: If options not available, create equity signal instead
            if option_type == 'EQUITY':
                logger.info(f"🔄 FALLBACK TO EQUITY: Creating equity signal for {options_symbol}")
                return self._create_equity_signal(options_symbol, action, entry_price, stop_loss, target, confidence, metadata)
            
            final_action = 'BUY' # Force all options signals to be BUY
            
            # 🔍 CRITICAL DEBUG: Log the complete symbol creation process
            logger.info(f"🔍 SYMBOL CREATION DEBUG:")
            logger.info(f"   Original: {symbol} → Options: {options_symbol}")
            logger.info(f"   Type: {option_type}, Action: {final_action}")
            logger.info(f"   Entry Price: ₹{entry_price} (underlying)")
            
            # 🎯 CRITICAL FIX: Get actual options premium from TrueData instead of stock price
            options_entry_price = self._get_options_premium(options_symbol, entry_price, option_type)
            
            # 🔍 DEBUG: Log premium fetching
            logger.info(f"   Options Premium: ₹{options_entry_price} (vs underlying ₹{entry_price})")
            
            # 🎯 CRITICAL FIX: Calculate correct stop_loss and target for options
            options_stop_loss, options_target = self._calculate_options_levels(
                options_entry_price, stop_loss, target, option_type, action, symbol
            )
            
            # 🎯 ALLOW 0.0 signals to pass to orchestrator for LTP fixing
            # Only validate if we have a real entry price (orchestrator will fix 0.0 prices)
            if options_entry_price > 0 and not self.validate_signal_levels(options_entry_price, options_stop_loss, options_target, 'BUY'):
                logger.warning(f"Invalid options signal levels: Entry={options_entry_price}, SL={options_stop_loss}, Target={options_target}")
                return None
            elif options_entry_price == 0:
                logger.info(f"🔄 PASSING 0.0 signal to orchestrator for LTP validation: {options_symbol}")
            
            # 🎯 CRITICAL FIX: Always BUY options (no selling due to margin requirements)
            final_action = 'BUY'  # Force all options signals to be BUY
            
            # Calculate risk metrics using OPTIONS pricing (handle 0.0 entry price)
            risk_amount = abs(options_entry_price - options_stop_loss)
            reward_amount = abs(options_target - options_entry_price)
            risk_percent = (risk_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            reward_percent = (reward_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # CRITICAL FIX: Generate unique signal_id for tracking
            signal_id = f"{self.name}_{options_symbol}_{int(datetime.now().timestamp())}"
            
            return {
                # Core signal fields (consistent naming)
                'signal_id': signal_id,
                'symbol': options_symbol,  # 🎯 FIXED: Use options symbol instead of underlying
                'underlying_symbol': symbol,  # Keep original for reference
                'option_type': option_type,  # CE or PE
                'action': final_action.upper(),  # Always BUY for options (no selling due to margin)
                'quantity': self._get_capital_constrained_quantity(options_symbol, symbol, options_entry_price),  # 🎯 CAPITAL-AWARE: Limit lots based on capital
                'entry_price': self._round_to_tick_size(options_entry_price),  # 🎯 FIXED: Use tick size rounding
                'stop_loss': self._round_to_tick_size(options_stop_loss),      # 🎯 FIXED: Tick size rounding
                'target': self._round_to_tick_size(options_target),            # 🎯 FIXED: Tick size rounding
                'strategy': self.name,  # Use 'strategy' for compatibility
                'strategy_name': self.name,  # Also include strategy_name for new components
                'confidence': round(min(confidence, 0.9), 2),
                'quality_score': round(min(confidence, 0.9), 2),  # Map confidence to quality_score
                
                # Risk metrics
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                
                # Enhanced metadata
                'metadata': {
                    **metadata,
                    'signal_validation': 'PASSED',
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.name,
                    'signal_source': 'strategy_engine',
                    'underlying_price': round(entry_price, 2),  # Keep original stock price for reference
                    'options_conversion': 'PREMIUM_BASED'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating standard signal: {e}")
            return None
    
    def _create_equity_signal(self, symbol: str, action: str, entry_price: float, 
                             stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """Create equity signal with standard parameters"""
        try:
            # Validate signal levels
            if not self.validate_signal_levels(entry_price, stop_loss, target, action):
                logger.warning(f"Invalid equity signal levels: {symbol}")
                return None
            
            # Calculate risk metrics
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(target - entry_price)
            risk_percent = (risk_amount / entry_price) * 100
            reward_percent = (reward_amount / entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Check minimum risk-reward ratio (DYNAMIC based on volatility)
            min_risk_reward_ratio = self._get_dynamic_min_risk_reward_ratio(symbol, entry_price)
            if risk_reward_ratio < min_risk_reward_ratio:
                logger.warning(f"Equity signal below {min_risk_reward_ratio}:1 ratio: {symbol} ({risk_reward_ratio:.2f})")
                return None
            
            signal = {
                'signal_id': f"{self.name}_{symbol}_{int(time_module.time())}",
                'symbol': symbol,
                'action': action.upper(),
                'quantity': self._get_capital_constrained_quantity(symbol, symbol, entry_price),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'strategy': self.name,
                'strategy_name': self.__class__.__name__,
                'confidence': confidence,
                'quality_score': confidence,
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                'metadata': {
                    **metadata,
                    'signal_type': 'EQUITY',
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.__class__.__name__,
                    'signal_source': 'strategy_engine'
                },
                'generated_at': datetime.now().isoformat()
            }
            
            # CRITICAL: Record position entry for management
            self.record_position_entry(symbol, signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating equity signal: {e}")
            return None
    
    def _create_futures_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """Create futures signal (placeholder for now)"""
        try:
            # For now, fallback to equity signal
            # TODO: Implement proper futures signal creation with correct expiry, etc.
            logger.info(f"📊 FUTURES signal requested for {symbol} - using equity for now")
            return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            
        except Exception as e:
            logger.error(f"Error creating futures signal: {e}")
            return None
    
    def _get_real_market_price(self, symbol: str) -> Optional[float]:
        """Get real market price from TrueData cache to ensure accurate strike calculation"""
        try:
            from data.truedata_client import live_market_data
            if live_market_data and symbol in live_market_data:
                stock_price = live_market_data[symbol].get('ltp', 0)
                logger.debug(f"📊 Real market price for {symbol}: ₹{stock_price}")
                return float(stock_price) if stock_price > 0 else None
            else:
                logger.warning(f"⚠️ No real market data available for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error getting real market price for {symbol}: {e}")
            return None

    async def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
        """Convert equity signal to options symbol with BUY-only approach - FIXED SYMBOL FORMAT"""
        
        try:
            # 🚨 CRITICAL FIX: Get REAL market price instead of using entry_price which might be wrong
            real_market_price = self._get_real_market_price(underlying_symbol)
            if real_market_price and real_market_price > 0:
                actual_price = real_market_price
                logger.info(f"🔍 PRICE CORRECTION: Using real market price ₹{actual_price:.2f} instead of ₹{current_price:.2f}")
            else:
                actual_price = current_price
                logger.warning(f"⚠️ Using passed price ₹{actual_price:.2f} (real price unavailable)")
            
            # 🎯 CRITICAL FIX: Convert to Zerodha's official symbol name FIRST
            from config.truedata_symbols import get_zerodha_symbol
            zerodha_underlying = get_zerodha_symbol(underlying_symbol)
            
            # 🎯 CRITICAL FIX: Only BUY signals for options (no selling due to margin requirements)
            # 🔧 IMPORTANT: Only use indices with confirmed options contracts on Zerodha
            if zerodha_underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:  # REMOVED MIDCPNIFTY - no options
                # Index options - use volume-based strike selection for liquidity
                expiry = await self._get_next_expiry()
                if not expiry:
                    logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - REJECTING SIGNAL")
                    return None, 'REJECTED'
                strike = self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                
                # 🔧 CRITICAL FIX: Use Zerodha's EXACT format from API response
                # Zerodha format: NIFTY07AUG2524650CE (not NIFTY25AUG24650CE)
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                
                logger.info(f"🎯 INDEX SIGNAL: {underlying_symbol} → OPTIONS (F&O enabled)")
                logger.info(f"   Generated: {options_symbol}")
                return options_symbol, option_type
            elif zerodha_underlying in ['MIDCPNIFTY', 'SENSEX']:
                # 🚨 CRITICAL: These indices cannot be traded as equity - SKIP SIGNAL
                logger.warning(f"⚠️ {zerodha_underlying} cannot be traded as equity - SIGNAL REJECTED")
                return None, 'REJECTED'
            else:
                # Stock options - convert equity to options using ZERODHA NAME
                # 🎯 USER REQUIREMENT: Volume-based strike selection for liquidity
                expiry = await self._get_next_expiry()
                if not expiry:
                    logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - REJECTING SIGNAL")
                    return None, 'REJECTED'
                strike = self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                
                # 🔧 CRITICAL FIX: Use Zerodha's exact symbol format for stocks too
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                
                # 🚨 CRITICAL FIX: Validate if options symbol exists in Zerodha before using
                if self._validate_options_symbol_exists(options_symbol):
                    logger.info(f"🎯 ZERODHA OPTIONS SYMBOL: {underlying_symbol} → {options_symbol}")
                    logger.info(f"   Mapping: {underlying_symbol} → {zerodha_underlying}")
                    logger.info(f"   Strike: {strike}, Expiry: {expiry}, Type: {option_type}")
                    logger.info(f"   Used Price: ₹{actual_price:.2f} (real market price)")
                    
                    return options_symbol, option_type
                else:
                    # 🎯 FALLBACK: Options not available, trade equity instead
                    logger.warning(f"⚠️ OPTIONS NOT AVAILABLE: {options_symbol} doesn't exist in Zerodha NFO")
                    logger.info(f"🔄 FALLBACK: Trading {zerodha_underlying} as EQUITY instead")
                    
                    return zerodha_underlying, 'EQUITY'
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            return underlying_symbol, 'CE'
    
    def _validate_options_symbol_exists(self, options_symbol: str) -> bool:
        """Validate if options symbol exists in Zerodha NFO instruments"""
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Zerodha client not available for options validation")
                return False  # Conservative: assume options don't exist
            
            # Use the Zerodha client's validation method
            is_valid = orchestrator.zerodha_client.validate_options_symbol(options_symbol)
            
            if is_valid:
                logger.info(f"✅ OPTIONS VALIDATED: {options_symbol} exists in Zerodha NFO")
                return True
            else:
                logger.warning(f"❌ OPTIONS NOT FOUND: {options_symbol} doesn't exist in Zerodha NFO")
                return False
                
        except Exception as e:
            logger.error(f"Error validating options symbol {options_symbol}: {e}")
            return False  # Conservative: assume options don't exist
    
    def _get_atm_strike(self, symbol: str, price: float) -> int:
        """Get ATM strike for index options - FIXED for Zerodha's actual intervals"""
        # 🚨 CRITICAL FIX: Based on user feedback "for indices only in 100"
        # All major indices use 100-point intervals in Zerodha
        
        if symbol == 'NIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 NIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'BANKNIFTY':
            strike = round(price / 100) * 100  # Already correct
            logger.info(f"🎯 BANKNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'FINNIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 FINNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        else:
            # Fallback for other indices
            strike = round(price / 100) * 100
            logger.info(f"🎯 {symbol} STRIKE: ₹{price} → {strike} (100-point interval fallback)")
            return int(strike)
    
    def _get_atm_strike_for_stock(self, current_price: float) -> int:
        """Get ATM strike for stock options - FIXED to use Zerodha's actual intervals"""
        try:
            # 🔍 DEBUG: Log current price and strike calculation
            logger.info(f"🔍 DEBUG: Calculating ATM strike for stock price: ₹{current_price}")
            
            # 🚨 CRITICAL FIX: Zerodha only offers strikes in multiples of 50 for most stocks
            # Based on user feedback: "for option price if we see only the prices which are in multiple of 50"
            interval = 50  # Fixed interval for all stocks to match Zerodha availability
            
            # Round to nearest 50
            atm_strike = round(current_price / interval) * interval
            
            logger.info(f"🎯 STOCK STRIKE CALCULATION (FIXED):")
            logger.info(f"   Current Price: ₹{current_price}")
            logger.info(f"   Strike Interval: {interval} (Zerodha standard)")
            logger.info(f"   ATM Strike: {int(atm_strike)}")
            logger.info(f"   Available: {int(atm_strike-50)}, {int(atm_strike)}, {int(atm_strike+50)}")
            
            return int(atm_strike)
            
        except Exception as e:
            logger.error(f"Error calculating ATM strike for stock: {e}")
            # Fallback to nearest 50 (Zerodha standard)
            fallback_strike = round(current_price / 50) * 50
            logger.warning(f"⚠️ FALLBACK STRIKE: {int(fallback_strike)} (rounded to nearest 50)")
            return int(fallback_strike)
      
    async def _get_next_expiry(self) -> str:
        """DYNAMIC EXPIRY SELECTION: Get optimal expiry based on strategy requirements"""
        # 🔍 DEBUG: Add comprehensive logging for expiry date debugging
        logger.info(f"🔍 DEBUG: Getting next expiry date...")
        
        # Try to get real expiry dates from Zerodha first
        available_expiries = await self._get_available_expiries_from_zerodha()
        
        if available_expiries:
            logger.info(f"✅ Found {len(available_expiries)} expiry dates from Zerodha API")
            for i, exp in enumerate(available_expiries[:3]):  # Log first 3
                logger.info(f"   {i+1}. {exp['formatted']} ({exp['date']})")
            
            # Use the next expiry (not nearest to avoid expiry day volatility)
            optimal_expiry = await self._get_optimal_expiry_for_strategy("next_weekly")  # Changed from default to "next_weekly"
            logger.info(f"🎯 SELECTED EXPIRY: {optimal_expiry}")
            return optimal_expiry
        else:
            logger.warning("⚠️ No expiry dates from Zerodha API - using calculated fallback")
            # Use simple fallback calculation for next Thursday
            from datetime import datetime, timedelta
            today = datetime.now().date()
            days_ahead = 3 - today.weekday()  # Thursday is 3 (Monday=0)
            if days_ahead <= 0:  # If today is Thursday or later, get next Thursday
                days_ahead += 7
            next_thursday = today + timedelta(days=days_ahead)
            
            # Format as DDMMMYY for Zerodha
            fallback_expiry = next_thursday.strftime("%d%b%y").upper()
            logger.info(f"🔄 FALLBACK EXPIRY: {fallback_expiry} (calculated next Thursday)")
            return fallback_expiry
    
    async def _get_optimal_expiry_for_strategy(self, preference: str = "nearest_weekly") -> str:
        """
        Get optimal expiry based on strategy requirements - FIXED ZERODHA FORMAT
        
        Args:
            preference: "nearest_weekly", "nearest_monthly", "next_weekly", "max_time_decay"
        """
        available_expiries = await self._get_available_expiries_from_zerodha()
        
        if not available_expiries:
            # 🚨 NO FALLBACK: Return None if no real expiries from Zerodha API
            logger.error("❌ No expiries from Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        today = datetime.now().date()
        
        # 🚨 CRITICAL FIX: Use next day as cutoff to avoid expired/expiring options
        # Today is July 31, so July 25 expiry has already passed
        cutoff_date = today + timedelta(days=1)  # Use tomorrow as cutoff for safety
        
        # Filter future expiries only
        future_expiries = [exp for exp in available_expiries if exp['date'] >= cutoff_date]
        
        if not future_expiries:
            # 🚨 NO FALLBACK: Return None if no future expiries found
            logger.error("❌ No future expiries found in Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        # Sort by date
        future_expiries.sort(key=lambda x: x['date'])
        
        if preference == "nearest_weekly":
            # Get the nearest expiry (usually weekly)
            nearest = future_expiries[0]
        elif preference == "nearest_monthly":
            # Try to find monthly expiry (usually last Thursday of month)
            monthly_expiries = [exp for exp in future_expiries if exp.get('is_monthly', False)]
            nearest = monthly_expiries[0] if monthly_expiries else future_expiries[0]
        elif preference == "next_weekly":
            # 🎯 USER REQUIREMENT: Next expiry minimum (not nearest)
            # Skip the nearest expiry and use the next one for better liquidity
            if len(future_expiries) > 1:
                nearest = future_expiries[1]  # Second expiry (next minimum)
                logger.info(f"✅ Selected NEXT expiry (not nearest) for liquidity: {nearest['formatted']}")
            else:
                nearest = future_expiries[0]  # Fallback if only one available
                logger.warning(f"⚠️ Only one expiry available, using: {nearest['formatted']}")
        else:  # max_time_decay
            # Choose expiry with optimal time decay (not too near, not too far)
            optimal_days = 7  # 1 week optimal
            best_expiry = future_expiries[0]
            best_diff = abs((best_expiry['date'] - today).days - optimal_days)
            
            for expiry in future_expiries:
                days_diff = abs((expiry['date'] - today).days - optimal_days)
                if days_diff < best_diff:
                    best_diff = days_diff
                    best_expiry = expiry
            nearest = best_expiry
        
        # 🔧 CRITICAL FIX: Convert to Zerodha format (25JUL instead of 31JUL25)
        exp_date = nearest['date']
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 07AUG25 (DD + MMM + YY), NOT 25AUG
        zerodha_expiry = f"{exp_date.day:02d}{month_names[exp_date.month - 1]}{str(exp_date.year)[-2:]}"
        
        logger.info(f"🎯 OPTIMAL EXPIRY: {zerodha_expiry} (from {nearest['formatted']})")
        logger.info(f"   Date: {exp_date}, Days ahead: {(exp_date - today).days}")
        
        return zerodha_expiry
    
    async def _get_available_expiries_from_zerodha(self) -> List[Dict]:
        """
        Fetch available expiry dates from Zerodha instruments API
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.error("❌ Zerodha client not available for expiry lookup - NO FALLBACK")
                return []
            
            # Use the new async method - we'll need to handle this synchronously
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Try to get expiries for common underlying symbols we trade
            all_expiries = set()
            
            # Get expiries for indices and stocks we commonly trade
            common_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'POWERGRID', 'RELIANCE', 'TCS']
            
            for symbol in common_symbols:
                try:
                    # 🎯 CRITICAL FIX: Handle both sync and async contexts properly
                    if loop.is_running():
                        # We're in async context - use asyncio.create_task() instead
                        import asyncio
                        try:
                            # Create a new task to avoid "cannot be called from a running event loop"
                            task = asyncio.create_task(
                                orchestrator.zerodha_client.get_available_expiries_for_symbol(symbol)
                            )
                            # Get the result - this works in async context
                            expiries = await task
                            
                            if expiries:
                                logger.info(f"📅 Using expiries from {symbol}: {len(expiries)} found")
                                return expiries
                        except Exception as async_err:
                            logger.warning(f"⚠️ Async expiry fetch failed for {symbol}: {async_err}")
                            continue
                    else:
                        # Run the async method
                        expiries = loop.run_until_complete(
                            orchestrator.zerodha_client.get_available_expiries_for_symbol(symbol)
                        )
                        
                        if expiries:
                            # Use expiries from the first successful symbol lookup
                            logger.info(f"📅 Using expiries from {symbol}: {len(expiries)} found")
                            return expiries
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get expiries for {symbol}: {e}")
                    continue
            
            # If no expiries found from API, REJECT signal
            logger.error("❌ No expiries found from Zerodha API - NO FALLBACK")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error fetching available expiries: {e}")
            return []
    
    def _get_fallback_expiries(self) -> List[Dict]:
        """Generate realistic weekly expiries when API is unavailable"""
        today = datetime.now().date()
        expiries = []
        
        # Add all Thursdays for next 8 weeks
        current_date = today
        for weeks_ahead in range(8):
            # Find next Thursday
            days_ahead = (3 - current_date.weekday()) % 7  # Thursday = 3
            if days_ahead == 0 and current_date == today:
                days_ahead = 7  # If today is Thursday, get next Thursday
                
            thursday = current_date + timedelta(days=days_ahead)
            
            # Format for Zerodha: 25AUG (YY + MMM)
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            formatted = f"{str(thursday.year)[-2:]}{month_names[thursday.month - 1]}"
            
            # Determine if it's monthly (last Thursday of month)
            next_week = thursday + timedelta(days=7)
            is_monthly = next_week.month != thursday.month
            
            expiries.append({
                'date': thursday,
                'formatted': formatted,
                'is_weekly': True,
                'is_monthly': is_monthly
            })
            
            current_date = thursday + timedelta(days=1)  # Move to next week
        
        logger.info(f"📅 Generated {len(expiries)} fallback expiries: {[e['formatted'] for e in expiries[:3]]}...")
        return expiries
    
    def _calculate_next_thursday_fallback(self) -> str:
        """Fallback calculation for next Thursday when API is unavailable - FIXED ZERODHA FORMAT"""
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
        if days_ahead == 0:
            days_ahead = 7  # If today is Thursday, get next Thursday
            
        next_thursday = today + timedelta(days=days_ahead)
        
        # 🚨 CRITICAL DEBUG: Log calculation details
        logger.info(f"🔍 EXPIRY CALCULATION DEBUG:")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')} (weekday: {today.weekday()})")
        logger.info(f"   Days ahead to Thursday: {days_ahead}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        
        # 🔧 CRITICAL FIX: Format for Zerodha - their format is 25JUL (not 31JUL25)
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 14AUG25 (DD + MMM + YY), NOT 14AUG (DD + MMM)
        expiry_formatted = f"{next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}"
        
        logger.info(f"📅 ZERODHA EXPIRY FORMAT: {expiry_formatted}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')}")
        logger.info(f"   OLD FORMAT would be: {next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}")
        logger.info(f"   NEW ZERODHA FORMAT: {expiry_formatted}")
        
        return expiry_formatted
    
    def _get_last_thursday_of_month(self, year: int, month: int) -> datetime:
        """Get the last Thursday of a given month - DEPRECATED: Use dynamic expiry selection"""
        import calendar
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        
        # Find the last Thursday
        last_date = datetime(year, month, last_day)
        
        # Thursday is 3, so we need to go back to find the last Thursday
        days_back = (last_date.weekday() - 3) % 7  # 3 = Thursday
        if days_back == 0 and last_date.weekday() == 3:
            # Already a Thursday
            return last_date
        else:
            # Go back to find the last Thursday
            last_thursday = last_date - timedelta(days=days_back)
            return last_thursday
    
    def _truncate_symbol_for_options(self, symbol: str) -> str:
        """Truncate symbol names for options format"""
        # Common truncations for stock options
        truncation_map = {
            'ICICIBANK': 'ICICIBANK',  # Actually, let's test with full name first
            'HDFCBANK': 'HDFCBANK',
            'RELIANCE': 'RELIANCE',
            'BHARTIARTL': 'BHARTIARTL'
        }
        return truncation_map.get(symbol, symbol)
    
    def _is_cooldown_passed(self) -> bool:
        """Check if cooldown period has passed"""
        if not self.last_signal_time:
            return True
        return (datetime.now() - self.last_signal_time).total_seconds() >= self.signal_cooldown
    
    async def send_to_trade_engine(self, signal: Dict):
        """Send signal to trade engine for execution"""
        try:
            # Get orchestrator instance and send signal to trade engine
            from src.core.orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                await orchestrator.trade_engine.process_signals([signal])
                logger.info(f"✅ Signal sent to trade engine: {signal['symbol']} {signal['action']}")
                return True
            else:
                logger.error(f"❌ Trade engine not available for signal: {signal['symbol']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending signal to trade engine: {e}")
            return False
    
    async def initialize(self):
        """Initialize the strategy - to be implemented by subclasses"""
        logger.info(f"Initializing {self.name} strategy")
        self.is_active = True
    
    async def on_market_data(self, data: Dict):
        """Handle incoming market data - to be implemented by subclasses"""
        pass
    
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 

    def _get_options_premium(self, options_symbol: str, fallback_price: float, option_type: str) -> float:
        """Get actual options premium - PRIMARY from TrueData, SECONDARY from Zerodha for validation only"""
        try:
            # 🎯 PRIMARY: Get options premium from TrueData cache (USER PREFERENCE)
            try:
                from data.truedata_client import live_market_data
                from config.options_symbol_mapping import convert_zerodha_to_truedata_options
                
                # Convert Zerodha format to TrueData format for lookup
                truedata_symbol = convert_zerodha_to_truedata_options(options_symbol)
                logger.debug(f"🔄 Format conversion: {options_symbol} -> {truedata_symbol}")
                
                if live_market_data and truedata_symbol in live_market_data:
                    options_data = live_market_data[truedata_symbol]
                    # Extract LTP (Last Traded Price) for options premium
                    premium = options_data.get('ltp', options_data.get('price', options_data.get('last_price')))
                    if premium and premium > 0:
                        logger.info(f"✅ Got options premium from TrueData: {options_symbol} ({truedata_symbol}) = ₹{premium}")
                        return float(premium)
                else:
                    logger.debug(f"📊 TrueData lookup failed: {truedata_symbol} not in cache")
            except Exception as e:
                logger.debug(f"Could not access TrueData for {options_symbol}: {e}")
            
            # 🎯 SECONDARY: Fallback to Zerodha API only if TrueData unavailable
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                
                if orchestrator and orchestrator.zerodha_client:
                    import asyncio
                    # Get real LTP from Zerodha
                    real_ltp = asyncio.create_task(orchestrator.zerodha_client.get_options_ltp(options_symbol))
                    premium = asyncio.get_event_loop().run_until_complete(real_ltp)
                    
                    if premium and premium > 0:
                        logger.info(f"✅ FALLBACK ZERODHA LTP: {options_symbol} = ₹{premium}")
                        return float(premium)
                    else:
                        logger.warning(f"⚠️ Zerodha LTP returned zero or None for {options_symbol}")
            except Exception as e:
                logger.debug(f"Could not get Zerodha LTP for {options_symbol}: {e}")
            
            # 🎯 NO REAL LTP: Pass 0.0 to orchestrator for validation (no fallbacks)
            logger.warning(f"⚠️ NO LTP AVAILABLE for {options_symbol} - passing to orchestrator for validation")
            return 0.0  # Return 0.0 to allow orchestrator LTP validation
            
        except Exception as e:
            logger.error(f"Error getting options premium for {options_symbol}: {e}")
            # Final fallback - reject signal
            return 0.0
    
    def _round_to_tick_size(self, price: float) -> float:
        """Round options price to proper tick size (₹0.05 for options)"""
        try:
            from src.utils.helpers import round_price_to_tick
            return round_price_to_tick(price, 0.05)  # Options tick size is ₹0.05
        except ImportError:
            # Fallback if import fails
            return round(price / 0.05) * 0.05

    
    def _calculate_options_levels(self, options_entry_price: float, original_stop_loss: float, 
                                 original_target: float, option_type: str, action: str, underlying_symbol: str) -> tuple:
        """Dynamically calculate stop_loss and target for options premium - ENSURES 2:1 RATIO"""
        try:
            # DYNAMIC FIX: Use market-based reward-to-risk ratio for quality trading
            target_risk_reward_ratio = self._get_dynamic_target_risk_reward_ratio(underlying_symbol, options_entry_price, option_type)
            
            # Calculate base risk amount (DYNAMIC percentage of premium based on volatility)
            base_risk_percent = self._get_dynamic_risk_percentage(underlying_symbol, options_entry_price)
            risk_amount = options_entry_price * base_risk_percent
            reward_amount = risk_amount * target_risk_reward_ratio  # Dynamic reward based on market conditions
            
            # For BUY actions (all our options signals):
            # - stop_loss = Lower premium (cut losses)
            # - target = Higher premium (take profits)
            options_stop_loss = options_entry_price - risk_amount
            options_target = options_entry_price + reward_amount
            
            # Ensure stop_loss doesn't go too low (minimum 5% of entry price)
            min_stop_loss = options_entry_price * 0.05  # Max 95% loss
            options_stop_loss = max(options_stop_loss, min_stop_loss)
            
            # Recalculate actual risk/reward after bounds
            actual_risk = options_entry_price - options_stop_loss
            actual_reward = options_target - options_entry_price
            actual_ratio = actual_reward / actual_risk if actual_risk > 0 else 2.1
            
            logger.info(f"📊 OPTIONS LEVELS (2:1 ENFORCED):")
            logger.info(f"   Entry: ₹{options_entry_price:.2f}")
            logger.info(f"   Stop Loss: ₹{options_stop_loss:.2f} (Risk: ₹{actual_risk:.2f})")
            logger.info(f"   Target: ₹{options_target:.2f} (Reward: ₹{actual_reward:.2f})")
            logger.info(f"   Actual R:R = {actual_ratio:.2f} (Target: {target_risk_reward_ratio})")
            
            return options_stop_loss, options_target
            
        except Exception as e:
            logger.error(f"Error calculating options levels: {e}")
            # Dynamic fallback with market-based ratio
            base_risk_percent = 0.15  # Conservative 15% fallback risk
            risk_amount = options_entry_price * base_risk_percent  
            target_ratio = 2.2  # Conservative fallback ratio
            reward_amount = risk_amount * target_ratio  # Conservative fallback reward
            stop_loss = options_entry_price - risk_amount
            target = options_entry_price + reward_amount
            # Ensure minimum stop loss
            stop_loss = max(stop_loss, options_entry_price * 0.05)
            return stop_loss, target
    
    def _calculate_dynamic_options_multiplier(self, option_type: str, options_entry_price: float) -> float:
        """Calculate dynamic options multiplier based on market conditions"""
        try:
            # Base multiplier starts at 2.0
            base_multiplier = 2.0
            
            # Adjust based on option premium level (higher premium = lower multiplier)
            if options_entry_price > 200:
                premium_adjustment = 0.8  # Deep ITM options move less
            elif options_entry_price > 100:
                premium_adjustment = 1.0  # ATM options
            else:
                premium_adjustment = 1.2  # OTM options move more
            
            # Adjust based on option type and market conditions
            type_adjustment = 1.0  # Base adjustment
            
            # Final multiplier
            multiplier = base_multiplier * premium_adjustment * type_adjustment
            return max(1.5, min(multiplier, 5.0))  # Bounds between 1.5x and 5x
            
        except Exception as e:
            logger.error(f"Error calculating dynamic multiplier: {e}")
            return 2.5  # Fallback
    
    def _calculate_dynamic_volatility_factor(self, underlying_price: float) -> float:
        """Calculate dynamic volatility factor based on market conditions"""
        try:
            # This would ideally use historical price data to calculate actual volatility
            # For now, use a market-condition based approach
            
            # Base volatility factor
            base_volatility = 0.02  # 2% base
            
            # Adjust based on market hours and conditions
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11 or 14 <= current_hour <= 15:  # High volatility hours
                time_adjustment = 1.3
            else:
                time_adjustment = 1.0
            
            # Adjust based on underlying price level (higher price = potentially lower volatility)
            if underlying_price > 10000:
                price_adjustment = 0.8
            elif underlying_price > 1000:
                price_adjustment = 1.0
            else:
                price_adjustment = 1.2
            
            volatility_factor = base_volatility * time_adjustment * price_adjustment
            return max(0.01, min(volatility_factor, 0.1))  # Between 1% and 10%
            
        except Exception as e:
            logger.error(f"Error calculating volatility factor: {e}")
            return 0.03  # 3% fallback
    
    def _extract_strike_from_symbol(self, options_symbol: str) -> float:
        """Extract strike price from options symbol - FIXED REGEX"""
        try:
            import re
            
            # 🎯 CORRECT FORMAT: SYMBOL + YYMMM + STRIKE + TYPE
            # Examples: ASIANPAINT25AUG2450CE, TCS25AUG3000PE
            
            # Pattern: Any letters + YYMMM + NUMBERS + CE/PE
            match = re.search(r'([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)$', options_symbol)
            
            if match:
                symbol_part = match.group(1)    # e.g., "ASIANPAINT" 
                date_part = match.group(2)      # e.g., "25AUG"
                strike_part = match.group(3)    # e.g., "2450"
                option_type = match.group(4)    # e.g., "CE"
                
                logger.info(f"🔍 STRIKE EXTRACTION: {options_symbol}")
                logger.info(f"   Symbol: {symbol_part}, Date: {date_part}, Strike: {strike_part}, Type: {option_type}")
                
                return float(strike_part)
            
            # If regex fails, use fallback
            logger.error(f"❌ Could not extract strike from {options_symbol}")
            return 2500.0  # Safe fallback
            
        except Exception as e:
            logger.error(f"Error extracting strike from {options_symbol}: {e}")
            return 2500.0  # Fallback
    
    def _get_dynamic_min_risk_reward_ratio(self, symbol: str, price: float) -> float:
        """Calculate minimum risk-reward ratio based on market volatility and symbol characteristics"""
        try:
            # Get market volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base minimum ratio (conservative)
            base_ratio = 1.2
            
            # Adjust based on volatility:
            # High volatility = lower minimum ratio (easier to achieve)  
            # Low volatility = higher minimum ratio (need better setups)
            if volatility_multiplier > 2.0:
                return base_ratio * 0.8  # 0.96 for high volatility
            elif volatility_multiplier > 1.5:
                return base_ratio * 0.9  # 1.08 for medium volatility  
            else:
                return base_ratio * 1.1  # 1.32 for low volatility
                
        except Exception as e:
            logger.error(f"Error calculating dynamic min R:R ratio: {e}")
            return 1.2  # Conservative fallback
    
    def _get_dynamic_target_risk_reward_ratio(self, symbol: str, price: float, option_type: str = 'CE') -> float:
        """Calculate target risk-reward ratio based on market conditions and symbol characteristics"""
        try:
            # Get market volatility and momentum indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base target ratio
            base_ratio = 2.0
            
            # Adjust based on volatility:
            # High volatility = higher target ratio (bigger moves possible)
            # Low volatility = lower target ratio (smaller moves expected)
            if volatility_multiplier > 2.5:
                target_ratio = base_ratio * 1.3  # 2.6 for very high volatility
            elif volatility_multiplier > 2.0:
                target_ratio = base_ratio * 1.2  # 2.4 for high volatility
            elif volatility_multiplier > 1.5:
                target_ratio = base_ratio * 1.1  # 2.2 for medium volatility
            else:
                target_ratio = base_ratio * 0.9  # 1.8 for low volatility
            
            # Options-specific adjustments
            if option_type in ['CE', 'PE']:
                # Options can have higher targets due to leverage
                target_ratio *= 1.1
            
            # Cap the ratio at reasonable bounds
            return max(1.5, min(target_ratio, 3.5))
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target R:R ratio: {e}")
            return 2.2  # Conservative fallback
    
    def _get_dynamic_risk_percentage(self, symbol: str, price: float) -> float:
        """Calculate risk percentage based on market volatility and price level"""
        try:
            # Get volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base risk percentage
            base_risk = 0.12  # 12% base risk
            
            # Adjust based on volatility:
            # High volatility = lower risk percentage (to account for bigger moves)
            # Low volatility = higher risk percentage (smaller moves, need wider stops)
            if volatility_multiplier > 2.0:
                risk_percent = base_risk * 0.8  # 9.6% for high volatility
            elif volatility_multiplier > 1.5:
                risk_percent = base_risk * 0.9  # 10.8% for medium volatility
            else:
                risk_percent = base_risk * 1.1  # 13.2% for low volatility
            
            # Ensure reasonable bounds
            return max(0.08, min(risk_percent, 0.20))  # Between 8% and 20%
            
        except Exception as e:
            logger.error(f"Error calculating dynamic risk percentage: {e}")
            return 0.15  # 15% fallback
    
    def _get_volatility_multiplier(self, symbol: str, price: float) -> float:
        """Get volatility multiplier for the symbol based on recent price action"""
        try:
            # Try to get actual volatility data from TrueData
            from data.truedata_client import live_market_data
            
            if symbol in live_market_data:
                market_data = live_market_data[symbol]
                
                # Calculate intraday volatility
                high = market_data.get('high', price)
                low = market_data.get('low', price)
                open_price = market_data.get('open', price)
                
                if high > 0 and low > 0 and open_price > 0:
                    # Calculate percentage range
                    day_range = ((high - low) / open_price) * 100
                    
                    # Convert to volatility multiplier
                    if day_range > 4.0:
                        return 2.5  # Very high volatility
                    elif day_range > 3.0:
                        return 2.0  # High volatility
                    elif day_range > 2.0:
                        return 1.5  # Medium volatility
                    else:
                        return 1.0  # Low volatility
            
            # Fallback: Use symbol characteristics
            # Major indices tend to be less volatile than individual stocks
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                return 1.8  # Index volatility
            else:
                return 1.5  # Stock volatility
                
        except Exception as e:
            logger.error(f"Error calculating volatility multiplier for {symbol}: {e}")
            return 1.5  # Moderate fallback
    
    def _calculate_days_to_expiry(self, options_symbol: str) -> int:
        """Calculate days to expiry from options symbol"""
        try:
            # Extract date from symbol and calculate days remaining
            import re
            from datetime import datetime, timedelta
            
            # Look for date pattern in symbol (e.g., 31JUL25)
            date_match = re.search(r'(\d{1,2})([A-Z]{3})(\d{2})', options_symbol)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)
                year = int(date_match.group(3)) + 2000
                
                month_map = {
                    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                }
                month = month_map.get(month_str, 1)
                
                expiry_date = datetime(year, month, day)
                days_remaining = (expiry_date - datetime.now()).days
                return max(1, days_remaining)  # At least 1 day
            
            # Fallback: assume 7 days
            return 7
            
        except Exception as e:
            logger.error(f"Error calculating expiry for {options_symbol}: {e}")
            return 7  # 1 week fallback
    
    def _get_dynamic_lot_size(self, options_symbol: str, underlying_symbol: str) -> int:
        """🎯 FULLY DYNAMIC: Fetch actual F&O lot sizes from Zerodha instruments API"""
        try:
            # Try to get actual lot size from Zerodha instruments API
            actual_lot_size = self._fetch_zerodha_lot_size(underlying_symbol)
            if actual_lot_size:
                logger.info(f"✅ DYNAMIC LOT SIZE: {underlying_symbol} = {actual_lot_size} (from Zerodha API)")
                return actual_lot_size
            
            # NO FALLBACKS - If Zerodha API doesn't provide lot size, reject signal
            logger.error(f"❌ NO LOT SIZE from Zerodha API for {underlying_symbol} - REJECTING SIGNAL")
            return None
                
        except Exception as e:
            logger.error(f"Error getting dynamic lot size for {options_symbol}: {e}")
            return None  # NO FALLBACKS
    
    def _map_truedata_to_zerodha_symbol(self, truedata_symbol: str) -> str:
        """Map TrueData symbol format to Zerodha format"""
        # Direct mapping for common indices
        symbol_mapping = {
            'NIFTY-I': 'NIFTY',
            'BANKNIFTY-I': 'BANKNIFTY', 
            'FINNIFTY-I': 'FINNIFTY',
            'MIDCPNIFTY-I': 'MIDCPNIFTY',
            'SENSEX-I': 'SENSEX',
            'BANKEX-I': 'BANKEX'
        }
        
        # Check direct mapping first
        if truedata_symbol in symbol_mapping:
            return symbol_mapping[truedata_symbol]
        
        # For regular stocks, remove any suffixes and clean
        cleaned_symbol = truedata_symbol.replace('-I', '').replace('-EQ', '').strip()
        
        return cleaned_symbol
    
    def _fetch_zerodha_lot_size(self, underlying_symbol: str) -> int:
        """🎯 DYNAMIC: Fetch actual lot size from Zerodha instruments API"""
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.debug(f"⚠️ Zerodha client not available for lot size lookup: {underlying_symbol}")
                return None
            
            # Try to get instruments data
            if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                try:
                    # Get NFO instruments (F&O contracts)
                    instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                    
                    # Look for the underlying symbol in F&O instruments
                    for instrument in instruments:
                        trading_symbol = instrument.get('tradingsymbol', '')
                        segment = instrument.get('segment', '')
                        
                        # CRITICAL FIX: Use proper symbol mapping function
                        clean_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                        
                        # Match underlying symbol (e.g., NIFTY, RELIANCE, etc.)
                        if (clean_underlying in trading_symbol and 
                            segment == 'NFO-OPT' and  # Options only
                            ('CE' in trading_symbol or 'PE' in trading_symbol)):
                            
                            lot_size = instrument.get('lot_size', 0)
                            if lot_size > 0:
                                logger.info(f"✅ ZERODHA LOT SIZE: {underlying_symbol} = {lot_size}")
                                return lot_size
                    
                    logger.debug(f"🔍 No F&O lot size found for {underlying_symbol} in Zerodha instruments")
                    return None
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error fetching Zerodha instruments for {underlying_symbol}: {e}")
                    return None
            else:
                logger.debug(f"⚠️ Zerodha KiteConnect not initialized for lot size lookup")
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching Zerodha lot size for {underlying_symbol}: {e}")
            return None
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                base_lot_size = self._get_dynamic_lot_size(options_symbol, underlying_symbol)
                if base_lot_size is None:
                    logger.error(f"❌ NO LOT SIZE AVAILABLE for {underlying_symbol} - REJECTING SIGNAL")
                    return 0
                cost_per_lot = base_lot_size * entry_price
                
                # Check affordability
                max_capital_per_trade = available_capital * 0.6  # 60% max per trade
                
                if cost_per_lot <= max_capital_per_trade:
                    logger.info(f"✅ F&O ORDER: {underlying_symbol} = 1 lot × {base_lot_size} = {base_lot_size} qty")
                    logger.info(f"   💰 Cost: ₹{cost_per_lot:,.0f} / Available: ₹{available_capital:,.0f}")
                    return base_lot_size
                elif cost_per_lot <= (available_capital * 0.8):
                    logger.info(f"✅ F&O ORDER (HIGH COST): {underlying_symbol} = 1 lot × {base_lot_size} = {base_lot_size} qty")
                    return base_lot_size
                else:
                    logger.warning(f"❌ F&O REJECTED: {underlying_symbol} too expensive (₹{cost_per_lot:,.0f} > 80% of ₹{available_capital:,.0f})")
                    return 0
            else:
                # 🎯 EQUITY: Use share-based calculation
                max_capital_per_trade = available_capital * 0.3  # 30% max per equity trade
                max_shares = int(max_capital_per_trade / entry_price)
                
                # Minimum viable quantity for equity
                min_shares = max(1, int(5000 / entry_price))  # At least ₹5000 worth
                final_quantity = max(min_shares, min(max_shares, 100))  # Between min and 100 shares
                
                cost = final_quantity * entry_price
                logger.info(f"✅ EQUITY ORDER: {underlying_symbol} = {final_quantity} shares")
                logger.info(f"   💰 Cost: ₹{cost:,.0f} / Available: ₹{available_capital:,.0f} ({cost/available_capital:.1%})")
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_available_capital(self) -> float:
        """🎯 DYNAMIC: Get available capital from Zerodha margins API in real-time"""
        try:
            # Try to get real-time capital from Zerodha margins API
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and orchestrator.zerodha_client:
                try:
                    # Try to get margins (available cash) from Zerodha
                    if hasattr(orchestrator.zerodha_client, 'get_margins'):
                        # Use async method if available
                        import asyncio
                        loop = asyncio.get_event_loop()
                        
                        if loop.is_running():
                            # If already in async context, use fallback
                            logger.debug("⚠️ Already in async context, using cached capital")
                            return 49233.5  # Use cached value
                        else:
                            # Run async method to get live margins
                            margins = loop.run_until_complete(orchestrator.zerodha_client.get_margins())
                            if margins and isinstance(margins, (int, float)) and margins > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{margins:,.2f} (live from Zerodha)")
                                return float(margins)
                    
                    # Fallback: Try sync method if available
                    if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                        try:
                            margins = orchestrator.zerodha_client.kite.margins()
                            equity_cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
                            if equity_cash > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{equity_cash:,.2f} (from Zerodha equity margins)")
                                return float(equity_cash)
                        except Exception as margin_error:
                            logger.debug(f"⚠️ Error fetching Zerodha margins: {margin_error}")
                            
                except Exception as zerodha_error:
                    logger.debug(f"⚠️ Error accessing Zerodha for capital: {zerodha_error}")
            
            # Fallback to cached/estimated value
            logger.debug("📋 Using fallback capital (Zerodha not available)")
            return 49233.5  # Current known balance as fallback
            
        except Exception as e:
            logger.error(f"Error getting dynamic available capital: {e}")
            return 49233.5  # Safe fallback
    
    def _get_volume_based_strike(self, underlying_symbol: str, current_price: float, expiry: str, action: str) -> int:
        """🎯 USER REQUIREMENT: Select strike based on volume - highest or second highest for liquidity"""
        try:
            # First get ATM strike as baseline
            atm_strike = self._get_atm_strike_for_stock(current_price)
            
            # Get available strikes around ATM (3 strikes above and below)
            strike_interval = 50 if underlying_symbol not in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else (50 if underlying_symbol == 'NIFTY' else 100)
            
            candidate_strikes = []
            for i in range(-3, 4):  # 7 strikes total around ATM
                strike = atm_strike + (i * strike_interval)
                if strike > 0:  # Only positive strikes
                    candidate_strikes.append(strike)
            
            logger.info(f"🎯 SIMPLIFIED STRIKE SELECTION for {underlying_symbol}")
            logger.info(f"   Current Price: ₹{current_price:.2f}, ATM: {atm_strike}")
            logger.info(f"   Using ATM strike for optimal execution")
            
            # 🎯 SIMPLIFIED: Always use ATM strike for best execution and no volume barriers
            return atm_strike
                
        except Exception as e:
            logger.error(f"Error in volume-based strike selection: {e}")
            # Fallback to ATM
            atm_strike = self._get_atm_strike_for_stock(current_price)
            logger.warning(f"⚠️ Fallback to ATM strike: {atm_strike}")
            return atm_strike
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {} 
            actual_lot_size = self._fetch_zerodha_lot_size(underlying_symbol)
            if actual_lot_size:
                logger.info(f"✅ DYNAMIC LOT SIZE: {underlying_symbol} = {actual_lot_size} (from Zerodha API)")
                return actual_lot_size
            
            # Fallback: EXCHANGE-DEFINED LOT SIZES (official NSE values)
            if underlying_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index options have standard lot sizes as per NSE
                lot_sizes = {'NIFTY': 75, 'BANKNIFTY': 25, 'FINNIFTY': 40}  
                fallback_size = lot_sizes.get(underlying_symbol, 75)
                logger.info(f"📋 FALLBACK LOT SIZE: {underlying_symbol} = {fallback_size} (NSE standard)")
                return fallback_size
            else:
                # Stock options: Use NSE standard of 750 for most stocks
                fallback_size = 750  # Standard NSE stock option lot size
                logger.info(f"📋 FALLBACK LOT SIZE: {underlying_symbol} = {fallback_size} (NSE stock standard)")
                return fallback_size
                
        except Exception as e:
            logger.error(f"Error getting dynamic lot size for {options_symbol}: {e}")
            return 75  # Safe fallback
    
    def _fetch_zerodha_lot_size(self, underlying_symbol: str) -> int:
        """🎯 DYNAMIC: Fetch actual lot size from Zerodha instruments API"""
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.debug(f"⚠️ Zerodha client not available for lot size lookup: {underlying_symbol}")
                return None
            
            # Try to get instruments data
            if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                try:
                    # Get NFO instruments (F&O contracts)
                    instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                    
                    # Look for the underlying symbol in F&O instruments
                    for instrument in instruments:
                        trading_symbol = instrument.get('tradingsymbol', '')
                        segment = instrument.get('segment', '')
                        
                        # CRITICAL FIX: Use proper symbol mapping function
                        clean_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                        
                        # Match underlying symbol (e.g., NIFTY, RELIANCE, etc.)
                        if (clean_underlying in trading_symbol and 
                            segment == 'NFO-OPT' and  # Options only
                            ('CE' in trading_symbol or 'PE' in trading_symbol)):
                            
                            lot_size = instrument.get('lot_size', 0)
                            if lot_size > 0:
                                logger.info(f"✅ ZERODHA LOT SIZE: {underlying_symbol} = {lot_size}")
                                return lot_size
                    
                    logger.debug(f"🔍 No F&O lot size found for {underlying_symbol} in Zerodha instruments")
                    return None
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error fetching Zerodha instruments for {underlying_symbol}: {e}")
                    return None
            else:
                logger.debug(f"⚠️ Zerodha KiteConnect not initialized for lot size lookup")
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching Zerodha lot size for {underlying_symbol}: {e}")
            return None
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                base_lot_size = self._get_dynamic_lot_size(options_symbol, underlying_symbol)
                if base_lot_size is None:
                    logger.error(f"❌ NO LOT SIZE AVAILABLE for {underlying_symbol} - REJECTING SIGNAL")
                    return 0
                cost_per_lot = base_lot_size * entry_price
                
                # Check affordability
                max_capital_per_trade = available_capital * 0.6  # 60% max per trade
                
                if cost_per_lot <= max_capital_per_trade:
                    logger.info(f"✅ F&O ORDER: {underlying_symbol} = 1 lot × {base_lot_size} = {base_lot_size} qty")
                    logger.info(f"   💰 Cost: ₹{cost_per_lot:,.0f} / Available: ₹{available_capital:,.0f}")
                    return base_lot_size
                elif cost_per_lot <= (available_capital * 0.8):
                    logger.info(f"✅ F&O ORDER (HIGH COST): {underlying_symbol} = 1 lot × {base_lot_size} = {base_lot_size} qty")
                    return base_lot_size
                else:
                    logger.warning(f"❌ F&O REJECTED: {underlying_symbol} too expensive (₹{cost_per_lot:,.0f} > 80% of ₹{available_capital:,.0f})")
                    return 0
            else:
                # 🎯 EQUITY: Use share-based calculation
                max_capital_per_trade = available_capital * 0.3  # 30% max per equity trade
                max_shares = int(max_capital_per_trade / entry_price)
                
                # Minimum viable quantity for equity
                min_shares = max(1, int(5000 / entry_price))  # At least ₹5000 worth
                final_quantity = max(min_shares, min(max_shares, 100))  # Between min and 100 shares
                
                cost = final_quantity * entry_price
                logger.info(f"✅ EQUITY ORDER: {underlying_symbol} = {final_quantity} shares")
                logger.info(f"   💰 Cost: ₹{cost:,.0f} / Available: ₹{available_capital:,.0f} ({cost/available_capital:.1%})")
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_available_capital(self) -> float:
        """🎯 DYNAMIC: Get available capital from Zerodha margins API in real-time"""
        try:
            # Try to get real-time capital from Zerodha margins API
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and orchestrator.zerodha_client:
                try:
                    # Try to get margins (available cash) from Zerodha
                    if hasattr(orchestrator.zerodha_client, 'get_margins'):
                        # Use async method if available
                        import asyncio
                        loop = asyncio.get_event_loop()
                        
                        if loop.is_running():
                            # If already in async context, use fallback
                            logger.debug("⚠️ Already in async context, using cached capital")
                            return 49233.5  # Use cached value
                        else:
                            # Run async method to get live margins
                            margins = loop.run_until_complete(orchestrator.zerodha_client.get_margins())
                            if margins and isinstance(margins, (int, float)) and margins > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{margins:,.2f} (live from Zerodha)")
                                return float(margins)
                    
                    # Fallback: Try sync method if available
                    if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                        try:
                            margins = orchestrator.zerodha_client.kite.margins()
                            equity_cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
                            if equity_cash > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{equity_cash:,.2f} (from Zerodha equity margins)")
                                return float(equity_cash)
                        except Exception as margin_error:
                            logger.debug(f"⚠️ Error fetching Zerodha margins: {margin_error}")
                            
                except Exception as zerodha_error:
                    logger.debug(f"⚠️ Error accessing Zerodha for capital: {zerodha_error}")
            
            # Fallback to cached/estimated value
            logger.debug("📋 Using fallback capital (Zerodha not available)")
            return 49233.5  # Current known balance as fallback
            
        except Exception as e:
            logger.error(f"Error getting dynamic available capital: {e}")
            return 49233.5  # Safe fallback
    
    def _get_volume_based_strike(self, underlying_symbol: str, current_price: float, expiry: str, action: str) -> int:
        """🎯 USER REQUIREMENT: Select strike based on volume - highest or second highest for liquidity"""
        try:
            # First get ATM strike as baseline
            atm_strike = self._get_atm_strike_for_stock(current_price)
            
            # Get available strikes around ATM (3 strikes above and below)
            strike_interval = 50 if underlying_symbol not in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else (50 if underlying_symbol == 'NIFTY' else 100)
            
            candidate_strikes = []
            for i in range(-3, 4):  # 7 strikes total around ATM
                strike = atm_strike + (i * strike_interval)
                if strike > 0:  # Only positive strikes
                    candidate_strikes.append(strike)
            
            logger.info(f"🎯 SIMPLIFIED STRIKE SELECTION for {underlying_symbol}")
            logger.info(f"   Current Price: ₹{current_price:.2f}, ATM: {atm_strike}")
            logger.info(f"   Using ATM strike for optimal execution")
            
            # 🎯 SIMPLIFIED: Always use ATM strike for best execution and no volume barriers
            return atm_strike
                
        except Exception as e:
            logger.error(f"Error in volume-based strike selection: {e}")
            # Fallback to ATM
            atm_strike = self._get_atm_strike_for_stock(current_price)
            logger.warning(f"⚠️ Fallback to ATM strike: {atm_strike}")
            return atm_strike
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {} 
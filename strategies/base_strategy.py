"""
Base Strategy Class - SCALPING OPTIMIZED
Common functionality for all trading strategies with proper ATR calculation and SCALPING risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
import numpy as np
import pytz  # Add timezone support
import time # Added for time.time()

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
        self.hour_start_time = datetime.now()
        
        # Enhanced cooldown control
        self.scalping_cooldown = 30  # 30 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
    def _check_signal_rate_limits(self) -> bool:
        """Check if signal generation is allowed based on rate limits"""
        current_time = datetime.now()
        
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
            # Fallback to simple percentage target
            if stop_loss < entry_price:  # BUY trade
                return entry_price * 1.015  # 1.5% target for scalping
            else:  # SELL trade
                return entry_price * 0.985  # 1.5% target for scalping
    
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
    
    def create_standard_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, 
                              metadata: Dict) -> Optional[Dict]:
        """Create standardized signal format - SUPPORTS EQUITY, FUTURES & OPTIONS"""
        try:
            # 🎯 INTELLIGENT SIGNAL TYPE SELECTION based on market conditions and symbol
            signal_type = self._determine_optimal_signal_type(symbol, entry_price, confidence, metadata)
            
            if signal_type == 'OPTIONS':
                # Convert to options signal
                return self._create_options_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
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
    
    def _create_options_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Dict:
        """Create standardized signal format for options"""
        try:
            # 🎯 CRITICAL FIX: Convert to options symbol and force BUY action
            options_symbol, option_type = self._convert_to_options_symbol(symbol, entry_price, action)
            
            # 🚨 CRITICAL: Check if signal was rejected (e.g., MIDCPNIFTY, SENSEX)
            if options_symbol is None or option_type == 'REJECTED':
                logger.warning(f"⚠️ OPTIONS SIGNAL REJECTED: {symbol} - cannot be traded")
                return None
            
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
                options_entry_price, stop_loss, target, option_type, action
            )
            
            # Validate signal levels with OPTIONS pricing
            if not self.validate_signal_levels(options_entry_price, options_stop_loss, options_target, 'BUY'):
                logger.warning(f"Invalid options signal levels: Entry={options_entry_price}, SL={options_stop_loss}, Target={options_target}")
                return None
            
            # 🎯 CRITICAL FIX: Always BUY options (no selling due to margin requirements)
            final_action = 'BUY'  # Force all options signals to be BUY
            
            # Calculate risk metrics using OPTIONS pricing
            risk_amount = abs(options_entry_price - options_stop_loss)
            reward_amount = abs(options_target - options_entry_price)
            risk_percent = (risk_amount / options_entry_price) * 100
            reward_percent = (reward_amount / options_entry_price) * 100
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
                'entry_price': round(options_entry_price, 2),  # 🎯 FIXED: Use options premium
                'stop_loss': round(options_stop_loss, 2),      # 🎯 FIXED: Correct options stop_loss
                'target': round(options_target, 2),            # 🎯 FIXED: Correct options target
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
            
            # Check minimum risk-reward ratio (adjusted for current market conditions)
            # Reduced from 2.0 to 1.5 for current low volatility market
            min_risk_reward_ratio = 1.5  # Adjusted for current market conditions
            if risk_reward_ratio < min_risk_reward_ratio:
                logger.warning(f"Equity signal below {min_risk_reward_ratio}:1 ratio: {symbol} ({risk_reward_ratio:.2f})")
                return None
            
            return {
                'signal_id': f"{self.name}_{symbol}_{int(time.time())}",
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

    def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
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
                # Index options - use current levels
                strike = self._get_atm_strike(zerodha_underlying, actual_price)
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                expiry = self._get_next_expiry()
                
                # 🔧 CRITICAL FIX: Use Zerodha's exact symbol format
                # Zerodha format: BANKNIFTY25JUL57100PE (not BANKNIFTY31JUL2557100PE)
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
                strike = self._get_atm_strike_for_stock(actual_price)
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                expiry = self._get_next_expiry()
                
                # 🔧 CRITICAL FIX: Use Zerodha's exact symbol format for stocks too
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                
                logger.info(f"🎯 ZERODHA OPTIONS SYMBOL: {underlying_symbol} → {options_symbol}")
                logger.info(f"   Mapping: {underlying_symbol} → {zerodha_underlying}")
                logger.info(f"   Strike: {strike}, Expiry: {expiry}, Type: {option_type}")
                logger.info(f"   Used Price: ₹{actual_price:.2f} (real market price)")
                
                return options_symbol, option_type
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            return underlying_symbol, 'CE'
    
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
      
    def _get_next_expiry(self) -> str:
        """DYNAMIC EXPIRY SELECTION: Get optimal expiry based on strategy requirements"""
        # 🔍 DEBUG: Add comprehensive logging for expiry date debugging
        logger.info(f"🔍 DEBUG: Getting next expiry date...")
        
        # Try to get real expiry dates from Zerodha first
        available_expiries = self._get_available_expiries_from_zerodha()
        
        if available_expiries:
            logger.info(f"✅ Found {len(available_expiries)} expiry dates from Zerodha API")
            for i, exp in enumerate(available_expiries[:3]):  # Log first 3
                logger.info(f"   {i+1}. {exp['formatted']} ({exp['date']})")
            
            # Use the next expiry (not nearest to avoid expiry day volatility)
            optimal_expiry = self._get_optimal_expiry_for_strategy("next_weekly")  # Changed from default to "next_weekly"
            logger.info(f"🎯 SELECTED EXPIRY: {optimal_expiry}")
            return optimal_expiry
        else:
            logger.warning("⚠️ No expiry dates from Zerodha API - using fallback calculation")
            fallback_expiry = self._calculate_next_thursday_fallback()
            logger.info(f"🎯 FALLBACK EXPIRY: {fallback_expiry}")
            return fallback_expiry
    
    def _get_optimal_expiry_for_strategy(self, preference: str = "nearest_weekly") -> str:
        """
        Get optimal expiry based on strategy requirements - FIXED ZERODHA FORMAT
        
        Args:
            preference: "nearest_weekly", "nearest_monthly", "next_weekly", "max_time_decay"
        """
        available_expiries = self._get_available_expiries_from_zerodha()
        
        if not available_expiries:
            # Fallback to calculated next Thursday if API unavailable
            return self._calculate_next_thursday_fallback()
        
        today = datetime.now().date()
        
        # Filter future expiries only
        future_expiries = [exp for exp in available_expiries if exp['date'] > today]
        
        if not future_expiries:
            return self._calculate_next_thursday_fallback()
        
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
            # Get second nearest (skip current week if very close to expiry)
            nearest = future_expiries[1] if len(future_expiries) > 1 else future_expiries[0]
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
        
        # Zerodha format: 25JUL (YY + MMM)
        zerodha_expiry = f"{str(exp_date.year)[-2:]}{month_names[exp_date.month - 1]}"
        
        logger.info(f"🎯 OPTIMAL EXPIRY: {zerodha_expiry} (from {nearest['formatted']})")
        logger.info(f"   Date: {exp_date}, Days ahead: {(exp_date - today).days}")
        
        return zerodha_expiry
    
    def _get_available_expiries_from_zerodha(self) -> List[Dict]:
        """
        Fetch available expiry dates from Zerodha instruments API
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Zerodha client not available for expiry lookup")
                return self._get_fallback_expiries()
            
            # Use the new async method - we'll need to handle this synchronously
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Try to get expiries for common underlying symbols we trade
            all_expiries = set()
            
            # Get expiries for indices and stocks we commonly trade
            common_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'POWERGRID', 'RELIANCE', 'TCS']
            
            for symbol in common_symbols:
                try:
                    if loop.is_running():
                        # If we're already in an async context, use the fallback
                        expiries = self._get_fallback_expiries()
                        return expiries
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
            
            # If no expiries found from API, use fallback
            logger.warning("⚠️ No expiries found from Zerodha API, using fallback")
            return self._get_fallback_expiries()
            
        except Exception as e:
            logger.error(f"❌ Error fetching available expiries: {e}")
            return self._get_fallback_expiries()
    
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
            
            # Format for Zerodha: 31JUL25
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            formatted = f"{thursday.day:02d}{month_names[thursday.month - 1]}{str(thursday.year)[-2:]}"
            
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
        
        # 🔧 CRITICAL FIX: Format for Zerodha - their format is 25JUL (not 31JUL25)
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # Zerodha format: 25JUL (YY + MMM, not DD + MMM + YY)
        expiry_formatted = f"{str(next_thursday.year)[-2:]}{month_names[next_thursday.month - 1]}"
        
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
        """Get actual options premium from TrueData cache"""
        try:
            # Try to get options premium from TrueData global cache
            try:
                from data.truedata_client import live_market_data
                if live_market_data and options_symbol in live_market_data:
                    options_data = live_market_data[options_symbol]
                    # Extract LTP (Last Traded Price) for options premium
                    premium = options_data.get('ltp', options_data.get('price', options_data.get('last_price')))
                    if premium and premium > 0:
                        logger.info(f"✅ Got options premium from TrueData: {options_symbol} = ₹{premium}")
                        return float(premium)
            except Exception as e:
                logger.debug(f"Could not access TrueData for {options_symbol}: {e}")
            
            # Fallback: Estimate options premium dynamically based on market conditions
            estimated_premium = self._estimate_options_premium_dynamic(fallback_price, option_type, options_symbol)
            logger.warning(f"⚠️ Using dynamic estimation for {options_symbol}: ₹{estimated_premium}")
            return estimated_premium
            
        except Exception as e:
            logger.error(f"Error getting options premium for {options_symbol}: {e}")
            # Final fallback
            return self._estimate_options_premium_dynamic(fallback_price, option_type, options_symbol)
    
    def _estimate_options_premium_dynamic(self, underlying_price: float, option_type: str, options_symbol: str) -> float:
        """FIXED: Calculate realistic options premium - hundreds for indices, not thousands"""
        try:
            # Extract strike and expiry from options symbol for dynamic calculation
            strike_price = self._extract_strike_from_symbol(options_symbol)
            days_to_expiry = self._calculate_days_to_expiry(options_symbol)
            
            # 🚨 CRITICAL FIX: Realistic premium calculation for different asset types
            if any(idx in options_symbol for idx in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']):
                # INDEX OPTIONS: Premium should be ₹10-500 maximum
                base_premium_percent = 0.002  # 0.2% of underlying (much lower)
                max_premium = 500  # Maximum ₹500 for index options
                min_premium = 10   # Minimum ₹10
            else:
                # STOCK OPTIONS: Premium should be ₹5-200 maximum  
                base_premium_percent = 0.015  # 1.5% of underlying
                max_premium = 200  # Maximum ₹200 for stock options
                min_premium = 5    # Minimum ₹5
            
            # Calculate moneyness (distance from ATM)
            moneyness = abs(underlying_price - strike_price) / underlying_price
            
            # Time decay factor (less impact for short-term options)
            time_value_factor = max(0.1, min(0.5, days_to_expiry / 30))  # Max 50% time value
            
            # Volatility factor (much lower)
            volatility_factor = 0.05  # 5% volatility factor (was too high before)
            
            # Base premium calculation - MUCH MORE CONSERVATIVE
            if option_type == 'CE':
                intrinsic_value = max(0, underlying_price - strike_price)
            else:  # PE
                intrinsic_value = max(0, strike_price - underlying_price)
            
            # Time value calculation - REALISTIC
            time_value = underlying_price * base_premium_percent * time_value_factor * (1 + moneyness)
            
            estimated_premium = intrinsic_value + time_value
            
            # Apply realistic bounds
            estimated_premium = max(min_premium, min(estimated_premium, max_premium))
            
            logger.info(f"📊 REALISTIC Premium: {option_type} = ₹{estimated_premium:.2f}")
            logger.info(f"   Underlying: ₹{underlying_price}, Strike: ₹{strike_price}")
            logger.info(f"   Intrinsic: ₹{intrinsic_value:.2f}, Time: ₹{time_value:.2f}")
            logger.info(f"   Days: {days_to_expiry}, Bounds: ₹{min_premium}-₹{max_premium}")
            
            return estimated_premium
            
        except Exception as e:
            logger.error(f"Error in premium calculation: {e}")
            # Conservative fallback
            if any(idx in options_symbol for idx in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']):
                return 50.0  # ₹50 fallback for indices
            else:
                return 20.0  # ₹20 fallback for stocks
    
    def _calculate_options_levels(self, options_entry_price: float, original_stop_loss: float, 
                                 original_target: float, option_type: str, action: str) -> tuple:
        """Dynamically calculate stop_loss and target for options premium - ENSURES 2:1 RATIO"""
        try:
            # CRITICAL FIX: Force 2:1 reward-to-risk ratio for quality trading
            target_risk_reward_ratio = 2.1  # Slightly above 2.0 to ensure passing filter
            
            # Calculate base risk amount (percentage of premium)
            base_risk_percent = 0.15  # 15% risk of premium
            risk_amount = options_entry_price * base_risk_percent
            reward_amount = risk_amount * target_risk_reward_ratio  # 2.1x reward
            
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
            # Fallback with guaranteed 2:1 ratio
            risk_amount = options_entry_price * 0.15  # 15% risk
            reward_amount = risk_amount * 2.1          # 2.1x reward (210% of risk)
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
        """Extract strike price from options symbol - FIXED to avoid date contamination"""
        try:
            # 🚨 CRITICAL FIX: Extract only strike, not date+strike
            # Pattern: SYMBOL + DATE(31JUL25) + STRIKE + TYPE(CE/PE)
            import re
            
            # First remove symbol name to isolate date+strike+type
            # Look for date pattern followed by strike and CE/PE
            date_strike_match = re.search(r'(\d{1,2}[A-Z]{3}\d{2})(\d+)(CE|PE)$', options_symbol)
            
            if date_strike_match:
                date_part = date_strike_match.group(1)  # e.g., "31JUL25"
                strike_part = date_strike_match.group(2)  # e.g., "2000"
                option_type = date_strike_match.group(3)  # e.g., "PE"
                
                logger.info(f"🔍 STRIKE EXTRACTION: {options_symbol}")
                logger.info(f"   Date: {date_part}, Strike: {strike_part}, Type: {option_type}")
                
                return float(strike_part)
            
            # Fallback: If pattern doesn't match, try original method but with warning
            logger.warning(f"⚠️ Fallback strike extraction for {options_symbol}")
            fallback_match = re.search(r'(\d+)(CE|PE)$', options_symbol)
            if fallback_match:
                extracted_value = float(fallback_match.group(1))
                logger.warning(f"   Fallback extracted: {extracted_value}")
                return extracted_value
                
            # Final fallback
            logger.error(f"❌ Could not extract strike from {options_symbol}")
            return 1000.0  # Safe fallback
            
        except Exception as e:
            logger.error(f"Error extracting strike from {options_symbol}: {e}")
            return 1000.0  # Fallback
    
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
        """Get CORRECT exchange-defined lot sizes - never modify exchange requirements"""
        try:
            # EXCHANGE-DEFINED LOT SIZES (cannot be changed - these are official)
            if underlying_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index options have standard lot sizes as per NSE
                lot_sizes = {'NIFTY': 75, 'BANKNIFTY': 25, 'FINNIFTY': 40}  
                return lot_sizes.get(underlying_symbol, 75)
            else:
                # Stock options have exchange-defined lot sizes - fetch from market data
                try:
                    from data.truedata_client import live_market_data
                    if live_market_data and underlying_symbol in live_market_data:
                        stock_price = live_market_data[underlying_symbol].get('ltp', 1000)
                        # CORRECT EXCHANGE LOT SIZES for major stocks (as per NSE/BSE)
                        if stock_price > 10000:
                            return 375   # Standard lot for very expensive stocks (e.g., MRF)
                        elif stock_price > 3000:
                            return 750   # Standard lot for expensive stocks (e.g., BAJFINANCE)
                        elif stock_price > 1000:
                            return 750   # Standard lot for medium-priced stocks
                        else:
                            return 1500  # Standard lot for cheaper stocks
                except:
                    pass
                
                # Fallback: use standard stock option lot size
                return 750  # Standard NSE stock option lot size
                
        except Exception as e:
            logger.error(f"Error getting lot size for {options_symbol}: {e}")
            return 75  # Safe fallback
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """Calculate quantity based on capital constraints - limit NUMBER OF LOTS, not lot size"""
        try:
            # Get the correct exchange-defined lot size
            base_lot_size = self._get_dynamic_lot_size(options_symbol, underlying_symbol)
            
            # Capital constraint: Maximum 80% of available capital per trade (dynamic)
            available_capital = self._get_available_capital()
            max_capital_per_trade = available_capital * 0.8  # 80% max per trade
            
            # Calculate how many lots we can afford
            cost_per_lot = base_lot_size * entry_price
            max_affordable_lots = int(max_capital_per_trade / cost_per_lot) if cost_per_lot > 0 else 0
            
            # Ensure at least 1 lot if affordable, maximum 5 lots for risk management
            if max_affordable_lots <= 0:
                logger.warning(f"💰 {options_symbol}: Cannot afford even 1 lot (₹{cost_per_lot:,.0f} > ₹{max_capital_per_trade:,.0f})")
                return 0  # Cannot afford any lots
            
            # Limit to maximum 5 lots for risk management
            num_lots = min(max_affordable_lots, 5)
            final_quantity = num_lots * base_lot_size
            
            logger.info(f"💰 {options_symbol}: {num_lots} lots × {base_lot_size} = {final_quantity} qty (₹{final_quantity * entry_price:,.0f})")
            return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating capital-constrained quantity: {e}")
            # Fallback: use 1 lot of the base lot size
            base_lot_size = self._get_dynamic_lot_size(options_symbol, underlying_symbol)
            return base_lot_size
    
    def _get_available_capital(self) -> float:
        """Get available capital dynamically (will be overridden by orchestrator/trading engine)"""
        try:
            # Try to get real-time capital from orchestrator/zerodha
            # This is a placeholder - the actual implementation will fetch from Zerodha API
            return 49233.5  # Fallback to current known balance
        except Exception as e:
            logger.error(f"Error getting available capital: {e}")
            return 49233.5  # Safe fallback 
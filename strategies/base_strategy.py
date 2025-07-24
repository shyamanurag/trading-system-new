"""
Base Strategy Class - SCALPING OPTIMIZED
Common functionality for all trading strategies with proper ATR calculation and SCALPING risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
import numpy as np
import pytz  # Add timezone support

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
        
        # SCALPING-OPTIMIZED cooldown controls
        self.scalping_cooldown = config.get('scalping_cooldown_seconds', 15)  # Default 15 seconds
        self.symbol_cooldowns = {}  # Symbol-specific cooldowns
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
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
                              metadata: Dict) -> Dict:
        """Create standardized signal format for all strategies"""
        try:
            # Validate signal levels
            if not self.validate_signal_levels(entry_price, stop_loss, target, action):
                return None
            
            # 🎯 CRITICAL FIX: Convert to options symbol for scalping strategies
            options_symbol, option_type = self._convert_to_options_symbol(symbol, entry_price, action)
            
            # Calculate risk metrics
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(target - entry_price)
            risk_percent = (risk_amount / entry_price) * 100
            reward_percent = (reward_amount / entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # CRITICAL FIX: Generate unique signal_id for tracking
            signal_id = f"{self.name}_{options_symbol}_{int(datetime.now().timestamp())}"
            
            return {
                # Core signal fields (consistent naming)
                'signal_id': signal_id,
                'symbol': options_symbol,  # 🎯 FIXED: Use options symbol instead of underlying
                'underlying_symbol': symbol,  # Keep original for reference
                'option_type': option_type,  # CE or PE
                'action': action.upper(),  # Use 'action' not 'direction'
                'quantity': 50,  # Standard lot size
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
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
                    'signal_source': 'strategy_engine'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating standard signal: {e}")
            return None
    
    def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
        """Convert underlying symbol to appropriate options symbol for scalping"""
        try:
            # For scalping strategies, convert equity signals to options
            if underlying_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index options - use current levels
                strike = self._get_atm_strike(underlying_symbol, current_price)
                option_type = 'CE' if action.upper() == 'BUY' else 'PE'
                expiry = self._get_next_expiry()
                options_symbol = f"{underlying_symbol}{expiry}{strike}{option_type}"
                return options_symbol, option_type
            else:
                # Stock options - convert equity to options
                # CRITICAL FIX: Truncate long symbol names for options
                truncated_symbol = self._truncate_symbol_for_options(underlying_symbol)
                strike = self._get_atm_strike_for_stock(current_price)
                option_type = 'CE' if action.upper() == 'BUY' else 'PE'  
                expiry = self._get_next_expiry()
                options_symbol = f"{truncated_symbol}{expiry}{strike}{option_type}"
                return options_symbol, option_type
                
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            # Fallback to underlying symbol
            return underlying_symbol, 'EQUITY'
    
    def _get_atm_strike(self, symbol: str, price: float) -> int:
        """Get ATM strike for index options"""
        if symbol == 'NIFTY':
            return round(price / 50) * 50  # Round to nearest 50
        elif symbol == 'BANKNIFTY':
            return round(price / 100) * 100  # Round to nearest 100
        elif symbol == 'FINNIFTY':
            return round(price / 50) * 50  # Round to nearest 50
        else:
            return int(price)
    
    def _get_atm_strike_for_stock(self, price: float) -> int:
        """Get ATM strike for stock options"""
        if price < 100:
            return round(price / 5) * 5  # Round to nearest 5
        elif price < 500:
            return round(price / 10) * 10  # Round to nearest 10
        else:
            return round(price / 50) * 50  # Round to nearest 50
    
    def _get_next_expiry(self) -> str:
        """Get next monthly expiry in correct Zerodha format like 25JUL24"""
        today = datetime.now()
        
        # CRITICAL FIX: Use standard monthly expiry format (25th of month)
        # Zerodha monthly expiries are typically on the last Thursday around 25th
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # For current month - check if we're past expiry
        current_month = today.month
        current_year = today.year
        
        # If we're past 25th of current month, use next month's expiry
        if today.day > 25:
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        
        year_suffix = str(current_year)[-2:]
        month_name = month_names[current_month - 1]
        
        # Standard monthly expiry day (25th)
        expiry_day = "25"
        
                return f"{expiry_day}{month_name}{year_suffix}"
    
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
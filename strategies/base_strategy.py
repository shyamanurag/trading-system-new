"""
Base Strategy Class
Common functionality for all trading strategies with proper ATR calculation and risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class BaseStrategy:
    """Base class for all trading strategies with proper ATR and risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "BaseStrategy"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
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
        """Calculate dynamic stop loss based on ATR with proper bounds"""
        try:
            # Calculate ATR-based stop loss distance
            atr_distance = atr * multiplier
            
            # Convert to percentage
            atr_percent = (atr_distance / entry_price) * 100
            
            # Apply bounds
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
            fallback_percent = 1.0  # 1% fallback
            if action.upper() == 'BUY':
                return entry_price * (1 - fallback_percent / 100)
            else:
                return entry_price * (1 + fallback_percent / 100)
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                risk_reward_ratio: float = 2.0) -> float:
        """Calculate dynamic target based on stop loss and risk/reward ratio"""
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
                return entry_price * 1.02  # 2% target
            else:  # SELL trade
                return entry_price * 0.98  # 2% target
    
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
            
            # Calculate risk metrics
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(target - entry_price)
            risk_percent = (risk_amount / entry_price) * 100
            reward_percent = (reward_amount / entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            return {
                'symbol': symbol,
                'action': action.upper(),
                'quantity': 50,  # Standard lot size
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'strategy': self.name,
                'confidence': round(min(confidence, 0.9), 2),
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                'metadata': {
                    **metadata,
                    'signal_validation': 'PASSED',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating standard signal: {e}")
            return None
    
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
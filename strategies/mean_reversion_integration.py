"""
Strategy Integration Helper for Professional Mean Reversion System
===================================================================
Provides simple methods for strategies to:
1. Check if they should trade (avoid chasing exhausted moves)
2. Get adaptive confidence thresholds
3. Adjust position sizes based on mean reversion risk
4. Determine optimal entry timing

Usage in any strategy:
    from strategies.mean_reversion_integration import StrategyMeanReversionHelper
    
    self.mr_helper = StrategyMeanReversionHelper(self)
    
    # Before generating signal:
    should_trade, reason = self.mr_helper.should_generate_signal(symbol, 'BUY', 8.5)
    if not should_trade:
        return None  # Skip this signal
    
    # Adjust position size:
    adjusted_quantity = self.mr_helper.adjust_position_size(base_quantity, symbol, 'BUY')
    
Author: Trading System v2
Created: 2025-11-13
"""

import logging
from typing import Tuple, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class StrategyMeanReversionHelper:
    """
    Simple integration helper for strategies to avoid chasing exhausted moves
    
    Each strategy gets one instance of this helper
    """
    
    def __init__(self, strategy):
        """
        Args:
            strategy: The strategy instance (must have self.market_bias)
        """
        self.strategy = strategy
        self.name = getattr(strategy, 'name', 'UnknownStrategy')
        logger.info(f"✅ {self.name}: Mean Reversion Helper initialized")
    
    def should_generate_signal(self, symbol: str, action: str, signal_confidence: float) -> Tuple[bool, str]:
        """
        Check if strategy should generate signal based on mean reversion state
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            signal_confidence: Strategy's raw confidence (0-10 scale)
            
        Returns:
            (should_trade: bool, reason: str)
        """
        try:
            # Get market bias and mean reversion signal
            market_bias = getattr(self.strategy, 'market_bias', None)
            if not market_bias:
                return True, "no_bias_system"
            
            mr_detector = getattr(market_bias, 'mean_reversion_detector', None)
            if not mr_detector:
                return True, "no_mr_detector"
            
            # Get latest NIFTY data for MR detection
            nifty_data = self._get_nifty_data()
            if not nifty_data:
                return True, "no_nifty_data"
            
            # Get mean reversion signal
            mr_signal = mr_detector.detect_mean_reversion(nifty_data)
            current_bias = market_bias.current_bias
            
            # DECISION LOGIC
            if mr_signal.mode == 'TREND_FOLLOW':
                # Fresh move, all signals allowed
                return True, f"TREND_FOLLOW:{mr_signal.recommended_action}"
            
            elif mr_signal.mode == 'CAUTION':
                # Normal operation, use standard confidence threshold
                min_conf = 7.5
                if signal_confidence >= min_conf:
                    return True, f"CAUTION:conf={signal_confidence:.1f}>={min_conf}"
                else:
                    return False, f"CAUTION:low_conf={signal_confidence:.1f}<{min_conf}"
            
            elif mr_signal.mode == 'MEAN_REVERSION':
                # Check if chasing or fading
                bias_direction = current_bias.direction
                
                # Chasing the exhausted move = BAD
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    # Need very high confidence to chase extended moves
                    min_conf = 9.0
                    if signal_confidence >= min_conf:
                        logger.warning(f"⚠️ {self.name}: CHASING EXTENDED MOVE for {symbol} {action} "
                                     f"(conf={signal_confidence:.1f} >= {min_conf}) - RISKY")
                        return True, f"MR:CHASE_EXTENDED:conf={signal_confidence:.1f}"
                    else:
                        return False, f"MR:REJECT_CHASE:conf={signal_confidence:.1f}<{min_conf}"
                
                # Fading the exhausted move = GOOD
                else:
                    min_conf = 7.0
                    if signal_confidence >= min_conf:
                        logger.info(f"✅ {self.name}: FADING EXTENDED MOVE for {symbol} {action} "
                                   f"(mean reversion trade)")
                        return True, f"MR:FADE_EXTENDED✅"
                    else:
                        return False, f"MR:low_conf={signal_confidence:.1f}<{min_conf}"
            
            elif mr_signal.mode == 'EXTREME_REVERSION':
                # Check if chasing or fading
                bias_direction = current_bias.direction
                
                # Chasing extreme exhausted move = VERY BAD
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    # Nearly impossible threshold - strongly discourage
                    min_conf = 9.5
                    if signal_confidence >= min_conf:
                        logger.error(f"🔴 {self.name}: CHASING EXTREME EXHAUSTED MOVE for {symbol} {action} "
                                    f"(conf={signal_confidence:.1f}) - VERY RISKY!")
                        return True, f"EXTREME:CHASE:conf={signal_confidence:.1f}🔴"
                    else:
                        logger.info(f"🛑 {self.name}: BLOCKED EXTREME CHASE for {symbol} {action} "
                                   f"(conf={signal_confidence:.1f}<{min_conf}) - Protecting capital")
                        return False, f"EXTREME:BLOCKED_CHASE🛑"
                
                # Fading extreme exhausted move = VERY GOOD
                else:
                    min_conf = 6.0
                    logger.info(f"🎯 {self.name}: EXTREME MEAN REVERSION TRADE for {symbol} {action} "
                               f"(high probability setup)")
                    return True, f"EXTREME:FADE✅✅"
            
            # Default allow
            return True, "default_allow"
            
        except Exception as e:
            logger.error(f"Error in mean reversion check: {e}")
            return True, f"error:{e}"
    
    def adjust_position_size(self, base_quantity: int, symbol: str, action: str) -> int:
        """
        Adjust position size based on mean reversion risk
        
        Args:
            base_quantity: Strategy's calculated position size
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            
        Returns:
            Adjusted quantity (int)
        """
        try:
            market_bias = getattr(self.strategy, 'market_bias', None)
            if not market_bias:
                return base_quantity
            
            mr_detector = getattr(market_bias, 'mean_reversion_detector', None)
            if not mr_detector:
                return base_quantity
            
            nifty_data = self._get_nifty_data()
            if not nifty_data:
                return base_quantity
            
            mr_signal = mr_detector.detect_mean_reversion(nifty_data)
            current_bias = market_bias.current_bias
            
            # Position size multipliers
            if mr_signal.mode == 'TREND_FOLLOW':
                # Fresh move, normal or slightly larger size
                multiplier = 1.1
                
            elif mr_signal.mode == 'CAUTION':
                # Normal size
                multiplier = 1.0
                
            elif mr_signal.mode == 'MEAN_REVERSION':
                bias_direction = current_bias.direction
                
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    # Chasing - reduce size
                    multiplier = 0.5
                    logger.info(f"⚠️ Position size reduced 50% for {symbol} {action} (chasing extended move)")
                else:
                    # Fading - normal to slightly larger
                    multiplier = 1.1
                    logger.info(f"✅ Position size boosted 10% for {symbol} {action} (mean reversion trade)")
                    
            elif mr_signal.mode == 'EXTREME_REVERSION':
                bias_direction = current_bias.direction
                
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    # Chasing extreme - heavily reduce
                    multiplier = 0.3
                    logger.warning(f"🔴 Position size reduced 70% for {symbol} {action} (extreme chase risk)")
                else:
                    # Fading extreme - boost size (high probability)
                    multiplier = 1.3
                    logger.info(f"🎯 Position size boosted 30% for {symbol} {action} (extreme mean reversion)")
            else:
                multiplier = 1.0
            
            adjusted = int(base_quantity * multiplier)
            adjusted = max(1, adjusted)  # At least 1
            
            if adjusted != base_quantity:
                logger.info(f"📊 Position Size Adjustment: {symbol} {action} -> "
                           f"{base_quantity} → {adjusted} ({multiplier:.1f}x)")
            
            return adjusted
            
        except Exception as e:
            logger.error(f"Error adjusting position size: {e}")
            return base_quantity
    
    def get_adaptive_confidence_threshold(self, action: str) -> Tuple[float, str]:
        """
        Get adaptive confidence threshold for signal filtering
        
        Args:
            action: 'BUY' or 'SELL'
            
        Returns:
            (min_confidence_threshold, reason)
        """
        try:
            market_bias = getattr(self.strategy, 'market_bias', None)
            if not market_bias:
                return 7.5, "default"
            
            mr_detector = getattr(market_bias, 'mean_reversion_detector', None)
            if not mr_detector:
                return 7.5, "default"
            
            nifty_data = self._get_nifty_data()
            if not nifty_data:
                return 7.5, "default"
            
            mr_signal = mr_detector.detect_mean_reversion(nifty_data)
            current_bias = market_bias.current_bias
            
            # Determine threshold
            if mr_signal.mode == 'TREND_FOLLOW':
                return 6.5, "TREND_FOLLOW"
                
            elif mr_signal.mode == 'CAUTION':
                return 7.5, "CAUTION"
                
            elif mr_signal.mode == 'MEAN_REVERSION':
                bias_direction = current_bias.direction
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    return 9.0, "MR:CHASE"
                else:
                    return 7.0, "MR:FADE"
                    
            elif mr_signal.mode == 'EXTREME_REVERSION':
                bias_direction = current_bias.direction
                if (action == 'BUY' and bias_direction == 'BULLISH') or \
                   (action == 'SELL' and bias_direction == 'BEARISH'):
                    return 9.5, "EXTREME:CHASE"
                else:
                    return 6.0, "EXTREME:FADE"
            
            return 7.5, "default"
            
        except Exception as e:
            logger.error(f"Error getting adaptive threshold: {e}")
            return 7.5, f"error:{e}"
    
    def _get_nifty_data(self) -> Optional[Dict]:
        """Get latest NIFTY data from orchestrator"""
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator:
                return None
            
            # Try to get from orchestrator's latest market data
            if hasattr(orchestrator, '_latest_market_data'):
                for symbol in ['NIFTY-I', 'NIFTY', 'NIFTY 50']:
                    if symbol in orchestrator._latest_market_data:
                        return orchestrator._latest_market_data[symbol]
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get NIFTY data: {e}")
            return None
    
    def log_signal_decision(self, symbol: str, action: str, confidence: float, 
                           allowed: bool, reason: str):
        """Log signal decision for debugging"""
        status = "✅ ALLOWED" if allowed else "🚫 BLOCKED"
        logger.info(f"{status}: {self.name} -> {symbol} {action} (conf={confidence:.1f}) | Reason: {reason}")


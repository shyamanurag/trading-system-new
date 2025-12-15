"""
🎯 ENHANCED OPEN POSITION DECISION SYSTEM
========================================
Comprehensive decision framework for managing existing open positions with
intelligent analysis, dynamic adjustments, and professional risk management.

COMPETITIVE ADVANTAGES:
1. Multi-factor position analysis with P&L, time, volatility, and market conditions
2. Dynamic profit booking and loss cutting based on market regime
3. Intelligent position scaling and risk adjustment
4. Time-based position management with aging analysis
5. Market condition adaptation for position decisions
6. Professional trailing stop and target management
7. Comprehensive decision audit trail and reasoning
"""

import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pytz

logger = logging.getLogger(__name__)

class OpenPositionAction(Enum):
    """Open position management actions"""
    HOLD = "HOLD"
    EXIT_FULL = "EXIT_FULL"
    EXIT_PARTIAL = "EXIT_PARTIAL"
    SCALE_IN = "SCALE_IN"
    ADJUST_STOP = "ADJUST_STOP"
    ADJUST_TARGET = "ADJUST_TARGET"
    TRAIL_STOP = "TRAIL_STOP"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"

class ExitReason(Enum):
    """Reasons for position exit"""
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TARGET_ACHIEVED = "TARGET_ACHIEVED"
    TRAILING_STOP_HIT = "TRAILING_STOP_HIT"
    TIME_BASED_EXIT = "TIME_BASED_EXIT"
    MARKET_CONDITION_CHANGE = "MARKET_CONDITION_CHANGE"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    PROFIT_BOOKING = "PROFIT_BOOKING"
    EMERGENCY_CLOSE = "EMERGENCY_CLOSE"
    INTRADAY_SQUARE_OFF = "INTRADAY_SQUARE_OFF"

@dataclass
class OpenPositionDecisionResult:
    """Result of open position decision analysis"""
    action: OpenPositionAction
    exit_reason: Optional[ExitReason]
    confidence: float  # 0-10 confidence in the decision
    urgency: str  # LOW, MEDIUM, HIGH, EMERGENCY
    quantity_percentage: float  # % of position to act on (0-100)
    new_stop_loss: Optional[float]
    new_target: Optional[float]
    reasoning: str
    metadata: Dict[str, Any]

class EnhancedOpenPositionDecision:
    """
    INSTITUTIONAL-GRADE OPEN POSITION DECISION SYSTEM
    
    Analyzes existing positions and makes intelligent decisions about
    holding, exiting, scaling, or adjusting based on multiple factors.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 🚨 INTRADAY PROFIT/LOSS THRESHOLDS (TUNED for realistic intraday targets)
        # Previous: 15%/25% (swing trading levels - never hit intraday)
        # New: 2%/4% (realistic intraday profit booking)
        self.profit_booking_threshold_1 = self.config.get('profit_booking_threshold_1', 2.0)  # 2% profit (was 15%)
        self.profit_booking_threshold_2 = self.config.get('profit_booking_threshold_2', 4.0)  # 4% profit (was 25%)
        self.stop_loss_threshold = self.config.get('stop_loss_threshold', -2.0)  # -2% loss (was -8%)
        self.trailing_stop_activation = self.config.get('trailing_stop_activation', 1.5)  # 1.5% profit (was 10%)
        
        # 🎯 RSI-BASED EXIT THRESHOLDS (NEW - KEY IMPROVEMENT)
        self.rsi_overbought_threshold = 85  # Partial exit when RSI > 85 AND profitable
        self.rsi_extreme_threshold = 90     # Tighten stop when RSI > 90
        self.rsi_oversold_threshold = 15    # Partial exit shorts when RSI < 15 AND profitable
        self.rsi_extreme_oversold = 10      # Tighten stop for shorts when RSI < 10
        
        # TIME-BASED PARAMETERS
        self.max_position_age_minutes = self.config.get('max_position_age_minutes', 240)  # 4 hours max
        self.quick_profit_time_minutes = self.config.get('quick_profit_time_minutes', 15)  # 15 min for quick profits
        self.intraday_square_off_time = time(15, 20)  # 3:20 PM IST
        
        # MARKET CONDITION PARAMETERS
        self.high_volatility_threshold = self.config.get('high_volatility_threshold', 3.0)  # 3% volatility
        self.low_volume_threshold = self.config.get('low_volume_threshold', 50000)  # 50K volume
        
        # SCALING PARAMETERS
        self.scale_in_profit_threshold = self.config.get('scale_in_profit_threshold', 5.0)  # 5% profit
        self.max_scale_percentage = self.config.get('max_scale_percentage', 25.0)  # 25% additional
        
        # DECISION HISTORY
        self.recent_decisions = []
        self.max_decision_history = 1000
        
    async def evaluate_open_position(
        self,
        position: Dict,
        current_price: float,
        market_data: Dict,
        market_bias = None,
        portfolio_context: Dict = None
    ) -> OpenPositionDecisionResult:
        """
        Comprehensive evaluation of what to do with an existing open position
        
        Args:
            position: Position details (symbol, entry_price, quantity, etc.)
            current_price: Current market price
            market_data: Current market data for the symbol
            market_bias: Market directional bias system
            portfolio_context: Overall portfolio context
            
        Returns:
            OpenPositionDecisionResult with recommended action and reasoning
        """
        try:
            symbol = position.get('symbol', '')
            entry_price = float(position.get('entry_price', 0.0))
            quantity = int(position.get('quantity', 0))
            action = position.get('action', 'BUY')
            entry_time = position.get('entry_time') or position.get('timestamp')
            
            logger.info(f"🔍 EVALUATING OPEN POSITION: {symbol} {action} {quantity}@₹{entry_price} | Current: ₹{current_price}")
            
            # STEP 1: Calculate Position Metrics (🔥 FIX: Pass market_data for RSI/MACD)
            position_metrics = await self._calculate_position_metrics(
                position, current_price, entry_time, market_data
            )
            
            # STEP 2: Check Emergency Exit Conditions
            emergency_result = await self._check_emergency_exit_conditions(
                position, current_price, position_metrics, market_data
            )
            if emergency_result.action == OpenPositionAction.EMERGENCY_EXIT:
                return emergency_result
            
            # STEP 3: Check Time-Based Exit Conditions
            time_result = await self._check_time_based_conditions(
                position, position_metrics, market_data
            )
            if time_result.action in [OpenPositionAction.EXIT_FULL, OpenPositionAction.EMERGENCY_EXIT]:
                return time_result
            
            # STEP 4: Check Stop Loss and Target Conditions
            stop_target_result = await self._check_stop_loss_and_targets(
                position, current_price, position_metrics
            )
            if stop_target_result.action == OpenPositionAction.EXIT_FULL:
                return stop_target_result
            
            # STEP 5: Analyze Profit Booking Opportunities
            profit_result = await self._analyze_profit_booking(
                position, current_price, position_metrics, market_data
            )
            if profit_result.action == OpenPositionAction.EXIT_PARTIAL:
                return profit_result
            
            # 🎯 STEP 5B: RSI-BASED EXIT CHECK (NEW - KEY IMPROVEMENT)
            # Exit when RSI is extreme even if profit targets not hit
            rsi_result = await self._check_rsi_based_exits(
                position, current_price, position_metrics, market_data
            )
            if rsi_result.action in [OpenPositionAction.EXIT_PARTIAL, OpenPositionAction.EXIT_FULL, 
                                      OpenPositionAction.TRAIL_STOP]:
                return rsi_result
            
            # STEP 6: Evaluate Position Scaling Opportunities
            scaling_result = await self._evaluate_position_scaling(
                position, current_price, position_metrics, market_data, market_bias
            )
            if scaling_result.action == OpenPositionAction.SCALE_IN:
                return scaling_result
            
            # STEP 7: Check Trailing Stop Adjustments
            trailing_result = await self._check_trailing_stop_adjustments(
                position, current_price, position_metrics
            )
            if trailing_result.action in [OpenPositionAction.TRAIL_STOP, OpenPositionAction.ADJUST_STOP]:
                return trailing_result
            
            # STEP 8: Market Condition Based Adjustments
            market_result = await self._analyze_market_condition_adjustments(
                position, current_price, position_metrics, market_data, market_bias
            )
            if market_result.action != OpenPositionAction.HOLD:
                return market_result
            
            # DEFAULT: HOLD POSITION
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=7.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Position within normal parameters - Continue holding",
                metadata={
                    'pnl_percent': position_metrics['pnl_percent'],
                    'age_minutes': position_metrics['age_minutes'],
                    'current_price': current_price
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error evaluating open position: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Evaluation error: {str(e)} - Defaulting to HOLD",
                metadata={'error': str(e)}
            )
    
    async def _calculate_position_metrics(self, position: Dict, current_price: float, 
                                          entry_time, market_data: Dict = None) -> Dict:
        """Calculate key position metrics including technical indicators"""
        try:
            entry_price = float(position.get('entry_price', 0.0))
            action = position.get('action', 'BUY')
            market_data = market_data or {}
            
            # Calculate P&L percentage
            if action == 'BUY':
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:  # SELL
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
            
            # Calculate position age
            age_minutes = 0
            if entry_time:
                try:
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    else:
                        entry_dt = entry_time
                    age_minutes = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 60
                except Exception as e:
                    logger.debug(f"Could not calculate position age: {e}")
                    age_minutes = 0
            
            # Calculate risk metrics
            stop_loss = position.get('stop_loss', 0.0)
            target = position.get('target', 0.0)
            
            risk_percent = 0.0
            reward_percent = 0.0
            
            if stop_loss and stop_loss > 0:
                if action == 'BUY':
                    risk_percent = ((entry_price - stop_loss) / entry_price) * 100
                else:
                    risk_percent = ((stop_loss - entry_price) / entry_price) * 100
            
            if target and target > 0:
                if action == 'BUY':
                    reward_percent = ((target - entry_price) / entry_price) * 100
                else:
                    reward_percent = ((entry_price - target) / entry_price) * 100
            
            # 🔥 FIX: Extract technical indicators from market_data (enriched by base_strategy)
            # Priority: market_data > position metadata > defaults
            metadata = position.get('metadata', {})
            rsi = market_data.get('rsi', position.get('rsi', metadata.get('rsi', 50.0)))
            macd_state = market_data.get('macd_crossover', market_data.get('macd_state', 
                         position.get('macd_state', metadata.get('macd_state', 'neutral'))))
            buy_pressure = market_data.get('buying_pressure', market_data.get('buy_pressure',
                           position.get('buy_pressure', metadata.get('buy_pressure', 0.5))))
            sell_pressure = market_data.get('selling_pressure', market_data.get('sell_pressure',
                            position.get('sell_pressure', metadata.get('sell_pressure', 0.5))))
            
            return {
                'pnl_percent': pnl_percent,
                'age_minutes': age_minutes,
                'risk_percent': abs(risk_percent),
                'reward_percent': abs(reward_percent),
                'risk_reward_ratio': abs(reward_percent / risk_percent) if risk_percent > 0 else 0,
                'entry_price': entry_price,
                'action': action,
                # 🔥 NEW: Technical indicators for trailing stop decisions
                'rsi': rsi,
                'macd_state': macd_state,
                'buy_pressure': buy_pressure,
                'sell_pressure': sell_pressure
            }
            
        except Exception as e:
            logger.error(f"Error calculating position metrics: {e}")
            return {
                'pnl_percent': 0.0,
                'age_minutes': 0.0,
                'risk_percent': 0.0,
                'reward_percent': 0.0,
                'risk_reward_ratio': 0.0,
                'entry_price': 0.0,
                'action': 'BUY',
                'rsi': 50.0,
                'macd_state': 'neutral',
                'buy_pressure': 0.5,
                'sell_pressure': 0.5
            }
    
    async def _check_emergency_exit_conditions(self, position: Dict, current_price: float, 
                                             metrics: Dict, market_data: Dict) -> OpenPositionDecisionResult:
        """Check for emergency exit conditions"""
        try:
            pnl_percent = metrics['pnl_percent']
            
            # EMERGENCY: Large loss (>15%)
            if pnl_percent < -15.0:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EMERGENCY_EXIT,
                    exit_reason=ExitReason.EMERGENCY_CLOSE,
                    confidence=10.0,
                    urgency="EMERGENCY",
                    quantity_percentage=100.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"EMERGENCY EXIT: Large loss {pnl_percent:.1f}% - Immediate exit required",
                    metadata={'pnl_percent': pnl_percent, 'loss_threshold': -15.0}
                )
            
            # EMERGENCY: Extreme market volatility
            volatility = abs(float(market_data.get('change_percent', 0.0)))
            if volatility > 8.0:  # >8% market move
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EMERGENCY_EXIT,
                    exit_reason=ExitReason.MARKET_CONDITION_CHANGE,
                    confidence=9.0,
                    urgency="EMERGENCY",
                    quantity_percentage=100.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"EMERGENCY EXIT: Extreme market volatility {volatility:.1f}%",
                    metadata={'volatility': volatility, 'threshold': 8.0}
                )
            
            # EMERGENCY: Intraday square-off time
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).time()
            if current_time >= self.intraday_square_off_time:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EMERGENCY_EXIT,
                    exit_reason=ExitReason.INTRADAY_SQUARE_OFF,
                    confidence=10.0,
                    urgency="EMERGENCY",
                    quantity_percentage=100.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"EMERGENCY EXIT: Intraday square-off time {current_time}",
                    metadata={'current_time': current_time.strftime('%H:%M:%S')}
                )
            
            # No emergency conditions
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="No emergency conditions detected",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Emergency check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_time_based_conditions(self, position: Dict, metrics: Dict, 
                                         market_data: Dict) -> OpenPositionDecisionResult:
        """Check time-based exit conditions"""
        try:
            age_minutes = metrics['age_minutes']
            pnl_percent = metrics['pnl_percent']
            
            # Position too old (>4 hours)
            if age_minutes > self.max_position_age_minutes:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_FULL,
                    exit_reason=ExitReason.TIME_BASED_EXIT,
                    confidence=8.0,
                    urgency="HIGH",
                    quantity_percentage=100.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"Position too old: {age_minutes:.1f} minutes > {self.max_position_age_minutes} limit",
                    metadata={'age_minutes': age_minutes, 'max_age': self.max_position_age_minutes}
                )
            
            # Quick profit booking (>3% profit in <15 minutes)
            if pnl_percent > 3.0 and age_minutes < self.quick_profit_time_minutes:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.PROFIT_BOOKING,
                    confidence=7.5,
                    urgency="MEDIUM",
                    quantity_percentage=50.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"Quick profit booking: {pnl_percent:.1f}% profit in {age_minutes:.1f} minutes",
                    metadata={'pnl_percent': pnl_percent, 'age_minutes': age_minutes}
                )
            
            # No time-based exit needed
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="No time-based exit conditions met",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error checking time-based conditions: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Time check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_stop_loss_and_targets(self, position: Dict, current_price: float, 
                                         metrics: Dict) -> OpenPositionDecisionResult:
        """Check stop loss and target conditions"""
        try:
            entry_price = metrics['entry_price']
            action = metrics['action']
            stop_loss = position.get('stop_loss', 0.0)
            target = position.get('target', 0.0)
            
            # Check stop loss hit
            if stop_loss and stop_loss > 0:
                stop_hit = False
                if action == 'BUY' and current_price <= stop_loss:
                    stop_hit = True
                elif action == 'SELL' and current_price >= stop_loss:
                    stop_hit = True
                
                if stop_hit:
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.EXIT_FULL,
                        exit_reason=ExitReason.STOP_LOSS_HIT,
                        confidence=10.0,
                        urgency="HIGH",
                        quantity_percentage=100.0,
                        new_stop_loss=None,
                        new_target=None,
                        reasoning=f"Stop loss hit: Current ₹{current_price} vs Stop ₹{stop_loss}",
                        metadata={'current_price': current_price, 'stop_loss': stop_loss}
                    )
            
            # Check target hit
            if target and target > 0:
                target_hit = False
                if action == 'BUY' and current_price >= target:
                    target_hit = True
                elif action == 'SELL' and current_price <= target:
                    target_hit = True
                
                if target_hit:
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.EXIT_FULL,
                        exit_reason=ExitReason.TARGET_ACHIEVED,
                        confidence=9.0,
                        urgency="MEDIUM",
                        quantity_percentage=100.0,
                        new_stop_loss=None,
                        new_target=None,
                        reasoning=f"Target achieved: Current ₹{current_price} vs Target ₹{target}",
                        metadata={'current_price': current_price, 'target': target}
                    )
            
            # No stop/target conditions met
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="No stop loss or target conditions met",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error checking stop/target conditions: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Stop/target check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _analyze_profit_booking(self, position: Dict, current_price: float, 
                                    metrics: Dict, market_data: Dict) -> OpenPositionDecisionResult:
        """
        Analyze profit booking opportunities
        
        🚨 INTRADAY OPTIMIZED THRESHOLDS:
        - Threshold 1: 2% profit → Book 50% (if held >10 min)
        - Threshold 2: 4% profit → Book 75% immediately
        """
        try:
            pnl_percent = metrics['pnl_percent']
            age_minutes = metrics['age_minutes']
            
            # 🎯 MAJOR PROFIT: Book 75% at 4%+ profit (don't wait, intraday profits vanish quickly)
            if pnl_percent >= self.profit_booking_threshold_2:
                logger.info(f"💰 MAJOR PROFIT BOOKING: {pnl_percent:.1f}% >= {self.profit_booking_threshold_2}%")
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.PROFIT_BOOKING,
                    confidence=8.5,
                    urgency="HIGH",
                    quantity_percentage=75.0,  # Book 75% profits
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"MAJOR PROFIT: {pnl_percent:.1f}% >= {self.profit_booking_threshold_2}% → Booking 75%",
                    metadata={'pnl_percent': pnl_percent, 'threshold': self.profit_booking_threshold_2}
                )
            
            # 🎯 MODERATE PROFIT: Book 50% at 2%+ profit (if held >10 minutes)
            elif pnl_percent >= self.profit_booking_threshold_1 and age_minutes > 10:
                logger.info(f"📈 MODERATE PROFIT BOOKING: {pnl_percent:.1f}% >= {self.profit_booking_threshold_1}% after {age_minutes:.1f}min")
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.PROFIT_BOOKING,
                    confidence=7.5,
                    urgency="MEDIUM",
                    quantity_percentage=50.0,  # Book 50% profits
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"MODERATE PROFIT: {pnl_percent:.1f}% >= {self.profit_booking_threshold_1}% after {age_minutes:.0f}min → Booking 50%",
                    metadata={'pnl_percent': pnl_percent, 'age_minutes': age_minutes}
                )
            
            # No profit booking needed
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="No profit booking conditions met",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing profit booking: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Profit booking analysis error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_rsi_based_exits(self, position: Dict, current_price: float,
                                    metrics: Dict, market_data: Dict) -> OpenPositionDecisionResult:
        """
        🎯 RSI-BASED EXIT SYSTEM (NEW - KEY WIN IMPROVEMENT)
        
        Problem: Positions with RSI 90+ were being held indefinitely.
        Solution: Use RSI extremes to trigger profit booking and stop tightening.
        
        Logic:
        - LONG positions: Exit when RSI > 85 (overbought)
        - SHORT positions: Exit when RSI < 15 (oversold)
        - Extreme RSI (>90 or <10): Tighten stop to lock profits
        """
        try:
            symbol = position.get('symbol', '')
            action = metrics['action']
            pnl_percent = metrics['pnl_percent']
            entry_price = metrics['entry_price']
            
            # Extract RSI from market data (try multiple sources)
            rsi = None
            if isinstance(market_data, dict):
                rsi = market_data.get('rsi') or market_data.get('RSI')
                # Also check nested data structures
                if rsi is None and 'indicators' in market_data:
                    rsi = market_data['indicators'].get('rsi')
            
            # If RSI not in market_data, try to calculate from TrueData live data
            if rsi is None:
                try:
                    from data.truedata_client import live_market_data
                    if symbol in live_market_data:
                        symbol_data = live_market_data[symbol]
                        # Calculate RSI from OHLC if price history available
                        prices = symbol_data.get('price_history', [])
                        if not prices and 'ltp' in symbol_data:
                            # Use current day's range to estimate RSI
                            ltp = float(symbol_data.get('ltp', 0))
                            open_price = float(symbol_data.get('open', ltp))
                            high = float(symbol_data.get('high', ltp))
                            low = float(symbol_data.get('low', ltp))
                            
                            if open_price > 0 and ltp > 0:
                                # Estimate RSI based on position in day's range
                                day_range = high - low
                                if day_range > 0:
                                    position_in_range = (ltp - low) / day_range
                                    # Map position to approximate RSI (0-100)
                                    # At low = RSI ~30, at high = RSI ~70, linear interpolation
                                    rsi = 30 + (position_in_range * 40)
                                    
                                    # Adjust for intraday momentum
                                    change_pct = ((ltp - open_price) / open_price) * 100
                                    if change_pct > 2:  # Strong up day
                                        rsi = min(95, rsi + 20)
                                    elif change_pct > 1:
                                        rsi = min(90, rsi + 10)
                                    elif change_pct < -2:  # Strong down day
                                        rsi = max(5, rsi - 20)
                                    elif change_pct < -1:
                                        rsi = max(10, rsi - 10)
                                    
                                    logger.debug(f"📊 RSI ESTIMATE: {symbol} RSI={rsi:.1f} (change={change_pct:+.2f}%)")
                except Exception as e:
                    logger.debug(f"Could not estimate RSI for {symbol}: {e}")
            
            if rsi is None:
                # Cannot determine RSI - skip RSI-based logic
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.HOLD,
                    exit_reason=None,
                    confidence=0.0,
                    urgency="LOW",
                    quantity_percentage=0.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning="RSI not available - skipping RSI-based exit check",
                    metadata={'rsi': None}
                )
            
            rsi = float(rsi)
            
            # ============= LONG POSITION RSI CHECKS =============
            if action == 'BUY':
                # EXTREME OVERBOUGHT (RSI > 90): Partial exit + tighten stop
                if rsi >= self.rsi_extreme_threshold:
                    if pnl_percent > 0:
                        # Profitable - book 50% profits
                        logger.info(f"🔴 RSI EXTREME EXIT: {symbol} RSI={rsi:.1f} > 90 with +{pnl_percent:.1f}% profit")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.EXIT_PARTIAL,
                            exit_reason=ExitReason.PROFIT_BOOKING,
                            confidence=8.5,
                            urgency="HIGH",
                            quantity_percentage=50.0,
                            new_stop_loss=current_price * 0.995,  # Tighten stop to 0.5% below
                            new_target=None,
                            reasoning=f"RSI EXTREME ({rsi:.1f}): Booking 50% profit at +{pnl_percent:.1f}% | Stop tightened",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_EXTREME_OVERBOUGHT'}
                        )
                    else:
                        # Not profitable but RSI extreme - tighten stop to minimize loss
                        logger.info(f"⚠️ RSI EXTREME: {symbol} RSI={rsi:.1f} > 90 but P&L={pnl_percent:.1f}% - Tightening stop")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.TRAIL_STOP,
                            exit_reason=None,
                            confidence=7.0,
                            urgency="MEDIUM",
                            quantity_percentage=0.0,
                            new_stop_loss=current_price * 0.99,  # 1% stop loss
                            new_target=None,
                            reasoning=f"RSI EXTREME ({rsi:.1f}): Tightening stop to minimize potential loss",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_EXTREME_PROTECT'}
                        )
                
                # OVERBOUGHT (RSI > 85): Partial exit if profitable
                elif rsi >= self.rsi_overbought_threshold:
                    if pnl_percent >= 0.5:  # At least 0.5% profit
                        logger.info(f"📈 RSI OVERBOUGHT EXIT: {symbol} RSI={rsi:.1f} > 85 with +{pnl_percent:.1f}% profit")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.EXIT_PARTIAL,
                            exit_reason=ExitReason.PROFIT_BOOKING,
                            confidence=7.5,
                            urgency="MEDIUM",
                            quantity_percentage=30.0,  # Book 30% at RSI > 85
                            new_stop_loss=entry_price * 1.002,  # Move stop to +0.2% (breakeven+)
                            new_target=None,
                            reasoning=f"RSI OVERBOUGHT ({rsi:.1f}): Booking 30% profit at +{pnl_percent:.1f}% | Stop to breakeven",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_OVERBOUGHT'}
                        )
            
            # ============= SHORT POSITION RSI CHECKS =============
            elif action == 'SELL':
                # 🔥 FIX: OVERBOUGHT AGAINST SHORT (RSI > 90): Stock rallying against short!
                # This was missing - shorts were held even when stock was screaming higher
                if rsi >= self.rsi_extreme_threshold:
                    # Stock is RALLYING against our short position - DANGER!
                    logger.warning(f"🚨 RSI AGAINST SHORT: {symbol} RSI={rsi:.1f} > 90 - Stock rallying against SHORT! P&L={pnl_percent:.1f}%")
                    if pnl_percent < -1.0:
                        # Already losing on the short - EXIT immediately
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.EXIT_FULL,
                            exit_reason=ExitReason.RISK_MANAGEMENT,
                            confidence=9.5,
                            urgency="EMERGENCY",
                            quantity_percentage=100.0,
                            new_stop_loss=None,
                            new_target=None,
                            reasoning=f"EMERGENCY SHORT EXIT: RSI={rsi:.1f} (stock rallying) + P&L={pnl_percent:.1f}% (losing)",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_AGAINST_SHORT_LOSING'}
                        )
                    else:
                        # Not losing yet but RSI extreme against short - tighten stop to 0.5%
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.TRAIL_STOP,
                            exit_reason=None,
                            confidence=8.0,
                            urgency="HIGH",
                            quantity_percentage=0.0,
                            new_stop_loss=current_price * 1.005,  # Very tight 0.5% stop above
                            new_target=None,
                            reasoning=f"SHORT WARNING: RSI={rsi:.1f} (stock rallying) - Tight stop @ ₹{current_price * 1.005:.2f}",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_AGAINST_SHORT_PROTECT'}
                        )
                
                # OVERBOUGHT (RSI > 85) against short - also dangerous
                elif rsi >= self.rsi_overbought_threshold:
                    if pnl_percent < 0:
                        logger.warning(f"⚠️ RSI WARNING SHORT: {symbol} RSI={rsi:.1f} > 85 - Stock rising against SHORT, P&L={pnl_percent:.1f}%")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.TRAIL_STOP,
                            exit_reason=None,
                            confidence=7.5,
                            urgency="MEDIUM",
                            quantity_percentage=0.0,
                            new_stop_loss=current_price * 1.01,  # 1% stop above
                            new_target=None,
                            reasoning=f"SHORT ALERT: RSI={rsi:.1f} rising against position - Tightening stop",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_AGAINST_SHORT_WARN'}
                        )
                
                # EXTREME OVERSOLD (RSI < 10): Stock dropping = GOOD for shorts, book profits
                elif rsi <= self.rsi_extreme_oversold:
                    if pnl_percent > 0:
                        logger.info(f"🔴 RSI EXTREME EXIT: {symbol} RSI={rsi:.1f} < 10 with +{pnl_percent:.1f}% profit")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.EXIT_PARTIAL,
                            exit_reason=ExitReason.PROFIT_BOOKING,
                            confidence=8.5,
                            urgency="HIGH",
                            quantity_percentage=50.0,
                            new_stop_loss=current_price * 1.005,  # Tighten stop to 0.5% above
                            new_target=None,
                            reasoning=f"RSI EXTREME OVERSOLD ({rsi:.1f}): Booking 50% profit at +{pnl_percent:.1f}%",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_EXTREME_OVERSOLD'}
                        )
                    else:
                        logger.info(f"⚠️ RSI EXTREME: {symbol} RSI={rsi:.1f} < 10 but P&L={pnl_percent:.1f}% - Tightening stop")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.TRAIL_STOP,
                            exit_reason=None,
                            confidence=7.0,
                            urgency="MEDIUM",
                            quantity_percentage=0.0,
                            new_stop_loss=current_price * 1.01,  # 1% stop loss above
                            new_target=None,
                            reasoning=f"RSI EXTREME OVERSOLD ({rsi:.1f}): Tightening stop to minimize loss",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_EXTREME_PROTECT'}
                        )
                
                # OVERSOLD (RSI < 15): Stock dropping = GOOD for shorts, book partial
                elif rsi <= self.rsi_oversold_threshold:
                    if pnl_percent >= 0.5:
                        logger.info(f"📉 RSI OVERSOLD EXIT: {symbol} RSI={rsi:.1f} < 15 with +{pnl_percent:.1f}% profit")
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.EXIT_PARTIAL,
                            exit_reason=ExitReason.PROFIT_BOOKING,
                            confidence=7.5,
                            urgency="MEDIUM",
                            quantity_percentage=30.0,
                            new_stop_loss=entry_price * 0.998,  # Move stop to breakeven-
                            new_target=None,
                            reasoning=f"RSI OVERSOLD ({rsi:.1f}): Booking 30% profit at +{pnl_percent:.1f}%",
                            metadata={'rsi': rsi, 'pnl_percent': pnl_percent, 'trigger': 'RSI_OVERSOLD'}
                        )
            
            # No RSI-based exit needed
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"RSI ({rsi:.1f}) within normal range - Continue holding",
                metadata={'rsi': rsi, 'pnl_percent': pnl_percent}
            )
            
        except Exception as e:
            logger.error(f"Error in RSI-based exit check: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"RSI check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _evaluate_position_scaling(self, position: Dict, current_price: float, 
                                       metrics: Dict, market_data: Dict, market_bias) -> OpenPositionDecisionResult:
        """Evaluate position scaling opportunities"""
        try:
            pnl_percent = metrics['pnl_percent']
            age_minutes = metrics['age_minutes']
            action = metrics['action']
            
            # Only scale if position is profitable and young
            if pnl_percent < self.scale_in_profit_threshold or age_minutes > 30:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.HOLD,
                    exit_reason=None,
                    confidence=0.0,
                    urgency="LOW",
                    quantity_percentage=0.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning="Position scaling conditions not met",
                    metadata={}
                )
            
            # Check market bias alignment for scaling
            if market_bias:
                try:
                    bias_direction = getattr(market_bias.current_bias, 'direction', 'NEUTRAL')
                    bias_confidence = getattr(market_bias.current_bias, 'confidence', 0.0)
                    
                    # Only scale if bias is aligned and strong
                    bias_aligned = (
                        (bias_direction == "BULLISH" and action == "BUY") or
                        (bias_direction == "BEARISH" and action == "SELL")
                    )
                    
                    if bias_aligned and bias_confidence > 7.0:
                        return OpenPositionDecisionResult(
                            action=OpenPositionAction.SCALE_IN,
                            exit_reason=None,
                            confidence=7.0,
                            urgency="MEDIUM",
                            quantity_percentage=self.max_scale_percentage,
                            new_stop_loss=None,
                            new_target=None,
                            reasoning=f"Scale position: {pnl_percent:.1f}% profit, bias aligned ({bias_direction})",
                            metadata={
                                'pnl_percent': pnl_percent,
                                'bias_direction': bias_direction,
                                'bias_confidence': bias_confidence
                            }
                        )
                except Exception as bias_error:
                    logger.debug(f"Market bias check failed during scaling: {bias_error}")
            
            # No scaling conditions met
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="Scaling conditions not met",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error evaluating position scaling: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Scaling evaluation error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_trailing_stop_adjustments(self, position: Dict, current_price: float, 
                                             metrics: Dict) -> OpenPositionDecisionResult:
        """Check for trailing stop adjustments - BOTH profitable AND losing positions"""
        try:
            pnl_percent = metrics['pnl_percent']
            entry_price = metrics['entry_price']
            action = metrics['action']
            symbol = position.get('symbol', 'UNKNOWN')
            
            # 🔥 FIX: Get MACD and momentum data to detect reversals
            macd_state = metrics.get('macd_state', 'neutral')
            buy_pressure = metrics.get('buy_pressure', 0.5)
            sell_pressure = metrics.get('sell_pressure', 0.5)
            rsi = metrics.get('rsi', 50)
            
            # ============= MOMENTUM REVERSAL DETECTION =============
            # 🔥 NEW: Tighten stops when momentum turns AGAINST the position
            # This catches situations where buy candles appear against a SHORT
            
            if action == 'SELL':  # SHORT position
                # SHORT is in danger when:
                # 1. MACD turns bullish (buy candles appearing)
                # 2. Buy pressure > 60%
                # 3. RSI rising above 55 (momentum shifting up)
                momentum_against = (
                    macd_state == 'bullish' or 
                    buy_pressure > 0.60 or
                    (rsi > 55 and pnl_percent < 0)  # RSI rising while losing
                )
                
                if momentum_against and pnl_percent < 0:
                    # Losing SHORT with momentum against - TIGHT stop
                    tight_stop = current_price * 1.005  # 0.5% stop
                    logger.warning(f"🔄 MOMENTUM REVERSAL SHORT: {symbol} MACD={macd_state}, "
                                  f"BuyPressure={buy_pressure:.0%}, RSI={rsi:.0f}, P&L={pnl_percent:.1f}%")
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.TRAIL_STOP,
                        exit_reason=None,
                        confidence=8.5,
                        urgency="HIGH",
                        quantity_percentage=0.0,
                        new_stop_loss=tight_stop,
                        new_target=None,
                        reasoning=f"MOMENTUM REVERSAL: {symbol} SHORT losing {pnl_percent:.1f}% with bullish signals - Tight stop @ ₹{tight_stop:.2f}",
                        metadata={
                            'pnl_percent': pnl_percent,
                            'new_stop_loss': tight_stop,
                            'macd_state': macd_state,
                            'buy_pressure': buy_pressure,
                            'trigger': 'MOMENTUM_REVERSAL_SHORT'
                        }
                    )
            
            elif action == 'BUY':  # LONG position
                # LONG is in danger when:
                # 1. MACD turns bearish
                # 2. Sell pressure > 60%
                # 3. RSI falling below 45 (momentum shifting down)
                momentum_against = (
                    macd_state == 'bearish' or 
                    sell_pressure > 0.60 or
                    (rsi < 45 and pnl_percent < 0)  # RSI falling while losing
                )
                
                if momentum_against and pnl_percent < 0:
                    # Losing LONG with momentum against - TIGHT stop
                    tight_stop = current_price * 0.995  # 0.5% stop
                    logger.warning(f"🔄 MOMENTUM REVERSAL LONG: {symbol} MACD={macd_state}, "
                                  f"SellPressure={sell_pressure:.0%}, RSI={rsi:.0f}, P&L={pnl_percent:.1f}%")
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.TRAIL_STOP,
                        exit_reason=None,
                        confidence=8.5,
                        urgency="HIGH",
                        quantity_percentage=0.0,
                        new_stop_loss=tight_stop,
                        new_target=None,
                        reasoning=f"MOMENTUM REVERSAL: {symbol} LONG losing {pnl_percent:.1f}% with bearish signals - Tight stop @ ₹{tight_stop:.2f}",
                        metadata={
                            'pnl_percent': pnl_percent,
                            'new_stop_loss': tight_stop,
                            'macd_state': macd_state,
                            'sell_pressure': sell_pressure,
                            'trigger': 'MOMENTUM_REVERSAL_LONG'
                        }
                    )
            
            # ============= OPTIONS-SPECIFIC TRAILING (FULL LOT ONLY) =============
            # Options trade in lots - can't do partial exits
            # Must trail aggressively with FULL position exit when stop hit
            import re
            is_options = bool(re.search(r'\d+[CP]E$', symbol.upper())) if symbol else False
            
            if is_options:
                # 🔥 OPTIONS 10%+: VERY TIGHT 1% trail - lock in profits!
                if pnl_percent >= 10.0:
                    tight_trail = 1.0
                    if action == 'BUY':
                        new_stop = current_price * (1 - tight_trail / 100)
                    else:
                        new_stop = current_price * (1 + tight_trail / 100)
                    
                    logger.warning(f"🔥 OPTIONS BIG WINNER: {symbol} +{pnl_percent:.1f}% → 1% trail @ ₹{new_stop:.2f}")
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.TRAIL_STOP,
                        exit_reason=None,
                        confidence=9.5,
                        urgency="HIGH",
                        quantity_percentage=100.0,
                        new_stop_loss=new_stop,
                        new_target=None,
                        reasoning=f"OPTIONS WINNER: {pnl_percent:.1f}% → 1% trail @ ₹{new_stop:.2f}",
                        metadata={'pnl_percent': pnl_percent, 'new_stop_loss': new_stop, 
                                  'trail_percentage': tight_trail, 'is_options': True}
                    )
                
                # 🔥 OPTIONS 5-10%: Use 1.5% trail
                if pnl_percent >= 5.0:
                    options_trail = 1.5
                    if action == 'BUY':
                        new_stop = current_price * (1 - options_trail / 100)
                    else:
                        new_stop = current_price * (1 + options_trail / 100)
                    
                    logger.warning(f"🔥 OPTIONS TRAILING: {symbol} +{pnl_percent:.1f}% → 1.5% trail @ ₹{new_stop:.2f}")
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.TRAIL_STOP,
                        exit_reason=None,
                        confidence=9.0,
                        urgency="HIGH",
                        quantity_percentage=100.0,
                        new_stop_loss=new_stop,
                        new_target=None,
                        reasoning=f"OPTIONS TRAILING: {pnl_percent:.1f}% → 1.5% trail @ ₹{new_stop:.2f}",
                        metadata={'pnl_percent': pnl_percent, 'new_stop_loss': new_stop,
                                  'trail_percentage': options_trail, 'is_options': True}
                    )
                
                # 🔥 OPTIONS 3-5%: Early 2% trail
                if pnl_percent >= 3.0:
                    options_trail = 2.0
                    if action == 'BUY':
                        new_stop = current_price * (1 - options_trail / 100)
                    else:
                        new_stop = current_price * (1 + options_trail / 100)
                    
                    logger.info(f"📊 OPTIONS EARLY TRAIL: {symbol} +{pnl_percent:.1f}% → 2% trail @ ₹{new_stop:.2f}")
                    return OpenPositionDecisionResult(
                        action=OpenPositionAction.TRAIL_STOP,
                        exit_reason=None,
                        confidence=8.0,
                        urgency="MEDIUM",
                        quantity_percentage=100.0,
                        new_stop_loss=new_stop,
                        new_target=None,
                        reasoning=f"OPTIONS EARLY TRAIL: {pnl_percent:.1f}% → 2% trail @ ₹{new_stop:.2f}",
                        metadata={'pnl_percent': pnl_percent, 'new_stop_loss': new_stop,
                                  'trail_percentage': options_trail, 'is_options': True}
                    )
                
                # Options < 3% profit - no trailing yet
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.HOLD,
                    exit_reason=None,
                    confidence=0.0,
                    urgency="LOW",
                    quantity_percentage=0.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"OPTIONS: {pnl_percent:.1f}% < 3% activation - waiting",
                    metadata={'is_options': True, 'pnl_percent': pnl_percent}
                )
            
            # ============= STANDARD TRAILING STOP FOR EQUITY POSITIONS =============
            # Only trail if position is profitable enough
            if pnl_percent < self.trailing_stop_activation:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.HOLD,
                    exit_reason=None,
                    confidence=0.0,
                    urgency="LOW",
                    quantity_percentage=0.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning="Trailing stop activation threshold not met",
                    metadata={}
                )
            
            # Calculate trailing stop price for profitable EQUITY positions
            trail_percentage = 2.0  # 2% trailing stop for equity
            if action == 'BUY':
                new_stop = current_price * (1 - trail_percentage / 100)
            else:
                new_stop = current_price * (1 + trail_percentage / 100)
            
            return OpenPositionDecisionResult(
                action=OpenPositionAction.TRAIL_STOP,
                exit_reason=None,
                confidence=8.0,
                urgency="MEDIUM",
                quantity_percentage=0.0,
                new_stop_loss=new_stop,
                new_target=None,
                reasoning=f"EQUITY trailing: {pnl_percent:.1f}% profit, stop @ ₹{new_stop:.2f}",
                metadata={
                    'pnl_percent': pnl_percent,
                    'new_stop_loss': new_stop,
                    'trail_percentage': trail_percentage
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking trailing stop: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Trailing stop check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _analyze_market_condition_adjustments(self, position: Dict, current_price: float, 
                                                  metrics: Dict, market_data: Dict, market_bias) -> OpenPositionDecisionResult:
        """Analyze market condition based adjustments"""
        try:
            pnl_percent = metrics['pnl_percent']
            action = metrics['action']
            
            # Check for adverse market conditions
            market_volatility = abs(float(market_data.get('change_percent', 0.0)))
            volume = int(market_data.get('volume', 0))
            
            # High volatility with loss - consider exit
            if market_volatility > self.high_volatility_threshold and pnl_percent < -3.0:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_FULL,
                    exit_reason=ExitReason.MARKET_CONDITION_CHANGE,
                    confidence=7.5,
                    urgency="HIGH",
                    quantity_percentage=100.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"High volatility ({market_volatility:.1f}%) with loss ({pnl_percent:.1f}%)",
                    metadata={'volatility': market_volatility, 'pnl_percent': pnl_percent}
                )
            
            # Low volume - reduce position if profitable
            if volume < self.low_volume_threshold and pnl_percent > 5.0:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.MARKET_CONDITION_CHANGE,
                    confidence=6.5,
                    urgency="MEDIUM",
                    quantity_percentage=30.0,
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"Low volume ({volume:,}) - partial profit booking",
                    metadata={'volume': volume, 'pnl_percent': pnl_percent}
                )
            
            # No market condition adjustments needed
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning="No market condition adjustments needed",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Market condition analysis error: {str(e)}",
                metadata={'error': str(e)}
            )

# Global instance
open_position_decision_system = EnhancedOpenPositionDecision()

async def evaluate_open_position(position: Dict, current_price: float, market_data: Dict, 
                                market_bias=None, portfolio_context: Dict = None) -> OpenPositionDecisionResult:
    """
    Global function to evaluate open position decisions
    
    Returns:
        OpenPositionDecisionResult with comprehensive decision analysis
    """
    return await open_position_decision_system.evaluate_open_position(
        position, current_price, market_data, market_bias, portfolio_context
    )
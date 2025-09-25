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
        
        # PROFIT/LOSS THRESHOLDS
        self.profit_booking_threshold_1 = self.config.get('profit_booking_threshold_1', 15.0)  # 15% profit
        self.profit_booking_threshold_2 = self.config.get('profit_booking_threshold_2', 25.0)  # 25% profit
        self.stop_loss_threshold = self.config.get('stop_loss_threshold', -8.0)  # -8% loss
        self.trailing_stop_activation = self.config.get('trailing_stop_activation', 10.0)  # 10% profit
        
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
            
            # STEP 1: Calculate Position Metrics
            position_metrics = await self._calculate_position_metrics(
                position, current_price, entry_time
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
    
    async def _calculate_position_metrics(self, position: Dict, current_price: float, entry_time) -> Dict:
        """Calculate key position metrics"""
        try:
            entry_price = float(position.get('entry_price', 0.0))
            action = position.get('action', 'BUY')
            
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
            
            return {
                'pnl_percent': pnl_percent,
                'age_minutes': age_minutes,
                'risk_percent': abs(risk_percent),
                'reward_percent': abs(reward_percent),
                'risk_reward_ratio': abs(reward_percent / risk_percent) if risk_percent > 0 else 0,
                'entry_price': entry_price,
                'action': action
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
                'action': 'BUY'
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
        """Analyze profit booking opportunities"""
        try:
            pnl_percent = metrics['pnl_percent']
            age_minutes = metrics['age_minutes']
            
            # Profit booking at 25% profit
            if pnl_percent >= self.profit_booking_threshold_2:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.PROFIT_BOOKING,
                    confidence=8.5,
                    urgency="MEDIUM",
                    quantity_percentage=75.0,  # Book 75% profits
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"Major profit booking: {pnl_percent:.1f}% profit >= {self.profit_booking_threshold_2}% threshold",
                    metadata={'pnl_percent': pnl_percent, 'threshold': self.profit_booking_threshold_2}
                )
            
            # Profit booking at 15% profit (if held >30 minutes)
            elif pnl_percent >= self.profit_booking_threshold_1 and age_minutes > 30:
                return OpenPositionDecisionResult(
                    action=OpenPositionAction.EXIT_PARTIAL,
                    exit_reason=ExitReason.PROFIT_BOOKING,
                    confidence=7.5,
                    urgency="MEDIUM",
                    quantity_percentage=50.0,  # Book 50% profits
                    new_stop_loss=None,
                    new_target=None,
                    reasoning=f"Moderate profit booking: {pnl_percent:.1f}% profit after {age_minutes:.1f} minutes",
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
        """Check for trailing stop adjustments"""
        try:
            pnl_percent = metrics['pnl_percent']
            entry_price = metrics['entry_price']
            action = metrics['action']
            
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
            
            # Calculate trailing stop price
            trail_percentage = 3.0  # 3% trailing stop
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
                reasoning=f"Trailing stop adjustment: {pnl_percent:.1f}% profit, new stop ₹{new_stop:.2f}",
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

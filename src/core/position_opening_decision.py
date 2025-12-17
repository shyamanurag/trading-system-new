"""
🎯 ENHANCED POSITION OPENING DECISION SYSTEM
===========================================
Comprehensive decision framework for opening new positions with multi-layer validation,
risk assessment, and intelligent filtering to prevent poor position decisions.

COMPETITIVE ADVANTAGES:
1. Multi-layer validation prevents bad position entries
2. Dynamic confidence thresholds based on market conditions
3. Position sizing optimization using Kelly criterion
4. Real-time risk assessment and capital allocation
5. Market regime awareness for adaptive decision making
6. Comprehensive logging for decision audit trail
"""

import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pytz

# Import RiskLevel from schema
from src.models.schema import RiskLevel

logger = logging.getLogger(__name__)

class PositionDecision(Enum):
    """Position opening decision outcomes"""
    APPROVED = "APPROVED"
    REJECTED_CONFIDENCE = "REJECTED_CONFIDENCE"
    REJECTED_BIAS = "REJECTED_BIAS"
    REJECTED_RISK = "REJECTED_RISK"
    REJECTED_TIMING = "REJECTED_TIMING"
    REJECTED_CAPITAL = "REJECTED_CAPITAL"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    REJECTED_MARKET_CONDITIONS = "REJECTED_MARKET_CONDITIONS"

@dataclass
class PositionDecisionResult:
    """Result of position opening decision"""
    decision: PositionDecision
    confidence_score: float
    risk_score: float
    position_size: int
    reasoning: str
    metadata: Dict[str, Any]

class EnhancedPositionOpeningDecision:
    """
    INSTITUTIONAL-GRADE POSITION OPENING DECISION SYSTEM
    
    Implements comprehensive multi-layer validation for position opening decisions
    with dynamic thresholds, risk assessment, and intelligent filtering.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # DYNAMIC CONFIDENCE THRESHOLDS
        self.base_confidence_threshold = self.config.get('base_confidence_threshold', 7.0)
        self.high_confidence_threshold = self.config.get('high_confidence_threshold', 8.5)
        self.override_confidence_threshold = self.config.get('override_confidence_threshold', 9.0)
        
        # RISK MANAGEMENT PARAMETERS
        self.max_position_risk = self.config.get('max_position_risk', 0.02)  # 2% per position
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.10)  # 10% total
        self.max_sector_concentration = self.config.get('max_sector_concentration', 0.30)  # 30% per sector
        
        # MARKET CONDITION PARAMETERS
        self.volatility_threshold_high = self.config.get('volatility_threshold_high', 25.0)
        self.volatility_threshold_low = self.config.get('volatility_threshold_low', 10.0)
        
        # TIMING RESTRICTIONS
        self.trading_start_time = time(9, 15)  # 9:15 AM IST
        self.no_new_positions_after = time(15, 0)  # 3:00 PM IST
        self.market_close_time = time(15, 30)  # 3:30 PM IST
        
        # POSITION TRACKING
        self.recent_decisions = []
        self.max_decision_history = 1000
        
        # 🚨 DAILY LOSS LIMIT TRACKING
        self.daily_loss_limit_pct = 0.02  # 2% max loss per day (HARD LIMIT)
        self.daily_start_capital = None  # Will be set at market open
        self.daily_realized_pnl = 0.0  # Track realized P&L from closed positions
        self.daily_loss_limit_breached = False
        self.daily_loss_breach_time = None
        self.last_reset_date = None
        
    async def evaluate_position_opening(
        self, 
        signal: Dict,
        market_data: Dict,
        current_positions: Dict,
        available_capital: float,
        market_bias = None,
        risk_manager = None
    ) -> PositionDecisionResult:
        """
        Comprehensive evaluation of whether to open a new position
        
        Args:
            signal: Trading signal with all parameters
            market_data: Current market data
            current_positions: Existing positions
            available_capital: Available capital for trading
            market_bias: Market directional bias system
            risk_manager: Risk management system
            
        Returns:
            PositionDecisionResult with decision and reasoning
        """
        try:
            symbol = signal.get('symbol', '')
            action = signal.get('action', 'BUY')
            confidence = float(signal.get('confidence', 0.0))
            entry_price = float(signal.get('entry_price', 0.0))
            
            # 🚨 CRITICAL FIX: OPTIONS CAN ONLY BE BOUGHT (not sold) due to margin constraints
            # Margin for options selling is 130%+ of capital, while buying only needs premium
            is_options = symbol.upper().endswith('CE') or symbol.upper().endswith('PE')
            if is_options and action.upper() == 'SELL':
                logger.warning(f"🚫 OPTIONS SELL BLOCKED: {symbol} - Cannot SELL options (margin requirement too high)")
                logger.warning(f"   💡 Options can only be BOUGHT. Forcing BUY action.")
                action = 'BUY'  # Force BUY for options
                signal['action'] = 'BUY'  # Update the signal too
            
            logger.info(f"🎯 EVALUATING POSITION OPENING: {symbol} {action} @ ₹{entry_price} (Confidence: {confidence:.1f})")
            
            # 🚨 DATA FLOW CHECK #3: Log position evaluation context
            logger.info(f"📊 DATA FLOW CHECK #3 - Position Evaluation Context:")
            logger.info(f"   Available Capital: ₹{available_capital:,.0f}")
            logger.info(f"   Current Positions: {len(current_positions)}")
            logger.info(f"   Market Bias Available: {market_bias is not None}")
            if market_bias:
                logger.info(f"   Market Bias: {getattr(market_bias.current_bias, 'direction', 'unknown')}")
                logger.info(f"   Market Regime: {getattr(market_bias.current_bias, 'market_regime', 'unknown')}")
            
            # STEP 0: 🚨 DAILY LOSS LIMIT CHECK (CRITICAL - Check FIRST)
            daily_loss_check = await self._check_daily_loss_limit(available_capital)
            if daily_loss_check.decision != PositionDecision.APPROVED:
                return daily_loss_check
            
            # STEP 1: Basic Signal Validation
            validation_result = await self._validate_basic_signal(signal)
            if validation_result.decision != PositionDecision.APPROVED:
                return validation_result
            
            # STEP 2: Market Timing Check
            timing_result = await self._check_market_timing()
            if timing_result.decision != PositionDecision.APPROVED:
                return timing_result
            
            # STEP 3: Duplicate Position Check (with REVERSAL detection)
            duplicate_result = await self._check_duplicate_position(symbol, action, current_positions)
            if duplicate_result.decision != PositionDecision.APPROVED:
                # 🚨 Check if this is a REVERSAL signal that should trigger exit
                if duplicate_result.metadata.get('trigger_exit', False):
                    logger.warning(f"🔄 REVERSAL DETECTED: {symbol} - Will trigger exit of existing position")
                return duplicate_result
            
            # STEP 4: Market Bias Alignment (with Relative Strength)
            bias_result = await self._check_market_bias_alignment(symbol, action, confidence, market_bias, market_data)
            if bias_result.decision != PositionDecision.APPROVED:
                return bias_result
            
            # STEP 4.5: 🚨 GLOBAL RSI EXTREME CHECK - Prevents trading at extremes
            rsi_extreme_result = await self._check_rsi_extreme_filter(symbol, action, market_data)
            if rsi_extreme_result.decision != PositionDecision.APPROVED:
                return rsi_extreme_result
            
            # STEP 5: Risk Assessment
            risk_result = await self._assess_position_risk(
                signal, current_positions, available_capital, risk_manager
            )
            if risk_result.decision != PositionDecision.APPROVED:
                return risk_result
            
            # STEP 6: Market Conditions Check
            conditions_result = await self._check_market_conditions(market_data)
            if conditions_result.decision != PositionDecision.APPROVED:
                return conditions_result
            
            # STEP 7: Position Sizing Optimization
            optimal_size = await self._calculate_optimal_position_size(
                signal, available_capital, current_positions
            )
            
            # STEP 8: Final Confidence Assessment
            final_confidence = await self._calculate_final_confidence(
                signal, market_data, market_bias
            )
            
            # FINAL DECISION
            if final_confidence >= self.base_confidence_threshold:
                logger.info(f"✅ POSITION APPROVED: {symbol} {action} - Size: {optimal_size}, Confidence: {final_confidence:.1f}")
                return PositionDecisionResult(
                    decision=PositionDecision.APPROVED,
                    confidence_score=final_confidence,
                    risk_score=risk_result.risk_score,
                    position_size=optimal_size,
                    reasoning=f"All checks passed. Final confidence: {final_confidence:.1f}",
                    metadata={
                        'symbol': symbol,
                        'action': action,
                        'entry_price': entry_price,
                        'timestamp': datetime.now().isoformat(),
                        'market_conditions': 'FAVORABLE'
                    }
                )
            else:
                logger.warning(f"❌ POSITION REJECTED: {symbol} - Final confidence {final_confidence:.1f} < {self.base_confidence_threshold}")
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_CONFIDENCE,
                    confidence_score=final_confidence,
                    risk_score=0.0,
                    position_size=0,
                    reasoning=f"Final confidence {final_confidence:.1f} below threshold {self.base_confidence_threshold}",
                    metadata={'symbol': symbol, 'action': action}
                )
                
        except Exception as e:
            logger.error(f"❌ Error evaluating position opening: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Error details: {str(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=0.0,
                risk_score=10.0,
                position_size=0,
                reasoning=f"Evaluation error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_daily_loss_limit(self, available_capital: float) -> PositionDecisionResult:
        """
        🚨 CRITICAL: Check if daily loss limit (2%) has been breached
        This is the FIRST check - prevents any new trades if limit hit
        """
        try:
            from datetime import datetime, date
            import pytz
            
            ist = pytz.timezone('Asia/Kolkata')
            current_datetime = datetime.now(ist)
            current_date = current_datetime.date()
            
            # Reset daily tracking at market open (new trading day)
            if self.last_reset_date != current_date:
                logger.info(f"📅 NEW TRADING DAY: Resetting daily loss tracking")
                logger.info(f"   Previous date: {self.last_reset_date}")
                logger.info(f"   Current date: {current_date}")
                
                self.daily_start_capital = available_capital
                self.daily_realized_pnl = 0.0
                self.daily_loss_limit_breached = False
                self.daily_loss_breach_time = None
                self.last_reset_date = current_date
                
                logger.info(f"   Starting capital: ₹{self.daily_start_capital:,.2f}")
                logger.info(f"   Daily loss limit: {self.daily_loss_limit_pct*100}% = ₹{self.daily_start_capital * self.daily_loss_limit_pct:,.2f}")
            
            # If already breached, reject immediately
            # FIXED: 2025-11-14 - Return statement moved INSIDE if block
            if self.daily_loss_limit_breached:
                time_since_breach = current_datetime - self.daily_loss_breach_time if self.daily_loss_breach_time else None
                logger.error(f"🚨 DAILY LOSS LIMIT BREACHED: NO NEW POSITIONS ALLOWED")
                logger.error(f"   Breach time: {self.daily_loss_breach_time}")
                logger.error(f"   Time elapsed: {time_since_breach}")
                logger.error(f"   Total realized loss: ₹{abs(self.daily_realized_pnl):,.2f}")
                
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=0.0,
                    risk_score=10.0,  # Maximum risk
                    position_size=0,
                    reasoning=f"DAILY LOSS LIMIT BREACHED: Lost {abs(self.daily_realized_pnl):,.0f} (>{self.daily_loss_limit_pct*100}% limit). NO NEW TRADES TODAY.",
                    metadata={'risk_level': 'EXTREME'}
                )
            
            # Calculate current daily P&L
            if self.daily_start_capital is None or self.daily_start_capital == 0:
                self.daily_start_capital = available_capital
            
            # Get unrealized P&L from open positions (passed through orchestrator)
            unrealized_pnl = 0.0
            if hasattr(self, '_current_unrealized_pnl'):
                unrealized_pnl = self._current_unrealized_pnl
            
            # Total daily P&L = Realized + Unrealized
            total_daily_pnl = self.daily_realized_pnl + unrealized_pnl
            daily_pnl_pct = (total_daily_pnl / self.daily_start_capital) * 100 if self.daily_start_capital > 0 else 0.0
            
            # Calculate max allowed loss
            max_allowed_loss = self.daily_start_capital * self.daily_loss_limit_pct
            
            # Check if limit breached
            if total_daily_pnl < -max_allowed_loss:
                self.daily_loss_limit_breached = True
                self.daily_loss_breach_time = current_datetime
                
                logger.critical(f"🚨🚨🚨 DAILY LOSS LIMIT BREACHED 🚨🚨🚨")
                logger.critical(f"   Starting Capital: ₹{self.daily_start_capital:,.2f}")
                logger.critical(f"   Realized Loss: ₹{abs(self.daily_realized_pnl):,.2f}")
                logger.critical(f"   Unrealized Loss: ₹{abs(unrealized_pnl):,.2f}")
                logger.critical(f"   Total Daily Loss: ₹{abs(total_daily_pnl):,.2f} ({abs(daily_pnl_pct):.2f}%)")
                logger.critical(f"   Max Allowed Loss: ₹{max_allowed_loss:,.2f} ({self.daily_loss_limit_pct*100}%)")
                logger.critical(f"   🛑 ALL NEW TRADING HALTED FOR TODAY")
                
                # 🎯 CRITICAL FIX (2025-12-01): Return INSIDE if block, not outside!
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=0.0,
                    risk_score=10.0,  # Maximum risk
                    position_size=0,
                    reasoning=f"DAILY LOSS LIMIT BREACHED: {abs(daily_pnl_pct):.2f}% loss (limit: {self.daily_loss_limit_pct*100}%). Trading halted.",
                    metadata={'risk_level': 'EXTREME'}
                )
            
            # Log current status (approaching limit warning)
            loss_used_pct = (abs(total_daily_pnl) / max_allowed_loss) * 100 if total_daily_pnl < 0 else 0.0
            
            if total_daily_pnl < 0:
                if loss_used_pct >= 80:
                    logger.warning(f"⚠️ DAILY LOSS WARNING: {loss_used_pct:.0f}% of limit used")
                    logger.warning(f"   Current loss: ₹{abs(total_daily_pnl):,.2f} ({abs(daily_pnl_pct):.2f}%)")
                    logger.warning(f"   Remaining buffer: ₹{max_allowed_loss - abs(total_daily_pnl):,.2f}")
                elif loss_used_pct >= 50:
                    logger.info(f"📊 Daily Loss Status: {loss_used_pct:.0f}% of limit used")
            else:
                logger.info(f"✅ Daily P&L: +₹{total_daily_pnl:,.2f} ({daily_pnl_pct:.2f}%)")
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=1.0,
                risk_score=0.1,  # Low risk
                position_size=0,
                reasoning="Daily loss limit check passed",
                metadata={'risk_level': 'LOW'}
            )
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # BLOCK on error - quality over quantity
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=0.0,
                risk_score=10.0,  # Maximum risk
                position_size=0,
                reasoning=f"Daily loss limit check failed - BLOCKED for safety: {str(e)}",
                metadata={'risk_level': 'BLOCKED'}
            )
    
    async def _validate_basic_signal(self, signal: Dict) -> PositionDecisionResult:
        """Validate basic signal parameters"""
        try:
            symbol = signal.get('symbol', '')
            action = signal.get('action', '')
            confidence = signal.get('confidence', 0.0)
            entry_price = signal.get('entry_price', 0.0)
            
            # Check required fields
            if not all([symbol, action, confidence, entry_price]):
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=0.0,
                    risk_score=10.0,
                    position_size=0,
                    reasoning="Missing required signal parameters",
                    metadata={'missing_fields': [k for k, v in {'symbol': symbol, 'action': action, 'confidence': confidence, 'entry_price': entry_price}.items() if not v]}
                )
            
            # Validate confidence range
            if confidence <= 0 or confidence > 10:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_CONFIDENCE,
                    confidence_score=confidence,
                    risk_score=5.0,
                    position_size=0,
                    reasoning=f"Invalid confidence value: {confidence}",
                    metadata={'confidence': confidence}
                )
            
            # Validate entry price
            if entry_price <= 0:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=confidence,
                    risk_score=10.0,
                    position_size=0,
                    reasoning=f"Invalid entry price: {entry_price}",
                    metadata={'entry_price': entry_price}
                )
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=confidence,
                risk_score=0.0,
                position_size=0,
                reasoning="Basic validation passed",
                metadata={}
            )
            
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=0.0,
                risk_score=10.0,
                position_size=0,
                reasoning=f"Validation error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_market_timing(self) -> PositionDecisionResult:
        """Check if market timing allows new positions"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # Saturday or Sunday
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_TIMING,
                    confidence_score=0.0,
                    risk_score=0.0,
                    position_size=0,
                    reasoning=f"Market closed - Weekend ({now.strftime('%A')})",
                    metadata={'day': now.strftime('%A')}
                )
            
            # Check market hours
            if current_time < self.trading_start_time:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_TIMING,
                    confidence_score=0.0,
                    risk_score=0.0,
                    position_size=0,
                    reasoning=f"Before market open - Current: {current_time}",
                    metadata={'current_time': current_time.strftime('%H:%M:%S')}
                )
            
            if current_time >= self.no_new_positions_after:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_TIMING,
                    confidence_score=0.0,
                    risk_score=0.0,
                    position_size=0,
                    reasoning=f"No new positions after {self.no_new_positions_after} - Current: {current_time}",
                    metadata={'current_time': current_time.strftime('%H:%M:%S')}
                )
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=0.0,
                risk_score=0.0,
                position_size=0,
                reasoning="Market timing check passed",
                metadata={'current_time': current_time.strftime('%H:%M:%S')}
            )
            
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_TIMING,
                confidence_score=0.0,
                risk_score=5.0,
                position_size=0,
                reasoning=f"Timing check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_duplicate_position(self, symbol: str, action: str, current_positions: Dict) -> PositionDecisionResult:
        """
        Check for duplicate positions
        
        🚨 CRITICAL FIX: If opposite signal (SELL for BUY position), this should 
        TRIGGER EXIT, not reject as duplicate!
        
        Logic:
        - BUY signal + existing BUY position → REJECT (duplicate)
        - SELL signal + existing BUY position → TRIGGER EXIT (return special flag)
        - SELL signal + existing SELL position → REJECT (duplicate)
        - BUY signal + existing SELL position → TRIGGER EXIT (cover short)
        """
        try:
            if symbol in current_positions:
                existing_position = current_positions[symbol]
                existing_action = existing_position.get('action', 'BUY')
                
                # 🎯 CHECK: Is this an OPPOSITE signal?
                is_opposite_signal = (
                    (action == 'SELL' and existing_action == 'BUY') or
                    (action == 'BUY' and existing_action == 'SELL')
                )
                
                if is_opposite_signal:
                    # This is a REVERSAL signal - should trigger exit of existing position!
                    logger.info(f"🔄 REVERSAL SIGNAL: {symbol} has {existing_action} position, received {action} signal")
                    logger.info(f"   → This should trigger EXIT of existing {existing_action} position")
                    
                    return PositionDecisionResult(
                        decision=PositionDecision.REJECTED_DUPLICATE,  # Still reject new position
                        confidence_score=0.0,
                        risk_score=0.0,
                        position_size=0,
                        reasoning=f"REVERSAL SIGNAL: {action} for existing {existing_action} position - EXIT TRIGGERED",
                        metadata={
                            'existing_position': existing_position,
                            'trigger_exit': True,  # 🚨 Flag to trigger exit
                            'exit_reason': f'REVERSAL_SIGNAL_{action}'
                        }
                    )
                else:
                    # Same direction - true duplicate
                    return PositionDecisionResult(
                        decision=PositionDecision.REJECTED_DUPLICATE,
                        confidence_score=0.0,
                        risk_score=0.0,
                        position_size=0,
                        reasoning=f"Duplicate {action} position found for {symbol}",
                        metadata={'existing_position': existing_position, 'trigger_exit': False}
                    )
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=0.0,
                risk_score=0.0,
                position_size=0,
                reasoning="No duplicate position found",
                metadata={}
            )
            
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=0.0,
                risk_score=5.0,
                position_size=0,
                reasoning=f"Duplicate check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_market_bias_alignment(self, symbol: str, action: str, confidence: float, market_bias, market_data: Dict) -> PositionDecisionResult:
        """Check alignment with market bias including relative strength AND dual-timeframe analysis"""
        try:
            if not market_bias:
                # No market bias system - allow with moderate confidence requirement
                if confidence >= self.base_confidence_threshold:
                    return PositionDecisionResult(
                        decision=PositionDecision.APPROVED,
                        confidence_score=confidence,
                        risk_score=0.0,
                        position_size=0,
                        reasoning="No market bias system - confidence check passed",
                        metadata={'no_bias_system': True}
                    )
                else:
                    return PositionDecisionResult(
                        decision=PositionDecision.REJECTED_CONFIDENCE,
                        confidence_score=confidence,
                        risk_score=0.0,
                        position_size=0,
                        reasoning=f"No bias system - confidence {confidence:.1f} < {self.base_confidence_threshold}",
                        metadata={'no_bias_system': True}
                    )
            
            # ============= DUAL-TIMEFRAME STOCK ANALYSIS =============
            dual_timeframe_data = None
            stock_change_percent = None
            
            if market_data and symbol in market_data:
                stock_data = market_data[symbol]
                
                # 🎯 NEW: Analyze stock's dual-timeframe momentum
                # (Previous Close vs Current) AND (Today's Open vs Current)
                from strategies.base_strategy import BaseStrategy
                temp_strategy = BaseStrategy({'signal_cooldown_seconds': 1})
                temp_strategy.market_bias = market_bias  # Link for alignment check
                
                dual_timeframe_data = temp_strategy.analyze_stock_dual_timeframe(symbol, stock_data)
                
                # Extract for bias check
                stock_change_percent = dual_timeframe_data.get('day_change_pct')
                
                # Log dual-timeframe insights
                logger.info(
                    f"📊 {symbol} DUAL-TIMEFRAME CHECK:\n"
                    f"   Day: {dual_timeframe_data.get('day_change_pct', 0):+.2f}% | "
                    f"   Intraday: {dual_timeframe_data.get('intraday_change_pct', 0):+.2f}%\n"
                    f"   Pattern: {dual_timeframe_data.get('pattern', 'UNKNOWN')} | "
                    f"   Alignment: {dual_timeframe_data.get('alignment', 'UNKNOWN')}"
                )
                
                # Fallback to traditional method if dual-timeframe fails
                if stock_change_percent is None:
                    stock_change_percent = stock_data.get('change_percent') or stock_data.get('provider_change_percent')
                    if stock_change_percent is not None:
                        stock_change_percent = float(stock_change_percent)
            
            # Use market bias system with relative strength check
            if market_bias.should_allow_signal(action, confidence, symbol=symbol, stock_change_percent=stock_change_percent):
                return PositionDecisionResult(
                    decision=PositionDecision.APPROVED,
                    confidence_score=confidence,
                    risk_score=0.0,
                    position_size=0,
                    reasoning="Market bias alignment check passed",
                    metadata={'bias_direction': getattr(market_bias.current_bias, 'direction', 'UNKNOWN')}
                )
            else:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_BIAS,
                    confidence_score=confidence,
                    risk_score=0.0,
                    position_size=0,
                    reasoning=f"Market bias rejected {action} signal",
                    metadata={'bias_direction': getattr(market_bias.current_bias, 'direction', 'UNKNOWN')}
                )
                
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=confidence,
                risk_score=5.0,
                position_size=0,
                reasoning=f"Bias check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _assess_position_risk(self, signal: Dict, current_positions: Dict, available_capital: float, risk_manager) -> PositionDecisionResult:
        """Assess position risk and capital requirements
        
        🔥 INTRADAY POSITION SIZING LOGIC (2025-12-03):
        - Intraday leverage = 4x (MIS product)
        - Max loss per trade = 2% of portfolio
        - Position size = Max Loss / Stop Loss Distance
        - Example: ₹50k capital, 4x leverage = ₹2L tradeable
        - Max loss = 2% of ₹50k = ₹1000
        - SBIN @ 950, SL @ 931 (2%) → Risk/share = ₹19
        - Max shares = ₹1000 / ₹19 = 52 shares
        """
        try:
            symbol = signal.get('symbol', '')
            action = signal.get('action', 'BUY')  # Extract action from signal
            entry_price = float(signal.get('entry_price', 0.0))
            stop_loss = float(signal.get('stop_loss', 0.0))
            
            # 🔥 USE SIGNAL QUANTITY - Already calculated by base_strategy with proper sizing
            signal_quantity = int(signal.get('quantity', 0))
            if signal_quantity <= 0:
                # Fallback: calculate based on 2% risk rule
                signal_quantity = self._estimate_position_quantity(signal, available_capital)
            
            estimated_value = entry_price * signal_quantity
            
            # 🔥 INTRADAY LEVERAGE: 4x margin available for MIS
            INTRADAY_LEVERAGE = 4.0
            max_tradeable_value = available_capital * INTRADAY_LEVERAGE  # ₹50k → ₹2L
            
            # Check if position fits within leveraged capital
            if estimated_value > max_tradeable_value:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_CAPITAL,
                    confidence_score=signal.get('confidence', 0.0),
                    risk_score=10.0,
                    position_size=0,
                    reasoning=f"Position ₹{estimated_value:,.0f} exceeds 4x leverage limit ₹{max_tradeable_value:,.0f}",
                    metadata={'required_capital': estimated_value, 'max_tradeable': max_tradeable_value}
                )
            
            # 🔥 CALCULATE ACTUAL RISK (not position value!)
            # Risk = (Entry - StopLoss) × Quantity
            if stop_loss > 0 and entry_price > 0:
                risk_per_share = abs(entry_price - stop_loss)
                actual_loss_risk = risk_per_share * signal_quantity
            else:
                # Fallback: assume 2% stop loss
                actual_loss_risk = estimated_value * 0.02
            
            # 🔥 MAX LOSS PER TRADE = 2% of portfolio (not position value!)
            MAX_LOSS_PER_TRADE_PCT = 0.02  # 2%
            max_allowed_loss = available_capital * MAX_LOSS_PER_TRADE_PCT
            
            # Calculate risk as percentage of capital (based on actual loss, not position value)
            position_risk = actual_loss_risk / available_capital if available_capital > 0 else 1.0
            
            # 🚨 CRITICAL FIX: Calculate TOTAL portfolio exposure INCLUDING current positions
            total_current_exposure = 0.0
            options_exposure = 0.0
            
            if current_positions:
                for pos in current_positions.values():
                    try:
                        pos_value = abs(getattr(pos, 'average_price', 0) * getattr(pos, 'quantity', 0))
                        total_current_exposure += pos_value
                        
                        # Track options exposure separately
                        # Options have format: SYMBOL + EXPIRY + STRIKE + CE/PE (e.g., RELIANCE24DEC2700CE)
                        # MUST have digits before CE/PE to be an option (the strike price)
                        pos_symbol = getattr(pos, 'symbol', '')
                        if self._is_options_symbol(pos_symbol):
                            options_exposure += pos_value
                    except Exception as e:
                        logger.debug(f"Error calculating exposure for position {pos}: {e}")
            
            # Calculate new total exposure if this position is opened
            is_options = self._is_options_symbol(symbol)
            
            # 🔥 INTRADAY MARGIN-BASED EXPOSURE (not position value!)
            # 🚨 CRITICAL FIX: Use ACTUAL Zerodha margin, not hardcoded 25%
            # Different stocks have different margin requirements (25%-75%)
            estimated_margin = estimated_value * 0.60  # Default to 60% (conservative)
            
            # Try to get actual margin from Zerodha API
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                    zerodha_client = orchestrator.zerodha_client
                    if hasattr(zerodha_client, 'get_required_margin_for_order'):
                        action = signal.get('action', 'BUY')
                        actual_margin = zerodha_client.get_required_margin_for_order(
                            symbol=symbol,
                            quantity=signal_quantity,
                            order_type=action,
                            product='MIS'
                        )
                        if actual_margin > 0:
                            estimated_margin = actual_margin
                            logger.info(f"💰 ZERODHA MARGIN API: {symbol} x{signal_quantity} = ₹{actual_margin:,.0f}")
            except Exception as margin_err:
                logger.debug(f"Could not get Zerodha margin, using conservative 60%: {margin_err}")
            
            # Calculate current margin used (conservative estimate for existing positions)
            current_margin_used = total_current_exposure * 0.60  # Conservative 60%
            new_total_margin = current_margin_used + estimated_margin
            
            # Options margin (premium-based, not leveraged)
            options_margin = options_exposure  # Options = full premium
            new_options_margin = options_margin + (estimated_value if is_options else 0)
            
            # Express MARGIN as percentage of capital (not position value!)
            margin_used_pct = new_total_margin / available_capital if available_capital > 0 else 1.0
            options_margin_pct = new_options_margin / available_capital if available_capital > 0 else 1.0
            
            logger.info(f"📊 PORTFOLIO EXPOSURE CHECK: {symbol}")
            logger.info(f"   Position Value: ₹{estimated_value:,.0f} ({signal_quantity} × ₹{entry_price:.2f})")
            logger.info(f"   💳 Margin Required: ₹{estimated_margin:,.0f} ({margin_used_pct*100:.1f}% of capital)")
            logger.info(f"   🎯 Actual Risk: ₹{actual_loss_risk:,.0f} ({position_risk*100:.1f}% of capital)")
            logger.info(f"   Max Allowed Loss: ₹{max_allowed_loss:,.0f} (2% of ₹{available_capital:,.0f})")
            
            # 🚨 HARD LIMIT: Max 50% of capital in OPTIONS MARGIN at any time
            MAX_OPTIONS_MARGIN = 0.50  # 50%
            if options_margin_pct > MAX_OPTIONS_MARGIN:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=signal.get('confidence', 0.0),
                    risk_score=10.0,
                    position_size=0,
                    reasoning=f"🚨 OPTIONS MARGIN LIMIT: {options_margin_pct:.1%} exceeds {MAX_OPTIONS_MARGIN:.1%}",
                    metadata={
                        'options_margin_pct': options_margin_pct,
                        'max_options_margin': MAX_OPTIONS_MARGIN,
                        'current_options_margin': options_margin,
                        'new_options_margin': estimated_value if is_options else 0
                    }
                )
            
            # 🚨 HARD LIMIT: Max 80% of capital in MARGIN at any time
            # With 4x leverage, 80% margin = 320% position exposure (allows good utilization)
            MAX_MARGIN_USAGE = 0.80  # 80% of capital as margin
            if margin_used_pct > MAX_MARGIN_USAGE:
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_CAPITAL,
                    confidence_score=signal.get('confidence', 0.0),
                    risk_score=10.0,
                    position_size=0,
                    reasoning=f"🚨 MARGIN LIMIT: {margin_used_pct:.1%} exceeds {MAX_MARGIN_USAGE:.1%} (Current: ₹{current_margin_used:,.0f}, New: +₹{estimated_margin:,.0f})",
                    metadata={
                        'margin_used_pct': margin_used_pct,
                        'max_margin_usage': MAX_MARGIN_USAGE,
                        'current_margin': current_margin_used,
                        'new_margin': estimated_margin
                    }
                )
            
            # 🎯 RISK CHECK: Actual loss must be within 2% of capital
            # This allows large positions (using 4x leverage) as long as stop loss limits loss to 2%
            if actual_loss_risk > max_allowed_loss:
                trade_type = "OPTIONS" if is_options else "EQUITY"
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_RISK,
                    confidence_score=signal.get('confidence', 0.0),
                    risk_score=position_risk * 10,
                    position_size=0,
                    reasoning=f"Potential loss ₹{actual_loss_risk:,.0f} exceeds 2% limit ₹{max_allowed_loss:,.0f}",
                    metadata={
                        'actual_loss_risk': actual_loss_risk,
                        'max_allowed_loss': max_allowed_loss,
                        'position_value': estimated_value,
                        'trade_type': trade_type
                    }
                )
            
            # Use risk manager if available
            if risk_manager:
                try:
                    # Convert dictionary signal to Signal object for risk manager
                    from src.core.models import Signal, OrderSide, OptionType
                    
                    # Create Signal object from dictionary
                    signal_obj = Signal(
                        signal_id=signal.get('signal_id', f"pos_decision_{symbol}_{int(datetime.now().timestamp())}"),
                        strategy_name=signal.get('strategy', 'unknown'),
                        symbol=symbol,
                        option_type=OptionType.CALL if 'CE' in symbol else OptionType.PUT if 'PE' in symbol else OptionType.CALL,
                        strike=float(signal.get('strike', 0.0)),
                        action=OrderSide.BUY if action == 'BUY' else OrderSide.SELL,
                        quality_score=float(signal.get('confidence', 0.0)),
                        quantity=int(signal.get('quantity', 100)),
                        entry_price=entry_price,
                        stop_loss_percent=float(signal.get('stop_loss_percent', 5.0)),  # Default 5%
                        target_percent=float(signal.get('target_percent', 10.0)),  # Default 10%
                        timestamp=datetime.now(),
                        metadata=signal.get('metadata', {})
                    )
                    
                    risk_validation = await risk_manager.validate_signal(signal_obj)
                    if not risk_validation.get('approved', False):
                        return PositionDecisionResult(
                            decision=PositionDecision.REJECTED_RISK,
                            confidence_score=signal.get('confidence', 0.0),
                            risk_score=8.0,
                            position_size=0,
                            reasoning=f"Risk manager rejected: {risk_validation.get('reason', 'Unknown')}",
                            metadata={'risk_manager_result': risk_validation}
                        )
                except Exception as rm_error:
                    logger.warning(f"Risk manager check failed: {rm_error}")
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=signal.get('confidence', 0.0),
                risk_score=position_risk * 10,
                position_size=signal_quantity,
                reasoning="Risk assessment passed",
                metadata={'position_risk': position_risk, 'estimated_value': estimated_value}
            )
            
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_RISK,
                confidence_score=0.0,
                risk_score=10.0,
                position_size=0,
                reasoning=f"Risk assessment error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _check_rsi_extreme_filter(self, symbol: str, action: str, market_data: Dict) -> PositionDecisionResult:
        """
        🚨 GLOBAL RSI EXTREME FILTER - Prevents ALL strategies from trading at extremes
        
        Logic:
        - RSI < 20: Stock extremely oversold → Don't SHORT (bounce likely)
        - RSI > 80: Stock extremely overbought → Don't BUY (drop likely)
        
        This is a SAFETY filter that overrides individual strategy decisions.
        """
        try:
            # Get RSI from market_data or signal metadata
            symbol_data = market_data.get(symbol, {})
            rsi = symbol_data.get('rsi', 50.0)  # Default to neutral
            
            # If RSI not in market_data, try to calculate from price history
            if rsi == 50.0 or rsi == 0:
                # Try to get RSI from orchestrator's indicator calculation
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        # Get recent price data
                        from datetime import datetime, timedelta
                        candles = await orchestrator.zerodha_client.get_historical_data(
                            symbol=symbol,
                            interval='15minute',
                            from_date=datetime.now() - timedelta(days=2),
                            to_date=datetime.now()
                        )
                        if candles and len(candles) >= 15:
                            closes = [c.get('close', c.get('ltp', 0)) for c in candles[-15:]]
                            if len(closes) >= 14:
                                rsi = self._calculate_rsi(closes)
                                logger.debug(f"📊 RSI CALCULATED for {symbol}: {rsi:.1f}")
                except Exception as rsi_calc_err:
                    logger.debug(f"Could not calculate RSI for {symbol}: {rsi_calc_err}")
            
            # 🚨 EXTREME RSI FILTER
            RSI_EXTREME_OVERSOLD = 20.0
            RSI_EXTREME_OVERBOUGHT = 80.0
            
            # Don't SHORT when extremely oversold (bounce likely)
            if action.upper() in ['SELL', 'SHORT'] and rsi < RSI_EXTREME_OVERSOLD and rsi > 0:
                logger.warning(f"🚫 RSI EXTREME FILTER: {symbol} RSI={rsi:.1f} < {RSI_EXTREME_OVERSOLD} - BLOCKING {action} (bounce likely)")
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_MARKET_CONDITIONS,
                    confidence_score=0.0,
                    risk_score=8.0,
                    position_size=0,
                    reasoning=f"🚫 RSI EXTREME: {symbol} RSI={rsi:.1f} is extremely oversold - {action} blocked (reversal/bounce likely)",
                    metadata={'rsi': rsi, 'threshold': RSI_EXTREME_OVERSOLD, 'action_blocked': action}
                )
            
            # Don't BUY when extremely overbought (drop likely)
            if action.upper() in ['BUY', 'LONG'] and rsi > RSI_EXTREME_OVERBOUGHT:
                logger.warning(f"🚫 RSI EXTREME FILTER: {symbol} RSI={rsi:.1f} > {RSI_EXTREME_OVERBOUGHT} - BLOCKING {action} (drop likely)")
                return PositionDecisionResult(
                    decision=PositionDecision.REJECTED_MARKET_CONDITIONS,
                    confidence_score=0.0,
                    risk_score=8.0,
                    position_size=0,
                    reasoning=f"🚫 RSI EXTREME: {symbol} RSI={rsi:.1f} is extremely overbought - {action} blocked (reversal/drop likely)",
                    metadata={'rsi': rsi, 'threshold': RSI_EXTREME_OVERBOUGHT, 'action_blocked': action}
                )
            
            # RSI is in acceptable range
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=0.0,
                risk_score=0.0,
                position_size=0,
                reasoning=f"RSI {rsi:.1f} in acceptable range for {action}",
                metadata={'rsi': rsi}
            )
            
        except Exception as e:
            logger.debug(f"RSI extreme check error (allowing trade): {e}")
            # On error, allow the trade (don't block due to calculation issues)
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=0.0,
                risk_score=0.0,
                position_size=0,
                reasoning="RSI check skipped (calculation error)",
                metadata={'error': str(e)}
            )
    
    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate RSI from price list"""
        if len(prices) < period + 1:
            return 50.0  # Default neutral
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    async def _check_market_conditions(self, market_data: Dict) -> PositionDecisionResult:
        """Check overall market conditions"""
        try:
            # Check for extreme volatility
            nifty_data = market_data.get('NIFTY-I', {})
            if nifty_data:
                volatility = abs(float(nifty_data.get('change_percent', 0.0)))
                
                if volatility > self.volatility_threshold_high:
                    return PositionDecisionResult(
                        decision=PositionDecision.REJECTED_MARKET_CONDITIONS,
                        confidence_score=0.0,
                        risk_score=8.0,
                        position_size=0,
                        reasoning=f"Extreme volatility detected: {volatility:.1f}% > {self.volatility_threshold_high}%",
                        metadata={'volatility': volatility, 'threshold': self.volatility_threshold_high}
                    )
            
            return PositionDecisionResult(
                decision=PositionDecision.APPROVED,
                confidence_score=0.0,
                risk_score=0.0,
                position_size=0,
                reasoning="Market conditions check passed",
                metadata={}
            )
            
        except Exception as e:
            return PositionDecisionResult(
                decision=PositionDecision.REJECTED_MARKET_CONDITIONS,
                confidence_score=0.0,
                risk_score=5.0,
                position_size=0,
                reasoning=f"Market conditions check error: {str(e)}",
                metadata={'error': str(e)}
            )
    
    async def _calculate_optimal_position_size(self, signal: Dict, available_capital: float, current_positions: Dict) -> int:
        """Calculate optimal position size using Kelly criterion and risk management"""
        try:
            symbol = signal.get('symbol', '')
            
            # CRITICAL FIX: USE THE SIGNAL'S PRE-CALCULATED QUANTITY
            # The quantity is already calculated in base_strategy.py using:
            # - 4x intraday leverage
            # - 2% max portfolio loss per trade
            # - Proper risk/reward calculation
            # DO NOT recalculate here - it was producing much smaller quantities
            
            signal_quantity = signal.get('quantity', 0)
            
            if signal_quantity > 0:
                # Use the strategy-calculated quantity directly
                logger.info(f"📊 POSITION SIZE: Using strategy-calculated qty: {symbol} = {signal_quantity}")
                return signal_quantity
            
            # Fallback: Calculate if signal has no quantity (shouldn't happen)
            logger.warning(f"⚠️ Signal {symbol} has no quantity - falling back to estimate")
            
            # For OPTIONS (CE/PE), minimum 1 lot
            if symbol.endswith('CE') or symbol.endswith('PE'):
                logger.warning(f"⚠️ OPTIONS signal has no quantity: {symbol} - using 1")
                return 1
            
            # For EQUITY fallback, use simple allocation
            entry_price = float(signal.get('entry_price', 100.0))
            allocation_amount = available_capital * 0.10  # 10% fallback allocation
            base_size = int(allocation_amount / entry_price)
            
            # Ensure minimum viable position
            return max(base_size, 1)
            
        except Exception as e:
            logger.error(f"Error calculating optimal position size: {e}")
            return 1
    
    def _is_options_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is an options contract.
        
        Options format: SYMBOL + EXPIRY + STRIKE + CE/PE
        Examples: RELIANCE24DEC2700CE, NIFTY24DEC24000PE, BANKNIFTY24D0552000CE
        
        Key distinguisher: Options have DIGITS immediately before CE/PE (the strike price)
        Stocks like BAJFINANCE, PETRONET are NOT options even though they end with CE/PE
        """
        import re
        
        if not symbol:
            return False
        
        # Options must end with CE or PE
        if not (symbol.endswith('CE') or symbol.endswith('PE')):
            return False
        
        # Options must have digits before CE/PE (the strike price)
        # Pattern: digits + CE/PE at the end
        # This distinguishes RELIANCE24DEC2700CE (option) from BAJFINANCE (stock)
        options_pattern = r'\d+(CE|PE)$'
        return bool(re.search(options_pattern, symbol))
    
    def _estimate_position_quantity(self, signal: Dict, available_capital: float) -> int:
        """Estimate position quantity based on available capital"""
        try:
            entry_price = float(signal.get('entry_price', 100.0))
            allocation_percent = 0.05  # CRITICAL FIX: 5% per position (was 2% - too conservative)
            # With ₹50,000 capital: 5% = ₹2,500 per position (minimum viable size)
            # With 2%, positions were under ₹1,000 (too small for meaningful trading)
            
            allocation_amount = available_capital * allocation_percent
            quantity = int(allocation_amount / entry_price)
            
            return max(quantity, 1)
            
        except Exception as e:
            logger.error(f"Error estimating position quantity: {e}")
            return 1
    
    async def _calculate_final_confidence(self, signal: Dict, market_data: Dict, market_bias) -> float:
        """Calculate final confidence score with all adjustments"""
        try:
            base_confidence = float(signal.get('confidence', 0.0))
            
            # CRITICAL FIX: Normalize confidence from 0-1 scale to 0-10 scale
            # Strategies send confidence in 0-1 scale (0.9 = 90%)
            # This module expects 0-10 scale (9.0 = 90%)
            if base_confidence <= 1.0:
                base_confidence = base_confidence * 10.0
                logger.debug(f"Normalized confidence from 0-1 to 0-10 scale: {base_confidence:.1f}/10")
            
            # Market bias alignment bonus
            if market_bias and hasattr(market_bias, 'current_bias'):
                bias_confidence = getattr(market_bias.current_bias, 'confidence', 0.0)
                if bias_confidence > 5.0:
                    base_confidence += 0.5  # Small bonus for strong bias
            
            # Market conditions adjustment
            nifty_data = market_data.get('NIFTY-I', {})
            if nifty_data:
                volatility = abs(float(nifty_data.get('change_percent', 0.0)))
                if volatility > 1.0:  # High volatility
                    base_confidence += 0.3  # Bonus for volatility opportunities
            
            return min(base_confidence, 10.0)  # Cap at 10.0
            
        except Exception as e:
            logger.error(f"Error calculating final confidence: {e}")
            return signal.get('confidence', 0.0)
    
    def update_realized_pnl(self, pnl: float, symbol: str = None):
        """
        🚨 CRITICAL: Update realized P&L when a position is closed
        Called by trade_engine or position_monitor after exit orders
        
        Args:
            pnl: Realized profit/loss from closed position
            symbol: Symbol that was closed (for logging)
        """
        try:
            self.daily_realized_pnl += pnl
            
            symbol_info = f" ({symbol})" if symbol else ""
            
            if pnl > 0:
                logger.info(f"✅ Position closed with PROFIT: +₹{pnl:,.2f}{symbol_info}")
            else:
                logger.warning(f"❌ Position closed with LOSS: -₹{abs(pnl):,.2f}{symbol_info}")
            
            logger.info(f"📊 Daily Realized P&L: ₹{self.daily_realized_pnl:,.2f}")
            
            # Check if approaching or breached daily loss limit
            if self.daily_start_capital and self.daily_start_capital > 0:
                max_allowed_loss = self.daily_start_capital * self.daily_loss_limit_pct
                loss_used_pct = (abs(self.daily_realized_pnl) / max_allowed_loss) * 100 if self.daily_realized_pnl < 0 else 0.0
                
                if self.daily_realized_pnl < -max_allowed_loss:
                    logger.critical(f"🚨 DAILY LOSS LIMIT EXCEEDED: {abs(self.daily_realized_pnl):,.2f} > {max_allowed_loss:,.2f}")
                    logger.critical(f"   Trading will be halted on next signal evaluation")
                elif loss_used_pct >= 80:
                    logger.warning(f"⚠️ APPROACHING DAILY LOSS LIMIT: {loss_used_pct:.0f}% used")
                    logger.warning(f"   Remaining buffer: ₹{max_allowed_loss - abs(self.daily_realized_pnl):,.2f}")
                    
        except Exception as e:
            logger.error(f"Error updating realized P&L: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def set_unrealized_pnl(self, unrealized_pnl: float):
        """
        Update unrealized P&L from open positions
        Called by orchestrator on each market data update
        
        Args:
            unrealized_pnl: Current unrealized P&L from all open positions
        """
        try:
            self._current_unrealized_pnl = unrealized_pnl
        except Exception as e:
            logger.error(f"Error setting unrealized P&L: {e}")

# Global instance
position_decision_system = EnhancedPositionOpeningDecision()

async def evaluate_position_opening(signal: Dict, market_data: Dict, current_positions: Dict, 
                                  available_capital: float, market_bias=None, risk_manager=None) -> PositionDecisionResult:
    """
    Global function to evaluate position opening decisions
    
    Returns:
        PositionDecisionResult with comprehensive decision analysis
    """
    return await position_decision_system.evaluate_position_opening(
        signal, market_data, current_positions, available_capital, market_bias, risk_manager
    )

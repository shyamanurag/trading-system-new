"""
Market Directional Bias System
Long-term solution for coordinated position taking and eliminating market-neutral losses

This system determines intraday market bias to coordinate all trading strategies
in the same direction, preventing conflicting BUY/SELL positions that guarantee losses.
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, time, timedelta
import numpy as np
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class MarketBias:
    """Market bias data structure"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float  # 0.0 to 10.0
    nifty_momentum: float  # NIFTY change percentage
    sector_alignment: float  # -1.0 to +1.0 (sector flow alignment)
    volume_confirmation: bool  # Volume supports the bias
    time_phase: str  # OPENING, MORNING, AFTERNOON, CLOSING
    last_updated: datetime
    # Enhanced fields for better bias detection
    market_regime: str = "NORMAL"  # From market internals
    breadth_score: float = 0.0  # Market breadth strength
    stability_score: float = 0.0  # Bias stability over time
    internals_alignment: float = 0.0  # How well internals align with bias

class MarketDirectionalBias:
    """
    Core system for determining market directional bias
    
    PURPOSE: Eliminate market-neutral trading losses by coordinating
    all strategies to trade predominantly in the market direction.
    
    APPROACH:
    1. Analyze NIFTY trend and momentum
    2. Assess sectoral flow alignment
    3. Consider volume confirmation
    4. Factor in time-of-day patterns
    5. Generate coordinated trading bias
    """
    
    def __init__(self):
        # 🔥 STORE LATEST NIFTY DATA: For strategy access without orchestrator dependency
        self.nifty_data = {}  # Latest NIFTY tick data
        
        self.current_bias = MarketBias(
            direction="NEUTRAL",
            confidence=0.0,
            nifty_momentum=0.0,
            sector_alignment=0.0,
            volume_confirmation=False,
            time_phase="OPENING",
            last_updated=datetime.now()
        )
        
        # Initialize market internals analyzer
        try:
            from src.core.market_internals import MarketInternalsAnalyzer
            self.internals_analyzer = MarketInternalsAnalyzer()
            self.use_internals = True
            logger.info("✅ Market Internals integrated with Bias System")
        except ImportError:
            self.internals_analyzer = None
            self.use_internals = False
            logger.warning("⚠️ Market Internals not available, using basic bias calculation")
        
        # BIAS CALCULATION PARAMETERS
        self.nifty_trend_threshold = 0.1  # Lowered to 0.1% for more sensitivity in low-movement markets
        self.sector_alignment_threshold = 0.6  # 60% sector alignment required
        self.volume_multiplier_threshold = 1.5  # 1.5x average volume for confirmation
        self.confidence_decay_minutes = 30  # Bias confidence decays over 30 minutes
        
        # BIAS STABILITY TRACKING
        self.bias_history = deque(maxlen=10)  # Track last 10 bias calculations
        self.last_bias_change = datetime.now()
        self.min_bias_duration = timedelta(minutes=5)  # Minimum time before bias change
        self.bias_change_count = 0  # Track frequency of changes
        
        # SECTOR TRACKING
        self.major_sectors = {
            'BANKING': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN'],
            'IT': ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
            'AUTO': ['MARUTI', 'TATAMOTORS', 'BAJAJ-AUTO', 'M&M', 'HEROMOTOCO'],
            'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON'],
            'METALS': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'COALINDIA'],
            'ENERGY': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL']
        }
        
        # HISTORICAL DATA FOR TREND ANALYSIS
        self.nifty_history = []  # Last 20 data points
        self.sector_history = {}  # sector -> list of change percentages
        self.max_history = 20
        
        # 🚨 MULTI-DAY OVERBOUGHT/OVERSOLD TRACKING
        self.daily_closes = deque(maxlen=5)  # Track last 5 days' closing levels
        self.daily_changes = deque(maxlen=5)  # Track last 5 days' % changes
        self.consecutive_bullish_days = 0  # Count consecutive positive days
        self.consecutive_bearish_days = 0  # Count consecutive negative days
        self.cumulative_move_3d = 0.0  # 3-day cumulative % change
        
        # 🔥 INTRADAY MOVE EXHAUSTION TRACKING - PERCENTAGE + ATR BASED (More Rational)
        self.todays_open = None  # Track today's opening price
        self.todays_high = None  # Track today's high
        self.todays_low = None  # Track today's low
        
        # ATR tracking for volatility-adaptive zones
        self.recent_daily_ranges = deque(maxlen=10)  # Track last 10 days' ranges
        self.current_atr_percent = 0.75  # Default ATR as % of price (approx 200pts on 26000)
        
        # 🔥 PERCENTAGE-BASED ZONES (Adapts to any NIFTY level)
        # 🚨 FIX: Previous thresholds were too aggressive
        # Example at NIFTY 26,000:
        #   EARLY: 0-0.3% = 0-78 pts (fresh move)
        #   MID: 0.3-0.7% = 78-182 pts (established trend - NORMAL RANGE)
        #   EXTENDED: 0.7-1.2% = 182-312 pts (stretched but tradeable)
        #   EXTREME: >1.2% = >312 pts (actual extreme - mean reversion)
        self.move_zones_pct = {
            'EARLY': (0.0, 0.30),      # 0-0.3%: Fresh move, trend-following OK
            'MID': (0.30, 0.70),       # 0.3-0.7%: NORMAL trending - follow trend
            'EXTENDED': (0.70, 1.20),  # 0.7-1.2%: Stretched but still tradeable
            'EXTREME': (1.20, 2.50)    # >1.2%: ACTUAL extreme - mean reversion
        }
        
        # ATR-NORMALIZED ZONES (Adjusts based on recent volatility)
        # 🚨 FIX: Previous thresholds triggered "exhaustion" too early
        # If ATR is high (volatile), zones expand. If ATR is low (quiet), zones contract.
        self.atr_zone_multipliers = {
            'EARLY': (0.0, 0.40),      # 0-40% of daily ATR (fresh)
            'MID': (0.40, 0.75),       # 40-75% of daily ATR (normal trending)
            'EXTENDED': (0.75, 1.00),  # 75-100% of daily ATR (stretched)
            'EXTREME': (1.00, 1.50)    # >100% of daily ATR (beyond normal range)
        }
        
        # TIME-OF-DAY BIAS MODIFIERS
        self.time_phases = {
            'OPENING': (9, 15, 10, 0),    # 9:15-10:00 - High volatility
            'MORNING': (10, 0, 12, 0),    # 10:00-12:00 - Trend establishment
            'AFTERNOON': (12, 0, 14, 30), # 12:00-14:30 - Momentum continuation
            'CLOSING': (14, 30, 15, 30)   # 14:30-15:30 - Final moves
        }
    
    @property
    def current_regime(self) -> str:
        """Get current market regime for easy access by strategies"""
        return getattr(self.current_bias, 'market_regime', 'NORMAL')
        
    async def update_market_bias(self, market_data: Dict) -> MarketBias:
        """
        Analyze market data and update directional bias with enhanced internals
        
        Args:
            market_data: Dictionary with symbol -> price data
            
        Returns:
            Updated MarketBias object
        """
        try:
            # Get NIFTY data - try multiple symbol variants
            nifty_symbols = ['NIFTY-I', 'NIFTY 50', 'NIFTY', 'NSE:NIFTY', 'NIFTY50']
            nifty_data = None
            used_symbol = None
            
            for sym in nifty_symbols:
                nifty_data = market_data.get(sym, {})
                if nifty_data and nifty_data.get('ltp'):
                    used_symbol = sym
                    logger.debug(f"✅ Found NIFTY data using symbol: {sym}")
                    break
            
            if not nifty_data or not nifty_data.get('ltp'):
                # DEBUG: Log what symbols are available
                available_symbols = list(market_data.keys())[:20]  # First 20 symbols
                logger.warning(f"No NIFTY data available for bias calculation - tried: {nifty_symbols}")
                logger.debug(f"Available symbols (first 20): {available_symbols}")
                return self.current_bias
            
            # 🔥 STORE FOR STRATEGY ACCESS (no orchestrator dependency)
            self.nifty_data = nifty_data
            
            # Debug: Log NIFTY data to understand what we're getting
            if 'ltp' in nifty_data and 'open' in nifty_data:
                ltp = float(nifty_data.get('ltp', 0))
                open_price = float(nifty_data.get('open', 0))
                actual_change = ltp - open_price
                actual_change_pct = (actual_change / open_price * 100) if open_price > 0 else 0
                prev_close = float(
                    nifty_data.get('previous_close', 0) or
                    nifty_data.get('prev_close', 0) or
                    nifty_data.get('close', 0) or
                    0
                )
                day_change_pct = ((ltp - prev_close) / prev_close * 100) if prev_close > 0 else 0
                logger.info(f"📊 NIFTY-I: LTP={ltp:.2f}, Open={open_price:.2f}, "
                           f"Actual Change={actual_change:.2f} ({actual_change_pct:+.2f}%), "
                           f"Day Change (PrevClose→Now)={day_change_pct:+.2f}%, "
                           f"Provided day change_percent={nifty_data.get('change_percent', 'N/A')}")
            
            # 1. ANALYZE MARKET INTERNALS (if available)
            market_internals = None
            if self.use_internals and self.internals_analyzer:
                market_internals = await self.internals_analyzer.analyze_market_internals(market_data)
            
            # 2. ANALYZE NIFTY MOMENTUM
            nifty_momentum = self._analyze_nifty_momentum(nifty_data)
            
            # 🚨 2B. UPDATE MULTI-DAY TRACKING & DETECT OVERBOUGHT/OVERSOLD
            self._update_daily_tracking(nifty_data, nifty_momentum)
            is_multi_day_overbought = self._detect_multi_day_overbought()
            is_multi_day_oversold = self._detect_multi_day_oversold()
            
            # 3. CALCULATE SECTOR ALIGNMENT
            sector_alignment = self._calculate_sector_alignment(market_data)
            
            # 4. CHECK VOLUME CONFIRMATION
            volume_confirmation = self._check_volume_confirmation(nifty_data)
            
            # 5. DETERMINE TIME PHASE
            time_phase = self._get_current_time_phase()
            
            # 6. CALCULATE ENHANCED BIAS (with internals if available)
            if market_internals:
                bias_direction, confidence = self._calculate_enhanced_bias(
                    nifty_momentum, sector_alignment, volume_confirmation,
                    time_phase, market_internals, nifty_data=nifty_data
                )
                market_regime = market_internals.market_regime
                breadth_score = market_internals.advance_decline_ratio
                internals_alignment = self._calculate_internals_alignment(
                    bias_direction, market_internals
                )
            else:
                # Fallback to basic calculation
                bias_direction, confidence = self._calculate_market_bias(
                    nifty_momentum, sector_alignment, volume_confirmation, time_phase
                )
                market_regime = "NORMAL"
                breadth_score = 1.0
                internals_alignment = 0.0
            
            # 7. CHECK BIAS STABILITY
            stability_score = self._calculate_bias_stability(bias_direction)
            
            # 8. APPLY STABILITY FILTER (prevent rapid flipping)
            if not self._should_change_bias(bias_direction, confidence, stability_score):
                # Keep current bias but update metrics
                bias_direction = self.current_bias.direction
                confidence = self.current_bias.confidence * 0.95  # Slight decay
            
            # 9. 🔥 CHECK FOR INTRADAY MOVE EXHAUSTION (Points-based rubber band effect)
            exhaustion_adjustment = self._check_move_exhaustion(nifty_data, bias_direction, confidence)
            bias_direction = exhaustion_adjustment['direction']
            confidence = exhaustion_adjustment['confidence']
            move_zone = exhaustion_adjustment['zone']
            
            # Store scenario for strategies to access
            self._last_scenario = exhaustion_adjustment.get('scenario', 'UNKNOWN')
            
            # 10. ENFORCE LOW-CONFIDENCE NEUTRALIZATION
            # TUNED: Lowered from 3.0 to 1.5 to allow more trades in choppy markets
            # Exhaustion logic above already prevents bad trades in extended moves
            if confidence < 1.5:
                bias_direction = "NEUTRAL"

            # 11. UPDATE CURRENT BIAS
            self.current_bias = MarketBias(
                direction=bias_direction,
                confidence=confidence,
                nifty_momentum=nifty_momentum,
                sector_alignment=sector_alignment,
                volume_confirmation=volume_confirmation,
                time_phase=time_phase,
                last_updated=datetime.now(),
                market_regime=market_regime,
                breadth_score=breadth_score,
                stability_score=stability_score,
                internals_alignment=internals_alignment
            )
            
            # Update history
            self.bias_history.append({
                'direction': bias_direction,
                'confidence': confidence,
                'timestamp': datetime.now()
            })
            
            # Log bias update
            logger.info(f"🎯 MARKET BIAS UPDATE: {bias_direction} "
                       f"(Confidence: {confidence:.1f}/10, NIFTY: {nifty_momentum:+.2f}%, "
                       f"Regime: {market_regime}, Breadth: {breadth_score:.2f}, "
                       f"Stability: {stability_score:.1f})")
            
            return self.current_bias
            
        except Exception as e:
            logger.error(f"Error updating market bias: {e}")
            return self.current_bias
    
    def _check_move_exhaustion(self, nifty_data: Dict, bias_direction: str, confidence: float) -> Dict:
        """
        🔥 COMPREHENSIVE INTRADAY MOVE & SCENARIO ANALYSIS
        
        Handles ALL market scenarios:
        1. Gap Up + Continuation (bullish)
        2. Gap Up + Fade (bearish reversal)
        3. Gap Down + Continuation (bearish)
        4. Gap Down + Recovery (bullish reversal)
        5. Flat Open + Trending Up
        6. Flat Open + Trending Down
        7. Flat Open + Choppy/Range-bound
        8. Extended Move + Exhaustion
        9. Extreme Move + Mean Reversion
        
        Returns:
            Dict with adjusted direction, confidence, zone, and scenario
        """
        try:
            ltp = float(nifty_data.get('ltp', 0))
            open_price = float(nifty_data.get('open', 0))
            previous_close = float(nifty_data.get('previous_close', 0))
            high = float(nifty_data.get('high', ltp))
            low = float(nifty_data.get('low', ltp))
            
            if not all([ltp, open_price]):
                return {'direction': bias_direction, 'confidence': confidence, 'zone': 'UNKNOWN', 'scenario': 'UNKNOWN'}
            
            # Update today's tracking
            if self.todays_open is None or open_price != self.todays_open:
                self.todays_open = open_price
                self.todays_high = high
                self.todays_low = low
            else:
                self.todays_high = max(self.todays_high, high)
                self.todays_low = min(self.todays_low, low)
            
            # ============= CALCULATE KEY METRICS =============
            # 1. Gap from previous close to open
            gap_pct = ((open_price - previous_close) / previous_close * 100) if previous_close > 0 else 0
            gap_pts = open_price - previous_close if previous_close > 0 else 0
            
            # 2. Intraday move from open (PERCENTAGE-BASED - adapts to any NIFTY level)
            move_from_open = ltp - open_price
            abs_move_pct = abs((move_from_open / open_price) * 100) if open_price > 0 else 0
            intraday_pct = (move_from_open / open_price * 100) if open_price > 0 else 0
            
            # 3. Day change from previous close
            day_change_pct = ((ltp - previous_close) / previous_close * 100) if previous_close > 0 else 0
            
            # 4. Daily range used (ATR-NORMALIZED)
            daily_range = (self.todays_high - self.todays_low)
            daily_range_pct = (daily_range / open_price * 100) if open_price > 0 else 0
            
            # Update ATR estimate based on current day's range
            if daily_range_pct > 0:
                self.current_atr_percent = daily_range_pct  # Use current day as proxy
            
            # ATR-normalized exhaustion (how much of typical daily range used)
            range_exhaustion_pct = (abs_move_pct / self.current_atr_percent * 100) if self.current_atr_percent > 0 else 0
            
            # ============= DETERMINE MARKET SCENARIO =============
            scenario = self._identify_market_scenario(gap_pct, intraday_pct, day_change_pct, abs_move_pct)
            
            # 🔥 DETERMINE MOVE ZONE (PERCENTAGE-BASED - More Rational)
            move_zone = 'EARLY'
            for zone_name, (min_pct, max_pct) in self.move_zones_pct.items():
                if min_pct <= abs_move_pct < max_pct:
                    move_zone = zone_name
                    break
            if abs_move_pct >= 1.20:  # Catch extreme moves (>1.2% is actual extreme)
                move_zone = 'EXTREME'
            
            # Determine directions (with magnitude awareness)
            intraday_direction = 'BULLISH' if intraday_pct > 0.05 else ('BEARISH' if intraday_pct < -0.05 else 'NEUTRAL')
            day_direction = 'BULLISH' if day_change_pct > 0.05 else ('BEARISH' if day_change_pct < -0.05 else 'NEUTRAL')
            
            # ============= 🔥 MAGNITUDE-WEIGHTED CONFIDENCE =============
            # Small moves = low conviction, larger moves = higher conviction (non-linear)
            # 0.1% move → 0.3 weight, 0.4% move → 0.8 weight, 0.8%+ → 1.0 weight
            magnitude_weight = self._calculate_magnitude_weight(abs_move_pct, abs(day_change_pct))
            
            # ============= 🔥 GAP + INTRADAY INTERACTION WEIGHT =============
            # Gap up + intraday up = CONFIRMING (high weight)
            # Gap up + intraday down = FADING (moderate weight for reversal)
            # Flat + intraday move = FRESH TREND (moderate weight)
            gap_interaction_weight, interaction_type = self._calculate_gap_interaction_weight(gap_pct, intraday_pct)
            
            # ============= COMBINED WEIGHTED BIAS SCORE =============
            # Score from -10 to +10 (negative = bearish, positive = bullish)
            raw_bias_score = day_change_pct * 10  # Scale to -10/+10 range
            weighted_bias_score = raw_bias_score * magnitude_weight * gap_interaction_weight
            
            # Log weighted analysis
            logger.debug(f"📊 WEIGHT ANALYSIS: Magnitude={magnitude_weight:.2f}, Gap Interaction={gap_interaction_weight:.2f} ({interaction_type})")
            
            # ============= SCENARIO-BASED BIAS ADJUSTMENT =============
            adjusted_confidence = confidence * magnitude_weight  # Start with magnitude-weighted confidence
            adjusted_direction = bias_direction
            
            # SCENARIO 1: GAP UP + CONTINUATION (Strong Bullish)
            if scenario == 'GAP_UP_CONTINUATION':
                if bias_direction == 'BULLISH':
                    if move_zone in ['EARLY', 'MID']:
                        adjusted_confidence *= 1.25  # Strong boost for trend continuation
                        logger.info(f"🚀 {scenario}: Strong bullish trend continuation +25%")
                    else:
                        adjusted_confidence *= 0.8  # Extended, reduce confidence
                        logger.info(f"⚠️ {scenario}: Extended move, reducing +confidence -20%")
                else:
                    adjusted_confidence *= 0.5  # Heavily penalize counter-trend
                    logger.info(f"🚫 {scenario}: Counter-trend signal penalized -50%")
            
            # SCENARIO 2: GAP UP + FADE (Bearish Reversal Signal)
            elif scenario == 'GAP_UP_FADE':
                if bias_direction == 'BEARISH':
                    adjusted_confidence *= 1.3  # Gap fade = strong reversal signal
                    logger.info(f"🔄 {scenario}: Gap fade favors BEARISH +30%")
                elif bias_direction == 'BULLISH':
                    adjusted_confidence *= 0.4  # Strong penality - don't fight the fade
                    logger.info(f"⚠️ {scenario}: Gap fading, BULLISH penalized -60%")
                else:
                    adjusted_direction = 'BEARISH'
                    adjusted_confidence = max(confidence * 0.8, 3.0)
                    logger.info(f"🔄 {scenario}: Shifting to BEARISH bias")
            
            # SCENARIO 3: GAP DOWN + CONTINUATION (Strong Bearish)
            elif scenario == 'GAP_DOWN_CONTINUATION':
                if bias_direction == 'BEARISH':
                    if move_zone in ['EARLY', 'MID']:
                        adjusted_confidence *= 1.25
                        logger.info(f"📉 {scenario}: Strong bearish continuation +25%")
                    else:
                        adjusted_confidence *= 0.8
                        logger.info(f"⚠️ {scenario}: Extended, reducing confidence -20%")
                else:
                    adjusted_confidence *= 0.5
                    logger.info(f"🚫 {scenario}: Counter-trend signal penalized -50%")
            
            # SCENARIO 4: GAP DOWN + RECOVERY (Bullish Reversal Signal)
            elif scenario == 'GAP_DOWN_RECOVERY':
                # Key insight: Recovery from gap down is bullish ONLY if day turns positive
                if day_change_pct > 0:
                    # Full recovery - strong bullish
                    if bias_direction == 'BULLISH':
                        adjusted_confidence *= 1.3
                        logger.info(f"🔄 {scenario}: Full gap recovery, BULLISH +30%")
                    else:
                        adjusted_confidence *= 0.5
                        logger.info(f"⚠️ {scenario}: Gap recovered, BEARISH penalized -50%")
                else:
                    # Partial recovery - day still down, BE CAUTIOUS
                    if bias_direction == 'BULLISH':
                        adjusted_confidence *= 0.7  # Don't over-trust partial recovery
                        logger.info(f"⚠️ {scenario}: Partial recovery only (day still {day_change_pct:+.2f}%), BULLISH reduced -30%")
                    elif bias_direction == 'BEARISH':
                        adjusted_confidence *= 0.9  # Slight reduction, trend still down
                        logger.info(f"📊 {scenario}: Day still down, BEARISH slightly reduced -10%")
            
            # SCENARIO 5: FLAT OPEN + TRENDING
            elif scenario == 'FLAT_TRENDING_UP':
                if bias_direction == 'BULLISH':
                    adjusted_confidence *= 1.15 if move_zone in ['EARLY', 'MID'] else 0.85
                    logger.info(f"📈 {scenario}: Clean uptrend from flat open")
                else:
                    adjusted_confidence *= 0.6
                    logger.info(f"🚫 {scenario}: Fighting clean uptrend, penalized -40%")
            
            elif scenario == 'FLAT_TRENDING_DOWN':
                if bias_direction == 'BEARISH':
                    adjusted_confidence *= 1.15 if move_zone in ['EARLY', 'MID'] else 0.85
                    logger.info(f"📉 {scenario}: Clean downtrend from flat open")
                else:
                    adjusted_confidence *= 0.6
                    logger.info(f"🚫 {scenario}: Fighting clean downtrend, penalized -40%")
            
            # SCENARIO 6: CHOPPY / RANGE-BOUND
            elif scenario == 'CHOPPY':
                adjusted_direction = 'NEUTRAL'
                adjusted_confidence = min(confidence * 0.5, 3.0)  # Heavy reduction for choppy
                logger.info(f"🔀 {scenario}: Choppy market, forcing NEUTRAL bias (conf: {adjusted_confidence:.1f})")
            
            # SCENARIO 7: MIXED SIGNALS
            elif scenario == 'MIXED_SIGNALS':
                adjusted_confidence *= 0.7  # Reduce confidence for unclear scenarios
                logger.info(f"⚠️ {scenario}: Mixed signals, reducing confidence -30%")
            
            # ============= MOVE ZONE ADJUSTMENTS (overlayed on scenario) =============
            if move_zone == 'EXTENDED' and adjusted_direction == intraday_direction:
                adjusted_confidence *= 0.75  # Additional penalty for chasing extended moves
                logger.info(f"📏 EXTENDED ZONE ({abs_move_pct:.2f}%): Additional -25% for trend-chasing")
            
            elif move_zone == 'EXTREME':
                if adjusted_direction == intraday_direction:
                    # DON'T chase extreme moves - force mean reversion
                    opposite_direction = 'BEARISH' if intraday_direction == 'BULLISH' else 'BULLISH'
                    adjusted_direction = opposite_direction
                    adjusted_confidence = min(confidence * 0.6, 5.0)
                    logger.warning(f"🔴 EXTREME ZONE ({abs_move_pct:.2f}%): Forcing {adjusted_direction} mean reversion")
                else:
                    adjusted_confidence *= 1.2  # Boost mean reversion in extreme zone
                    logger.info(f"✅ EXTREME ZONE ({abs_move_pct:.2f}%): Mean reversion boost +20%")
            
            # ============= RANGE EXHAUSTION CHECK =============
            # 🚨 FIX: 85% was too aggressive - 100% ATR is NORMAL on trending days
            if range_exhaustion_pct > 100:  # Beyond typical daily ATR
                if adjusted_direction == intraday_direction:
                    adjusted_confidence *= 0.75  # Moderate penalty (was 0.5)
                    logger.warning(f"📏 RANGE EXCEEDED ({range_exhaustion_pct:.0f}%): Trend-chasing penalized -25%")
                else:
                    adjusted_confidence *= 1.15
                    logger.info(f"📏 RANGE EXCEEDED ({range_exhaustion_pct:.0f}%): Mean reversion favored +15%")
            elif range_exhaustion_pct > 90:
                # High usage but normal for trending day - just log, no penalty
                logger.info(f"📏 HIGH RANGE ({range_exhaustion_pct:.0f}%): Normal for trending day")
            
            # ============= FINAL CONFIDENCE BOUNDS =============
            adjusted_confidence = max(0.0, min(10.0, adjusted_confidence))
            
            # Log comprehensive analysis (PERCENTAGE-BASED)
            logger.info(f"📊 MOVE ANALYSIS: Gap={gap_pct:+.2f}% | Intraday={intraday_pct:+.2f}% | Day={day_change_pct:+.2f}% | "
                       f"Zone={move_zone} | Scenario={scenario} | "
                       f"Move: {abs_move_pct:.2f}% (ATR used: {range_exhaustion_pct:.0f}%) | "
                       f"Final Bias: {adjusted_direction} @ {adjusted_confidence:.1f}/10")
            
            return {
                'direction': adjusted_direction,
                'confidence': adjusted_confidence,
                'zone': move_zone,
                'scenario': scenario
            }
            
        except Exception as e:
            logger.error(f"Error in move exhaustion check: {e}")
            return {'direction': bias_direction, 'confidence': confidence, 'zone': 'ERROR', 'scenario': 'ERROR'}
    
    def _calculate_magnitude_weight(self, abs_move_pct: float, abs_day_change_pct: float) -> float:
        """
        🔥 MAGNITUDE-WEIGHTED CONFIDENCE
        
        Small moves should have LOW conviction, larger moves should have HIGHER conviction.
        Uses non-linear scaling to prevent both:
        - Taking weak signals (0.1% move shouldn't trigger high-confidence trades)
        - Over-weighting extreme moves (diminishing returns after 0.6%)
        
        Returns: 0.0 to 1.0 weight
        
        Scale:
          0.0% - 0.10%: 0.2 weight (very weak, barely directional)
          0.10% - 0.20%: 0.4 weight (weak but directional)
          0.20% - 0.35%: 0.6 weight (moderate, tradeable)
          0.35% - 0.50%: 0.8 weight (strong signal)
          0.50%+: 1.0 weight (very strong, but watch for exhaustion)
        """
        # Use the larger of intraday move or day change
        max_move = max(abs_move_pct, abs_day_change_pct)
        
        if max_move < 0.10:
            weight = 0.2  # Very weak - nearly flat
        elif max_move < 0.20:
            weight = 0.4  # Weak but directional  
        elif max_move < 0.35:
            weight = 0.6  # Moderate - tradeable
        elif max_move < 0.50:
            weight = 0.8  # Strong signal
        else:
            weight = 1.0  # Very strong
        
        return weight
    
    def _calculate_gap_interaction_weight(self, gap_pct: float, intraday_pct: float) -> tuple:
        """
        🔥 GAP + INTRADAY INTERACTION ANALYSIS
        
        The relationship between gap direction and subsequent intraday movement
        is crucial for understanding bias strength.
        
        Returns: (weight: float, interaction_type: str)
        
        Scenarios:
        1. CONFIRMING (high weight): Gap and intraday same direction
           - Gap up + Intraday up = Strong bullish (1.2x weight)
           - Gap down + Intraday down = Strong bearish (1.2x weight)
        
        2. FADING (moderate weight for reversal): Gap filled
           - Gap up + Intraday down = Bearish reversal (1.0x weight for shorts)
           - Gap down + Intraday up = Bullish reversal (1.0x weight for longs)
        
        3. FLAT START (neutral weight): No gap, fresh trend
           - Flat + Intraday move = Fresh signal (0.9x weight)
        
        4. CHOPPY (low weight): Mixed signals
           - Gap one way, intraday flat = Low conviction (0.6x weight)
        """
        GAP_THRESHOLD = 0.15  # 0.15% gap is meaningful
        INTRADAY_THRESHOLD = 0.08  # 0.08% intraday move is meaningful
        
        has_gap_up = gap_pct > GAP_THRESHOLD
        has_gap_down = gap_pct < -GAP_THRESHOLD
        is_flat_gap = abs(gap_pct) <= GAP_THRESHOLD
        
        is_intraday_up = intraday_pct > INTRADAY_THRESHOLD
        is_intraday_down = intraday_pct < -INTRADAY_THRESHOLD
        is_intraday_flat = abs(intraday_pct) <= INTRADAY_THRESHOLD
        
        # CONFIRMING: Gap and intraday same direction
        if (has_gap_up and is_intraday_up) or (has_gap_down and is_intraday_down):
            return 1.2, "CONFIRMING"
        
        # FADING: Gap being filled (reversal signal)
        if (has_gap_up and is_intraday_down) or (has_gap_down and is_intraday_up):
            return 1.0, "FADING"
        
        # FLAT START: No gap, fresh trend developing
        if is_flat_gap and (is_intraday_up or is_intraday_down):
            return 0.9, "FRESH_TREND"
        
        # CHOPPY: Gap but no follow-through
        if (has_gap_up or has_gap_down) and is_intraday_flat:
            return 0.6, "STALLED"
        
        # DEAD FLAT: No movement at all
        if is_flat_gap and is_intraday_flat:
            return 0.3, "FLAT"
        
        return 0.7, "MIXED"
    
    def _identify_market_scenario(self, gap_pct: float, intraday_pct: float, day_change_pct: float, abs_move_pct: float) -> str:
        """
        Identify the current market scenario based on gap, intraday, and day movements.
        
        🔥 PERCENTAGE-BASED (Adapts to any NIFTY level)
        
        Returns one of:
        - GAP_UP_CONTINUATION: Gap up and continuing higher
        - GAP_UP_FADE: Gap up but fading (selling into strength)
        - GAP_DOWN_CONTINUATION: Gap down and continuing lower
        - GAP_DOWN_RECOVERY: Gap down but recovering (RUBBER BAND!)
        - RUBBER_BAND_RECOVERY: Strong snap-back from extended move
        - FLAT_TRENDING_UP: Flat open, trending higher
        - FLAT_TRENDING_DOWN: Flat open, trending lower
        - CHOPPY: No clear direction, range-bound
        - MIXED_SIGNALS: Conflicting signals
        
        🔥 RUBBER BAND DETECTION:
        - Extended move: >0.4% from open (approx 100 pts at NIFTY 26000)
        - Reversal sign: intraday_pct direction opposite to gap_pct
        """
        GAP_THRESHOLD = 0.25  # 0.25% gap is significant
        TREND_THRESHOLD = 0.10  # 0.10% intraday move is trending
        RUBBER_BAND_PCT = 0.40  # 0.4% move from open is extended (≈100 pts at 26000)
        CHOPPY_THRESHOLD = 0.12  # <0.12% move is choppy (≈30 pts at 26000)
        
        has_gap_up = gap_pct > GAP_THRESHOLD
        has_gap_down = gap_pct < -GAP_THRESHOLD
        is_flat_open = abs(gap_pct) <= GAP_THRESHOLD
        
        is_trending_up = intraday_pct > TREND_THRESHOLD
        is_trending_down = intraday_pct < -TREND_THRESHOLD
        is_flat_intraday = abs(intraday_pct) <= TREND_THRESHOLD
        
        # 🔥 RUBBER BAND DETECTION - Extended move reversing (PERCENTAGE-BASED)
        is_extended_move = abs_move_pct > RUBBER_BAND_PCT
        
        # Check for rubber band snap-back
        if is_extended_move:
            # Gap down + intraday up = rubber band recovery
            if has_gap_down and intraday_pct > 0.05:
                logger.info(f"🎯 RUBBER BAND DETECTED: Gap {gap_pct:.2f}% + Intraday {intraday_pct:+.2f}% = SNAP-BACK RECOVERY")
                return 'RUBBER_BAND_RECOVERY'
            # Gap up + intraday down = rubber band fade
            elif has_gap_up and intraday_pct < -0.05:
                logger.info(f"🎯 RUBBER BAND DETECTED: Gap {gap_pct:.2f}% + Intraday {intraday_pct:+.2f}% = SNAP-BACK FADE")
                return 'RUBBER_BAND_FADE'
        
        # GAP UP scenarios
        if has_gap_up:
            if is_trending_up or (is_flat_intraday and day_change_pct > GAP_THRESHOLD):
                return 'GAP_UP_CONTINUATION'
            elif is_trending_down:
                return 'GAP_UP_FADE'
            else:
                return 'MIXED_SIGNALS'
        
        # GAP DOWN scenarios
        elif has_gap_down:
            if is_trending_down or (is_flat_intraday and day_change_pct < -GAP_THRESHOLD):
                return 'GAP_DOWN_CONTINUATION'
            elif is_trending_up:
                return 'GAP_DOWN_RECOVERY'
            # Even slight positive is early recovery sign after gap down
            elif intraday_pct > 0.05 and abs(gap_pct) > 0.4:
                logger.info(f"📈 EARLY RECOVERY: Gap {gap_pct:.2f}% but intraday {intraday_pct:+.2f}% positive")
                return 'GAP_DOWN_EARLY_RECOVERY'
            else:
                return 'MIXED_SIGNALS'
        
        # FLAT OPEN scenarios
        elif is_flat_open:
            if is_trending_up:
                return 'FLAT_TRENDING_UP'
            elif is_trending_down:
                return 'FLAT_TRENDING_DOWN'
            elif is_flat_intraday and abs_move_pct < CHOPPY_THRESHOLD:
                return 'CHOPPY'
            else:
                return 'MIXED_SIGNALS'
        
        return 'MIXED_SIGNALS'
    
    def _analyze_nifty_momentum(self, nifty_data: Dict) -> float:
        """
        DUAL-TIMEFRAME MOMENTUM ANALYSIS
        Calculates BOTH day change (prev close → current) AND intraday change (open → current)
        Combines them to detect: gap fades, reversals, continuations, choppy action
        """
        try:
            ltp = float(nifty_data.get('ltp', 0))
            if ltp <= 0:
                return 0.0
            
            # ============= CALCULATE DAY CHANGE (Previous Close → Current) =============
            day_change_pct = 0.0
            previous_close = float(nifty_data.get('previous_close', 0))
            
            if previous_close > 0:
                day_change_pct = ((ltp - previous_close) / previous_close) * 100
            elif 'change_percent' in nifty_data:
                day_change_pct = float(nifty_data['change_percent'])
            
            # ============= CALCULATE INTRADAY CHANGE (Open → Current) =============
            intraday_change_pct = 0.0
            open_price = float(nifty_data.get('open', 0))
            
            if open_price > 0:
                intraday_change_pct = ((ltp - open_price) / open_price) * 100
            
            # ============= DETECT GAP & REVERSAL PATTERNS =============
            gap_open_pct = 0.0
            if previous_close > 0 and open_price > 0:
                gap_open_pct = ((open_price - previous_close) / previous_close) * 100
            
            # Pattern detection
            pattern = self._detect_market_pattern(day_change_pct, intraday_change_pct, gap_open_pct)
            
            # ============= CALCULATE WEIGHTED BIAS =============
            # Day change = 60% weight (overall trend)
            # Intraday change = 40% weight (current momentum)
            weighted_change = (day_change_pct * 0.6) + (intraday_change_pct * 0.4)
            
            # Log comprehensive analysis
            logger.info(
                f"📊 NIFTY DUAL-TIMEFRAME ANALYSIS:\n"
                f"   LTP: {ltp:.2f} | Prev Close: {previous_close:.2f} | Open: {open_price:.2f}\n"
                f"   📈 Day Change: {day_change_pct:+.2f}% (Prev Close → Now)\n"
                f"   ⚡ Intraday: {intraday_change_pct:+.2f}% (Open → Now)\n"
                f"   🎯 Gap at Open: {gap_open_pct:+.2f}%\n"
                f"   🔍 Pattern: {pattern}\n"
                f"   ⚖️  Weighted Bias: {weighted_change:+.2f}% (60% day, 40% intraday)"
            )
            
            # Store for strategies to access
            self.nifty_data = {
                'ltp': ltp,
                'day_change_pct': day_change_pct,
                'intraday_change_pct': intraday_change_pct,
                'gap_open_pct': gap_open_pct,
                'pattern': pattern,
                'weighted_bias': weighted_change
            }
            
            # Update history
            self._update_nifty_history(weighted_change, ltp)
            
            return weighted_change
            
        except Exception as e:
            logger.error(f"Error in dual-timeframe NIFTY analysis: {e}")
            return 0.0
    
    def _detect_market_pattern(self, day_change: float, intraday_change: float, gap_pct: float) -> str:
        """
        Detect market patterns based on day vs intraday movement
        Returns: Pattern description for logging and decision making
        """
        try:
            # Both positive = Bullish continuation
            if day_change > 0.2 and intraday_change > 0.15:
                return "BULLISH CONTINUATION"
            
            # Both negative = Bearish continuation
            if day_change < -0.2 and intraday_change < -0.15:
                return "BEARISH CONTINUATION"
            
            # Gap down but recovering = Potential reversal
            if gap_pct < -0.3 and intraday_change > 0.2:
                recovery_pct = abs(intraday_change / gap_pct) * 100 if gap_pct != 0 else 0
                return f"GAP DOWN RECOVERY ({recovery_pct:.0f}% recovered)"
            
            # Gap up but fading = Weakness
            if gap_pct > 0.3 and intraday_change < -0.2:
                fade_pct = abs(intraday_change / gap_pct) * 100 if gap_pct != 0 else 0
                return f"GAP UP FADE ({fade_pct:.0f}% faded)"
            
            # Day bearish but intraday bullish = Intraday reversal attempt
            if day_change < -0.2 and intraday_change > 0.15:
                return "INTRADAY BULLISH REVERSAL"
            
            # Day bullish but intraday bearish = Losing momentum
            if day_change > 0.2 and intraday_change < -0.15:
                return "INTRADAY WEAKNESS"
            
            # Low movement = Choppy
            if abs(day_change) < 0.15 and abs(intraday_change) < 0.15:
                return "CHOPPY/RANGE-BOUND"
            
            # Default
            return "MIXED SIGNALS"
            
        except Exception as e:
            logger.error(f"Error detecting pattern: {e}")
            return "UNKNOWN"
    
    def _update_nifty_history(self, weighted_change: float, ltp: float):
        """Update NIFTY history with weighted change"""
        try:
            # Update NIFTY history
            self.nifty_history.append({
                'change_percent': weighted_change,
                'ltp': ltp,
                'timestamp': datetime.now()
            })
            
            # Keep only recent history
            if len(self.nifty_history) > self.max_history:
                self.nifty_history = self.nifty_history[-self.max_history:]
                
        except Exception as e:
            logger.warning(f"Error updating NIFTY history: {e}")

    def _analyze_gap_component(self, nifty_data: Dict) -> float:
        """Analyze overnight gap: today open vs yesterday close (percent)"""
        try:
            open_price = float(nifty_data.get('open', 0))
            prev_close = float(nifty_data.get('prev_close', 0))
            if prev_close > 0 and open_price > 0 and open_price != prev_close:
                gap_pct = ((open_price - prev_close) / prev_close) * 100.0
                return round(gap_pct, 3)
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_sector_alignment(self, market_data: Dict) -> float:
        """Calculate how aligned sectors are with market direction"""
        try:
            sector_scores = {}
            
            for sector_name, symbols in self.major_sectors.items():
                sector_changes = []
                
                for symbol in symbols:
                    symbol_data = market_data.get(symbol, {})
                    if symbol_data:
                        change_percent = float(symbol_data.get('change_percent', 0))
                        sector_changes.append(change_percent)
                
                if sector_changes:
                    # Calculate sector average change
                    sector_avg = np.mean(sector_changes)
                    sector_scores[sector_name] = sector_avg
                    
                    # Update sector history
                    if sector_name not in self.sector_history:
                        self.sector_history[sector_name] = []
                    
                    self.sector_history[sector_name].append(sector_avg)
                    if len(self.sector_history[sector_name]) > self.max_history:
                        self.sector_history[sector_name] = self.sector_history[sector_name][-self.max_history:]
            
            if not sector_scores:
                return 0.0
            
            # Calculate overall sectoral alignment
            positive_sectors = sum(1 for score in sector_scores.values() if score > 0.1)
            negative_sectors = sum(1 for score in sector_scores.values() if score < -0.1)
            total_sectors = len(sector_scores)
            
            if total_sectors == 0:
                return 0.0
            
            # Calculate alignment score (-1 to +1)
            if positive_sectors > negative_sectors:
                alignment = (positive_sectors - negative_sectors) / total_sectors
            else:
                alignment = -(negative_sectors - positive_sectors) / total_sectors
            
            return alignment
            
        except Exception as e:
            logger.warning(f"Error calculating sector alignment: {e}")
            return 0.0
    
    def _check_volume_confirmation(self, nifty_data: Dict) -> bool:
        """Check if volume confirms the price movement"""
        try:
            volume = float(nifty_data.get('volume', 0))
            change_percent = abs(float(nifty_data.get('change_percent', 0)))
            
            # Calculate expected volume based on price change magnitude
            # Higher price changes should have higher volume
            expected_volume_multiplier = 1 + (change_percent / 100) * 2  # 2% change = 2x volume
            
            # Simple heuristic: If volume is above 1.5M for NIFTY with significant move
            if change_percent > 0.2 and volume > 1500000:
                return True
            elif change_percent > 0.5 and volume > 1000000:
                return True
            else:
                return False
                
        except Exception as e:
            logger.warning(f"Error checking volume confirmation: {e}")
            return False
    
    def _get_current_time_phase(self) -> str:
        """Determine current market time phase"""
        try:
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            for phase_name, (start_hour, start_min, end_hour, end_min) in self.time_phases.items():
                start_time = time(start_hour, start_min)
                end_time = time(end_hour, end_min)
                
                if start_time <= current_time <= end_time:
                    return phase_name
            
            return "CLOSED"
            
        except Exception as e:
            logger.warning(f"Error determining time phase: {e}")
            return "UNKNOWN"
    
    def _calculate_market_bias(self, nifty_momentum: float, sector_alignment: float, 
                             volume_confirmation: bool, time_phase: str) -> Tuple[str, float]:
        """Calculate overall market bias and confidence"""
        try:
            # BASE BIAS DETERMINATION
            bias_direction = "NEUTRAL"
            confidence = 0.0
            
            # MOMENTUM ANALYSIS
            if abs(nifty_momentum) >= self.nifty_trend_threshold:
                if nifty_momentum > 0:
                    bias_direction = "BULLISH"
                else:
                    bias_direction = "BEARISH"
                
                # Base confidence from momentum strength
                confidence = min(abs(nifty_momentum) * 3, 7.0)  # Max 7/10 from momentum
            
            # SECTOR ALIGNMENT BOOST
            if abs(sector_alignment) >= self.sector_alignment_threshold:
                if (bias_direction == "BULLISH" and sector_alignment > 0) or \
                   (bias_direction == "BEARISH" and sector_alignment < 0):
                    # Aligned sectors boost confidence
                    confidence += abs(sector_alignment) * 2.0  # Up to +2.0
                elif bias_direction != "NEUTRAL":
                    # Misaligned sectors reduce confidence
                    confidence *= 0.7
            
            # VOLUME CONFIRMATION BOOST
            if volume_confirmation and bias_direction != "NEUTRAL":
                confidence += 1.0  # +1.0 for volume confirmation
            
            # TIME PHASE MODIFIER
            time_multiplier = self._get_time_phase_multiplier(time_phase)
            confidence *= time_multiplier
            
            # CAP CONFIDENCE
            confidence = min(confidence, 10.0)
            confidence = max(confidence, 0.0)
            
            # BIAS THRESHOLD CHECK
            # 🚨 FIX: 3.0 was too high - 0.6% clear uptrend (confidence ~2.0) was being neutralized
            # A 0.3% move should at minimum establish directional bias
            if confidence < 1.5:  # Lowered from 3.0 - only truly uncertain moves become NEUTRAL
                bias_direction = "NEUTRAL"
                confidence = 0.0
            
            # NEW: Debug for index trading
            if 'NIFTY' in time_phase or 'BANKNIFTY' in time_phase:  # Example check - adjust as needed
                logger.info(f"🔍 INDEX BIAS DEBUG: Momentum={nifty_momentum}%, Threshold={self.nifty_trend_threshold}%, Direction={bias_direction}")
            
            return bias_direction, confidence
            
        except Exception as e:
            logger.error(f"Error calculating market bias: {e}")
            return "NEUTRAL", 0.0
    
    def _get_time_phase_multiplier(self, time_phase: str) -> float:
        """Get confidence multiplier based on time phase"""
        multipliers = {
            'OPENING': 1.2,    # Opening volatility is reliable
            'MORNING': 1.0,    # Standard reliability  
            'AFTERNOON': 0.9,  # Slightly less reliable
            'CLOSING': 1.1,    # Closing moves are meaningful
            'CLOSED': 0.0      # No trading
        }
        return multipliers.get(time_phase, 0.5)
    
    def _calculate_trend_consistency(self, recent_changes: List[float]) -> float:
        """Calculate how consistent the recent trend is"""
        if len(recent_changes) < 3:
            return 0.0
        
        # Check if all changes are in same direction
        positive_count = sum(1 for x in recent_changes if x > 0)
        negative_count = sum(1 for x in recent_changes if x < 0)
        
        total_count = len(recent_changes)
        consistency = max(positive_count, negative_count) / total_count
        
        return consistency - 0.5  # 0.5 to 0.5 range, where 0.5 = all same direction
    
    def should_allow_signal(self, signal_direction: str, signal_confidence: float, symbol: str = None, 
                          stock_change_percent: float = None) -> bool:
        """
        Determine if a signal should be allowed based on market bias with RELATIVE STRENGTH
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            signal_confidence: Signal confidence (0-10)
            symbol: Trading symbol (optional, used to identify index vs stock)
            stock_change_percent: Stock's % change (for relative strength check)
            
        Returns:
            True if signal should be allowed, False if it should be rejected
        """
        try:
            # CRITICAL FIX: Normalize confidence to 0-10 scale
            # Strategies send confidence in 0-1 scale (0.85 = 85%)
            # Market bias expects 0-10 scale (8.5 = 85%)
            if signal_confidence <= 1.0:
                # Convert from 0-1 scale to 0-10 scale
                signal_confidence = signal_confidence * 10.0
                logger.debug(f"Normalized confidence from 0-1 scale to 0-10 scale: {signal_confidence:.1f}/10")
            elif signal_confidence > 10:
                # Handle percentage scale (85 = 85%)
                logger.debug(f"Normalizing confidence from percentage: {signal_confidence} → {signal_confidence/10}")
                signal_confidence = signal_confidence / 10.0
            
            # Regime-aware thresholds
            regime = getattr(self.current_bias, 'market_regime', 'NORMAL')
            # Make counter-trend overrides harder in choppy/sideways days
            override_threshold = 8.5  # REDUCED from 9.7/9.9 to allow more signals through
            neutral_threshold = 6.5 if regime in ('CHOPPY', 'VOLATILE_CHOPPY') else 6.5

            # HIGH CONFIDENCE OVERRIDE: Allow counter-trend for very strong signals (regime aware)
            if signal_confidence >= override_threshold:
                logger.info(f"🎯 HIGH CONFIDENCE OVERRIDE: {signal_direction} allowed (confidence={signal_confidence:.1f}, regime={regime})")
                return True
            
            # Treat very low confidence bias effectively as NEUTRAL
            effective_direction = self.current_bias.direction
            if getattr(self.current_bias, 'confidence', 0.0) < 3.0:
                effective_direction = "NEUTRAL"

            # NEUTRAL BIAS: Allow signals with moderate confidence (regime aware)
            if effective_direction == "NEUTRAL":
                allowed = signal_confidence >= neutral_threshold
                if not allowed:
                    logger.debug(f"Signal rejected: Confidence {signal_confidence:.1f} < {neutral_threshold} threshold for neutral bias (regime={regime})")
                return allowed
            
            # DIRECTIONAL BIAS: Adaptive strategy based on bias strength
            # 🎯 CRITICAL IMPROVEMENT: Mean reversion for INDEX trades ONLY
            # 🎯 USER INSIGHT: Stocks can swing 3-5% independently, indices limited to 1-2%
            bias_strength = getattr(self.current_bias, 'confidence', 0.0)
            nifty_change = getattr(self.current_bias, 'nifty_momentum', 0.0)  # nifty_momentum = % change
            
            # Detect if this is an INDEX trade (NIFTY/BANKNIFTY options) vs STOCK trade
            is_index_trade = False
            if symbol:
                # Check if symbol contains index names
                index_identifiers = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']
                is_index_trade = any(idx in symbol.upper() for idx in index_identifiers)
            
            # Determine if market is OVEREXTENDED (mean reversion opportunity)
            # ONLY apply to index trades - stocks have independent swings
            is_overextended = abs(nifty_change) >= 1.0 and is_index_trade  # ±1.0% NIFTY for INDEX trades only
            
            # ADAPTIVE LOGIC (INDEX ONLY):
            # 1. Moderate NIFTY (< 1.0%): TREND FOLLOWING for indices
            # 2. Extended NIFTY (>= 1.0%): MEAN REVERSION for indices only
            # 3. STOCKS: Always trend following (can swing independently)
            
            if is_overextended:
                # MEAN REVERSION MODE: Fade the market move (INDEX ONLY)
                # If NIFTY +1%, favor NIFTY SHORTS (index upside limited)
                # If NIFTY -1%, favor NIFTY LONGS (index downside limited)
                bias_aligned = (
                    (effective_direction == "BULLISH" and signal_direction == "SELL") or
                    (effective_direction == "BEARISH" and signal_direction == "BUY")
                )
                logger.info(f"🔄 MEAN REVERSION (INDEX): NIFTY {nifty_change:+.1f}% (±1% = limited room) → "
                          f"Favoring {signal_direction} {symbol} counter-trend")
            else:
                # TREND FOLLOWING MODE: Ride the momentum
                # For STOCKS: Always use this (independent swings)
                # For INDEX: Use when NIFTY < 1%
                bias_aligned = (
                    (effective_direction == "BULLISH" and signal_direction == "BUY") or
                    (effective_direction == "BEARISH" and signal_direction == "SELL")
                )
                symbol_type = "INDEX" if is_index_trade else "STOCK"
                logger.debug(f"📈 TREND FOLLOWING ({symbol_type}): NIFTY {nifty_change:+.1f}% → "
                           f"Favoring {signal_direction} {symbol} with {effective_direction} bias")
            
            if bias_aligned:
                # 🎯 RELATIVE STRENGTH CHECK (User insight: Stock must OUTPERFORM market)
                # For LONGS: Stock must be stronger than NIFTY
                # For SHORTS: Stock must be weaker than NIFTY
                if stock_change_percent is not None and not is_index_trade:
                    relative_strength = stock_change_percent - nifty_change
                    min_outperformance = 0.3  # Stock must outperform by at least 0.3%
                    
                    if signal_direction == "BUY":
                        # LONG: Stock must outperform market
                        if relative_strength < min_outperformance:
                            logger.info(f"❌ RELATIVE STRENGTH FAIL: {symbol} {signal_direction} rejected - "
                                      f"Stock {stock_change_percent:+.2f}% vs NIFTY {nifty_change:+.2f}% "
                                      f"(RS: {relative_strength:+.2f}% < {min_outperformance:+.2f}% required)")
                            return False
                        else:
                            logger.info(f"✅ RELATIVE STRENGTH: {symbol} OUTPERFORMING - "
                                      f"Stock {stock_change_percent:+.2f}% vs NIFTY {nifty_change:+.2f}% "
                                      f"(RS: {relative_strength:+.2f}%)")
                    
                    elif signal_direction == "SELL":
                        # SHORT: Stock must underperform market
                        if relative_strength > -min_outperformance:
                            logger.info(f"❌ RELATIVE WEAKNESS FAIL: {symbol} {signal_direction} rejected - "
                                      f"Stock {stock_change_percent:+.2f}% vs NIFTY {nifty_change:+.2f}% "
                                      f"(RS: {relative_strength:+.2f}% > {-min_outperformance:+.2f}% max)")
                            return False
                        else:
                            logger.info(f"✅ RELATIVE WEAKNESS: {symbol} UNDERPERFORMING - "
                                      f"Stock {stock_change_percent:+.2f}% vs NIFTY {nifty_change:+.2f}% "
                                      f"(RS: {relative_strength:+.2f}%)")
                
                # Aligned signals get lower threshold
                allowed = signal_confidence >= 5.5
                if not allowed:
                    logger.debug(f"Aligned signal rejected: Confidence {signal_confidence:.1f} < 5.5 threshold")
                return allowed
            else:
                # Counter-trend signals need much higher confidence, scaled by bias confidence
                bias_conf = getattr(self.current_bias, 'confidence', 0.0)
                required = 7.5 + min(bias_conf, 3.0)  # 7.5 to 10.5, capped effectively by 10
                required = min(required, 9.9)
                allowed = signal_confidence >= required
                if not allowed:
                    logger.debug(f"Counter-trend signal rejected: Confidence {signal_confidence:.1f} < {required:.1f} threshold (bias_conf={bias_conf:.1f})")
                return allowed
                
        except Exception as e:
            logger.warning(f"Error in bias alignment check: {e}")
            return signal_confidence >= 7.0  # Default threshold
    
    def should_align_with_bias(self, signal_direction: str, signal_confidence: float) -> bool:
        """
        DEPRECATED: Use should_allow_signal() instead
        Kept for backward compatibility
        """
        return self.should_allow_signal(signal_direction, signal_confidence)
    
    def get_position_size_multiplier(self, signal_direction: str) -> float:
        """
        Get position size multiplier based on bias alignment
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            
        Returns:
            Multiplier for position size (0.5 to 1.5)
        """
        try:
            if self.current_bias.direction == "NEUTRAL":
                return 1.0  # Standard size for neutral market
            
            # Check if signal aligns with bias
            bias_aligned = (
                (self.current_bias.direction == "BULLISH" and signal_direction == "BUY") or
                (self.current_bias.direction == "BEARISH" and signal_direction == "SELL")
            )
            
            if bias_aligned:
                # Larger positions when aligned with market bias
                confidence_factor = self.current_bias.confidence / 10.0
                return 1.0 + (confidence_factor * 0.5)  # 1.0 to 1.5x
            else:
                # Smaller positions when counter to market bias
                return 0.7  # 30% smaller positions
                
        except Exception as e:
            logger.warning(f"Error calculating position size multiplier: {e}")
            return 1.0
    
    def _calculate_enhanced_bias(self, nifty_momentum: float, sector_alignment: float,
                                volume_confirmation: bool, time_phase: str,
                                internals, nifty_data: Dict = None) -> Tuple[str, float]:
        """Calculate market bias using comprehensive internals"""
        try:
            # Start with basic components
            base_direction = "NEUTRAL"
            base_confidence = 0.0
            
            # 1. Price momentum component (30% weight)
            if abs(nifty_momentum) >= self.nifty_trend_threshold:
                if nifty_momentum > 0:
                    base_direction = "BULLISH"
                else:
                    base_direction = "BEARISH"
                base_confidence = min(abs(nifty_momentum) * 2, 3.0)  # Max 3.0 from momentum
            
            # 2. Market internals component (40% weight)
            internals_direction = "NEUTRAL"
            internals_confidence = 0.0
            
            if internals.bullish_score > internals.bearish_score + 10:
                internals_direction = "BULLISH"
                internals_confidence = (internals.bullish_score - internals.bearish_score) / 20
            elif internals.bearish_score > internals.bullish_score + 10:
                internals_direction = "BEARISH"
                internals_confidence = (internals.bearish_score - internals.bullish_score) / 20
            else:
                internals_direction = "NEUTRAL"
                internals_confidence = internals.neutral_score / 25
            
            internals_confidence = min(internals_confidence, 4.0)  # Max 4.0 from internals
            
            # 3. Breadth component (20% weight) - symmetric, volume-aware
            breadth_confidence = 0.0
            adr = getattr(internals, 'advance_decline_ratio', 1.0)
            up_vol = getattr(internals, 'up_volume_ratio', 50)  # percent
            # Bullish breadth
            if adr >= 1.5 and up_vol >= 60:
                breadth_confidence = 2.0
                internals_direction = "BULLISH" if internals_direction == "NEUTRAL" else internals_direction
            elif adr >= 1.2:
                breadth_confidence = 1.0
            # Bearish breadth
            # TUNED: Widened from 0.67 to 0.70 to catch more bearish breadth signals
            elif adr <= 0.70 and up_vol <= 40:
                breadth_confidence = 2.0
                internals_direction = "BEARISH" if internals_direction == "NEUTRAL" else internals_direction
            elif adr <= 0.85:
                breadth_confidence = 1.0
            
            # 4. Regime adjustment (10% weight)
            # TUNED: Reduced CHOPPY penalty from 0.5 to 0.7 (was too harsh)
            regime_multiplier = 1.0
            if internals.market_regime == "CHOPPY":
                regime_multiplier = 0.7  # Moderate reduction in choppy markets
            elif internals.market_regime == "TRENDING":
                regime_multiplier = 1.2  # Increase confidence in trending markets
            elif internals.market_regime == "VOLATILE_CHOPPY":
                regime_multiplier = 0.4  # Low confidence in volatile chop (was 0.3)
            
            # 2.5 Opening gap component (time-phase weighted)
            gap_pct = self._analyze_gap_component(nifty_data or {})
            gap_weight = 0.0
            try:
                # Emphasize gap in OPENING; decay after 30 minutes
                current_time = datetime.now().time()
                is_opening = self._get_time_phase().upper() == 'OPENING'
                if is_opening:
                    gap_weight = 0.7
                elif self._get_time_phase().upper() in ('MORNING',):
                    gap_weight = 0.3
                else:
                    gap_weight = 0.0
                # In CHOPPY regime cap gap influence
                if internals.market_regime in ('CHOPPY', 'VOLATILE_CHOPPY'):
                    gap_weight = min(gap_weight, 0.3)
            except Exception:
                gap_weight = 0.0

            # Combine all components
            if base_direction == internals_direction and base_direction != "NEUTRAL":
                # Aligned signals - add confidences
                total_confidence = base_confidence + internals_confidence + breadth_confidence
                final_direction = base_direction
            elif base_direction == "NEUTRAL":
                # Use internals direction if price is neutral
                total_confidence = internals_confidence + breadth_confidence * 0.5
                final_direction = internals_direction
            elif internals_direction == "NEUTRAL":
                # Use price direction if internals are neutral
                total_confidence = base_confidence + breadth_confidence * 0.5
                final_direction = base_direction
            else:
                # Conflicting signals - use dominant one
                if internals_confidence > base_confidence:
                    final_direction = internals_direction
                    total_confidence = internals_confidence - base_confidence
                else:
                    final_direction = base_direction
                    total_confidence = base_confidence - internals_confidence
            
            # Apply gap influence to direction and confidence
            if gap_weight > 0 and abs(gap_pct) >= 0.5:  # consider meaningful gap
                gap_direction = 'BULLISH' if gap_pct > 0 else 'BEARISH'
                if final_direction == gap_direction:
                    total_confidence += abs(gap_pct) * (gap_weight / 2.0)
                else:
                    total_confidence -= abs(gap_pct) * (gap_weight / 2.0)
                    if total_confidence < 0.5:
                        final_direction = 'NEUTRAL'
                        total_confidence = max(0.0, total_confidence)

            # Apply regime multiplier (confidence dampening in chop)
            total_confidence *= regime_multiplier
            
            # Apply time phase multiplier
            time_multiplier = self._get_time_phase_multiplier(time_phase)
            total_confidence *= time_multiplier
            
            # Add volume confirmation bonus
            if volume_confirmation and final_direction != "NEUTRAL":
                total_confidence += 1.0
            
            # Cap confidence
            total_confidence = min(total_confidence, 10.0)
            total_confidence = max(total_confidence, 0.0)
            
            # Check minimum threshold
            # TUNED: Lowered from 3.0 to 1.5 (same as basic calculation)
            if total_confidence < 1.5:
                final_direction = "NEUTRAL"
                total_confidence = 0.0
            
            return final_direction, total_confidence
            
        except Exception as e:
            logger.error(f"Error in enhanced bias calculation: {e}")
            # Fallback to basic calculation
            return self._calculate_market_bias(
                nifty_momentum, sector_alignment, volume_confirmation, time_phase
            )
    
    def _calculate_internals_alignment(self, bias_direction: str, internals) -> float:
        """Calculate how well internals align with the bias"""
        try:
            alignment_score = 0.0
            
            if bias_direction == "BULLISH":
                # Check bullish alignment
                if internals.advance_decline_ratio > 1.5:
                    alignment_score += 0.3
                if internals.up_volume_ratio > 60:
                    alignment_score += 0.2
                if internals.bullish_score > 60:
                    alignment_score += 0.3
                if internals.vix_change < 0:
                    alignment_score += 0.2
            elif bias_direction == "BEARISH":
                # Check bearish alignment
                if internals.advance_decline_ratio < 0.67:
                    alignment_score += 0.3
                if internals.up_volume_ratio < 40:
                    alignment_score += 0.2
                if internals.bearish_score > 60:
                    alignment_score += 0.3
                if internals.vix_change > 0:
                    alignment_score += 0.2
            else:
                # Neutral alignment
                if 0.8 < internals.advance_decline_ratio < 1.2:
                    alignment_score += 0.4
                if internals.neutral_score > 50:
                    alignment_score += 0.6
            
            return min(alignment_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating internals alignment: {e}")
            return 0.0
    
    def _calculate_bias_stability(self, new_direction: str) -> float:
        """Calculate stability score for bias changes"""
        try:
            if len(self.bias_history) < 3:
                return 0.5  # Neutral stability for insufficient history
            
            # Check recent bias directions
            recent_biases = [b['direction'] for b in list(self.bias_history)[-5:]]
            
            # Count direction changes
            changes = 0
            for i in range(1, len(recent_biases)):
                if recent_biases[i] != recent_biases[i-1]:
                    changes += 1
            
            # Calculate stability (fewer changes = higher stability)
            change_ratio = changes / (len(recent_biases) - 1)
            stability = 1.0 - change_ratio
            
            # Bonus for consistent direction
            if all(b == new_direction for b in recent_biases[-3:]):
                stability = min(stability + 0.2, 1.0)
            
            return stability
            
        except Exception as e:
            logger.error(f"Error calculating bias stability: {e}")
            return 0.5
    
    def _should_change_bias(self, new_direction: str, new_confidence: float, 
                           stability: float) -> bool:
        """Determine if bias should change (with hysteresis)"""
        try:
            # Always allow first bias
            if not self.bias_history:
                return True
            
            current_direction = self.current_bias.direction
            
            # Same direction - always update
            if new_direction == current_direction:
                return True
            
            # Check minimum time since last change
            time_since_change = datetime.now() - self.last_bias_change
            if time_since_change < self.min_bias_duration:
                # Too soon to change - need very high confidence
                if new_confidence < 7.0:
                    return False
            
            # Check if market is too choppy
            if stability < 0.3:  # Very unstable
                # Require higher confidence to change
                if new_confidence < 6.0:
                    return False
            
            # Check confidence differential
            confidence_diff = new_confidence - self.current_bias.confidence
            if confidence_diff < 2.0:  # New bias must be significantly more confident
                return False
            
            # Update change tracking
            if new_direction != current_direction:
                self.last_bias_change = datetime.now()
                self.bias_change_count += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking bias change: {e}")
            return True
    
    def _update_daily_tracking(self, nifty_data: Dict, nifty_momentum: float):
        """Update multi-day tracking for overbought/oversold detection"""
        try:
            # Only update once per day (at market close or first update of the day)
            now = datetime.now()
            today_str = now.strftime('%Y-%m-d')
            
            # Track NIFTY close for the day
            nifty_close = float(nifty_data.get('ltp', 0))
            if nifty_close > 0:
                # If this is a new day, record previous day's data
                if len(self.daily_closes) == 0 or self.daily_closes[-1][0] != today_str:
                    self.daily_closes.append((today_str, nifty_close))
                    self.daily_changes.append((today_str, nifty_momentum))
                    
                    # Update consecutive days counter
                    if nifty_momentum > 0.3:  # Bullish day (>0.3%)
                        self.consecutive_bullish_days += 1
                        self.consecutive_bearish_days = 0
                    elif nifty_momentum < -0.3:  # Bearish day (<-0.3%)
                        self.consecutive_bearish_days += 1
                        self.consecutive_bullish_days = 0
                    else:  # Flat day - reset counters
                        self.consecutive_bullish_days = 0
                        self.consecutive_bearish_days = 0
                    
                    # Calculate 3-day cumulative move
                    if len(self.daily_changes) >= 3:
                        self.cumulative_move_3d = sum([change for _, change in list(self.daily_changes)[-3:]])
                    
                    logger.info(f"📅 DAILY TRACKING UPDATE: Day={today_str}, Close={nifty_close:.0f}, "
                              f"Change={nifty_momentum:+.2f}%, "
                              f"Consecutive Bullish={self.consecutive_bullish_days}, "
                              f"Consecutive Bearish={self.consecutive_bearish_days}, "
                              f"3D Cumulative={self.cumulative_move_3d:+.2f}%")
        except Exception as e:
            logger.error(f"Error updating daily tracking: {e}")
    
    def _detect_multi_day_overbought(self) -> bool:
        """
        Detect multi-day overbought conditions
        Returns True if market is overbought based on multi-day analysis
        """
        try:
            # Criterion 1: 3+ consecutive bullish days
            streak_overbought = self.consecutive_bullish_days >= 3
            
            # Criterion 2: 3-day cumulative move > +2.5%
            cumulative_overbought = self.cumulative_move_3d > 2.5
            
            # Criterion 3: Today's momentum strong but 3-day extended
            if len(self.daily_changes) >= 3:
                today_momentum = self.daily_changes[-1][1] if self.daily_changes else 0
                strong_today = today_momentum > 0.5  # Today is +0.5%+
                extended_3d = self.cumulative_move_3d > 2.0  # But 3-day already +2%
                momentum_exhaustion = strong_today and extended_3d
            else:
                momentum_exhaustion = False
            
            is_overbought = streak_overbought or cumulative_overbought or momentum_exhaustion
            
            if is_overbought:
                logger.warning(f"🔴 MULTI-DAY OVERBOUGHT DETECTED:")
                logger.warning(f"   Consecutive Bullish Days: {self.consecutive_bullish_days} {'✅ OVERBOUGHT' if streak_overbought else ''}")
                logger.warning(f"   3-Day Cumulative: {self.cumulative_move_3d:+.2f}% {'✅ OVERBOUGHT' if cumulative_overbought else ''}")
                logger.warning(f"   Momentum Exhaustion: {'✅ OVERBOUGHT' if momentum_exhaustion else 'No'}")
                logger.warning(f"   🚨 CAUTION: Market may be due for pullback/consolidation")
            
            return is_overbought
        except Exception as e:
            logger.error(f"Error detecting multi-day overbought: {e}")
            return False
    
    def _detect_multi_day_oversold(self) -> bool:
        """
        Detect multi-day oversold conditions
        Returns True if market is oversold based on multi-day analysis
        """
        try:
            # Criterion 1: 3+ consecutive bearish days
            streak_oversold = self.consecutive_bearish_days >= 3
            
            # Criterion 2: 3-day cumulative move < -2.5%
            cumulative_oversold = self.cumulative_move_3d < -2.5
            
            is_oversold = streak_oversold or cumulative_oversold
            
            if is_oversold:
                logger.warning(f"🟢 MULTI-DAY OVERSOLD DETECTED:")
                logger.warning(f"   Consecutive Bearish Days: {self.consecutive_bearish_days} {'✅ OVERSOLD' if streak_oversold else ''}")
                logger.warning(f"   3-Day Cumulative: {self.cumulative_move_3d:+.2f}% {'✅ OVERSOLD' if cumulative_oversold else ''}")
                logger.warning(f"   🚨 CAUTION: Market may be due for bounce/rally")
            
            return is_oversold
        except Exception as e:
            logger.error(f"Error detecting multi-day oversold: {e}")
            return False
    
    def get_current_bias_summary(self) -> Dict:
        """Get current bias summary for logging/monitoring"""
        return {
            'direction': self.current_bias.direction,
            'confidence': round(self.current_bias.confidence, 2),
            'nifty_momentum': round(self.current_bias.nifty_momentum, 3),
            'sector_alignment': round(self.current_bias.sector_alignment, 3),
            'volume_confirmation': self.current_bias.volume_confirmation,
            'time_phase': self.current_bias.time_phase,
            'market_regime': getattr(self.current_bias, 'market_regime', 'NORMAL'),
            'breadth_score': round(getattr(self.current_bias, 'breadth_score', 1.0), 2),
            'stability_score': round(getattr(self.current_bias, 'stability_score', 0.5), 2),
            'internals_alignment': round(getattr(self.current_bias, 'internals_alignment', 0.0), 2),
            'consecutive_bullish_days': self.consecutive_bullish_days,
            'consecutive_bearish_days': self.consecutive_bearish_days,
            'cumulative_3d_move': round(self.cumulative_move_3d, 2),
            'last_updated': self.current_bias.last_updated.strftime('%H:%M:%S'),
            'age_minutes': (datetime.now() - self.current_bias.last_updated).total_seconds() / 60,
            'bias_changes': self.bias_change_count
        }

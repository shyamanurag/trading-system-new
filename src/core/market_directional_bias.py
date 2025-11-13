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

# Import professional mean reversion detector
try:
    from src.core.mean_reversion_detector import ProfessionalMeanReversionDetector
    MEAN_REVERSION_AVAILABLE = True
except ImportError:
    MEAN_REVERSION_AVAILABLE = False
    logger.warning("⚠️ Professional Mean Reversion Detector not available")

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
        
        # Initialize professional mean reversion detector
        if MEAN_REVERSION_AVAILABLE:
            self.mean_reversion_detector = ProfessionalMeanReversionDetector()
            logger.info("✅ Professional Mean Reversion Detector integrated")
        else:
            self.mean_reversion_detector = None
        
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
        
        # 🔥 INTRADAY MOVE EXHAUSTION TRACKING (User insight: 150+ points = stretched)
        self.todays_open = None  # Track today's opening price
        self.todays_high = None  # Track today's high
        self.todays_low = None  # Track today's low
        self.typical_daily_range = 200  # NIFTY typical daily range in points
        
        # Mean reversion zones based on points moved from open
        self.move_zones = {
            'EARLY': (0, 50),        # 0-50 points: Fresh move, trend-following
            'MID': (50, 100),        # 50-100 points: Established, cautious trend
            'EXTENDED': (100, 150),  # 100-150 points: Stretched, watch for reversal
            'EXTREME': (150, 250)    # 150+ points: Mean reversion mode
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
            
            # Debug: Log NIFTY data to understand what we're getting
            if 'ltp' in nifty_data and 'open' in nifty_data:
                ltp = float(nifty_data.get('ltp', 0))
                open_price = float(nifty_data.get('open', 0))
                actual_change = ltp - open_price
                actual_change_pct = (actual_change / open_price * 100) if open_price > 0 else 0
                logger.info(f"📊 NIFTY-I: LTP={ltp:.2f}, Open={open_price:.2f}, "
                           f"Actual Change={actual_change:.2f} ({actual_change_pct:+.2f}%), "
                           f"Provided change_percent={nifty_data.get('change_percent', 'N/A')}")
            
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
            
            # 9. 🔥 CHECK FOR MEAN REVERSION (Multi-indicator professional system)
            if self.mean_reversion_detector:
                # Use professional multi-indicator detector
                mr_signal = self.mean_reversion_detector.detect_mean_reversion(nifty_data, market_data)
                confidence *= mr_signal.bias_adjustment
                
                # If extreme reversion detected, consider flipping bias
                if mr_signal.mode == 'EXTREME_REVERSION':
                    if confidence > 5.0:
                        # Flip to counter-trend
                        bias_direction = 'BEARISH' if bias_direction == 'BULLISH' else 'BULLISH'
                        confidence = min(confidence * 0.8, 6.0)
                        logger.warning(f"🔄 EXTREME REVERSION: Flipped bias to {bias_direction} (MR confidence: {mr_signal.confidence:.1f})")
                    else:
                        bias_direction = 'NEUTRAL'
                        confidence = 0.0
                
                logger.info(f"🎯 Mean Reversion Mode: {mr_signal.mode} | Action: {mr_signal.recommended_action} | "
                           f"Bias Adjustment: {mr_signal.bias_adjustment:.2f}x")
            else:
                # Fallback to simple points-based check
                exhaustion_adjustment = self._check_move_exhaustion(nifty_data, bias_direction, confidence)
                bias_direction = exhaustion_adjustment['direction']
                confidence = exhaustion_adjustment['confidence']
            
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
        🔥 CHECK FOR INTRADAY MOVE EXHAUSTION
        
        User insight: When NIFTY has moved 150+ points from open, further moves in same 
        direction become difficult. System should:
        - Reduce confidence for trend continuation
        - Favor mean reversion trades
        - Prevent chasing exhausted moves
        
        Returns:
            Dict with adjusted direction, confidence, and move zone
        """
        try:
            ltp = float(nifty_data.get('ltp', 0))
            open_price = float(nifty_data.get('open', 0))
            high = float(nifty_data.get('high', ltp))
            low = float(nifty_data.get('low', ltp))
            
            if not all([ltp, open_price]):
                return {'direction': bias_direction, 'confidence': confidence, 'zone': 'UNKNOWN'}
            
            # Update today's tracking
            if self.todays_open is None or open_price != self.todays_open:
                self.todays_open = open_price
                self.todays_high = high
                self.todays_low = low
            else:
                self.todays_high = max(self.todays_high, high)
                self.todays_low = min(self.todays_low, low)
            
            # Calculate move from open in POINTS
            move_from_open = ltp - open_price
            abs_move = abs(move_from_open)
            
            # Determine move zone
            move_zone = 'EARLY'
            for zone_name, (min_pts, max_pts) in self.move_zones.items():
                if min_pts <= abs_move < max_pts:
                    move_zone = zone_name
                    break
            
            # Determine current move direction
            current_move_direction = 'BULLISH' if move_from_open > 0 else 'BEARISH'
            
            # Calculate how much room is left in typical daily range
            daily_range_used = (self.todays_high - self.todays_low)
            range_exhaustion_pct = (daily_range_used / self.typical_daily_range) * 100
            
            # Adjust confidence based on move zone and direction alignment
            adjusted_confidence = confidence
            adjusted_direction = bias_direction
            
            if move_zone == 'EARLY':
                # 0-50 points: Fresh move, boost trend-following
                if bias_direction == current_move_direction:
                    adjusted_confidence *= 1.2  # +20% confidence for aligned trend
                    logger.info(f"🚀 EARLY MOVE ({abs_move:.0f} pts): Boosting {bias_direction} confidence +20%")
                    
            elif move_zone == 'MID':
                # 50-100 points: Established move, normal operation
                logger.debug(f"📊 MID MOVE ({abs_move:.0f} pts): Normal operation")
                
            elif move_zone == 'EXTENDED':
                # 100-150 points: Stretched, reduce trend-following confidence
                if bias_direction == current_move_direction:
                    adjusted_confidence *= 0.7  # -30% for chasing extended moves
                    logger.info(f"⚠️ EXTENDED MOVE ({abs_move:.0f} pts): Reducing {bias_direction} confidence -30% (stretched)")
                else:
                    # Counter-trend (mean reversion) gets boost
                    adjusted_confidence *= 1.1
                    logger.info(f"🔄 EXTENDED MOVE ({abs_move:.0f} pts): Boosting {bias_direction} counter-trend +10% (mean reversion)")
                    
            elif move_zone == 'EXTREME':
                # 150+ points: STRONG mean reversion mode
                if bias_direction == current_move_direction:
                    # DON'T chase extreme moves - neutralize or flip
                    if confidence > 5.0:
                        # High confidence trend = flip to mean reversion
                        adjusted_direction = 'BEARISH' if current_move_direction == 'BULLISH' else 'BULLISH'
                        adjusted_confidence = min(confidence * 0.8, 6.0)  # Cap at 6.0 for mean reversion
                        logger.warning(f"🔴 EXTREME MOVE ({abs_move:.0f} pts): FLIPPING to {adjusted_direction} "
                                     f"mean reversion mode (was {bias_direction})")
                    else:
                        # Low confidence = neutralize to avoid chasing
                        adjusted_direction = 'NEUTRAL'
                        adjusted_confidence = 0.0
                        logger.warning(f"🔴 EXTREME MOVE ({abs_move:.0f} pts): NEUTRALIZING to avoid chasing {current_move_direction} move")
                else:
                    # Already counter-trend = strong boost for mean reversion
                    adjusted_confidence *= 1.3  # +30% for mean reversion in extreme zone
                    logger.info(f"✅ EXTREME MOVE ({abs_move:.0f} pts): Boosting {bias_direction} mean reversion +30%")
            
            # Additional check: Daily range exhaustion
            if range_exhaustion_pct > 80:
                if bias_direction == current_move_direction:
                    adjusted_confidence *= 0.6  # Heavy penalty for chasing when range exhausted
                    logger.warning(f"📏 RANGE EXHAUSTED ({range_exhaustion_pct:.0f}%): Reducing {bias_direction} confidence -40%")
            
            # Log move analysis
            logger.info(f"📊 MOVE ANALYSIS: {move_from_open:+.0f} pts from open | Zone: {move_zone} | "
                       f"Range: {daily_range_used:.0f}/{self.typical_daily_range:.0f} pts ({range_exhaustion_pct:.0f}%) | "
                       f"Bias: {adjusted_direction} @ {adjusted_confidence:.1f}/10")
            
            return {
                'direction': adjusted_direction,
                'confidence': adjusted_confidence,
                'zone': move_zone
            }
            
        except Exception as e:
            logger.error(f"Error checking move exhaustion: {e}")
            return {'direction': bias_direction, 'confidence': confidence, 'zone': 'ERROR'}
    
    def _analyze_nifty_momentum(self, nifty_data: Dict) -> float:
        """Analyze NIFTY intraday momentum from today's open (percent)"""
        try:
            # CRITICAL FIX: ALWAYS calculate change from LTP and open
            # Don't trust the provided change_percent field as it's often stale/wrong
            change_percent = 0.0
            if 'ltp' in nifty_data and 'open' in nifty_data:
                ltp = float(nifty_data.get('ltp', 0))
                open_price = float(nifty_data.get('open', 0))
                if open_price > 0:
                    change_percent = ((ltp - open_price) / open_price) * 100
                    logger.debug(f"✅ Calculated NIFTY change: {change_percent:+.2f}% (LTP={ltp:.2f}, Open={open_price:.2f})")
            else:
                # Fallback: Try to get from tick data fields if LTP/open not available
                for field in ['change_percent', 'price_change', 'change_pct', 'change', 'pct_change']:
                    if field in nifty_data:
                        change_percent = float(nifty_data[field])
                        logger.debug(f"⚠️ Using provided {field}: {change_percent:+.2f}% (LTP/open not available)")
                        break
                    
            ltp = float(nifty_data.get('ltp', 0))
            
            # Update NIFTY history
            self.nifty_history.append({
                'change_percent': change_percent,
                'ltp': ltp,
                'timestamp': datetime.now()
            })
            
            # Keep only recent history
            if len(self.nifty_history) > self.max_history:
                self.nifty_history = self.nifty_history[-self.max_history:]
            
            # Calculate momentum strength
            if len(self.nifty_history) >= 5:
                # Use moving average of recent changes for trend confirmation
                recent_changes = [h['change_percent'] for h in self.nifty_history[-5:]]
                momentum = np.mean(recent_changes)
                
                # Apply trend consistency bonus
                trend_consistency = self._calculate_trend_consistency(recent_changes)
                momentum *= (1 + trend_consistency * 0.5)  # Up to 50% bonus for consistency
                
                logger.debug(f"🎯 NIFTY momentum calculated: {momentum:.2f}% (from {len(recent_changes)} recent changes)")
                return momentum
            else:
                logger.debug(f"🎯 NIFTY momentum (single point): {change_percent:.2f}%")
                return change_percent
                
        except Exception as e:
            logger.warning(f"Error analyzing NIFTY momentum: {e}")
            return 0.0

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
            if confidence < 3.0:  # Minimum confidence for bias
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

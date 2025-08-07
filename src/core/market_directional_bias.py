"""
Market Directional Bias System
Long-term solution for coordinated position taking and eliminating market-neutral losses

This system determines intraday market bias to coordinate all trading strategies
in the same direction, preventing conflicting BUY/SELL positions that guarantee losses.
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, time
import numpy as np
from dataclasses import dataclass

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
        
        # BIAS CALCULATION PARAMETERS
        self.nifty_trend_threshold = 0.3  # 0.3% minimum for bias detection
        self.sector_alignment_threshold = 0.6  # 60% sector alignment required
        self.volume_multiplier_threshold = 1.5  # 1.5x average volume for confirmation
        self.confidence_decay_minutes = 30  # Bias confidence decays over 30 minutes
        
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
        
        # TIME-OF-DAY BIAS MODIFIERS
        self.time_phases = {
            'OPENING': (9, 15, 10, 0),    # 9:15-10:00 - High volatility
            'MORNING': (10, 0, 12, 0),    # 10:00-12:00 - Trend establishment
            'AFTERNOON': (12, 0, 14, 30), # 12:00-14:30 - Momentum continuation
            'CLOSING': (14, 30, 15, 30)   # 14:30-15:30 - Final moves
        }
        
    async def update_market_bias(self, market_data: Dict) -> MarketBias:
        """
        Analyze market data and update directional bias
        
        Args:
            market_data: Dictionary with symbol -> price data
            
        Returns:
            Updated MarketBias object
        """
        try:
            # Get NIFTY data
            nifty_data = market_data.get('NIFTY-I', {})
            if not nifty_data:
                logger.warning("No NIFTY data available for bias calculation")
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
            
            # 1. ANALYZE NIFTY MOMENTUM
            nifty_momentum = self._analyze_nifty_momentum(nifty_data)
            
            # 2. CALCULATE SECTOR ALIGNMENT
            sector_alignment = self._calculate_sector_alignment(market_data)
            
            # 3. CHECK VOLUME CONFIRMATION
            volume_confirmation = self._check_volume_confirmation(nifty_data)
            
            # 4. DETERMINE TIME PHASE
            time_phase = self._get_current_time_phase()
            
            # 5. CALCULATE OVERALL BIAS
            bias_direction, confidence = self._calculate_market_bias(
                nifty_momentum, sector_alignment, volume_confirmation, time_phase
            )
            
            # 6. UPDATE CURRENT BIAS
            self.current_bias = MarketBias(
                direction=bias_direction,
                confidence=confidence,
                nifty_momentum=nifty_momentum,
                sector_alignment=sector_alignment,
                volume_confirmation=volume_confirmation,
                time_phase=time_phase,
                last_updated=datetime.now()
            )
            
            # Log bias update
            logger.info(f"🎯 MARKET BIAS UPDATE: {bias_direction} "
                       f"(Confidence: {confidence:.1f}/10, NIFTY: {nifty_momentum:+.2f}%, "
                       f"Sectors: {sector_alignment:+.2f}, Phase: {time_phase})")
            
            return self.current_bias
            
        except Exception as e:
            logger.error(f"Error updating market bias: {e}")
            return self.current_bias
    
    def _analyze_nifty_momentum(self, nifty_data: Dict) -> float:
        """Analyze NIFTY momentum and trend strength"""
        try:
            # Try multiple possible field names for price change
            change_percent = 0.0
            for field in ['change_percent', 'price_change', 'change_pct', 'change', 'pct_change']:
                if field in nifty_data:
                    change_percent = float(nifty_data[field])
                    break
            
            # If still zero, try to calculate from price data
            if change_percent == 0.0 and 'ltp' in nifty_data and 'open' in nifty_data:
                ltp = float(nifty_data.get('ltp', 0))
                open_price = float(nifty_data.get('open', 0))
                if open_price > 0:
                    change_percent = ((ltp - open_price) / open_price) * 100
                    
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
    
    def should_allow_signal(self, signal_direction: str, signal_confidence: float) -> bool:
        """
        Determine if a signal should be allowed based on market bias
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            signal_confidence: Signal confidence (0-10)
            
        Returns:
            True if signal should be allowed, False if it should be rejected
        """
        try:
            # HIGH CONFIDENCE OVERRIDE: Allow counter-trend for very strong signals
            if signal_confidence >= 8.5:
                logger.info(f"🎯 HIGH CONFIDENCE OVERRIDE: {signal_direction} allowed despite bias")
                return True
            
            # NEUTRAL BIAS: Allow signals with moderate confidence
            if self.current_bias.direction == "NEUTRAL":
                allowed = signal_confidence >= 6.5
                if not allowed:
                    logger.debug(f"Signal rejected: Confidence {signal_confidence:.1f} < 6.5 threshold for neutral bias")
                return allowed
            
            # DIRECTIONAL BIAS: Check alignment
            bias_aligned = (
                (self.current_bias.direction == "BULLISH" and signal_direction == "BUY") or
                (self.current_bias.direction == "BEARISH" and signal_direction == "SELL")
            )
            
            if bias_aligned:
                # Aligned signals get lower threshold
                allowed = signal_confidence >= 5.5
                if not allowed:
                    logger.debug(f"Aligned signal rejected: Confidence {signal_confidence:.1f} < 5.5 threshold")
                return allowed
            else:
                # Counter-trend signals need higher confidence
                allowed = signal_confidence >= 7.5
                if not allowed:
                    logger.debug(f"Counter-trend signal rejected: Confidence {signal_confidence:.1f} < 7.5 threshold")
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
    
    def get_current_bias_summary(self) -> Dict:
        """Get current bias summary for logging/monitoring"""
        return {
            'direction': self.current_bias.direction,
            'confidence': round(self.current_bias.confidence, 2),
            'nifty_momentum': round(self.current_bias.nifty_momentum, 3),
            'sector_alignment': round(self.current_bias.sector_alignment, 3),
            'volume_confirmation': self.current_bias.volume_confirmation,
            'time_phase': self.current_bias.time_phase,
            'last_updated': self.current_bias.last_updated.strftime('%H:%M:%S'),
            'age_minutes': (datetime.now() - self.current_bias.last_updated).total_seconds() / 60
        }

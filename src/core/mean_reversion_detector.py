"""
Professional Mean Reversion Detection System
=============================================
Multi-indicator "rubber band effect" detector for identifying stretched markets
and preventing chasing exhausted moves.

Combines:
- Absolute points tracking (NIFTY-specific)
- RSI momentum exhaustion
- Bollinger Bands statistical extremes  
- ATR-based dynamic zones (volatility-adjusted)
- VWAP deviation (institutional anchor)
- Volume confirmation

Author: Trading System v2
Created: 2025-11-13
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MeanReversionSignal:
    """Mean reversion detection result"""
    mode: str  # TREND_FOLLOW, CAUTION, MEAN_REVERSION, EXTREME_REVERSION
    confidence: float  # 0-10 scale
    indicators: Dict[str, any]  # Individual indicator readings
    recommended_action: str  # CHASE, HOLD, FADE, STRONG_FADE
    bias_adjustment: float  # Multiplier for bias confidence (0.5 to 1.5)
    reason: str  # Human-readable explanation

class ProfessionalMeanReversionDetector:
    """
    Multi-indicator mean reversion detector
    
    Uses ensemble approach - multiple indicators must confirm
    to generate high-confidence mean reversion signals
    """
    
    def __init__(self):
        # Historical data storage
        self.price_history = deque(maxlen=50)  # For RSI, BB, ATR
        self.volume_history = deque(maxlen=50)
        self.vwap_history = deque(maxlen=1)  # Reset daily
        
        # Indicator parameters
        self.rsi_period = 14
        self.bb_period = 20
        self.bb_std = 2.0
        self.atr_period = 14
        
        # RSI thresholds
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.rsi_extreme_overbought = 80
        self.rsi_extreme_oversold = 20
        
        # NIFTY-specific absolute point zones
        self.point_zones = {
            'EARLY': (0, 50),
            'MID': (50, 100),
            'EXTENDED': (100, 150),
            'EXTREME': (150, 300)
        }
        
        # Today's tracking (reset daily)
        self.todays_open = None
        self.todays_vwap = None
        self.todays_cumulative_volume = 0
        self.todays_cumulative_pv = 0  # price * volume
        
        logger.info("✅ Professional Mean Reversion Detector initialized")
    
    def detect_mean_reversion(self, nifty_data: Dict, market_data: Dict = None) -> MeanReversionSignal:
        """
        Main detection method - analyzes all indicators and returns composite signal
        
        Args:
            nifty_data: Current NIFTY price/volume data
            market_data: Optional broader market data for context
            
        Returns:
            MeanReversionSignal with mode and recommended actions
        """
        try:
            # Extract NIFTY data
            ltp = float(nifty_data.get('ltp', 0))
            open_price = float(nifty_data.get('open', 0))
            high = float(nifty_data.get('high', ltp))
            low = float(nifty_data.get('low', ltp))
            volume = float(nifty_data.get('volume', 0))
            
            if not all([ltp, open_price]):
                return self._neutral_signal("Insufficient data")
            
            # Reset daily tracking if new day
            if self.todays_open is None or open_price != self.todays_open:
                self._reset_daily_tracking(open_price)
            
            # Update history
            self._update_history(ltp, high, low, volume)
            
            # Calculate all indicators
            indicators = {}
            
            # 1. Absolute points from open
            indicators['points'] = self._calculate_points_indicator(ltp, open_price, high, low)
            
            # 2. RSI (momentum exhaustion)
            indicators['rsi'] = self._calculate_rsi()
            
            # 3. Bollinger Bands (statistical extremes)
            indicators['bollinger'] = self._calculate_bollinger_bands(ltp)
            
            # 4. ATR-based dynamic zones
            indicators['atr'] = self._calculate_atr_zones(ltp, high, low)
            
            # 5. VWAP deviation
            indicators['vwap'] = self._calculate_vwap_deviation(ltp, volume)
            
            # 6. Volume profile
            indicators['volume'] = self._analyze_volume_profile(volume)
            
            # Synthesize all indicators into composite signal
            signal = self._synthesize_indicators(indicators, ltp, open_price)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in mean reversion detection: {e}")
            return self._neutral_signal(f"Error: {e}")
    
    def _reset_daily_tracking(self, open_price: float):
        """Reset intraday tracking for new day"""
        self.todays_open = open_price
        self.todays_vwap = None
        self.todays_cumulative_volume = 0
        self.todays_cumulative_pv = 0
        logger.info(f"📅 New trading day started: Open={open_price:.2f}")
    
    def _update_history(self, close: float, high: float, low: float, volume: float):
        """Update price and volume history"""
        self.price_history.append({
            'close': close,
            'high': high,
            'low': low,
            'timestamp': datetime.now()
        })
        self.volume_history.append(volume)
    
    def _calculate_points_indicator(self, ltp: float, open_price: float, 
                                    high: float, low: float) -> Dict:
        """Calculate absolute points-based indicator"""
        move_from_open = ltp - open_price
        abs_move = abs(move_from_open)
        
        # Determine zone
        zone = 'EARLY'
        for zone_name, (min_pts, max_pts) in self.point_zones.items():
            if min_pts <= abs_move < max_pts:
                zone = zone_name
                break
        
        # Calculate daily range exhaustion
        daily_range = high - low
        typical_range = 200  # NIFTY typical range
        range_pct = (daily_range / typical_range) * 100
        
        # Scoring: Higher score = more stretched
        if zone == 'EARLY':
            score = abs_move / 50  # 0-1
        elif zone == 'MID':
            score = 1 + (abs_move - 50) / 50  # 1-2
        elif zone == 'EXTENDED':
            score = 2 + (abs_move - 100) / 50  # 2-3
        else:  # EXTREME
            score = 3 + min((abs_move - 150) / 100, 2)  # 3-5
        
        return {
            'move_from_open': move_from_open,
            'abs_move': abs_move,
            'zone': zone,
            'range_exhaustion_pct': range_pct,
            'score': score,
            'is_stretched': zone in ['EXTENDED', 'EXTREME']
        }
    
    def _calculate_rsi(self) -> Dict:
        """Calculate RSI momentum indicator"""
        if len(self.price_history) < self.rsi_period + 1:
            return {'value': 50, 'state': 'NEUTRAL', 'score': 0}
        
        # Calculate price changes
        closes = [p['close'] for p in list(self.price_history)[-self.rsi_period-1:]]
        deltas = np.diff(closes)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Determine state and score
        if rsi >= self.rsi_extreme_overbought:
            state = 'EXTREME_OVERBOUGHT'
            score = 3 + (rsi - 80) / 10  # 3-5
        elif rsi >= self.rsi_overbought:
            state = 'OVERBOUGHT'
            score = 1 + (rsi - 70) / 10  # 1-3
        elif rsi <= self.rsi_extreme_oversold:
            state = 'EXTREME_OVERSOLD'
            score = 3 + (20 - rsi) / 10  # 3-5
        elif rsi <= self.rsi_oversold:
            state = 'OVERSOLD'
            score = 1 + (30 - rsi) / 10  # 1-3
        else:
            state = 'NEUTRAL'
            score = 0
        
        return {
            'value': rsi,
            'state': state,
            'score': score,
            'is_stretched': state in ['OVERBOUGHT', 'OVERSOLD', 'EXTREME_OVERBOUGHT', 'EXTREME_OVERSOLD']
        }
    
    def _calculate_bollinger_bands(self, ltp: float) -> Dict:
        """Calculate Bollinger Bands statistical indicator"""
        if len(self.price_history) < self.bb_period:
            return {'position': 0, 'state': 'NEUTRAL', 'score': 0}
        
        closes = [p['close'] for p in list(self.price_history)[-self.bb_period:]]
        sma = np.mean(closes)
        std = np.std(closes)
        
        upper_band = sma + (self.bb_std * std)
        lower_band = sma - (self.bb_std * std)
        
        # Calculate position within bands (-1 to +1)
        band_width = upper_band - lower_band
        if band_width > 0:
            position = (ltp - sma) / (band_width / 2)
        else:
            position = 0
        
        # Determine state and score
        if position >= 1.0:  # At or beyond upper band
            state = 'EXTREME_HIGH'
            score = 3 + min(abs(position - 1.0) * 2, 2)  # 3-5
        elif position >= 0.8:  # Approaching upper band
            state = 'HIGH'
            score = 1 + (position - 0.8) * 10  # 1-3
        elif position <= -1.0:  # At or beyond lower band
            state = 'EXTREME_LOW'
            score = 3 + min(abs(position + 1.0) * 2, 2)  # 3-5
        elif position <= -0.8:  # Approaching lower band
            state = 'LOW'
            score = 1 + abs(position + 0.8) * 10  # 1-3
        else:
            state = 'NEUTRAL'
            score = 0
        
        return {
            'sma': sma,
            'upper': upper_band,
            'lower': lower_band,
            'position': position,
            'state': state,
            'score': score,
            'is_stretched': abs(position) >= 0.8
        }
    
    def _calculate_atr_zones(self, ltp: float, high: float, low: float) -> Dict:
        """Calculate ATR-based dynamic zones (volatility-adjusted)"""
        if len(self.price_history) < self.atr_period + 1:
            return {'atr': 0, 'zone': 'UNKNOWN', 'score': 0}
        
        # Calculate True Range for each period
        prices = list(self.price_history)[-self.atr_period:]
        true_ranges = []
        
        for i in range(1, len(prices)):
            hl = prices[i]['high'] - prices[i]['low']
            hc = abs(prices[i]['high'] - prices[i-1]['close'])
            lc = abs(prices[i]['low'] - prices[i-1]['close'])
            true_ranges.append(max(hl, hc, lc))
        
        atr = np.mean(true_ranges) if true_ranges else 0
        
        if atr == 0:
            return {'atr': 0, 'zone': 'UNKNOWN', 'score': 0}
        
        # Calculate move in ATR units
        move_from_open = abs(ltp - self.todays_open) if self.todays_open else 0
        atr_units = move_from_open / atr
        
        # Determine zone
        if atr_units < 1.0:
            zone = 'NORMAL'
            score = 0
        elif atr_units < 2.0:
            zone = 'EXTENDED'
            score = 1 + (atr_units - 1.0)  # 1-2
        elif atr_units < 3.0:
            zone = 'VERY_EXTENDED'
            score = 2 + (atr_units - 2.0)  # 2-3
        else:
            zone = 'EXTREME'
            score = 3 + min((atr_units - 3.0), 2)  # 3-5
        
        return {
            'atr': atr,
            'atr_units': atr_units,
            'zone': zone,
            'score': score,
            'is_stretched': atr_units >= 2.0
        }
    
    def _calculate_vwap_deviation(self, ltp: float, volume: float) -> Dict:
        """Calculate VWAP deviation (institutional anchor point)"""
        # Update VWAP
        self.todays_cumulative_pv += ltp * volume
        self.todays_cumulative_volume += volume
        
        if self.todays_cumulative_volume > 0:
            vwap = self.todays_cumulative_pv / self.todays_cumulative_volume
        else:
            vwap = ltp
        
        self.todays_vwap = vwap
        
        # Calculate deviation
        deviation = ltp - vwap
        deviation_pct = (deviation / vwap * 100) if vwap > 0 else 0
        
        # Score based on deviation
        abs_dev_pct = abs(deviation_pct)
        if abs_dev_pct < 0.2:
            state = 'AT_VWAP'
            score = 0
        elif abs_dev_pct < 0.4:
            state = 'NEAR_VWAP'
            score = abs_dev_pct * 2.5  # 0.5-1.0
        elif abs_dev_pct < 0.6:
            state = 'AWAY_FROM_VWAP'
            score = 1 + (abs_dev_pct - 0.4) * 5  # 1-2
        elif abs_dev_pct < 0.8:
            state = 'FAR_FROM_VWAP'
            score = 2 + (abs_dev_pct - 0.6) * 5  # 2-3
        else:
            state = 'EXTREME_FROM_VWAP'
            score = 3 + min((abs_dev_pct - 0.8) * 2.5, 2)  # 3-5
        
        return {
            'vwap': vwap,
            'deviation': deviation,
            'deviation_pct': deviation_pct,
            'state': state,
            'score': score,
            'is_stretched': abs_dev_pct >= 0.6
        }
    
    def _analyze_volume_profile(self, current_volume: float) -> Dict:
        """Analyze volume to confirm moves"""
        if len(self.volume_history) < 20:
            return {'state': 'INSUFFICIENT_DATA', 'multiplier': 1.0}
        
        recent_volumes = list(self.volume_history)[-20:]
        avg_volume = np.mean(recent_volumes)
        
        if avg_volume == 0:
            return {'state': 'NO_VOLUME', 'multiplier': 1.0}
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= 2.0:
            state = 'VERY_HIGH'
            multiplier = 1.3  # High volume confirms the move
        elif volume_ratio >= 1.5:
            state = 'HIGH'
            multiplier = 1.2
        elif volume_ratio >= 0.8:
            state = 'NORMAL'
            multiplier = 1.0
        elif volume_ratio >= 0.5:
            state = 'LOW'
            multiplier = 0.9  # Low volume = weak move
        else:
            state = 'VERY_LOW'
            multiplier = 0.7  # Very low volume = suspicious move
        
        return {
            'current': current_volume,
            'average': avg_volume,
            'ratio': volume_ratio,
            'state': state,
            'multiplier': multiplier
        }
    
    def _synthesize_indicators(self, indicators: Dict, ltp: float, open_price: float) -> MeanReversionSignal:
        """
        Synthesize all indicators into composite mean reversion signal
        
        Scoring system:
        - Each indicator contributes 0-5 points
        - Total score determines mode
        - Multiple confirmations required for high confidence
        """
        # Extract scores
        points_score = indicators['points']['score']
        rsi_score = indicators['rsi']['score']
        bb_score = indicators['bollinger']['score']
        atr_score = indicators['atr']['score']
        vwap_score = indicators['vwap']['score']
        
        # Count how many indicators show stretch
        stretch_count = sum([
            indicators['points']['is_stretched'],
            indicators['rsi']['is_stretched'],
            indicators['bollinger']['is_stretched'],
            indicators['atr']['is_stretched'],
            indicators['vwap']['is_stretched']
        ])
        
        # Calculate total score (weighted)
        total_score = (
            points_score * 1.5 +  # Points get highest weight (NIFTY-specific)
            rsi_score * 1.2 +     # RSI is reliable
            bb_score * 1.0 +      # Bollinger Bands
            atr_score * 1.0 +     # ATR zones
            vwap_score * 0.8      # VWAP deviation
        )
        
        # Apply volume multiplier
        volume_multiplier = indicators['volume']['multiplier']
        total_score *= volume_multiplier
        
        # Determine mode and confidence
        if total_score < 3:
            mode = 'TREND_FOLLOW'
            confidence = 8.0  # High confidence to follow trend
            action = 'CHASE'
            bias_adj = 1.2  # Boost trend confidence
            reason = f"Fresh move, all clear ({stretch_count}/5 stretched)"
            
        elif total_score < 6:
            mode = 'CAUTION'
            confidence = 5.0  # Medium confidence
            action = 'HOLD'
            bias_adj = 1.0  # Normal
            reason = f"Moderate extension ({stretch_count}/5 stretched)"
            
        elif total_score < 10:
            mode = 'MEAN_REVERSION'
            confidence = 7.0  # Good confidence for mean reversion
            action = 'FADE'
            bias_adj = 0.7  # Reduce trend confidence
            reason = f"Stretched market ({stretch_count}/5 stretched, score={total_score:.1f})"
            
        else:  # total_score >= 10
            mode = 'EXTREME_REVERSION'
            confidence = 9.0  # Very high confidence
            action = 'STRONG_FADE'
            bias_adj = 0.3  # Heavily penalize trend chasing
            reason = f"EXTREME stretch ({stretch_count}/5 stretched, score={total_score:.1f})"
        
        # Build detailed reason
        details = []
        if indicators['points']['zone'] in ['EXTENDED', 'EXTREME']:
            details.append(f"Points: {indicators['points']['zone']} ({indicators['points']['abs_move']:.0f} pts)")
        if indicators['rsi']['state'] != 'NEUTRAL':
            details.append(f"RSI: {indicators['rsi']['state']} ({indicators['rsi']['value']:.1f})")
        if indicators['bollinger']['state'] != 'NEUTRAL':
            details.append(f"BB: {indicators['bollinger']['state']}")
        if indicators['atr']['zone'] not in ['NORMAL', 'UNKNOWN']:
            details.append(f"ATR: {indicators['atr']['zone']} ({indicators['atr']['atr_units']:.1f}σ)")
        if indicators['vwap']['state'] not in ['AT_VWAP', 'NEAR_VWAP']:
            details.append(f"VWAP: {indicators['vwap']['state']} ({indicators['vwap']['deviation_pct']:+.2f}%)")
        
        if details:
            reason += " | " + " | ".join(details)
        
        # Log the detection
        move_direction = "UP" if ltp > open_price else "DOWN"
        logger.info(f"🎯 MEAN REVERSION: {mode} | {move_direction} move | "
                   f"Score: {total_score:.1f} | Confidence: {confidence:.1f}/10 | "
                   f"Action: {action} | Bias Adj: {bias_adj:.2f}x")
        logger.info(f"   Reason: {reason}")
        
        return MeanReversionSignal(
            mode=mode,
            confidence=confidence,
            indicators=indicators,
            recommended_action=action,
            bias_adjustment=bias_adj,
            reason=reason
        )
    
    def _neutral_signal(self, reason: str) -> MeanReversionSignal:
        """Return neutral signal when detection not possible"""
        return MeanReversionSignal(
            mode='TREND_FOLLOW',
            confidence=5.0,
            indicators={},
            recommended_action='HOLD',
            bias_adjustment=1.0,
            reason=reason
        )


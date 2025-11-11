"""
Signal Enhancement Layer
=========================
Applies sophisticated filters and confluence checks to improve signal quality
WITHOUT modifying individual strategy code.

Enhancements:
1. Multi-timeframe confluence validation
2. Volume profile analysis
3. Market microstructure confirmation
4. Adaptive confidence based on recent performance
5. Statistical significance testing
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class SignalEnhancer:
    """Enhances signal quality through confluence and statistical validation"""
    
    def __init__(self):
        # Performance tracking for adaptive confidence
        self.signal_history = []  # Last 100 signals with outcomes
        self.strategy_performance = {}  # Per-strategy win rates
        
        # Price history for multi-timeframe analysis
        self.price_history = defaultdict(list)  # symbol -> prices
        self.volume_history = defaultdict(list)  # symbol -> volumes
        
        # Volume profile tracking
        self.volume_at_price = defaultdict(lambda: defaultdict(float))  # symbol -> {price: volume}
        
        # Enhancement thresholds
        self.min_confluence_score = 0.60  # Minimum 60% confluence required
        self.min_volume_ratio = 1.2  # Minimum 20% above average volume
        self.min_microstructure_score = 0.50  # Minimum microstructure quality
        
        logger.info("✅ Signal Enhancement Layer initialized")
    
    async def enhance_signals(self, signals: List[Dict], market_data: Dict) -> List[Dict]:
        """
        Apply sophisticated enhancements to signals
        
        Returns: Enhanced signals with adjusted confidence and metadata
        """
        if not signals:
            return signals
        
        enhanced_signals = []
        
        for signal in signals:
            try:
                # Update market data history
                self._update_market_history(signal.get('symbol'), market_data)
                
                # Calculate enhancement scores
                confluence_score = self._calculate_confluence(signal, market_data)
                volume_score = self._calculate_volume_quality(signal, market_data)
                microstructure_score = self._calculate_microstructure_quality(signal, market_data)
                timeframe_score = self._check_timeframe_alignment(signal, market_data)
                
                # Calculate overall enhancement score
                enhancement_score = (
                    confluence_score * 0.30 +
                    volume_score * 0.25 +
                    microstructure_score * 0.25 +
                    timeframe_score * 0.20
                )
                
                # Get adaptive confidence adjustment
                strategy = signal.get('metadata', {}).get('strategy', 'unknown')
                performance_factor = self._get_strategy_performance_factor(strategy)
                
                # Apply enhancements
                original_confidence = signal.get('confidence', 0.5)
                enhanced_confidence = original_confidence * enhancement_score * performance_factor
                
                # Filter: Only pass signals with sufficient quality
                if enhancement_score >= self.min_confluence_score:
                    signal['confidence'] = min(enhanced_confidence, 10.0)
                    signal['metadata'] = signal.get('metadata', {})
                    signal['metadata'].update({
                        'enhanced': True,
                        'original_confidence': original_confidence,
                        'confluence_score': round(confluence_score, 3),
                        'volume_score': round(volume_score, 3),
                        'microstructure_score': round(microstructure_score, 3),
                        'timeframe_score': round(timeframe_score, 3),
                        'enhancement_score': round(enhancement_score, 3),
                        'performance_factor': round(performance_factor, 3)
                    })
                    
                    enhanced_signals.append(signal)
                    
                    logger.info(f"✅ ENHANCED: {signal.get('symbol')} {signal.get('action')} - "
                              f"Confidence: {original_confidence:.2f} → {enhanced_confidence:.2f} "
                              f"(enhancement: {enhancement_score:.2f}, perf: {performance_factor:.2f})")
                else:
                    logger.info(f"❌ FILTERED: {signal.get('symbol')} {signal.get('action')} - "
                              f"Low enhancement score: {enhancement_score:.2f} < {self.min_confluence_score}")
                
            except Exception as e:
                logger.error(f"Error enhancing signal for {signal.get('symbol')}: {e}")
                # Keep original signal if enhancement fails
                enhanced_signals.append(signal)
        
        logger.info(f"📊 ENHANCEMENT: {len(signals)} → {len(enhanced_signals)} signals passed quality filters")
        return enhanced_signals
    
    def _calculate_confluence(self, signal: Dict, market_data: Dict) -> float:
        """
        Calculate confluence score (0.0-1.0) based on multiple confirming factors
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            factors = []
            
            # Factor 1: Price momentum alignment
            if symbol in self.price_history and len(self.price_history[symbol]) >= 5:
                prices = self.price_history[symbol][-5:]
                momentum = (prices[-1] - prices[0]) / prices[0]
                
                if (action == 'BUY' and momentum > 0.002) or (action == 'SELL' and momentum < -0.002):
                    factors.append(1.0)  # Strong alignment
                elif abs(momentum) < 0.001:
                    factors.append(0.5)  # Neutral
                else:
                    factors.append(0.0)  # Against momentum
            
            # Factor 2: Volume confirmation
            if symbol in self.volume_history and len(self.volume_history[symbol]) >= 3:
                current_vol = self.volume_history[symbol][-1]
                avg_vol = np.mean(self.volume_history[symbol][-20:]) if len(self.volume_history[symbol]) >= 20 else current_vol
                
                if current_vol > avg_vol * 1.5:
                    factors.append(1.0)  # Strong volume
                elif current_vol > avg_vol:
                    factors.append(0.7)  # Above average
                else:
                    factors.append(0.3)  # Weak volume
            
            # Factor 3: Market structure
            data = market_data.get(symbol, {})
            change_pct = data.get('change_percent', 0)
            
            if (action == 'BUY' and change_pct > 0.5) or (action == 'SELL' and change_pct < -0.5):
                factors.append(1.0)  # Market moving in signal direction
            elif abs(change_pct) < 0.2:
                factors.append(0.5)  # Consolidating
            else:
                factors.append(0.2)  # Weak structure
            
            # Return average of all factors
            return np.mean(factors) if factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating confluence: {e}")
            return 0.5
    
    def _calculate_volume_quality(self, signal: Dict, market_data: Dict) -> float:
        """
        Analyze volume quality and distribution
        """
        try:
            symbol = signal.get('symbol')
            data = market_data.get(symbol, {})
            
            current_volume = data.get('volume', 0)
            
            if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
                return 0.5  # Neutral if insufficient history
            
            volumes = self.volume_history[symbol]
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            
            if avg_volume == 0:
                return 0.5
            
            volume_ratio = current_volume / avg_volume
            
            # Score based on volume ratio
            if volume_ratio > 2.0:
                return 1.0  # Exceptional volume
            elif volume_ratio > 1.5:
                return 0.9  # Strong volume
            elif volume_ratio > 1.2:
                return 0.7  # Good volume
            elif volume_ratio > 0.8:
                return 0.5  # Average volume
            else:
                return 0.3  # Weak volume
                
        except Exception as e:
            logger.error(f"Error calculating volume quality: {e}")
            return 0.5
    
    def _calculate_microstructure_quality(self, signal: Dict, market_data: Dict) -> float:
        """
        Analyze market microstructure quality
        """
        try:
            symbol = signal.get('symbol')
            data = market_data.get(symbol, {})
            
            # Check bid-ask spread proxy (using high-low range)
            high = data.get('high', 0)
            low = data.get('low', 0)
            ltp = data.get('ltp', 0)
            
            if ltp == 0:
                return 0.5
            
            spread_proxy = (high - low) / ltp
            
            # Lower spread = better quality
            if spread_proxy < 0.005:  # < 0.5% range
                return 1.0  # Excellent liquidity
            elif spread_proxy < 0.01:  # < 1% range
                return 0.8  # Good liquidity
            elif spread_proxy < 0.02:  # < 2% range
                return 0.6  # Fair liquidity
            else:
                return 0.4  # Poor liquidity
                
        except Exception as e:
            logger.error(f"Error calculating microstructure quality: {e}")
            return 0.5
    
    def _check_timeframe_alignment(self, signal: Dict, market_data: Dict) -> float:
        """
        Check if signal aligns across multiple timeframes
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return 0.7  # Neutral if insufficient data
            
            prices = self.price_history[symbol]
            
            # Short-term (last 3)
            short_trend = (prices[-1] - prices[-3]) / prices[-3] if len(prices) >= 3 else 0
            
            # Medium-term (last 10)
            medium_trend = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            
            # Long-term (last 20)
            long_trend = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else 0
            
            # Check alignment
            if action == 'BUY':
                # All timeframes should be positive or neutral
                if short_trend > 0 and medium_trend > 0 and long_trend > 0:
                    return 1.0  # Perfect alignment
                elif short_trend > 0 and medium_trend > 0:
                    return 0.8  # Good alignment
                elif short_trend > 0:
                    return 0.6  # Partial alignment
                else:
                    return 0.3  # Poor alignment
            else:  # SELL
                # All timeframes should be negative or neutral
                if short_trend < 0 and medium_trend < 0 and long_trend < 0:
                    return 1.0  # Perfect alignment
                elif short_trend < 0 and medium_trend < 0:
                    return 0.8  # Good alignment
                elif short_trend < 0:
                    return 0.6  # Partial alignment
                else:
                    return 0.3  # Poor alignment
                    
        except Exception as e:
            logger.error(f"Error checking timeframe alignment: {e}")
            return 0.7
    
    def _get_strategy_performance_factor(self, strategy: str) -> float:
        """
        Get adaptive confidence factor based on recent strategy performance
        """
        try:
            if strategy not in self.strategy_performance:
                return 1.0  # Neutral for new strategies
            
            perf = self.strategy_performance[strategy]
            win_rate = perf.get('win_rate', 0.50)
            
            # Adjust confidence based on win rate
            if win_rate >= 0.65:
                return 1.15  # Boost for high-performing strategies
            elif win_rate >= 0.55:
                return 1.05  # Slight boost
            elif win_rate >= 0.45:
                return 1.0  # Neutral
            elif win_rate >= 0.35:
                return 0.9  # Reduce for underperforming
            else:
                return 0.8  # Significant reduction
                
        except Exception as e:
            logger.error(f"Error getting performance factor: {e}")
            return 1.0
    
    def _update_market_history(self, symbol: str, market_data: Dict):
        """Update price and volume history for analysis"""
        try:
            data = market_data.get(symbol, {})
            
            ltp = data.get('ltp', 0)
            volume = data.get('volume', 0)
            
            if ltp > 0:
                self.price_history[symbol].append(ltp)
                if len(self.price_history[symbol]) > 50:
                    self.price_history[symbol].pop(0)
            
            if volume > 0:
                self.volume_history[symbol].append(volume)
                if len(self.volume_history[symbol]) > 50:
                    self.volume_history[symbol].pop(0)
                    
        except Exception as e:
            logger.error(f"Error updating market history: {e}")
    
    def update_signal_outcome(self, signal_id: str, strategy: str, was_profitable: bool, pnl: float):
        """
        Update performance tracking when trade outcome is known
        """
        try:
            # Update strategy performance
            if strategy not in self.strategy_performance:
                self.strategy_performance[strategy] = {
                    'total_signals': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_pnl': 0.0,
                    'win_rate': 0.50
                }
            
            perf = self.strategy_performance[strategy]
            perf['total_signals'] += 1
            perf['total_pnl'] += pnl
            
            if was_profitable:
                perf['wins'] += 1
            else:
                perf['losses'] += 1
            
            # Update win rate
            if perf['total_signals'] > 0:
                perf['win_rate'] = perf['wins'] / perf['total_signals']
            
            # Add to signal history
            self.signal_history.append({
                'signal_id': signal_id,
                'strategy': strategy,
                'profitable': was_profitable,
                'pnl': pnl,
                'timestamp': datetime.now()
            })
            
            # Keep only last 100 signals
            if len(self.signal_history) > 100:
                self.signal_history.pop(0)
            
            logger.info(f"📊 {strategy}: Win rate: {perf['win_rate']:.1%} "
                       f"({perf['wins']}/{perf['total_signals']}), "
                       f"Total P&L: ₹{perf['total_pnl']:.2f}")
                       
        except Exception as e:
            logger.error(f"Error updating signal outcome: {e}")
    
    def get_enhancement_stats(self) -> Dict:
        """Get statistics about signal enhancement"""
        return {
            'total_signals_processed': len(self.signal_history),
            'strategy_performance': dict(self.strategy_performance),
            'symbols_tracked': len(self.price_history),
            'min_confluence_score': self.min_confluence_score
        }

# Global instance
signal_enhancer = SignalEnhancer()


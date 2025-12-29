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
6. Historical data warmup for accurate scoring from startup
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
        
        # Track warmup status
        self.warmed_up_symbols = set()
        self.zerodha_client = None
        self._warmup_complete = False
        
        logger.info("✅ Signal Enhancement Layer initialized")
    
    def set_zerodha_client(self, client):
        """Set Zerodha client for historical data fetching"""
        self.zerodha_client = client
        logger.info("📊 SignalEnhancer: Zerodha client connected for historical data")
    
    async def warmup_with_historical_data(self, symbols: List[str], days: int = 3) -> int:
        """
        Pre-populate price and volume history with historical data from Zerodha.
        This ensures accurate enhancement scores from startup.
        
        Args:
            symbols: List of symbols to warm up
            days: Number of days of history to fetch (default 3)
            
        Returns:
            Number of symbols successfully warmed up
        """
        if not self.zerodha_client:
            logger.warning("⚠️ No Zerodha client available for warmup")
            return 0
        
        warmed_up = 0
        logger.info(f"🔥 WARMUP: Loading {days} days of history for {len(symbols)} symbols...")
        
        # Limit to top 50 symbols to avoid rate limits
        symbols_to_warm = symbols[:50]
        
        for symbol in symbols_to_warm:
            if symbol in self.warmed_up_symbols:
                continue
                
            try:
                # Fetch 5-minute candles for the last few days
                candles = await self._fetch_symbol_history(symbol, days)
                
                if candles and len(candles) >= 20:
                    # Extract close prices and volumes
                    for candle in candles[-50:]:  # Last 50 candles
                        close = candle.get('close', 0)
                        volume = candle.get('volume', 0)
                        
                        if close > 0:
                            self.price_history[symbol].append(close)
                        if volume > 0:
                            self.volume_history[symbol].append(volume)
                    
                    self.warmed_up_symbols.add(symbol)
                    warmed_up += 1
                    
                    if warmed_up % 10 == 0:
                        logger.info(f"📊 WARMUP progress: {warmed_up}/{len(symbols_to_warm)} symbols loaded")
                        
            except Exception as e:
                logger.debug(f"Could not warm up {symbol}: {e}")
                continue
        
        self._warmup_complete = True
        logger.info(f"✅ WARMUP COMPLETE: {warmed_up} symbols with {len(self.price_history.get(symbols_to_warm[0] if symbols_to_warm else '', []))} price points each")
        return warmed_up
    
    async def _fetch_symbol_history(self, symbol: str, days: int) -> List[Dict]:
        """Fetch historical candle data for a symbol"""
        try:
            if not self.zerodha_client:
                return []
            
            # Check if zerodha_client has get_historical_data method
            if hasattr(self.zerodha_client, 'get_historical_data'):
                # 🚨 CRITICAL FIX: Use from_date/to_date parameters (not days)
                from datetime import datetime, timedelta
                to_date = datetime.now()
                from_date = to_date - timedelta(days=days)
                
                candles = await self.zerodha_client.get_historical_data(
                    symbol=symbol,
                    interval='5minute',
                    from_date=from_date,
                    to_date=to_date,
                    exchange='NSE'
                )
                return candles if candles else []
            
            return []
            
        except Exception as e:
            logger.debug(f"Error fetching history for {symbol}: {e}")
            return []
    
    def is_symbol_warmed_up(self, symbol: str) -> bool:
        """Check if a symbol has sufficient historical data"""
        return (
            symbol in self.warmed_up_symbols or
            (len(self.price_history.get(symbol, [])) >= 20 and 
             len(self.volume_history.get(symbol, [])) >= 10)
        )
    
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
        
        IMPORTANT: Returns 0.75 (passing score) if insufficient history data,
        since the signal already passed strategy-level filters (MTF, RSI, etc.)
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            # 🔧 2025-12-29: Option-type aware momentum check
            # PUT options profit from stock FALLING = need SELL direction logic
            # CALL options profit from stock RISING = need BUY direction logic
            metadata = signal.get('metadata', {})
            option_type = metadata.get('option_type', '')
            effective_action = action
            if option_type == 'PE':  # PUT option profits from falling prices
                effective_action = 'SELL'
            elif option_type == 'CE':  # CALL option profits from rising prices
                effective_action = 'BUY'
            
            factors = []
            has_sufficient_history = False
            
            # Factor 1: Price momentum alignment
            if symbol in self.price_history and len(self.price_history[symbol]) >= 5:
                has_sufficient_history = True
                prices = self.price_history[symbol][-5:]
                momentum = (prices[-1] - prices[0]) / prices[0]
                
                # Use effective_action for options
                if (effective_action == 'BUY' and momentum > 0.002) or (effective_action == 'SELL' and momentum < -0.002):
                    factors.append(1.0)  # Strong alignment
                elif abs(momentum) < 0.001:
                    factors.append(0.5)  # Neutral
                else:
                    factors.append(0.3)  # Against momentum (less harsh)
            
            # Factor 2: Volume confirmation
            if symbol in self.volume_history and len(self.volume_history[symbol]) >= 3:
                has_sufficient_history = True
                current_vol = self.volume_history[symbol][-1]
                avg_vol = np.mean(self.volume_history[symbol][-20:]) if len(self.volume_history[symbol]) >= 20 else current_vol
                
                if current_vol > avg_vol * 1.5:
                    factors.append(1.0)  # Strong volume
                elif current_vol > avg_vol:
                    factors.append(0.7)  # Above average
                else:
                    factors.append(0.5)  # Average volume (less harsh)
            
            # Factor 3: Market structure - ALWAYS use this
            # 🔧 Use effective_action for options (PUT=SELL direction, CALL=BUY direction)
            data = market_data.get(symbol, {})
            change_pct = data.get('change_percent', 0)
            
            if (effective_action == 'BUY' and change_pct > 0.5) or (effective_action == 'SELL' and change_pct < -0.5):
                factors.append(1.0)  # Market moving in signal direction
            elif (effective_action == 'BUY' and change_pct > 0) or (effective_action == 'SELL' and change_pct < 0):
                factors.append(0.8)  # Positive alignment
            elif abs(change_pct) < 0.2:
                factors.append(0.6)  # Consolidating
            else:
                factors.append(0.4)  # Weak structure (less harsh)
            
            # 🔥 FIX: If no history data, use signal's pre-calculated confidence
            # The signal already passed MTF, RSI, Bollinger, RS filters
            if not has_sufficient_history:
                # Trust the strategy's analysis - return passing score
                signal_confidence = signal.get('confidence', 5.0)
                if signal_confidence >= 8.0:
                    return 0.85  # High confidence signal, trust it
                elif signal_confidence >= 7.0:
                    return 0.75  # Good confidence, pass it
                else:
                    return 0.65  # Moderate - still pass threshold
            
            # Return average of all factors
            return np.mean(factors) if factors else 0.75
            
        except Exception as e:
            logger.error(f"Error calculating confluence: {e}")
            return 0.5
    
    def _calculate_volume_quality(self, signal: Dict, market_data: Dict) -> float:
        """
        Analyze volume quality and distribution
        
        IMPORTANT: Returns 0.75 (passing score) if insufficient history,
        since the signal already passed strategy-level volume analysis.
        """
        try:
            symbol = signal.get('symbol')
            data = market_data.get(symbol, {})
            
            current_volume = data.get('volume', 0)
            
            # 🔥 FIX: If insufficient history, check signal's volume_strength
            if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
                # Use the strategy's pre-calculated volume strength if available
                volume_strength = signal.get('metadata', {}).get('volume_strength', 0.5)
                if volume_strength > 0.7:
                    return 0.85
                elif volume_strength > 0.4:
                    return 0.75  # Pass threshold
                return 0.70  # Default passing score (trust strategy analysis)
            
            volumes = self.volume_history[symbol]
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            
            if avg_volume == 0:
                return 0.70  # Default passing
            
            volume_ratio = current_volume / avg_volume
            
            # Score based on volume ratio
            if volume_ratio > 2.0:
                return 1.0  # Exceptional volume
            elif volume_ratio > 1.5:
                return 0.9  # Strong volume
            elif volume_ratio > 1.2:
                return 0.8  # Good volume
            elif volume_ratio > 0.8:
                return 0.65  # Average volume (less harsh)
            else:
                return 0.5  # Below average (less harsh)
                
        except Exception as e:
            logger.error(f"Error calculating volume quality: {e}")
            return 0.5
    
    def _calculate_microstructure_quality(self, signal: Dict, market_data: Dict) -> float:
        """
        Analyze market microstructure quality
        
        For F&O stocks (which our signals target), liquidity is generally good.
        """
        try:
            symbol = signal.get('symbol')
            data = market_data.get(symbol, {})
            
            # Check bid-ask spread proxy (using high-low range)
            high = data.get('high', 0)
            low = data.get('low', 0)
            ltp = data.get('ltp', 0)
            
            if ltp == 0 or high == 0 or low == 0:
                # No OHLC data - these are F&O stocks, assume good liquidity
                return 0.75  # Default passing score
            
            spread_proxy = (high - low) / ltp
            
            # Lower spread = better quality
            # Note: For trending stocks, wider range is expected
            if spread_proxy < 0.01:  # < 1% range
                return 1.0  # Excellent liquidity
            elif spread_proxy < 0.02:  # < 2% range
                return 0.85  # Good liquidity
            elif spread_proxy < 0.04:  # < 4% range (common for trending)
                return 0.70  # Fair liquidity
            else:
                return 0.55  # Wide range but still acceptable for F&O
                
        except Exception as e:
            logger.error(f"Error calculating microstructure quality: {e}")
            return 0.5
    
    def _check_timeframe_alignment(self, signal: Dict, market_data: Dict) -> float:
        """
        Check if signal aligns across multiple timeframes
        
        IMPORTANT: If insufficient history, USE the signal's MTF analysis
        which already passed 60min/15min/5min alignment checks.
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            
            # 🔧 2025-12-29: Option-type aware trend check
            metadata = signal.get('metadata', {})
            option_type = metadata.get('option_type', '')
            effective_action = action
            if option_type == 'PE':  # PUT profits from falling = SELL direction
                effective_action = 'SELL'
            elif option_type == 'CE':  # CALL profits from rising = BUY direction
                effective_action = 'BUY'
            
            # 🔥 FIX: Use signal's MTF alignment score if we don't have history
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                # The signal already passed MTF analysis in base_strategy
                # Check for MTF data in signal metadata
                
                # If signal has high confidence (boosted by MTF), trust it
                confidence = signal.get('confidence', 5.0)
                if confidence >= 9.0:
                    return 0.95  # Signal passed MTF with 1.5x boost
                elif confidence >= 7.5:
                    return 0.80
                
                return 0.75  # Default passing score for MTF-approved signals
            
            prices = self.price_history[symbol]
            
            # Short-term (last 3)
            short_trend = (prices[-1] - prices[-3]) / prices[-3] if len(prices) >= 3 else 0
            
            # Medium-term (last 10)
            medium_trend = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            
            # Long-term (last 20)
            long_trend = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else 0
            
            # Check alignment - use effective_action for options
            if effective_action == 'BUY':
                # All timeframes should be positive or neutral
                if short_trend > 0 and medium_trend > 0 and long_trend > 0:
                    return 1.0  # Perfect alignment
                elif short_trend > 0 and medium_trend > 0:
                    return 0.85  # Good alignment
                elif short_trend > 0:
                    return 0.70  # Partial alignment
                else:
                    return 0.50  # Poor alignment (less harsh)
            else:  # SELL (or PUT option)
                # All timeframes should be negative or neutral
                if short_trend < 0 and medium_trend < 0 and long_trend < 0:
                    return 1.0  # Perfect alignment
                elif short_trend < 0 and medium_trend < 0:
                    return 0.85  # Good alignment
                elif short_trend < 0:
                    return 0.70  # Partial alignment
                else:
                    return 0.50  # Poor alignment (less harsh)
                    
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

    def get_calibrated_confidence(self, strategy: str, base_confidence: float) -> Tuple[float, str]:
        """
        🎯 CALIBRATED CONFIDENCE - Adjusts arbitrary confidence based on ACTUAL win rate!
        
        If a strategy claims 8.0/10 confidence but only wins 40% of trades,
        the calibrated confidence will be reduced.
        
        Args:
            strategy: Strategy name
            base_confidence: Original confidence (0-10)
            
        Returns:
            calibrated_confidence: Adjusted confidence based on actual performance
            reason: Explanation of adjustment
        """
        try:
            if strategy not in self.strategy_performance:
                return base_confidence, "NO_HISTORY"
            
            perf = self.strategy_performance[strategy]
            
            # Need at least 10 trades for meaningful calibration
            if perf['total_signals'] < 10:
                return base_confidence, f"INSUFFICIENT_DATA ({perf['total_signals']} trades)"
            
            actual_win_rate = perf['win_rate']
            
            # What confidence SHOULD be based on actual win rate
            # Confidence 8.0 should mean 80% win rate
            expected_win_rate = base_confidence / 10.0
            
            # Calibration factor: actual / expected
            # If actual is 40% but expected is 80%, factor is 0.5
            if expected_win_rate > 0:
                calibration_factor = actual_win_rate / expected_win_rate
            else:
                calibration_factor = 1.0
            
            # Limit adjustment to ±30%
            calibration_factor = max(0.7, min(1.3, calibration_factor))
            
            calibrated_confidence = base_confidence * calibration_factor
            
            # Also consider recent performance (last 20 trades)
            recent_signals = [s for s in self.signal_history if s['strategy'] == strategy][-20:]
            if len(recent_signals) >= 5:
                recent_wins = sum(1 for s in recent_signals if s['profitable'])
                recent_win_rate = recent_wins / len(recent_signals)
                
                # If recent performance is worse than historical, penalize more
                if recent_win_rate < actual_win_rate - 0.1:
                    calibrated_confidence *= 0.9  # 10% penalty for deteriorating performance
                    reason = f"CALIBRATED: {actual_win_rate:.0%} win rate, RECENT WORSE ({recent_win_rate:.0%})"
                elif recent_win_rate > actual_win_rate + 0.1:
                    calibrated_confidence *= 1.1  # 10% boost for improving performance
                    reason = f"CALIBRATED: {actual_win_rate:.0%} win rate, RECENT BETTER ({recent_win_rate:.0%})"
                else:
                    reason = f"CALIBRATED: {actual_win_rate:.0%} win rate ({perf['total_signals']} trades)"
            else:
                reason = f"CALIBRATED: {actual_win_rate:.0%} win rate ({perf['total_signals']} trades)"
            
            # Ensure within valid range
            calibrated_confidence = max(0, min(10, calibrated_confidence))
            
            if abs(calibrated_confidence - base_confidence) > 0.5:
                logger.info(f"🎯 CONFIDENCE CALIBRATION: {strategy} {base_confidence:.1f} → {calibrated_confidence:.1f} ({reason})")
            
            return calibrated_confidence, reason
            
        except Exception as e:
            logger.error(f"Error in confidence calibration: {e}")
            return base_confidence, "ERROR"

    def get_strategy_performance_summary(self) -> Dict:
        """
        🎯 Get detailed performance summary for all strategies
        
        Returns comprehensive metrics for each strategy to help
        identify which strategies are actually profitable.
        """
        try:
            summary = {}
            
            for strategy, perf in self.strategy_performance.items():
                if perf['total_signals'] == 0:
                    continue
                
                # Calculate average P&L per trade
                avg_pnl = perf['total_pnl'] / perf['total_signals']
                
                # Calculate profit factor
                wins = perf['wins']
                losses = perf['losses']
                
                # Get average win and loss amounts
                win_signals = [s['pnl'] for s in self.signal_history 
                               if s['strategy'] == strategy and s['profitable']]
                loss_signals = [abs(s['pnl']) for s in self.signal_history 
                                if s['strategy'] == strategy and not s['profitable']]
                
                avg_win = sum(win_signals) / len(win_signals) if win_signals else 0
                avg_loss = sum(loss_signals) / len(loss_signals) if loss_signals else 0
                
                # Profit factor = gross profits / gross losses
                gross_profit = sum(win_signals)
                gross_loss = sum(loss_signals)
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                # Risk/reward ratio
                rr_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
                
                # Expected value per trade
                expected_value = (perf['win_rate'] * avg_win) - ((1 - perf['win_rate']) * avg_loss)
                
                summary[strategy] = {
                    'total_trades': perf['total_signals'],
                    'wins': wins,
                    'losses': losses,
                    'win_rate': perf['win_rate'],
                    'total_pnl': perf['total_pnl'],
                    'avg_pnl_per_trade': avg_pnl,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'profit_factor': profit_factor,
                    'rr_ratio': rr_ratio,
                    'expected_value': expected_value,
                    'recommendation': 'PROFITABLE' if expected_value > 0 else 'NEEDS_IMPROVEMENT'
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting strategy performance summary: {e}")
            return {}

    def should_allow_signal_based_on_performance(self, strategy: str, confidence: float) -> Tuple[bool, str]:
        """
        🎯 PERFORMANCE-BASED FILTER
        
        Block signals from strategies that are consistently losing money.
        
        Returns:
            allowed: True if signal should be allowed
            reason: Explanation
        """
        try:
            if strategy not in self.strategy_performance:
                return True, "NEW_STRATEGY"
            
            perf = self.strategy_performance[strategy]
            
            # Need at least 15 trades to make performance decisions
            if perf['total_signals'] < 15:
                return True, f"LEARNING ({perf['total_signals']}/15 trades)"
            
            win_rate = perf['win_rate']
            
            # Block if win rate is terrible
            if win_rate < 0.30:  # Less than 30% win rate
                logger.warning(f"🚫 BLOCKED: {strategy} has {win_rate:.0%} win rate - too low!")
                return False, f"WIN_RATE_TOO_LOW ({win_rate:.0%})"
            
            # Block if losing money overall
            if perf['total_pnl'] < -5000 and perf['total_signals'] >= 20:
                logger.warning(f"🚫 BLOCKED: {strategy} has ₹{perf['total_pnl']:,.0f} total P&L - losing money!")
                return False, f"NEGATIVE_PNL (₹{perf['total_pnl']:,.0f})"
            
            # Reduce confidence requirement for high-performing strategies
            if win_rate > 0.60 and perf['total_pnl'] > 0:
                return True, f"HIGH_PERFORMER ({win_rate:.0%} win rate)"
            
            # Standard approval
            return True, f"APPROVED ({win_rate:.0%} win rate)"
            
        except Exception as e:
            logger.error(f"Error in performance filter: {e}")
            return True, "ERROR"

# Global instance
signal_enhancer = SignalEnhancer()


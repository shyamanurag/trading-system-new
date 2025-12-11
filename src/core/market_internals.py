"""
Market Internals Analysis System
================================
Comprehensive market internals for better bias detection and regime identification
Includes breadth, volatility, volume profile, and market microstructure analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class MarketInternals:
    """Complete market internals snapshot"""
    # Breadth Indicators
    advance_decline_ratio: float = 0.0  # Advancing stocks / Declining stocks
    advance_decline_line: float = 0.0  # Cumulative A-D
    stocks_above_vwap: float = 0.0  # % of stocks trading above VWAP
    new_highs_lows: float = 0.0  # New 52-week highs - lows
    
    # Volume Analysis
    up_volume_ratio: float = 0.0  # Volume in advancing stocks / Total volume
    volume_breadth: float = 0.0  # Up volume - Down volume
    institutional_flow: float = 0.0  # Large trade volume ratio
    
    # Volatility Metrics
    intraday_volatility: float = 0.0  # Current volatility vs average
    vix_level: float = 0.0  # India VIX level
    vix_change: float = 0.0  # VIX change from open
    realized_volatility: float = 0.0  # Actual price movement volatility
    
    # Market Structure
    market_regime: str = "NORMAL"  # TRENDING, CHOPPY, VOLATILE, QUIET
    trend_strength: float = 0.0  # 0-100 scale
    choppiness_index: float = 0.0  # 0-100 scale (higher = more choppy)
    
    # Sector Rotation
    leading_sectors: List[str] = field(default_factory=list)
    lagging_sectors: List[str] = field(default_factory=list)
    sector_rotation_score: float = 0.0  # Rotation intensity
    
    # Time-based Patterns
    opening_range_position: float = 0.0  # Where price is within opening range
    time_weighted_trend: float = 0.0  # Trend weighted by time of day
    
    # Composite Scores
    bullish_score: float = 0.0  # 0-100
    bearish_score: float = 0.0  # 0-100
    neutral_score: float = 0.0  # 0-100
    
    timestamp: datetime = field(default_factory=datetime.now)

class MarketInternalsAnalyzer:
    """
    Advanced Market Internals Analyzer
    ==================================
    Provides comprehensive market analysis beyond simple price movement
    """
    
    def __init__(self):
        # Historical data storage
        self.price_history = {}  # symbol -> deque of prices
        self.volume_history = {}  # symbol -> deque of volumes
        self.breadth_history = deque(maxlen=100)  # Historical breadth data
        
        # Market regime detection
        self.regime_history = deque(maxlen=20)
        self.current_regime = "NORMAL"
        self.regime_confidence = 0.0
        
        # Volatility tracking
        self.volatility_baseline = {}  # symbol -> baseline volatility
        self.vix_history = deque(maxlen=50)
        
        # Opening range tracking
        self.opening_ranges = {}  # symbol -> (high, low) for first 30 mins
        self.opening_range_established = False
        
        # Sector performance
        self.sector_performance = {}
        self.sector_constituents = {
            'BANKING': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN', 
                       'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB'],
            'IT': ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM', 
                  'MINDTREE', 'MPHASIS', 'LTTS', 'PERSISTENT', 'COFORGE'],
            'AUTO': ['MARUTI', 'TATAMOTORS', 'BAJAJ-AUTO', 'M&M', 'HEROMOTOCO',
                    'EICHERMOT', 'TVSMOTOR', 'ASHOKLEY', 'ESCORTS'],
            'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON',
                      'LUPIN', 'GLENMARK', 'TORNTPHARM', 'ALKEM'],
            'METALS': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'COALINDIA',
                      'NMDC', 'NATIONALUM', 'SAIL', 'MOIL'],
            'ENERGY': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL',
                      'PETRONET', 'CASTROLIND', 'HINDPETRO'],
            'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR',
                    'MARICO', 'GODREJCP', 'COLPAL', 'EMAMILTD'],
            'REALTY': ['DLF', 'GODREJPROP', 'OBEROIRLTY', 'PRESTIGE', 'BRIGADE',
                      'PHOENIXLTD', 'SOBHA', 'SUNTECK']
        }
        
        # Choppiness detection
        self.choppiness_window = 14
        self.choppiness_threshold = 61.8  # Above this = choppy market
        
        logger.info("✅ Market Internals Analyzer initialized")
    
    async def analyze_market_internals(self, market_data: Dict) -> MarketInternals:
        """
        Perform comprehensive market internals analysis
        
        Args:
            market_data: Current market data for all symbols
            
        Returns:
            MarketInternals object with complete analysis
        """
        try:
            internals = MarketInternals()
            
            # 1. Calculate Market Breadth
            breadth_metrics = self._calculate_breadth(market_data)
            internals.advance_decline_ratio = breadth_metrics['ad_ratio']
            internals.advance_decline_line = breadth_metrics['ad_line']
            internals.stocks_above_vwap = breadth_metrics['above_vwap']
            internals.new_highs_lows = breadth_metrics['highs_lows']
            
            # 2. Analyze Volume Profile
            volume_metrics = self._analyze_volume_profile(market_data)
            internals.up_volume_ratio = volume_metrics['up_volume_ratio']
            internals.volume_breadth = volume_metrics['volume_breadth']
            internals.institutional_flow = volume_metrics['institutional_flow']
            
            # 3. Calculate Volatility Metrics
            volatility_metrics = self._calculate_volatility_metrics(market_data)
            internals.intraday_volatility = volatility_metrics['intraday_vol']
            internals.vix_level = volatility_metrics['vix_level']
            internals.vix_change = volatility_metrics['vix_change']
            internals.realized_volatility = volatility_metrics['realized_vol']
            
            # 4. Detect Market Regime
            regime_analysis = self._detect_market_regime(market_data, breadth_metrics, volatility_metrics)
            internals.market_regime = regime_analysis['regime']
            internals.trend_strength = regime_analysis['trend_strength']
            internals.choppiness_index = regime_analysis['choppiness']
            
            # 5. Analyze Sector Rotation
            sector_analysis = self._analyze_sector_rotation(market_data)
            internals.leading_sectors = sector_analysis['leaders']
            internals.lagging_sectors = sector_analysis['laggards']
            internals.sector_rotation_score = sector_analysis['rotation_score']
            
            # 6. Time-based Analysis
            time_analysis = self._analyze_time_patterns(market_data)
            internals.opening_range_position = time_analysis['or_position']
            internals.time_weighted_trend = time_analysis['weighted_trend']
            
            # 7. Calculate Composite Scores
            composite_scores = self._calculate_composite_scores(
                breadth_metrics, volume_metrics, volatility_metrics, 
                regime_analysis, sector_analysis
            )
            internals.bullish_score = composite_scores['bullish']
            internals.bearish_score = composite_scores['bearish']
            internals.neutral_score = composite_scores['neutral']
            
            # Log summary
            logger.info(f"📊 MARKET INTERNALS: Regime={internals.market_regime}, "
                       f"A/D={internals.advance_decline_ratio:.2f}, "
                       f"Choppiness={internals.choppiness_index:.1f}, "
                       f"Scores: Bull={internals.bullish_score:.1f}, "
                       f"Bear={internals.bearish_score:.1f}, "
                       f"Neutral={internals.neutral_score:.1f}")
            
            return internals
            
        except Exception as e:
            logger.error(f"Error analyzing market internals: {e}")
            return MarketInternals()
    
    def _calculate_breadth(self, market_data: Dict) -> Dict:
        """Calculate market breadth indicators"""
        try:
            advancing = 0
            declining = 0
            unchanged = 0
            above_vwap = 0
            total_stocks = 0
            new_highs = 0
            new_lows = 0
            
            for symbol, data in market_data.items():
                # Skip indices
                if symbol.endswith('-I'):
                    continue
                    
                total_stocks += 1
                
                # Price change
                change_pct = data.get('change_percent', 0)
                if change_pct > 0.1:
                    advancing += 1
                elif change_pct < -0.1:
                    declining += 1
                else:
                    unchanged += 1
                
                # VWAP comparison
                ltp = data.get('ltp', 0)
                vwap = data.get('vwap', ltp)  # Use LTP if VWAP not available
                if ltp > vwap:
                    above_vwap += 1
                
                # 52-week highs/lows (simplified - would need historical data)
                high_52w = data.get('year_high', 0)
                low_52w = data.get('year_low', 0)
                if high_52w > 0 and ltp >= high_52w * 0.98:  # Within 2% of 52w high
                    new_highs += 1
                elif low_52w > 0 and ltp <= low_52w * 1.02:  # Within 2% of 52w low
                    new_lows += 1
            
            # Calculate ratios
            ad_ratio = advancing / declining if declining > 0 else advancing
            above_vwap_pct = (above_vwap / total_stocks * 100) if total_stocks > 0 else 50
            
            # Update A-D line
            ad_diff = advancing - declining
            self.breadth_history.append(ad_diff)
            ad_line = sum(self.breadth_history)
            
            return {
                'ad_ratio': ad_ratio,
                'ad_line': ad_line,
                'above_vwap': above_vwap_pct,
                'highs_lows': new_highs - new_lows,
                'advancing': advancing,
                'declining': declining,
                'unchanged': unchanged
            }
            
        except Exception as e:
            logger.error(f"Error calculating breadth: {e}")
            return {
                'ad_ratio': 1.0,
                'ad_line': 0,
                'above_vwap': 50,
                'highs_lows': 0,
                'advancing': 0,
                'declining': 0,
                'unchanged': 0
            }
    
    def _analyze_volume_profile(self, market_data: Dict) -> Dict:
        """Analyze volume distribution and flow"""
        try:
            up_volume = 0
            down_volume = 0
            total_volume = 0
            large_trades_volume = 0
            
            for symbol, data in market_data.items():
                # Skip indices
                if symbol.endswith('-I'):
                    continue
                
                volume = data.get('volume', 0)
                change_pct = data.get('change_percent', 0)
                
                total_volume += volume
                
                if change_pct > 0:
                    up_volume += volume
                else:
                    down_volume += volume
                
                # Detect institutional volume (simplified)
                avg_trade_size = data.get('avg_trade_size', 0)
                if avg_trade_size > 10000:  # Large average trade size
                    large_trades_volume += volume
            
            up_volume_ratio = (up_volume / total_volume * 100) if total_volume > 0 else 50
            volume_breadth = up_volume - down_volume
            institutional_ratio = (large_trades_volume / total_volume * 100) if total_volume > 0 else 0
            
            return {
                'up_volume_ratio': up_volume_ratio,
                'volume_breadth': volume_breadth,
                'institutional_flow': institutional_ratio,
                'total_volume': total_volume
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return {
                'up_volume_ratio': 50,
                'volume_breadth': 0,
                'institutional_flow': 0,
                'total_volume': 0
            }
    
    def _calculate_volatility_metrics(self, market_data: Dict) -> Dict:
        """Calculate various volatility metrics"""
        try:
            # Get VIX data if available
            vix_data = market_data.get('INDIAVIX-I', {})
            vix_level = vix_data.get('ltp', 15)  # Default to 15 if not available
            vix_open = vix_data.get('open', vix_level)
            vix_change = ((vix_level - vix_open) / vix_open * 100) if vix_open > 0 else 0
            
            # Calculate intraday volatility
            price_ranges = []
            for symbol, data in market_data.items():
                if symbol.endswith('-I'):
                    continue
                    
                high = data.get('high', 0)
                low = data.get('low', 0)
                close = data.get('ltp', 0)
                
                if high > 0 and low > 0 and close > 0:
                    # True Range as % of price
                    true_range_pct = ((high - low) / close) * 100
                    price_ranges.append(true_range_pct)
            
            # Average intraday volatility
            intraday_vol = np.mean(price_ranges) if price_ranges else 1.0
            
            # Calculate realized volatility (simplified)
            if len(self.breadth_history) > 5:
                recent_changes = list(self.breadth_history)[-5:]
                realized_vol = np.std(recent_changes) if recent_changes else 1.0
            else:
                realized_vol = intraday_vol
            
            return {
                'vix_level': vix_level,
                'vix_change': vix_change,
                'intraday_vol': intraday_vol,
                'realized_vol': realized_vol
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {e}")
            return {
                'vix_level': 15,
                'vix_change': 0,
                'intraday_vol': 1.0,
                'realized_vol': 1.0
            }
    
    def _detect_market_regime(self, market_data: Dict, breadth: Dict, volatility: Dict) -> Dict:
        """Detect current market regime"""
        try:
            # Calculate Choppiness Index (for reference, but not sole determinant)
            choppiness = self._calculate_choppiness_index(market_data)
            
            # Determine trend strength
            nifty_data = market_data.get('NIFTY-I', {})
            nifty_change = abs(nifty_data.get('change_percent', 0))
            ad_ratio = breadth['ad_ratio']
            
            # 🚨 FIX: Calculate INTRADAY TREND QUALITY (more reliable than choppiness index)
            # Choppiness Index was returning 100.0 for clear bullish days
            ltp = float(nifty_data.get('ltp', 0))
            open_price = float(nifty_data.get('open', ltp))
            high = float(nifty_data.get('high', ltp))
            low = float(nifty_data.get('low', ltp))
            
            # Intraday directional quality: how close is price to high/low vs middle?
            day_range = high - low
            if day_range > 0 and ltp > 0:
                # 0 = at low, 1 = at high
                range_position = (ltp - low) / day_range
                # Calculate directional strength: closer to 0 or 1 = more directional
                directional_strength = abs(range_position - 0.5) * 2  # 0 = middle (choppy), 1 = at extremes (trending)
                
                # Intraday trend direction
                intraday_move_pct = ((ltp - open_price) / open_price * 100) if open_price > 0 else 0
            else:
                directional_strength = 0.5
                intraday_move_pct = 0
            
            # Trend strength calculation (enhanced with directional quality)
            if ad_ratio > 2 or ad_ratio < 0.5:  # Strong breadth
                trend_strength = min(100, nifty_change * 20 + 40)
            elif ad_ratio > 1.5 or ad_ratio < 0.67:  # Moderate breadth
                trend_strength = min(100, nifty_change * 15 + 20)
            else:  # Weak breadth
                trend_strength = min(100, nifty_change * 10)
            
            # 🎯 ENHANCED: Boost trend strength if price is directional
            if directional_strength > 0.7:  # Price near high or low
                trend_strength = min(100, trend_strength + 20)
            
            # Determine regime - 🚨 FIX: Prioritize actual movement over choppiness index
            vix_level = volatility['vix_level']
            intraday_vol = volatility['intraday_vol']
            
            # 🎯 CRITICAL FIX: If NIFTY has strong directional move, it's TRENDING not CHOPPY
            # Previous bug: NIFTY +0.73% with A/D 1.28 was marked CHOPPY
            is_strong_intraday_move = abs(intraday_move_pct) >= 0.5  # 0.5%+ intraday = trending
            is_strong_breadth = ad_ratio > 1.2 or ad_ratio < 0.8  # Strong breadth imbalance
            
            if is_strong_intraday_move and is_strong_breadth:
                # Clear trending market - override choppiness
                if vix_level > 25:
                    regime = "VOLATILE_TRENDING"
                else:
                    regime = "TRENDING"
            elif choppiness > self.choppiness_threshold and not is_strong_intraday_move:
                if vix_level > 20:
                    regime = "VOLATILE_CHOPPY"
                else:
                    regime = "CHOPPY"
            elif trend_strength > 60:
                if vix_level > 25:
                    regime = "VOLATILE_TRENDING"
                else:
                    regime = "TRENDING"
            elif intraday_vol < 0.5:
                regime = "QUIET"
            else:
                regime = "NORMAL"
            
            # Store regime history
            self.regime_history.append(regime)
            
            # Calculate regime stability
            if len(self.regime_history) >= 5:
                recent_regimes = list(self.regime_history)[-5:]
                most_common = max(set(recent_regimes), key=recent_regimes.count)
                regime_confidence = recent_regimes.count(most_common) / 5 * 100
            else:
                regime_confidence = 50
            
            return {
                'regime': regime,
                'trend_strength': trend_strength,
                'choppiness': choppiness,
                'regime_confidence': regime_confidence
            }
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {
                'regime': 'NORMAL',
                'trend_strength': 50,
                'choppiness': 50,
                'regime_confidence': 50
            }
    
    def _calculate_choppiness_index(self, market_data: Dict) -> float:
        """
        Calculate Choppiness Index for market
        
        🔥 FIX: Use actual 5-minute candle data instead of storing same day OHLC repeatedly.
        The bug was storing day's HIGH/LOW (which don't change) leading to 100% choppiness.
        Now we fetch real intraday candles from Zerodha for proper calculation.
        """
        try:
            # Initialize candle cache if needed
            if not hasattr(self, '_choppiness_candles'):
                self._choppiness_candles = {'candles': [], 'last_fetch': None}
            
            # Fetch 5-minute candles from Zerodha (refresh every 5 minutes)
            current_time = datetime.now()
            should_fetch = (
                self._choppiness_candles['last_fetch'] is None or 
                (current_time - self._choppiness_candles['last_fetch']).total_seconds() > 300
            )
            
            if should_fetch:
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        import asyncio
                        # Fetch last 3 hours of 5-min candles (36 candles)
                        candles = asyncio.get_event_loop().run_until_complete(
                            orchestrator.zerodha_client.get_historical_data(
                                symbol='NIFTY 50',
                                interval='5minute',
                                from_date=current_time - timedelta(hours=3),
                                to_date=current_time
                            )
                        )
                        if candles and len(candles) >= self.choppiness_window:
                            self._choppiness_candles['candles'] = candles[-self.choppiness_window - 1:]
                            self._choppiness_candles['last_fetch'] = current_time
                            logger.debug(f"📊 Choppiness: Fetched {len(candles)} candles for NIFTY")
                except Exception as e:
                    logger.debug(f"Could not fetch candles for choppiness: {e}")
            
            # Use cached candles if available
            candles = self._choppiness_candles.get('candles', [])
            
            if len(candles) < self.choppiness_window:
                # Fallback: Use live tick data to estimate choppiness from price movements
                nifty_data = market_data.get('NIFTY-I', {})
                ltp = nifty_data.get('ltp', 0)
                open_price = nifty_data.get('open', ltp)
                
                if ltp > 0 and open_price > 0:
                    # Simple volatility-based choppiness estimate
                    intraday_change = abs((ltp - open_price) / open_price) * 100
                    
                    # Lower change = more choppy (range-bound)
                    # Higher change = more trending
                    if intraday_change < 0.2:
                        return 75.0  # Very choppy/tight range
                    elif intraday_change < 0.4:
                        return 60.0  # Moderately choppy
                    elif intraday_change < 0.6:
                        return 50.0  # Neutral
                    elif intraday_change < 1.0:
                        return 40.0  # Moderately trending
                    else:
                        return 30.0  # Strong trend
                
                return 50.0  # Neutral default
            
            # Calculate ATR sum from real candles
            atr_sum = 0
            for i in range(1, len(candles)):
                high = candles[i].get('high', 0)
                low = candles[i].get('low', 0)
                prev_close = candles[i-1].get('close', 0)
                
                if high > 0 and low > 0 and prev_close > 0:
                    high_low = high - low
                    high_close = abs(high - prev_close)
                    low_close = abs(low - prev_close)
                    true_range = max(high_low, high_close, low_close)
                    atr_sum += true_range
            
            # Calculate highest high and lowest low
            highest = max(c.get('high', 0) for c in candles)
            lowest = min(c.get('low', float('inf')) for c in candles)
            
            # Choppiness Index formula
            if highest > lowest and atr_sum > 0:
                log_ratio = np.log10(atr_sum / (highest - lowest))
                log_period = np.log10(self.choppiness_window)
                choppiness = 100 * log_ratio / log_period
                return min(100, max(0, choppiness))
            
            return 50.0  # Neutral default
            
        except Exception as e:
            logger.error(f"Error calculating choppiness index: {e}")
            return 50.0
    
    def _analyze_sector_rotation(self, market_data: Dict) -> Dict:
        """Analyze sector rotation patterns"""
        try:
            sector_performances = {}
            
            for sector_name, constituents in self.sector_constituents.items():
                sector_changes = []
                sector_volumes = []
                
                for symbol in constituents:
                    if symbol in market_data:
                        change = market_data[symbol].get('change_percent', 0)
                        volume = market_data[symbol].get('volume', 0)
                        sector_changes.append(change)
                        sector_volumes.append(volume)
                
                if sector_changes:
                    avg_change = np.mean(sector_changes)
                    total_volume = sum(sector_volumes)
                    sector_performances[sector_name] = {
                        'change': avg_change,
                        'volume': total_volume
                    }
            
            # Sort sectors by performance
            sorted_sectors = sorted(sector_performances.items(), 
                                  key=lambda x: x[1]['change'], 
                                  reverse=True)
            
            # Identify leaders and laggards
            leaders = [s[0] for s in sorted_sectors[:3]]
            laggards = [s[0] for s in sorted_sectors[-3:]]
            
            # Calculate rotation score (spread between best and worst)
            if sorted_sectors:
                best_performance = sorted_sectors[0][1]['change']
                worst_performance = sorted_sectors[-1][1]['change']
                rotation_score = abs(best_performance - worst_performance)
            else:
                rotation_score = 0
            
            # Store for history
            self.sector_performance = sector_performances
            
            return {
                'leaders': leaders,
                'laggards': laggards,
                'rotation_score': rotation_score,
                'performances': sector_performances
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sector rotation: {e}")
            return {
                'leaders': [],
                'laggards': [],
                'rotation_score': 0,
                'performances': {}
            }
    
    def _analyze_time_patterns(self, market_data: Dict) -> Dict:
        """Analyze time-based patterns"""
        try:
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Establish opening range (first 30 minutes)
            if current_time.hour == 9 and current_time.minute < 45:
                if not self.opening_range_established:
                    for symbol, data in market_data.items():
                        high = data.get('high', 0)
                        low = data.get('low', 0)
                        if high > 0 and low > 0:
                            self.opening_ranges[symbol] = (high, low)
                    
                    if current_time.minute >= 44:
                        self.opening_range_established = True
            
            # Calculate opening range position for NIFTY
            or_position = 50  # Default neutral
            if 'NIFTY-I' in self.opening_ranges and 'NIFTY-I' in market_data:
                or_high, or_low = self.opening_ranges['NIFTY-I']
                current_price = market_data['NIFTY-I'].get('ltp', 0)
                
                if or_high > or_low and current_price > 0:
                    # Position within opening range (0 = at low, 100 = at high)
                    or_position = ((current_price - or_low) / (or_high - or_low)) * 100
                    or_position = min(100, max(0, or_position))
            
            # Time-weighted trend (stronger weight for established trends)
            time_weight = 1.0
            if current_time.hour < 10:
                time_weight = 0.5  # Opening volatility
            elif current_time.hour < 11:
                time_weight = 0.8  # Early trend
            elif current_time.hour < 14:
                time_weight = 1.0  # Established trend
            else:
                time_weight = 0.7  # Closing volatility
            
            nifty_change = market_data.get('NIFTY-I', {}).get('change_percent', 0)
            weighted_trend = nifty_change * time_weight
            
            return {
                'or_position': or_position,
                'weighted_trend': weighted_trend,
                'time_weight': time_weight
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time patterns: {e}")
            return {
                'or_position': 50,
                'weighted_trend': 0,
                'time_weight': 1.0
            }
    
    def _calculate_composite_scores(self, breadth: Dict, volume: Dict, 
                                   volatility: Dict, regime: Dict, 
                                   sectors: Dict) -> Dict:
        """
        Calculate composite bullish/bearish/neutral scores with comprehensive logic.
        
        Handles all scenarios:
        - Strong bullish (A/D > 1.5, volume confirms, low VIX)
        - Moderate bullish (A/D > 1.15, some confirmation)
        - Strong bearish (A/D < 0.67, volume confirms, high VIX)
        - Moderate bearish (A/D < 0.85, some confirmation)
        - Neutral/Choppy (A/D near 1.0, mixed signals)
        """
        try:
            bullish_score = 0
            bearish_score = 0
            neutral_score = 0
            
            # ============= BREADTH CONTRIBUTION (35% weight) =============
            # A/D ratio is the most important indicator
            ad_ratio = breadth['ad_ratio']
            above_vwap = breadth.get('above_vwap', 50)  # % of stocks above VWAP
            
            # Strong bullish breadth
            if ad_ratio >= 2.0:
                bullish_score += 35
            elif ad_ratio >= 1.5:
                bullish_score += 28
            elif ad_ratio >= 1.25:
                bullish_score += 20
            elif ad_ratio >= 1.1:
                bullish_score += 12
            # Strong bearish breadth
            elif ad_ratio <= 0.5:
                bearish_score += 35
            elif ad_ratio <= 0.67:
                bearish_score += 28
            elif ad_ratio <= 0.80:
                bearish_score += 20
            elif ad_ratio <= 0.90:
                bearish_score += 12
            # Neutral breadth (0.90 - 1.10)
            else:
                neutral_score += 18
            
            # VWAP confirmation (additional breadth signal)
            if above_vwap > 60:
                bullish_score += 5
            elif above_vwap < 40:
                bearish_score += 5
            
            # ============= VOLUME CONTRIBUTION (25% weight) =============
            up_vol_ratio = volume['up_volume_ratio']
            volume_breadth = volume.get('volume_breadth', 0)
            
            # Strong volume confirmation
            if up_vol_ratio >= 70:
                bullish_score += 25
            elif up_vol_ratio >= 60:
                bullish_score += 18
            elif up_vol_ratio >= 55:
                bullish_score += 10
            elif up_vol_ratio <= 30:
                bearish_score += 25
            elif up_vol_ratio <= 40:
                bearish_score += 18
            elif up_vol_ratio <= 45:
                bearish_score += 10
            else:
                neutral_score += 12
            
            # ============= VOLATILITY CONTRIBUTION (20% weight) =============
            vix_level = volatility['vix_level']
            vix_change = volatility.get('vix_change', 0)
            
            # VIX level interpretation
            if vix_level < 13:
                bullish_score += 12  # Complacency - bullish
                neutral_score += 8
            elif vix_level < 18:
                neutral_score += 15  # Normal range
                bullish_score += 5
            elif vix_level < 25:
                neutral_score += 10
                bearish_score += 10  # Elevated concern
            elif vix_level < 35:
                bearish_score += 15  # High fear
                neutral_score += 5
            else:
                bearish_score += 20  # Extreme fear/panic
            
            # VIX change adds context
            if vix_change > 10:  # VIX spiking
                bearish_score += 5
            elif vix_change < -10:  # VIX collapsing
                bullish_score += 5
            
            # ============= REGIME CONTRIBUTION (15% weight) =============
            market_regime = regime['regime']
            choppiness = regime.get('choppiness', 50)
            
            if market_regime == "TRENDING":
                # Trending market - use A/D to determine direction
                if ad_ratio > 1.05:
                    bullish_score += 15
                elif ad_ratio < 0.95:
                    bearish_score += 15
                else:
                    neutral_score += 8
            elif market_regime == "VOLATILE_TRENDING":
                # Volatile but trending - reduce conviction
                if ad_ratio > 1.1:
                    bullish_score += 10
                elif ad_ratio < 0.9:
                    bearish_score += 10
                neutral_score += 5
            elif market_regime in ["CHOPPY", "VOLATILE_CHOPPY"]:
                neutral_score += 15  # Choppy = stay neutral
            elif market_regime == "QUIET":
                neutral_score += 10
                # In quiet markets, lean with breadth
                if ad_ratio > 1.1:
                    bullish_score += 5
                elif ad_ratio < 0.9:
                    bearish_score += 5
            else:
                neutral_score += 10
            
            # ============= SECTOR ROTATION (5% weight) =============
            rotation_score = sectors.get('rotation_score', 0)
            leaders = sectors.get('leaders', [])
            laggards = sectors.get('laggards', [])
            
            # Defensive sectors leading = bearish
            defensive_sectors = ['PHARMA', 'FMCG', 'UTILITIES']
            cyclical_sectors = ['BANKING', 'AUTO', 'REALTY', 'METAL']
            
            defensive_leading = any(s in leaders for s in defensive_sectors)
            cyclical_leading = any(s in leaders for s in cyclical_sectors)
            
            if cyclical_leading and not defensive_leading:
                bullish_score += 5
            elif defensive_leading and not cyclical_leading:
                bearish_score += 5
            else:
                neutral_score += 3
            
            # ============= NORMALIZE TO 100 =============
            total = bullish_score + bearish_score + neutral_score
            if total > 0:
                bullish_score = (bullish_score / total) * 100
                bearish_score = (bearish_score / total) * 100
                neutral_score = (neutral_score / total) * 100
            else:
                # Default to neutral if no signals
                neutral_score = 100
            
            return {
                'bullish': round(bullish_score, 1),
                'bearish': round(bearish_score, 1),
                'neutral': round(neutral_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating composite scores: {e}")
            return {
                'bullish': 33.3,
                'bearish': 33.3,
                'neutral': 33.4
            }
    
    def get_regime_recommendation(self, regime: str) -> Dict:
        """Get trading recommendations based on market regime"""
        recommendations = {
            "TRENDING": {
                "position_size": 1.0,
                "stop_loss_multiplier": 1.5,
                "take_profit_multiplier": 2.0,
                "new_positions_allowed": True,
                "strategy_focus": "momentum"
            },
            "CHOPPY": {
                "position_size": 0.5,
                "stop_loss_multiplier": 0.8,
                "take_profit_multiplier": 1.2,
                "new_positions_allowed": False,
                "strategy_focus": "mean_reversion"
            },
            "VOLATILE_CHOPPY": {
                "position_size": 0.3,
                "stop_loss_multiplier": 0.6,
                "take_profit_multiplier": 1.0,
                "new_positions_allowed": False,
                "strategy_focus": "risk_management"
            },
            "VOLATILE_TRENDING": {
                "position_size": 0.7,
                "stop_loss_multiplier": 2.0,
                "take_profit_multiplier": 3.0,
                "new_positions_allowed": True,
                "strategy_focus": "trend_following"
            },
            "QUIET": {
                "position_size": 0.4,
                "stop_loss_multiplier": 0.5,
                "take_profit_multiplier": 0.8,
                "new_positions_allowed": False,
                "strategy_focus": "scalping"
            },
            "NORMAL": {
                "position_size": 0.8,
                "stop_loss_multiplier": 1.0,
                "take_profit_multiplier": 1.5,
                "new_positions_allowed": True,
                "strategy_focus": "balanced"
            }
        }
        
        return recommendations.get(regime, recommendations["NORMAL"])

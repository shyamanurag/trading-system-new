"""
INSTITUTIONAL-GRADE BASE STRATEGY
Professional foundation with advanced mathematical models and quantitative analysis.

DAVID VS GOLIATH COMPETITIVE ADVANTAGES:
1. Advanced ATR calculation with GARCH volatility modeling
2. Professional risk management with Kelly criterion and VaR
3. Real-time performance attribution and Sharpe ratio tracking
4. Adaptive position sizing based on market regime and volatility
5. Statistical significance testing for all trading decisions
6. Professional execution algorithms with market impact modeling
7. Machine learning enhanced signal validation
8. Institutional-grade performance monitoring and alerting

Built to compete with hedge funds using superior mathematical rigor.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time, timedelta
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
import pytz
import time as time_module
import os
import math
import warnings
warnings.filterwarnings('ignore')

# Import our professional mathematical foundation
from src.core.enhanced_strategy.mathematical_foundation import ProfessionalMathFoundation

logger = logging.getLogger(__name__)

class BaseStrategy:
    """
    INSTITUTIONAL-GRADE BASE STRATEGY
    
    COMPETITIVE ADVANTAGES:
    1. GARCH-ENHANCED ATR: Superior volatility estimation vs simple ATR
    2. KELLY CRITERION: Optimal position sizing vs fixed percentages
    3. REAL-TIME SHARPE: Performance attribution vs basic P&L tracking
    4. VAR MONITORING: Professional risk management vs simple stop losses
    5. STATISTICAL VALIDATION: Significance testing vs gut feelings
    6. ADAPTIVE SIZING: Market regime awareness vs static allocation
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "InstitutionalBaseStrategy"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)
        
        # PROFESSIONAL MATHEMATICAL FOUNDATION - Using static methods
        
        # 🚨 CRITICAL: Duplicate order prevention system (SHARED across ALL strategies)
        # Use class-level dict so ALL strategy instances see ALL orders
        if not hasattr(BaseStrategy, '_global_recent_orders'):
            BaseStrategy._global_recent_orders = {}
        self._recent_orders = BaseStrategy._global_recent_orders  # Point to shared dict
        
        # PROFESSIONAL PERFORMANCE TRACKING
        self.strategy_returns = []
        self.trade_history = []
        self.performance_attribution = {
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'var_95': 0.0,
            'statistical_significance': 1.0,
            'kelly_optimal_size': 0.02
        }
        
        # Signal rate limiting to prevent flooding (not hard caps)
        self.max_signals_per_hour = 50  # Maximum 50 signals per hour
        self.max_signals_per_strategy = 10  # Maximum 10 signals per strategy per hour
        self.signals_generated_this_hour = 0
        self.strategy_signals_this_hour = 0
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        self.hour_start_time = datetime.now(ist)
        
        # Enhanced cooldown control
        self.scalping_cooldown = 30  # 30 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        self.position_cooldowns = {}  # Phantom position cleanup cooldowns
        
        # 🎯 ADAPTIVE ENTRY: Track pending limit orders for smart cancellation
        # {symbol: {'order_id': str, 'action': str, 'limit_price': float, 
        #           'created_at': datetime, 'validity_seconds': int, 'original_signal': dict}}
        self.pending_limit_orders: Dict[str, Dict] = {}
        
        # EMERGENCY STOP LOSS THRESHOLDS (configurable)
        self.emergency_loss_amount = config.get('emergency_loss_amount', -1000)  # ₹1000 default
        self.emergency_loss_percent = config.get('emergency_loss_percent', -2.0)  # 2% default
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
        # 🔥 ZERODHA INTRADAY DATA CACHE for proper GARCH calculations
        # For intraday trading: use 5-minute candles, not daily
        self._intraday_candle_cache = {}  # symbol -> {'candles': [], 'fetched_at': datetime}
        self._garch_cache_expiry_minutes = 30  # Refresh cache every 30 minutes for intraday
        self._garch_cache = {}  # symbol -> {'garch_vol': float, 'atr': float, 'updated_at': datetime}
        
        # 📊 CAMARILLA PIVOTS CACHE (refreshed daily)
        # Professional intraday trading levels using previous day's daily OHLC
        self._camarilla_cache = {}  # symbol -> {'h4': float, 'h3': float, ..., 'l4': float}
        self._camarilla_cache_date = None  # Track cache date for daily refresh
        
        # Symbol filtering and selection
        self.watchlist = set()  # Symbols this strategy is interested in
        self.active_symbols = set()  # Symbols currently being analyzed
        self.symbol_filters = config.get('symbol_filters', {})
        self.max_symbols_to_analyze = config.get('max_symbols_to_analyze', 20)
        
        # CRITICAL: Position Management System
        self.active_positions = {}  # symbol -> position data with strategy linkage
        self.position_metadata = {}  # symbol -> strategy-specific position data
        self.trailing_stops = {}
        self.emergency_exits_processed = {}  # symbol -> timestamp (prevent repeated emergency exits)
        
        # 🎯 MARKET BIAS COORDINATION
        self.market_bias = None  # Will be set by orchestrator
        self.position_entry_times = {}  # symbol -> entry timestamp
        self.failed_options_symbols = set()  # Track symbols that failed subscription
        self._last_known_capital = 0.0  # Cache for capital when API fails
        self._latest_market_data = {}  # Store latest market data for relative strength checks
        
        # 🔥 BASE CAPITAL FOR CONSISTENT POSITION SIZING
        # Problem: Available capital decreases as positions are taken, causing later trades
        # to be sized smaller and rejected by MIN_ORDER_VALUE.
        # Solution: Use a fixed "base capital" for position sizing, refreshed daily.
        self._base_capital = 0.0  # Will be set on first capital fetch each day
        self._base_capital_date = None  # Date when base capital was set
        
        # Signal generation throttling
        self._last_signal_generation = {}  # symbol -> timestamp
        self._signal_throttle_interval = 5.0  # 5 seconds between signals for same symbol
        
        # 🚨 SIGNAL EXPIRY AND EXECUTION THROTTLING
        self.signal_expiry_seconds = 120  # 2 minutes - signals valid for 2 minutes only
        self.execution_throttle_seconds = 30  # 30 seconds between execution attempts
        self.signal_timestamps = {}  # symbol -> signal generation timestamp
        self.last_execution_attempts = {}  # symbol -> last execution attempt timestamp
        self.expired_signals_for_elite = []  # Store expired signals for Elite Recommendations

    def _cleanup_expired_signals(self) -> None:
        """🚨 2-MINUTE SIGNAL VALIDITY: Delete signals older than 2 minutes and route to Elite Recommendations"""
        try:
            current_time = time_module.time()
            expired_symbols = []
            
            for symbol, timestamp in list(self.signal_timestamps.items()):
                age_seconds = current_time - timestamp
                if age_seconds > self.signal_expiry_seconds:
                    expired_symbols.append((symbol, age_seconds))
            
            # Delete expired signals from memory and route to Elite Recommendations
            for symbol, age_seconds in expired_symbols:
                if symbol in self.current_positions:
                    signal = self.current_positions[symbol]
                    if isinstance(signal, dict) and signal.get('action') != 'HOLD':
                        logger.info(f"🗑️ EXPIRED SIGNAL: {symbol} (age: {age_seconds:.1f}s) - Routing to Elite Recommendations")
                        
                        # Route unexecuted signal to Elite Recommendations
                        self._route_expired_signal_to_elite(signal, age_seconds)
                        
                        # Complete removal from system
                        del self.current_positions[symbol]
                
                # CRITICAL: Clean up ALL tracking data for complete removal
                if symbol in self.signal_timestamps:
                    del self.signal_timestamps[symbol]
                if symbol in self.last_execution_attempts:
                    del self.last_execution_attempts[symbol]
                if symbol in self.symbol_cooldowns:
                    del self.symbol_cooldowns[symbol]
                if symbol in self.position_cooldowns:
                    del self.position_cooldowns[symbol]
                
                # Clear recent order tracking to allow fresh signal generation
                recent_order_key = f"recent_order_{symbol}"
                if hasattr(self, '_recent_orders') and recent_order_key in self._recent_orders:
                    del self._recent_orders[recent_order_key]
                    logger.info(f"🧹 CLEARED ORDER HISTORY: {symbol} - Fresh signals now allowed")
                    
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired signals: {e}")
    
    def _route_expired_signal_to_elite(self, signal: Dict, age_seconds: float) -> None:
        """Route expired unexecuted signal to Elite Trade Recommendations"""
        try:
            import requests
            from datetime import datetime
            
            # Prepare expired signal data for Elite Recommendations
            elite_signal = {
                'symbol': signal.get('symbol'),
                'action': signal.get('action'),
                'entry_price': signal.get('entry_price'),
                'stop_loss': signal.get('stop_loss'),
                'target': signal.get('target'),
                'confidence': signal.get('confidence'),
                'strategy': signal.get('strategy', self.name),
                'status': 'EXPIRED_UNEXECUTED',
                'expiry_reason': f'Signal expired after {age_seconds:.0f}s (2-minute validity)',
                'generated_at': signal.get('generated_at', datetime.now().isoformat()),
                'expired_at': datetime.now().isoformat(),
                'signal_age_seconds': age_seconds,
                'metadata': signal.get('metadata', {})
            }
            
            # Try to send to Elite Recommendations API
            try:
                response = requests.post(
                    'http://localhost:8000/api/elite-recommendations/add-expired-signal',
                    json=elite_signal,
                    timeout=2
                )
                
                if response.status_code == 200:
                    logger.info(f"📋 ELITE: Expired signal {signal.get('symbol')} added to recommendations")
                else:
                    logger.debug(f"Elite API returned {response.status_code} for expired signal")
                    
            except requests.exceptions.RequestException:
                # Store locally if API unavailable
                self.expired_signals_for_elite.append(elite_signal)
                # Keep only last 50 expired signals
                if len(self.expired_signals_for_elite) > 50:
                    self.expired_signals_for_elite.pop(0)
                logger.debug(f"Elite API unavailable - stored expired signal locally")
                
        except Exception as e:
            logger.error(f"Error routing expired signal to Elite: {e}")
    
    def _can_execute_signal(self, symbol: str) -> bool:
        """🚨 EXECUTION THROTTLING: Check if signal can be executed (30-second throttle)"""
        try:
            if symbol not in self.last_execution_attempts:
                return True  # First execution attempt
            
            current_time = time_module.time()
            last_attempt = self.last_execution_attempts[symbol]
            time_since_last = current_time - last_attempt
            
            if time_since_last < self.execution_throttle_seconds:
                remaining_time = self.execution_throttle_seconds - time_since_last
                logger.info(f"⏳ EXECUTION THROTTLED: {symbol} ({remaining_time:.1f}s remaining)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking execution throttle: {e}")
            return False
    
    def _record_execution_attempt(self, symbol: str) -> None:
        """Record execution attempt for throttling"""
        try:
            self.last_execution_attempts[symbol] = time_module.time()
            logger.debug(f"📊 Execution attempt recorded: {symbol}")
        except Exception as e:
            logger.error(f"❌ Error recording execution attempt: {e}")
    
    def _track_signal_creation(self, symbol: str) -> None:
        """🚨 SIGNAL TRACKING: Record when a signal is created"""
        try:
            self.signal_timestamps[symbol] = time_module.time()
            logger.debug(f"📝 Signal timestamp recorded: {symbol}")
        except Exception as e:
            logger.error(f"❌ Error tracking signal creation: {e}")
    
    async def on_market_data(self, data: Dict):
        """🚨 BASE SIGNAL PROCESSING: Clean up expired signals before processing"""
        try:
            # 0. Store latest market data for relative strength checks
            self._latest_market_data = data
            
            # 1. Clean up expired signals (older than 5 minutes)
            self._cleanup_expired_signals()
            
            # 2. Call the strategy-specific implementation
            # This method should be overridden by child strategies
            pass
            
        except Exception as e:
            logger.error(f"❌ Error in base on_market_data: {e}")
    
    def purge_symbol_state(self, symbol: str) -> None:
        """Remove cached state for a symbol so strategy decides fresh next cycle."""
        try:
            if symbol in getattr(self, 'current_positions', {}):
                self.current_positions.pop(symbol, None)
            if symbol in getattr(self, 'symbol_cooldowns', {}):
                self.symbol_cooldowns.pop(symbol, None)
            if symbol in getattr(self, 'position_cooldowns', {}):
                self.position_cooldowns.pop(symbol, None)
            if hasattr(self, 'price_history') and isinstance(getattr(self, 'price_history'), dict):
                self.price_history.pop(symbol, None)
            if hasattr(self, 'volume_history') and isinstance(getattr(self, 'volume_history'), dict):
                self.volume_history.pop(symbol, None)
            if symbol in getattr(self, 'active_positions', {}):
                # Do not alter real positions; only clear strategy-side caches
                pass
            logger.info(f"🧹 {self.__class__.__name__}: Purged cached state for {symbol}")
        except Exception as e:
            logger.debug(f"{self.__class__.__name__}: purge_symbol_state failed for {symbol}: {e}")

    def set_market_bias(self, market_bias):
        """Set market bias system for coordinated signal generation"""
        self.market_bias = market_bias
        logger.debug(f"🎯 {self.name}: Market bias system connected")
        
        # Position deduplication and management flags
        self.max_position_age_hours = 24  # Auto-close positions after 24 hours
        self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
        self.profit_lock_percentage = 1.0  # Lock profit at 1%
    
    # ============================================================================
    # 🎯 MULTI-TIMEFRAME ANALYSIS - FEWER TRADES, HIGHER ACCURACY
    # ============================================================================
    
    async def fetch_multi_timeframe_data(self, symbol: str, force_refresh: bool = False) -> bool:
        """
        Fetch MULTI-TIMEFRAME historical data from Zerodha.
        Fetches 5-min, 15-min, and 60-min candles for proper trend confirmation.
        
        This enables the strategy to only take trades when ALL timeframes align,
        resulting in FEWER but HIGHER ACCURACY trades.
        
        🔥 FIX: Now refreshes MTF data every 5 minutes instead of caching forever.
        Stale MTF data was causing BEARISH readings on stocks that were actually rallying.
        """
        try:
            # Initialize MTF storage
            if not hasattr(self, 'mtf_data'):
                self.mtf_data = {}
            if not hasattr(self, '_mtf_fetched'):
                self._mtf_fetched = {}  # Changed to dict for timestamps
            
            # 🔥 FIX: Check if data needs refresh (every 5 minutes)
            current_time = datetime.now()
            refresh_interval_seconds = 300  # 5 minutes
            
            if symbol in self._mtf_fetched and not force_refresh:
                last_fetch = self._mtf_fetched[symbol]
                age_seconds = (current_time - last_fetch).total_seconds()
                if age_seconds < refresh_interval_seconds:
                    return True  # Still fresh, no need to refetch
            
            if symbol not in self.mtf_data:
                self.mtf_data[symbol] = {'5min': [], '15min': [], '60min': []}
            
            # Get Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not hasattr(orchestrator, 'zerodha_client') or not orchestrator.zerodha_client:
                return False
            
            zerodha_client = orchestrator.zerodha_client
            from datetime import datetime, timedelta
            
            # ============= FETCH 5-MINUTE CANDLES =============
            candles_5m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='5minute',
                from_date=datetime.now() - timedelta(days=3),
                to_date=datetime.now()
            )
            if candles_5m and len(candles_5m) >= 14:
                self.mtf_data[symbol]['5min'] = candles_5m[-50:]
            
            # ============= FETCH 15-MINUTE CANDLES =============
            candles_15m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='15minute',
                from_date=datetime.now() - timedelta(days=5),
                to_date=datetime.now()
            )
            if candles_15m and len(candles_15m) >= 14:
                self.mtf_data[symbol]['15min'] = candles_15m[-30:]
            
            # ============= FETCH 60-MINUTE (HOURLY) CANDLES =============
            candles_60m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='60minute',
                from_date=datetime.now() - timedelta(days=10),
                to_date=datetime.now()
            )
            if candles_60m and len(candles_60m) >= 14:
                self.mtf_data[symbol]['60min'] = candles_60m[-20:]
            
            # Record fetch timestamp for refresh logic
            self._mtf_fetched[symbol] = datetime.now()
            
            tf_5m = len(self.mtf_data[symbol]['5min'])
            tf_15m = len(self.mtf_data[symbol]['15min'])
            tf_60m = len(self.mtf_data[symbol]['60min'])
            logger.debug(f"📊 MTF REFRESH: {symbol} - 5min:{tf_5m}, 15min:{tf_15m}, 60min:{tf_60m}")
            
            return True
            
        except Exception as e:
            logger.debug(f"⚠️ MTF fetch error for {symbol}: {e}")
            return False
    
    def _get_indicator_series_from_mtf(self, symbol: str, timeframe: str = '5min', limit: int = 50) -> Dict:
        """
        Get indicator input series from cached Zerodha candles (mtf_data).

        This avoids using per-cycle LTP samples for indicators like RSI/MACD/Bollinger,
        making calculations time-consistent (based on candle closes).

        Returns:
            {
              'opens': List[float],
              'closes': List[float],
              'highs': List[float],
              'lows': List[float],
              'volumes': List[float],
              'source': 'mtf_data' | 'missing'
            }
        """
        try:
            tf = timeframe
            if tf not in ('5min', '15min', '60min'):
                tf = '5min'

            if not hasattr(self, 'mtf_data') or symbol not in self.mtf_data:
                return {'opens': [], 'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'source': 'missing'}

            candles = self.mtf_data.get(symbol, {}).get(tf, []) or []
            if not candles:
                return {'opens': [], 'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'source': 'missing'}

            candles = candles[-max(1, int(limit)):]

            opens = []
            closes = []
            highs = []
            lows = []
            volumes = []

            for c in candles:
                if not isinstance(c, dict):
                    continue
                open_ = float(c.get('open', 0) or 0)
                close = float(c.get('close', 0) or 0)
                high = float(c.get('high', close) or close)
                low = float(c.get('low', close) or close)
                vol = float(c.get('volume', 0) or 0)
                if close > 0:
                    opens.append(open_ if open_ > 0 else close)
                    closes.append(close)
                    highs.append(high)
                    lows.append(low)
                    volumes.append(vol)

            return {'opens': opens, 'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes, 'source': 'mtf_data'}
        except Exception:
            return {'opens': [], 'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'source': 'missing'}

    def analyze_multi_timeframe(self, symbol: str, action: str = None) -> Dict:
        """
        🎯 MULTI-TIMEFRAME ANALYSIS for Higher Accuracy Signals
        
        Strategy: Only take trades when ALL timeframes align
        - 60-min (Hourly): Major trend direction
        - 15-min: Medium-term trend confirmation  
        - 5-min: Entry timing
        
        Returns:
            Dict with 'mtf_aligned', 'direction', 'confidence_multiplier', etc.
        """
        try:
            result = {
                'mtf_aligned': False,
                'direction': 'NEUTRAL',
                'confidence_multiplier': 1.0,
                'timeframes': {'5min': 'NEUTRAL', '15min': 'NEUTRAL', '60min': 'NEUTRAL'},
                'alignment_score': 0,
                'reasoning': ''
            }
            
            if not hasattr(self, 'mtf_data') or symbol not in self.mtf_data:
                result['reasoning'] = 'No MTF data - using single timeframe'
                return result
            
            mtf = self.mtf_data[symbol]
            
            # ============= 60-MINUTE (HOURLY) TREND =============
            # 🚨 CRITICAL FIX: Changed from OR to AND logic + SMA slope detection
            # OR logic caused false BULLISH when price still above SMA but falling
            # AND logic requires BOTH conditions = more NEUTRAL = fewer false conflicts
            trend_60m = 'NEUTRAL'
            if mtf['60min'] and len(mtf['60min']) >= 5:
                closes = [c['close'] for c in mtf['60min'][-10:]]
                sma_5 = np.mean(closes[-5:]) if len(closes) >= 5 else closes[-1]
                sma_5_prev = np.mean(closes[-6:-1]) if len(closes) >= 6 else sma_5
                current = closes[-1]
                prev_close = closes[-2] if len(closes) >= 2 else current
                
                # Momentum: recent price change
                momentum = (current / closes[-3] - 1) * 100 if len(closes) >= 3 else 0
                # SMA slope: is the average itself rising or falling?
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                # Price direction: current candle
                price_direction = (current - prev_close) / prev_close * 100 if prev_close > 0 else 0
                
                # 🎯 AND logic: Require BOTH SMA position AND momentum alignment
                # BULLISH: Price above SMA AND SMA rising AND positive momentum
                if current > sma_5 * 1.002 and sma_slope > 0.05 and momentum > 0.3:
                    trend_60m = 'BULLISH'
                # BEARISH: Price below SMA AND SMA falling AND negative momentum
                elif current < sma_5 * 0.998 and sma_slope < -0.05 and momentum < -0.3:
                    trend_60m = 'BEARISH'
                # Otherwise NEUTRAL - this reduces false conflicts
            result['timeframes']['60min'] = trend_60m
            
            # ============= 15-MINUTE TREND =============
            trend_15m = 'NEUTRAL'
            if mtf['15min'] and len(mtf['15min']) >= 5:
                closes = [c['close'] for c in mtf['15min'][-15:]]
                sma_5 = np.mean(closes[-5:]) if len(closes) >= 5 else closes[-1]
                sma_5_prev = np.mean(closes[-6:-1]) if len(closes) >= 6 else sma_5
                current = closes[-1]
                
                momentum = (current / closes[-3] - 1) * 100 if len(closes) >= 3 else 0
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                
                # 🎯 AND logic for 15-min
                if current > sma_5 * 1.001 and sma_slope > 0.03 and momentum > 0.2:
                    trend_15m = 'BULLISH'
                elif current < sma_5 * 0.999 and sma_slope < -0.03 and momentum < -0.2:
                    trend_15m = 'BEARISH'
            result['timeframes']['15min'] = trend_15m
            
            # ============= 5-MINUTE TREND (Entry Timing) =============
            trend_5m = 'NEUTRAL'
            if mtf['5min'] and len(mtf['5min']) >= 5:
                closes = [c['close'] for c in mtf['5min'][-20:]]
                sma_5 = np.mean(closes[-5:]) if len(closes) >= 5 else closes[-1]
                sma_5_prev = np.mean(closes[-6:-1]) if len(closes) >= 6 else sma_5
                current = closes[-1]
                
                momentum = (current / closes[-2] - 1) * 100 if len(closes) >= 2 else 0
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                
                # 🎯 AND logic for 5-min (slightly looser for entry timing)
                if current > sma_5 and sma_slope > 0.01 and momentum > 0.1:
                    trend_5m = 'BULLISH'
                elif current < sma_5 and sma_slope < -0.01 and momentum < -0.1:
                    trend_5m = 'BEARISH'
            result['timeframes']['5min'] = trend_5m
            
            # ============= ALIGNMENT CHECK =============
            bullish_count = sum(1 for tf in result['timeframes'].values() if tf == 'BULLISH')
            bearish_count = sum(1 for tf in result['timeframes'].values() if tf == 'BEARISH')
            
            # Check alignment with requested action
            action_aligned = True
            if action:
                if action.upper() == 'BUY' and bearish_count > bullish_count:
                    action_aligned = False
                elif action.upper() == 'SELL' and bullish_count > bearish_count:
                    action_aligned = False
            
            # Count NEUTRAL timeframes
            neutral_count = sum(1 for tf in result['timeframes'].values() if tf == 'NEUTRAL')
            
            # PERFECT ALIGNMENT (All 3 timeframes agree)
            if bullish_count == 3:
                result['mtf_aligned'] = True
                result['direction'] = 'BULLISH'
                result['confidence_multiplier'] = 1.5  # +50% confidence boost
                result['alignment_score'] = 3
                result['reasoning'] = '🎯 PERFECT MTF: All timeframes BULLISH'
                
            elif bearish_count == 3:
                result['mtf_aligned'] = True
                result['direction'] = 'BEARISH'
                result['confidence_multiplier'] = 1.5
                result['alignment_score'] = 3
                result['reasoning'] = '🎯 PERFECT MTF: All timeframes BEARISH'
                
            # STRONG ALIGNMENT (2/3 agree, including hourly)
            elif bullish_count == 2 and trend_60m == 'BULLISH':
                result['mtf_aligned'] = True
                result['direction'] = 'BULLISH'
                result['confidence_multiplier'] = 1.25  # +25% boost
                result['alignment_score'] = 2
                result['reasoning'] = '📈 STRONG MTF: Hourly + 1 other BULLISH'
                
            elif bearish_count == 2 and trend_60m == 'BEARISH':
                result['mtf_aligned'] = True
                result['direction'] = 'BEARISH'
                result['confidence_multiplier'] = 1.25
                result['alignment_score'] = 2
                result['reasoning'] = '📉 STRONG MTF: Hourly + 1 other BEARISH'
                
            # 🚨 NEW: NEUTRAL-DOMINANT scenarios - NO CONFLICT, just no strong trend
            # All 3 NEUTRAL = No MTF opinion, let signal through
            # 🔥 FIX: If signal aligns with market bias, DON'T penalize - the market bias IS the confirmation
            elif neutral_count == 3:
                result['mtf_aligned'] = True  # Allow through
                result['direction'] = 'NEUTRAL'
                
                # Check if signal aligns with market bias
                market_bias_direction = None
                if hasattr(self, 'market_bias') and self.market_bias:
                    try:
                        bias_info = self.market_bias.get_bias()
                        market_bias_direction = bias_info.get('bias', 'NEUTRAL')
                    except:
                        pass
                
                # If action aligns with market bias, no penalty (bias IS the confirmation)
                # SELL in BEARISH market or BUY in BULLISH market = aligned
                action_aligns_with_bias = (
                    (action and action.upper() == 'SELL' and market_bias_direction == 'BEARISH') or
                    (action and action.upper() == 'BUY' and market_bias_direction == 'BULLISH')
                )
                
                if action_aligns_with_bias:
                    result['confidence_multiplier'] = 1.0  # No penalty - market bias is confirmation
                    result['reasoning'] = f'⏸️ MTF NEUTRAL but signal aligns with {market_bias_direction} market bias - no penalty'
                else:
                    result['confidence_multiplier'] = 0.95  # Reduced penalty (was 0.90)
                    result['reasoning'] = '⏸️ MTF NEUTRAL: No strong trend detected - signal allowed'
                
                result['alignment_score'] = 0
            
            # 2 NEUTRAL + 1 directional that MATCHES action = Weak support
            elif neutral_count == 2:
                if action and action.upper() == 'BUY' and bullish_count == 1:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BULLISH'
                    result['confidence_multiplier'] = 1.0  # No boost, no penalty
                    result['alignment_score'] = 1
                    result['reasoning'] = '📊 MTF WEAK SUPPORT: 1 BULLISH + 2 NEUTRAL'
                elif action and action.upper() == 'SELL' and bearish_count == 1:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BEARISH'
                    result['confidence_multiplier'] = 1.0
                    result['alignment_score'] = 1
                    result['reasoning'] = '📊 MTF WEAK SUPPORT: 1 BEARISH + 2 NEUTRAL'
                else:
                    # 1 directional that CONFLICTS with action
                    result['mtf_aligned'] = False
                    result['direction'] = 'NEUTRAL'
                    result['confidence_multiplier'] = 0.5  # Penalty for conflict
                    result['alignment_score'] = 0
                    result['reasoning'] = f'⚠️ MTF CONFLICT: 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
            
            # 1 NEUTRAL + mixed signals - check for conflict vs support
            elif neutral_count == 1:
                # 2 in same direction that matches action = good
                if action and action.upper() == 'BUY' and bullish_count == 2:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BULLISH'
                    result['confidence_multiplier'] = 1.15
                    result['alignment_score'] = 2
                    result['reasoning'] = '📈 MTF SUPPORT: 2 BULLISH + 1 NEUTRAL'
                elif action and action.upper() == 'SELL' and bearish_count == 2:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BEARISH'
                    result['confidence_multiplier'] = 1.15
                    result['alignment_score'] = 2
                    result['reasoning'] = '📉 MTF SUPPORT: 2 BEARISH + 1 NEUTRAL'
                # 1 BULLISH + 1 BEARISH + 1 NEUTRAL = true conflict
                elif bullish_count == 1 and bearish_count == 1:
                    result['mtf_aligned'] = False
                    result['direction'] = 'NEUTRAL'
                    result['confidence_multiplier'] = 0.5
                    result['alignment_score'] = 0
                    result['reasoning'] = f'⚠️ MTF CONFLICT: Mixed signals 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
                else:
                    result['mtf_aligned'] = False
                    result['direction'] = 'NEUTRAL'
                    result['confidence_multiplier'] = 0.6
                    result['alignment_score'] = max(bullish_count, bearish_count)
                    result['reasoning'] = f'⚠️ MTF WEAK: 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
                
            # ACTUAL CONFLICT - opposing signals without neutral buffer
            else:
                result['mtf_aligned'] = False
                result['direction'] = 'NEUTRAL'
                result['confidence_multiplier'] = 0.5  # Penalize by 50%
                result['alignment_score'] = max(bullish_count, bearish_count)
                result['reasoning'] = f'⚠️ MTF CONFLICT: 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
            
            # Additional penalty if action conflicts with STRONG MTF direction (2+ in opposite)
            if not action_aligned and (bullish_count >= 2 or bearish_count >= 2):
                result['confidence_multiplier'] *= 0.5
                result['reasoning'] += f' | Action {action} conflicts with MTF'
            
            return result
            
        except Exception as e:
            logger.error(f"MTF analysis error for {symbol}: {e}")
            return {
                'mtf_aligned': False,
                'direction': 'NEUTRAL', 
                'confidence_multiplier': 1.0,
                'timeframes': {'5min': 'ERROR', '15min': 'ERROR', '60min': 'ERROR'},
                'alignment_score': 0,
                'reasoning': f'MTF error: {str(e)}'
            }
    
    def check_relative_strength(self, symbol: str, action: str, stock_change_percent: float, 
                               nifty_change_percent: float, min_outperformance: float = 0.3) -> Tuple[bool, str]:
        """
        Check if stock has relative strength/weakness vs NIFTY
        
        PROFESSIONAL LOGIC:
        - LONGS: Stock must OUTPERFORM market (stronger than NIFTY)
        - SHORTS: Stock must UNDERPERFORM market (weaker than NIFTY)
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            stock_change_percent: Stock's % change
            nifty_change_percent: NIFTY's % change
            min_outperformance: Minimum % outperformance required (default 0.3%)
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        try:
            # Skip check for index trades (NIFTY/BANKNIFTY options)
            index_identifiers = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']
            if any(idx in symbol.upper() for idx in index_identifiers):
                return True, "Index trade - no RS check needed"
            
            relative_strength = stock_change_percent - nifty_change_percent
            
            if action.upper() == "BUY":
                # LONG: Stock must outperform market
                if relative_strength < min_outperformance:
                    reason = (f"❌ WEAK STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}% < {min_outperformance:+.2f}% required)")
                    logger.info(reason)
                    return False, reason
                else:
                    reason = (f"✅ STRONG STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}%)")
                    logger.info(reason)
                    return True, reason
            
            elif action.upper() == "SELL":
                # SHORT: Stock must underperform market
                if relative_strength > -min_outperformance:
                    reason = (f"❌ STRONG STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}% > {-min_outperformance:+.2f}% max)")
                    logger.info(reason)
                    return False, reason
                else:
                    reason = (f"✅ WEAK STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}%)")
                    logger.info(reason)
                    return True, reason
            
            return True, "Action not BUY/SELL"
            
        except Exception as e:
            logger.warning(f"Error checking relative strength for {symbol}: {e}")
            return False, f"RS check error - BLOCKED: {e}"  # Block on error - quality over quantity
        
        # 🎯 ACTIVE POSITION MANAGEMENT CONFIGURATION
        self.enable_active_management = self.config.get('enable_active_management', True)
        self.partial_profit_threshold = self.config.get('partial_profit_threshold', 15)  # Book profits at 15%
        self.aggressive_profit_threshold = self.config.get('aggressive_profit_threshold', 25)  # Aggressive booking at 25%
        self.scaling_profit_threshold = self.config.get('scaling_profit_threshold', 5)  # Scale position at 5% profit
        self.breakeven_buffer = self.config.get('breakeven_buffer', 2)  # 2% buffer above breakeven
        self.time_based_tightening_hours = self.config.get('time_based_tightening', 2)  # Tighten stops after 2 hours
        self.volatility_adjustment_threshold = self.config.get('volatility_threshold', 3)  # Adjust stops at 3% volatility
        
        # ⏰ TRADING TIME RESTRICTIONS (IST)
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.no_new_signals_after = time(15, 0)  # 3:00 PM IST - No new signals
        self.mandatory_close_time = time(15, 20)  # 3:20 PM IST - Force close all positions
        self.warning_close_time = time(15, 15)    # 3:15 PM IST - Start aggressive closing
        
        # Position management tracking
        self.management_actions_taken = {}  # symbol -> list of actions taken
        self.last_management_time = {}  # symbol -> last management timestamp
        self.options_partial_bookings = {}  # symbol -> set of booking levels done
    
    def _has_booked_partial(self, symbol: str, level: str) -> bool:
        """Check if a partial booking level has already been done for this symbol"""
        if symbol not in self.options_partial_bookings:
            return False
        return level in self.options_partial_bookings[symbol]
    
    def _record_partial_booking(self, symbol: str, level: str):
        """Record that a partial booking was done"""
        if symbol not in self.options_partial_bookings:
            self.options_partial_bookings[symbol] = set()
        self.options_partial_bookings[symbol].add(level)
        
    def _is_trading_hours_active(self) -> bool:
        """⏰ CHECK TRADING HOURS - Simplified check for position management"""
        try:
            # Ensure ist_timezone is available (fallback for inheritance issues)
            if not hasattr(self, 'ist_timezone'):
                import pytz
                self.ist_timezone = pytz.timezone('Asia/Kolkata')
                
            current_time_ist = datetime.now(self.ist_timezone).time()
            
            # Market open check (9:15 AM - 3:30 PM IST)
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            return market_open <= current_time_ist <= market_close
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFE fallback - BLOCK trading if error in time check (safer)
            return False
    
    def _get_position_close_urgency(self) -> str:
        """⏰ GET POSITION CLOSE URGENCY - Determine urgency level for position closure"""
        try:
            # Ensure ist_timezone is available (fallback for inheritance issues)
            if not hasattr(self, 'ist_timezone'):
                import pytz
                self.ist_timezone = pytz.timezone('Asia/Kolkata')
                
            # 🚨 DEFENSIVE: Ensure mandatory_close_time exists (fallback for inheritance issues)
            if not hasattr(self, 'mandatory_close_time'):
                logger.warning("⚠️ mandatory_close_time not found, using default")
                from datetime import time
                self.mandatory_close_time = time(15, 20)  # 3:20 PM IST
                
            current_time_ist = datetime.now(self.ist_timezone).time()
            
            # Ensure all time attributes are time objects, not strings
            mandatory_close = self.mandatory_close_time
            if isinstance(mandatory_close, str):
                from datetime import time
                hour, minute = map(int, mandatory_close.split(':'))
                mandatory_close = time(hour, minute)
            
            if current_time_ist >= mandatory_close:  # After 3:20 PM
                return "IMMEDIATE"
            
            if hasattr(self, 'warning_close_time'):
                warning_close = self.warning_close_time
                if isinstance(warning_close, str):
                    from datetime import time
                    hour, minute = map(int, warning_close.split(':'))
                    warning_close = time(hour, minute)
                if current_time_ist >= warning_close:  # After 3:15 PM
                    return "URGENT"
            
            if hasattr(self, 'no_new_signals_after'):
                no_new_signals = self.no_new_signals_after
                if isinstance(no_new_signals, str):
                    from datetime import time
                    hour, minute = map(int, no_new_signals.split(':'))
                    no_new_signals = time(hour, minute)
                if current_time_ist >= no_new_signals:  # After 3:00 PM
                    return "GRADUAL"
            
                return "NORMAL"
                
        except Exception as e:
            logger.error(f"Error determining close urgency: {e}")
            return "NORMAL"
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        time_since_last = (current_time_ist - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
    def _check_signal_rate_limits(self) -> bool:
        """Check if signal generation is allowed based on rate limits"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        # Reset hourly counters if hour has passed
        if (current_time - self.hour_start_time).total_seconds() >= 3600:
            self.signals_generated_this_hour = 0
            self.strategy_signals_this_hour = 0
            self.hour_start_time = current_time
        
        # Check global hourly limit
        if self.signals_generated_this_hour >= self.max_signals_per_hour:
            logger.debug(f"⚠️ Hourly signal limit reached: {self.signals_generated_this_hour}/{self.max_signals_per_hour}")
            return False
        
        # Check strategy-specific hourly limit
        if self.strategy_signals_this_hour >= self.max_signals_per_strategy:
            logger.debug(f"⚠️ Strategy signal limit reached: {self.strategy_signals_this_hour}/{self.max_signals_per_strategy}")
            return False
        
        return True
    
    def _check_capital_affordability(self, symbol: str, quantity: int, price: float, available_capital: float) -> bool:
        """Check if signal is affordable with available capital - CRITICAL FIX for 1,237 failures"""
        required_capital = price * quantity
        
        if required_capital > available_capital:
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} needs ₹{required_capital:,.0f} > available ₹{available_capital:,.0f}")
            return False
        
        # Also check if it's more than 80% of available capital (risk management)
        if required_capital > (available_capital * 0.8):
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} uses {required_capital/available_capital:.1%} of capital (>80% limit)")
            return False
        
        return True
    
    def _increment_signal_counters(self):
        """Increment signal counters when a signal is generated"""
        self.signals_generated_this_hour += 1
        self.strategy_signals_this_hour += 1
        
    def _record_order_placement(self, symbol: str):
        """🚨 CRITICAL: Record when an order is placed to prevent duplicates (GLOBAL across all strategies)"""
        try:
            current_time = time_module.time()
            
            # Record exact symbol
            recent_order_key = f"recent_order_{symbol}"
            self._recent_orders[recent_order_key] = current_time
            
            # 🚨 CRITICAL FIX: Also record UNDERLYING to block ALL related orders
            # Extract underlying: "TITAN25OCT3650CE" → "TITAN"
            underlying = symbol
            if symbol.endswith('CE') or symbol.endswith('PE'):
                import re
                match = re.match(r'^([A-Z]+)', symbol)
                if match:
                    underlying = match.group(1)
            
            # Record underlying separately (prevents CE and PE on same stock)
            if underlying != symbol:
                underlying_key = f"recent_order_{underlying}"
                self._recent_orders[underlying_key] = current_time
                logger.info(f"📝 RECORDED ORDER (GLOBAL): {symbol} + underlying {underlying} by {self.name}")
            else:
                logger.info(f"📝 RECORDED ORDER (GLOBAL): {symbol} by {self.name}")
            
            logger.info(f"   📊 Total tracked orders: {len(self._recent_orders)}")
            
            # Clean up old entries (older than 1 hour)
            cutoff_time = current_time - 3600
            keys_to_remove = [k for k, v in self._recent_orders.items() if v < cutoff_time]
            for key in keys_to_remove:
                del self._recent_orders[key]
                
        except Exception as e:
            logger.error(f"Error recording order placement: {e}")
    
    # ========================================
    # CRITICAL: POSITION MANAGEMENT SYSTEM
    # ========================================
    
    # ========================================
    # 🚨 OPTIONS POSITION MANAGEMENT HELPERS
    # ========================================
    
    def _parse_options_symbol(self, symbol: str) -> tuple:
        """
        Parse options symbol to extract: (underlying, option_type, strike, expiry)
        
        Examples:
            BANKNIFTY25DEC26900PE → (BANKNIFTY, PE, 26900, 25DEC)
            NIFTY25D2726000CE → (NIFTY, CE, 26000, 25D27)
            RELIANCE → (RELIANCE, EQUITY, None, None)
        """
        if not symbol:
            return ('', 'EQUITY', None, None)
        
        symbol = symbol.upper().strip()
        
        # Check if it's an options symbol (ends with CE or PE)
        if not (symbol.endswith('CE') or symbol.endswith('PE')):
            return (symbol, 'EQUITY', None, None)
        
        option_type = 'CE' if symbol.endswith('CE') else 'PE'
        base = symbol[:-2]
        
        # Extract strike price (digits at the end)
        import re
        strike_match = re.search(r'(\d+)$', base)
        if not strike_match:
            return (symbol, option_type, None, None)
        
        strike = int(strike_match.group(1))
        remaining = base[:strike_match.start()]
        
        # Extract expiry and underlying
        expiry_match = re.search(r'(\d{2}[A-Z0-9]+)$', remaining)
        if expiry_match:
            expiry = expiry_match.group(1)
            underlying = remaining[:expiry_match.start()]
        else:
            expiry = None
            underlying = remaining
        
        # Clean underlying
        underlying = re.sub(r'\d+$', '', underlying)
        
        return (underlying, option_type, strike, expiry)
    
    def _get_options_position_group_key(self, symbol: str) -> str:
        """
        Get position group key - all strikes of same underlying+type share same key.
        BANKNIFTY25DEC26900PE → BANKNIFTY:PE
        BANKNIFTY25DEC26850PE → BANKNIFTY:PE (SAME GROUP!)
        """
        underlying, option_type, _, _ = self._parse_options_symbol(symbol)
        return f"{underlying}:{option_type}"
    
    async def _has_existing_options_position(self, options_symbol: str, zerodha_client) -> tuple:
        """
        Check if there's already a position for this underlying + option type.
        All strikes of same underlying+type are treated as ONE position.
        
        Returns: (has_position, existing_position_info)
        """
        try:
            underlying, option_type, strike, _ = self._parse_options_symbol(options_symbol)
            
            if option_type == 'EQUITY':
                return False, None
            
            if zerodha_client:
                positions = zerodha_client.get_positions_sync()
                if positions and isinstance(positions, dict):
                    for pos_list in [positions.get('net', []), positions.get('day', [])]:
                        if isinstance(pos_list, list):
                            for pos in pos_list:
                                pos_symbol = pos.get('tradingsymbol', '')
                                pos_qty = pos.get('quantity', 0)
                                
                                if pos_qty == 0:
                                    continue
                                
                                pos_underlying, pos_type, pos_strike, _ = self._parse_options_symbol(pos_symbol)
                                
                                # Check if same underlying AND same option type
                                if pos_underlying == underlying and pos_type == option_type:
                                    logger.warning(f"🚫 OPTIONS DUPLICATE: {options_symbol} blocked - Already have {pos_type} on {pos_underlying}")
                                    logger.warning(f"   Existing: {pos_symbol} (strike {pos_strike}) qty={pos_qty}")
                                    return True, {
                                        'existing_symbol': pos_symbol,
                                        'existing_strike': pos_strike,
                                        'existing_quantity': pos_qty
                                    }
            
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Error checking options position: {e}")
            return False, None
    
    async def _get_opposite_side_positions(self, options_symbol: str, zerodha_client) -> list:
        """
        Get positions on opposite side that need square-off.
        If buying CE, returns any PE positions for same underlying.
        """
        try:
            underlying, option_type, _, _ = self._parse_options_symbol(options_symbol)
            
            if option_type == 'EQUITY':
                return []
            
            opposite_type = 'PE' if option_type == 'CE' else 'CE'
            opposite_positions = []
            
            if zerodha_client:
                positions = zerodha_client.get_positions_sync()
                if positions and isinstance(positions, dict):
                    for pos_list in [positions.get('net', []), positions.get('day', [])]:
                        if isinstance(pos_list, list):
                            for pos in pos_list:
                                pos_symbol = pos.get('tradingsymbol', '')
                                pos_qty = pos.get('quantity', 0)
                                
                                if pos_qty == 0:
                                    continue
                                
                                pos_underlying, pos_type, pos_strike, _ = self._parse_options_symbol(pos_symbol)
                                
                                # Same underlying BUT opposite type
                                if pos_underlying == underlying and pos_type == opposite_type:
                                    opposite_positions.append({
                                        'symbol': pos_symbol,
                                        'quantity': pos_qty,
                                        'strike': pos_strike,
                                        'type': pos_type,
                                        'pnl': pos.get('pnl', 0),
                                        'average_price': pos.get('average_price', 0)
                                    })
            
            if opposite_positions:
                logger.info(f"⚠️ OPPOSITE SIDE: {options_symbol} ({option_type}) has {len(opposite_positions)} {opposite_type} positions")
            
            return opposite_positions
            
        except Exception as e:
            logger.error(f"❌ Error getting opposite positions: {e}")
            return []
    
    async def _square_off_opposite_positions(self, options_symbol: str, zerodha_client) -> list:
        """Square off opposite side positions before entering new direction."""
        try:
            opposite_positions = await self._get_opposite_side_positions(options_symbol, zerodha_client)
            
            if not opposite_positions:
                return []
            
            _, new_type, _, _ = self._parse_options_symbol(options_symbol)
            opposite_type = 'PE' if new_type == 'CE' else 'CE'
            
            logger.info(f"🔄 AUTO SQUARE-OFF: Closing {len(opposite_positions)} {opposite_type} before {new_type}")
            
            results = []
            for pos in opposite_positions:
                try:
                    exit_action = 'SELL' if pos['quantity'] > 0 else 'BUY'
                    exit_qty = abs(pos['quantity'])
                    
                    logger.info(f"   🔴 Squaring off: {pos['symbol']} {exit_action} {exit_qty}")
                    
                    result = await zerodha_client.place_order(
                        symbol=pos['symbol'],
                        quantity=exit_qty,
                        order_type=exit_action,
                        product='MIS',
                        price_type='MARKET',
                        exchange='NFO'
                    )
                    
                    results.append({
                        'symbol': pos['symbol'],
                        'action': exit_action,
                        'quantity': exit_qty,
                        'order_id': result.get('order_id') if result else None,
                        'reason': f'Auto square-off before {new_type} entry'
                    })
                    
                except Exception as sq_err:
                    logger.error(f"   ❌ Square-off failed for {pos['symbol']}: {sq_err}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in square_off_opposite_positions: {e}")
            return []
    
    async def _is_order_pending_for_symbol(self, symbol: str, zerodha_client) -> tuple:
        """
        Check if there's a pending order for this symbol or its underlying+type.
        Returns: (is_pending, pending_order_id)
        """
        try:
            underlying, option_type, _, _ = self._parse_options_symbol(symbol)
            
            orders = await zerodha_client.get_orders()
            if not orders:
                return False, None
            
            for order in orders:
                status = order.get('status', '').upper()
                
                if status not in ['PENDING', 'OPEN', 'TRIGGER PENDING', 'AMO REQ RECEIVED']:
                    continue
                
                order_symbol = order.get('tradingsymbol', '')
                order_underlying, order_type, _, _ = self._parse_options_symbol(order_symbol)
                
                # Block if same underlying + same type has pending order
                if order_underlying == underlying and order_type == option_type:
                    order_id = order.get('order_id')
                    logger.warning(f"⏳ PENDING ORDER: {order_symbol} (order_id={order_id}) - blocking {symbol}")
                    return True, order_id
            
            return False, None
            
        except Exception as e:
            logger.debug(f"Pending order check error: {e}")
            return False, None
    
    async def _cancel_stale_pending_orders(self, zerodha_client, max_age_minutes: int = 15) -> list:
        """Cancel pending orders older than max_age_minutes."""
        try:
            cancelled = []
            now = datetime.now()
            
            orders = await zerodha_client.get_orders()
            if not orders:
                return []
            
            for order in orders:
                order_id = order.get('order_id')
                status = order.get('status', '').upper()
                
                if status not in ['PENDING', 'OPEN', 'TRIGGER PENDING', 'AMO REQ RECEIVED']:
                    continue
                
                order_time_str = order.get('order_timestamp') or order.get('exchange_timestamp')
                if not order_time_str:
                    continue
                
                try:
                    if isinstance(order_time_str, str):
                        order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                    else:
                        order_time = order_time_str
                    
                    age_minutes = (now - order_time.replace(tzinfo=None)).total_seconds() / 60
                    
                    if age_minutes >= max_age_minutes:
                        symbol = order.get('tradingsymbol', 'UNKNOWN')
                        logger.warning(f"⏰ STALE ORDER: {order_id} ({symbol}) - {age_minutes:.1f} min old")
                        
                        cancel_result = await zerodha_client.cancel_order(order_id)
                        
                        if cancel_result:
                            cancelled.append({'order_id': order_id, 'symbol': symbol, 'age': age_minutes})
                            logger.info(f"   ✅ Cancelled stale order: {order_id}")
                            
                except Exception as parse_err:
                    continue
            
            if cancelled:
                logger.info(f"🧹 Cancelled {len(cancelled)} stale pending orders")
            
            return cancelled
            
        except Exception as e:
            logger.error(f"❌ Error cancelling stale orders: {e}")
            return []
    
    def has_existing_position(self, symbol: str, action: str = None, option_type: str = None) -> bool:
        """🚨 CRITICAL FIX: Check for existing positions to prevent DUPLICATE ORDERS
        
        🔧 2025-12-29: Added action parameter for REVERSAL detection
        - SAME direction signal → Block as DUPLICATE
        - OPPOSITE direction signal → Allow (triggers EXIT/REVERSAL)
        
        🔧 2025-12-29 v2: Added option_type for correct direction calculation
        - BUY CALL = effectively LONG
        - BUY PUT = effectively SHORT  
        - SELL CALL = effectively SHORT
        - SELL PUT = effectively LONG
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL' - if provided, checks direction matching
            option_type: 'CE' or 'PE' - for options, determines effective direction
        """
        
        # Extract underlying symbol for comprehensive checking
        # For options: "TCS25OCT2940CE" → "TCS"
        # For equity: "TCS" → "TCS"
        underlying = symbol
        if symbol.endswith('CE') or symbol.endswith('PE'):
            # Remove expiry and strike: "TCS25OCT2940CE" → "TCS"
            import re
            match = re.match(r'^([A-Z]+)', symbol)
            if match:
                underlying = match.group(1)
        
        # 🚨 STEP 1: Check REAL Zerodha positions first (most authoritative)
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                # Get real positions from Zerodha
                positions = orchestrator.zerodha_client.get_positions_sync()
                if positions and isinstance(positions, dict):
                    # Check both net and day positions
                    for pos_list in [positions.get('net', []), positions.get('day', [])]:
                        if isinstance(pos_list, list):
                            for pos in pos_list:
                                pos_symbol = pos.get('tradingsymbol', '')
                                pos_qty = pos.get('quantity', 0)
                                
                                if pos_qty == 0:
                                    continue  # Skip closed positions
                                
                                # Check exact match first
                                if pos_symbol == symbol:
                                    # 🔧 2025-12-29: Check if this is REVERSAL signal (opposite direction)
                                    if action:
                                        # pos_qty > 0 means LONG position, < 0 means SHORT
                                        existing_is_long = pos_qty > 0
                                        
                                        # 🔧 2025-12-29 v2: Calculate EFFECTIVE direction for options
                                        # BUY PUT = SHORT direction, BUY CALL = LONG direction
                                        # SELL PUT = LONG direction, SELL CALL = SHORT direction
                                        raw_is_buy = action.upper() == 'BUY'
                                        if option_type:
                                            if option_type.upper() in ['PE', 'PUT']:
                                                # PUT: BUY=SHORT, SELL=LONG
                                                signal_is_long = not raw_is_buy
                                            else:
                                                # CALL: BUY=LONG, SELL=SHORT
                                                signal_is_long = raw_is_buy
                                            direction_desc = f"{action} {option_type} (effective: {'LONG' if signal_is_long else 'SHORT'})"
                                        else:
                                            signal_is_long = raw_is_buy
                                            direction_desc = action
                                        
                                        # If signal is OPPOSITE to existing position = REVERSAL (allow it)
                                        if (existing_is_long and not signal_is_long) or (not existing_is_long and signal_is_long):
                                            logger.info(f"🔄 REVERSAL SIGNAL DETECTED: {symbol} has {'LONG' if existing_is_long else 'SHORT'} position, new signal is {direction_desc}")
                                            logger.info(f"   ✅ Allowing signal to trigger EXIT/REVERSAL")
                                            return False  # Allow the reversal signal
                                    
                                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} has REAL position qty={pos_qty}")
                                    return True
                                
                                # CRITICAL FIX: Also check for same underlying
                                # If TCS25OCT2940CE exists, block ALL TCS signals (TCS25OCT2950CE, TCS equity, etc.)
                                pos_underlying = pos_symbol
                                if pos_symbol.endswith('CE') or pos_symbol.endswith('PE'):
                                    import re
                                    match = re.match(r'^([A-Z]+)', pos_symbol)
                                    if match:
                                        pos_underlying = match.group(1)
                                
                                if pos_underlying == underlying:
                                    # Same underlying check - also consider reversal
                                    if action:
                                        existing_is_long = pos_qty > 0
                                        
                                        # 🔧 2025-12-29 v2: Calculate EFFECTIVE direction for options
                                        raw_is_buy = action.upper() == 'BUY'
                                        if option_type:
                                            if option_type.upper() in ['PE', 'PUT']:
                                                signal_is_long = not raw_is_buy
                                            else:
                                                signal_is_long = raw_is_buy
                                            direction_desc = f"{action} {option_type} (effective: {'LONG' if signal_is_long else 'SHORT'})"
                                        else:
                                            signal_is_long = raw_is_buy
                                            direction_desc = action
                                        
                                        if (existing_is_long and not signal_is_long) or (not existing_is_long and signal_is_long):
                                            logger.info(f"🔄 REVERSAL SIGNAL for underlying {underlying}: Existing {pos_symbol} is {'LONG' if existing_is_long else 'SHORT'}, new {symbol} is {direction_desc}")
                                            return False  # Allow the reversal signal
                                    
                                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} - Found existing position for underlying {underlying}: {pos_symbol} qty={pos_qty}")
                                    return True
        except Exception as e:
            # 🚨 FAIL-SAFE 2025-12-30: If we can't check positions, BLOCK the trade
            # This prevents duplicates when Zerodha API fails after restart
            logger.warning(f"⚠️ FAIL-SAFE BLOCK: Cannot verify {symbol} position status: {e}")
            logger.warning(f"   Blocking trade to prevent potential duplicate - will retry next cycle")
            return True  # BLOCK when uncertain - conservative approach
        
        # 🚨 STEP 2: Check recent order history to prevent rapid duplicates (2-minute window)
        try:
            # Check if we've placed an order for this symbol in the last 2 minutes (matches signal validity)
            current_time = time_module.time()
            
            if hasattr(self, '_recent_orders'):
                # Check exact symbol match
                exact_key = f"recent_order_{symbol}"
                last_order_time = self._recent_orders.get(exact_key, 0)
                if current_time - last_order_time < 120:  # 2 minutes (matches signal expiry)
                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} ordered {(current_time - last_order_time):.0f}s ago")
                    return True
                
                # CRITICAL FIX: Also check for underlying symbol
                # If TCS25OCT2940CE was ordered, block all TCS-related signals
                underlying_key = f"recent_order_{underlying}"
                last_underlying_time = self._recent_orders.get(underlying_key, 0)
                if current_time - last_underlying_time < 120:
                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED (GLOBAL): {symbol} - Underlying {underlying} ordered {(current_time - last_underlying_time):.0f}s ago")
                    logger.warning(f"   🎯 Blocked by {self.name} - prevents contradictory CE/PE on same stock")
                    return True
                    
                # Also check all recent orders for same underlying
                for recent_key, recent_time in self._recent_orders.items():
                    if not recent_key.startswith('recent_order_'):
                        continue
                    recent_symbol = recent_key.replace('recent_order_', '')
                    
                    # Extract underlying from recent order
                    recent_underlying = recent_symbol
                    if recent_symbol.endswith('CE') or recent_symbol.endswith('PE'):
                        import re
                        match = re.match(r'^([A-Z]+)', recent_symbol)
                        if match:
                            recent_underlying = match.group(1)
                    
                    # Block if same underlying and within 2 minutes
                    if recent_underlying == underlying and current_time - recent_time < 120:
                        logger.warning(f"🚫 DUPLICATE ORDER BLOCKED (GLOBAL): {symbol} - Related order {recent_symbol} placed {(current_time - recent_time):.0f}s ago")
                        logger.warning(f"   🎯 Blocked by {self.name} - prevents multiple positions on {underlying}")
                        return True
            else:
                self._recent_orders = {}
                
        except Exception as e:
            logger.debug(f"Could not check recent orders: {e}")
        
        # 🚨 STEP 2.5: Check SAME-DIRECTION duplicate via Zerodha ORDERS (not just positions)
        # 🔧 2025-12-30: Fix for BPCL/SUZLON duplicate - positions take time to update but orders are immediate
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                today_orders = orchestrator.zerodha_client.get_orders_sync()
                if today_orders:
                    for order in today_orders:
                        order_symbol = order.get('tradingsymbol', '')
                        order_status = order.get('status', '')
                        order_action = order.get('transaction_type', '').upper()
                        order_qty = order.get('quantity', 0)
                        
                        # Only check COMPLETE orders for the same symbol
                        if order_symbol == symbol and order_status == 'COMPLETE':
                            # Check if it's the SAME direction (not a reversal/exit)
                            same_direction = (action and action.upper() == order_action)
                            
                            if same_direction:
                                logger.warning(f"🚫 SAME-DIRECTION DUPLICATE BLOCKED: {symbol} {action}")
                                logger.warning(f"   Already have COMPLETE {order_action} order for {order_qty} shares")
                                logger.warning(f"   This prevents adding to existing position!")
                                return True
        except Exception as e:
            logger.debug(f"Could not check Zerodha orders: {e}")
        
        # 🚨 STEP 3: Check local strategy positions
        if symbol in self.active_positions:
            # Check for phantom positions (older than 30 minutes)
            position_data = self.active_positions[symbol]
            if isinstance(position_data, dict):
                timestamp = position_data.get('timestamp', 0)
                current_time = time_module.time()
                
                # CRITICAL FIX: Handle timestamp corruption (Unix epoch issues)
                if timestamp == 0 or timestamp < 1000000000:  # Before year 2001 (likely corrupted)
                    logger.warning(f"🧹 CLEARING CORRUPTED TIMESTAMP POSITION: {symbol} (timestamp: {timestamp})")
                    del self.active_positions[symbol]
                    # Add cooldown to prevent immediate regeneration
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
                
                age_minutes = (current_time - timestamp) / 60
                
                # CRITICAL FIX: Handle extreme ages (likely timestamp corruption)
                if age_minutes > 1440:  # More than 24 hours indicates corruption
                    logger.warning(f"🧹 CLEARING PHANTOM POSITION: {symbol} (age: {age_minutes:.1f} min - likely corrupted timestamp)")
                    del self.active_positions[symbol]
                    # Add cooldown to prevent immediate regeneration
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
                elif age_minutes > 30:  # Normal 30 minute cleanup
                    logger.warning(f"🧹 CLEARING PHANTOM POSITION: {symbol} (age: {age_minutes:.1f} min)")
                    del self.active_positions[symbol]
                    # CRITICAL FIX: Add cooldown period after clearing phantom position
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
            
            logger.info(f"🚫 {self.strategy_name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
            return True
        return False
    
    def _add_position_cooldown(self, symbol: str, seconds: int):
        """Add cooldown period for a symbol after phantom position cleanup"""
        expiry_time = time_module.time() + seconds
        self.position_cooldowns[symbol] = expiry_time
        logger.info(f"🕐 COOLDOWN ADDED: {symbol} for {seconds} seconds")
    
    def _is_position_cooldown_active(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period"""
        if symbol not in self.position_cooldowns:
            return False
        
        current_time = time_module.time()
        if current_time < self.position_cooldowns[symbol]:
            remaining = int(self.position_cooldowns[symbol] - current_time)
            logger.info(f"🕐 COOLDOWN ACTIVE: {symbol} ({remaining}s remaining)")
            return True
        else:
            # Cooldown expired, remove it
            del self.position_cooldowns[symbol]
            return False
    
    async def check_and_cancel_stale_limit_orders(self, market_data: Dict) -> List[str]:
        """
        🎯 SMART LIMIT ORDER CANCELLATION
        
        Cancels pending limit orders if:
        1. Order has expired (validity_seconds elapsed)
        2. Sentiment/indicators have reversed against the order direction
        3. Price has moved too far away from limit price
        
        Returns: List of cancelled order symbols
        """
        cancelled_symbols = []
        
        if not self.pending_limit_orders:
            return cancelled_symbols
        
        try:
            now = datetime.now()
            symbols_to_remove = []
            
            for symbol, order_info in self.pending_limit_orders.items():
                order_id = order_info.get('order_id')
                action = order_info.get('action', 'BUY')
                limit_price = order_info.get('limit_price', 0)
                created_at = order_info.get('created_at', now)
                validity_seconds = order_info.get('validity_seconds', 300)
                
                # Get current market data for this symbol
                symbol_data = market_data.get(symbol, {})
                current_price = symbol_data.get('ltp') or symbol_data.get('last_price', 0)
                
                should_cancel = False
                cancel_reason = ""
                
                # CHECK 1: Time expiry
                elapsed = (now - created_at).total_seconds()
                if elapsed >= validity_seconds:
                    should_cancel = True
                    cancel_reason = f"EXPIRED ({elapsed:.0f}s >= {validity_seconds}s validity)"
                
                # CHECK 2: Sentiment/Indicator reversal
                if not should_cancel and current_price > 0:
                    # Get current indicators
                    prices = self.price_history.get(symbol, [])
                    if len(prices) >= 14:
                        rsi = self._calculate_rsi(np.array(prices), 14)
                        
                        # For BUY limit order: Cancel if RSI now overbought (>70) or bearish momentum
                        if action == 'BUY':
                            if rsi > 70:
                                should_cancel = True
                                cancel_reason = f"SENTIMENT REVERSAL: RSI={rsi:.1f} > 70 (overbought) against BUY"
                            # Also check if price moved significantly AWAY (up) from our limit
                            elif current_price > limit_price * 1.01:  # 1% above limit
                                should_cancel = True
                                cancel_reason = f"PRICE MOVED AWAY: Current ₹{current_price:.2f} >> Limit ₹{limit_price:.2f}"
                        
                        # For SELL limit order: Cancel if RSI now oversold (<30) or bullish momentum
                        elif action == 'SELL':
                            if rsi < 30:
                                should_cancel = True
                                cancel_reason = f"SENTIMENT REVERSAL: RSI={rsi:.1f} < 30 (oversold) against SELL"
                            # Also check if price moved significantly AWAY (down) from our limit
                            elif current_price < limit_price * 0.99:  # 1% below limit
                                should_cancel = True
                                cancel_reason = f"PRICE MOVED AWAY: Current ₹{current_price:.2f} << Limit ₹{limit_price:.2f}"
                
                # CHECK 3: MTF reversal against order direction
                if not should_cancel and current_price > 0:
                    mtf_result = self.analyze_multi_timeframe(symbol, action)
                    mtf_direction = mtf_result.get('direction', 'NEUTRAL')
                    mtf_score = mtf_result.get('alignment_score', 0)
                    
                    # Strong MTF reversal against our order
                    if mtf_score >= 2:
                        if (action == 'BUY' and mtf_direction == 'BEARISH') or \
                           (action == 'SELL' and mtf_direction == 'BULLISH'):
                            should_cancel = True
                            cancel_reason = f"MTF REVERSAL: {mtf_direction} ({mtf_score}/3 TF) against {action}"
                
                # Execute cancellation
                if should_cancel:
                    logger.warning(f"🚫 SMART CANCEL: {symbol} {action} limit @ ₹{limit_price:.2f}")
                    logger.warning(f"   Reason: {cancel_reason}")
                    
                    # Cancel via Zerodha if we have order_id
                    if order_id:
                        try:
                            from src.core.orchestrator import get_orchestrator_instance
                            orchestrator = get_orchestrator_instance()
                            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                                await orchestrator.zerodha_client.cancel_order(order_id)
                                logger.info(f"   ✅ Order {order_id} cancelled successfully")
                        except Exception as cancel_error:
                            logger.error(f"   ⚠️ Failed to cancel order {order_id}: {cancel_error}")
                    
                    symbols_to_remove.append(symbol)
                    cancelled_symbols.append(symbol)
            
            # Remove cancelled orders from tracking
            for symbol in symbols_to_remove:
                del self.pending_limit_orders[symbol]
            
            if cancelled_symbols:
                logger.info(f"🎯 SMART CANCELLATION: Cancelled {len(cancelled_symbols)} stale/reversed limit orders")
            
            return cancelled_symbols
            
        except Exception as e:
            logger.error(f"Error checking stale limit orders: {e}")
            return cancelled_symbols
    
    def track_pending_limit_order(self, symbol: str, order_id: str, action: str, 
                                   limit_price: float, validity_seconds: int, signal: Dict):
        """Track a new pending limit order for smart cancellation"""
        self.pending_limit_orders[symbol] = {
            'order_id': order_id,
            'action': action,
            'limit_price': limit_price,
            'created_at': datetime.now(),
            'validity_seconds': validity_seconds,
            'original_signal': signal
        }
        logger.info(f"📋 TRACKING LIMIT ORDER: {symbol} {action} @ ₹{limit_price:.2f} (valid {validity_seconds}s)")
    
    def remove_pending_limit_order(self, symbol: str):
        """Remove a pending limit order from tracking (when filled or cancelled)"""
        if symbol in self.pending_limit_orders:
            del self.pending_limit_orders[symbol]
            logger.debug(f"📋 REMOVED LIMIT ORDER TRACKING: {symbol}")
    
    async def manage_existing_positions(self, market_data: Dict) -> List[Dict]:
        """🎯 COMPREHENSIVE POSITION MANAGEMENT - Active monitoring and management"""
        try:
            # 🚨 CRITICAL FIX: Sync local positions with REAL Zerodha positions
            # Remove positions that no longer exist in broker
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            real_symbols_with_positions = set()
            
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                try:
                    real_positions = await orchestrator.zerodha_client.get_positions()

                    # 🚨 VALIDATION: Ensure real_positions is a dict
                    if real_positions is None:
                        logger.warning("⚠️ get_positions returned None")
                        real_positions = {}
                    elif isinstance(real_positions, int):
                        logger.error(f"❌ get_positions returned int instead of dict: {real_positions}")
                        real_positions = {}
                    elif not isinstance(real_positions, dict):
                        logger.error(f"❌ get_positions returned {type(real_positions)} instead of dict: {real_positions}")
                        real_positions = {}

                    if real_positions:
                        # First, collect all symbols that have real positions
                        for pos_list in [real_positions.get('net', []), real_positions.get('day', [])]:
                            for pos in pos_list:
                                symbol = pos.get('tradingsymbol')
                                qty = pos.get('quantity', 0)
                                if qty != 0:  # Only consider non-zero positions
                                    real_symbols_with_positions.add(symbol)
                        
                        # Clean up local positions that don't exist in broker
                        symbols_to_remove = []
                        for symbol in list(self.active_positions.keys()):
                            if symbol not in real_symbols_with_positions:
                                logger.warning(f"🧹 CLEANING STALE POSITION: {symbol} (not in broker)")
                                symbols_to_remove.append(symbol)
                        
                        for symbol in symbols_to_remove:
                            del self.active_positions[symbol]
                    
                        # Now process emergency exits for REAL positions
                        # 🚨 CRITICAL FIX: Track processed symbols to prevent duplicate exits
                        emergency_exits_processed = set()
                        
                        for pos_list in [real_positions.get('net', []), real_positions.get('day', [])]:
                            for pos in pos_list:
                                symbol = pos.get('tradingsymbol')
                                qty = pos.get('quantity', 0)
                                avg_price = pos.get('average_price', 0)
                                pnl = pos.get('pnl', 0) or pos.get('unrealised', 0) or 0
                                
                                # Skip if no actual position (qty = 0 means position closed)
                                if qty == 0:
                                    continue
                                
                                # 🚨 CRITICAL: Skip if already processed (prevents duplicate exits)
                                if symbol in emergency_exits_processed:
                                    logger.debug(f"⏭️ Skipping {symbol} - already checked for emergency exit")
                                    continue
                                emergency_exits_processed.add(symbol)
                                
                                # 🚨 COOLDOWN: Skip if emergency exit was recently processed for this symbol
                                current_time = datetime.now()
                                if symbol in self.emergency_exits_processed:
                                    last_exit_time = self.emergency_exits_processed[symbol]
                                    time_since_exit = (current_time - last_exit_time).total_seconds()
                                    if time_since_exit < 300:  # 5 minute cooldown
                                        logger.debug(f"⏳ Emergency exit cooldown: {symbol} ({time_since_exit:.0f}s remaining)")
                                        continue
                                
                                # EMERGENCY: Exit ANY position with >₹1000 loss or >2% loss
                                loss_threshold_amount = -1000  # ₹1000 loss
                                loss_threshold_percent = -2.0  # 2% loss
                                
                                # Calculate percentage loss
                                if avg_price > 0 and qty != 0:
                                    current_price = market_data.get(symbol, {}).get('ltp', avg_price)
                                    pnl_percent = ((current_price - avg_price) / avg_price) * 100
                                else:
                                    pnl_percent = 0
                                
                                # Check if position needs emergency exit
                                if (pnl < loss_threshold_amount) or (pnl_percent < loss_threshold_percent):
                                    logger.error(f"🚨 EMERGENCY STOP LOSS TRIGGERED: {symbol}")
                                    logger.error(f"   Loss: ₹{pnl:.2f} ({pnl_percent:.1f}%), Qty: {qty}, Avg: ₹{avg_price:.2f}")
                                    
                                    # 🚨 CRITICAL FIX: Only place exit order if position actually exists (qty != 0)
                                    if qty != 0:
                                        # Force immediate exit signal
                                        exit_signal = {
                                            'symbol': symbol,
                                            'action': 'SELL' if qty > 0 else 'BUY',
                                            'quantity': abs(qty),
                                            'entry_price': market_data.get(symbol, {}).get('ltp', avg_price),
                                            'stop_loss': 0,
                                            'target': 0,
                                            'confidence': 10.0,  # Maximum confidence for emergency exit
                                            'reason': f'EMERGENCY_STOP_LOSS: ₹{pnl:.2f} ({pnl_percent:.1f}%)',  # Add at top level
                                            'metadata': {
                                                'reason': 'EMERGENCY_STOP_LOSS',
                                                'loss_amount': pnl,
                                                'loss_percent': pnl_percent,
                                                'management_action': True,
                                                'closing_action': True,
                                                'bypass_all_checks': True
                                            }
                                        }
                                        await self._execute_management_action(exit_signal)
                                        logger.error(f"🚨 EXECUTED EMERGENCY EXIT for {symbol} - Loss: ₹{pnl:.2f}")
                                        
                                        # 🚨 COOLDOWN: Record emergency exit to prevent repeats
                                        self.emergency_exits_processed[symbol] = current_time
                                    else:
                                        # Position already closed, just log the loss and clean up
                                        logger.error(f"🚨 POSITION ALREADY CLOSED: {symbol} - Loss recorded: ₹{pnl:.2f}")
                                        logger.error(f"   No exit order needed (quantity = 0) - cleaning up tracking")
                                        # Clean up tracking for closed position
                                        if symbol in self.active_positions:
                                            del self.active_positions[symbol]
            
                except Exception as positions_error:
                    logger.error(f"❌ Error processing positions: {positions_error}")
                    logger.error(f"   Error type: {type(positions_error)}")
                    if "can't be used in 'await' expression" in str(positions_error):
                        logger.error("🚨 CRITICAL: Zerodha API returned non-coroutine for positions")
            
            # ⏰ CHECK POSITION CLOSURE URGENCY based on current time
            close_urgency = self._get_position_close_urgency()
            current_time_ist = datetime.now(self.ist_timezone).strftime('%H:%M:%S')
            
            positions_to_exit = []
            positions_to_modify = []
            
            for symbol, position in self.active_positions.items():
                # 🔥 FIX: Get market data from multiple sources for synced positions
                # Previously positions not in market_data were silently skipped - no RSI exit!
                symbol_data = market_data.get(symbol)
                
                if not symbol_data:
                    # Fallback 1: TrueData live cache
                    try:
                        from data.truedata_client import live_market_data
                        if symbol in live_market_data:
                            symbol_data = live_market_data[symbol]
                    except Exception:
                        pass
                
                if not symbol_data:
                    # Fallback 2: Zerodha positions API (has last_price)
                    try:
                        from src.core.orchestrator import get_orchestrator_instance
                        orch = get_orchestrator_instance()
                        if orch and hasattr(orch, 'zerodha_client'):
                            pos_data = await orch.zerodha_client.get_positions()
                            for pos in pos_data.get('net', []):
                                if pos.get('tradingsymbol') == symbol:
                                    symbol_data = {'ltp': pos.get('last_price', 0), 'open': pos.get('average_price', 0)}
                                    break
                    except Exception:
                        pass
                
                if not symbol_data:
                    logger.warning(f"⚠️ POSITION {symbol}: Skipping - no market data available")
                    continue
                    
                current_price = symbol_data.get('ltp', 0)
                if current_price == 0:
                    logger.warning(f"⚠️ POSITION {symbol}: Skipping - LTP is 0")
                    continue
                
                # ⏰ PRIORITY: HANDLE TIME-BASED CLOSURE URGENCY
                if close_urgency == "IMMEDIATE":  # After 3:20 PM - FORCE CLOSE ALL
                    positions_to_exit.append({
                        'symbol': symbol,
                        'reason': f'MANDATORY_CLOSE_3:20PM_IST',
                        'current_price': current_price,
                        'position': position,
                        'urgent': True
                    })
                    logger.warning(f"🚨 {self.name}: MANDATORY CLOSE {symbol} at {current_time_ist} IST (After 3:20 PM)")
                    continue
                    
                elif close_urgency == "URGENT":  # 3:15-3:20 PM - AGGRESSIVE CLOSING
                    # Force exit losing positions, book profits on winning ones
                    entry_price = position.get('entry_price', 0)
                    action = position.get('action', 'BUY')
                    
                    if action == 'BUY':
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                    
                    # Close losing positions immediately, be more aggressive on winners
                    if pnl_pct < -2:  # Losing >2%
                        positions_to_exit.append({
                            'symbol': symbol,
                            'reason': f'URGENT_CLOSE_3:15PM_LOSS_{pnl_pct:.1f}%',
                            'current_price': current_price,
                            'position': position,
                            'urgent': True
                        })
                        logger.warning(f"🚨 {self.name}: URGENT CLOSE {symbol} (Loss: {pnl_pct:.1f}%) at {current_time_ist} IST")
                        continue
                    elif pnl_pct > 5:  # Winning >5% - book 75% profits
                        await self.book_partial_profits(symbol, current_price, position, 75)
                        logger.info(f"⏰ {self.name}: URGENT PROFIT BOOKING 75% for {symbol} (P&L: {pnl_pct:.1f}%) at {current_time_ist} IST")
                        
                elif close_urgency == "GRADUAL":  # 3:00-3:15 PM - NO NEW POSITIONS, gradual exit
                    # Start booking profits more aggressively, no new scaling
                    entry_price = position.get('entry_price', 0)
                    action = position.get('action', 'BUY')
                    
                    if action == 'BUY':
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                    
                    # More aggressive profit booking after 3 PM
                    if pnl_pct > 8:  # Lower threshold for profit booking
                        await self.book_partial_profits(symbol, current_price, position, 50)
                        logger.info(f"⏰ {self.name}: GRADUAL PROFIT BOOKING 50% for {symbol} (P&L: {pnl_pct:.1f}%) at {current_time_ist} IST")
                
                # 1. CHECK FOR REGULAR EXIT CONDITIONS (if not urgent closure)
                if close_urgency not in ["IMMEDIATE", "URGENT"]:
                    exit_decision = await self.should_exit_position(symbol, current_price, position)
                    
                    if exit_decision['should_exit']:
                        positions_to_exit.append({
                            'symbol': symbol,
                            'reason': exit_decision['reason'],
                            'current_price': current_price,
                            'position': position,
                            'urgent': False
                        })
                        continue
                
                # 2. ENHANCED OPEN POSITION DECISION ANALYSIS
                if close_urgency == "NORMAL":
                    # Use enhanced decision system for comprehensive position analysis
                    # 🔥 FIX: Use symbol_data (fetched from multiple sources) instead of market_data[symbol]
                    decision_result = await self._evaluate_open_position_decision(
                        symbol, current_price, position, symbol_data
                    )
                    
                    # Execute decision based on enhanced analysis
                    await self._execute_position_decision(symbol, current_price, position, decision_result)
                    
                    # FALLBACK: Legacy position management for compatibility
                    management_actions = await self.analyze_position_management(symbol, current_price, position, symbol_data)
                    
                    # 3. UPDATE TRAILING STOPS (if not handled by enhanced system)
                    if decision_result.action.value not in ['TRAIL_STOP', 'ADJUST_STOP']:
                        await self.update_trailing_stop(symbol, current_price, position)
                    
                    # 4. PARTIAL PROFIT BOOKING (if not handled by enhanced system)
                    if decision_result.action.value != 'EXIT_PARTIAL' and management_actions.get('book_partial_profits'):
                        await self.book_partial_profits(symbol, current_price, position, management_actions['partial_percentage'])
                    
                    # 5. SCALE INTO POSITION (if not handled by enhanced system)
                    if decision_result.action.value != 'SCALE_IN' and management_actions.get('scale_position'):
                        await self.scale_into_position(symbol, current_price, position, management_actions['scale_quantity'])
                    
                    # 6. DYNAMIC STOP LOSS ADJUSTMENT (if not handled by enhanced system)
                    if decision_result.action.value not in ['ADJUST_STOP', 'TRAIL_STOP'] and management_actions.get('adjust_stop_loss'):
                        await self.adjust_dynamic_stop_loss(symbol, current_price, position, management_actions['new_stop_loss'])
                    
                    # 7. TIME-BASED PROFIT PROTECTION
                    await self.apply_time_based_management(symbol, current_price, position)
                    
                    # 8. VOLATILITY-BASED ADJUSTMENTS
                    await self.apply_volatility_based_management(symbol, current_price, position, symbol_data)
                    
            # Execute position exits
            for exit_data in positions_to_exit:
                await self.exit_position(exit_data['symbol'], exit_data['current_price'], exit_data['reason'])
                
            # Enhanced logging with time context
            if len(self.active_positions) > 0:
                logger.info(f"🎯 {self.name}: Managing {len(self.active_positions)} positions | "
                           f"Exits: {len(positions_to_exit)} | Urgency: {close_urgency} | Time: {current_time_ist} IST")
                
        except Exception as e:
            logger.error(f"Error managing existing positions: {e}")
    
    async def _evaluate_open_position_decision(self, symbol: str, current_price: float, 
                                             position: Dict, market_data: Dict):
        """
        Evaluate open position using enhanced decision system
        
        🚨 CRITICAL FIX: Enrich market_data with technical indicators (RSI, MACD, etc.)
        so the position decision system can make intelligent exit decisions based on CHARTS.
        
        Without this, positions just get generic "HOLD" decisions and lose money.
        """
        try:
            # Import the enhanced open position decision system
            from src.core.open_position_decision import evaluate_open_position
            
            # Get market bias if available
            market_bias = getattr(self, 'market_bias', None)
            
            # 🚨 CRITICAL: ENRICH market_data with technical indicators for CHART-BASED decisions
            enriched_market_data = await self._enrich_position_data_with_indicators(symbol, market_data)
            
            # Log what indicators are available for decision making
            rsi_available = 'rsi' in enriched_market_data
            macd_available = 'macd_crossover' in enriched_market_data
            logger.debug(f"📊 Position Analysis Data: {symbol} - RSI={enriched_market_data.get('rsi', 'N/A')}, "
                        f"MACD={enriched_market_data.get('macd_crossover', 'N/A')}, "
                        f"Change={enriched_market_data.get('change_percent', 0):.2f}%")
            
            # Evaluate position decision with ENRICHED data
            decision_result = await evaluate_open_position(
                position=position,
                current_price=current_price,
                market_data=enriched_market_data,
                market_bias=market_bias,
                portfolio_context={'strategy_name': self.name}
            )
            
            logger.info(f"🎯 POSITION DECISION: {symbol} -> {decision_result.action.value} "
                       f"(Confidence: {decision_result.confidence:.1f}, Urgency: {decision_result.urgency})")
            logger.info(f"   Reasoning: {decision_result.reasoning}")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"❌ Error evaluating open position decision for {symbol}: {e}")
            # Return default HOLD decision
            from src.core.open_position_decision import OpenPositionDecisionResult, OpenPositionAction
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Decision evaluation error: {str(e)} - Defaulting to HOLD",
                metadata={'error': str(e)}
            )
    
    async def _enrich_position_data_with_indicators(self, symbol: str, market_data: Dict) -> Dict:
        """
        🚨 CRITICAL: Enrich market data with technical indicators for position analysis
        
        Without RSI, MACD, and other indicators, the position decision system cannot
        make intelligent exit decisions based on chart patterns. Positions end up
        being held indefinitely with generic "HOLD" reasoning.
        
        This method calculates:
        - RSI (Relative Strength Index) - for overbought/oversold detection
        - MACD crossover - for momentum reversal detection
        - Buying/Selling pressure - for candle body analysis
        - Price momentum - for trend strength
        """
        try:
            # Start with existing market data
            enriched_data = dict(market_data) if market_data else {}
            
            # Get price data from TrueData live feed
            from data.truedata_client import live_market_data
            
            if symbol in live_market_data:
                symbol_data = live_market_data[symbol]
                
                # Add basic price data
                enriched_data['ltp'] = symbol_data.get('ltp', enriched_data.get('ltp', 0))
                enriched_data['open'] = symbol_data.get('open', enriched_data.get('open', 0))
                enriched_data['high'] = symbol_data.get('high', enriched_data.get('high', 0))
                enriched_data['low'] = symbol_data.get('low', enriched_data.get('low', 0))
                enriched_data['volume'] = symbol_data.get('volume', enriched_data.get('volume', 0))
                enriched_data['change_percent'] = symbol_data.get('change_percent', 0)
                
                ltp = float(enriched_data.get('ltp', 0))
                open_price = float(enriched_data.get('open', ltp))
                high = float(enriched_data.get('high', ltp))
                low = float(enriched_data.get('low', ltp))
                
                if ltp > 0 and open_price > 0:
                    change_pct = ((ltp - open_price) / open_price) * 100

                    # ============= PREFERRED: INDICATORS FROM 5m CANDLE CLOSES (mtf_data) =============
                    # This matches the rest of the system (RSI/MACD/Bollinger based on candle closes),
                    # not per-cycle LTP samples.
                    
                    # 🔧 FIX 2024-12-24: Ensure mtf_data is fetched BEFORE trying to use it!
                    # Without this, position analysis was falling back to tick-based RSI.
                    if not hasattr(self, 'mtf_data') or symbol not in self.mtf_data or not self.mtf_data.get(symbol, {}).get('5min'):
                        await self.fetch_multi_timeframe_data(symbol)
                    
                    mtf_series = self._get_indicator_series_from_mtf(symbol, timeframe='5min', limit=60)
                    opens_5m = mtf_series.get('opens', []) if isinstance(mtf_series, dict) else []
                    closes = mtf_series.get('closes', []) if isinstance(mtf_series, dict) else []
                    highs_5m = mtf_series.get('highs', []) if isinstance(mtf_series, dict) else []
                    lows_5m = mtf_series.get('lows', []) if isinstance(mtf_series, dict) else []

                    # RSI (prefer candle closes; fallback to legacy real_rsi buffer if candles missing)
                    if len(closes) >= 15:
                        rsi = self._calculate_rsi(closes, 14)
                        rsi_source = "mtf_5m"
                    else:
                        rsi = await self._calculate_real_rsi(symbol, ltp)
                        rsi_source = "ltp_buffer"
                    enriched_data['rsi'] = rsi

                    # Buying/Selling pressure (prefer last 5m candle range; fallback to day-range)
                    buying_pressure = 0.5
                    selling_pressure = 0.5
                    if (
                        highs_5m and lows_5m and opens_5m and closes and
                        len(highs_5m) == len(lows_5m) == len(opens_5m) == len(closes)
                    ):
                        last_high = float(highs_5m[-1] or 0)
                        last_low = float(lows_5m[-1] or 0)
                        last_open = float(opens_5m[-1] or 0)
                        last_close = float(closes[-1] or 0)
                        rng = last_high - last_low

                        if rng > 0 and last_close > 0 and last_open > 0:
                            # Close position in range: 0..1 (0 at low, 1 at high)
                            pos_in_range = (last_close - last_low) / rng
                            pos_in_range = max(0.0, min(1.0, pos_in_range))

                            # Candle body strength: 0..1, direction sets bias
                            body = (last_close - last_open) / rng
                            body_strength = min(1.0, abs(body))
                            direction = 1.0 if body >= 0 else -1.0

                            # Combine location + body into smoother pressure (avoids frequent 0/100 prints)
                            base_pressure = 0.5 + 0.5 * direction * body_strength  # 0..1
                            buying_pressure = 0.6 * base_pressure + 0.4 * pos_in_range

                            # Soft clamp to avoid exact 0/100 from rounding unless truly extreme
                            buying_pressure = max(0.01, min(0.99, buying_pressure))
                            selling_pressure = 1.0 - buying_pressure
                    else:
                        day_range = high - low
                        candle_body = ltp - open_price
                        if day_range > 0:
                            if candle_body > 0:  # Green day candle
                                buying_pressure = min(1.0, candle_body / day_range + 0.5)
                                selling_pressure = 1 - buying_pressure
                            else:  # Red day candle
                                selling_pressure = min(1.0, abs(candle_body) / day_range + 0.5)
                                buying_pressure = 1 - selling_pressure

                    enriched_data['buying_pressure'] = buying_pressure
                    enriched_data['selling_pressure'] = selling_pressure

                    # MACD (prefer real MACD from candle closes; fallback to neutral if not enough history)
                    macd_state = 'neutral'
                    macd_crossover_event = None
                    macd_hist = 0.0
                    if len(closes) >= 35:
                        macd_data = self.calculate_macd_signal(closes)
                        macd_state = macd_data.get('state', 'neutral') or 'neutral'
                        macd_crossover_event = macd_data.get('crossover')
                        macd_hist = float(macd_data.get('histogram', 0) or 0)

                    # Backward-compatible field name expected by open_position_decision.py
                    # Use crossover event when it exists, otherwise current state.
                    enriched_data['macd_state'] = macd_state
                    enriched_data['macd_crossover'] = macd_crossover_event or macd_state
                    enriched_data['macd_histogram'] = macd_hist
                    
                    # ============= MOMENTUM AND TREND =============
                    enriched_data['momentum'] = change_pct / 2.0  # Normalized momentum
                    enriched_data['intraday_change_pct'] = change_pct
                    
                    # Log enriched data summary
                    logger.info(
                        f"📊 {symbol} POSITION ANALYSIS: RSI={enriched_data.get('rsi', 'N/A'):.1f} ({rsi_source}), "
                        f"MACD={enriched_data.get('macd_crossover', 'N/A')}, Change={change_pct:+.2f}%, "
                        f"Buy/Sell={buying_pressure:.0%}/{selling_pressure:.0%}"
                    )
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching position data for {symbol}: {e}")
            return market_data if market_data else {}
    
    async def _calculate_real_rsi(self, symbol: str, current_price: float, period: int = 14) -> float:
        """
        🔥 PROPER RSI CALCULATION using real price history
        
        The old fake RSI was just mapping day's range to 30-70, which gave wrong values
        like RSI=41 for a stock up 3.31%. Real RSI requires historical price changes.
        """
        try:
            # Prefer candle closes from mtf_data for RSI whenever available
            mtf_series = self._get_indicator_series_from_mtf(symbol, timeframe='5min', limit=60)
            closes = mtf_series.get('closes', []) if isinstance(mtf_series, dict) else []
            if len(closes) >= period + 1:
                return self._calculate_rsi(closes, period)

            # Initialize price history if needed
            if not hasattr(self, '_rsi_price_history'):
                self._rsi_price_history = {}
            
            if symbol not in self._rsi_price_history:
                self._rsi_price_history[symbol] = []
            
            # Add current price to history
            self._rsi_price_history[symbol].append(current_price)
            
            # Keep last 50 prices
            self._rsi_price_history[symbol] = self._rsi_price_history[symbol][-50:]
            
            prices = self._rsi_price_history[symbol]
            
            # Need at least period+1 prices for RSI
            if len(prices) < period + 1:
                # Fallback: estimate from intraday change when not enough history
                from data.truedata_client import live_market_data
                if symbol in live_market_data:
                    data = live_market_data[symbol]
                    ltp = data.get('ltp', current_price)
                    open_price = data.get('open', ltp)
                    if open_price > 0:
                        change_pct = ((ltp - open_price) / open_price) * 100
                        # Better estimation: map change to RSI more accurately
                        if change_pct > 3.0:
                            return 90.0  # Very strong bullish
                        elif change_pct > 2.0:
                            return 80.0  # Strong bullish
                        elif change_pct > 1.0:
                            return 70.0  # Bullish
                        elif change_pct > 0.5:
                            return 60.0  # Mildly bullish
                        elif change_pct > -0.5:
                            return 50.0  # Neutral
                        elif change_pct > -1.0:
                            return 40.0  # Mildly bearish
                        elif change_pct > -2.0:
                            return 30.0  # Bearish
                        elif change_pct > -3.0:
                            return 20.0  # Strong bearish
                        else:
                            return 10.0  # Very strong bearish
                return 50.0  # Neutral if no data
            
            # Calculate price changes
            prices_arr = np.array(prices)
            deltas = np.diff(prices_arr)
            
            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gain and loss (Wilder's smoothing)
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            # Handle edge cases
            if avg_loss == 0 and avg_gain == 0:
                return 50.0  # No movement
            elif avg_loss == 0:
                return 95.0  # Only gains - very overbought
            elif avg_gain == 0:
                return 5.0   # Only losses - very oversold
            
            # Calculate RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Clamp to valid range
            return max(5.0, min(95.0, rsi))
            
        except Exception as e:
            logger.debug(f"Error calculating real RSI for {symbol}: {e}")
            return 50.0  # Return neutral on error
    
    async def _execute_position_decision(self, symbol: str, current_price: float, 
                                       position: Dict, decision_result):
        """Execute the decision from enhanced position analysis"""
        try:
            action = decision_result.action
            
            if action.value == "EXIT_FULL":
                # Full position exit
                await self.exit_position(symbol, current_price, decision_result.exit_reason.value)
                logger.info(f"✅ EXECUTED: Full exit for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "EXIT_PARTIAL":
                # Partial position exit
                percentage = decision_result.quantity_percentage
                await self.book_partial_profits(symbol, current_price, position, percentage)
                logger.info(f"✅ EXECUTED: Partial exit {percentage}% for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "EMERGENCY_EXIT":
                # Emergency exit
                await self.exit_position(symbol, current_price, "EMERGENCY_EXIT")
                logger.warning(f"🚨 EXECUTED: Emergency exit for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "SCALE_IN":
                # Scale into position
                percentage = decision_result.quantity_percentage
                current_quantity = position.get('quantity', 0)
                scale_quantity = int(current_quantity * percentage / 100)
                if scale_quantity > 0:
                    await self.scale_into_position(symbol, current_price, position, scale_quantity)
                    logger.info(f"✅ EXECUTED: Scale in {scale_quantity} shares for {symbol} - {decision_result.reasoning}")
                
            elif action.value in ["TRAIL_STOP", "ADJUST_STOP"]:
                # Adjust stop loss
                if decision_result.new_stop_loss:
                    await self.adjust_dynamic_stop_loss(symbol, current_price, position, decision_result.new_stop_loss)
                    logger.info(f"✅ EXECUTED: Stop adjustment to ₹{decision_result.new_stop_loss:.2f} for {symbol}")
                
            elif action.value == "HOLD":
                # Hold position - no action needed
                logger.debug(f"📊 HOLDING: {symbol} - {decision_result.reasoning}")
                
            else:
                logger.warning(f"⚠️ Unknown position action: {action.value} for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error executing position decision for {symbol}: {e}")
    
    async def should_exit_position(self, symbol: str, current_price: float, position: Dict) -> Dict:
        """Determine if position should be exited based on trailing stops, targets, time"""
        try:
            entry_price = position.get('entry_price', 0)
            action = position.get('action', 'BUY')
            stop_loss = position.get('stop_loss', 0)
            target = position.get('target', 0)
            
            # CRITICAL FIX: Handle None values for stop_loss and target
            if stop_loss is None:
                stop_loss = 0
            if target is None:
                target = 0
            
            # Check stop loss (only if not zero)
            if stop_loss > 0:
                if action == 'BUY' and current_price <= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
                elif action == 'SELL' and current_price >= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
            
            # Check target (only if not zero)
            if target > 0:
                if action == 'BUY' and current_price >= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
                elif action == 'SELL' and current_price <= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
            
            # Check trailing stop
            if symbol in self.trailing_stops:
                trailing_stop = self.trailing_stops[symbol]['stop_price']
                if action == 'BUY' and current_price <= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
                elif action == 'SELL' and current_price >= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
            
            # Check position age (auto-close old positions)
            entry_time = self.position_entry_times.get(symbol)
            if entry_time:
                age_hours = (datetime.now() - entry_time).total_seconds() / 3600
                if age_hours > self.max_position_age_hours:
                    return {'should_exit': True, 'reason': 'POSITION_EXPIRED'}
            
            return {'should_exit': False, 'reason': 'HOLD'}
            
        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")
            return {'should_exit': False, 'reason': 'ERROR'}
    
    async def update_trailing_stop(self, symbol: str, current_price: float, position: Dict):
        """Update trailing stop for profitable positions"""
        try:
            action = position.get('action', 'BUY')
            entry_price = position.get('entry_price', 0)
            
            # Calculate profit percentage
            if action == 'BUY':
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # 🚨 DEFENSIVE: Ensure profit_lock_percentage exists (fallback for inheritance issues)
            if not hasattr(self, 'profit_lock_percentage'):
                logger.warning("⚠️ profit_lock_percentage not found, using default")
                self.profit_lock_percentage = 1.0  # Lock profit at 1%
            
            # Only set trailing stop if position is profitable
            if profit_pct > self.profit_lock_percentage:
                
                # 🚨 DEFENSIVE: Ensure trailing_stop_percentage exists
                if not hasattr(self, 'trailing_stop_percentage'):
                    logger.warning("⚠️ trailing_stop_percentage not found, using default")
                    self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
                
                # Calculate trailing stop price
                if action == 'BUY':
                    trailing_stop_price = current_price * (1 - self.trailing_stop_percentage / 100)
                else:
                    trailing_stop_price = current_price * (1 + self.trailing_stop_percentage / 100)
                
                # Update trailing stop if it's better than current
                if symbol not in self.trailing_stops:
                    self.trailing_stops[symbol] = {
                        'stop_price': trailing_stop_price,
                        'last_update': datetime.now(),
                        'highest_profit': profit_pct
                    }
                    logger.info(f"🎯 {self.name}: Set trailing stop for {symbol} at ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                    
                    # 🔥 CRITICAL FIX: Sync to position_tracker when first setting trailing stop
                    try:
                        from src.core.position_tracker import position_tracker
                        if symbol in position_tracker.positions:
                            position_tracker.positions[symbol].trailing_stop = trailing_stop_price
                            position_tracker.positions[symbol].stop_loss = trailing_stop_price
                            logger.info(f"✅ NEW TRAILING STOP SYNCED: {symbol} → ₹{trailing_stop_price:.2f}")
                    except Exception as sync_err:
                        logger.error(f"❌ Failed to sync new trailing stop: {sync_err}")
                else:
                    current_trailing = self.trailing_stops[symbol]
                    
                    # Update if new trailing stop is better
                    if ((action == 'BUY' and trailing_stop_price > current_trailing['stop_price']) or
                        (action == 'SELL' and trailing_stop_price < current_trailing['stop_price'])):
                        
                        self.trailing_stops[symbol].update({
                            'stop_price': trailing_stop_price,
                            'last_update': datetime.now(),
                            'highest_profit': max(profit_pct, current_trailing['highest_profit'])
                        })
                        logger.info(f"🎯 {self.name}: Updated trailing stop for {symbol} to ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                        
                        # 🔥 CRITICAL FIX: Sync to position_tracker so position_monitor can trigger exits!
                        try:
                            from src.core.position_tracker import position_tracker
                            if symbol in position_tracker.positions:
                                position_tracker.positions[symbol].trailing_stop = trailing_stop_price
                                # Also update stop_loss to the trailing level
                                position_tracker.positions[symbol].stop_loss = trailing_stop_price
                                logger.info(f"✅ TRAILING STOP SYNCED TO POSITION TRACKER: {symbol} → ₹{trailing_stop_price:.2f}")
                        except Exception as sync_err:
                            logger.error(f"❌ Failed to sync trailing stop to position_tracker: {sync_err}")
                        
                        # 🔥 CRITICAL FIX: Send trailing stop to broker
                        await self._modify_broker_stop_loss(symbol, trailing_stop_price, action)
                        
        except Exception as e:
            logger.error(f"Error updating trailing stop for {symbol}: {e}")
    
    async def _modify_broker_stop_loss(self, symbol: str, new_sl_price: float, action: str):
        """🔥 CRITICAL: Modify stop loss order at broker for trailing stops"""
        try:
            # Get orchestrator to access zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not (orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client):
                logger.debug(f"⚠️ Cannot modify SL - zerodha client not available")
                return
            
            zerodha = orchestrator.zerodha_client
            
            # Get current open SL order for this symbol
            try:
                orders = await zerodha.get_orders()
                if not orders:
                    logger.debug(f"⚠️ No orders found for {symbol}")
                    return
            except Exception as e:
                logger.error(f"Error fetching orders for {symbol}: {e}")
                return
            
            # Find the active SL order for this symbol
            sl_order = None
            for order in orders:
                if (order.get('tradingsymbol') == symbol and 
                    order.get('order_type') in ['SL', 'SL-M'] and
                    order.get('status') in ['OPEN', 'TRIGGER PENDING'] and
                    order.get('tag') == 'ALGO_SL'):
                    sl_order = order
                    break
            
            if not sl_order:
                logger.debug(f"⚠️ No open SL order found for {symbol} (may have been filled)")
                return
            
            order_id = sl_order.get('order_id')
            old_trigger = sl_order.get('trigger_price', 0)
            
            # Only modify if new SL is significantly different (avoid spam)
            if abs(new_sl_price - old_trigger) < 0.50:  # Less than ₹0.50 change
                logger.debug(f"Skipping SL modification for {symbol} - change too small")
                return
            
            # Modify the SL order with new trigger price
            modify_params = {
                'trigger_price': new_sl_price,
                'order_type': 'SL-M'
            }
            
            result = await zerodha.modify_order(order_id, modify_params)
            
            if result:
                logger.info(f"✅ BROKER SL UPDATED: {symbol} {old_trigger:.2f} -> {new_sl_price:.2f} (Order: {order_id})")
            else:
                logger.warning(f"⚠️ SL modification returned no result for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error modifying broker SL for {symbol}: {e}")
    
    async def analyze_position_management(self, symbol: str, current_price: float, position: Dict, market_data: Dict) -> Dict:
        """🧠 INTELLIGENT POSITION ANALYSIS - Determine optimal management actions"""
        try:
            entry_price = position.get('entry_price', 0)
            action = position.get('action', 'BUY')
            quantity = position.get('quantity', 0)
            entry_time = position.get('timestamp')
            
            # Calculate current profit/loss
            if action == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Calculate position age in minutes
            position_age = 0
            if entry_time:
                try:
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    else:
                        entry_dt = entry_time
                    position_age = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 60
                except:
                    position_age = 0
            
            # Get market indicators
            volume = market_data.get('volume', 0)
            change_pct = market_data.get('change_percent', 0)
            
            actions = {
                'book_partial_profits': False,
                'scale_position': False,
                'adjust_stop_loss': False,
                'partial_percentage': 0,
                'scale_quantity': 0,
                'new_stop_loss': 0
            }
            
            # 1. DYNAMIC PROFIT BOOKING - DIFFERENT FOR OPTIONS vs EQUITY
            target = position.get('target', 0)
            is_options = position.get('is_options', False) or 'CE' in symbol or 'PE' in symbol
            
            if is_options:
                # 🚨 OPTIONS PROFIT BOOKING - Much quicker due to theta decay
                # Options profits vanish quickly if not booked!
                
                if pnl_pct >= 15 and not self._has_booked_partial(symbol, '50%'):
                    # 15%+ profit: Book 50% immediately
                    actions['book_partial_profits'] = True
                    actions['partial_percentage'] = 50
                    logger.info(f"💰 OPTIONS PROFIT: {symbol} - Booking 50% at +{pnl_pct:.1f}% (15% threshold)")
                    
                elif pnl_pct >= 25 and not self._has_booked_partial(symbol, '75%'):
                    # 25%+ profit: Book another 25% (total 75% booked)
                    actions['book_partial_profits'] = True
                    actions['partial_percentage'] = 50  # 50% of remaining = 25% of original
                    logger.info(f"💰 OPTIONS PROFIT: {symbol} - Booking 50% of remaining at +{pnl_pct:.1f}% (25% threshold)")
                    
                elif pnl_pct >= 40:
                    # 40%+ profit: Book everything, don't be greedy
                    actions['immediate_exit'] = True
                    actions['exit_reason'] = 'OPTIONS_PROFIT_40PCT'
                    logger.info(f"💰 OPTIONS PROFIT: {symbol} - FULL EXIT at +{pnl_pct:.1f}% (40% is great for options!)")
                    
                # Time-based exit for options regardless of profit
                if position_age >= 60:  # 1 hour max hold for options
                    if pnl_pct > 0:
                        actions['immediate_exit'] = True
                        actions['exit_reason'] = 'OPTIONS_TIME_EXIT_1HR_PROFIT'
                        logger.info(f"⏰ OPTIONS TIME EXIT: {symbol} - Exiting with +{pnl_pct:.1f}% after 1hr (theta risk)")
                    elif pnl_pct > -5:
                        actions['immediate_exit'] = True
                        actions['exit_reason'] = 'OPTIONS_TIME_EXIT_1HR_SMALL_LOSS'
                        logger.info(f"⏰ OPTIONS TIME EXIT: {symbol} - Exiting at {pnl_pct:.1f}% after 1hr (cut losses)")
                        
            else:
                # EQUITY PROFIT BOOKING (original logic)
                if target > 0:
                    # Calculate distance to target
                    if action == 'BUY':
                        target_achievement = (current_price - entry_price) / (target - entry_price) if target > entry_price else 0
                    else:
                        target_achievement = (entry_price - current_price) / (entry_price - target) if entry_price > target else 0
                    
                    # Dynamic profit booking based on target progress
                    if target_achievement >= 0.8:  # 80% of target achieved
                        if position_age > 30:  # Held for 30+ minutes - book profits
                            actions['book_partial_profits'] = True
                            actions['partial_percentage'] = 60  # Book 60% of position
                            logger.info(f"💰 {self.name}: {symbol} - Booking 60% profits (Target: {target_achievement*100:.1f}%, Age: {position_age:.1f}min)")
                    elif target_achievement >= 1.0:  # Target exceeded - aggressive booking
                        actions['book_partial_profits'] = True
                        actions['partial_percentage'] = 80  # Book 80% profits
                        logger.info(f"💰 {self.name}: {symbol} - Target exceeded! Booking 80% profits (Achievement: {target_achievement*100:.1f}%)")
            
            # 2. MOMENTUM-BASED POSITION SCALING (Conservative - only for strong setups)
            # Only scale if risk per trade is still within 1% limit
            current_risk_percent = abs(current_price - position.get('stop_loss', entry_price)) / entry_price * 100 if entry_price > 0 else 0
            if current_risk_percent < 0.8 and pnl_pct > 3 and abs(change_pct) > 1.5:  # Conservative scaling
                if position_age < 10 and quantity < 150:  # Fresh position, not too large
                    actions['scale_position'] = True
                    actions['scale_quantity'] = max(1, int(quantity * 0.15))  # Scale by 15% only
                    logger.info(f"📈 {self.name}: {symbol} - Conservative scaling by {actions['scale_quantity']} shares (risk: {current_risk_percent:.2f}%)")
            
            # 3. DYNAMIC TRAILING STOP - DIFFERENT FOR OPTIONS vs EQUITY
            original_stop = position.get('stop_loss', 0)
            is_options = position.get('is_options', False) or 'CE' in symbol or 'PE' in symbol
            
            if is_options:
                # 🚨 OPTIONS TRAILING STOP - Much more aggressive due to theta decay
                # Options need to lock in profits quickly or theta eats them
                if pnl_pct >= 10:
                    # 10%+ profit: Move stop to ENTRY (lock in zero loss)
                    if action == 'BUY':
                        actions['new_stop_loss'] = entry_price  # Breakeven
                    else:
                        actions['new_stop_loss'] = entry_price
                    actions['adjust_stop_loss'] = True
                    logger.info(f"🛡️ OPTIONS TRAILING: {symbol} - Moving stop to BREAKEVEN (P&L: {pnl_pct:.2f}%)")
                    
                elif pnl_pct >= 20:
                    # 20%+ profit: Lock in 50% of profits
                    locked_profit = (current_price - entry_price) * 0.5 if action == 'BUY' else (entry_price - current_price) * 0.5
                    if action == 'BUY':
                        actions['new_stop_loss'] = entry_price + locked_profit
                    else:
                        actions['new_stop_loss'] = entry_price - locked_profit
                    actions['adjust_stop_loss'] = True
                    logger.info(f"🛡️ OPTIONS TRAILING: {symbol} - Locking 50% profit (P&L: {pnl_pct:.2f}%)")
                    
                elif pnl_pct >= 30:
                    # 30%+ profit: Lock in 70% of profits (tight trailing)
                    locked_profit = (current_price - entry_price) * 0.7 if action == 'BUY' else (entry_price - current_price) * 0.7
                    if action == 'BUY':
                        actions['new_stop_loss'] = entry_price + locked_profit
                    else:
                        actions['new_stop_loss'] = entry_price - locked_profit
                    actions['adjust_stop_loss'] = True
                    logger.info(f"🛡️ OPTIONS TRAILING: {symbol} - Locking 70% profit (P&L: {pnl_pct:.2f}%)")
            else:
                # EQUITY trailing stop (original logic)
                if original_stop > 0 and pnl_pct > 5:  # Only after decent profit
                    original_risk_distance = abs(entry_price - original_stop)
                    buffer_distance = original_risk_distance * 0.3  # 30% of original risk as buffer
                    
                    if action == 'BUY':
                        actions['new_stop_loss'] = max(entry_price + buffer_distance, current_price - original_risk_distance * 0.8)
                    else:
                        actions['new_stop_loss'] = min(entry_price - buffer_distance, current_price + original_risk_distance * 0.8)
                    actions['adjust_stop_loss'] = True
                    logger.info(f"🛡️ {self.name}: {symbol} - Dynamic trailing stop (P&L: {pnl_pct:.2f}%, Risk Distance: {original_risk_distance:.2f})")
            
            # 4. SCALPING AUTO-EXIT: Close positions after 10 minutes max (quick in/out)
            if position_age > 10:  # 10 minutes max hold for scalping
                actions['immediate_exit'] = True
                actions['exit_reason'] = 'SCALPING_AUTO_EXIT_10MIN'
                logger.info(f"⚡ {self.name}: {symbol} - Auto-exit after {position_age:.1f} minutes (scalping rule)")
            
            # 5. SMALL PROFIT CAPTURE: Take profits quickly on small moves
            elif pnl_pct > 3 and position_age > 2:  # 3%+ profit after 2+ minutes
                actions['immediate_exit'] = True
                actions['exit_reason'] = 'QUICK_PROFIT_CAPTURE'
                logger.info(f"💨 {self.name}: {symbol} - Quick profit capture: {pnl_pct:.2f}% in {position_age:.1f}min")
            
            return actions
            
        except Exception as e:
            logger.error(f"Error analyzing position management for {symbol}: {e}")
            return {}
    
    async def book_partial_profits(self, symbol: str, current_price: float, position: Dict, percentage: int):
        """💰 PARTIAL PROFIT BOOKING - Lock in profits while maintaining exposure"""
        try:
            current_quantity = position.get('quantity', 0)
            action = position.get('action', 'BUY')
            
            # Calculate quantity to book
            quantity_to_book = max(1, int(current_quantity * percentage / 100))
            
            # 🔥 FIX: Minimum order value check for partial exits
            # Partial exits that create tiny orders waste brokerage
            MIN_PARTIAL_ORDER_VALUE = 50000.0  # ₹50,000 minimum for partial exits
            partial_order_value = quantity_to_book * current_price
            remaining_qty = current_quantity - quantity_to_book
            remaining_value = remaining_qty * current_price
            
            if partial_order_value < MIN_PARTIAL_ORDER_VALUE:
                # Partial exit too small - check if full exit makes sense
                if remaining_value < MIN_PARTIAL_ORDER_VALUE:
                    # Both partial and remaining are small - do FULL exit instead
                    logger.warning(f"🔄 {symbol}: Partial exit ₹{partial_order_value:,.0f} too small, doing FULL exit instead")
                    await self.exit_position(symbol, current_price, f'FULL_EXIT_SMALL_POSITION')
                    return
                else:
                    # Skip partial, keep full position
                    logger.info(f"⏭️ {symbol}: Skipping partial exit (₹{partial_order_value:,.0f} < ₹{MIN_PARTIAL_ORDER_VALUE:,.0f})")
                    return
            
            # Also check remaining position isn't too small
            if remaining_value < MIN_PARTIAL_ORDER_VALUE and remaining_qty > 0:
                # Remaining would be too small - do full exit
                logger.warning(f"🔄 {symbol}: Remaining ₹{remaining_value:,.0f} too small, doing FULL exit instead")
                await self.exit_position(symbol, current_price, f'FULL_EXIT_SMALL_REMAINING')
                return
            
            # Create exit signal for partial quantity
            exit_action = 'SELL' if action == 'BUY' else 'BUY'
            
            # Generate partial exit signal for execution
            partial_signal = await self._create_management_signal(
                symbol=symbol,
                action=exit_action,
                quantity=quantity_to_book,
                price=current_price,
                reason=f'PARTIAL_PROFIT_BOOKING_{percentage}%'
            )
            
            # Execute the partial exit order
            if partial_signal:
                await self._execute_management_action(partial_signal)
                logger.info(f"💰 {self.name}: Booking {percentage}% profits for {symbol} - {quantity_to_book} shares at ₹{current_price:.2f}")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'PARTIAL_PROFIT_BOOKING_{percentage}%')
                self.last_management_time[symbol] = datetime.now()
                
                # Update position quantity
                remaining_quantity = current_quantity - quantity_to_book
                if remaining_quantity > 0:
                    position['quantity'] = remaining_quantity
                    logger.info(f"📊 {symbol}: Remaining position - {remaining_quantity} shares")
                else:
                    # Position fully closed
                    await self.exit_position(symbol, current_price, f'FULL_PROFIT_BOOKING_{percentage}%')
            
        except Exception as e:
            logger.error(f"Error booking partial profits for {symbol}: {e}")
    
    async def scale_into_position(self, symbol: str, current_price: float, position: Dict, additional_quantity: int):
        """📈 POSITION SCALING - Add to winning positions with strong momentum"""
        try:
            action = position.get('action', 'BUY')
            
            # Create additional position signal for execution
            scale_signal = await self._create_management_signal(
                symbol=symbol,
                action=action,  # Same direction as original
                quantity=additional_quantity,
                price=current_price,
                reason='POSITION_SCALING_MOMENTUM'
            )
            
            # Execute the scaling order
            if scale_signal:
                await self._execute_management_action(scale_signal)
                logger.info(f"📈 {self.name}: Scaling {symbol} position - Adding {additional_quantity} shares at ₹{current_price:.2f}")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'POSITION_SCALING_{additional_quantity}_shares')
                self.last_management_time[symbol] = datetime.now()
                
                # Update position tracking to include scaled quantity
                current_quantity = position.get('quantity', 0)
                position['quantity'] = current_quantity + additional_quantity
                
                # Recalculate average entry price
                current_entry = position.get('entry_price', 0)
                current_value = current_quantity * current_entry
                additional_value = additional_quantity * current_price
                new_avg_entry = (current_value + additional_value) / (current_quantity + additional_quantity)
                position['entry_price'] = new_avg_entry
                
                logger.info(f"📊 {symbol}: Scaled position - {position['quantity']} total shares, avg entry: ₹{new_avg_entry:.2f}")
            
        except Exception as e:
            logger.error(f"Error scaling position for {symbol}: {e}")
    
    async def adjust_dynamic_stop_loss(self, symbol: str, current_price: float, position: Dict, new_stop_loss: float):
        """🛡️ DYNAMIC STOP LOSS - Adjust stop loss based on market conditions"""
        try:
            current_stop = position.get('stop_loss', 0)
            action = position.get('action', 'BUY')
            
            # Only adjust if new stop is better (more protective while profitable)
            should_update = False
            if action == 'BUY' and new_stop_loss > current_stop:
                should_update = True
            elif action == 'SELL' and (current_stop == 0 or new_stop_loss < current_stop):
                should_update = True
            
            if should_update:
                position['stop_loss'] = new_stop_loss
                logger.info(f"🛡️ {self.name}: Adjusted {symbol} stop loss to ₹{new_stop_loss:.2f} (was ₹{current_stop:.2f})")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'STOP_LOSS_ADJUSTMENT_TO_{new_stop_loss:.2f}')
                self.last_management_time[symbol] = datetime.now()
                
                # 🔥 CRITICAL FIX: Sync stop loss to position_tracker so position_monitor can trigger exits!
                # Without this, stop losses were only stored locally and NEVER executed
                try:
                    from src.core.position_tracker import position_tracker
                    if symbol in position_tracker.positions:
                        position_tracker.positions[symbol].stop_loss = new_stop_loss
                        logger.info(f"✅ STOP LOSS SYNCED TO POSITION TRACKER: {symbol} → ₹{new_stop_loss:.2f}")
                    else:
                        logger.warning(f"⚠️ {symbol} not in position_tracker - stop loss only local")
                except Exception as sync_err:
                    logger.error(f"❌ Failed to sync stop loss to position_tracker: {sync_err}")
            
        except Exception as e:
            logger.error(f"Error adjusting stop loss for {symbol}: {e}")
    
    async def apply_time_based_management(self, symbol: str, current_price: float, position: Dict):
        """⏰ TIME-BASED MANAGEMENT - Apply time decay considerations"""
        try:
            entry_time = position.get('timestamp')
            if not entry_time:
                return
                
            # Calculate position age
            try:
                if isinstance(entry_time, str):
                    entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                else:
                    entry_dt = entry_time
                position_age_hours = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 3600
            except:
                return
            
            action = position.get('action', 'BUY')
            entry_price = position.get('entry_price', 0)
            
            # Calculate current P&L
            if action == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Time-based profit protection (tighten stops over time)
            if position_age_hours > 2 and pnl_pct > 0:  # 2+ hours and profitable
                # Tighten trailing stop for older positions
                tighter_stop_pct = max(0.5, 2.0 - (position_age_hours * 0.2))  # Gradually tighten
                
                if symbol in self.trailing_stops:
                    current_trail = self.trailing_stops[symbol]['stop_price']
                    if action == 'BUY':
                        tighter_stop = current_price * (1 - tighter_stop_pct / 100)
                        if tighter_stop > current_trail:
                            self.trailing_stops[symbol]['stop_price'] = tighter_stop
                            logger.info(f"⏰ {self.name}: Tightened trailing stop for {symbol} due to time (age: {position_age_hours:.1f}h)")
                    else:
                        tighter_stop = current_price * (1 + tighter_stop_pct / 100)
                        if tighter_stop < current_trail:
                            self.trailing_stops[symbol]['stop_price'] = tighter_stop
                            logger.info(f"⏰ {self.name}: Tightened trailing stop for {symbol} due to time (age: {position_age_hours:.1f}h)")
            
        except Exception as e:
            logger.error(f"Error applying time-based management for {symbol}: {e}")
    
    async def apply_volatility_based_management(self, symbol: str, current_price: float, position: Dict, market_data: Dict):
        """📊 VOLATILITY-BASED MANAGEMENT - Adjust based on market volatility"""
        try:
            # Calculate short-term volatility from price movements
            high = market_data.get('high', current_price)
            low = market_data.get('low', current_price)
            volume = market_data.get('volume', 0)
            
            # Calculate intraday volatility
            if high > 0 and low > 0:
                intraday_volatility = ((high - low) / current_price) * 100
                
                action = position.get('action', 'BUY')
                entry_price = position.get('entry_price', 0)
                
                # High volatility (>3%) - tighten stops
                if intraday_volatility > 3:
                    if symbol in self.trailing_stops:
                        current_trail = self.trailing_stops[symbol]['stop_price']
                        volatility_adjustment = 0.5  # Tighter stops in high volatility
                        
                        if action == 'BUY':
                            adjusted_stop = current_price * (1 - volatility_adjustment / 100)
                            if adjusted_stop > current_trail:
                                self.trailing_stops[symbol]['stop_price'] = adjusted_stop
                                logger.info(f"📊 {self.name}: Tightened stop for {symbol} due to high volatility ({intraday_volatility:.2f}%)")
                        else:
                            adjusted_stop = current_price * (1 + volatility_adjustment / 100)
                            if adjusted_stop < current_trail:
                                self.trailing_stops[symbol]['stop_price'] = adjusted_stop
                                logger.info(f"📊 {self.name}: Tightened stop for {symbol} due to high volatility ({intraday_volatility:.2f}%)")
                
                # Low volatility (<1%) with high volume - consider scaling
                elif intraday_volatility < 1 and volume > 500000:
                    # This suggests strong conviction move - handled in main analysis
                    pass
            
        except Exception as e:
            logger.error(f"Error applying volatility-based management for {symbol}: {e}")
    
    def get_position_management_summary(self) -> Dict:
        """📊 GET POSITION MANAGEMENT SUMMARY - For monitoring and reporting"""
        try:
            summary = {
                'total_positions': len(self.active_positions),
                'positions_with_trailing_stops': len(self.trailing_stops),
                'management_actions': {},
                'position_details': []
            }
            
            # Count management actions
            for symbol, actions in self.management_actions_taken.items():
                for action in actions:
                    if action not in summary['management_actions']:
                        summary['management_actions'][action] = 0
                    summary['management_actions'][action] += 1
            
            # Position details with current P&L
            for symbol, position in self.active_positions.items():
                entry_price = position.get('entry_price', 0)
                current_price = position.get('current_price', entry_price)
                action = position.get('action', 'BUY')
                quantity = position.get('quantity', 0)
                
                # Calculate P&L
                if action == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                
                # Position age
                entry_time = position.get('timestamp')
                age_hours = 0
                if entry_time:
                    try:
                        if isinstance(entry_time, str):
                            entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                        else:
                            entry_dt = entry_time
                        age_hours = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 3600
                    except:
                        pass
                
                position_detail = {
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl_percent': pnl_pct,
                    'age_hours': age_hours,
                    'has_trailing_stop': symbol in self.trailing_stops,
                    'management_actions': self.management_actions_taken.get(symbol, [])
                }
                
                summary['position_details'].append(position_detail)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating position management summary: {e}")
            return {}
    
    def log_position_management_status(self):
        """📊 LOG POSITION MANAGEMENT STATUS - Regular monitoring log"""
        try:
            summary = self.get_position_management_summary()
            
            if summary['total_positions'] > 0:
                logger.info(f"🎯 {self.name} POSITION MANAGEMENT STATUS:")
                logger.info(f"   📊 Total Positions: {summary['total_positions']}")
                logger.info(f"   🛡️ Trailing Stops: {summary['positions_with_trailing_stops']}")
                
                # Log management actions taken
                if summary['management_actions']:
                    actions_str = ", ".join([f"{action}: {count}" for action, count in summary['management_actions'].items()])
                    logger.info(f"   ⚡ Actions Taken: {actions_str}")
                
                # Log top 3 positions by P&L
                positions = sorted(summary['position_details'], key=lambda x: x['pnl_percent'], reverse=True)[:3]
                for pos in positions:
                    logger.info(f"   📈 {pos['symbol']}: {pos['pnl_percent']:.2f}% | "
                               f"Age: {pos['age_hours']:.1f}h | Actions: {len(pos['management_actions'])}")
        
        except Exception as e:
            logger.error(f"Error logging position management status: {e}")
    
    async def _create_management_signal(self, symbol: str, action: str, quantity: int, price: float, reason: str) -> Dict:
        """🎯 CREATE MANAGEMENT SIGNAL - Format position management actions as executable signals"""
        try:
            # Create signal in the same format as regular trading signals
            management_signal = {
                'signal_id': f"{self.name}_MGMT_{symbol}_{int(time_module.time())}",
                'symbol': symbol,
                'action': action.upper(),
                'quantity': quantity,
                'entry_price': price,
                'price': price,  # Both fields for compatibility
                'order_type': 'MARKET',  # Management actions use market orders for quick execution
                'product': self._get_product_type_for_symbol(symbol),
                'validity': 'DAY',
                'tag': 'POSITION_MGMT',
                'strategy': self.name,
                'strategy_name': self.name,
                'reason': reason,
                'user_id': 'system',
                'timestamp': datetime.now().isoformat(),
                'management_action': True,  # Flag to identify management actions
                'closing_action': True,     # Allow execution even after 3:00 PM
                'source': 'position_management'
            }
            
            logger.debug(f"🎯 Created management signal: {symbol} {action} {quantity} @ ₹{price:.2f} ({reason})")
            return management_signal
            
        except Exception as e:
            logger.error(f"Error creating management signal for {symbol}: {e}")
            return {}
    
    def _get_product_type_for_symbol(self, symbol: str) -> str:
        """Get appropriate product type for symbol"""
        # Options require NRML, equity can use MIS for intraday
        if 'CE' in symbol or 'PE' in symbol:
            return 'NRML'  # Options must use NRML
        else:
            return 'MIS'  # Margin Intraday Square-off for equity
    
    async def _execute_management_action(self, signal: Dict):
        """🚀 EXECUTE MANAGEMENT ACTION - Send management signals for immediate execution"""
        try:
            # 🚨 CRITICAL: Record order placement to prevent duplicates
            symbol = signal.get('symbol')
            if symbol:
                self._record_order_placement(symbol)
            
            # Get orchestrator instance for execution
            orchestrator = self._get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                # Send directly to trade engine for immediate execution
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.info(f"🚀 Executing management action: {signal['symbol']} {signal['action']} {signal['quantity']} ({reason})")
                
                # Process through trade engine (bypasses deduplication for management actions)
                await orchestrator.trade_engine._process_live_signal(signal)
                
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.info(f"✅ Management action submitted: {signal['symbol']} {reason}")
                
            else:
                # Fallback: Store in pending management actions for next cycle processing
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.warning(f"⚠️ No trade engine available - queuing management action: {signal['symbol']} {reason}")
                
                if not hasattr(self, 'pending_management_actions'):
                    self.pending_management_actions = []
                self.pending_management_actions.append(signal)
                
        except Exception as e:
            logger.error(f"❌ Error executing management action for {signal.get('symbol', 'UNKNOWN')}: {e}")
            # Don't raise exception to avoid breaking position management loop
    
    def _get_orchestrator_instance(self):
        """Get orchestrator instance for execution"""
        try:
            # Try to get orchestrator instance from singleton pattern
            if hasattr(self, 'orchestrator') and self.orchestrator:
                return self.orchestrator
            
            # Try to get from TradingOrchestrator singleton
            from src.core.orchestrator import TradingOrchestrator
            return getattr(TradingOrchestrator, '_instance', None)
            
        except Exception as e:
            logger.error(f"Error getting orchestrator instance: {e}")
            return None
    
    async def process_pending_management_actions(self):
        """🔄 PROCESS PENDING MANAGEMENT ACTIONS - Handle queued management actions"""
        try:
            if not hasattr(self, 'pending_management_actions') or not self.pending_management_actions:
                return
            
            logger.info(f"🔄 Processing {len(self.pending_management_actions)} pending management actions")
            
            for signal in self.pending_management_actions.copy():
                await self._execute_management_action(signal)
                self.pending_management_actions.remove(signal)
                
            logger.info(f"✅ Processed all pending management actions")
            
        except Exception as e:
            logger.error(f"Error processing pending management actions: {e}")
    
    async def exit_position(self, symbol: str, exit_price: float, reason: str):
        """Exit position and clean up tracking data"""
        try:
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                entry_price = position.get('entry_price', 0)
                action = position.get('action', 'BUY')
                
                # Calculate realized P&L
                if action == 'BUY':
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                
                # Log position exit
                logger.info(f"🚪 {self.name}: EXITING {symbol} at ₹{exit_price:.2f} | "
                           f"Entry: ₹{entry_price:.2f} | P&L: {pnl_pct:.2f}% | Reason: {reason}")
                
                # Clean up position tracking
                del self.active_positions[symbol]
                if symbol in self.position_metadata:
                    del self.position_metadata[symbol]
                if symbol in self.trailing_stops:
                    del self.trailing_stops[symbol]
                if symbol in self.position_entry_times:
                    del self.position_entry_times[symbol]
                
                # Create exit signal for execution
                exit_signal = {
                    'symbol': symbol,
                    'action': 'SELL' if action == 'BUY' else 'BUY',  # Opposite action to close
                    'entry_price': exit_price,
                    'stop_loss': 0,  # No stop loss for exit signal
                    'target': exit_price,
                    'confidence': 10.0,  # High confidence for exits
                    'quantity': position.get('quantity', 1),
                    'strategy': self.name,
                    'signal_type': 'POSITION_EXIT',
                    'exit_reason': reason,
                    'original_entry_price': entry_price,
                    'realized_pnl_pct': pnl_pct,
                    'metadata': {
                        'position_exit': True,
                        'exit_reason': reason,
                        'holding_time_hours': (datetime.now() - self.position_entry_times.get(symbol, datetime.now())).total_seconds() / 3600
                    }
                }
                
                # Store exit signal for orchestrator collection
                self.current_positions[f"{symbol}_EXIT"] = exit_signal
                
        except Exception as e:
            logger.error(f"Error exiting position for {symbol}: {e}")
    
    def record_position_entry(self, symbol: str, signal: Dict):
        """Record position entry for tracking and management"""
        try:
            # Store active position data
            self.active_positions[symbol] = {
                'entry_price': signal.get('entry_price', 0),
                'action': signal.get('action', 'BUY'),
                'stop_loss': signal.get('stop_loss', 0),
                'target': signal.get('target', 0),
                'confidence': signal.get('confidence', 0),
                'quantity': signal.get('quantity', 1),
                'strategy': self.name,
                'entry_time': datetime.now(),
                'timestamp': time_module.time()
            }
            
            # Store entry time for age tracking
            self.position_entry_times[symbol] = datetime.now()
            
            # Store strategy-specific metadata
            self.position_metadata[symbol] = signal.get('metadata', {})
            
            logger.info(f"📈 {self.name}: POSITION ENTERED {symbol} {signal.get('action')} at ₹{signal.get('entry_price', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Error recording position entry for {symbol}: {e}")
    
    def _is_symbol_scalping_cooldown_passed(self, symbol: str, cooldown_seconds: int = 30) -> bool:
        """Check if symbol-specific SCALPING cooldown has passed"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= cooldown_seconds
    
    def _update_symbol_cooldown(self, symbol: str):
        """Update symbol-specific cooldown timestamp"""
        if not hasattr(self, 'symbol_cooldowns'):
            self.symbol_cooldowns = {}
        self.symbol_cooldowns[symbol] = datetime.now()
        
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours - INTRADAY FOCUSED with square-off logic"""
        try:
            # Get current time in IST (same as orchestrator)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # NSE trading hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # 🚨 DAVID VS GOLIATH: Stop OPTIONS even EARLIER (avoid theta decay trap)
            # Market makers win in the last 2 hours via time decay
            # Exit before they feast on our premiums
            options_cutoff_time = time(13, 30)  # 1:30 PM - No new OPTIONS after this (was 2:00 PM)
            square_off_time = time(15, 0)  # 3:00 PM - Start square-off
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                logger.info(f"🚫 SAFETY: Trading blocked on weekend. Current day: {now.strftime('%A')}")
                return False
            
            is_trading_time = market_open <= current_time <= market_close
            is_square_off_time = square_off_time <= current_time <= market_close
            is_options_late = options_cutoff_time <= current_time <= market_close
            
            if not is_trading_time:
                logger.info(f"🚫 SAFETY: Trading blocked outside market hours. Current IST time: {current_time} "
                           f"(Market: {market_open} - {market_close})")
                return False
            elif is_square_off_time:
                logger.warning(f"⚠️ INTRADAY SQUARE-OFF: New positions blocked. Current time: {current_time} "
                              f"(Square-off starts: {square_off_time})")
                return False
            else:
            # Note: Options-specific cutoff check removed - handled by _is_options_trading_hours() instead
            # This method is for general trading hours check only
                return True  # Market is open for new positions
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFETY: If timezone check fails, default to False (safer)
            return False
    
    def _is_options_trading_hours(self) -> bool:
        """Check if within OPTIONS trading hours - stricter cutoff to avoid theta decay"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # NSE trading hours
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # 🚨 DAVID VS GOLIATH: Stop OPTIONS even EARLIER (avoid theta decay trap)
            options_cutoff_time = time(13, 30)  # 1:30 PM - No new OPTIONS after this
            
            # Check if weekend
            if now.weekday() >= 5:
                return False
            
            # Check if within options trading window (9:15 AM to 1:30 PM)
            is_within_hours = market_open <= current_time < options_cutoff_time
            
            if not is_within_hours and market_open <= current_time <= market_close:
                logger.warning(f"🚫 OPTIONS CUTOFF: No new options after {options_cutoff_time} (avoid theta decay)")
                return False
            elif not is_within_hours:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking options trading hours: {e}")
            return False
    
    async def _get_iv_rank(self, symbol: str) -> Optional[float]:
        """
        Get IV Rank for symbol (0-100 scale)
        IV Rank > 50 = expensive options (high IV relative to historical)
        IV Rank < 50 = cheap options (low IV relative to historical)
        """
        try:
            # Try to get IV from Zerodha option chain
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                # Get option chain with IV data
                option_chain = await orchestrator.zerodha_client.get_option_chain(symbol)
                if option_chain and 'analytics' in option_chain:
                    # Calculate simple IV rank from current IV vs typical range
                    current_iv = option_chain.get('analytics', {}).get('implied_volatility', 0)
                    if current_iv > 0:
                        # Simple approximation: IV below 20% = low, above 30% = high
                        # Convert to rank: (current - min) / (max - min) * 100
                        iv_min, iv_max = 15, 40  # Typical NIFTY/BANKNIFTY range
                        iv_rank = min(100, max(0, (current_iv - iv_min) / (iv_max - iv_min) * 100))
                        logger.info(f"📊 IV RANK: {symbol} IV={current_iv:.1f}%, Rank={iv_rank:.0f}%")
                        return iv_rank
            
            return None  # IV data not available
            
        except Exception as e:
            logger.debug(f"Error getting IV rank for {symbol}: {e}")
            return None
    
    async def _get_days_to_expiry(self, symbol: str) -> Optional[int]:
        """Get days to expiry for nearest options contract"""
        try:
            from datetime import datetime, timedelta
            import re
            
            # Try to parse expiry from options symbol format (e.g., NIFTY25DEC25850PE)
            # Pattern: NAME + YY + MMM + STRIKE + CE/PE
            match = re.match(r'([A-Z]+)(\d{2})([A-Z]{3})(\d+)(CE|PE)', symbol.upper())
            if match:
                year_short = int(match.group(2))
                month_str = match.group(3)
                
                # Convert month string to number
                months = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                         'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
                month_num = months.get(month_str, 0)
                
                if month_num > 0:
                    # Assume 20XX for year
                    year = 2000 + year_short
                    # Monthly expiry is last Thursday of month (approximate with day 28)
                    expiry_date = datetime(year, month_num, 28)
                    
                    # Adjust to actual last Thursday
                    while expiry_date.weekday() != 3:  # 3 = Thursday
                        expiry_date -= timedelta(days=1)
                    
                    days_remaining = (expiry_date - datetime.now()).days
                    logger.info(f"📅 EXPIRY CHECK: {symbol} expires in {days_remaining} days")
                    return max(0, days_remaining)
            
            # For underlying symbols, get nearest expiry from Zerodha
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                next_expiry = await orchestrator.zerodha_client.get_next_expiry(symbol)
                if next_expiry:
                    days_remaining = (next_expiry - datetime.now()).days
                    return max(0, days_remaining)
            
            return None  # Expiry data not available
            
        except Exception as e:
            logger.debug(f"Error getting days to expiry for {symbol}: {e}")
            return None
    
    async def _check_momentum_for_options(self, symbol: str, action: str, entry_price: float, metadata: Dict) -> Dict:
        """
        🎯 ALGORITHMIC FIX: Momentum Confirmation for Options Entry
        
        WHY MOMENTUM MATTERS FOR OPTIONS:
        - Options have time decay (theta) working against you
        - Need quick, strong moves to overcome theta + bid-ask spread
        - Weak momentum = premium erosion before direction move
        
        CONFIRMATION REQUIRES:
        1. RSI momentum aligned with direction (not overbought/oversold against you)
        2. Volume surge (>1.5x average) = institutional participation
        3. Price acceleration (recent candles trending)
        """
        try:
            result = {
                'confirmed': False,
                'reason': '',
                'details': '',
                'strength_score': 0  # 0-100
            }
            
            # Get market data
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator:
                # Can't check momentum, be conservative
                result['reason'] = 'No market data access'
                return result
            
            # Get RSI if available from metadata or calculate
            rsi = metadata.get('rsi', 50)
            volume_ratio = metadata.get('volume_ratio', 1.0)
            change_pct = metadata.get('change_percent', 0)
            intraday_change = metadata.get('intraday_change_pct', 0)
            
            strength_score = 0
            issues = []
            confirmations = []
            
            # ========== CHECK 1: RSI ALIGNMENT ==========
            # For BUY (calls): RSI should be 40-70 (momentum but not overbought)
            # For SELL (puts): RSI should be 30-60 (weakness but not oversold)
            if action.upper() == 'BUY':
                if 40 <= rsi <= 70:
                    strength_score += 30
                    confirmations.append(f"RSI={rsi:.0f} bullish")
                elif rsi > 70:
                    issues.append(f"RSI={rsi:.0f} overbought")
                elif rsi < 30:
                    issues.append(f"RSI={rsi:.0f} too weak for calls")
                else:
                    strength_score += 15  # Partial credit
            else:  # PUT
                if 30 <= rsi <= 60:
                    strength_score += 30
                    confirmations.append(f"RSI={rsi:.0f} bearish")
                elif rsi < 30:
                    issues.append(f"RSI={rsi:.0f} oversold")
                elif rsi > 70:
                    issues.append(f"RSI={rsi:.0f} too strong for puts")
                else:
                    strength_score += 15
            
            # ========== CHECK 2: VOLUME SURGE ==========
            # Need at least 1.5x average volume for options trade
            if volume_ratio >= 2.0:
                strength_score += 35
                confirmations.append(f"Volume surge {volume_ratio:.1f}x")
            elif volume_ratio >= 1.5:
                strength_score += 25
                confirmations.append(f"Good volume {volume_ratio:.1f}x")
            elif volume_ratio >= 1.0:
                strength_score += 10
            else:
                issues.append(f"Low volume {volume_ratio:.1f}x")
            
            # ========== CHECK 3: PRICE MOMENTUM ==========
            # Check if price is moving in our direction
            if action.upper() == 'BUY':
                if intraday_change >= 0.5:
                    strength_score += 35
                    confirmations.append(f"Intraday +{intraday_change:.1f}%")
                elif intraday_change >= 0:
                    strength_score += 15
                else:
                    issues.append(f"Negative intraday {intraday_change:.1f}%")
            else:  # PUT
                if intraday_change <= -0.5:
                    strength_score += 35
                    confirmations.append(f"Intraday {intraday_change:.1f}%")
                elif intraday_change <= 0:
                    strength_score += 15
                else:
                    issues.append(f"Positive intraday {intraday_change:.1f}%")
            
            # ========== FINAL DECISION ==========
            # Need at least 60 strength score for options
            result['strength_score'] = strength_score
            
            if strength_score >= 60:
                result['confirmed'] = True
                result['details'] = ' | '.join(confirmations)
            else:
                result['confirmed'] = False
                result['reason'] = ' + '.join(issues) if issues else f"Weak momentum (score={strength_score})"
            
            logger.info(f"📊 MOMENTUM CHECK: {symbol}")
            logger.info(f"   Score: {strength_score}/100, Confirmed: {result['confirmed']}")
            logger.info(f"   ✅ {', '.join(confirmations)}" if confirmations else "")
            logger.info(f"   ❌ {', '.join(issues)}" if issues else "")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in momentum check for {symbol}: {e}")
            return {'confirmed': False, 'reason': f'Error: {e}', 'strength_score': 0}
    
    async def _check_greeks_for_options(self, options_symbol: str, premium: float, underlying_price: float, option_type: str) -> Dict:
        """
        🎯 ALGORITHMIC FIX: Greeks-aware filtering for options
        
        WHY GREEKS MATTER:
        - Delta: How much option moves per ₹1 underlying move. Low delta = needs huge move
        - Theta: Daily time decay. High theta = losing money every day
        - Delta/Theta ratio tells if potential gain > expected time decay
        
        RULES:
        1. Delta should be 0.25-0.55 (not too OTM, not too ITM)
        2. Delta/Theta ratio should be > 0.1 (can overcome daily decay)
        3. Premium shouldn't be too cheap (< ₹10) or too expensive (> 3% of underlying)
        """
        try:
            result = {
                'favorable': True,  # Default optimistic if we can't check
                'reason': '',
                'details': '',
                'estimated_delta': 0,
                'estimated_theta': 0
            }
            
            # ========== PREMIUM SANITY CHECKS ==========
            # Too cheap = too far OTM, will decay to zero
            if premium < 5:
                result['favorable'] = False
                result['reason'] = f'Premium ₹{premium:.1f} too cheap (< ₹5) - likely worthless'
                return result
            
            # Too expensive = losing too much if wrong
            premium_pct = (premium / underlying_price) * 100
            if premium_pct > 5:
                result['favorable'] = False
                result['reason'] = f'Premium {premium_pct:.1f}% of underlying is too expensive (> 5%)'
                return result
            
            # ========== ESTIMATE GREEKS (if actual Greeks not available) ==========
            # Simple moneyness-based delta estimate
            # ATM ≈ 0.5 delta, OTM ≈ 0.3-0.4, far OTM < 0.2
            
            # Calculate how far OTM the option is
            # For CE: (strike - underlying) / underlying * 100
            # For PE: (underlying - strike) / underlying * 100
            try:
                import re
                # Extract strike from symbol like NIFTY25DEC24500CE
                match = re.search(r'(\d{4,6})(CE|PE)$', options_symbol)
                if match:
                    strike = int(match.group(1))
                    
                    if option_type == 'CE':
                        otm_pct = ((strike - underlying_price) / underlying_price) * 100
                    else:  # PE
                        otm_pct = ((underlying_price - strike) / underlying_price) * 100
                    
                    # Estimate delta based on OTM percentage
                    if otm_pct <= 0:  # ITM
                        estimated_delta = 0.55 + (abs(otm_pct) * 0.01)  # Deeper ITM = higher delta
                        estimated_delta = min(0.9, estimated_delta)
                    elif otm_pct <= 1:  # Near ATM
                        estimated_delta = 0.45
                    elif otm_pct <= 2:  # Slightly OTM
                        estimated_delta = 0.35
                    elif otm_pct <= 3:  # OTM
                        estimated_delta = 0.25
                    elif otm_pct <= 5:  # Far OTM
                        estimated_delta = 0.15
                    else:  # Very far OTM
                        estimated_delta = 0.08
                    
                    result['estimated_delta'] = estimated_delta
                    
                    # Delta too low = needs huge move
                    if estimated_delta < 0.15:
                        result['favorable'] = False
                        result['reason'] = f'Delta ~{estimated_delta:.2f} too low ({otm_pct:.1f}% OTM) - needs unrealistic move'
                        return result
                    
                    # Estimate theta (rough: 0.5-2% of premium per day for weekly options)
                    # Higher premium = higher absolute theta but lower relative decay
                    estimated_theta = premium * 0.015  # 1.5% daily decay estimate
                    result['estimated_theta'] = estimated_theta
                    
                    # Check delta/theta ratio
                    # Good options: delta * expected_move > theta
                    # Expected move in NIFTY = 0.5-1% per day
                    expected_daily_move = underlying_price * 0.007  # 0.7% expected move
                    daily_gain_potential = expected_daily_move * estimated_delta
                    
                    if daily_gain_potential < estimated_theta * 1.5:
                        result['favorable'] = False
                        result['reason'] = f'Theta decay (₹{estimated_theta:.1f}/day) exceeds potential gain (₹{daily_gain_potential:.1f})'
                        return result
                    
                    result['details'] = f"Delta~{estimated_delta:.2f}, Theta~₹{estimated_theta:.1f}/day, {otm_pct:.1f}% OTM"
                    
            except Exception as calc_err:
                logger.debug(f"Greeks calculation error: {calc_err}")
            
            # If we reach here, Greeks are acceptable
            result['favorable'] = True
            return result
            
        except Exception as e:
            logger.debug(f"Error checking Greeks for {options_symbol}: {e}")
            return {'favorable': True, 'reason': '', 'details': 'Greeks check skipped'}
    
    def _check_trend_strength_for_options(self, symbol: str, action: str, metadata: Dict) -> Dict:
        """
        🎯 ALGORITHMIC FIX: Only trade options in strong trending markets
        
        WHY TREND STRENGTH MATTERS:
        - Options LOSE money in sideways markets (theta decay)
        - Need strong directional trend to overcome time decay
        - Choppy markets = whipsaw = options losses
        
        CHECKS:
        1. ADX > 20 (trend strength indicator)
        2. Moving averages aligned (price > SMA20 > SMA50 for bullish)
        3. No recent reversals (consistent direction)
        4. Day change and intraday change in same direction
        """
        try:
            result = {
                'strong_trend': False,
                'reason': '',
                'details': '',
                'trend_score': 0
            }
            
            trend_score = 0
            confirmations = []
            issues = []
            
            # ========== CHECK 1: MTF ALIGNMENT ==========
            # Multi-timeframe alignment from metadata
            mtf_aligned = metadata.get('mtf_aligned', False)
            mtf_direction = metadata.get('mtf_direction', 'NEUTRAL')
            
            if mtf_aligned:
                trend_score += 30
                confirmations.append(f"MTF aligned {mtf_direction}")
            else:
                issues.append("MTF not aligned")
            
            # ========== CHECK 2: PRICE VS MOVING AVERAGES ==========
            # Check if price is above/below key MAs
            ma_signal = metadata.get('ma_signal', 'NEUTRAL')
            
            if action.upper() == 'BUY' and ma_signal == 'BULLISH':
                trend_score += 25
                confirmations.append("Price above MAs")
            elif action.upper() == 'SELL' and ma_signal == 'BEARISH':
                trend_score += 25
                confirmations.append("Price below MAs")
            elif ma_signal == 'NEUTRAL':
                issues.append("MAs neutral/mixed")
            else:
                issues.append(f"MAs against direction ({ma_signal})")
            
            # ========== CHECK 3: DAY AND INTRADAY DIRECTION ALIGNMENT ==========
            day_change = metadata.get('change_percent', 0)
            intraday_change = metadata.get('intraday_change_pct', 0)
            
            if action.upper() == 'BUY':
                if day_change > 0 and intraday_change > 0:
                    trend_score += 25
                    confirmations.append(f"Day +{day_change:.1f}%, Intra +{intraday_change:.1f}%")
                elif day_change < 0 and intraday_change < 0:
                    issues.append("Both negative for CALL")
                else:
                    issues.append("Mixed day/intraday for CALL")
            else:  # PUT
                if day_change < 0 and intraday_change < 0:
                    trend_score += 25
                    confirmations.append(f"Day {day_change:.1f}%, Intra {intraday_change:.1f}%")
                elif day_change > 0 and intraday_change > 0:
                    issues.append("Both positive for PUT")
                else:
                    issues.append("Mixed day/intraday for PUT")
            
            # ========== CHECK 4: VOLATILITY REGIME ==========
            # Medium volatility is best for options (too low = no moves, too high = expensive)
            vix = metadata.get('vix', 15)  # Default 15 if not available
            
            if 12 <= vix <= 25:
                trend_score += 20
                confirmations.append(f"VIX {vix:.0f} optimal")
            elif vix < 12:
                issues.append(f"VIX {vix:.0f} too low (no moves)")
            elif vix > 25:
                issues.append(f"VIX {vix:.0f} high (expensive)")
            
            # ========== FINAL DECISION ==========
            result['trend_score'] = trend_score
            
            # Need at least 50 score for options
            if trend_score >= 50:
                result['strong_trend'] = True
                result['details'] = ' | '.join(confirmations)
            else:
                result['strong_trend'] = False
                result['reason'] = ' + '.join(issues) if issues else f"Weak trend (score={trend_score})"
            
            logger.info(f"📊 TREND CHECK: {symbol}")
            logger.info(f"   Score: {trend_score}/100, Strong: {result['strong_trend']}")
            if confirmations:
                logger.info(f"   ✅ {', '.join(confirmations)}")
            if issues:
                logger.info(f"   ❌ {', '.join(issues)}")
            
            return result
            
        except Exception as e:
            logger.debug(f"Error in trend check for {symbol}: {e}")
            # Default to allowing the trade if check fails
            return {'strong_trend': True, 'reason': '', 'details': 'Trend check skipped'}
    
    def _is_intraday_square_off_time(self) -> bool:
        """Check if it's time to square off intraday positions"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Square-off window: 3:00 PM to 3:30 PM
            square_off_start = time(15, 0)
            market_close = time(15, 30)
            
            return square_off_start <= current_time <= market_close
            
        except Exception as e:
            logger.error(f"Error checking square-off time: {e}")
            return False
    
    def _is_opening_gap_gate_active(self, market_data: Dict, gap_threshold: float = 0.8) -> bool:
        """Opening gate: block counter-gap trades in first minutes after large gap"""
        try:
            # Determine time phase from orchestrator if available
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            time_phase = getattr(getattr(orchestrator, 'market_bias', None), 'current_bias', None)
            phase = getattr(time_phase, 'time_phase', 'UNKNOWN') if time_phase else 'UNKNOWN'

            if phase not in ('OPENING', 'MORNING'):
                return False

            # Use index data for gap (NIFTY-I preferred)
            index_data = market_data.get('NIFTY-I') or market_data.get('NIFTY') or {}
            open_price = float(index_data.get('open', 0) or 0)
            prev_close = float(index_data.get('prev_close', 0) or 0)
            if open_price > 0 and prev_close > 0:
                gap_pct = ((open_price - prev_close) / prev_close) * 100.0
                return abs(gap_pct) >= gap_threshold
            return False
        except Exception:
            return False

    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """Calculate True Range - the foundation of proper ATR calculation"""
        try:
            if prev_close <= 0:
                return high - low  # First calculation or invalid previous close
            
            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            range1 = high - low
            range2 = abs(high - prev_close)
            range3 = abs(low - prev_close)
            
            return max(range1, range2, range3)
            
        except Exception as e:
            logger.error(f"Error calculating True Range: {e}")
            return high - low if high > low else 0.01  # Fallback
    
    def calculate_atr(self, symbol: str, current_high: float, current_low: float, 
                     current_close: float, period: int = 14) -> float:
        """
        PROFESSIONAL GARCH-ENHANCED ATR CALCULATION
        DAVID VS GOLIATH ADVANTAGE: Superior volatility estimation using GARCH models
        """
        try:
            # Store current data
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            # Add current data point
            data_point = {
                'high': current_high,
                'low': current_low,
                'close': current_close,
                'timestamp': datetime.now()
            }
            
            self.historical_data[symbol].append(data_point)
            
            # Trim history if needed
            if len(self.historical_data[symbol]) > self.max_history:
                self.historical_data[symbol].pop(0)
            
            history = self.historical_data[symbol]
            if len(history) < 2:
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # PROFESSIONAL GARCH-ENHANCED ATR
            if len(history) >= 10:  # Need sufficient data for GARCH
                # 🔥 PRIORITY: Use Zerodha daily GARCH if available (cached)
                if symbol in self._garch_cache:
                    cached = self._garch_cache[symbol]['data']
                    garch_atr = cached['garch_atr']
                    traditional_atr = cached['traditional_atr']
                    data_source = cached['data_source']
                else:
                    # Fallback to tick-based GARCH (less accurate but available)
                    prices = np.array([h['close'] for h in history])
                    garch_atr = ProfessionalMathFoundation.garch_atr(prices, period)
                    traditional_atr = self._calculate_traditional_atr_internal(history, period)
                    data_source = 'tick_based'
                
                # ENSEMBLE ATR (70% GARCH, 30% traditional)
                ensemble_atr = (garch_atr * 0.7) + (traditional_atr * 0.3)
                
                # PROFESSIONAL VALIDATION
                atr_percentage = ensemble_atr / current_close if current_close > 0 else 0.02
                
                # Adaptive bounds based on market conditions
                if atr_percentage < 0.003:  # Too conservative
                    ensemble_atr = current_close * 0.008
                elif atr_percentage > 0.08:  # Too aggressive
                    ensemble_atr = current_close * 0.04
                
                # 🚨 FIX: Add INFO logging for GARCH visibility (every 20th calculation per symbol)
                if not hasattr(self, '_garch_log_counter'):
                    self._garch_log_counter = {}
                self._garch_log_counter[symbol] = self._garch_log_counter.get(symbol, 0) + 1
                if self._garch_log_counter[symbol] % 20 == 1:
                    source_icon = "📈" if data_source == 'zerodha_daily' else "⚡"
                    logger.info(f"📊 GARCH ATR: {symbol} GARCH=₹{garch_atr:.2f} Trad=₹{traditional_atr:.2f} Ensemble=₹{ensemble_atr:.2f} ({atr_percentage*100:.2f}%) {source_icon} {data_source}")
                
                # Update performance attribution
                self._update_performance_attribution(symbol, ensemble_atr, garch_atr, traditional_atr)
                
                return max(ensemble_atr, 1.0)
            
            else:
                # Fallback to traditional ATR for insufficient data
                return self._calculate_traditional_atr_internal(history, period)
                
        except Exception as e:
            logger.error(f"Professional ATR calculation failed for {symbol}: {e}")
            return current_high - current_low if current_high > current_low else current_close * 0.01
    
    def _calculate_traditional_atr_internal(self, history: List[Dict], period: int) -> float:
        """Traditional ATR calculation for ensemble"""
        try:
            true_ranges = []
            for i in range(1, len(history)):
                prev_close = history[i-1]['close']
                current_data = history[i]
                tr = self.calculate_true_range(
                    current_data['high'], 
                    current_data['low'], 
                    prev_close
                )
                true_ranges.append(tr)
            
            if len(true_ranges) == 0:
                return 0.02
            
            atr_period = min(period, len(true_ranges))
            recent_trs = true_ranges[-atr_period:]
            atr = np.mean(recent_trs)
            
            # Ensure minimum ATR (0.1% of price) and reasonable maximum (10% of price)
            # Use last candle's close from history for reference price
            last_close = history[-1]['close'] if history else 100.0
            min_atr = last_close * 0.001
            max_atr = last_close * 0.1
            
            return max(min_atr, min(atr, max_atr))
            
        except Exception as e:
            logger.error(f"Traditional ATR calculation failed: {e}")
            return 0.02
    
    async def calculate_garch_from_zerodha(self, symbol: str, period: int = 30) -> Dict:
        """
        🔥 INTRADAY GARCH CALCULATION using Zerodha 5-minute candles
        
        For INTRADAY trading, we use 5-minute candles (last 2-3 days)
        instead of daily candles. This gives us intraday volatility patterns.
        
        Returns: {
            'garch_volatility': float,  # Intraday volatility (scaled)
            'garch_atr': float,         # GARCH-enhanced intraday ATR
            'traditional_atr': float,   # For comparison
            'current_regime': str,      # 'HIGH', 'NORMAL', 'LOW'
            'data_source': str          # 'zerodha_5min' or 'fallback'
        }
        """
        try:
            from datetime import datetime, timedelta
            
            # Check cache first (shorter expiry for intraday: 30 minutes)
            if symbol in self._garch_cache:
                cache_entry = self._garch_cache[symbol]
                cache_age = (datetime.now() - cache_entry['updated_at']).total_seconds() / 60  # Minutes
                if cache_age < 30:  # 30 minute cache for intraday
                    return cache_entry['data']
            
            # Fetch intraday candles from Zerodha
            zerodha_client = None
            if hasattr(self, 'broker_client') and self.broker_client:
                zerodha_client = self.broker_client
            else:
                try:
                    from brokers.zerodha import zerodha_client as zc
                    zerodha_client = zc
                except:
                    pass
            
            if not zerodha_client:
                logger.debug(f"No Zerodha client available for {symbol} GARCH")
                return self._fallback_garch(symbol)
            
            # 🔥 INTRADAY: Get 5-minute candles for last 3 days
            # This gives us ~225 candles (75 per day x 3 days)
            candles = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='5minute',
                from_date=datetime.now() - timedelta(days=3)
            )
            
            if not candles or len(candles) < 50:
                # Fallback to 15-minute candles
                candles = await zerodha_client.get_historical_data(
                    symbol=symbol,
                    interval='15minute',
                    from_date=datetime.now() - timedelta(days=5)
                )
            
            if not candles or len(candles) < 30:
                logger.debug(f"Insufficient intraday data for {symbol}: {len(candles) if candles else 0} candles")
                return self._fallback_garch(symbol)
            
            # Extract OHLC
            prices = np.array([c['close'] for c in candles])
            highs = np.array([c['high'] for c in candles])
            lows = np.array([c['low'] for c in candles])
            
            # Calculate intraday returns
            returns = np.diff(prices) / prices[:-1]
            
            # GARCH(1,1) with parameters tuned for INTRADAY data
            # Higher alpha for faster reaction, lower beta for less persistence
            alpha = 0.15  # Higher for intraday reactivity
            beta = 0.80   # Lower for intraday (less persistent)
            omega = np.var(returns) * (1 - alpha - beta)
            
            # GARCH recursion
            n = len(returns)
            variance = np.zeros(n)
            variance[0] = np.var(returns[:min(20, n)])
            
            for t in range(1, n):
                variance[t] = omega + alpha * (returns[t-1] ** 2) + beta * variance[t-1]
            
            # Intraday volatility (scale to daily equivalent for comparison)
            # 5-min candles: ~75 per day, so multiply by sqrt(75)
            candles_per_day = 75  # Approx 5-min candles in trading day
            garch_volatility = np.sqrt(variance[-1]) * np.sqrt(candles_per_day)
            
            # GARCH-enhanced intraday ATR
            current_price = prices[-1]
            garch_atr = np.sqrt(variance[-1]) * current_price * 2  # Intraday ATR
            
            # Traditional ATR from candles
            true_ranges = []
            for i in range(1, len(candles)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - prices[i-1]),
                    abs(lows[i] - prices[i-1])
                )
                true_ranges.append(tr)
            # Use last 14 candles for traditional ATR (like 14-period ATR)
            traditional_atr = np.mean(true_ranges[-14:]) if len(true_ranges) >= 14 else np.mean(true_ranges)
            
            # Volatility regime detection (relative to recent history)
            recent_var = variance[-20:] if len(variance) >= 20 else variance
            avg_vol = np.mean(np.sqrt(recent_var))
            current_vol = np.sqrt(variance[-1])
            
            if current_vol > avg_vol * 1.5:
                regime = 'HIGH'
            elif current_vol < avg_vol * 0.6:
                regime = 'LOW'
            else:
                regime = 'NORMAL'
            
            result = {
                'garch_volatility': float(garch_volatility),
                'garch_atr': float(garch_atr),
                'traditional_atr': float(traditional_atr),
                'current_regime': regime,
                'data_source': 'zerodha_5min',
                'candle_count': len(candles)
            }
            
            # Cache the result (30 min expiry for intraday)
            self._garch_cache[symbol] = {
                'data': result,
                'updated_at': datetime.now()
            }
            
            # Log occasionally (not every call)
            if not hasattr(self, '_garch_log_count'):
                self._garch_log_count = {}
            self._garch_log_count[symbol] = self._garch_log_count.get(symbol, 0) + 1
            if self._garch_log_count[symbol] % 50 == 1:
                logger.info(f"📊 INTRADAY GARCH: {symbol} Vol={garch_volatility:.1%} ATR=₹{garch_atr:.2f} "
                           f"Trad=₹{traditional_atr:.2f} Regime={regime} ({len(candles)} 5min candles)")
            
            return result
            
        except Exception as e:
            logger.debug(f"Zerodha GARCH failed for {symbol}: {e}")
            return self._fallback_garch(symbol)
    
    async def prefetch_garch_for_symbols(self, symbols: List[str], max_concurrent: int = 5):
        """
        🔥 PREFETCH GARCH data for multiple symbols efficiently
        
        Call this at the start of generate_signals to warm the cache.
        Only fetches symbols that aren't already cached.
        """
        import asyncio
        from datetime import datetime
        
        # Filter symbols that need fetching
        symbols_to_fetch = []
        for symbol in symbols:
            if symbol in self._garch_cache:
                cache_age_minutes = (datetime.now() - self._garch_cache[symbol]['updated_at']).total_seconds() / 60
                if cache_age_minutes < self._garch_cache_expiry_minutes:
                    continue  # Already cached and fresh
            symbols_to_fetch.append(symbol)
        
        if not symbols_to_fetch:
            return  # All cached
        
        # Fetch in batches to avoid overwhelming Zerodha API
        logger.debug(f"📊 GARCH PREFETCH: {len(symbols_to_fetch)} symbols need daily data")
        
        for i in range(0, len(symbols_to_fetch), max_concurrent):
            batch = symbols_to_fetch[i:i+max_concurrent]
            tasks = [self.calculate_garch_from_zerodha(sym) for sym in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"📊 GARCH PREFETCH COMPLETE: {len(symbols_to_fetch)} symbols cached")
    
    def _fallback_garch(self, symbol: str) -> Dict:
        """Fallback GARCH when Zerodha data unavailable"""
        # Use tick history if available
        if symbol in self.historical_data and len(self.historical_data[symbol]) >= 10:
            prices = np.array([h['close'] for h in self.historical_data[symbol]])
            # Rough estimate - scale up since ticks have less variance than daily
            simple_vol = np.std(np.diff(prices) / prices[:-1]) * np.sqrt(252) * 5  # Scale factor
            simple_atr = np.std(np.diff(prices)) * 2
            return {
                'garch_volatility': float(simple_vol),
                'garch_atr': float(simple_atr),
                'traditional_atr': float(simple_atr),
                'current_regime': 'NORMAL',
                'data_source': 'tick_fallback',
                'candle_count': 0
            }
        
        return {
            'garch_volatility': 0.25,  # 25% default
            'garch_atr': 0.02,
            'traditional_atr': 0.02,
            'current_regime': 'NORMAL',
            'data_source': 'default',
            'candle_count': 0
        }
    
    def _update_performance_attribution(self, symbol: str, ensemble_atr: float, 
                                      garch_atr: float, traditional_atr: float):
        """Update performance attribution for professional analysis"""
        try:
            if not hasattr(self, 'atr_performance'):
                self.atr_performance = {}
            
            if symbol not in self.atr_performance:
                self.atr_performance[symbol] = {
                    'ensemble_history': [],
                    'garch_history': [],
                    'traditional_history': [],
                    'accuracy_scores': []
                }
            
            perf = self.atr_performance[symbol]
            perf['ensemble_history'].append(ensemble_atr)
            perf['garch_history'].append(garch_atr)
            perf['traditional_history'].append(traditional_atr)
            
            # Keep only recent history (last 50 observations)
            for key in ['ensemble_history', 'garch_history', 'traditional_history']:
                if len(perf[key]) > 50:
                    perf[key].pop(0)
            
            # Update strategy-level performance attribution
            if len(self.strategy_returns) > 0:
                recent_returns = np.array(self.strategy_returns[-20:])  # Last 20 trades
                
                # Update professional metrics
                self.performance_attribution['sharpe_ratio'] = ProfessionalMathFoundation.sharpe_ratio(recent_returns)
                self.performance_attribution['var_95'] = ProfessionalMathFoundation.var_calculation(recent_returns)
                self.performance_attribution['statistical_significance'] = ProfessionalMathFoundation.statistical_significance_test(recent_returns)
                
                # Calculate win rate and average win/loss
                wins = recent_returns[recent_returns > 0]
                losses = recent_returns[recent_returns < 0]
                
                self.performance_attribution['win_rate'] = len(wins) / len(recent_returns) if len(recent_returns) > 0 else 0.0
                self.performance_attribution['avg_win'] = np.mean(wins) if len(wins) > 0 else 0.0
                self.performance_attribution['avg_loss'] = np.mean(losses) if len(losses) > 0 else 0.0
                
                # Calculate Kelly optimal size
                if len(wins) > 0 and len(losses) > 0:
                    self.performance_attribution['kelly_optimal_size'] = ProfessionalMathFoundation.kelly_position_size(
                        self.performance_attribution['win_rate'],
                        abs(self.performance_attribution['avg_win']),
                        abs(self.performance_attribution['avg_loss']),
                        100000  # Assume ₹1L capital for percentage calculation
                    ) / 100000  # Convert back to fraction
                    
        except Exception as e:
            logger.error(f"Performance attribution update failed: {e}")
    
    def get_professional_position_size(self, symbol: str, signal_confidence: float, 
                                     current_price: float, capital: float) -> float:
        """
        PROFESSIONAL POSITION SIZING using Kelly Criterion
        COMPETITIVE ADVANTAGE: Optimal sizing vs fixed percentages
        """
        try:
            # Base position size from Kelly criterion
            kelly_size = self.performance_attribution.get('kelly_optimal_size', 0.02)
            
            # Adjust based on signal confidence
            confidence_multiplier = min(signal_confidence / 10.0, 1.0)  # Normalize to 0-1
            
            # Adjust based on current volatility (ATR)
            if symbol in self.historical_data and len(self.historical_data[symbol]) > 5:
                recent_data = self.historical_data[symbol][-1]
                atr = self.calculate_atr(symbol, recent_data['high'], recent_data['low'], recent_data['close'])
                volatility_adjustment = min(1.0, 0.02 / (atr / current_price))  # Reduce size for high volatility
            else:
                volatility_adjustment = 1.0
            
            # Professional position sizing formula
            optimal_size = kelly_size * confidence_multiplier * volatility_adjustment
            
            # Safety bounds
            optimal_size = max(0.005, min(optimal_size, 0.05))  # Between 0.5% and 5%
            
            position_value = optimal_size * capital
            
            logger.debug(f"🎯 PROFESSIONAL SIZING: {symbol} kelly={kelly_size:.3f} "
                        f"confidence={confidence_multiplier:.2f} vol_adj={volatility_adjustment:.2f} "
                        f"final={optimal_size:.3f} value=₹{position_value:,.0f}")
            
            return position_value
            
        except Exception as e:
            logger.error(f"Professional position sizing failed for {symbol}: {e}")
            return capital * 0.02  # 2% fallback
    
    def calculate_dynamic_stop_loss(self, entry_price: float, atr: float, action: str, 
                                   multiplier: float = 2.0, min_percent: float = 0.5, 
                                   max_percent: float = 5.0, available_capital: float = None) -> float:
        """Calculate dynamic stop loss with MAXIMUM 1% RISK PER TRADE constraint"""
        try:
            # Get available capital for 1% risk calculation
            if available_capital is None:
                available_capital = self._get_available_capital()
            
            # MAXIMUM 1% RISK PER TRADE CONSTRAINT
            max_risk_amount = available_capital * 0.01  # 1% of capital
            
            # Calculate ATR-based stop loss distance
            atr_distance = atr * multiplier
            
            # Convert to percentage
            atr_percent = (atr_distance / entry_price) * 100
            
            # CRITICAL: Ensure stop loss doesn't exceed 1% risk per trade
            # Estimate typical trade size to validate risk
            typical_trade_value = min(available_capital * 0.25, 50000)  # 25% capital or ₹50k max
            typical_quantity = typical_trade_value / entry_price
            potential_risk = atr_distance * typical_quantity
            
            # If ATR-based risk exceeds 1%, constrain it
            if potential_risk > max_risk_amount:
                # Recalculate stop distance to exactly match 1% risk
                constrained_distance = max_risk_amount / typical_quantity
                constrained_percent = (constrained_distance / entry_price) * 100
                logger.info(f"🛡️ 1% RISK CONSTRAINT: {action} @ {entry_price:.2f} - ATR stop {atr_percent:.2f}% → {constrained_percent:.2f}%")
                bounded_percent = constrained_percent
            else:
                # Apply SCALPING-OPTIMIZED bounds (tighter than original)
                bounded_percent = max(min_percent, min(atr_percent, max_percent))
            
            bounded_distance = (bounded_percent / 100) * entry_price
            
            # Calculate stop loss based on action
            if action.upper() == 'BUY':
                stop_loss = entry_price - bounded_distance
            else:  # SELL
                stop_loss = entry_price + bounded_distance
            
            logger.info(f"🎯 DYNAMIC STOP: {action} @ {entry_price:.2f} → SL @ {stop_loss:.2f} "
                       f"(Risk: {bounded_percent:.2f}%, Max Risk: ₹{max_risk_amount:.0f})")
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            # Fallback to percentage-based stop loss
            fallback_percent = 0.5  # 0.5% fallback for scalping
            if action.upper() == 'BUY':
                return entry_price * (1 - fallback_percent / 100)
            else:
                return entry_price * (1 + fallback_percent / 100)
    
    def calculate_rsi_divergence(self, symbol: str, prices: List[float], rsi_values: List[float]) -> Optional[str]:
        """
        🎯 CODE ENHANCEMENT: Detect RSI divergence for high-probability reversals
        RSI divergence is one of the most reliable reversal signals
        
        Returns: 'bullish', 'bearish', or None
        """
        try:
            if len(prices) < 14 or len(rsi_values) < 14:
                return None
            
            # Find recent peaks and troughs
            recent_prices = prices[-14:]
            recent_rsi = rsi_values[-14:]
            
            # Bullish divergence: Price makes lower low, RSI makes higher low
            price_low_1 = min(recent_prices[:7])
            price_low_2 = min(recent_prices[7:])
            
            # Find corresponding RSI values
            price_low_1_idx = recent_prices[:7].index(price_low_1)
            price_low_2_idx = 7 + recent_prices[7:].index(price_low_2)
            
            rsi_at_low_1 = recent_rsi[price_low_1_idx]
            rsi_at_low_2 = recent_rsi[price_low_2_idx]
            
            # Bullish divergence detected
            # 🔥 FIX: Require MINIMUM 2.0 RSI points difference to avoid false signals
            # AXISBANK bug: 0.1 RSI diff (32.5→32.6) triggered false reversal
            MIN_RSI_DIVERGENCE = 2.0
            rsi_diff = rsi_at_low_2 - rsi_at_low_1
            if price_low_2 < price_low_1 and rsi_diff >= MIN_RSI_DIVERGENCE:
                logger.info(f"📈 BULLISH DIVERGENCE detected for {symbol}: Price {price_low_1:.2f}→{price_low_2:.2f}, RSI {rsi_at_low_1:.1f}→{rsi_at_low_2:.1f} (diff: {rsi_diff:.1f})")
                return 'bullish'
            elif price_low_2 < price_low_1 and rsi_at_low_2 > rsi_at_low_1:
                logger.debug(f"⚠️ Weak bullish divergence ignored for {symbol}: RSI diff {rsi_diff:.1f} < {MIN_RSI_DIVERGENCE}")
            
            # Bearish divergence: Price makes higher high, RSI makes lower high
            price_high_1 = max(recent_prices[:7])
            price_high_2 = max(recent_prices[7:])
            
            price_high_1_idx = recent_prices[:7].index(price_high_1)
            price_high_2_idx = 7 + recent_prices[7:].index(price_high_2)
            
            rsi_at_high_1 = recent_rsi[price_high_1_idx]
            rsi_at_high_2 = recent_rsi[price_high_2_idx]
            
            # Bearish divergence detected
            # 🔥 FIX: Require MINIMUM 2.0 RSI points difference to avoid false signals
            rsi_diff_bear = rsi_at_high_1 - rsi_at_high_2
            if price_high_2 > price_high_1 and rsi_diff_bear >= MIN_RSI_DIVERGENCE:
                logger.info(f"📉 BEARISH DIVERGENCE detected for {symbol}: Price {price_high_1:.2f}→{price_high_2:.2f}, RSI {rsi_at_high_1:.1f}→{rsi_at_high_2:.1f} (diff: {rsi_diff_bear:.1f})")
                return 'bearish'
            elif price_high_2 > price_high_1 and rsi_at_high_2 < rsi_at_high_1:
                logger.debug(f"⚠️ Weak bearish divergence ignored for {symbol}: RSI diff {rsi_diff_bear:.1f} < {MIN_RSI_DIVERGENCE}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating RSI divergence: {e}")
            return None
    
    def detect_bollinger_squeeze(self, symbol: str, prices: List[float], period: int = 20, 
                                   highs: List[float] = None, lows: List[float] = None,
                                   volumes: List[float] = None) -> Dict:
        """
        🎯 TTM SQUEEZE INDICATOR - Professional Implementation
        
        The TTM Squeeze detects when Bollinger Bands contract INSIDE Keltner Channels,
        indicating a period of low volatility that typically precedes a large move.
        
        Components:
        1. Bollinger Bands (20-period, 2 std dev)
        2. Keltner Channels (20-period, 1.5 ATR)
        3. Momentum Oscillator (for breakout direction)
        4. Volume confirmation
        5. Historical squeeze duration tracking
        
        Returns: {
            'squeezing': bool,           # True = BB inside KC (squeeze ON)
            'breakout_direction': str,   # 'up', 'down', or None
            'squeeze_intensity': float,  # 0-1, how tight the squeeze
            'bandwidth': float,          # BB bandwidth as % of price
            'momentum': float,           # Momentum oscillator value
            'squeeze_bars': int,         # How many bars in squeeze
            'keltner_squeeze': bool,     # True TTM squeeze (BB inside KC)
            'volume_confirms': bool,     # Volume expanding on breakout
            'squeeze_quality': str       # 'HIGH', 'MEDIUM', 'LOW'
        }
        """
        try:
            min_period = max(period, 20)
            if len(prices) < min_period:
                return self._empty_squeeze_result()
            
            prices_arr = np.array(prices[-min_period*2:] if len(prices) >= min_period*2 else prices)
            current_price = prices[-1]
            
            # ============= CALCULATE ATR (True Range) =============
            if highs and lows and len(highs) >= min_period and len(lows) >= min_period:
                highs_arr = np.array(highs[-min_period:])
                lows_arr = np.array(lows[-min_period:])
                closes = prices_arr[-min_period:]
                
                # True Range = max(H-L, |H-Prev_C|, |L-Prev_C|)
                tr = np.zeros(min_period - 1)
                for i in range(1, min_period):
                    hl = highs_arr[i] - lows_arr[i]
                    hc = abs(highs_arr[i] - closes[i-1])
                    lc = abs(lows_arr[i] - closes[i-1])
                    tr[i-1] = max(hl, hc, lc)
                atr = np.mean(tr) if len(tr) > 0 else 0
            else:
                # Fallback: Estimate ATR from price changes
                price_changes = np.abs(np.diff(prices_arr[-min_period:]))
                atr = np.mean(price_changes) * 1.5 if len(price_changes) > 0 else 0
            
            # ============= BOLLINGER BANDS =============
            recent_prices = prices_arr[-period:]
            sma = np.mean(recent_prices)
            std = np.std(recent_prices)
            
            if std < 0.0001 or sma <= 0 or atr < 0.0001:
                return self._empty_squeeze_result()
            
            bb_mult = 2.0  # Standard 2 std dev
            bb_upper = sma + (bb_mult * std)
            bb_lower = sma - (bb_mult * std)
            bandwidth = (bb_upper - bb_lower) / sma
            
            # ============= KELTNER CHANNELS =============
            kc_mult = 1.5  # Standard 1.5 ATR
            kc_upper = sma + (kc_mult * atr)
            kc_lower = sma - (kc_mult * atr)
            kc_width = (kc_upper - kc_lower) / sma if sma > 0 else 0
            
            # ============= TTM SQUEEZE DETECTION =============
            # TRUE SQUEEZE: Bollinger Bands are INSIDE Keltner Channels
            keltner_squeeze = (bb_lower > kc_lower) and (bb_upper < kc_upper)
            
            # Also check if BB is significantly narrower than KC
            bb_kc_ratio = bandwidth / kc_width if kc_width > 0 else 1.0
            squeeze_intensity = max(0, 1 - bb_kc_ratio)  # Higher = tighter squeeze
            
            # Fallback bandwidth-based squeeze (for intraday with limited data)
            # Adaptive thresholds based on price level
            if current_price > 1000:
                squeeze_threshold = 0.015  # 1.5% for high-priced stocks
            elif current_price > 100:
                squeeze_threshold = 0.02   # 2% for mid-priced stocks
            else:
                squeeze_threshold = 0.025  # 2.5% for low-priced stocks
            
            bandwidth_squeeze = bandwidth < squeeze_threshold
            
            # Combined squeeze detection
            is_squeezing = keltner_squeeze or (bandwidth_squeeze and squeeze_intensity > 0.4)
            
            # ============= HISTORICAL SQUEEZE TRACKING =============
            # Check how long we've been in a squeeze (more bars = bigger move coming)
            squeeze_bars = 0
            if len(prices) >= period * 3:
                for i in range(1, min(period, len(prices) - period)):
                    hist_prices = prices[-(period+i):-i]
                    hist_sma = np.mean(hist_prices)
                    hist_std = np.std(hist_prices)
                    if hist_std < 0.0001 or hist_sma <= 0:
                        break
                    hist_bw = (4 * hist_std) / hist_sma
                    if hist_bw < squeeze_threshold * 1.2:  # Was also squeezing
                        squeeze_bars += 1
                    else:
                        break
            
            # ============= MOMENTUM OSCILLATOR (Squeeze Histogram) =============
            # This determines breakout direction - uses linear regression
            momentum = 0.0
            momentum_increasing = False
            
            if len(prices) >= period:
                # Calculate momentum using price deviation from midline
                midline = (max(recent_prices) + min(recent_prices)) / 2
                price_dev = current_price - midline
                
                # Normalize by ATR for comparability
                momentum = price_dev / atr if atr > 0 else 0
                
                # Check if momentum is increasing (key for breakout)
                if len(prices) >= period + 5:
                    prev_prices = prices[-(period+5):-5]
                    prev_midline = (max(prev_prices) + min(prev_prices)) / 2
                    prev_momentum = (prices[-5] - prev_midline) / atr if atr > 0 else 0
                    momentum_increasing = abs(momentum) > abs(prev_momentum)
            
            # ============= VOLUME CONFIRMATION =============
            volume_confirms = False
            volume_ratio = 1.0
            if volumes and len(volumes) >= period:
                recent_vol = volumes[-1]
                avg_vol = np.mean(volumes[-period:-1]) if len(volumes) > period else np.mean(volumes[-period:])
                volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
                # Volume should expand on breakout (>1.2x average)
                volume_confirms = volume_ratio > 1.2
            
            # ============= BREAKOUT DIRECTION =============
            breakout_direction = None
            
            # 🔥 FIX: Stricter breakout confirmation to avoid premature entries
            # Only signal breakout if:
            # 1. We are/were in a squeeze (but now breaking out)
            # 2. Momentum is STRONG and clear
            # 3. Price has BROKEN OUTSIDE the Bollinger Bands (not just above SMA)
            # 4. Volume confirms the move
            if is_squeezing or squeeze_intensity > 0.3:
                # Recent price momentum (5-bar) - require stronger move
                recent_momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
                
                # Position relative to bands
                position_in_bands = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
                
                # 🔥 FIX: Much stricter breakout conditions
                # Breakout UP conditions:
                # - Momentum oscillator STRONG positive (was 0.3, now 0.6)
                # - Price ABOVE upper Bollinger Band (was just > SMA)
                # - Recent momentum at least 0.5% (was 0.2%)
                # - Volume confirms OR Keltner squeeze
                strong_volume = volume_ratio > 1.3
                has_confirmation = strong_volume or keltner_squeeze
                
                if momentum > 0.6 and current_price > bb_upper and recent_momentum > 0.005 and has_confirmation:
                    breakout_direction = 'up'
                # Breakout DOWN conditions:
                elif momentum < -0.6 and current_price < bb_lower and recent_momentum < -0.005 and has_confirmation:
                    breakout_direction = 'down'
                
                # 🔥 FIX: Log near-breakouts for debugging
                elif abs(momentum) > 0.4 and (current_price > sma * 1.005 or current_price < sma * 0.995):
                    logger.debug(f"⏳ {symbol} SQUEEZE BUILDING - Not yet breakout: "
                                f"momentum={momentum:.2f} (need ±0.6), price vs band={position_in_bands:.0%}, "
                                f"recent_mom={recent_momentum:.3%} (need ±0.5%), vol={volume_ratio:.1f}x")
            
            # ============= SQUEEZE QUALITY ASSESSMENT =============
            quality_score = 0
            if keltner_squeeze:
                quality_score += 3  # True TTM squeeze
            if squeeze_bars >= 5:
                quality_score += 2  # Extended squeeze
            if volume_confirms:
                quality_score += 2  # Volume confirms
            if momentum_increasing:
                quality_score += 1  # Momentum building
            if squeeze_intensity > 0.6:
                quality_score += 1  # Very tight
            
            if quality_score >= 7:
                squeeze_quality = 'HIGH'
            elif quality_score >= 4:
                squeeze_quality = 'MEDIUM'
            else:
                squeeze_quality = 'LOW'
            
            # ============= LOGGING =============
            if breakout_direction and squeeze_quality in ['HIGH', 'MEDIUM']:
                logger.info(f"🎯 TTM SQUEEZE BREAKOUT {breakout_direction.upper()}: {symbol} | "
                           f"Quality: {squeeze_quality} | Intensity: {squeeze_intensity:.0%} | "
                           f"BW: {bandwidth:.2%} | Bars: {squeeze_bars} | Vol: {volume_ratio:.1f}x | "
                           f"Keltner: {'✓' if keltner_squeeze else '✗'}")
            elif is_squeezing and squeeze_quality == 'HIGH':
                logger.debug(f"🔥 TTM SQUEEZE BUILDING: {symbol} | Quality: {squeeze_quality} | "
                            f"Bars: {squeeze_bars} | Momentum: {momentum:+.2f}")
            
            return {
                'squeezing': is_squeezing,
                'breakout_direction': breakout_direction,
                'squeeze_intensity': squeeze_intensity,
                'bandwidth': bandwidth,
                'momentum': momentum,
                'squeeze_bars': squeeze_bars,
                'keltner_squeeze': keltner_squeeze,
                'volume_confirms': volume_confirms,
                'squeeze_quality': squeeze_quality,
                'volume_ratio': volume_ratio,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'kc_upper': kc_upper,
                'kc_lower': kc_lower
            }
            
        except Exception as e:
            logger.error(f"Error detecting TTM squeeze for {symbol}: {e}")
            return self._empty_squeeze_result()
    
    def _empty_squeeze_result(self) -> Dict:
        """Return empty squeeze result for error cases"""
        return {
            'squeezing': False,
            'breakout_direction': None,
            'squeeze_intensity': 0.0,
            'bandwidth': 0.0,
            'momentum': 0.0,
            'squeeze_bars': 0,
            'keltner_squeeze': False,
            'volume_confirms': False,
            'squeeze_quality': 'LOW',
            'volume_ratio': 1.0,
            'bb_upper': 0,
            'bb_lower': 0,
            'kc_upper': 0,
            'kc_lower': 0
        }
    
    def detect_candlestick_patterns(self, symbol: str, candles: List[Dict]) -> Dict:
        """
        🔥 NEW: Professional Candlestick Pattern Detection
        
        Detects classic candlestick patterns that indicate:
        1. Reversal signals (Hammer, Shooting Star, Engulfing)
        2. Continuation signals (Three Soldiers, Marubozu)
        3. Indecision (Doji, Spinning Top)
        
        Args:
            symbol: Trading symbol
            candles: List of candle dicts with 'open', 'high', 'low', 'close'
                    (most recent candle LAST)
        
        Returns:
            Dict with pattern info and trading bias
        """
        try:
            if not candles or len(candles) < 3:
                return self._empty_candle_pattern()
            
            # Get last 3 candles for pattern detection
            c1 = candles[-3]  # 3 bars ago
            c2 = candles[-2]  # 2 bars ago  
            c3 = candles[-1]  # Current bar
            
            # Helper calculations
            def body(c):
                return c['close'] - c['open']
            
            def body_size(c):
                return abs(body(c))
            
            def upper_wick(c):
                return c['high'] - max(c['open'], c['close'])
            
            def lower_wick(c):
                return min(c['open'], c['close']) - c['low']
            
            def candle_range(c):
                return c['high'] - c['low'] if c['high'] > c['low'] else 0.0001
            
            def is_bullish(c):
                return c['close'] > c['open']
            
            def is_bearish(c):
                return c['close'] < c['open']
            
            patterns_found = []
            bullish_score = 0
            bearish_score = 0
            
            # ============= SINGLE CANDLE PATTERNS (Current Bar) =============
            c3_body = body_size(c3)
            c3_range = candle_range(c3)
            c3_upper = upper_wick(c3)
            c3_lower = lower_wick(c3)
            
            # DOJI: Tiny body, indecision - significance depends on TREND position
            if c3_body < c3_range * 0.1:
                patterns_found.append('DOJI')
                # 🔥 FIX: Check TREND from previous candles, not the tiny doji body
                # Doji after uptrend (at top) = bearish reversal signal
                # Doji after downtrend (at bottom) = bullish reversal signal
                prior_trend = (c2['close'] - c1['close']) + (c3['close'] - c2['close']) / 2
                if prior_trend > 0:
                    # Was rising → Doji at TOP → bearish reversal
                    bearish_score += 2
                    patterns_found.append('DOJI_AT_TOP')
                elif prior_trend < 0:
                    # Was falling → Doji at BOTTOM → bullish reversal
                    bullish_score += 2
                    patterns_found.append('DOJI_AT_BOTTOM')
                # If flat trend, doji is just indecision - no score change
            
            # HAMMER: Small body at top, long lower wick (bullish reversal)
            if c3_lower > c3_body * 2 and c3_upper < c3_body * 0.5:
                patterns_found.append('HAMMER')
                bullish_score += 3
            
            # SHOOTING STAR: Small body at bottom, long upper wick (bearish reversal)
            if c3_upper > c3_body * 2 and c3_lower < c3_body * 0.5:
                patterns_found.append('SHOOTING_STAR')
                bearish_score += 3
            
            # MARUBOZU: Strong body, minimal wicks (strong trend)
            if c3_body > c3_range * 0.8:
                if is_bullish(c3):
                    patterns_found.append('BULLISH_MARUBOZU')
                    bullish_score += 2
                else:
                    patterns_found.append('BEARISH_MARUBOZU')
                    bearish_score += 2
            
            # ============= TWO CANDLE PATTERNS =============
            c2_body = body_size(c2)
            
            # BULLISH ENGULFING: Green candle engulfs previous red
            if is_bearish(c2) and is_bullish(c3) and c3_body > c2_body * 1.2:
                if c3['close'] > c2['open'] and c3['open'] < c2['close']:
                    patterns_found.append('BULLISH_ENGULFING')
                    bullish_score += 4
            
            # BEARISH ENGULFING: Red candle engulfs previous green
            if is_bullish(c2) and is_bearish(c3) and c3_body > c2_body * 1.2:
                if c3['close'] < c2['open'] and c3['open'] > c2['close']:
                    patterns_found.append('BEARISH_ENGULFING')
                    bearish_score += 4
            
            # ============= THREE CANDLE PATTERNS =============
            
            # THREE WHITE SOLDIERS: 3 consecutive bullish candles with higher closes
            if is_bullish(c1) and is_bullish(c2) and is_bullish(c3):
                if c2['close'] > c1['close'] and c3['close'] > c2['close']:
                    patterns_found.append('THREE_WHITE_SOLDIERS')
                    bullish_score += 5
            
            # THREE BLACK CROWS: 3 consecutive bearish candles with lower closes
            if is_bearish(c1) and is_bearish(c2) and is_bearish(c3):
                if c2['close'] < c1['close'] and c3['close'] < c2['close']:
                    patterns_found.append('THREE_BLACK_CROWS')
                    bearish_score += 5
            
            # MORNING STAR: Bearish -> Small body -> Bullish (reversal up)
            if is_bearish(c1) and body_size(c2) < body_size(c1) * 0.3 and is_bullish(c3):
                if c3['close'] > (c1['open'] + c1['close']) / 2:
                    patterns_found.append('MORNING_STAR')
                    bullish_score += 4
            
            # EVENING STAR: Bullish -> Small body -> Bearish (reversal down)
            if is_bullish(c1) and body_size(c2) < body_size(c1) * 0.3 and is_bearish(c3):
                if c3['close'] < (c1['open'] + c1['close']) / 2:
                    patterns_found.append('EVENING_STAR')
                    bearish_score += 4
            
            # ============= CALCULATE NET BIAS =============
            net_score = bullish_score - bearish_score
            
            if net_score >= 3:
                bias = 'STRONG_BULLISH'
            elif net_score >= 1:
                bias = 'BULLISH'
            elif net_score <= -3:
                bias = 'STRONG_BEARISH'
            elif net_score <= -1:
                bias = 'BEARISH'
            else:
                bias = 'NEUTRAL'
            
            result = {
                'patterns': patterns_found,
                'bullish_score': bullish_score,
                'bearish_score': bearish_score,
                'net_score': net_score,
                'bias': bias,
                'has_reversal_signal': any(p in ['HAMMER', 'SHOOTING_STAR', 'BULLISH_ENGULFING', 
                                                  'BEARISH_ENGULFING', 'MORNING_STAR', 'EVENING_STAR'] 
                                          for p in patterns_found),
                'has_continuation': any(p in ['THREE_WHITE_SOLDIERS', 'THREE_BLACK_CROWS', 
                                               'BULLISH_MARUBOZU', 'BEARISH_MARUBOZU'] 
                                        for p in patterns_found)
            }
            
            if patterns_found:
                logger.info(f"🕯️ CANDLE PATTERNS: {symbol} {patterns_found} → {bias} (score: {net_score:+d})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting candle patterns for {symbol}: {e}")
            return self._empty_candle_pattern()
    
    def _empty_candle_pattern(self) -> Dict:
        """Return empty candle pattern result"""
        return {
            'patterns': [],
            'bullish_score': 0,
            'bearish_score': 0,
            'net_score': 0,
            'bias': 'NEUTRAL',
            'has_reversal_signal': False,
            'has_continuation': False
        }
    
    def calculate_macd_signal(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        🎯 CODE ENHANCEMENT: MACD with histogram divergence detection
        MACD is excellent for trend strength and momentum
        
        Returns: {'macd': float, 'signal': float, 'histogram': float, 'divergence': str}
        """
        try:
            if len(prices) < slow + signal:
                return {'macd': 0, 'signal': 0, 'histogram': 0, 'divergence': None}
            
            prices_array = np.array(prices)
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(prices_array, fast)
            ema_slow = self._calculate_ema(prices_array, slow)
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            macd_series = prices_array[-len(macd_line):]
            signal_line = self._calculate_ema(macd_line, signal)
            
            # Histogram
            histogram = macd_line[-len(signal_line):] - signal_line
            
            # Detect histogram divergence
            divergence = None
            if len(histogram) >= 10:
                recent_hist = histogram[-10:]
                # Positive divergence: histogram making higher lows
                if recent_hist[-1] > recent_hist[-5] and recent_hist[-1] < 0:
                    divergence = 'bullish'
                # Negative divergence: histogram making lower highs
                elif recent_hist[-1] < recent_hist[-5] and recent_hist[-1] > 0:
                    divergence = 'bearish'
            
            # Detect crossover (MACD just crossed signal line)
            crossover = None
            if macd_line[-1] > signal_line[-1] and macd_line[-2] < signal_line[-2]:
                crossover = 'bullish'
            elif macd_line[-1] < signal_line[-1] and macd_line[-2] > signal_line[-2]:
                crossover = 'bearish'
            
            # 🔥 FIX: Also show current MACD STATE (not just crossover)
            # This gives trend direction even without exact crossover
            macd_state = 'neutral'
            if macd_line[-1] > signal_line[-1]:
                macd_state = 'bullish'  # MACD above signal = bullish momentum
            elif macd_line[-1] < signal_line[-1]:
                macd_state = 'bearish'  # MACD below signal = bearish momentum
            
            # 🔧 2025-12-29: Add SHORT MACD for intraday (5-13-4 instead of 12-26-9)
            # Short MACD reacts faster to price changes
            short_macd_state = 'neutral'
            macd_trend = 'NEUTRAL'  # RISING, FALLING, NEUTRAL
            
            if len(prices) >= 18:  # Need at least 13+4+1 for short MACD
                short_ema_fast = self._calculate_ema(prices_array, 5)
                short_ema_slow = self._calculate_ema(prices_array, 13)
                short_macd_line = short_ema_fast - short_ema_slow
                short_signal_line = self._calculate_ema(short_macd_line, 4)
                
                if short_macd_line[-1] > short_signal_line[-1]:
                    short_macd_state = 'bullish'
                elif short_macd_line[-1] < short_signal_line[-1]:
                    short_macd_state = 'bearish'
                
                # Histogram trend - is momentum shifting?
                # Compare last 3 histogram bars to previous 3
                if len(histogram) >= 6:
                    recent_hist_avg = np.mean(histogram[-3:])
                    older_hist_avg = np.mean(histogram[-6:-3])
                    hist_change = recent_hist_avg - older_hist_avg
                    
                    if hist_change > 0.05:  # Histogram rising
                        macd_trend = 'RISING'  # Momentum shifting bullish
                    elif hist_change < -0.05:  # Histogram falling
                        macd_trend = 'FALLING'  # Momentum shifting bearish
            
            return {
                'macd': macd_line[-1],
                'signal': signal_line[-1],
                'histogram': histogram[-1],
                'divergence': divergence,
                'crossover': crossover,  # Exact crossover event (rare)
                'state': macd_state,     # Standard MACD state (12-26-9)
                'short_state': short_macd_state,  # 🆕 Short MACD state (5-13-4)
                'macd_trend': macd_trend  # 🆕 RISING, FALLING, NEUTRAL
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'divergence': None}
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema

    # ============================================================================
    # 🎯 VOLUME-BASED LEADING INDICATORS - CAN PREDICT PRICE MOVES!
    # ============================================================================
    
    def calculate_obv(self, prices: List[float], volumes: List[float]) -> Dict:
        """
        🎯 ON-BALANCE VOLUME (OBV) - A TRUE LEADING INDICATOR!
        
        OBV LEADS PRICE because:
        - Smart money accumulates BEFORE price moves up
        - Distribution happens BEFORE price drops
        - Volume precedes price in most cases
        
        Returns:
            obv: Current OBV value
            obv_trend: 'rising', 'falling', 'flat'
            obv_divergence: 'bullish' (price down, OBV up), 'bearish' (price up, OBV down), None
            obv_breakout: True if OBV making new highs/lows before price
            accumulation_signal: True if smart money accumulating
        """
        try:
            if len(prices) < 10 or len(volumes) < 10:
                return {
                    'obv': 0, 'obv_trend': 'flat', 'obv_divergence': None,
                    'obv_breakout': False, 'accumulation_signal': False
                }
            
            prices = np.array(prices[-50:])  # Use last 50 periods
            volumes = np.array(volumes[-50:])
            
            # Calculate OBV
            obv = np.zeros(len(prices))
            obv[0] = volumes[0]
            
            for i in range(1, len(prices)):
                if prices[i] > prices[i-1]:
                    obv[i] = obv[i-1] + volumes[i]  # Price up = add volume
                elif prices[i] < prices[i-1]:
                    obv[i] = obv[i-1] - volumes[i]  # Price down = subtract volume
                else:
                    obv[i] = obv[i-1]  # Price unchanged = OBV unchanged
            
            # OBV Trend (using 5-period regression)
            if len(obv) >= 5:
                obv_slope = (obv[-1] - obv[-5]) / 5
                obv_avg = np.mean(obv[-10:])
                obv_trend = 'rising' if obv_slope > obv_avg * 0.01 else ('falling' if obv_slope < -obv_avg * 0.01 else 'flat')
            else:
                obv_trend = 'flat'
            
            # 🎯 OBV DIVERGENCE - THE KEY LEADING SIGNAL!
            # Bullish divergence: Price making lower lows, OBV making higher lows
            # Bearish divergence: Price making higher highs, OBV making lower highs
            obv_divergence = None
            if len(prices) >= 10:
                price_5d_change = prices[-1] - prices[-5]
                obv_5d_change = obv[-1] - obv[-5]
                
                # Bullish divergence: price down but OBV up (accumulation!)
                if price_5d_change < 0 and obv_5d_change > 0:
                    obv_divergence = 'bullish'
                # Bearish divergence: price up but OBV down (distribution!)
                elif price_5d_change > 0 and obv_5d_change < 0:
                    obv_divergence = 'bearish'
            
            # OBV Breakout - OBV making new highs/lows before price
            obv_20_high = np.max(obv[-20:]) if len(obv) >= 20 else obv[-1]
            obv_20_low = np.min(obv[-20:]) if len(obv) >= 20 else obv[-1]
            price_20_high = np.max(prices[-20:]) if len(prices) >= 20 else prices[-1]
            price_20_low = np.min(prices[-20:]) if len(prices) >= 20 else prices[-1]
            
            obv_breakout = False
            if obv[-1] >= obv_20_high * 0.99 and prices[-1] < price_20_high * 0.98:
                obv_breakout = True  # OBV at high but price not = bullish setup
            elif obv[-1] <= obv_20_low * 1.01 and prices[-1] > price_20_low * 1.02:
                obv_breakout = True  # OBV at low but price not = bearish setup
            
            # Accumulation Signal - sustained OBV rise without proportional price rise
            accumulation_signal = False
            if len(prices) >= 10:
                price_pct_change = (prices[-1] - prices[-10]) / prices[-10] * 100
                obv_pct_change = (obv[-1] - obv[-10]) / (abs(obv[-10]) + 1) * 100
                
                # OBV rising faster than price = accumulation
                if obv_pct_change > price_pct_change + 5:  # OBV +5% more than price
                    accumulation_signal = True
            
            return {
                'obv': obv[-1],
                'obv_trend': obv_trend,
                'obv_divergence': obv_divergence,
                'obv_breakout': obv_breakout,
                'accumulation_signal': accumulation_signal,
                'obv_slope': obv_slope if len(obv) >= 5 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
            return {
                'obv': 0, 'obv_trend': 'flat', 'obv_divergence': None,
                'obv_breakout': False, 'accumulation_signal': False
            }

    def calculate_money_flow_index(self, highs: List[float], lows: List[float], 
                                   closes: List[float], volumes: List[float], period: int = 14) -> Dict:
        """
        🎯 MONEY FLOW INDEX (MFI) - RSI with Volume!
        
        MFI is better than RSI because:
        - Incorporates volume (smart money leaves volume footprints)
        - More reliable overbought/oversold signals
        - Volume-weighted so it respects institutional activity
        
        Returns:
            mfi: Current MFI value (0-100)
            mfi_divergence: 'bullish', 'bearish', or None
            overbought: True if MFI > 80
            oversold: True if MFI < 20
        """
        try:
            if len(closes) < period + 1:
                return {'mfi': 50, 'mfi_divergence': None, 'overbought': False, 'oversold': False}
            
            highs = np.array(highs[-(period+5):])
            lows = np.array(lows[-(period+5):])
            closes = np.array(closes[-(period+5):])
            volumes = np.array(volumes[-(period+5):])
            
            # Typical Price
            typical_price = (highs + lows + closes) / 3
            
            # Raw Money Flow
            raw_money_flow = typical_price * volumes
            
            # Positive and Negative Money Flow
            positive_flow = np.zeros(len(typical_price))
            negative_flow = np.zeros(len(typical_price))
            
            for i in range(1, len(typical_price)):
                if typical_price[i] > typical_price[i-1]:
                    positive_flow[i] = raw_money_flow[i]
                elif typical_price[i] < typical_price[i-1]:
                    negative_flow[i] = raw_money_flow[i]
            
            # Sum over period
            positive_sum = np.sum(positive_flow[-period:])
            negative_sum = np.sum(negative_flow[-period:])
            
            # Money Flow Ratio and MFI
            if negative_sum == 0:
                mfi = 100
            else:
                money_ratio = positive_sum / negative_sum
                mfi = 100 - (100 / (1 + money_ratio))
            
            # MFI Divergence
            mfi_divergence = None
            if len(closes) >= 10:
                price_trend = closes[-1] - closes[-5]
                # Would need historical MFI for proper divergence, simplified here
                if mfi < 30 and price_trend < 0:
                    mfi_divergence = 'bullish'  # Oversold + falling price = potential reversal
                elif mfi > 70 and price_trend > 0:
                    mfi_divergence = 'bearish'  # Overbought + rising price = potential reversal
            
            return {
                'mfi': mfi,
                'mfi_divergence': mfi_divergence,
                'overbought': mfi > 80,
                'oversold': mfi < 20
            }
            
        except Exception as e:
            logger.error(f"Error calculating MFI: {e}")
            return {'mfi': 50, 'mfi_divergence': None, 'overbought': False, 'oversold': False}

    def calculate_volume_weighted_rsi(self, prices: List[float], volumes: List[float], period: int = 14) -> Dict:
        """
        🎯 VOLUME-WEIGHTED RSI (VRSI) - RSI that respects volume!
        
        Standard RSI treats all price changes equally, but a 1% move on 10M volume
        is more significant than 1% on 100K volume. VRSI weights changes by volume.
        
        Formula:
            - Weight each price change by its corresponding volume
            - Separate into volume-weighted gains and losses
            - VRSI = 100 - (100 / (1 + volume_weighted_RS))
        
        Returns:
            vrsi: Volume-Weighted RSI (0-100)
            rsi: Standard RSI for comparison
            divergence: 'bullish' if VRSI > RSI (volume supports move), 'bearish' if VRSI < RSI
            volume_confirmation: True if volume confirms RSI signal
        """
        try:
            if len(prices) < period + 1 or len(volumes) < period + 1:
                return {'vrsi': 50, 'rsi': 50, 'divergence': None, 'volume_confirmation': False}
            
            prices = np.array(prices[-(period+1):])
            volumes = np.array(volumes[-(period+1):])
            
            # Calculate price changes
            deltas = np.diff(prices)
            
            # Corresponding volumes (for each price change, use the volume of that period)
            change_volumes = volumes[1:]  # volumes corresponding to each delta
            
            # Volume-weighted gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            volume_weighted_gains = gains * change_volumes
            volume_weighted_losses = losses * change_volumes
            
            # Sum over period
            total_volume = np.sum(change_volumes[-period:])
            if total_volume == 0:
                return {'vrsi': 50, 'rsi': 50, 'divergence': None, 'volume_confirmation': False}
            
            # Volume-weighted averages
            avg_vw_gain = np.sum(volume_weighted_gains[-period:]) / total_volume
            avg_vw_loss = np.sum(volume_weighted_losses[-period:]) / total_volume
            
            # Standard RSI for comparison
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            # Calculate standard RSI
            if avg_loss == 0 and avg_gain == 0:
                rsi = 50
            elif avg_loss == 0:
                rsi = 95
            elif avg_gain == 0:
                rsi = 5
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Calculate VRSI
            if avg_vw_loss == 0 and avg_vw_gain == 0:
                vrsi = 50
            elif avg_vw_loss == 0:
                vrsi = 95
            elif avg_vw_gain == 0:
                vrsi = 5
            else:
                vw_rs = avg_vw_gain / avg_vw_loss
                vrsi = 100 - (100 / (1 + vw_rs))
            
            # Detect divergence between VRSI and RSI
            divergence = None
            diff = vrsi - rsi
            if diff > 10:
                divergence = 'bullish'  # Volume supports upward momentum more than price shows
            elif diff < -10:
                divergence = 'bearish'  # Volume supports downward momentum more than price shows
            
            # Volume confirmation
            # If both RSI and VRSI agree on direction (both oversold or both overbought)
            volume_confirmation = (
                (rsi < 30 and vrsi < 35) or  # Both oversold
                (rsi > 70 and vrsi > 65) or  # Both overbought
                (40 < rsi < 60 and 40 < vrsi < 60)  # Both neutral
            )
            
            # 🔧 2025-12-29: Calculate SHORT VRSI (5 periods) to capture RECENT volume direction
            # This fixes the lag issue - VRSI 14 shows past, VRSI 5 shows current
            short_period = 5
            vrsi_short = 50.0  # Default
            vrsi_trend = 'NEUTRAL'  # 'RISING', 'FALLING', 'NEUTRAL'
            
            if len(prices) >= short_period + 1 and len(volumes) >= short_period + 1:
                # Recalculate for short period
                short_gains = gains[-short_period:]
                short_losses = losses[-short_period:]
                short_volumes = change_volumes[-short_period:]
                
                short_total_vol = np.sum(short_volumes)
                if short_total_vol > 0:
                    short_vw_gain = np.sum(short_gains * short_volumes) / short_total_vol
                    short_vw_loss = np.sum(short_losses * short_volumes) / short_total_vol
                    
                    if short_vw_loss == 0 and short_vw_gain == 0:
                        vrsi_short = 50.0
                    elif short_vw_loss == 0:
                        vrsi_short = 95.0
                    elif short_vw_gain == 0:
                        vrsi_short = 5.0
                    else:
                        short_vw_rs = short_vw_gain / short_vw_loss
                        vrsi_short = 100 - (100 / (1 + short_vw_rs))
                
                # Determine VRSI trend: is recent volume shifting?
                # If short VRSI is 10+ points below long VRSI, volume is shifting to selling
                # If short VRSI is 10+ points above long VRSI, volume is shifting to buying
                trend_diff = vrsi_short - vrsi
                if trend_diff > 10:
                    vrsi_trend = 'RISING'  # Recent volume on UP moves (confirms BUY)
                elif trend_diff < -10:
                    vrsi_trend = 'FALLING'  # Recent volume on DOWN moves (confirms SELL)
            
            return {
                'vrsi': round(vrsi, 1),
                'vrsi_short': round(vrsi_short, 1),  # 🆕 5-period VRSI
                'vrsi_trend': vrsi_trend,  # 🆕 'RISING', 'FALLING', 'NEUTRAL'
                'rsi': round(rsi, 1),
                'divergence': divergence,
                'volume_confirmation': volume_confirmation,
                'vrsi_overbought': vrsi > 70,
                'vrsi_oversold': vrsi < 30
            }
            
        except Exception as e:
            logger.error(f"Error calculating VRSI: {e}")
            return {'vrsi': 50, 'rsi': 50, 'divergence': None, 'volume_confirmation': False}

    def calculate_volume_weighted_pressure(self, highs: List[float], lows: List[float], 
                                           closes: List[float], volumes: List[float],
                                           opens: List[float] = None) -> Dict:
        """
        🎯 VOLUME-WEIGHTED BUY/SELL PRESSURE
        
        Instead of just using price position in candle range, weight by volume.
        High volume at the top of the range = strong selling pressure
        High volume at the bottom of the range = strong buying pressure
        
        Formula:
            - For each candle, calculate buy/sell pressure from price position
            - Weight by volume of that candle
            - Aggregate over recent candles
        
        Returns:
            vw_buying_pressure: 0-1 (volume-weighted)
            vw_selling_pressure: 0-1 (volume-weighted)
            pressure_ratio: buying/selling ratio
            dominant_pressure: 'BUY', 'SELL', or 'NEUTRAL'
            volume_intensity: How much volume is behind the pressure
        """
        try:
            min_len = min(len(highs), len(lows), len(closes), len(volumes))
            if min_len < 5:
                return {
                    'vw_buying_pressure': 0.5, 'vw_selling_pressure': 0.5,
                    'pressure_ratio': 1.0, 'dominant_pressure': 'NEUTRAL',
                    'volume_intensity': 0
                }
            
            # Use last 20 candles for pressure calculation
            lookback = min(20, min_len)
            
            highs = np.array(highs[-lookback:])
            lows = np.array(lows[-lookback:])
            closes = np.array(closes[-lookback:])
            volumes = np.array(volumes[-lookback:])
            
            if opens is not None and len(opens) >= lookback:
                opens = np.array(opens[-lookback:])
            else:
                opens = None
            
            total_volume = np.sum(volumes)
            if total_volume == 0:
                return {
                    'vw_buying_pressure': 0.5, 'vw_selling_pressure': 0.5,
                    'pressure_ratio': 1.0, 'dominant_pressure': 'NEUTRAL',
                    'volume_intensity': 0
                }
            
            # Calculate pressure for each candle
            vw_buy_pressure_sum = 0
            vw_sell_pressure_sum = 0
            
            for i in range(len(closes)):
                candle_range = highs[i] - lows[i]
                if candle_range <= 0:
                    continue
                
                # Basic pressure from close position in range
                buy_pressure = (closes[i] - lows[i]) / candle_range
                sell_pressure = (highs[i] - closes[i]) / candle_range
                
                # If we have open, also factor in candle direction
                if opens is not None:
                    candle_body = closes[i] - opens[i]
                    body_ratio = abs(candle_body) / candle_range if candle_range > 0 else 0
                    
                    if candle_body > 0:  # Bullish candle
                        buy_pressure = buy_pressure * 0.7 + body_ratio * 0.3
                    else:  # Bearish candle
                        sell_pressure = sell_pressure * 0.7 + body_ratio * 0.3
                
                # Weight by volume
                volume_weight = volumes[i] / total_volume
                vw_buy_pressure_sum += buy_pressure * volume_weight
                vw_sell_pressure_sum += sell_pressure * volume_weight
            
            # Normalize to 0-1
            vw_buying_pressure = min(max(vw_buy_pressure_sum, 0), 1)
            vw_selling_pressure = min(max(vw_sell_pressure_sum, 0), 1)
            
            # Pressure ratio
            if vw_selling_pressure > 0:
                pressure_ratio = vw_buying_pressure / vw_selling_pressure
            else:
                pressure_ratio = 2.0 if vw_buying_pressure > 0.5 else 1.0
            
            # Determine dominant pressure
            if pressure_ratio > 1.5:
                dominant_pressure = 'BUY'
            elif pressure_ratio < 0.67:
                dominant_pressure = 'SELL'
            else:
                dominant_pressure = 'NEUTRAL'
            
            # Volume intensity (average volume vs typical)
            avg_volume = np.mean(volumes)
            recent_volume = np.mean(volumes[-5:])
            volume_intensity = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            return {
                'vw_buying_pressure': round(vw_buying_pressure, 3),
                'vw_selling_pressure': round(vw_selling_pressure, 3),
                'pressure_ratio': round(pressure_ratio, 2),
                'dominant_pressure': dominant_pressure,
                'volume_intensity': round(volume_intensity, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume-weighted pressure: {e}")
            return {
                'vw_buying_pressure': 0.5, 'vw_selling_pressure': 0.5,
                'pressure_ratio': 1.0, 'dominant_pressure': 'NEUTRAL',
                'volume_intensity': 0
            }

    def calculate_real_vwap(self, prices: List[float], volumes: List[float], 
                            highs: List[float] = None, lows: List[float] = None) -> Dict:
        """
        🎯 REAL VWAP CALCULATION - Fixed version!
        
        VWAP = Σ(Price × Volume) / Σ(Volume)
        
        Returns:
            vwap: Volume Weighted Average Price
            vwap_deviation: How far current price is from VWAP (%)
            above_vwap: True if price above VWAP (bullish)
            vwap_trend: 'rising', 'falling', 'flat'
        """
        try:
            if len(prices) < 5 or len(volumes) < 5:
                return {'vwap': 0, 'vwap_deviation': 0, 'above_vwap': False, 'vwap_trend': 'flat'}
            
            prices = np.array(prices[-50:])
            volumes = np.array(volumes[-50:])
            
            # Use typical price if OHLC available, otherwise just close
            if highs is not None and lows is not None:
                highs = np.array(highs[-50:])
                lows = np.array(lows[-50:])
                typical_prices = (highs + lows + prices) / 3
            else:
                typical_prices = prices
            
            # REAL VWAP: Each price weighted by its own volume
            cumulative_volume = np.cumsum(volumes)
            cumulative_vwap = np.cumsum(typical_prices * volumes)
            
            # Avoid division by zero
            vwap_series = np.where(cumulative_volume > 0, 
                                   cumulative_vwap / cumulative_volume, 
                                   typical_prices)
            
            current_vwap = vwap_series[-1]
            current_price = prices[-1]
            
            # VWAP Deviation
            vwap_deviation = ((current_price - current_vwap) / current_vwap * 100) if current_vwap > 0 else 0
            
            # VWAP Trend
            if len(vwap_series) >= 5:
                vwap_slope = vwap_series[-1] - vwap_series[-5]
                vwap_trend = 'rising' if vwap_slope > 0 else ('falling' if vwap_slope < 0 else 'flat')
            else:
                vwap_trend = 'flat'
            
            return {
                'vwap': current_vwap,
                'vwap_deviation': vwap_deviation,
                'above_vwap': current_price > current_vwap,
                'vwap_trend': vwap_trend
            }
            
        except Exception as e:
            logger.error(f"Error calculating real VWAP: {e}")
            return {'vwap': 0, 'vwap_deviation': 0, 'above_vwap': False, 'vwap_trend': 'flat'}

    def calculate_volume_price_trend(self, prices: List[float], volumes: List[float]) -> Dict:
        """
        🎯 VOLUME PRICE TREND (VPT) - Another leading indicator!
        
        VPT = Previous VPT + Volume × (Price Change %)
        
        Shows the strength of price moves based on volume.
        Divergence between VPT and price can signal reversals.
        """
        try:
            if len(prices) < 10 or len(volumes) < 10:
                return {'vpt': 0, 'vpt_trend': 'flat', 'vpt_divergence': None}
            
            prices = np.array(prices[-30:])
            volumes = np.array(volumes[-30:])
            
            # Calculate VPT
            vpt = np.zeros(len(prices))
            for i in range(1, len(prices)):
                price_change_pct = (prices[i] - prices[i-1]) / prices[i-1]
                vpt[i] = vpt[i-1] + volumes[i] * price_change_pct
            
            # VPT Trend
            vpt_slope = vpt[-1] - vpt[-5] if len(vpt) >= 5 else 0
            vpt_trend = 'rising' if vpt_slope > 0 else ('falling' if vpt_slope < 0 else 'flat')
            
            # VPT Divergence
            vpt_divergence = None
            price_change = prices[-1] - prices[-5] if len(prices) >= 5 else 0
            
            if price_change < 0 and vpt_slope > 0:
                vpt_divergence = 'bullish'  # Price down, VPT up = accumulation
            elif price_change > 0 and vpt_slope < 0:
                vpt_divergence = 'bearish'  # Price up, VPT down = distribution
            
            return {
                'vpt': vpt[-1],
                'vpt_trend': vpt_trend,
                'vpt_divergence': vpt_divergence
            }
            
        except Exception as e:
            logger.error(f"Error calculating VPT: {e}")
            return {'vpt': 0, 'vpt_trend': 'flat', 'vpt_divergence': None}

    def get_volume_leading_signals(self, symbol: str, prices: List[float], volumes: List[float],
                                   highs: List[float] = None, lows: List[float] = None) -> Dict:
        """
        🎯 MASTER FUNCTION: Get all volume-based leading signals
        
        Combines OBV, MFI, VWAP, VPT into a single leading indicator score.
        
        Returns:
            leading_score: -100 to +100 (negative=bearish, positive=bullish)
            leading_signals: List of active signals
            should_buy: True if strong buy setup
            should_sell: True if strong sell setup
            accumulation: True if smart money accumulating
            distribution: True if smart money distributing
        """
        try:
            signals = []
            leading_score = 0
            
            # OBV Analysis
            obv_data = self.calculate_obv(prices, volumes)
            if obv_data['obv_divergence'] == 'bullish':
                leading_score += 30
                signals.append('OBV_BULLISH_DIVERGENCE')
            elif obv_data['obv_divergence'] == 'bearish':
                leading_score -= 30
                signals.append('OBV_BEARISH_DIVERGENCE')
            
            if obv_data['accumulation_signal']:
                leading_score += 20
                signals.append('ACCUMULATION')
            
            if obv_data['obv_trend'] == 'rising':
                leading_score += 10
            elif obv_data['obv_trend'] == 'falling':
                leading_score -= 10
            
            # MFI Analysis
            if highs and lows:
                mfi_data = self.calculate_money_flow_index(highs, lows, prices, volumes)
                if mfi_data['oversold']:
                    leading_score += 15
                    signals.append('MFI_OVERSOLD')
                elif mfi_data['overbought']:
                    leading_score -= 15
                    signals.append('MFI_OVERBOUGHT')
                
                if mfi_data['mfi_divergence'] == 'bullish':
                    leading_score += 20
                    signals.append('MFI_BULLISH_DIVERGENCE')
                elif mfi_data['mfi_divergence'] == 'bearish':
                    leading_score -= 20
                    signals.append('MFI_BEARISH_DIVERGENCE')
            
            # VWAP Analysis
            vwap_data = self.calculate_real_vwap(prices, volumes, highs, lows)
            if vwap_data['above_vwap'] and vwap_data['vwap_trend'] == 'rising':
                leading_score += 10
                signals.append('ABOVE_RISING_VWAP')
            elif not vwap_data['above_vwap'] and vwap_data['vwap_trend'] == 'falling':
                leading_score -= 10
                signals.append('BELOW_FALLING_VWAP')
            
            # VPT Analysis
            vpt_data = self.calculate_volume_price_trend(prices, volumes)
            if vpt_data['vpt_divergence'] == 'bullish':
                leading_score += 15
                signals.append('VPT_BULLISH_DIVERGENCE')
            elif vpt_data['vpt_divergence'] == 'bearish':
                leading_score -= 15
                signals.append('VPT_BEARISH_DIVERGENCE')
            
            # Determine action
            should_buy = leading_score >= 40  # Strong bullish signals
            should_sell = leading_score <= -40  # Strong bearish signals
            accumulation = 'ACCUMULATION' in signals or obv_data['accumulation_signal']
            distribution = 'OBV_BEARISH_DIVERGENCE' in signals or 'VPT_BEARISH_DIVERGENCE' in signals
            
            logger.debug(f"📊 {symbol} VOLUME LEADING: Score={leading_score}, Signals={signals}")
            
            return {
                'leading_score': leading_score,
                'leading_signals': signals,
                'should_buy': should_buy,
                'should_sell': should_sell,
                'accumulation': accumulation,
                'distribution': distribution,
                'obv_data': obv_data,
                'vwap_data': vwap_data,
                'vpt_data': vpt_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume leading signals for {symbol}: {e}")
            return {
                'leading_score': 0, 'leading_signals': [],
                'should_buy': False, 'should_sell': False,
                'accumulation': False, 'distribution': False
            }
    
    def detect_market_regime(self, symbol: str, prices: List[float], volumes: List[float]) -> Dict:
        """
        🎯 CODE ENHANCEMENT: Sophisticated market regime detection
        Different strategies work in different regimes
        
        Returns: {'regime': str, 'strength': float, 'volatility': str}
        """
        try:
            if len(prices) < 50:
                return {'regime': 'UNKNOWN', 'strength': 0.0, 'volatility': 'NORMAL'}
            
            recent_prices = np.array(prices[-50:])
            recent_volumes = np.array(volumes[-50:]) if len(volumes) >= 50 else None
            
            # Calculate metrics
            returns = np.diff(recent_prices) / recent_prices[:-1]
            
            # 1. Trend detection (using ADX concept)
            sma_20 = np.mean(recent_prices[-20:])
            sma_50 = np.mean(recent_prices)
            trend_slope = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            # 2. Volatility regime
            volatility = np.std(returns) * np.sqrt(252)
            hist_volatility = np.std(np.diff(prices[-100:-50]) / prices[-100:-50]) * np.sqrt(252) if len(prices) >= 100 else volatility
            
            volatility_regime = 'HIGH' if volatility > hist_volatility * 1.3 else 'LOW' if volatility < hist_volatility * 0.7 else 'NORMAL'
            
            # 3. Determine regime
            if abs(trend_slope) > 0.05 and sma_20 > sma_50 * 1.01:
                regime = 'STRONG_TRENDING_UP'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif abs(trend_slope) > 0.05 and sma_20 < sma_50 * 0.99:
                regime = 'STRONG_TRENDING_DOWN'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif abs(trend_slope) > 0.02:
                regime = 'TRENDING_UP' if trend_slope > 0 else 'TRENDING_DOWN'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif volatility_regime == 'HIGH':
                regime = 'VOLATILE_RANGING'
                strength = 0.5
            else:
                regime = 'RANGING'
                strength = 0.3
            
            logger.debug(f"📊 Market Regime for {symbol}: {regime} (strength: {strength:.2f}, vol: {volatility_regime})")
            
            return {
                'regime': regime,
                'strength': strength,
                'volatility': volatility_regime,
                'trend_slope': trend_slope,
                'current_volatility': volatility
            }
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {'regime': 'UNKNOWN', 'strength': 0.0, 'volatility': 'NORMAL'}
    
    def analyze_market_depth(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """
        🎯 MARKET DEPTH ANALYSIS from Zerodha Level-2 Data
        Analyzes bid/ask spread, order book imbalance, and liquidity
        
        Returns:
            - bid_ask_spread: Percentage spread between best bid and ask
            - order_imbalance: Ratio of buy vs sell pressure (-1 to +1)
            - liquidity_score: 0-10 score based on depth liquidity
            - buy_wall: True if significant buy support detected
            - sell_wall: True if significant sell resistance detected
            - recommendation: 'FAVORABLE_BUY', 'FAVORABLE_SELL', 'NEUTRAL', 'POOR_LIQUIDITY'
        """
        try:
            data = market_data.get(symbol, {})
            depth = data.get('depth', {})
            
            if not depth:
                logger.debug(f"📊 {symbol}: No market depth data available")
                return {
                    'bid_ask_spread': 0,
                    'order_imbalance': 0,
                    'liquidity_score': 5,
                    'buy_wall': False,
                    'sell_wall': False,
                    'recommendation': 'NO_DEPTH_DATA'
                }
            
            buy_depth = depth.get('buy', [])
            sell_depth = depth.get('sell', [])
            
            if not buy_depth or not sell_depth:
                return {
                    'bid_ask_spread': 0,
                    'order_imbalance': 0,
                    'liquidity_score': 5,
                    'buy_wall': False,
                    'sell_wall': False,
                    'recommendation': 'INCOMPLETE_DEPTH'
                }
            
            # 1. Bid-Ask Spread Analysis
            best_bid = buy_depth[0].get('price', 0) if buy_depth else 0
            best_ask = sell_depth[0].get('price', 0) if sell_depth else 0
            mid_price = (best_bid + best_ask) / 2 if (best_bid > 0 and best_ask > 0) else 0
            
            bid_ask_spread = 0
            if mid_price > 0:
                bid_ask_spread = ((best_ask - best_bid) / mid_price) * 100
            
            # 2. Order Book Imbalance (buy vs sell pressure)
            total_bid_qty = sum(level.get('quantity', 0) for level in buy_depth[:5])
            total_ask_qty = sum(level.get('quantity', 0) for level in sell_depth[:5])
            total_qty = total_bid_qty + total_ask_qty
            
            order_imbalance = 0
            if total_qty > 0:
                order_imbalance = (total_bid_qty - total_ask_qty) / total_qty  # -1 to +1
            
            # 3. Liquidity Score (based on depth and spread)
            liquidity_score = 5  # Default neutral
            
            # Better liquidity = tighter spread and more depth
            if bid_ask_spread < 0.05 and total_qty > 10000:
                liquidity_score = 9
            elif bid_ask_spread < 0.10 and total_qty > 5000:
                liquidity_score = 8
            elif bid_ask_spread < 0.15 and total_qty > 2000:
                liquidity_score = 7
            elif bid_ask_spread < 0.20:
                liquidity_score = 6
            elif bid_ask_spread > 0.50:
                liquidity_score = 3  # Poor liquidity
            elif bid_ask_spread > 1.0:
                liquidity_score = 1  # Very poor liquidity
            
            # 4. Buy/Sell Wall Detection (large orders at specific levels)
            buy_wall = False
            sell_wall = False
            
            if len(buy_depth) >= 3:
                avg_bid_qty = total_bid_qty / min(5, len(buy_depth))
                if buy_depth[0].get('quantity', 0) > avg_bid_qty * 3:
                    buy_wall = True
                    logger.info(f"🛡️ {symbol}: BUY WALL detected at ₹{best_bid}")
            
            if len(sell_depth) >= 3:
                avg_ask_qty = total_ask_qty / min(5, len(sell_depth))
                if sell_depth[0].get('quantity', 0) > avg_ask_qty * 3:
                    sell_wall = True
                    logger.info(f"🧱 {symbol}: SELL WALL detected at ₹{best_ask}")
            
            # 5. Trading Recommendation based on depth
            recommendation = 'NEUTRAL'
            
            if liquidity_score <= 3:
                recommendation = 'POOR_LIQUIDITY'
            elif order_imbalance > 0.3 and not sell_wall:
                recommendation = 'FAVORABLE_BUY'
            elif order_imbalance < -0.3 and not buy_wall:
                recommendation = 'FAVORABLE_SELL'
            elif sell_wall:
                recommendation = 'RESISTANCE_AHEAD'
            elif buy_wall:
                recommendation = 'SUPPORT_BELOW'
            
            result = {
                'bid_ask_spread': round(bid_ask_spread, 4),
                'order_imbalance': round(order_imbalance, 3),
                'liquidity_score': liquidity_score,
                'buy_wall': buy_wall,
                'sell_wall': sell_wall,
                'recommendation': recommendation,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'total_bid_qty': total_bid_qty,
                'total_ask_qty': total_ask_qty
            }
            
            if liquidity_score <= 4 or buy_wall or sell_wall:
                logger.info(f"📊 {symbol} DEPTH: Spread={bid_ask_spread:.2f}%, Imbalance={order_imbalance:+.2f}, Liquidity={liquidity_score}/10, Rec={recommendation}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market depth for {symbol}: {e}")
            return {
                'bid_ask_spread': 0,
                'order_imbalance': 0,
                'liquidity_score': 5,
                'buy_wall': False,
                'sell_wall': False,
                'recommendation': 'ERROR'
            }
    
    def analyze_open_interest(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """
        🎯 OPEN INTEREST ANALYSIS from TrueData
        Tracks institutional positioning through OI changes
        
        Returns:
            - oi: Current Open Interest
            - oi_change: Change in OI from previous session
            - oi_signal: 'LONG_BUILDUP', 'SHORT_BUILDUP', 'LONG_UNWINDING', 'SHORT_COVERING', 'NEUTRAL'
            - institutional_bias: 'BULLISH', 'BEARISH', 'NEUTRAL'
            - confidence: Confidence in the OI signal (0-1)
        """
        try:
            data = market_data.get(symbol, {})
            
            oi = data.get('oi', 0)
            oi_change = data.get('oi_change', 0)
            change_percent = data.get('change_percent', 0)
            
            if oi <= 0:
                return {
                    'oi': 0,
                    'oi_change': 0,
                    'oi_signal': 'NO_OI_DATA',
                    'institutional_bias': 'NEUTRAL',
                    'confidence': 0
                }
            
            # Calculate OI change percentage
            oi_change_pct = (oi_change / (oi - oi_change) * 100) if (oi - oi_change) > 0 else 0
            
            # Determine OI signal based on price and OI movement
            # Long Buildup: Price Up + OI Up (bullish)
            # Short Buildup: Price Down + OI Up (bearish)
            # Long Unwinding: Price Down + OI Down (bearish to neutral)
            # Short Covering: Price Up + OI Down (bullish but weak)
            
            oi_signal = 'NEUTRAL'
            institutional_bias = 'NEUTRAL'
            confidence = 0.5
            
            price_up = change_percent > 0.3
            price_down = change_percent < -0.3
            oi_up = oi_change_pct > 1.0
            oi_down = oi_change_pct < -1.0
            
            if price_up and oi_up:
                oi_signal = 'LONG_BUILDUP'
                institutional_bias = 'BULLISH'
                confidence = min(0.5 + abs(oi_change_pct) / 10, 0.95)
                logger.info(f"📈 {symbol} OI ANALYSIS: LONG BUILDUP - Price +{change_percent:.1f}%, OI +{oi_change_pct:.1f}%")
            
            elif price_down and oi_up:
                oi_signal = 'SHORT_BUILDUP'
                institutional_bias = 'BEARISH'
                confidence = min(0.5 + abs(oi_change_pct) / 10, 0.95)
                logger.info(f"📉 {symbol} OI ANALYSIS: SHORT BUILDUP - Price {change_percent:.1f}%, OI +{oi_change_pct:.1f}%")
            
            elif price_down and oi_down:
                oi_signal = 'LONG_UNWINDING'
                institutional_bias = 'BEARISH'  # Longs exiting = bearish
                confidence = min(0.4 + abs(oi_change_pct) / 15, 0.8)
                logger.info(f"📉 {symbol} OI ANALYSIS: LONG UNWINDING - Price {change_percent:.1f}%, OI {oi_change_pct:.1f}%")
            
            elif price_up and oi_down:
                oi_signal = 'SHORT_COVERING'
                institutional_bias = 'BULLISH'  # Shorts exiting = bullish but weak
                confidence = min(0.4 + abs(oi_change_pct) / 15, 0.75)
                logger.info(f"📈 {symbol} OI ANALYSIS: SHORT COVERING - Price +{change_percent:.1f}%, OI {oi_change_pct:.1f}%")
            
            return {
                'oi': oi,
                'oi_change': oi_change,
                'oi_change_pct': round(oi_change_pct, 2),
                'oi_signal': oi_signal,
                'institutional_bias': institutional_bias,
                'confidence': round(confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing OI for {symbol}: {e}")
            return {
                'oi': 0,
                'oi_change': 0,
                'oi_signal': 'ERROR',
                'institutional_bias': 'NEUTRAL',
                'confidence': 0
            }
    
    def calculate_daily_weekly_levels(self, symbol: str, market_data: Dict) -> Dict[str, Any]:
        """
        🎯 DAILY/WEEKLY PIVOT POINTS AND MAJOR S/R LEVELS
        
        Calculates:
        - Daily Pivot Points (Classic): PP, R1, R2, R3, S1, S2, S3
        - Weekly Levels from price history (if available)
        - Key psychological levels (round numbers)
        - Identifies if price is near major level
        
        Returns comprehensive level analysis for entry/exit decisions
        """
        try:
            data = market_data.get(symbol, {})
            ltp = data.get('ltp', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            close = data.get('close', 0) or data.get('previous_close', 0)
            open_price = data.get('open', 0)
            
            if ltp <= 0:
                return {'levels': {}, 'near_level': None, 'distance_to_level': 0}
            
            # Use yesterday's high/low/close for pivot calculation
            # If not available, use today's open and estimates
            prev_high = high if high > 0 else ltp * 1.01
            prev_low = low if low > 0 else ltp * 0.99
            prev_close = close if close > 0 else ltp
            
            # ============= CLASSIC PIVOT POINTS =============
            # PP = (H + L + C) / 3
            pivot_point = (prev_high + prev_low + prev_close) / 3
            
            # Support and Resistance levels
            r1 = 2 * pivot_point - prev_low
            r2 = pivot_point + (prev_high - prev_low)
            r3 = prev_high + 2 * (pivot_point - prev_low)
            
            s1 = 2 * pivot_point - prev_high
            s2 = pivot_point - (prev_high - prev_low)
            s3 = prev_low - 2 * (prev_high - pivot_point)
            
            # ============= FIBONACCI PIVOT LEVELS =============
            fib_r1 = pivot_point + 0.382 * (prev_high - prev_low)
            fib_r2 = pivot_point + 0.618 * (prev_high - prev_low)
            fib_s1 = pivot_point - 0.382 * (prev_high - prev_low)
            fib_s2 = pivot_point - 0.618 * (prev_high - prev_low)
            
            # ============= PSYCHOLOGICAL LEVELS (Round Numbers) =============
            round_factor = 50 if ltp > 500 else (10 if ltp > 100 else 5)
            psychological_above = ((ltp // round_factor) + 1) * round_factor
            psychological_below = (ltp // round_factor) * round_factor
            
            # ============= COLLECT ALL LEVELS =============
            levels = {
                'pivot': round(pivot_point, 2),
                'r1': round(r1, 2),
                'r2': round(r2, 2),
                'r3': round(r3, 2),
                's1': round(s1, 2),
                's2': round(s2, 2),
                's3': round(s3, 2),
                'fib_r1': round(fib_r1, 2),
                'fib_r2': round(fib_r2, 2),
                'fib_s1': round(fib_s1, 2),
                'fib_s2': round(fib_s2, 2),
                'psychological_above': psychological_above,
                'psychological_below': psychological_below,
                'day_high': round(prev_high, 2),
                'day_low': round(prev_low, 2),
                'vwap_estimate': round((prev_high + prev_low + prev_close) / 3, 2)  # Approximation
            }
            
            # ============= FIND NEAREST LEVEL =============
            all_levels = [
                ('pivot', pivot_point),
                ('r1', r1), ('r2', r2), ('r3', r3),
                ('s1', s1), ('s2', s2), ('s3', s3),
                ('day_high', prev_high), ('day_low', prev_low),
                ('psych_above', psychological_above), ('psych_below', psychological_below)
            ]
            
            nearest_level = None
            min_distance = float('inf')
            
            for name, level in all_levels:
                distance = abs(ltp - level)
                distance_pct = (distance / ltp) * 100 if ltp > 0 else 0
                
                if distance_pct < min_distance:
                    min_distance = distance_pct
                    nearest_level = {
                        'name': name,
                        'price': round(level, 2),
                        'distance_percent': round(distance_pct, 2),
                        'type': 'RESISTANCE' if level > ltp else 'SUPPORT'
                    }
            
            # ============= TRADING RECOMMENDATION =============
            recommendation = 'NEUTRAL'
            
            # Check if near significant level (within 0.3%)
            if min_distance < 0.3:
                if nearest_level['type'] == 'SUPPORT':
                    recommendation = 'NEAR_SUPPORT'
                else:
                    recommendation = 'NEAR_RESISTANCE'
            
            # Check position relative to pivot
            if ltp > pivot_point:
                position_vs_pivot = 'ABOVE_PIVOT'
            else:
                position_vs_pivot = 'BELOW_PIVOT'
            
            result = {
                'levels': levels,
                'nearest_level': nearest_level,
                'position_vs_pivot': position_vs_pivot,
                'recommendation': recommendation,
                'current_price': ltp
            }
            
            # Log if near important level
            if min_distance < 0.5:
                logger.info(f"📊 {symbol} NEAR LEVEL: {nearest_level['name']} at ₹{nearest_level['price']} ({min_distance:.2f}% away)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating daily/weekly levels for {symbol}: {e}")
            return {
                'levels': {},
                'nearest_level': None,
                'position_vs_pivot': 'UNKNOWN',
                'recommendation': 'ERROR'
            }
    
    def calculate_smart_entry_score(self, symbol: str, signal_type: str, market_data: Dict) -> float:
        """
        🎯 CODE ENHANCEMENT: Multi-factor entry quality score
        Combines multiple technical factors for optimal entry timing
        
        Returns: Score 0.0-1.0 (1.0 = perfect entry setup)
        """
        try:
            data = market_data.get(symbol, {})
            
            # Get price history
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return 0.5  # Neutral if insufficient data
            
            prices = self.price_history[symbol]
            volumes = self.volume_history.get(symbol, [])
            
            score_factors = []
            
            # Factor 1: RSI positioning (30% weight)
            if len(prices) >= 14:
                rsi = self._calculate_rsi(prices, 14)
                if signal_type == 'BUY':
                    # Prefer RSI 30-50 (oversold but recovering)
                    if 30 <= rsi <= 50:
                        score_factors.append(0.3)
                    elif 25 <= rsi < 30 or 50 < rsi <= 55:
                        score_factors.append(0.2)
                    else:
                        score_factors.append(0.1)
                else:  # SELL
                    # Prefer RSI 50-70 (overbought but weakening)
                    if 50 <= rsi <= 70:
                        score_factors.append(0.3)
                    elif 45 <= rsi < 50 or 70 < rsi <= 75:
                        score_factors.append(0.2)
                    else:
                        score_factors.append(0.1)
            
            # Factor 2: Volume confirmation (25% weight)
            if len(volumes) >= 20:
                current_vol = volumes[-1]
                avg_vol = np.mean(volumes[-20:])
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
                
                if vol_ratio > 1.5:
                    score_factors.append(0.25)  # Strong volume
                elif vol_ratio > 1.2:
                    score_factors.append(0.18)  # Good volume
                elif vol_ratio > 1.0:
                    score_factors.append(0.12)  # Above average
                else:
                    score_factors.append(0.05)  # Weak volume
            
            # Factor 3: Price action alignment (25% weight)
            if len(prices) >= 5:
                short_momentum = (prices[-1] - prices[-3]) / prices[-3]
                medium_momentum = (prices[-1] - prices[-5]) / prices[-5]
                
                if signal_type == 'BUY':
                    if short_momentum > 0 and medium_momentum > 0:
                        score_factors.append(0.25)  # Aligned momentum
                    elif short_momentum > 0:
                        score_factors.append(0.15)  # Short-term momentum
                    else:
                        score_factors.append(0.05)  # Against momentum
                else:  # SELL
                    if short_momentum < 0 and medium_momentum < 0:
                        score_factors.append(0.25)  # Aligned momentum
                    elif short_momentum < 0:
                        score_factors.append(0.15)  # Short-term momentum
                    else:
                        score_factors.append(0.05)  # Against momentum
            
            # Factor 4: Support/Resistance proximity (20% weight)
            current_price = data.get('ltp', 0)
            if current_price > 0 and len(prices) >= 20:
                recent_high = max(prices[-20:])
                recent_low = min(prices[-20:])
                price_range = recent_high - recent_low
                
                if signal_type == 'BUY':
                    # Better entry near support (lower 25% of range)
                    distance_from_low = (current_price - recent_low) / price_range if price_range > 0 else 0.5
                    if distance_from_low < 0.25:
                        score_factors.append(0.20)
                    elif distance_from_low < 0.40:
                        score_factors.append(0.15)
                    else:
                        score_factors.append(0.05)
                else:  # SELL
                    # Better entry near resistance (upper 25% of range)
                    distance_from_high = (recent_high - current_price) / price_range if price_range > 0 else 0.5
                    if distance_from_high < 0.25:
                        score_factors.append(0.20)
                    elif distance_from_high < 0.40:
                        score_factors.append(0.15)
                    else:
                        score_factors.append(0.05)
            
            total_score = sum(score_factors)
            
            logger.debug(f"📊 Entry Score for {symbol} {signal_type}: {total_score:.2f}")
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating entry score: {e}")
            return 0.5
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator - FIXED: Never returns exactly 0"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            prices_array = np.array(prices[-period-1:])
            deltas = np.diff(prices_array)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            
            # 🔥 FIX: Handle edge cases properly
            if avg_loss == 0 and avg_gain == 0:
                # No price movement - return neutral
                return 50.0
            elif avg_loss == 0:
                # Only gains - extremely overbought
                return 95.0
            elif avg_gain == 0:
                # Only losses - extremely oversold (but NOT 0)
                return 5.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # 🔥 FIX: Clamp RSI to valid range [5, 95] to avoid edge cases
            rsi = max(5.0, min(95.0, rsi))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def calculate_volatility_adjusted_position_size(self, symbol: str, base_quantity: int, 
                                                    entry_price: float, stop_loss: float) -> int:
        """
        🎯 CODE ENHANCEMENT: Dynamic position sizing based on volatility
        Reduces position size in high volatility, increases in low volatility
        
        Returns: Adjusted quantity
        """
        try:
            # Get price history
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return base_quantity
            
            prices = self.price_history[symbol]
            
            # Calculate current volatility
            returns = np.diff(prices[-20:]) / prices[-20:-1]
            current_vol = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Calculate historical volatility (last 50 days if available)
            if len(prices) >= 50:
                hist_returns = np.diff(prices[-50:]) / prices[-50:-1]
                hist_vol = np.std(hist_returns) * np.sqrt(252)
            else:
                hist_vol = current_vol
            
            # Volatility ratio
            vol_ratio = current_vol / hist_vol if hist_vol > 0 else 1.0
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            risk_percent = risk_per_share / entry_price if entry_price > 0 else 0.05
            
            # Adjust position size based on volatility
            if vol_ratio > 1.5:  # High volatility
                adjustment_factor = 0.6  # Reduce to 60%
                logger.info(f"⚠️ HIGH VOLATILITY for {symbol}: Reducing position size to 60%")
            elif vol_ratio > 1.2:  # Elevated volatility
                adjustment_factor = 0.8  # Reduce to 80%
                logger.info(f"⚠️ ELEVATED VOLATILITY for {symbol}: Reducing position size to 80%")
            elif vol_ratio < 0.7:  # Low volatility
                adjustment_factor = 1.2  # Increase to 120%
                logger.info(f"✅ LOW VOLATILITY for {symbol}: Increasing position size to 120%")
            else:  # Normal volatility
                adjustment_factor = 1.0
            
            # Also consider risk percentage
            if risk_percent > 0.05:  # Risk > 5% per share
                risk_adjustment = 0.05 / risk_percent
                adjustment_factor *= risk_adjustment
                logger.info(f"⚠️ HIGH RISK/SHARE for {symbol}: Further reducing position")
            
            adjusted_quantity = int(base_quantity * adjustment_factor)
            
            # Ensure minimum quantity
            adjusted_quantity = max(adjusted_quantity, 1)
            
            logger.info(f"📊 Position Size for {symbol}: {base_quantity} → {adjusted_quantity} (vol_ratio: {vol_ratio:.2f}, risk: {risk_percent:.2%})")
            
            return adjusted_quantity
            
        except Exception as e:
            logger.error(f"Error calculating volatility-adjusted position size: {e}")
            return base_quantity
    
    def calculate_trailing_stop_with_atr(self, symbol: str, entry_price: float, current_price: float,
                                        position_type: str, atr_multiplier: float = 2.0) -> float:
        """
        🎯 CODE ENHANCEMENT: ATR-based trailing stop (adapts to volatility)
        Uses Average True Range for volatility-adjusted stops
        
        Returns: Trailing stop price
        """
        try:
            # Get price history for ATR calculation
            if symbol not in self.price_history or len(self.price_history[symbol]) < 14:
                # Fallback to fixed percentage
                if position_type.upper() == 'LONG':
                    return current_price * 0.98  # 2% trailing stop
                else:
                    return current_price * 1.02
            
            prices = self.price_history[symbol][-14:]
            
            # Calculate True Range
            tr_list = []
            for i in range(1, len(prices)):
                high = prices[i]
                low = prices[i]
                prev_close = prices[i-1]
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                tr_list.append(tr)
            
            # Average True Range
            atr = np.mean(tr_list) if tr_list else (current_price * 0.02)
            
            # Calculate trailing stop
            if position_type.upper() == 'LONG':
                trailing_stop = current_price - (atr * atr_multiplier)
                # Never move stop down
                if entry_price > current_price:  # In loss
                    initial_stop = entry_price * 0.98
                    trailing_stop = max(trailing_stop, initial_stop)
            else:  # SHORT
                trailing_stop = current_price + (atr * atr_multiplier)
                # Never move stop up
                if entry_price < current_price:  # In loss
                    initial_stop = entry_price * 1.02
                    trailing_stop = min(trailing_stop, initial_stop)
            
            logger.debug(f"📊 ATR Trailing Stop for {symbol}: ATR={atr:.2f}, Stop={trailing_stop:.2f}")
            
            return trailing_stop
            
        except Exception as e:
            logger.error(f"Error calculating ATR trailing stop: {e}")
            # Fallback
            if position_type.upper() == 'LONG':
                return current_price * 0.98
            else:
                return current_price * 1.02
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                risk_reward_ratio: float = None) -> float:
        """Calculate dynamic target with MARKET-ADAPTIVE risk/reward ratio"""
        try:
            # Get current market regime for adaptive risk-reward
            market_regime = "NORMAL"
            nifty_momentum = 0.0
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'market_bias') and orchestrator.market_bias:
                    market_regime = getattr(orchestrator.market_bias.current_bias, 'market_regime', 'NORMAL')
                    nifty_momentum = getattr(orchestrator.market_bias.current_bias, 'nifty_momentum', 0.0)
            except:
                pass
            
            # 🚨 DAVID VS GOLIATH: HIGHER R:R to compensate for tighter stops
            # Tighter stops (3-7%) mean we need bigger targets to be profitable
            if risk_reward_ratio is None:
                # RANGING MARKET: Still conservative but higher (was 1.2)
                if abs(nifty_momentum) < 0.15 or market_regime in ('ranging', 'sideways', 'CHOPPY'):
                    risk_reward_ratio = 1.8  # 1:1.8 (was 1.2) - tighter stops need bigger targets
                    logger.debug(f"🔄 RANGING MARKET: Using higher R:R = 1:{risk_reward_ratio} (tight stops)")
                # TRENDING MARKET: Significantly higher (was 2.0)
                elif abs(nifty_momentum) >= 0.3:
                    risk_reward_ratio = 2.5  # 1:2.5 (was 2.0) - ride the trend harder
                    logger.debug(f"📈 TRENDING MARKET: Using aggressive R:R = 1:{risk_reward_ratio} (tight stops)")
                # MODERATE MOMENTUM: Higher balanced (was 1.5)
                else:
                    risk_reward_ratio = 2.0  # 1:2.0 (was 1.5)
                    logger.debug(f"⚖️ MODERATE MARKET: Using improved R:R = 1:{risk_reward_ratio} (tight stops)")
            
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            
            # Calculate reward distance
            reward_distance = risk_distance * risk_reward_ratio
            
            # Calculate target based on entry vs stop loss relationship
            if stop_loss < entry_price:  # BUY trade
                target = entry_price + reward_distance
            else:  # SELL trade
                target = entry_price - reward_distance
            
            logger.info(f"🎯 DYNAMIC TARGET: Entry={entry_price:.2f}, SL={stop_loss:.2f}, "
                       f"Target={target:.2f}, R:R=1:{risk_reward_ratio}, Regime={market_regime}")
            
            return round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target: {e}")
            # Conservative fallback for ranging markets
            target_percent = 0.008  # 0.8% conservative fallback
            if stop_loss < entry_price:  # BUY trade
                return entry_price * (1 + target_percent)
            else:  # SELL trade
                return entry_price * (1 - target_percent)
    
    def calculate_chart_based_stop_loss(self, symbol: str, action: str, entry_price: float, 
                                        symbol_data: Dict = None) -> float:
        """
        🎯 CHART-BASED STOP LOSS - Uses ATR and swing levels instead of fixed percentages
        
        For BUY: Stop below recent swing low OR entry - 1.5×ATR (whichever is tighter but safe)
        For SELL: Stop above recent swing high OR entry + 1.5×ATR
        
        PROFESSIONAL APPROACH:
        1. Find recent swing high/low from price history
        2. Calculate ATR-based stop (volatility-adjusted)
        3. Use the more protective level (tighter stop within reason)
        4. Ensure minimum 0.5% and maximum 3% for intraday
        """
        try:
            # Get ATR for this symbol
            high = symbol_data.get('high', entry_price) if symbol_data else entry_price
            low = symbol_data.get('low', entry_price) if symbol_data else entry_price
            close = symbol_data.get('close', entry_price) if symbol_data else entry_price
            
            atr = self.calculate_atr(symbol, high, low, close)
            
            # Find swing levels from price history
            swing_low, swing_high = self._find_swing_levels(symbol)
            
            # 📊 Get Camarilla levels for professional stop loss placement
            camarilla_stop = None
            try:
                # Check if Camarilla levels are cached (synchronous context)
                if symbol in self._camarilla_cache:
                    camarilla = self._camarilla_cache[symbol]
                    if action.upper() == 'BUY':
                        # For BUY: Stop below L2 or L3 (key support)
                        l2, l3 = camarilla['l2'], camarilla['l3']
                        if l3 < entry_price:
                            camarilla_stop = l3 * 0.998  # Just below L3
                        elif l2 < entry_price:
                            camarilla_stop = l2 * 0.998  # Just below L2
                    else:  # SELL
                        # For SELL: Stop above H2 or H3 (key resistance)
                        h2, h3 = camarilla['h2'], camarilla['h3']
                        if h3 > entry_price:
                            camarilla_stop = h3 * 1.002  # Just above H3
                        elif h2 > entry_price:
                            camarilla_stop = h2 * 1.002  # Just above H2
            except Exception:
                pass
            
            if action.upper() == 'BUY':
                # ATR-based stop: 1.5x ATR below entry
                atr_stop = entry_price - (atr * 1.5)
                
                # Swing-based stop: Just below recent swing low
                swing_stop = swing_low * 0.998 if swing_low > 0 else atr_stop
                
                # Choose best stop: Camarilla > Swing > ATR (tightest valid)
                candidate_stops = [atr_stop]
                if swing_stop and swing_stop < entry_price:
                    candidate_stops.append(swing_stop)
                if camarilla_stop and camarilla_stop < entry_price:
                    candidate_stops.append(camarilla_stop)
                
                # Use TIGHTEST stop (highest value) but respect limits
                min_stop = entry_price * 0.97   # Max 3% loss
                max_stop = entry_price * 0.995  # Min 0.5% stop distance
                
                stop_loss = max(min_stop, min(max_stop, max(candidate_stops)))
                
                log_msg = f"📉 CHART-BASED SL (BUY): {symbol} ATR=₹{atr_stop:.2f}, Swing=₹{swing_stop:.2f}"
                if camarilla_stop:
                    log_msg += f", Camarilla=₹{camarilla_stop:.2f}"
                log_msg += f", Final=₹{stop_loss:.2f} ({((entry_price - stop_loss) / entry_price * 100):.1f}%)"
                logger.info(log_msg)
                
            else:  # SELL
                # ATR-based stop: 1.5x ATR above entry
                atr_stop = entry_price + (atr * 1.5)
                
                # Swing-based stop: Just above recent swing high
                swing_stop = swing_high * 1.002 if swing_high > 0 else atr_stop
                
                # Choose best stop: Camarilla > Swing > ATR (tightest valid)
                candidate_stops = [atr_stop]
                if swing_stop and swing_stop > entry_price:
                    candidate_stops.append(swing_stop)
                if camarilla_stop and camarilla_stop > entry_price:
                    candidate_stops.append(camarilla_stop)
                
                # Use TIGHTEST stop (lowest value) but respect limits
                min_stop = entry_price * 1.005  # Min 0.5% stop distance
                max_stop = entry_price * 1.03   # Max 3% loss
                
                stop_loss = min(max_stop, max(min_stop, min(candidate_stops)))
                
                log_msg = f"📉 CHART-BASED SL (SELL): {symbol} ATR=₹{atr_stop:.2f}, Swing=₹{swing_stop:.2f}"
                if camarilla_stop:
                    log_msg += f", Camarilla=₹{camarilla_stop:.2f}"
                log_msg += f", Final=₹{stop_loss:.2f} ({((stop_loss - entry_price) / entry_price * 100):.1f}%)"
                logger.info(log_msg)
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Chart-based SL calculation failed for {symbol}: {e}")
            # Fallback to 1.5% fixed stop
            if action.upper() == 'BUY':
                return entry_price * 0.985
            else:
                return entry_price * 1.015
    
    def _find_swing_levels(self, symbol: str, lookback: int = 20) -> Tuple[float, float]:
        """
        Find recent swing high and swing low from price history
        
        Returns: (swing_low, swing_high) - 0 if not enough data
        """
        try:
            if symbol not in self.historical_data or len(self.historical_data[symbol]) < 5:
                return 0, 0
            
            history = self.historical_data[symbol][-lookback:]
            
            # Extract lows and highs
            lows = [h.get('low', h.get('close', 0)) for h in history]
            highs = [h.get('high', h.get('close', 0)) for h in history]
            
            # Find swing low: point where low < neighbors on both sides
            swing_low = min(lows) if lows else 0
            
            # Find swing high: point where high > neighbors on both sides  
            swing_high = max(highs) if highs else 0
            
            # More sophisticated swing detection
            for i in range(2, len(lows) - 2):
                # Swing low: lower than 2 candles on each side
                if lows[i] < min(lows[i-2:i]) and lows[i] < min(lows[i+1:i+3]):
                    if lows[i] > swing_low * 0.98:  # More recent and relevant
                        swing_low = lows[i]
                        
            for i in range(2, len(highs) - 2):
                # Swing high: higher than 2 candles on each side
                if highs[i] > max(highs[i-2:i]) and highs[i] > max(highs[i+1:i+3]):
                    if highs[i] < swing_high * 1.02:  # More recent and relevant
                        swing_high = highs[i]
            
            return swing_low, swing_high
            
        except Exception as e:
            logger.error(f"Swing level detection failed for {symbol}: {e}")
            return 0, 0
    
    async def _get_camarilla_levels(self, symbol: str) -> Dict:
        """
        📊 CAMARILLA PIVOTS - Professional Intraday Trading Levels
        
        Fetches or calculates Camarilla pivot points using previous day's daily OHLC.
        Levels are cached daily for performance.
        
        Returns: {
            'h4': float, 'h3': float, 'h2': float, 'h1': float,
            'l1': float, 'l2': float, 'l3': float, 'l4': float,
            'prev_high': float, 'prev_low': float, 'prev_close': float
        }
        """
        try:
            # Check if cache needs daily refresh
            today = datetime.now().strftime('%Y-%m-%d')
            if self._camarilla_cache_date != today:
                logger.info(f"📊 Refreshing Camarilla cache for new day: {today}")
                self._camarilla_cache = {}
                self._camarilla_cache_date = today
            
            # Return cached levels if available
            if symbol in self._camarilla_cache:
                return self._camarilla_cache[symbol]
            
            # Check Zerodha availability
            if not self.orchestrator or not hasattr(self.orchestrator, 'zerodha_client'):
                return {}
            
            zerodha_client = self.orchestrator.zerodha_client
            if not zerodha_client or not getattr(zerodha_client, 'is_connected', False):
                return {}
            
            # Map index symbols for Zerodha
            symbol_upper = symbol.upper().strip()
            index_map = {
                'NIFTY-I': ('NIFTY 50', 'NSE'), 'NIFTY': ('NIFTY 50', 'NSE'),
                'BANKNIFTY-I': ('NIFTY BANK', 'NSE'), 'BANKNIFTY': ('NIFTY BANK', 'NSE'),
                'FINNIFTY-I': ('NIFTY FIN SERVICE', 'NSE'), 'FINNIFTY': ('NIFTY FIN SERVICE', 'NSE'),
                'SENSEX-I': ('SENSEX', 'BSE'), 'SENSEX': ('SENSEX', 'BSE'),
            }
            
            zerodha_symbol, exchange = index_map.get(symbol_upper, (symbol_upper, 'NSE'))
            
            # Fetch last 5 daily candles (handles weekends/holidays)
            candles = await zerodha_client.get_historical_data(
                symbol=zerodha_symbol,
                interval='day',
                from_date=datetime.now() - timedelta(days=7),
                to_date=datetime.now(),
                exchange=exchange
            )
            
            if not candles or len(candles) < 2:
                return {}
            
            # Get previous day's complete candle (second-to-last)
            yesterday = candles[-2]
            prev_high = float(yesterday.get('high', 0))
            prev_low = float(yesterday.get('low', 0))
            prev_close = float(yesterday.get('close', 0))
            
            if prev_high <= 0 or prev_low <= 0 or prev_close <= 0:
                return {}
            
            # Calculate Camarilla levels
            range_val = prev_high - prev_low
            
            # Resistance levels (H1 to H4)
            h4 = prev_close + range_val * 1.1 / 2
            h3 = prev_close + range_val * 1.1 / 4
            h2 = prev_close + range_val * 1.1 / 6
            h1 = prev_close + range_val * 1.1 / 12
            
            # Support levels (L1 to L4)
            l1 = prev_close - range_val * 1.1 / 12
            l2 = prev_close - range_val * 1.1 / 6
            l3 = prev_close - range_val * 1.1 / 4
            l4 = prev_close - range_val * 1.1 / 2
            
            levels = {
                'h4': round(h4, 2), 'h3': round(h3, 2), 'h2': round(h2, 2), 'h1': round(h1, 2),
                'l1': round(l1, 2), 'l2': round(l2, 2), 'l3': round(l3, 2), 'l4': round(l4, 2),
                'prev_high': round(prev_high, 2),
                'prev_low': round(prev_low, 2),
                'prev_close': round(prev_close, 2),
                'range': round(range_val, 2)
            }
            
            # Cache for the day
            self._camarilla_cache[symbol] = levels
            logger.info(f"✅ Camarilla: {symbol} H4={h4:.2f}, L4={l4:.2f}, Range={range_val:.2f}")
            
            return levels
            
        except Exception as e:
            logger.debug(f"Camarilla calculation skipped for {symbol}: {e}")
            return {}
    
    def calculate_chart_based_levels(self, symbol: str, action: str, entry_price: float,
                                     symbol_data: Dict = None) -> Tuple[float, float]:
        """
        🎯 CALCULATE BOTH STOP LOSS AND TARGET USING CHART-BASED METHODS
        
        Returns: (stop_loss, target)
        
        This is the main method strategies should call for professional SL/Target calculation.
        """
        try:
            # Calculate chart-based stop loss
            stop_loss = self.calculate_chart_based_stop_loss(symbol, action, entry_price, symbol_data)
            
            # Calculate dynamic target based on the stop loss (maintains proper R:R)
            target = self.calculate_dynamic_target(entry_price, stop_loss)
            
            return stop_loss, target
            
        except Exception as e:
            logger.error(f"Chart-based levels calculation failed for {symbol}: {e}")
            # Fallback to reasonable intraday levels
            if action.upper() == 'BUY':
                return entry_price * 0.985, entry_price * 1.02
            else:
                return entry_price * 1.015, entry_price * 0.98
    
    def _calculate_adaptive_confidence_threshold(self, symbol: str, action: str, confidence: float, 
                                                    relative_strength: float = None) -> Tuple[float, str]:
        """
        🎯 RATIONAL CONFIDENCE THRESHOLD SYSTEM (Recalibrated 2025-12-26)
        
        DESIGN PRINCIPLES:
        1. BASE = 8.0 (clean, round number - requires 80% confidence minimum)
        2. PRIMARY adjustment: ONE scenario-based adjustment (-1.5 to +1.0)
        3. SECONDARY adjustments: Small bonuses, capped at ±0.5 total
        4. FINAL bounds: 7.0 to 9.0 (never too easy, never impossible)
        
        LOGIC:
        - With-trend in clear trend: EASIER (confidence boost = lower threshold)
        - Counter-trend: HARDER (need higher confidence)
        - Mean reversion at extremes: EASIER (good setups)
        - Choppy/unclear: SLIGHTLY HARDER (be selective)
        - Exceptional RS stocks: EASIER (strength/weakness is clear)
        
        Returns:
            (min_confidence_threshold, reason_string)
        """
        try:
            # ============= BASE THRESHOLD =============
            # 8.0 = 80% confidence minimum - professional standard
            BASE_THRESHOLD = 8.0
            min_conf = BASE_THRESHOLD
            reasons = []
            
            # ============= PRIMARY ADJUSTMENT: SCENARIO (only ONE applies) =============
            # This is the main driver - based on market structure
            primary_adj = 0.0
            scenario = None
            
            if hasattr(self, 'market_bias') and self.market_bias:
                current_bias = self.market_bias.current_bias
                bias_direction = getattr(current_bias, 'direction', 'NEUTRAL')
                scenario = getattr(self.market_bias, '_last_scenario', None)
                
                # Determine if signal is WITH or AGAINST the trend
                is_with_trend = (
                    (action.upper() == 'BUY' and bias_direction == 'BULLISH') or
                    (action.upper() == 'SELL' and bias_direction == 'BEARISH')
                )
            
            if scenario:
                # SCENARIO-BASED PRIMARY ADJUSTMENT
                # 🚨 2025-12-26: Counter-trend = 0 (neutral at 8.0), not penalized
                # With-trend gets bonus, counter-trend stays at base
                if scenario in ['GAP_UP_CONTINUATION', 'GAP_DOWN_CONTINUATION']:
                    # Strong trend - reward aligned, counter stays at base
                    primary_adj = -1.0 if is_with_trend else 0.0
                    reasons.append(f"TREND_CONT:{'WITH' if is_with_trend else 'COUNTER'}({primary_adj:+.1f})")
                
                elif scenario in ['FLAT_TRENDING_UP', 'FLAT_TRENDING_DOWN']:
                    # Mild trend - small adjustments
                    primary_adj = -0.5 if is_with_trend else 0.0
                    reasons.append(f"FLAT_TREND:{'WITH' if is_with_trend else 'COUNTER'}({primary_adj:+.1f})")
                
                elif scenario in ['GAP_UP_FADE', 'GAP_DOWN_RECOVERY']:
                    # Reversal scenario - counter-trend is actually WITH the reversal
                    primary_adj = -0.8 if not is_with_trend else 0.0
                    reasons.append(f"REVERSAL:{'FADE' if not is_with_trend else 'CHASE'}({primary_adj:+.1f})")
                
                elif scenario in ['RUBBER_BAND_RECOVERY', 'RUBBER_BAND_FADE']:
                    # Mean reversion at extremes - strong setup
                    primary_adj = -1.5 if not is_with_trend else 0.0
                    reasons.append(f"MEAN_REV:{'FADE' if not is_with_trend else 'CHASE'}({primary_adj:+.1f})")
                
                elif scenario == 'GAP_DOWN_EARLY_RECOVERY':
                    # Early recovery - favor buys
                    primary_adj = -1.0 if action.upper() == 'BUY' else 0.0
                    reasons.append(f"EARLY_RECOVERY({primary_adj:+.1f})")
                
                elif scenario in ['CHOPPY', 'MIXED_SIGNALS']:
                    # Uncertain - neutral
                    primary_adj = 0.0
                    reasons.append(f"CHOPPY({primary_adj:+.1f})")
                
                else:
                    # Unknown scenario - neutral
                    primary_adj = 0.0
            else:
                # No scenario - use basic trend alignment
                primary_adj = -0.3 if is_with_trend else 0.0
                reasons.append(f"BASIC:{'WITH' if is_with_trend else 'COUNTER'}({primary_adj:+.1f})")
            
            min_conf += primary_adj
            
            # ============= SECONDARY ADJUSTMENTS (capped at ±0.5 total) =============
            secondary_adj = 0.0
            
            # 1. Exceptional Relative Strength (±0.3)
            if relative_strength is not None:
                if action.upper() == 'BUY' and relative_strength > 5.0:
                    rs_bonus = min(0.3, relative_strength / 20.0)
                    secondary_adj -= rs_bonus
                    reasons.append(f"RS:+{relative_strength:.1f}%(-{rs_bonus:.1f})")
                elif action.upper() == 'SELL' and relative_strength < -5.0:
                    rs_bonus = min(0.3, abs(relative_strength) / 20.0)
                    secondary_adj -= rs_bonus
                    reasons.append(f"RS:{relative_strength:.1f}%(-{rs_bonus:.1f})")
            
            # 2. Market Regime (±0.2)
            if hasattr(self, 'market_bias') and self.market_bias:
                market_regime = getattr(self.market_bias.current_bias, 'market_regime', 'NORMAL')
                if market_regime in ['STRONG_TRENDING', 'TRENDING']:
                    secondary_adj -= 0.2
                    reasons.append("TRENDING(-0.2)")
                elif market_regime in ['CHOPPY', 'VOLATILE_CHOPPY']:
                    secondary_adj += 0.2
                    reasons.append("CHOPPY(+0.2)")
            
            # Cap secondary adjustments
            secondary_adj = max(-0.5, min(0.5, secondary_adj))
            min_conf += secondary_adj
            
            # ============= FINAL BOUNDS =============
            # 7.0 minimum = still need 70% confidence
            # 9.0 maximum = counter-trend in extreme case, not impossible
            min_conf = max(7.0, min(min_conf, 9.0))
            
            reason_str = f"BASE:{BASE_THRESHOLD}→{min_conf:.1f} | " + " | ".join(reasons) if reasons else f"BASE:{BASE_THRESHOLD}"
            return min_conf, reason_str
            
        except Exception as e:
            logger.error(f"Error calculating adaptive threshold: {e}")
            return 8.0, "error:default"
    
    def _get_nifty_data_from_bias(self) -> Optional[Dict]:
        """Get NIFTY data from market bias system"""
        try:
            if not (hasattr(self, 'market_bias') and self.market_bias):
                return None
            
            # Try to get NIFTY data from bias system's latest update
            if hasattr(self.market_bias, 'current_bias'):
                # The bias system stores NIFTY data internally
                # Check for various NIFTY representations
                for attr in ['nifty_data', '_nifty_data', 'latest_nifty_data']:
                    if hasattr(self.market_bias, attr):
                        data = getattr(self.market_bias, attr, None)
                        if data and isinstance(data, dict):
                            return data
            
            # Fallback: Try to access orchestrator's data
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, '_latest_market_data'):
                    for symbol in ['NIFTY-I', 'NIFTY', 'NIFTY 50']:
                        if symbol in orchestrator._latest_market_data:
                            return orchestrator._latest_market_data[symbol]
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get NIFTY data: {e}")
            return None
    
    def analyze_stock_dual_timeframe(self, symbol: str, stock_data: Dict) -> Dict:
        """
        DUAL-TIMEFRAME STOCK ANALYSIS (same as NIFTY logic)
        Analyzes BOTH day change (prev close → current) AND intraday change (open → current)
        
        Returns:
            Dict with: day_change_pct, intraday_change_pct, gap_pct, pattern, weighted_bias, alignment_with_market
        """
        try:
            ltp = float(stock_data.get('ltp', 0))
            if ltp <= 0:
                return {'error': 'Invalid LTP', 'weighted_bias': 0.0}
            
            # ============= CALCULATE DAY CHANGE (Previous Close → Current) =============
            day_change_pct = 0.0
            previous_close = float(stock_data.get('previous_close', 0))
            
            if previous_close > 0:
                day_change_pct = ((ltp - previous_close) / previous_close) * 100
            elif 'change_percent' in stock_data:
                day_change_pct = float(stock_data['change_percent'])
            
            # ============= CALCULATE INTRADAY CHANGE (Open → Current) =============
            intraday_change_pct = 0.0
            open_price = float(stock_data.get('open', 0))
            
            if open_price > 0:
                intraday_change_pct = ((ltp - open_price) / open_price) * 100
            
            # ============= DETECT GAP & REVERSAL PATTERNS =============
            gap_pct = 0.0
            if previous_close > 0 and open_price > 0:
                gap_pct = ((open_price - previous_close) / previous_close) * 100
            
            # Pattern detection
            pattern = self._detect_stock_pattern(day_change_pct, intraday_change_pct, gap_pct)
            
            # ============= CALCULATE WEIGHTED BIAS =============
            # Day change = 60% weight (overall trend)
            # Intraday change = 40% weight (current momentum)
            weighted_bias = (day_change_pct * 0.6) + (intraday_change_pct * 0.4)
            
            # ============= ALIGN WITH MARKET (NIFTY) BIAS =============
            # Check if stock is moving with or against overall market
            alignment = "UNKNOWN"
            if hasattr(self, 'market_bias') and hasattr(self.market_bias, 'nifty_data'):
                nifty_weighted = self.market_bias.nifty_data.get('weighted_bias', 0)
                
                # Both positive = WITH market
                if weighted_bias > 0.1 and nifty_weighted > 0.1:
                    alignment = "WITH MARKET (BULL)"
                # Both negative = WITH market
                elif weighted_bias < -0.1 and nifty_weighted < -0.1:
                    alignment = "WITH MARKET (BEAR)"
                # Stock bullish, market bearish = AGAINST
                elif weighted_bias > 0.1 and nifty_weighted < -0.1:
                    alignment = "AGAINST MARKET (RELATIVE STRENGTH)"
                # Stock bearish, market bullish = AGAINST
                elif weighted_bias < -0.1 and nifty_weighted > 0.1:
                    alignment = "AGAINST MARKET (RELATIVE WEAKNESS)"
                else:
                    alignment = "NEUTRAL"
            
            result = {
                'symbol': symbol,
                'ltp': ltp,
                'previous_close': previous_close,
                'open': open_price,
                'day_change_pct': day_change_pct,
                'intraday_change_pct': intraday_change_pct,
                'gap_pct': gap_pct,
                'pattern': pattern,
                'weighted_bias': weighted_bias,
                'alignment': alignment
            }
            
            # Log for significant stocks/movements
            if abs(weighted_bias) > 0.5 or abs(gap_pct) > 0.5:
                logger.info(
                    f"📊 {symbol} DUAL-TIMEFRAME:\n"
                    f"   LTP: ₹{ltp:.2f} | Prev: ₹{previous_close:.2f} | Open: ₹{open_price:.2f}\n"
                    f"   📈 Day: {day_change_pct:+.2f}% | ⚡ Intraday: {intraday_change_pct:+.2f}% | 🎯 Gap: {gap_pct:+.2f}%\n"
                    f"   🔍 Pattern: {pattern} | ⚖️  Weighted: {weighted_bias:+.2f}%\n"
                    f"   🌍 Market Alignment: {alignment}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} dual-timeframe: {e}")
            return {'error': str(e), 'weighted_bias': 0.0}
    
    def _detect_stock_pattern(self, day_change: float, intraday_change: float, gap_pct: float) -> str:
        """
        Detect stock patterns based on day vs intraday movement
        Same logic as NIFTY pattern detection
        """
        try:
            # Both positive = Bullish continuation
            if day_change > 0.3 and intraday_change > 0.2:
                return "BULLISH CONTINUATION"
            
            # Both negative = Bearish continuation
            if day_change < -0.3 and intraday_change < -0.2:
                return "BEARISH CONTINUATION"
            
            # Gap down but recovering = Potential reversal
            if gap_pct < -0.5 and intraday_change > 0.3:
                recovery_pct = abs(intraday_change / gap_pct) * 100 if gap_pct != 0 else 0
                return f"GAP DOWN RECOVERY ({recovery_pct:.0f}%)"
            
            # Gap up but fading = Weakness
            if gap_pct > 0.5 and intraday_change < -0.3:
                fade_pct = abs(intraday_change / gap_pct) * 100 if gap_pct != 0 else 0
                return f"GAP UP FADE ({fade_pct:.0f}%)"
            
            # Day bearish but intraday bullish = Intraday reversal
            if day_change < -0.3 and intraday_change > 0.2:
                return "INTRADAY REVERSAL (BULL)"
            
            # Day bullish but intraday bearish = Losing momentum
            if day_change > 0.3 and intraday_change < -0.2:
                return "INTRADAY WEAKNESS"
            
            # Low movement = Choppy
            if abs(day_change) < 0.2 and abs(intraday_change) < 0.2:
                return "CHOPPY/RANGE"
            
            # Default
            return "MIXED"
            
        except Exception as e:
            logger.error(f"Error detecting stock pattern: {e}")
            return "UNKNOWN"
    
    def validate_signal_levels(self, entry_price: float, stop_loss: float, 
                              target: float, action: str) -> bool:
        """Validate that signal levels make logical sense"""
        try:
            # Normalize numeric types to avoid '<' between str and int/float errors
            entry_price = float(entry_price)
            stop_loss = float(stop_loss)
            target = float(target)
            if action.upper() == 'BUY':
                # For BUY: stop_loss < entry_price < target
                if not (stop_loss < entry_price < target):
                    logger.warning(f"❌ Invalid BUY signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
                
                # 🔥 ENHANCED: Percentage-based minimum spreads (protects against order rejections)
                sl_spread_pct = ((entry_price - stop_loss) / entry_price) * 100
                target_spread_pct = ((target - entry_price) / entry_price) * 100
                
                # Define minimums based on price band
                if entry_price >= 1000:
                    MIN_SL_SPREAD = 0.3  # 0.3% for high-priced stocks
                    MIN_TARGET_SPREAD = 0.5  # 0.5% minimum target
                elif entry_price >= 100:
                    MIN_SL_SPREAD = 0.4  # 0.4% for mid-priced
                    MIN_TARGET_SPREAD = 0.6  # 0.6% minimum target
                elif entry_price >= 10:
                    MIN_SL_SPREAD = 0.5  # 0.5% for low-priced
                    MIN_TARGET_SPREAD = 0.8  # 0.8% minimum target
                else:
                    # Options/Ultra-low: Use absolute ₹0.10 minimum
                    MIN_SL_SPREAD = (0.10 / entry_price) * 100
                    MIN_TARGET_SPREAD = (0.15 / entry_price) * 100
                
                if sl_spread_pct < MIN_SL_SPREAD:
                    logger.warning(f"❌ BUY: SL too close to entry: {sl_spread_pct:.2f}% < {MIN_SL_SPREAD:.2f}% "
                                 f"(SL={stop_loss:.2f}, Entry={entry_price:.2f})")
                    return False
                
                if target_spread_pct < MIN_TARGET_SPREAD:
                    logger.warning(f"❌ BUY: Target too close to entry: {target_spread_pct:.2f}% < {MIN_TARGET_SPREAD:.2f}% "
                                 f"(Entry={entry_price:.2f}, Target={target:.2f})")
                    return False
            else:  # SELL
                # For SELL: target < entry_price < stop_loss
                if not (target < entry_price < stop_loss):
                    logger.warning(f"❌ Invalid SELL signal levels: Target={target}, Entry={entry_price}, SL={stop_loss}")
                    return False
                
                # 🔥 ENHANCED: Percentage-based minimum spreads
                sl_spread_pct = ((stop_loss - entry_price) / entry_price) * 100
                target_spread_pct = ((entry_price - target) / entry_price) * 100
                
                # Define minimums based on price band
                if entry_price >= 1000:
                    MIN_SL_SPREAD = 0.3  # 0.3% for high-priced stocks
                    MIN_TARGET_SPREAD = 0.5  # 0.5% minimum target
                elif entry_price >= 100:
                    MIN_SL_SPREAD = 0.4  # 0.4% for mid-priced
                    MIN_TARGET_SPREAD = 0.6  # 0.6% minimum target
                elif entry_price >= 10:
                    MIN_SL_SPREAD = 0.5  # 0.5% for low-priced
                    MIN_TARGET_SPREAD = 0.8  # 0.8% minimum target
                else:
                    # Options/Ultra-low: Use absolute ₹0.10 minimum
                    MIN_SL_SPREAD = (0.10 / entry_price) * 100
                    MIN_TARGET_SPREAD = (0.15 / entry_price) * 100
                
                if sl_spread_pct < MIN_SL_SPREAD:
                    logger.warning(f"❌ SELL: SL too close to entry: {sl_spread_pct:.2f}% < {MIN_SL_SPREAD:.2f}% "
                                 f"(Entry={entry_price:.2f}, SL={stop_loss:.2f})")
                    return False
                
                if target_spread_pct < MIN_TARGET_SPREAD:
                    logger.warning(f"❌ SELL: Target too close to entry: {target_spread_pct:.2f}% < {MIN_TARGET_SPREAD:.2f}% "
                                 f"(Target={target:.2f}, Entry={entry_price:.2f})")
                    return False
            
            # Check for identical levels (problematic for low-priced stocks)
            if entry_price == stop_loss == target:
                logger.warning(f"Invalid signal levels: All levels identical ({entry_price}) - likely rounding issue for low-priced stock")
                return False
            
            # Check risk/reward ratio is reasonable (>= ~0.45:1 to 5:1)
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            
            if risk <= 0:
                logger.warning(f"Zero or negative risk: {risk}")
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 0.45 or risk_reward_ratio > 5.0:
                logger.warning(f"Unreasonable risk/reward ratio: {risk_reward_ratio}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal levels: {e}")
            return False
    
    async def create_standard_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, 
                              metadata: Dict, market_bias=None, market_data: Dict = None) -> Optional[Dict]:
        """Create standardized signal format - SUPPORTS EQUITY, FUTURES & OPTIONS"""
        try:
            # 🔧 TIME RESTRICTIONS MOVED TO RISK MANAGER
            # Strategies should always generate signals for analysis
            # Risk Manager will reject orders based on time restrictions
            
            # 🎯 DIRECTIONAL ACTION: For options, adjust based on PUT/CALL
            # PUT options profit from FALLING → directional action = SELL
            # CALL options profit from RISING → directional action = BUY
            # This is used throughout for directional checks (RS, bias, Camarilla, etc.)
            directional_action = action.upper()
            option_type = metadata.get('option_type', '') if metadata else ''
            if option_type == 'PE':  # PUT option
                directional_action = 'SELL'
            elif option_type == 'CE':  # CALL option
                directional_action = 'BUY'
            
            # 🎯 RELATIVE STRENGTH CHECK: Stock must outperform/underperform market
            # Use provided market_data or fall back to stored latest data
            data_to_use = market_data if market_data else self._latest_market_data
            
            # 🔥 EXCEPTIONAL RS TRACKING - Used for bias filter bypass
            exceptional_rs = False
            exceptional_rs_value = 0.0
            
            if market_bias and data_to_use:
                # Get NIFTY change percent from market bias
                nifty_change = getattr(getattr(market_bias, 'current_bias', None), 'nifty_momentum', None)
                
                # Get stock change percent from market data
                stock_change = None
                if symbol in data_to_use:
                    stock_data = data_to_use[symbol]
                    stock_change = stock_data.get('change_percent') or stock_data.get('provider_change_percent')
                    if stock_change is not None:
                        stock_change = float(stock_change)
                
                # Perform relative strength check
                if nifty_change is not None and stock_change is not None:
                    # 🔥 CALCULATE RELATIVE STRENGTH
                    relative_strength = stock_change - nifty_change
                    exceptional_rs_value = relative_strength
                    
                    # 🔥 EXCEPTIONAL RS DETECTION - Stock significantly outperforming/underperforming market
                    # 🔧 FIX: Use directional_action for options (PUT=SELL, CALL=BUY)
                    EXCEPTIONAL_RS_THRESHOLD = 5.0  # 5% is exceptional
                    
                    if directional_action == 'BUY' and relative_strength > EXCEPTIONAL_RS_THRESHOLD:
                        exceptional_rs = True
                        logger.info(f"🌟 EXCEPTIONAL RS DETECTED: {symbol} +{relative_strength:.2f}% vs NIFTY - "
                                   f"May bypass bias filter for strong momentum play!")
                    elif directional_action == 'SELL' and relative_strength < -EXCEPTIONAL_RS_THRESHOLD:
                        exceptional_rs = True
                        logger.info(f"🌟 EXCEPTIONAL WEAKNESS DETECTED: {symbol} {relative_strength:.2f}% vs NIFTY - "
                                   f"May bypass bias filter for weak stock short!")
                    
                    # 🔥 HARD BLOCK: Don't buy RED stocks in GREEN market (and vice versa)
                    # 🔧 FIX: Use directional_action for options
                    # This was causing JSWENERGY loss - bought a down stock in up market
                    if directional_action == 'BUY' and stock_change < 0 and nifty_change > 0.2:
                        logger.warning(f"🚫 HARD BLOCK: {symbol} BUY rejected - Stock DOWN ({stock_change:+.2f}%) in UP market (NIFTY {nifty_change:+.2f}%)")
                        return None
                    elif directional_action == 'SELL' and stock_change > 0 and nifty_change < -0.2:
                        logger.warning(f"🚫 HARD BLOCK: {symbol} SELL rejected - Stock UP ({stock_change:+.2f}%) in DOWN market (NIFTY {nifty_change:+.2f}%)")
                        return None
                    
                    # 🔥 STRICT RELATIVE STRENGTH: Don't buy weak stocks in bull market!
                    # Increased from 0.3% to 0.5% minimum outperformance
                    MIN_OUTPERFORMANCE = 0.5  # Stock must beat NIFTY by at least 0.5%
                    
                    # 🔧 Use directional_action which handles PUT=SELL, CALL=BUY
                    rs_allowed, rs_reason = self.check_relative_strength(
                        symbol=symbol,
                        action=directional_action,  # Use directional_action for options
                        stock_change_percent=stock_change,
                        nifty_change_percent=nifty_change,
                        min_outperformance=MIN_OUTPERFORMANCE
                    )
                    
                    if not rs_allowed:
                        logger.info(f"🚫 RELATIVE STRENGTH FILTER: {symbol} {directional_action} rejected - {rs_reason}")
                        return None
            
            # 🎯 MARKET BIAS COORDINATION: Filter signals based on market direction
            if market_bias:
                # CRITICAL FIX: Normalize confidence to 0-10 scale
                # Some strategies use percentage (0-100), others use decimal (0-10)
                if confidence > 10:
                    # It's a percentage, convert to 0-10 scale
                    normalized_confidence = confidence / 10.0
                    logger.debug(f"📊 Confidence normalization for {symbol}: {confidence}% → {normalized_confidence}/10")
                else:
                    # Already in 0-10 scale
                    normalized_confidence = confidence
                    logger.debug(f"📊 Confidence for {symbol} already normalized: {normalized_confidence}/10")
                
                # Use the new clearer method if available
                if hasattr(market_bias, 'should_allow_signal'):
                    # 🔥 COUNTER-TREND SUPPORT: Pass micro indicators for counter-trend validation
                    # Extract micro indicators from metadata for intraday scalping decisions
                    micro_indicators = None
                    if metadata:
                        micro_indicators = {
                            'rsi': metadata.get('rsi', metadata.get('fast_rsi', 50)),
                            'bollinger_squeeze': metadata.get('bollinger_squeeze', False),
                            'bollinger_position': metadata.get('bollinger_position', 'middle'),
                            'stoch_rsi': metadata.get('stoch_rsi', 0.5),
                            'vwap_deviation': metadata.get('vwap_deviation', 0),
                        }
                    
                    # Get stock change percent from market data for relative strength
                    stock_change = None
                    if market_data and symbol in market_data:
                        stock_data = market_data.get(symbol, {})
                        stock_change = stock_data.get('change_percent', stock_data.get('day_change_percent'))
                    
                    # 🔧 Use directional_action which handles PUT=SELL, CALL=BUY
                    should_allow = market_bias.should_allow_signal(
                        directional_action,  # Use directional_action for options
                        normalized_confidence,
                        symbol=symbol,
                        stock_change_percent=stock_change,
                        micro_indicators=micro_indicators
                    )
                else:
                    # Fallback: if no bias method available, BLOCK signal (quality over quantity)
                    should_allow = False
                    logger.warning(f"🚫 BLOCKED: Market bias object missing should_allow_signal method - rejecting {symbol} {action}")
                
                # 🚫 EXCEPTIONAL RS OVERRIDE DISABLED - Quality over quantity
                # Previously allowed trades against bias, causing losses
                # Now: If bias says NO, we respect it. Period.
                if not should_allow and exceptional_rs:
                    logger.info(f"🚫 RS OVERRIDE BLOCKED: {symbol} {action} has exceptional RS but bias says NO - Respecting bias filter")
                    metadata['exceptional_rs_blocked'] = True
                    metadata['relative_strength'] = exceptional_rs_value
                
                if not should_allow:
                    # 🔧 FIX: Log directional_action for options (PUT shows as SELL, CALL as BUY)
                    logger.info(f"🚫 BIAS FILTER: {symbol} {directional_action} rejected by market bias "
                               f"(Bias: {getattr(market_bias.current_bias, 'direction', 'UNKNOWN')}, "
                               f"Raw Confidence: {confidence}, Normalized: {normalized_confidence:.1f}/10)")
                    return None
                else:
                    # Apply position size multiplier ONLY when aligned with current bias
                    try:
                        current_bias_dir = getattr(getattr(market_bias, 'current_bias', None), 'direction', 'NEUTRAL')
                        # 🔧 Use directional_action for options (PUT = SELL direction, CALL = BUY)
                        is_aligned = (
                            (current_bias_dir == 'BULLISH' and directional_action == 'BUY') or
                            (current_bias_dir == 'BEARISH' and directional_action == 'SELL')
                        )
                    except Exception:
                        current_bias_dir = 'NEUTRAL'
                        is_aligned = False

                    if is_aligned and hasattr(market_bias, 'get_position_size_multiplier'):
                        # Micro-size in CHOPPY regimes even when aligned
                        # 🔧 FIX: Use directional_action for options (PUT=SELL, CALL=BUY)
                        bias_multiplier = market_bias.get_position_size_multiplier(directional_action)
                        try:
                            regime = getattr(getattr(market_bias, 'current_bias', None), 'market_regime', 'NORMAL')
                            if regime in ('CHOPPY', 'VOLATILE_CHOPPY'):
                                bias_multiplier = min(bias_multiplier, 1.0)
                        except Exception:
                            pass
                        metadata['bias_multiplier'] = bias_multiplier
                        if bias_multiplier > 1.0:
                            # 🔧 FIX: Log directional_action which shows true intent (PUT=SELL, CALL=BUY)
                            logger.info(f"🔥 BIAS BOOST: {symbol} {directional_action} gets {bias_multiplier:.1f}x position size")
                        elif bias_multiplier < 1.0:
                            logger.info(f"⚠️ BIAS REDUCE: {symbol} {directional_action} gets {bias_multiplier:.1f}x position size")
                    else:
                        metadata['bias_multiplier'] = 1.0
            
            # ============================================================
            # 📊 CAMARILLA SIGNAL FILTER (Professional Risk Management)
            # ============================================================
            # Block signals that violate Camarilla pivot structure
            # 🔧 FIX: Use directional_action for options (PUT=SELL, CALL=BUY)
            try:
                if camarilla_signal:
                    # REJECT BUY signals in risky zones
                    if directional_action == 'BUY':
                        if camarilla_signal == "BREAKDOWN_ZONE":
                            logger.warning(f"🚫 CAMARILLA FILTER: {symbol} BUY blocked - Below L4 breakdown")
                            return None
                        elif camarilla_signal == "RESISTANCE_ZONE" and confidence < 9.0:
                            logger.warning(f"🚫 CAMARILLA FILTER: {symbol} BUY blocked - Near H3 resistance (conf={confidence:.1f})")
                            return None
                    
                    # REJECT SELL signals in risky zones
                    elif directional_action == 'SELL':
                        if camarilla_signal == "BREAKOUT_ZONE":
                            logger.warning(f"🚫 CAMARILLA FILTER: {symbol} SELL blocked - Above H4 breakout")
                            return None
                        elif camarilla_signal == "SUPPORT_ZONE" and confidence < 9.0:
                            logger.warning(f"🚫 CAMARILLA FILTER: {symbol} SELL blocked - Near L3 support (conf={confidence:.1f})")
                            return None
                    
                    # BOOST confidence for confirmed breakouts/breakdowns
                    if camarilla_signal == "BREAKOUT_CONFIRMED" and directional_action == 'BUY':
                        metadata['camarilla_boost'] = True
                        logger.info(f"🚀 CAMARILLA BOOST: {symbol} BUY breakout above H4")
                    elif camarilla_signal == "BREAKDOWN_CONFIRMED" and directional_action == 'SELL':
                        metadata['camarilla_boost'] = True
                        logger.info(f"📉 CAMARILLA BOOST: {symbol} SELL breakdown below L4")
            except Exception as cam_filter_err:
                logger.debug(f"Camarilla filter skipped: {cam_filter_err}")

            # CRITICAL FIX: Type validation to prevent float/string arithmetic errors
            try:
                entry_price = float(entry_price) if entry_price not in [None, '', 'N/A', '-'] else 0.0
                stop_loss = float(stop_loss) if stop_loss not in [None, '', 'N/A', '-'] else 0.0
                target = float(target) if target not in [None, '', 'N/A', '-'] else 0.0
                confidence = float(confidence) if confidence not in [None, '', 'N/A', '-'] else 0.0
            except (ValueError, TypeError) as type_error:
                logger.error(f"❌ TYPE ERROR for {symbol}: Invalid numeric data - {type_error}")
                logger.error(f"   entry_price: {repr(entry_price)}, stop_loss: {repr(stop_loss)}, "
                            f"target: {repr(target)}, confidence: {repr(confidence)}")
                return None
            
            # Validate numeric ranges
            if entry_price <= 0:
                logger.error(f"❌ INVALID ENTRY PRICE for {symbol}: {entry_price} - REJECTING SIGNAL")
                logger.error(f"   This will cause quantity = 0 and signal rejection")
                return None
            # ========================================
            # 🚫 MAX CONCURRENT POSITIONS CHECK - DISABLED
            # ========================================
            # User preference: Quality over quantity, not arbitrary caps
            # Let risk management and capital constraints handle this naturally
            MAX_CONCURRENT_POSITIONS = 50  # Effectively no limit - quality filters should do the job
            
            is_management = metadata.get('management_action', False)
            is_closing = metadata.get('closing_action', False)
            bypass_checks = metadata.get('bypass_all_checks', False)
            
            if not (is_management or is_closing or bypass_checks):
                # Count current open positions
                current_position_count = len(self.active_positions)
                
                # Also check Zerodha positions
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        zerodha_positions = await orchestrator.zerodha_client.get_positions()
                        if zerodha_positions:
                            real_positions = [p for p in zerodha_positions if p.get('quantity', 0) != 0]
                            current_position_count = max(current_position_count, len(real_positions))
                except:
                    pass
                
                if current_position_count >= MAX_CONCURRENT_POSITIONS:
                    logger.warning(f"🚫 MAX POSITIONS REACHED: {current_position_count}/{MAX_CONCURRENT_POSITIONS} - Blocking {symbol} {action}")
                    return None
            
            # ========================================
            # CRITICAL: POSITION DEDUPLICATION CHECK
            # 🔧 2025-12-29: Pass action to detect REVERSAL signals
            # SELL signal on LONG position = EXIT, not duplicate!
            # 🔧 2025-12-29 v2: Pass option_type for correct direction calculation
            # BUY PUT on LONG = REVERSAL (allow), BUY CALL on LONG = DUPLICATE (block)
            # ========================================
            if not (is_management or is_closing or bypass_checks):
                signal_option_type = metadata.get('option_type', '') if metadata else ''
                if self.has_existing_position(symbol, action, signal_option_type):
                    logger.info(f"🚫 {self.name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
                    return None
            
            # ========================================
            # CRITICAL: PHANTOM POSITION COOLDOWN CHECK  
            # ========================================
            if self._is_position_cooldown_active(symbol):
                logger.info(f"🕐 {self.name}: SIGNAL DELAYED for {symbol} - Position cooldown active")
                return None
            
            # ========================================
            # 🔥 PROFESSIONAL MEAN REVERSION-AWARE CONFIDENCE THRESHOLD
            # ========================================
            # Multi-indicator system prevents chasing exhausted moves (150+ points)
            # 🔥 Pass exceptional_rs_value to give bonus for exceptional RS stocks
            min_conf, adjustment_reason = self._calculate_adaptive_confidence_threshold(
                symbol, action, confidence, relative_strength=exceptional_rs_value
            )
            logger.debug(f"📊 Adaptive Threshold: {symbol} {action} -> min_conf={min_conf:.1f} ({adjustment_reason})")

            # Ensure confidence is numeric before comparison
            try:
                if not isinstance(confidence, (int, float)):
                    logger.error(f"❌ CONFIDENCE TYPE ERROR for {symbol}: confidence is {type(confidence)} = {repr(confidence)}")
                    confidence = float(confidence) if confidence else 0.0
                
                # CRITICAL FIX: Normalize confidence to 0-10 scale for comparison with min_conf
                # Strategies generate confidence in 0-1 scale (0.9 = 90%)
                # min_conf is in 0-10 scale (8.5 = 85%)
                confidence_normalized = confidence * 10.0 if confidence <= 1.0 else confidence
                
                if confidence_normalized < min_conf:
                    logger.info(f"🗑️ {self.name}: LOW CONFIDENCE SIGNAL SCRAPPED for {symbol} - Confidence: {confidence_normalized:.1f}/10 (min={min_conf})")
                    return None
                else:
                    logger.debug(f"✅ Confidence check passed: {symbol} - {confidence_normalized:.1f}/10 >= {min_conf}")
            except (TypeError, ValueError) as e:
                logger.error(f"❌ Error comparing confidence for {symbol}: {e}")
                logger.error(f"   confidence={repr(confidence)}, min_conf={repr(min_conf)}")
                return None

            # Opening gap gate: DISABLED - market_data not available in this context
            # TODO: Move this check to risk manager or pass market_data to this method
            
            # 🎯 INTELLIGENT SIGNAL TYPE SELECTION based on market conditions and symbol
            # Ensure numeric types for decision helpers
            try:
                _entry_price_num = float(entry_price)
            except (TypeError, ValueError):
                _entry_price_num = 0.0
            try:
                _confidence_num = float(confidence)
            except (TypeError, ValueError):
                _confidence_num = 0.0

            signal_type = self._determine_optimal_signal_type(symbol, _entry_price_num, _confidence_num, metadata)
            
            # 📊 Pre-fetch Camarilla levels for this symbol (cached daily for all signal types)
            try:
                await self._get_camarilla_levels(symbol)
            except Exception as cam_err:
                logger.debug(f"Camarilla prefetch skipped: {cam_err}")
            
            if signal_type == 'OPTIONS':
                # Convert to options signal
                return await self._create_options_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            elif signal_type == 'FUTURES':
                # Create futures signal (if available)
                return self._create_futures_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            else:
                # Create equity signal (default)
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
                
        except Exception as e:
            logger.error(f"Error creating signal for {symbol}: {e}")
            return None
    
    def _determine_optimal_signal_type(self, symbol: str, entry_price: float, confidence: float, metadata: Dict) -> str:
        """
        Determine the best signal type based on market conditions and F&O availability.
        
        INSTRUMENT SELECTION PRIORITY (for F&O enabled symbols):
        1. INDEX trades → OPTIONS (NIFTY, BANKNIFTY, etc.)
        2. FUTURES → 85%+ confidence (leveraged equity exposure)
        3. OPTIONS → 90%+ confidence (higher risk, higher reward)
        4. EQUITY → Below 85% confidence (safest)
        """
        try:
            # 🚨 CRITICAL FIX: Normalize confidence to 0-1 scale
            # Strategies send 0-10 scale, we need 0-1 for thresholds
            if confidence > 1.0:
                normalized_confidence = confidence / 10.0
                logger.debug(f"📊 Normalizing confidence: {confidence:.2f} → {normalized_confidence:.2f}")
            else:
                normalized_confidence = confidence
            
            # 🚨 CRITICAL: Check F&O availability first
            from config.truedata_symbols import is_fo_enabled, should_use_equity_only
            
            # DEBUG: Log F&O check details
            fo_enabled = is_fo_enabled(symbol)
            equity_only = should_use_equity_only(symbol)
            logger.info(f"🔍 F&O CHECK for {symbol}: fo_enabled={fo_enabled}, equity_only={equity_only}")
            
            # 🔧 CRITICAL: Define option_type at start to avoid undefined variable error
            option_type = metadata.get('option_type', '') if metadata else ''
            logger.debug(f"   Strategy instance: {self.name}, Signal ID: {getattr(metadata, 'get', lambda x: 'unknown')('signal_id', 'unknown')}")
            
            # CRITICAL DEBUG: For problematic symbols, add extra validation
            if symbol in ['FORCEMOT', 'RCOM', 'DEVYANI', 'RAYMOND', 'ASTRAL', 'IDEA']:
                logger.info(f"🔍 PROBLEMATIC SYMBOL DEBUG: {symbol} - F&O={fo_enabled}, Equity_Only={equity_only}")
            
            # HARD RULE: Avoid options for very low-priced stocks (illiquid contracts)
            if entry_price and entry_price < 50:
                logger.info(f"🎯 LOW PRICE EQUITY-ONLY: {symbol} @ ₹{entry_price:.2f} → EQUITY (avoid illiquid options)")
                return 'EQUITY'

            # Force equity for known cash-only stocks
            if equity_only:
                # 🎯 CRITICAL FIX: Adjust action based on original option intent
                option_type = metadata.get('option_type', '')
                if option_type == 'PE':  # PUT option = bearish intent
                    metadata['action'] = 'SELL'
                    logger.info(f"🎯 CASH-ONLY STOCK: {symbol} → EQUITY SELL (PUT intent, no F&O)")
                elif option_type == 'CE':  # CALL option = bullish intent
                    metadata['action'] = 'BUY'
                    logger.info(f"🎯 CASH-ONLY STOCK: {symbol} → EQUITY BUY (CALL intent, no F&O)")
                else:
                    logger.info(f"🎯 CASH-ONLY STOCK: {symbol} → EQUITY (no F&O available)")
                return 'EQUITY'
            
            # Check if F&O is available for this symbol
            if not fo_enabled:
                # 🎯 CRITICAL FIX: Adjust action based on original option intent
                option_type = metadata.get('option_type', '')
                if option_type == 'PE':  # PUT option = bearish intent
                    metadata['action'] = 'SELL'
                    logger.info(f"🎯 NO F&O AVAILABLE: {symbol} → EQUITY SELL (PUT intent)")
                elif option_type == 'CE':  # CALL option = bullish intent
                    metadata['action'] = 'BUY'
                    logger.info(f"🎯 NO F&O AVAILABLE: {symbol} → EQUITY BUY (CALL intent)")
                else:
                    logger.info(f"🎯 NO F&O AVAILABLE: {symbol} → EQUITY (no options trading)")
                return 'EQUITY'
            
            # ========== F&O ENABLED SYMBOLS - INSTRUMENT SELECTION ==========
            
            # Factors for signal type selection
            is_index = symbol.endswith('-I') or symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
            is_scalping = metadata.get('risk_type', '').startswith('SCALPING')
            volatility_score = metadata.get('volume_score', 0)
            signal_type = metadata.get('signal_type', '')
            
            # 🎯 CONFIDENCE THRESHOLDS (RELAXED for more F&O trades)
            # Futures: 85%+ (leveraged equity, simpler than options)
            # Options: 90%+ (complex Greeks, time decay)
            FUTURES_THRESHOLD = 0.85  # 85% confidence for futures
            OPTIONS_THRESHOLD = 0.90  # 90% confidence for options
            HIGH_VOL_OPTIONS_THRESHOLD = 0.85  # Lower for high volatility setups
            
            # 1. INDEX SYMBOLS → Always OPTIONS (most liquid)
            if is_index:
                logger.info(f"🎯 INDEX SIGNAL: {symbol} → OPTIONS (index always uses options)")
                return 'OPTIONS'
            
            # 2. ELITE CONFIDENCE (90%+) → OPTIONS
            # High edge = options leverage makes sense
            if normalized_confidence >= OPTIONS_THRESHOLD:
                logger.info(f"🎯 ELITE CONFIDENCE: {symbol} → OPTIONS (conf={normalized_confidence:.2f} ≥ {OPTIONS_THRESHOLD})")
                return 'OPTIONS'
            
            # 3. HIGH VOLATILITY + 85%+ → OPTIONS
            # Volatility = premium expansion opportunity
            if volatility_score >= 0.80 and normalized_confidence >= HIGH_VOL_OPTIONS_THRESHOLD:
                logger.info(f"🎯 HIGH VOL + STRONG CONF: {symbol} → OPTIONS (vol={volatility_score:.2f}, conf={normalized_confidence:.2f})")
                return 'OPTIONS'
            
            # 4. GOOD CONFIDENCE (85%+) → FUTURES
            # Futures = leveraged equity exposure without Greeks complexity
            # Better than equity for intraday with decent confidence
            if normalized_confidence >= FUTURES_THRESHOLD:
                logger.info(f"🎯 FUTURES TRADE: {symbol} → FUTURES (conf={normalized_confidence:.2f} ≥ {FUTURES_THRESHOLD})")
                return 'FUTURES'
            
            # 5. MODERATE CONFIDENCE (80-85%) → EQUITY with leverage (MIS)
            # Can still use intraday leverage but in cash segment
            if normalized_confidence >= 0.80:
                # 🔧 CRITICAL: Correct action for PUT/CALL intent
                if option_type == 'PE':
                    metadata['action'] = 'SELL'
                    logger.info(f"🎯 LEVERAGED EQUITY: {symbol} → EQUITY SELL (PUT intent, MIS) (conf={normalized_confidence:.2f} ≥ 0.80)")
                elif option_type == 'CE':
                    metadata['action'] = 'BUY'
                    logger.info(f"🎯 LEVERAGED EQUITY: {symbol} → EQUITY BUY (CALL intent, MIS) (conf={normalized_confidence:.2f} ≥ 0.80)")
                else:
                logger.info(f"🎯 LEVERAGED EQUITY: {symbol} → EQUITY (MIS) (conf={normalized_confidence:.2f} ≥ 0.80)")
                return 'EQUITY'
            
            # 6. LOWER CONFIDENCE (<80%) → EQUITY (safer)
            # Don't use leverage for weaker signals
            else:
                # 🔧 CRITICAL: Correct action for PUT/CALL intent
                if option_type == 'PE':
                    metadata['action'] = 'SELL'
                    logger.info(f"🎯 CONSERVATIVE: {symbol} → EQUITY SELL (PUT intent) (conf={normalized_confidence:.2f} < 0.80)")
                elif option_type == 'CE':
                    metadata['action'] = 'BUY'
                    logger.info(f"🎯 CONSERVATIVE: {symbol} → EQUITY BUY (CALL intent) (conf={normalized_confidence:.2f} < 0.80)")
            else:
                logger.info(f"🎯 CONSERVATIVE: {symbol} → EQUITY (conf={normalized_confidence:.2f} < 0.80)")
                return 'EQUITY'
                
        except Exception as e:
            logger.error(f"Error determining signal type: {e}")
            return 'EQUITY'  # Safest fallback
    
    async def _create_options_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Dict:
        """Create standardized signal format for options"""
        try:
            # ✅ OPTIONS TRADING RE-ENABLED (Dec 18, 2024)
            # Fixes implemented:
            # 1. All strikes of same underlying+type = ONE position (no duplicates)
            # 2. Auto square-off opposite side (CE→PE or PE→CE)
            # 3. Pending order tracking (block duplicates, cancel stale after 15 min)
            # 4. IV filter, momentum confirmation, Greeks check, trend strength filter
            # 5. Tighter stop losses and faster profit booking for options
            
            # If outside options trading hours, skip (stricter cutoff to avoid theta decay)
            if not self._is_options_trading_hours():
                logger.warning(f"⏸️ OPTIONS HOURS CLOSED - Skipping options signal for {symbol}")
                return None
            
            # 🚨 FIX #1: TIME-BASED FILTER - No new options after 2:30 PM (theta acceleration)
            from datetime import datetime
            current_time = datetime.now()
            # FIXED: block if hour > 14 (3pm+) OR if exactly 2:30pm+
            if current_time.hour > 14 or (current_time.hour == 14 and current_time.minute >= 30):
                logger.warning(f"⏰ OPTIONS CUTOFF: {symbol} - No new options after 2:30 PM (theta decay risk)")
                logger.info(f"   💡 Falling back to equity signal instead")
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            
            # 🚨 FIX #2: IV FILTER - Don't buy expensive options (high IV = expensive = likely to lose)
            try:
                iv_rank = await self._get_iv_rank(symbol)
                if iv_rank and iv_rank > 50:
                    logger.warning(f"📈 HIGH IV REJECTED: {symbol} IV Rank {iv_rank:.0f}% > 50% - Options too expensive")
                    logger.info(f"   💡 Falling back to equity signal (cheaper, no theta decay)")
                    return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            except Exception as iv_err:
                logger.debug(f"IV check skipped for {symbol}: {iv_err}")
            
            # 🚨 FIX #3: EXPIRY CHECK - Avoid options with < 3 days to expiry (fast decay)
            try:
                days_to_expiry = await self._get_days_to_expiry(symbol)
                if days_to_expiry is not None and days_to_expiry < 3:
                    logger.warning(f"⏳ SHORT EXPIRY REJECTED: {symbol} only {days_to_expiry} days to expiry")
                    logger.info(f"   💡 Falling back to equity signal (avoiding theta cliff)")
                    return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            except Exception as exp_err:
                logger.debug(f"Expiry check skipped for {symbol}: {exp_err}")
            
            # 🚨 FIX #4: MOMENTUM CONFIRMATION - Only enter options on strong moves
            # Options need quick moves to overcome theta decay. Weak momentum = likely loss
            momentum_check = await self._check_momentum_for_options(symbol, action, entry_price, metadata)
            if not momentum_check.get('confirmed', False):
                reason = momentum_check.get('reason', 'Weak momentum')
                logger.warning(f"📉 MOMENTUM REJECTED: {symbol} - {reason}")
                logger.info(f"   💡 Options need strong moves. Falling back to equity.")
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            else:
                logger.info(f"✅ MOMENTUM CONFIRMED: {symbol} - {momentum_check.get('details', '')}")
            
            # 🚨 FIX #6: TREND STRENGTH FILTER - Only trade options in strong trends
            # Sideways/choppy markets kill options due to theta decay
            trend_check = self._check_trend_strength_for_options(symbol, action, metadata)
            if not trend_check.get('strong_trend', False):
                reason = trend_check.get('reason', 'Weak/sideways trend')
                logger.warning(f"📊 TREND REJECTED: {symbol} - {reason}")
                logger.info(f"   💡 Options need trending markets. Falling back to equity.")
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            else:
                logger.info(f"✅ TREND CONFIRMED: {symbol} - {trend_check.get('details', '')}")
            
            # 🎯 CRITICAL FIX: Convert to options symbol and force BUY action
            options_symbol, option_type = await self._convert_to_options_symbol(symbol, entry_price, action)
            
            # 🚨 CRITICAL: Check if signal was rejected (e.g., MIDCPNIFTY, SENSEX)
            if options_symbol is None or option_type == 'REJECTED':
                logger.warning(f"⚠️ OPTIONS SIGNAL REJECTED: {symbol} - cannot be traded")
                return None
            
            # 🎯 FALLBACK: If options not available, create equity signal instead
            # 🔧 2025-12-29: FIX CRITICAL BUG - Flip action based on original option_type
            # BUY PUT (bearish) → SELL EQUITY
            # BUY CALL (bullish) → BUY EQUITY
            if option_type == 'EQUITY':
                original_option_type = metadata.get('option_type', '') if metadata else ''
                equity_action = action
                
                if original_option_type == 'PE':
                    # PUT option = bearish bet, so for equity we should SELL (short)
                    equity_action = 'SELL'
                    logger.info(f"🔄 PUT→EQUITY FALLBACK: {options_symbol} - Converting BUY PUT to SELL EQUITY (short)")
                elif original_option_type == 'CE':
                    # CALL option = bullish bet, so for equity we should BUY (long)
                    equity_action = 'BUY'
                    logger.info(f"🔄 CALL→EQUITY FALLBACK: {options_symbol} - Converting BUY CALL to BUY EQUITY (long)")
                else:
                logger.info(f"🔄 FALLBACK TO EQUITY: Creating equity signal for {options_symbol}")
                
                return self._create_equity_signal(options_symbol, equity_action, entry_price, stop_loss, target, confidence, metadata)
            
            final_action = 'BUY' # Force all options signals to be BUY
            
            # 🔍 CRITICAL DEBUG: Log the complete symbol creation process
            logger.info(f"🔍 SYMBOL CREATION DEBUG:")
            logger.info(f"   Original: {symbol} → Options: {options_symbol}")
            logger.info(f"   Type: {option_type}, Action: {final_action}")
            logger.info(f"   Entry Price: ₹{entry_price} (underlying)")
            
            # ========================================
            # 🚨 FIX #7: OPTIONS POSITION MANAGEMENT
            # - Check for existing position (same underlying + type = ONE position)
            # - Square off opposite side automatically
            # - Check for pending orders
            # ========================================
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                zerodha_client = orchestrator.zerodha_client if orchestrator else None
                
                if zerodha_client:
                    # CHECK 1: Is there already a position for same underlying + option type?
                    # BANKNIFTY 26900 PE and BANKNIFTY 26850 PE are treated as ONE position
                    has_position, existing_info = await self._has_existing_options_position(options_symbol, zerodha_client)
                    if has_position:
                        logger.warning(f"🚫 OPTIONS DUPLICATE BLOCKED: {options_symbol}")
                        logger.warning(f"   Already have {option_type} position on {symbol}: {existing_info.get('existing_symbol', 'unknown')}")
                        logger.info(f"   💡 All strikes of same underlying+type are ONE position. Close existing first.")
                        return None  # Block the signal completely
                    
                    # CHECK 2: Is there an opposite side position that needs to be squared off?
                    # If buying CE, square off any PE positions first
                    opposite_positions = await self._get_opposite_side_positions(options_symbol, zerodha_client)
                    if opposite_positions:
                        opposite_type = 'PE' if option_type == 'CE' else 'CE'
                        logger.info(f"🔄 AUTO SQUARE-OFF REQUIRED: Found {len(opposite_positions)} {opposite_type} positions")
                        
                        # Square off the opposite positions
                        square_off_results = await self._square_off_opposite_positions(options_symbol, zerodha_client)
                        logger.info(f"   ✅ Square-off orders placed: {len(square_off_results)}")
                        
                        # Wait a moment for the square-offs to process
                        await asyncio.sleep(2)
                    
                    # CHECK 3: Is there a pending order for this underlying + type?
                    is_pending, pending_order_id = await self._is_order_pending_for_symbol(options_symbol, zerodha_client)
                    if is_pending:
                        logger.warning(f"⏳ PENDING ORDER BLOCKS NEW SIGNAL: {options_symbol}")
                        logger.warning(f"   Pending order_id: {pending_order_id}")
                        logger.info(f"   💡 Wait for pending order to execute or be cancelled")
                        return None  # Block the signal
                        
            except Exception as opm_err:
                logger.warning(f"⚠️ Options position check error (continuing): {opm_err}")
            
            # 🎯 CRITICAL FIX: Get actual options premium from TrueData instead of stock price
            options_entry_price = self._get_options_premium(options_symbol, symbol)
            
            # 🔍 DEBUG: Log premium fetching
            logger.info(f"   Options Premium: ₹{options_entry_price} (vs underlying ₹{entry_price})")
            
            # 🚨 FIX #5: GREEKS-AWARE CHECK - Verify delta/theta ratio is favorable
            greeks_check = await self._check_greeks_for_options(options_symbol, options_entry_price, entry_price, option_type)
            if not greeks_check.get('favorable', True):  # Default to True if check fails
                reason = greeks_check.get('reason', 'Unfavorable Greeks')
                logger.warning(f"📊 GREEKS REJECTED: {symbol} - {reason}")
                logger.info(f"   💡 Options Greeks unfavorable. Falling back to equity.")
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            elif greeks_check.get('details'):
                logger.info(f"✅ GREEKS OK: {symbol} - {greeks_check.get('details', '')}")
            
            # 🚨 CRITICAL: Block options signals with zero LTP completely
            if options_entry_price <= 0:
                # Attempt nearby-strike rescue before giving up
                try:
                    rescue = self._attempt_nearby_strike_rescue(options_symbol)
                except Exception as _rescue_err:
                    rescue = None
                    logger.debug(f"Nearby-strike rescue error: {_rescue_err}")
                if rescue and rescue.get('symbol') and rescue.get('ltp', 0) > 0:
                    new_symbol = rescue['symbol']
                    options_entry_price = rescue['ltp']
                    logger.info(f"🛟 RESCUED OPTIONS: Switching to {new_symbol} with LTP ₹{options_entry_price}")
                    options_symbol = new_symbol
                
                if options_entry_price <= 0:
                    logger.error(f"❌ REJECTING OPTIONS SIGNAL: {options_symbol} has ZERO LTP - cannot trade")
                    # Only fall back to equity if market is open
                    if self._is_trading_hours():
                        logger.info(f"🔄 ATTEMPTING EQUITY FALLBACK for {symbol} due to zero options LTP")
                        logger.info(f"   REASON: Options contract {options_symbol} not liquid or doesn't exist")
                        logger.info(f"   SOLUTION: Trading underlying equity with same risk-reward profile")
                        
                        # CRITICAL FIX: Ensure metadata shows EQUITY signal type for fallback
                        equity_metadata = metadata.copy()
                        equity_metadata['signal_type'] = 'EQUITY'
                        equity_metadata['fallback_reason'] = 'options_ltp_zero'
                        equity_metadata['original_options_symbol'] = options_symbol
                        
                        # 🔧 2025-12-29: FIX CRITICAL BUG - Flip action based on original option_type
                        # BUY PUT (bearish) → SELL EQUITY
                        # BUY CALL (bullish) → BUY EQUITY
                        equity_action = action
                        if option_type == 'PE':
                            equity_action = 'SELL'
                            logger.info(f"   🔄 PUT→EQUITY: Converting BUY PUT to SELL EQUITY (short)")
                        elif option_type == 'CE':
                            equity_action = 'BUY'
                            logger.info(f"   🔄 CALL→EQUITY: Converting BUY CALL to BUY EQUITY (long)")
                        
                        return self._create_equity_signal(symbol, equity_action, entry_price, stop_loss, target, confidence, equity_metadata)
                    return None

            # 🎯 CRITICAL FIX: Calculate correct stop_loss and target for options (only after non-zero premium)
            options_stop_loss, options_target = self._calculate_options_levels(
                options_entry_price, stop_loss, target, option_type, action, symbol
            )
            
            # Validate signal levels only if we have a real entry price
            if not self.validate_signal_levels(options_entry_price, options_stop_loss, options_target, 'BUY'):
                logger.warning(f"Invalid options signal levels: Entry={options_entry_price}, SL={options_stop_loss}, Target={options_target}")
                return None
            
            # 🎯 CRITICAL FIX: Always BUY options (no selling due to margin requirements)
            final_action = 'BUY'  # Force all options signals to be BUY
            
            # Calculate risk metrics using OPTIONS pricing (handle 0.0 entry price)
            risk_amount = abs(options_entry_price - options_stop_loss)
            reward_amount = abs(options_target - options_entry_price)
            risk_percent = (risk_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            reward_percent = (reward_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # CRITICAL FIX: Generate unique signal_id for tracking
            signal_id = f"{self.name}_{options_symbol}_{int(datetime.now().timestamp())}"
            
            # CRITICAL FIX: Validate quantity BEFORE creating signal
            quantity = self._get_capital_constrained_quantity(options_symbol, symbol, options_entry_price)
            if quantity <= 0:
                logger.error(f"❌ SIGNAL REJECTED: {options_symbol} - Quantity is {quantity} (insufficient capital or invalid lot size)")
                logger.error(f"   This signal will NOT be sent to trade engine")
                return None
            
            # 🔥 OPTIONS ARE ALWAYS INTRADAY: Must be squared off same day
            is_intraday = True
            trading_mode = 'INTRADAY'
            timeframe = "Same Day (Intraday)"
            square_off_time = "15:15 IST"
            
            return {
                # Core signal fields (consistent naming)
                'signal_id': signal_id,
                'symbol': options_symbol,  # 🎯 FIXED: Use options symbol instead of underlying
                'underlying_symbol': symbol,  # Keep original for reference
                'option_type': option_type,  # CE or PE
                'action': final_action.upper(),  # Always BUY for options (no selling due to margin)
                'quantity': quantity,  # 🎯 CAPITAL-AWARE: Limit lots based on capital (validated above)
                'entry_price': self._round_to_tick_size(options_entry_price),  # 🎯 FIXED: Use tick size rounding
                'stop_loss': self._round_to_tick_size(options_stop_loss),      # 🎯 FIXED: Tick size rounding
                'target': self._round_to_tick_size(options_target),            # 🎯 FIXED: Tick size rounding
                'strategy': self.name,  # Use 'strategy' for compatibility
                'strategy_name': self.name,  # Also include strategy_name for new components
                'confidence': round(confidence, 2),
                'quality_score': round(confidence, 2),  # Map confidence to quality_score
                
                # 🔥 NEW: Trading mode indicators
                'is_intraday': is_intraday,
                'trading_mode': trading_mode,
                'timeframe': timeframe,
                'square_off_time': square_off_time,
                
                # Risk metrics
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                
                # Enhanced metadata
                'metadata': {
                    **metadata,
                    'signal_validation': 'PASSED',
                    'trading_mode': trading_mode,
                    'is_intraday': is_intraday,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.name,
                    'signal_source': 'strategy_engine',
                    'underlying_price': round(entry_price, 2),  # Keep original stock price for reference
                    'options_conversion': 'PREMIUM_BASED'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating standard signal: {e}")
            return None
    
    def _create_equity_signal(self, symbol: str, action: str, entry_price: float, 
                             stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """Create equity signal with standard parameters
        
        🎯 POSITION SIZING RULES (User Requirements):
        1. Max loss per trade = 2% of portfolio value
        2. Intraday leverage = 4x (MIS margin)
        3. Quantity = Max Loss / Risk Per Share (capped by leverage limit)
        
        🎯 MULTI-TIMEFRAME FILTER (High Accuracy):
        - Only generates signals when 60min + 15min + 5min trends align
        - Perfect alignment = 1.5x confidence boost
        - Strong alignment = 1.25x confidence boost  
        - No alignment = Signal BLOCKED
        """
        try:
            # 🎯 CRITICAL FIX: Ensure equity action aligns with original options intent
            # When options fallback to equity, PUT = SELL, CALL = BUY
            original_option_type = metadata.get('option_type', '')
            if original_option_type == 'PE' and action.upper() == 'BUY':
                logger.warning(f"🔧 ACTION CORRECTION: {symbol} PUT→EQUITY changing BUY→SELL")
                action = 'SELL'
                # 🔧 RECALCULATE SL/TARGET for SELL (not just swap - that inverts R:R!)
                # BUY levels have: risk_pct = (entry-SL)/entry, reward_pct = (target-entry)/entry
                # For SELL: SL above entry, Target below entry, SAME R:R
                old_sl, old_target = stop_loss, target
                if entry_price > 0:
                    risk_pct = abs(entry_price - old_sl) / entry_price if old_sl else 0.03
                    reward_pct = abs(old_target - entry_price) / entry_price if old_target else 0.075
                    # For SELL: SL = entry * (1 + risk_pct), Target = entry * (1 - reward_pct)
                    stop_loss = entry_price * (1 + risk_pct)
                    target = entry_price * (1 - reward_pct)
                    logger.info(f"🔧 LEVELS RECALCULATED for SELL: Entry={entry_price:.2f}, SL={stop_loss:.2f} (+{risk_pct*100:.1f}%), Target={target:.2f} (-{reward_pct*100:.1f}%)")
                else:
                    logger.warning(f"⚠️ Cannot recalculate levels for {symbol} - no entry price")
            elif original_option_type == 'CE' and action.upper() == 'SELL':
                logger.warning(f"🔧 ACTION CORRECTION: {symbol} CALL→EQUITY changing SELL→BUY")
                action = 'BUY'
                # 🔧 RECALCULATE SL/TARGET for BUY (not just swap)
                old_sl, old_target = stop_loss, target
                if entry_price > 0:
                    risk_pct = abs(old_sl - entry_price) / entry_price if old_sl else 0.03
                    reward_pct = abs(entry_price - old_target) / entry_price if old_target else 0.075
                    # For BUY: SL = entry * (1 - risk_pct), Target = entry * (1 + reward_pct)
                    stop_loss = entry_price * (1 - risk_pct)
                    target = entry_price * (1 + reward_pct)
                    logger.info(f"🔧 LEVELS RECALCULATED for BUY: Entry={entry_price:.2f}, SL={stop_loss:.2f} (-{risk_pct*100:.1f}%), Target={target:.2f} (+{reward_pct*100:.1f}%)")
                else:
                    logger.warning(f"⚠️ Cannot recalculate levels for {symbol} - no entry price")
            
            # Hard block known delisted/suspended symbols at source
            try:
                blocked_symbols = {'RCOM', 'RELCAPITAL', 'YESBANK', 'JETAIRWAYS'}
                if symbol in blocked_symbols:
                    logger.warning(f"🚫 BLOCKED EQUITY SIGNAL: {symbol} is delisted/suspended - rejecting")
                    return None
            except Exception:
                pass
            
            # 🚫 PENNY STOCK FILTER: Block stocks under ₹50 (high slippage, destroys profits)
            MIN_STOCK_PRICE = 50.0
            if entry_price and entry_price < MIN_STOCK_PRICE:
                logger.warning(f"🚫 PENNY STOCK BLOCKED: {symbol} @ ₹{entry_price:.2f} < ₹{MIN_STOCK_PRICE} minimum")
                return None
            
            # ============================================================
            # 🎯 MULTI-TIMEFRAME FILTER - FEWER TRADES, HIGHER ACCURACY
            # ============================================================
            mtf_result = self.analyze_multi_timeframe(symbol, action)
            
            # Log MTF analysis
            logger.info(f"📊 MTF ANALYSIS: {symbol} {action}")
            logger.info(f"   60min: {mtf_result['timeframes']['60min']} | 15min: {mtf_result['timeframes']['15min']} | 5min: {mtf_result['timeframes']['5min']}")
            logger.info(f"   Aligned: {mtf_result['mtf_aligned']} | Score: {mtf_result['alignment_score']}/3 | {mtf_result['reasoning']}")
            
            # BLOCK SIGNAL if MTF not aligned (strict mode for accuracy)
            if not mtf_result['mtf_aligned'] and mtf_result['alignment_score'] < 2:
                # 🔧 FIX: Log directional_action for options
                logger.warning(f"🚫 MTF BLOCK: {symbol} {directional_action} - Timeframes not aligned ({mtf_result['reasoning']})")
                return None
            
            # 🔥 CRITICAL: BLOCK if action CONFLICTS with strong MTF alignment
            # If 3/3 or 2/3 timeframes are BEARISH but action is BUY → BLOCK
            # If 3/3 or 2/3 timeframes are BULLISH but action is SELL → BLOCK
            # 🔧 EXCEPTION: REVERSAL signals bypass MTF block (need to exit positions)
            mtf_direction = mtf_result.get('direction', 'NEUTRAL')
            if mtf_result['alignment_score'] >= 2 and mtf_direction != 'NEUTRAL':
                action_conflicts = (
                    (mtf_direction == 'BEARISH' and action == 'BUY') or
                    (mtf_direction == 'BULLISH' and action == 'SELL')
                )
                if action_conflicts:
                    # 🔧 CHECK IF THIS IS A REVERSAL SIGNAL (meant to exit existing position)
                    # Reversal signals should bypass MTF block - we need to exit!
                    is_reversal = False
                    try:
                        # Check if we have an existing position in OPPOSITE direction
                        option_type = metadata.get('option_type', '') if metadata else ''
                        existing_positions = getattr(self, 'active_positions', {})
                        
                        # Check broker positions too
                        broker_positions = []
                        if hasattr(self, 'zerodha') and self.zerodha:
                            try:
                                broker_positions = self.zerodha.positions() or []
                            except:
                                pass
                        
                        for pos in broker_positions:
                            pos_symbol = pos.get('tradingsymbol', '')
                            pos_qty = pos.get('quantity', 0)
                            if pos_symbol == symbol and pos_qty != 0:
                                existing_is_long = pos_qty > 0
                                # Determine if current signal is opposite direction
                                if option_type == 'PE':  # PUT = SHORT
                                    signal_is_long = False
                                elif option_type == 'CE':  # CALL = LONG
                                    signal_is_long = True
                                else:
                                    signal_is_long = (action == 'BUY')
                                
                                # Opposite directions = REVERSAL
                                if (existing_is_long and not signal_is_long) or (not existing_is_long and signal_is_long):
                                    is_reversal = True
                                    logger.info(f"🔄 MTF BYPASS: {symbol} {action} is REVERSAL signal - bypassing MTF conflict")
                                    break
                    except Exception as rev_err:
                        logger.debug(f"Reversal check error: {rev_err}")
                    
                    # 🔧 2025-12-29: Also bypass MTF if current price move strongly contradicts MTF
                    strong_move_bypass = False
                    weighted_change = 0
                    try:
                        # Try to get change data from multiple sources
                        day_change = 0
                        intraday_change = 0
                        
                        # Source 1: Metadata (if passed by strategy)
                        if metadata:
                            day_change = metadata.get('change_percent', metadata.get('day_change_pct', 0))
                            intraday_change = metadata.get('intraday_change_pct', metadata.get('intraday_change', 0))
                        
                        # Source 2: Calculate from live data if metadata is empty
                        if day_change == 0 and intraday_change == 0:
                            try:
                                from data.truedata_client import live_market_data
                                if symbol in live_market_data:
                                    stock_data = live_market_data[symbol]
                                    ltp = float(stock_data.get('ltp', 0))
                                    prev_close = float(stock_data.get('previous_close', 0))
                                    open_price = float(stock_data.get('open', 0))
                                    if ltp > 0 and prev_close > 0:
                                        day_change = ((ltp - prev_close) / prev_close) * 100
                                    if ltp > 0 and open_price > 0:
                                        intraday_change = ((ltp - open_price) / open_price) * 100
                            except Exception:
                                pass
                        
                        weighted_change = 0.6 * day_change + 0.4 * intraday_change
                        
                        # If MTF shows BULLISH but stock is down >2%, MTF is lagging
                        if mtf_direction == 'BULLISH' and weighted_change < -2.0 and directional_action == 'SELL':
                            strong_move_bypass = True
                            logger.info(f"🔄 MTF STRONG MOVE BYPASS: {symbol} SELL - Stock down {weighted_change:.1f}% but MTF=BULLISH (lagging)")
                        # If MTF shows BEARISH but stock is up >2%, MTF is lagging
                        elif mtf_direction == 'BEARISH' and weighted_change > 2.0 and directional_action == 'BUY':
                            strong_move_bypass = True
                            logger.info(f"🔄 MTF STRONG MOVE BYPASS: {symbol} BUY - Stock up +{weighted_change:.1f}% but MTF=BEARISH (lagging)")
                    except Exception as mv_err:
                        logger.debug(f"Strong move bypass check error: {mv_err}")
                    
                    if not is_reversal and not strong_move_bypass:
                        # 🔧 FIX: Log directional_action for options
                        logger.warning(f"🚫 MTF CONFLICT BLOCK: {symbol} {directional_action} - MTF shows {mtf_direction} "
                                      f"({mtf_result['alignment_score']}/3 timeframes) but action is {directional_action}")
                    return None
                    else:
                        bypass_reason = "Reversal signal" if is_reversal else f"Strong move ({weighted_change:.1f}%)"
                        logger.info(f"✅ MTF CONFLICT BYPASSED: {symbol} {directional_action} - {bypass_reason} allowed")
            
            # Apply confidence multiplier from MTF
            original_confidence = confidence
            confidence = confidence * mtf_result['confidence_multiplier']
            
            # Cap at 10.0
            confidence = min(confidence, 10.0)
            
            if mtf_result['confidence_multiplier'] != 1.0:
                logger.info(f"   🎯 Confidence: {original_confidence:.1f} → {confidence:.1f} (MTF: {mtf_result['confidence_multiplier']:.2f}x)")
            
            # 🔥 CRITICAL FIX: Second confidence check AFTER MTF adjustment
            # Minimum confidence threshold to ensure high-accuracy trades only
            MIN_FINAL_CONFIDENCE = 7.0  # Absolute minimum after all adjustments
            if confidence < MIN_FINAL_CONFIDENCE:
                logger.warning(f"🗑️ MTF CONFIDENCE TOO LOW: {symbol} {action} - Final confidence {confidence:.1f}/10 < {MIN_FINAL_CONFIDENCE} minimum")
                return None

            # Validate signal levels
            if not self.validate_signal_levels(entry_price, stop_loss, target, action):
                logger.warning(f"Invalid equity signal levels: {symbol}")
                return None
            
            # Calculate risk metrics
            risk_amount = abs(entry_price - stop_loss)  # Risk per share (₹)
            reward_amount = abs(target - entry_price)
            risk_percent = (risk_amount / entry_price) * 100
            reward_percent = (reward_amount / entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Check minimum risk-reward ratio (DYNAMIC based on volatility)
            min_risk_reward_ratio = self._get_dynamic_min_risk_reward_ratio(symbol, entry_price)
            
            # RESTORED: Enforce proper risk-reward - quality over quantity
            # Minimum 1.5:1 risk-reward for any trade
            min_risk_reward_ratio = max(min_risk_reward_ratio, 1.5)
            
            if risk_reward_ratio < min_risk_reward_ratio:
                logger.warning(f"Equity signal below {min_risk_reward_ratio}:1 ratio: {symbol} ({risk_reward_ratio:.2f})")
                return None
            
            # ============================================================
            # 🎯 HYBRID APPROACH: SCALP vs SWING based on MTF alignment
            # ============================================================
            # MTF 0-1/3: Choppy market → SCALP mode (quick in/out, small targets)
            # MTF 2-3/3: Trending market → SWING mode (larger targets, longer hold)
            mtf_score = mtf_result.get('alignment_score', 0)
            
            # 🚫 SCALP MODE DISABLED - Was causing losses due to slippage and forced exits
            # All trades now use INTRADAY mode with normal targets
            # The MTF score is logged but doesn't change trading behavior
            
            hybrid_mode = 'INTRADAY'  # No more SCALP/SWING distinction
            max_hold_minutes = 0  # No forced time-based exit
            
            # Keep original stop_loss and target (already calculated by ATR)
            logger.info(f"📈 INTRADAY MODE: {symbol} {action} (MTF {mtf_score}/3)")
            logger.info(f"   Target: {reward_percent:.1f}% | SL: {risk_percent:.1f}% | Hold: Until target/SL/3:15PM")
            
            # 🔥 INTRADAY FOCUS: All hybrid trades are intraday
            is_intraday = True  # Always intraday for hybrid approach
            trading_mode = f'INTRADAY_{hybrid_mode}'
            
            # 🔥 INTRADAY TIMEFRAME
            timeframe = "Same Day (Intraday)"
            square_off_time = "15:15 IST"
            
            # ============================================================
            # 🎯 CRITICAL: PROPER POSITION SIZING (4x LEVERAGE + 1% MAX LOSS)
            # ============================================================
            # REDUCED from 2% to 1% to limit daily losses
            # Real-time available margin (feasibility cap)
            available_capital = self._get_available_capital()
            if available_capital <= 0:
                logger.warning(f"🚫 NO AVAILABLE CAPITAL: {symbol} - cannot size order")
                return None

            # Stable base capital (sizing base for the day)
            sizing_capital = self._get_base_capital_for_sizing()
            if sizing_capital <= 0:
                sizing_capital = available_capital
            
            # Rule 1: Max loss = 1% of portfolio (was 2%)
            max_loss_per_trade = sizing_capital * 0.01
            
            # ============================================================
            # 🎯 OPTION 2 FIX: TIGHTEN STOP LOSS FOR LOW-CAPITAL ACCOUNTS
            # ============================================================
            # Problem: Wide stops (>3%) with low capital creates position values
            # below ₹50,000 minimum, blocking valid signals.
            # Solution: Cap stop loss at 3% for accounts < ₹300,000
            # This ensures: max_loss / (entry × 3%) × entry ≥ ₹50,000
            LOW_CAPITAL_THRESHOLD = 300000.0  # ₹3 lakh
            MAX_STOP_PERCENT_LOW_CAPITAL = 0.03  # 3% max stop for low capital
            MIN_ORDER_VALUE = 50000.0  # Minimum position value
            
            if sizing_capital < LOW_CAPITAL_THRESHOLD:
                current_stop_percent = risk_amount / entry_price
                
                if current_stop_percent > MAX_STOP_PERCENT_LOW_CAPITAL:
                    # Recalculate stop loss with tighter distance
                    old_stop_loss = stop_loss
                    old_risk_amount = risk_amount
                    
                    new_stop_distance = entry_price * MAX_STOP_PERCENT_LOW_CAPITAL
                    
                    if action.upper() == 'BUY':
                        stop_loss = entry_price - new_stop_distance
                    else:  # SELL
                        stop_loss = entry_price + new_stop_distance
                    
                    # Update risk metrics
                    risk_amount = new_stop_distance
                    risk_percent = MAX_STOP_PERCENT_LOW_CAPITAL * 100
                    
                    # Also adjust target to maintain R:R ratio (min 2.5:1 for intraday)
                    min_rr_ratio = 2.5
                    new_reward_amount = risk_amount * min_rr_ratio
                    if action.upper() == 'BUY':
                        target = entry_price + new_reward_amount
                    else:
                        target = entry_price - new_reward_amount
                    
                    reward_amount = new_reward_amount
                    reward_percent = (reward_amount / entry_price) * 100
                    risk_reward_ratio = min_rr_ratio
                    
                    logger.info(f"🔧 LOW CAPITAL ADJUSTMENT for {symbol}:")
                    logger.info(f"   Capital: ₹{sizing_capital:,.0f} < ₹{LOW_CAPITAL_THRESHOLD:,.0f} threshold")
                    logger.info(f"   Stop: {old_risk_amount/entry_price*100:.1f}% → {MAX_STOP_PERCENT_LOW_CAPITAL*100:.1f}%")
                    logger.info(f"   SL: ₹{old_stop_loss:.2f} → ₹{stop_loss:.2f}")
                    logger.info(f"   Target adjusted to ₹{target:.2f} (R:R = {min_rr_ratio}:1)")
            
            # Rule 2: Intraday leverage = 4x
            INTRADAY_LEVERAGE = 4.0
            # Desired max position value based on base capital (consistent sizing)
            max_position_value = sizing_capital * INTRADAY_LEVERAGE
            # Hard feasibility cap based on what Zerodha says is currently available
            max_position_value_by_available = available_capital * INTRADAY_LEVERAGE
            
            # Calculate quantity based on risk (stop loss distance)
            if risk_amount <= 0:
                logger.error(f"❌ INVALID RISK: {symbol} has zero/negative risk amount ₹{risk_amount}")
                return None
            
            # Quantity based on max loss rule
            qty_by_risk = int(max_loss_per_trade / risk_amount)
            
            # Quantity based on leverage limit
            qty_by_leverage = int(max_position_value / entry_price)

            # Quantity based on real-time available margin (feasibility)
            qty_by_available = int(max_position_value_by_available / entry_price) if entry_price > 0 else 0
            
            # Use the smaller of the two (most restrictive)
            final_quantity = min(qty_by_risk, qty_by_leverage, qty_by_available)
            
            # 🔧 2025-12-30 FIX: Index futures must trade in lot sizes
            # NIFTY-I, BANKNIFTY-I, etc. have fixed lot sizes that must be respected
            INDEX_FUTURES = ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 
                           'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
            if symbol.upper() in INDEX_FUTURES:
                lot_size = self._get_futures_lot_size(symbol)
                # Round DOWN to nearest lot (can't trade fractional lots)
                final_quantity = (final_quantity // lot_size) * lot_size
                # Minimum 1 lot for index futures
                if final_quantity < lot_size:
                    # Check if we can afford 1 lot
                    one_lot_value = lot_size * entry_price
                    one_lot_margin = one_lot_value / INTRADAY_LEVERAGE
                    if one_lot_margin <= available_capital * 0.5:  # Max 50% of available
                        final_quantity = lot_size
                        logger.info(f"📊 INDEX FUTURES: {symbol} using minimum 1 lot = {lot_size} qty")
                    else:
                        logger.warning(f"🚫 INDEX FUTURES BLOCKED: {symbol} needs ₹{one_lot_margin:,.0f} margin for 1 lot, only ₹{available_capital:,.0f} available")
                        return None
                else:
                    logger.info(f"📊 INDEX FUTURES: {symbol} qty={final_quantity} ({final_quantity//lot_size} lots of {lot_size})")
            else:
                # Ensure minimum 1 share for equity
                final_quantity = max(final_quantity, 1)
            
            # Calculate actual values for logging
            position_value = final_quantity * entry_price
            actual_max_loss = final_quantity * risk_amount
            margin_required = position_value / INTRADAY_LEVERAGE  # 25% of position
            
            # 🔥 FIX: Minimum order value to prevent brokerage losses on tiny trades
            # At ₹50,000, a 1% move = ₹500 profit, covering brokerage (~₹60) with good buffer
            MIN_ORDER_VALUE = 50000.0
            if position_value < MIN_ORDER_VALUE:
                logger.warning(f"🚫 SMALL ORDER BLOCKED: {symbol} position ₹{position_value:,.0f} < min ₹{MIN_ORDER_VALUE:,.0f}")
                return None
            
            logger.info(f"📊 POSITION SIZING: {symbol} {action}")
            logger.info(
                f"   💰 Sizing Base: ₹{sizing_capital:,.0f} | Available Now: ₹{available_capital:,.0f} | "
                f"Max Loss (1% of base): ₹{max_loss_per_trade:,.0f}"
            )
            logger.info(f"   📉 Risk/Share: ₹{risk_amount:.2f} | Entry: ₹{entry_price:.2f} | SL: ₹{stop_loss:.2f}")
            logger.info(
                f"   🎯 Qty by Risk: {qty_by_risk} | Qty by Leverage(base): {qty_by_leverage} | "
                f"Qty by Available(now): {qty_by_available} | FINAL: {final_quantity}"
            )
            logger.info(f"   💵 Position Value: ₹{position_value:,.0f} | Margin: ₹{margin_required:,.0f} | Max Loss: ₹{actual_max_loss:,.0f}")
            
            # ============================================================
            # 🎯 SMART ENTRY PRICING (PULLBACK-AWARE)
            # ============================================================
            # PROBLEM: Entering at LTP after signal confirmation = entering at peak
            # SOLUTION: Check if we're at a peak and wait for pullback
            
            original_entry = entry_price
            order_type = 'MARKET'  # Default
            limit_discount_pct = 0.0
            limit_validity_seconds = 300  # 5 minutes for limit orders
            peak_detected = False
            pullback_available = False
            
            # Normalize confidence to 0-10 scale if needed
            conf_normalized = confidence if confidence > 1.0 else confidence * 10.0
            
            # 🎯 PEAK DETECTION: Check if current price is at recent high/low
            try:
                if hasattr(self, 'price_history') and symbol in self.price_history:
                    prices = self.price_history.get(symbol, [])
                    if len(prices) >= 10:
                        recent_high = max(prices[-10:])
                        recent_low = min(prices[-10:])
                        price_range = recent_high - recent_low if recent_high > recent_low else 1
                        
                        if action.upper() == 'BUY':
                            # Check if we're near the recent high (peak)
                            distance_from_high = (recent_high - original_entry) / price_range
                            if distance_from_high < 0.2:  # Within top 20% of range
                                peak_detected = True
                                logger.warning(f"⚠️ {symbol}: BUY at PEAK! Price near recent high (₹{recent_high:.2f})")
                            elif distance_from_high > 0.4:  # Price has pulled back
                                pullback_available = True
                                logger.info(f"✅ {symbol}: PULLBACK DETECTED! Good entry (distance from high: {distance_from_high:.0%})")
                        else:  # SELL
                            # Check if we're near the recent low (trough)
                            distance_from_low = (original_entry - recent_low) / price_range
                            if distance_from_low < 0.2:  # Within bottom 20% of range
                                peak_detected = True
                                logger.warning(f"⚠️ {symbol}: SELL at TROUGH! Price near recent low (₹{recent_low:.2f})")
                            elif distance_from_low > 0.4:  # Price has bounced
                                pullback_available = True
                                logger.info(f"✅ {symbol}: BOUNCE DETECTED! Good entry (distance from low: {distance_from_low:.0%})")
            except Exception as peak_err:
                logger.debug(f"Peak detection skipped: {peak_err}")
            
            # ============================================================
            # 📊 CAMARILLA PIVOTS - Professional Intraday Entry Levels
            # ============================================================
            # Uses previous day's daily OHLC for precise S/R levels
            # H4, H3, H2, H1 (resistance) and L1, L2, L3, L4 (support)
            
            support_entry = None
            resistance_entry = None
            sr_based_entry = False
            camarilla_signal = None
            
            try:
                # Get Camarilla levels from cache (sync access - levels are cached daily)
                camarilla = self._camarilla_cache.get(symbol, {})
                
                if camarilla:
                    h4, h3, h2, h1 = camarilla['h4'], camarilla['h3'], camarilla['h2'], camarilla['h1']
                    l1, l2, l3, l4 = camarilla['l1'], camarilla['l2'], camarilla['l3'], camarilla['l4']
                    
                    if action.upper() == 'BUY':
                        # Find best BUY entry using Camarilla support levels
                        support_levels = []
                        
                        # Priority: L3 > L2 > L1 (key support levels)
                        for level_name, level_val in [('L3', l3), ('L2', l2), ('L1', l1)]:
                            if level_val > 0 and level_val < original_entry:
                                distance_pct = (original_entry - level_val) / original_entry * 100
                                # Wider range for intraday volatility
                                if 0.05 <= distance_pct <= 2.5:
                                    support_levels.append((level_name, level_val, distance_pct))
                        
                        # Also check swing low as backup
                        swing_low, swing_high = self._find_swing_levels(symbol)
                        if swing_low > 0 and swing_low < original_entry:
                            distance_pct = (original_entry - swing_low) / original_entry * 100
                            if 0.05 <= distance_pct <= 2.5:
                                support_levels.append(('swing_low', swing_low, distance_pct))
                        
                        if support_levels:
                            # Pick NEAREST support
                            support_levels.sort(key=lambda x: x[2])
                            nearest = support_levels[0]
                            support_entry = nearest[1]
                            logger.info(f"📊 CAMARILLA BUY: {symbol} → {nearest[0]}=₹{support_entry:.2f} (-{nearest[2]:.2f}%)")
                        
                        # Validate signal against Camarilla structure
                        if original_entry > h3:
                            camarilla_signal = "RESISTANCE_ZONE"
                            logger.warning(f"⚠️ {symbol} BUY RISKY: Price above H3 (₹{h3:.2f})")
                        elif original_entry < l4:
                            camarilla_signal = "BREAKDOWN_ZONE"
                            logger.warning(f"⚠️ {symbol} BUY RISKY: Price below L4 (₹{l4:.2f})")
                        elif original_entry > h4:
                            camarilla_signal = "BREAKOUT_CONFIRMED"
                            logger.info(f"🚀 {symbol} BUY BREAKOUT: Above H4 (₹{h4:.2f})")
                        elif l3 <= original_entry <= h3:
                            camarilla_signal = "RANGE_BOUND"
                    
                    else:  # SELL
                        # Find best SELL entry using Camarilla resistance levels
                        resistance_levels = []
                        
                        # Priority: H3 > H2 > H1 (key resistance levels)
                        for level_name, level_val in [('H3', h3), ('H2', h2), ('H1', h1)]:
                            if level_val > 0 and level_val > original_entry:
                                distance_pct = (level_val - original_entry) / original_entry * 100
                                # Wider range for intraday volatility
                                if 0.05 <= distance_pct <= 2.5:
                                    resistance_levels.append((level_name, level_val, distance_pct))
                        
                        # Also check swing high as backup
                        swing_low, swing_high = self._find_swing_levels(symbol)
                        if swing_high > 0 and swing_high > original_entry:
                            distance_pct = (swing_high - original_entry) / original_entry * 100
                            if 0.05 <= distance_pct <= 2.5:
                                resistance_levels.append(('swing_high', swing_high, distance_pct))
                        
                        if resistance_levels:
                            # Pick NEAREST resistance
                            resistance_levels.sort(key=lambda x: x[2])
                            nearest = resistance_levels[0]
                            resistance_entry = nearest[1]
                            logger.info(f"📊 CAMARILLA SELL: {symbol} → {nearest[0]}=₹{resistance_entry:.2f} (+{nearest[2]:.2f}%)")
                        
                        # Validate signal against Camarilla structure
                        if original_entry < l3:
                            camarilla_signal = "SUPPORT_ZONE"
                            logger.warning(f"⚠️ {symbol} SELL RISKY: Price below L3 (₹{l3:.2f})")
                        elif original_entry > h4:
                            camarilla_signal = "BREAKOUT_ZONE"
                            logger.warning(f"⚠️ {symbol} SELL RISKY: Price above H4 (₹{h4:.2f})")
                        elif original_entry < l4:
                            camarilla_signal = "BREAKDOWN_CONFIRMED"
                            logger.info(f"📉 {symbol} SELL BREAKDOWN: Below L4 (₹{l4:.2f})")
                        elif l3 <= original_entry <= h3:
                            camarilla_signal = "RANGE_BOUND"
            
            except Exception as sr_err:
                logger.debug(f"Camarilla pivot skipped: {sr_err}")
            
            # ============================================================
            # 🎯 ADAPTIVE ENTRY DECISION
            # ============================================================
            # Priority: 1) S/R levels, 2) Pullback/Peak detection, 3) Confidence-based
            
            if action.upper() == 'BUY' and support_entry and support_entry > 0:
                # Use support level for BUY entry
                distance_pct = (original_entry - support_entry) / original_entry * 100
                
                # 🔧 FIX: Cap maximum distance - if support is too far, use smaller discount
                # In bullish trend, waiting for price to go DOWN 1%+ to fill BUY is unrealistic
                MAX_SR_DISTANCE_PCT = 0.5  # Max 0.5% below LTP for BUY limit
                
                if distance_pct > MAX_SR_DISTANCE_PCT:
                    # Support too far - use small discount instead (0.15% below LTP)
                    entry_price = round(original_entry * 0.9985, 2)  # 0.15% below LTP
                    logger.warning(f"⚠️ S/R TOO FAR: {symbol} BUY - Support ₹{support_entry:.2f} is -{distance_pct:.2f}% away")
                    logger.info(f"🎯 CAPPED ENTRY: {symbol} BUY at ₹{entry_price:.2f} (0.15% below LTP ₹{original_entry:.2f})")
                    limit_validity_seconds = 180  # 3 minutes for close limit
                else:
                    entry_price = round(support_entry, 2)
                    sr_based_entry = True
                    limit_validity_seconds = 300 if distance_pct < 0.3 else 600
                    logger.info(f"🎯 S/R ENTRY: {symbol} BUY at support ₹{entry_price:.2f} (LTP: ₹{original_entry:.2f}, -{distance_pct:.2f}%)")
                
                order_type = 'LIMIT'
                
                # 🔧 FIX: Recalculate SL for new entry price - SL must be BELOW entry for BUY
                if stop_loss >= entry_price:
                    # SL is above entry - invalid for BUY! Recalculate as 1% below new entry
                    old_sl = stop_loss
                    stop_loss = round(entry_price * 0.99, 2)  # 1% below new entry
                    target = round(entry_price + (entry_price - stop_loss) * 2.0, 2)  # Maintain 1:2 R:R
                    logger.info(f"🔧 SL ADJUSTED: {symbol} BUY - Old SL ₹{old_sl:.2f} > Entry ₹{entry_price:.2f} → New SL ₹{stop_loss:.2f}")
            
            elif action.upper() == 'SELL' and resistance_entry and resistance_entry > 0:
                # Use resistance level for SELL entry
                distance_pct = (resistance_entry - original_entry) / original_entry * 100
                
                # 🔧 FIX: Cap maximum distance - if resistance is too far, use smaller discount
                # In bearish trend, waiting for price to go UP 1%+ to fill SELL is unrealistic
                MAX_SR_DISTANCE_PCT = 0.5  # Max 0.5% above LTP for SELL limit
                
                if distance_pct > MAX_SR_DISTANCE_PCT:
                    # Resistance too far - use small discount instead (0.15% above LTP)
                    entry_price = round(original_entry * 1.0015, 2)  # 0.15% above LTP
                    logger.warning(f"⚠️ S/R TOO FAR: {symbol} SELL - Resistance ₹{resistance_entry:.2f} is +{distance_pct:.2f}% away")
                    logger.info(f"🎯 CAPPED ENTRY: {symbol} SELL at ₹{entry_price:.2f} (0.15% above LTP ₹{original_entry:.2f})")
                    limit_validity_seconds = 180  # 3 minutes for close limit
                else:
                    entry_price = round(resistance_entry, 2)
                    sr_based_entry = True
                    limit_validity_seconds = 300 if distance_pct < 0.3 else 600
                    logger.info(f"🎯 S/R ENTRY: {symbol} SELL at resistance ₹{entry_price:.2f} (LTP: ₹{original_entry:.2f}, +{distance_pct:.2f}%)")
                
                order_type = 'LIMIT'

                # 🔧 FIX: Recalculate SL for new entry price - SL must be ABOVE entry for SELL
                if stop_loss <= entry_price:
                    # SL is below entry - invalid for SELL! Recalculate as 1% above new entry
                    old_sl = stop_loss
                    stop_loss = round(entry_price * 1.01, 2)  # 1% above new entry
                    target = round(entry_price - (stop_loss - entry_price) * 2.0, 2)  # Maintain 1:2 R:R
                    logger.info(f"🔧 SL ADJUSTED: {symbol} SELL - Old SL ₹{old_sl:.2f} < Entry ₹{entry_price:.2f} → New SL ₹{stop_loss:.2f}")
            
            elif pullback_available and conf_normalized >= 8.5:
                # Price has pulled back AND signal is strong - use MARKET to capture it
                order_type = 'MARKET'
                limit_discount_pct = 0.0
                logger.info(f"🎯 PULLBACK ENTRY: {symbol} - Price already at good level → MARKET order")
            
            elif peak_detected:
                # At a peak without nearby S/R - use small discount and short validity
                order_type = 'LIMIT'
                limit_discount_pct = 0.20  # Reduced from 0.50%
                limit_validity_seconds = 300  # Reduced from 600
                if action.upper() == 'BUY':
                    entry_price = original_entry * (1 - limit_discount_pct / 100)
                else:
                    entry_price = original_entry * (1 + limit_discount_pct / 100)
                logger.info(f"⚠️ PEAK ENTRY: {symbol} at peak, no S/R nearby → LIMIT at {limit_discount_pct}% (₹{original_entry:.2f} → ₹{entry_price:.2f})")
            
            elif conf_normalized >= 9.0:
                # 🔥 STRONG SIGNAL: Use MARKET order - don't miss it!
                order_type = 'MARKET'
                limit_discount_pct = 0.0
                logger.info(f"🎯 STRONG SIGNAL: {symbol} ({conf_normalized:.1f}/10) → MARKET order (no S/R delay)")
            
            elif conf_normalized >= 7.5:
                # 📊 MEDIUM/NORMAL SIGNAL: Use very tight LIMIT (0.10%)
                # Changed from 0.15-0.30% to 0.10% - high chance of fill
                order_type = 'LIMIT'
                limit_discount_pct = 0.10
                limit_validity_seconds = 180  # 3 minutes
                if action.upper() == 'BUY':
                    entry_price = original_entry * (1 - limit_discount_pct / 100)
                else:
                    entry_price = original_entry * (1 + limit_discount_pct / 100)
                logger.info(f"🎯 TIGHT LIMIT: {symbol} ({conf_normalized:.1f}/10) → LIMIT at {limit_discount_pct}% (₹{original_entry:.2f} → ₹{entry_price:.2f})")
            
            else:
                # Lower confidence - use MARKET to avoid missing if signal is valid
                order_type = 'MARKET'
                limit_discount_pct = 0.0
                logger.info(f"🎯 DEFAULT MARKET: {symbol} ({conf_normalized:.1f}/10) → MARKET order")
            
            # Recalculate position value with new entry price
            position_value = final_quantity * entry_price
            
            signal = {
                'signal_id': f"{self.name}_{symbol}_{int(time_module.time())}",
                'symbol': symbol,
                'action': action.upper(),
                'quantity': final_quantity,  # 🎯 FIXED: Risk-based quantity
                'entry_price': round(entry_price, 2),
                'original_entry_price': round(original_entry, 2),  # 🎯 Track original LTP
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'order_type': order_type,  # 🎯 ADAPTIVE: MARKET or LIMIT
                'limit_price': round(entry_price, 2) if order_type == 'LIMIT' else None,
                'limit_validity_seconds': limit_validity_seconds if order_type == 'LIMIT' else None,
                'strategy': self.name,
                'strategy_name': self.__class__.__name__,
                'confidence': confidence,
                'quality_score': confidence,
                
                # 🔥 Trading mode indicators
                'is_intraday': is_intraday,
                'trading_mode': trading_mode,
                'timeframe': timeframe,
                'square_off_time': square_off_time,
                
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2),
                    'max_loss': round(actual_max_loss, 2),
                    'position_value': round(position_value, 2),
                    'margin_required': round(margin_required, 2)
                },
                'metadata': {
                    **metadata,
                    'signal_type': 'EQUITY',
                    'trading_mode': trading_mode,
                    'hybrid_mode': hybrid_mode,  # SCALP or SWING
                    'max_hold_minutes': max_hold_minutes,  # 10 for SCALP, 0 for SWING
                    'mtf_score': mtf_score,  # 0-3 MTF alignment score
                    'is_intraday': is_intraday,
                    'timeframe': timeframe,
                    'leverage_factor': INTRADAY_LEVERAGE,
                    'max_loss_pct': 2.0,
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.__class__.__name__,
                    'signal_source': 'strategy_engine'
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating equity signal: {e}")
            return None
    
    def _create_futures_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """
        Create FUTURES signal for leveraged intraday trading.
        
        FUTURES ADVANTAGES over OPTIONS:
        1. No theta decay (time value loss)
        2. Simpler Greeks (delta ≈ 1 for near-term)
        3. Lower margin than buying shares outright
        4. Direct price movement correlation
        
        FUTURES FORMAT:
        - Stock futures: SYMBOL + YYMMMFUT (e.g., RELIANCE25DECFUT)
        - Index futures: NIFTY25DECFUT, BANKNIFTY25DECFUT
        """
        try:
            from datetime import datetime
            
            # Get current month expiry suffix (e.g., 25DEC for December 2025)
            now = datetime.now()
            expiry_suffix = now.strftime('%y%b').upper() + 'FUT'  # e.g., 25DECFUT
            
            # Construct futures symbol
            futures_symbol = f"{symbol}{expiry_suffix}"
            
            # Calculate position sizing for futures
            # Futures lot sizes vary by symbol - use standard sizing
            lot_size = self._get_futures_lot_size(symbol)
            
            # Calculate risk-based quantity (respecting 1% max loss rule)
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share <= 0:
                risk_per_share = entry_price * 0.02  # Default 2% SL
            
            # Use stable base capital for sizing, but keep real-time available for feasibility.
            available_capital = self._get_available_capital()
            sizing_capital = self._get_base_capital_for_sizing()
            if sizing_capital <= 0:
                sizing_capital = available_capital if available_capital > 0 else 100000.0

            max_loss_amount = sizing_capital * 0.01  # 1% max loss (base)
            
            # Calculate quantity based on risk (in lots)
            qty_by_risk = int(max_loss_amount / (risk_per_share * lot_size)) * lot_size
            qty_by_risk = max(lot_size, qty_by_risk)  # At least 1 lot
            
            # Margin requirement check (futures typically need ~10-15% margin)
            margin_required = entry_price * qty_by_risk * 0.15  # 15% margin estimate
            if available_capital > 0 and margin_required > available_capital * 0.5:  # Don't use >50% of available now
                qty_by_risk = int((available_capital * 0.5) / (entry_price * 0.15))
                qty_by_risk = (qty_by_risk // lot_size) * lot_size  # Round to lot size
                qty_by_risk = max(lot_size, qty_by_risk)
            
            logger.info(f"📊 FUTURES SIGNAL: {futures_symbol}")
            logger.info(f"   Underlying: {symbol} @ ₹{entry_price:.2f}")
            logger.info(f"   Lot Size: {lot_size} | Qty: {qty_by_risk}")
            logger.info(f"   SL: ₹{stop_loss:.2f} | Target: ₹{target:.2f}")
            logger.info(f"   Margin Est: ₹{margin_required:,.0f}")
            
            # ============================================================
            # 🎯 ADAPTIVE ENTRY PRICING FOR FUTURES
            # ============================================================
            original_entry = entry_price
            order_type = 'LIMIT'  # Default for futures
            limit_discount_pct = 0.0
            limit_validity_seconds = 300
            
            conf_normalized = confidence if confidence > 1.0 else confidence * 10.0
            
            if conf_normalized >= 9.0:
                order_type = 'MARKET'
                logger.info(f"🎯 ADAPTIVE FUTURES: {symbol} STRONG signal ({conf_normalized:.1f}) → MARKET order")
            elif conf_normalized >= 8.0:
                order_type = 'LIMIT'
                limit_discount_pct = 0.10  # Tighter for futures (more liquid)
                limit_validity_seconds = 180
                if action.upper() == 'BUY':
                    entry_price = original_entry * (1 - limit_discount_pct / 100)
                else:
                    entry_price = original_entry * (1 + limit_discount_pct / 100)
                logger.info(f"🎯 ADAPTIVE FUTURES: {symbol} MEDIUM → LIMIT at {limit_discount_pct}% (₹{original_entry:.2f} → ₹{entry_price:.2f})")
            else:
                order_type = 'LIMIT'
                limit_discount_pct = 0.20
                limit_validity_seconds = 300
                if action.upper() == 'BUY':
                    entry_price = original_entry * (1 - limit_discount_pct / 100)
                else:
                    entry_price = original_entry * (1 + limit_discount_pct / 100)
                logger.info(f"🎯 ADAPTIVE FUTURES: {symbol} NORMAL → LIMIT at {limit_discount_pct}% (₹{original_entry:.2f} → ₹{entry_price:.2f})")
            
            # Create signal with futures-specific fields
            signal = {
                'symbol': futures_symbol,
                'underlying': symbol,
                'action': action,
                'entry_price': round(entry_price, 2),
                'original_entry_price': round(original_entry, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'quantity': qty_by_risk,
                'lot_size': lot_size,
                'confidence': confidence,
                'signal_type': 'FUTURES',
                'instrument_type': 'FUT',
                'exchange': 'NFO',
                'product': 'MIS',  # Intraday
                'order_type': order_type,  # 🎯 ADAPTIVE
                'limit_price': round(entry_price, 2) if order_type == 'LIMIT' else None,
                'limit_validity_seconds': limit_validity_seconds if order_type == 'LIMIT' else None,
                'validity': 'DAY',
                'margin_required': round(margin_required, 2),
                'risk_per_lot': round(risk_per_share * lot_size, 2),
                'strategy': self.strategy_name,
                'metadata': {
                    **metadata,
                    'underlying_symbol': symbol,
                    'futures_symbol': futures_symbol,
                    'expiry': expiry_suffix,
                    'lot_size': lot_size,
                    'is_futures': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating futures signal: {e}")
            # Fallback to equity if futures creation fails
            logger.warning(f"⚠️ FUTURES FALLBACK: Creating equity signal for {symbol}")
            return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
    
    def _get_futures_lot_size(self, symbol: str) -> int:
        """Get the lot size for futures contract of a symbol"""
        # Standard lot sizes for major F&O stocks (as of Dec 2024)
        # 🔧 CORRECTED Dec 2024: NIFTY=65, BANKNIFTY=35 (user confirmed)
        LOT_SIZES = {
            # Indices (CORRECTED Dec 2024 - user confirmed: NIFTY=65, BANKNIFTY=35)
            'NIFTY': 65, 'BANKNIFTY': 35, 'FINNIFTY': 40, 'MIDCPNIFTY': 50,
            'NIFTY-I': 65, 'BANKNIFTY-I': 35, 'FINNIFTY-I': 40, 'MIDCPNIFTY-I': 50,
            # Large caps
            'RELIANCE': 250, 'TCS': 150, 'HDFCBANK': 550, 'ICICIBANK': 700,
            'INFY': 300, 'HINDUNILVR': 300, 'ITC': 1600, 'SBIN': 750,
            'BHARTIARTL': 475, 'KOTAKBANK': 400, 'LT': 150, 'AXISBANK': 600,
            'ASIANPAINT': 300, 'MARUTI': 100, 'TITAN': 375, 'BAJFINANCE': 125,
            'HCLTECH': 350, 'WIPRO': 1500, 'SUNPHARMA': 700, 'ULTRACEMCO': 100,
            'TECHM': 300, 'TATAMOTORS': 1425, 'TATASTEEL': 1700, 'POWERGRID': 2700,
            'NTPC': 1500, 'ONGC': 1925, 'COALINDIA': 2100, 'BPCL': 1800,
            'IOC': 3250, 'GAIL': 2625, 'JSWSTEEL': 600, 'HINDALCO': 1075,
            'ADANIENT': 250, 'ADANIPORTS': 500, 'DRREDDY': 125, 'CIPLA': 650,
            'APOLLOHOSP': 250, 'EICHERMOT': 350, 'M&M': 350, 'BAJAJ-AUTO': 250,
            'HEROMOTOCO': 300, 'TATACONSUM': 450, 'BRITANNIA': 200, 'NESTLEIND': 50,
            'DIVISLAB': 100, 'GRASIM': 250, 'INDUSINDBK': 500, 'VEDL': 1550,
            'TATAPOWER': 2025, 'DLF': 825, 'SIEMENS': 75, 'TORNTPOWER': 275,
            # Add more as needed
        }
        
        # Handle -I suffix for index futures from TrueData
        clean_symbol = symbol.upper().replace('-I', '')
        
        # Return lot size or default to a reasonable value
        return LOT_SIZES.get(symbol.upper()) or LOT_SIZES.get(clean_symbol, 500)
    
    def _get_real_market_price(self, symbol: str) -> Optional[float]:
        """Get real market price from TrueData cache to ensure accurate strike calculation"""
        try:
            from data.truedata_client import live_market_data
            
            # Debug: Log available symbols in cache
            if live_market_data:
                available_symbols = list(live_market_data.keys())
                logger.info(f"🔍 DEBUG: TrueData cache has {len(available_symbols)} symbols")
                # Check if HDFC variants exist
                hdfc_symbols = [s for s in available_symbols if 'HDFC' in s.upper()]
                if hdfc_symbols:
                    logger.info(f"🔍 DEBUG: HDFC symbols in cache: {hdfc_symbols}")
                else:
                    logger.warning(f"⚠️ DEBUG: No HDFC symbols found in TrueData cache")
                    
            if live_market_data and symbol in live_market_data:
                stock_price = live_market_data[symbol].get('ltp', 0)
                logger.info(f"📊 Real market price for {symbol}: ₹{stock_price}")
                return float(stock_price) if stock_price > 0 else None
            else:
                logger.warning(f"⚠️ No real market data available for {symbol}")
                # Debug: Show what symbols are available
                if live_market_data:
                    sample_symbols = list(live_market_data.keys())[:10]
                    logger.info(f"🔍 DEBUG: Sample symbols in cache: {sample_symbols}")
                return None
        except Exception as e:
            logger.error(f"Error getting real market price for {symbol}: {e}")
            return None

    def _attempt_nearby_strike_rescue(self, options_symbol: str) -> Optional[Dict]:
        """Try nearby strikes (±2 steps) to find a tradable option LTP via Zerodha sync path.
        Returns {'symbol': new_symbol, 'ltp': price} if found, else None.
        """
        try:
            import re as _re
            m = _re.match(r'^([A-Z]+)(\d{2}[A-Z]{3}\d{2})(\d+)(CE|PE)$', options_symbol)
            if not m:
                return None
            underlying, expiry, strike_str, opt_type = m.groups()
            try:
                base_strike = int(strike_str)
            except Exception:
                return None

            # Get zerodha client
            if not getattr(self, 'zerodha_client', None):
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    if orchestrator:
                        self.zerodha_client = orchestrator.zerodha_client
                except Exception:
                    pass
            if not getattr(self, 'zerodha_client', None):
                return None

            # Use 50 as generic strike step for stocks; indices have 50 as well in most cases
            step = 50
            candidates = []
            for k in [-2, -1, 1, 2]:  # skip 0 because current strike already failed
                candidate_strike = base_strike + k * step
                if candidate_strike <= 0:
                    continue
                sym = f"{underlying}{expiry}{candidate_strike}{opt_type}"
                candidates.append(sym)

            for sym in candidates:
                try:
                    ltp = self.zerodha_client.get_options_ltp_sync(sym)
                    if ltp and ltp > 0:
                        return {'symbol': sym, 'ltp': float(ltp)}
                except Exception:
                    continue

            return None
        except Exception:
            return None

    async def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
        """Convert equity signal to options symbol with BUY-only approach - FIXED SYMBOL FORMAT"""
        
        try:
            # 🚨 CRITICAL FIX: Get REAL market price instead of using entry_price which might be wrong
            logger.info(f"🔍 DEBUG: Converting {underlying_symbol} to options with passed price ₹{current_price:.2f}")
            
            real_market_price = self._get_real_market_price(underlying_symbol)
            if real_market_price and real_market_price > 0:
                actual_price = real_market_price
                logger.info(f"🔍 PRICE CORRECTION: Using real market price ₹{actual_price:.2f} instead of ₹{current_price:.2f}")
            else:
                actual_price = current_price
                logger.warning(f"⚠️ Using passed price ₹{actual_price:.2f} (real price unavailable)")

            # 🚨 DEFENSIVE: Validate that actual_price is not zero/negative
            if actual_price <= 0:
                logger.error(f"❌ INVALID ACTUAL PRICE: {actual_price} for {underlying_symbol} - cannot proceed")
                return underlying_symbol, 'EQUITY'
                
            # Debug: Check if the price looks reasonable for this symbol
            if underlying_symbol == 'HDFCBANK' and actual_price < 800:
                logger.error(f"🚨 SUSPICIOUS PRICE: HDFCBANK price ₹{actual_price:.2f} seems too low (expected ~960)")
                logger.error(f"🚨 This will generate wrong strike prices. Investigate price source!")
            elif underlying_symbol == 'GAIL' and (actual_price < 150 or actual_price > 200):
                logger.warning(f"⚠️ GAIL price ₹{actual_price:.2f} outside expected range (150-200)")
            
            # 🎯 CRITICAL FIX: Convert to Zerodha's official symbol name FIRST
            from config.truedata_symbols import get_zerodha_symbol, is_fo_enabled
            zerodha_underlying = get_zerodha_symbol(underlying_symbol)
            
            # CRITICAL FIX: Check if symbol is F&O enabled before attempting options
            if not is_fo_enabled(zerodha_underlying):
                logger.warning(f"⚠️ {zerodha_underlying} is NOT F&O enabled - cannot trade options")
                logger.info(f"🔄 FALLBACK: Trading {zerodha_underlying} as EQUITY instead")
                return zerodha_underlying, 'EQUITY'
            
            # 🎯 CRITICAL FIX: Only BUY signals for options (no selling due to margin requirements)
            # 🔧 IMPORTANT: Only use indices with confirmed options contracts on Zerodha
            if zerodha_underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:  # REMOVED MIDCPNIFTY - no options
                # Index options - use volume-based strike selection for liquidity
                try:
                    expiry = await self._get_next_expiry(zerodha_underlying)
                    if not expiry:
                        logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - REJECTING SIGNAL")
                        return None, 'REJECTED'

                    # 🚨 DEFENSIVE: Check if expiry is valid before using
                    if not isinstance(expiry, str):
                        logger.error(f"❌ INVALID EXPIRY TYPE: {type(expiry)} = {expiry} for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                    strike = await self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)

                    # 🚨 DEFENSIVE: Check if strike is valid
                    if not isinstance(strike, int) or strike <= 0:
                        logger.error(f"❌ INVALID STRIKE: {strike} (type: {type(strike)}) for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                except Exception as await_error:
                    logger.error(f"❌ AWAIT ERROR in index options: {await_error}")
                    logger.error(f"   Error type: {type(await_error)}")
                    if "can't be used in 'await' expression" in str(await_error):
                        logger.error(f"🚨 CRITICAL: Attempted to await a non-coroutine for {zerodha_underlying}")
                        logger.error(f"   This indicates a method returning wrong type instead of coroutine")
                    return underlying_symbol, 'EQUITY'
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                # 🔧 CRITICAL FIX: Use Zerodha's EXACT format from API response
                # Zerodha format: NIFTY07AUG2524650CE (not NIFTY25AUG24650CE)
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                
                logger.info(f"🎯 INDEX SIGNAL: {underlying_symbol} → OPTIONS (F&O enabled)")
                logger.info(f"   Generated: {options_symbol}")
                return options_symbol, option_type
            elif zerodha_underlying in ['MIDCPNIFTY', 'SENSEX']:
                # 🚨 CRITICAL: These indices cannot be traded as equity - SKIP SIGNAL
                logger.warning(f"⚠️ {zerodha_underlying} cannot be traded as equity - SIGNAL REJECTED")
                return None, 'REJECTED'
            else:
                # Stock options - convert equity to options using ZERODHA NAME
                # 🎯 USER REQUIREMENT: Volume-based strike selection for liquidity
                try:
                    expiry = await self._get_next_expiry(zerodha_underlying)
                    if not expiry:
                        logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - FALLBACK TO EQUITY")
                        return None, 'REJECTED'

                    # 🚨 DEFENSIVE: Check if expiry is valid before using
                    if not isinstance(expiry, str):
                        logger.error(f"❌ INVALID EXPIRY TYPE: {type(expiry)} = {expiry} for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                    strike = await self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)

                    # 🚨 DEFENSIVE: Check if strike is valid
                    if not isinstance(strike, int) or strike <= 0:
                        logger.error(f"❌ INVALID STRIKE: {strike} (type: {type(strike)}) for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                except Exception as await_error:
                    logger.error(f"❌ AWAIT ERROR in stock options: {await_error}")
                    logger.error(f"   Error type: {type(await_error)}")
                    if "can't be used in 'await' expression" in str(await_error):
                        logger.error(f"🚨 CRITICAL: Attempted to await a non-coroutine for {zerodha_underlying}")
                        logger.error(f"   This indicates a method returning wrong type instead of coroutine")
                    return underlying_symbol, 'EQUITY'
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                
                # 🔧 CRITICAL FIX: Use Zerodha's exact symbol format for stocks too
                # Zerodha format: GAIL02SEP25150CE should be GAIL25SEP02150CE (YYMMMDDD format)
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                logger.debug(f"🔍 GENERATED OPTIONS SYMBOL: {options_symbol} (format: {zerodha_underlying} + {expiry} + {strike} + {option_type})")
                
                # 🚨 CRITICAL FIX: Validate if options symbol exists in Zerodha before using
                if self._validate_options_symbol_exists(options_symbol):
                    logger.info(f"🎯 ZERODHA OPTIONS SYMBOL: {underlying_symbol} → {options_symbol}")
                    logger.info(f"   Mapping: {underlying_symbol} → {zerodha_underlying}")
                    logger.info(f"   Strike: {strike}, Expiry: {expiry}, Type: {option_type}")
                    logger.info(f"   Used Price: ₹{actual_price:.2f} (real market price)")
                    return options_symbol, option_type
                else:
                    # 🎯 FALLBACK: Options not available, trade equity instead
                    logger.warning(f"⚠️ OPTIONS NOT AVAILABLE: {options_symbol} doesn't exist in Zerodha NFO")
                    logger.info(f"🔄 FALLBACK: Trading {zerodha_underlying} as EQUITY instead")
                    
                    return zerodha_underlying, 'EQUITY'
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            return underlying_symbol, 'CE'
    
    def _validate_options_symbol_exists(self, options_symbol: str, underlying_symbol: str = None) -> bool:
        """Validate if options symbol exists in Zerodha NFO instruments"""
        try:
            # Extract underlying symbol if not provided
            if not underlying_symbol:
                # Extract from options symbol (e.g., NIFTY14AUG2524550PE -> NIFTY)
                underlying_symbol = options_symbol.split('CE')[0].split('PE')[0]
                # Remove date patterns to get clean symbol
                import re
                underlying_symbol = re.sub(r'\d{2}[A-Z]{3}\d{2}', '', underlying_symbol)
            
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Zerodha client not available for options validation")
                return False  # Conservative: assume options don't exist
            
            # CRITICAL FIX: validate_options_symbol is async, but this method is sync
            # We need to run it synchronously here
            import asyncio
            try:
                # Get the current event loop or create new one
                try:
                    loop = asyncio.get_running_loop()
                    # We're already in an async context, create a task
                    future = asyncio.create_task(orchestrator.zerodha_client.validate_options_symbol(options_symbol))
                    # Can't await here in sync method, so return True for now (assume valid)
                    logger.warning(f"⚠️ Async validation deferred for {options_symbol} - assuming valid")
                    return True
                except RuntimeError:
                    # No running loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    is_valid = loop.run_until_complete(orchestrator.zerodha_client.validate_options_symbol(options_symbol))
            except Exception as async_err:
                logger.error(f"❌ Error in async validation: {async_err}")
                # Fallback: assume valid to allow trading
                return True
            
            if is_valid:
                logger.info(f"✅ OPTIONS VALIDATED: {options_symbol} exists in Zerodha NFO")
                return True
            else:
                logger.warning(f"❌ OPTIONS NOT FOUND: {options_symbol} doesn't exist in Zerodha NFO")
                
                # Debug what options are actually available
                try:
                    # Extract expiry from options symbol for debugging
                    import re
                    match = re.search(r'(\d{2}[A-Z]{3}\d{2})', options_symbol)
                    if match:
                        expiry_str = match.group(1)
                        import asyncio
                        asyncio.create_task(self._debug_available_options(underlying_symbol, expiry_str))
                except Exception as debug_e:
                    logger.error(f"Debug options failed: {debug_e}")
                
                return False
                
        except Exception as e:
            logger.error(f"Error validating options symbol {options_symbol}: {e}")
            return False  # Conservative: assume options don't exist
    
    async def _debug_available_options(self, underlying_symbol: str, expiry_str: str) -> None:
        """Debug function to check what options are actually available"""
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Cannot debug options - Zerodha client not available")
                return
            
            logger.info(f"🔍 DEBUGGING AVAILABLE OPTIONS for {underlying_symbol} expiry {expiry_str}")
            
            # Get all NFO instruments
            try:
                instruments = await orchestrator.zerodha_client.get_instruments("NFO")

                # 🚨 VALIDATION: Ensure instruments is a list
                if instruments is None:
                    logger.error("❌ get_instruments returned None")
                    return
                elif isinstance(instruments, int):
                    logger.error(f"❌ get_instruments returned int instead of list: {instruments}")
                    return
                elif not isinstance(instruments, list):
                    logger.error(f"❌ get_instruments returned {type(instruments)} instead of list: {instruments}")
                    return
                elif not instruments:
                    logger.error("❌ No NFO instruments available")
                    return

            except Exception as instruments_error:
                logger.error(f"❌ Error getting NFO instruments: {instruments_error}")
                logger.error(f"   Error type: {type(instruments_error)}")
                if "can't be used in 'await' expression" in str(instruments_error):
                    logger.error("🚨 CRITICAL: Zerodha API returned non-coroutine for instruments")
                return
            
            # Find all options for this underlying and expiry
            available_options = []
            for inst in instruments:
                trading_symbol = inst.get('tradingsymbol', '')
                if (underlying_symbol.upper() in trading_symbol.upper() and 
                    expiry_str in trading_symbol and
                    inst.get('instrument_type') in ['CE', 'PE']):
                    available_options.append({
                        'symbol': trading_symbol,
                        'strike': inst.get('strike', 0),
                        'type': inst.get('instrument_type'),
                        'expiry': inst.get('expiry')
                    })
            
            if available_options:
                # Sort by strike price
                available_options.sort(key=lambda x: float(x['strike']) if x['strike'] else 0)
                
                logger.info(f"✅ FOUND {len(available_options)} options for {underlying_symbol} {expiry_str}")
                
                # Show CE options
                ce_options = [opt for opt in available_options if opt['type'] == 'CE']
                if ce_options:
                    strikes = [str(int(float(opt['strike']))) for opt in ce_options[:10]]  # First 10
                    logger.info(f"   CE Strikes: {', '.join(strikes)}{'...' if len(ce_options) > 10 else ''}")
                
                # Show PE options  
                pe_options = [opt for opt in available_options if opt['type'] == 'PE']
                if pe_options:
                    strikes = [str(int(float(opt['strike']))) for opt in pe_options[:10]]  # First 10
                    logger.info(f"   PE Strikes: {', '.join(strikes)}{'...' if len(pe_options) > 10 else ''}")
            else:
                logger.error(f"❌ NO OPTIONS FOUND for {underlying_symbol} {expiry_str}")
                
                # Check if the underlying exists at all
                all_underlyings = set()
                for inst in instruments:
                    trading_symbol = inst.get('tradingsymbol', '')
                    if inst.get('instrument_type') in ['CE', 'PE']:
                        # Extract underlying from options symbol
                        import re
                        match = re.match(r'^([A-Z]+)', trading_symbol)
                        if match:
                            all_underlyings.add(match.group(1))
                
                if underlying_symbol.upper() not in all_underlyings:
                    logger.error(f"❌ UNDERLYING NOT FOUND: {underlying_symbol} not in NFO options")
                    similar = [u for u in all_underlyings if underlying_symbol.upper()[:4] in u]
                    if similar:
                        logger.info(f"   Similar underlyings: {', '.join(list(similar)[:5])}")
                else:
                    logger.error(f"❌ NO OPTIONS for expiry {expiry_str} - check expiry date")
                        
        except Exception as e:
            logger.error(f"Error debugging available options: {e}")
    
    def _get_atm_strike(self, symbol: str, price: float) -> int:
        """Get ATM strike for index options - FIXED for Zerodha's actual intervals"""
        # 🚨 CRITICAL FIX: Based on user feedback "for indices only in 100"
        # All major indices use 100-point intervals in Zerodha
        
        if symbol == 'NIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 NIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'BANKNIFTY':
            strike = round(price / 100) * 100  # Already correct
            logger.info(f"🎯 BANKNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'FINNIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 FINNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        else:
            # Fallback for other indices
            strike = round(price / 100) * 100
            logger.info(f"🎯 {symbol} STRIKE: ₹{price} → {strike} (100-point interval fallback)")
            return int(strike)
    
    def _get_atm_strike_for_stock(self, current_price: float) -> int:
        """Get ATM strike for stock options - FIXED to use Zerodha's actual intervals"""
        try:
            # 🔍 DEBUG: Log current price and strike calculation
            logger.info(f"🔍 DEBUG: Calculating ATM strike for stock price: ₹{current_price}")
            
            # 🚨 CRITICAL FIX: Zerodha only offers strikes in multiples of 50 for most stocks
            # Based on user feedback: "for option price if we see only the prices which are in multiple of 50"
            interval = 50  # Fixed interval for all stocks to match Zerodha availability
            
            # Round to nearest 50
            atm_strike = round(current_price / interval) * interval
            
            logger.info(f"🎯 STOCK STRIKE CALCULATION (FIXED):")
            logger.info(f"   Current Price: ₹{current_price}")
            logger.info(f"   Strike Interval: {interval} (Zerodha standard)")
            logger.info(f"   ATM Strike: {int(atm_strike)}")
            logger.info(f"   Available: {int(atm_strike-50)}, {int(atm_strike)}, {int(atm_strike+50)}")
            
            return int(atm_strike)
            
        except Exception as e:
            logger.error(f"Error calculating ATM strike for stock: {e}")
            # Fallback to nearest 50 (Zerodha standard)
            fallback_strike = round(current_price / 50) * 50
            logger.warning(f"⚠️ FALLBACK STRIKE: {int(fallback_strike)} (rounded to nearest 50)")
            return int(fallback_strike)
      
    async def _get_next_expiry(self, underlying_symbol: str = "NIFTY") -> str:
        """DYNAMIC EXPIRY SELECTION: Get optimal expiry based on strategy requirements"""
        # 🔍 DEBUG: Add comprehensive logging for expiry date debugging
        logger.info(f"🔍 DEBUG: Getting next expiry date...")
        
        # Try to get real expiry dates from Zerodha first
        try:
            available_expiries = await self._get_available_expiries_from_zerodha(underlying_symbol)
        except Exception as e:
            logger.error(f"Error fetching expiries from Zerodha: {e}")
            available_expiries = []
        
        if available_expiries:
            logger.info(f"✅ Found {len(available_expiries)} expiry dates from Zerodha API")
            for i, exp in enumerate(available_expiries[:3]):  # Log first 3
                logger.info(f"   {i+1}. {exp['formatted']} ({exp['date']})")
            
            # Prefer nearest weekly first; if LTP missing later, logic will escalate to next
            optimal_expiry = await self._get_optimal_expiry_for_strategy(underlying_symbol, "nearest_weekly")

            # 🚨 DEFENSIVE: Validate optimal_expiry before returning
            if optimal_expiry is None:
                logger.error(f"❌ _get_optimal_expiry_for_strategy returned None for {underlying_symbol}")
                logger.error("   This should not happen - falling back to calculated expiry")
                # Continue to fallback logic below
            elif not isinstance(optimal_expiry, str):
                logger.error(f"❌ _get_optimal_expiry_for_strategy returned invalid type: {type(optimal_expiry)} = {optimal_expiry}")
                logger.error("   This should not happen - falling back to calculated expiry")
                optimal_expiry = None
            else:
                logger.info(f"🎯 SELECTED EXPIRY: {optimal_expiry}")
                return optimal_expiry
        else:
            logger.warning("⚠️ No expiry dates from Zerodha API - using calculated fallback")
            # Fallback: for stocks, choose last Thursday of current/next month; for indices, next Thursday
            from datetime import datetime, timedelta
            today = datetime.now().date()
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            is_index = zerodha_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']

            def _last_thursday(year: int, month: int):
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                d = datetime(year, month, last_day).date()
                # Thursday = 3
                offset = (d.weekday() - 3) % 7
                return d - timedelta(days=offset)

            if is_index:
                days_ahead = (3 - today.weekday()) % 7  # next Thursday including today
                if days_ahead == 0:
                    days_ahead = 7
                fallback_date = today + timedelta(days=days_ahead)
            else:
                # Stock options: monthly expiry (last Thursday). If today >= last Thursday, move to next month
                lt = _last_thursday(today.year, today.month)
                if today >= lt:
                    year = today.year + (1 if today.month == 12 else 0)
                    month = 1 if today.month == 12 else today.month + 1
                    lt = _last_thursday(year, month)
                fallback_date = lt

            # CRITICAL FIX: Use Zerodha format YYMM not DDMMMYY
            fallback_expiry = fallback_date.strftime("%y%b").upper()
            logger.info(f"🔄 FALLBACK EXPIRY: {fallback_expiry} ({'monthly last Thursday' if not is_index else 'next Thursday'})")
            return fallback_expiry
    
    async def _get_optimal_expiry_for_strategy(self, underlying_symbol: str = "NIFTY", preference: str = "nearest_weekly") -> str:
        """
        Get optimal expiry based on strategy requirements - FIXED ZERODHA FORMAT
        
        Args:
            preference: "nearest_weekly", "nearest_monthly", "next_weekly", "max_time_decay"
        """
        try:
            # Map TrueData symbol to Zerodha symbol before fetching expiries
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            available_expiries = await self._get_available_expiries_from_zerodha(zerodha_symbol)
        except Exception as e:
            logger.error(f"Error fetching expiries from Zerodha: {e}")
            available_expiries = []
        
        if not available_expiries:
            # 🚨 NO FALLBACK: Return None if no real expiries from Zerodha API
            logger.error("❌ No expiries from Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        today = datetime.now().date()
        
        # 🚨 CRITICAL FIX: Use next day as cutoff to avoid expired/expiring options
        # Today is July 31, so July 25 expiry has already passed
        cutoff_date = today + timedelta(days=1)  # Use tomorrow as cutoff for safety
        
        # Filter future expiries only
        future_expiries = [exp for exp in available_expiries if exp['date'] >= cutoff_date]
        
        if not future_expiries:
            # 🚨 NO FALLBACK: Return None if no future expiries found
            logger.error("❌ No future expiries found in Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        # Sort by date
        future_expiries.sort(key=lambda x: x['date'])
        
        # 🎯 SMART EXPIRY SELECTION: Indices vs Stocks
        # Map TrueData symbols to Zerodha symbols for proper identification
        zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
        is_index = zerodha_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']
        
        # 🚨 CRITICAL FIX 2025-12-02: ALWAYS SKIP NEAREST EXPIRY, USE NEXT ONE
        # User requirement: Never buy nearest expiry options, always use next expiry
        # This avoids theta decay and allows proper time for price movement
        
        if len(future_expiries) < 2:
            logger.error(f"❌ NOT ENOUGH EXPIRIES: Need at least 2 expiries to skip nearest for {zerodha_symbol}")
            return None
        
        # Sort by date to get proper order
        future_expiries.sort(key=lambda x: x['date'])
        
        # 🔥 ALWAYS SKIP NEAREST EXPIRY - Use index [1] not [0]
        nearest_expiry = future_expiries[0]
        next_expiry = future_expiries[1]
        
        days_to_nearest = (nearest_expiry['date'] - today).days
        days_to_next = (next_expiry['date'] - today).days
        
        logger.info(f"📊 EXPIRY SELECTION for {zerodha_symbol}:")
        logger.info(f"   🚫 SKIPPING NEAREST: {nearest_expiry['formatted']} ({days_to_nearest} days)")
        logger.info(f"   ✅ USING NEXT: {next_expiry['formatted']} ({days_to_next} days)")
        
        # Use next expiry (skip nearest)
        nearest = next_expiry
        
        if is_index:
            logger.info(f"📊 INDEX {zerodha_symbol}: Using NEXT expiry (skipped nearest) → {days_to_next} days")
        else:
            # For stocks, check if we have monthly expiry in the next options
            if next_expiry.get('is_monthly', False):
                logger.info(f"📊 STOCK {zerodha_symbol}: Using NEXT MONTHLY expiry → {days_to_next} days")
            else:
                logger.info(f"📊 STOCK {zerodha_symbol}: Using NEXT expiry → {days_to_next} days")
            
        # Override with preference if specified
        if preference == "next_weekly" and len(future_expiries) > 1:
            nearest = future_expiries[1]
            logger.info(f"   Override: Using next expiry as requested")
        
        # 🔧 CRITICAL FIX: Convert to Zerodha format (25JUL instead of 31JUL25)
        exp_date = nearest['date']
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 25SEP (YY + MMM), NOT 30SEP25
        try:
            # 🚨 DEFENSIVE: Validate date components before formatting
            if not (1 <= exp_date.month <= 12):
                logger.error(f"❌ INVALID MONTH: {exp_date.month} for {underlying_symbol}")
                return None

            if not (1 <= exp_date.day <= 31):
                logger.error(f"❌ INVALID DAY: {exp_date.day} for {underlying_symbol}")
                return None

            zerodha_expiry = f"{str(exp_date.year)[-2:]}{month_names[exp_date.month - 1]}"

            # 🚨 DEFENSIVE: Validate the formatted result
            if not isinstance(zerodha_expiry, str) or len(zerodha_expiry) != 5:
                logger.error(f"❌ INVALID EXPIRY FORMAT: {zerodha_expiry} (type: {type(zerodha_expiry)}, length: {len(zerodha_expiry)}) for {underlying_symbol}")
                return None
        
            logger.info(f"🎯 OPTIMAL EXPIRY: {zerodha_expiry} (from {nearest['formatted']})")
            logger.info(f"   Date: {exp_date}, Days ahead: {(exp_date - today).days}")
            
            return zerodha_expiry

        except Exception as format_error:
            logger.error(f"❌ EXPIRY FORMATTING ERROR for {underlying_symbol}: {format_error}")
            logger.error(f"   Date object: {exp_date} (type: {type(exp_date)})")
            logger.error(f"   Month: {getattr(exp_date, 'month', 'MISSING')} Day: {getattr(exp_date, 'day', 'MISSING')} Year: {getattr(exp_date, 'year', 'MISSING')}")
            return None
    
    async def _get_available_expiries_from_zerodha(self, underlying_symbol: str) -> List[Dict]:
        """
        Fetch available expiry dates from Zerodha instruments API
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                # During backtesting, Zerodha client won't be available - use fallback
                if hasattr(self, 'backtest_mode') and self.backtest_mode:
                    logger.info("📊 In backtest mode - using calculated expiries")
                else:
                    logger.error("❌ Zerodha client not available for expiry lookup")
                return []
            
            # 🚨 DEFENSIVE: Try to get expiries for the specific underlying symbol first
            try:
                logger.info(f"🔍 Trying to get expiries directly for {zerodha_symbol}")
                expiries = await orchestrator.zerodha_client.get_available_expiries_for_symbol(zerodha_symbol)

                # 🚨 DEFENSIVE: Validate the response
                if expiries is None:
                    logger.error(f"❌ get_available_expiries_for_symbol returned None for {zerodha_symbol}")
                    expiries = []
                elif isinstance(expiries, int):
                    logger.error(f"❌ get_available_expiries_for_symbol returned int instead of list: {expiries} for {zerodha_symbol}")
                    expiries = []
                elif not isinstance(expiries, list):
                    logger.error(f"❌ get_available_expiries_for_symbol returned {type(expiries)} instead of list: {expiries} for {zerodha_symbol}")
                    expiries = []
                elif expiries:  # List is not empty
                    logger.info(f"✅ Found {len(expiries)} expiries for {zerodha_symbol}")
                    return expiries
            except Exception as direct_err:
                logger.warning(f"⚠️ Direct expiry fetch failed for {zerodha_symbol}: {direct_err}")

            # Fallback: Try common symbols if direct fetch failed
            logger.info(f"🔄 Falling back to common symbols for expiry lookup")

            # Try to get expiries for common underlying symbols we trade
            common_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'POWERGRID', 'RELIANCE', 'TCS']
            
            for symbol in common_symbols:
                try:
                    logger.info(f"🔍 Trying common symbol {symbol} for expiry data")
                    expiries = await orchestrator.zerodha_client.get_available_expiries_for_symbol(symbol)

                    # 🚨 DEFENSIVE: Validate the response
                    if expiries is None:
                        logger.warning(f"⚠️ get_available_expiries_for_symbol returned None for {symbol}")
                        continue
                    elif isinstance(expiries, int):
                        logger.error(f"❌ get_available_expiries_for_symbol returned int instead of list: {expiries} for {symbol}")
                        continue
                    elif not isinstance(expiries, list):
                        logger.error(f"❌ get_available_expiries_for_symbol returned {type(expiries)} instead of list: {expiries} for {symbol}")
                        continue
                    elif expiries:  # List is not empty
                            logger.info(f"📅 Using expiries from {symbol}: {len(expiries)} found")
                            return expiries
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching expiries for {symbol}: {e}")
                    continue
            
            # If no expiries found from API, REJECT signal
            logger.error("❌ No expiries found from Zerodha API - NO FALLBACK")
            # 🚨 FINAL VALIDATION: Ensure we return a valid list of dictionaries
            if not isinstance(expiries, list):
                logger.error(f"❌ expiries is not a list: {type(expiries)} = {expiries}")
            return []
            
            # Validate each expiry entry
            valid_expiries = []
            for expiry in expiries:
                if isinstance(expiry, dict) and 'date' in expiry and 'formatted' in expiry:
                    valid_expiries.append(expiry)
                else:
                    logger.warning(f"⚠️ Filtering out invalid expiry entry: {expiry} (type: {type(expiry)})")

            return valid_expiries
            
        except Exception as e:
            logger.error(f"❌ Error fetching available expiries: {e}")
            # Add debug info to help identify the issue
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return []
    
    def _get_fallback_expiries(self) -> List[Dict]:
        """Generate realistic weekly expiries when API is unavailable"""
        today = datetime.now().date()
        expiries = []
        
        # Add all Thursdays for next 8 weeks
        current_date = today
        for weeks_ahead in range(8):
            # Find next Thursday
            days_ahead = (3 - current_date.weekday()) % 7  # Thursday = 3
            if days_ahead == 0 and current_date == today:
                days_ahead = 7  # If today is Thursday, get next Thursday
                
            thursday = current_date + timedelta(days=days_ahead)
            
            # Format for Zerodha: 25AUG (YY + MMM)
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            formatted = f"{str(thursday.year)[-2:]}{month_names[thursday.month - 1]}"
            
            # Determine if it's monthly (last Thursday of month)
            next_week = thursday + timedelta(days=7)
            is_monthly = next_week.month != thursday.month
            
            expiries.append({
                'date': thursday,
                'formatted': formatted,
                'is_weekly': True,
                'is_monthly': is_monthly
            })
            
            current_date = thursday + timedelta(days=1)  # Move to next week
        
        logger.info(f"📅 Generated {len(expiries)} fallback expiries: {[e['formatted'] for e in expiries[:3]]}...")
        return expiries
    
    def _calculate_next_thursday_fallback(self) -> str:
        """Fallback calculation for next Thursday when API is unavailable - FIXED ZERODHA FORMAT"""
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
        if days_ahead == 0:
            days_ahead = 7  # If today is Thursday, get next Thursday
            
        next_thursday = today + timedelta(days=days_ahead)
        
        # 🚨 CRITICAL DEBUG: Log calculation details
        logger.info(f"🔍 EXPIRY CALCULATION DEBUG:")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')} (weekday: {today.weekday()})")
        logger.info(f"   Days ahead to Thursday: {days_ahead}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        
        # 🔧 CRITICAL FIX: Format for Zerodha - their format is 25JUL (not 31JUL25)
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 14AUG25 (DD + MMM + YY), NOT 14AUG (DD + MMM)
        expiry_formatted = f"{next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}"
        
        logger.info(f"📅 ZERODHA EXPIRY FORMAT: {expiry_formatted}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')}")
        logger.info(f"   OLD FORMAT would be: {next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}")
        logger.info(f"   NEW ZERODHA FORMAT: {expiry_formatted}")
        
        return expiry_formatted
    
    def _get_last_thursday_of_month(self, year: int, month: int) -> datetime:
        """Get the last Thursday of a given month - DEPRECATED: Use dynamic expiry selection"""
        import calendar
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        
        # Find the last Thursday
        last_date = datetime(year, month, last_day)
        
        # Thursday is 3, so we need to go back to find the last Thursday
        days_back = (last_date.weekday() - 3) % 7  # 3 = Thursday
        if days_back == 0 and last_date.weekday() == 3:
            # Already a Thursday
            return last_date
        else:
            # Go back to find the last Thursday
            last_thursday = last_date - timedelta(days=days_back)
            return last_thursday
    
    def _truncate_symbol_for_options(self, symbol: str) -> str:
        """Truncate symbol names for options format"""
        # Common truncations for stock options
        truncation_map = {
            'ICICIBANK': 'ICICIBANK',  # Actually, let's test with full name first
            'HDFCBANK': 'HDFCBANK',
            'RELIANCE': 'RELIANCE',
            'BHARTIARTL': 'BHARTIARTL'
        }
        return truncation_map.get(symbol, symbol)
    
    def _is_cooldown_passed(self) -> bool:
        """Check if cooldown period has passed"""
        if not self.last_signal_time:
            return True
        return (datetime.now() - self.last_signal_time).total_seconds() >= self.signal_cooldown
    
    async def send_to_trade_engine(self, signal: Dict):
        """Send signal to trade engine for execution"""
        try:
            # Get orchestrator instance and send signal to trade engine
            from src.core.orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                await orchestrator.trade_engine.process_signals([signal])
                logger.info(f"✅ Signal sent to trade engine: {signal['symbol']} {signal['action']}")
                return True
            else:
                logger.error(f"❌ Trade engine not available for signal: {signal['symbol']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending signal to trade engine: {e}")
            return False
    
    async def initialize(self):
        """Initialize the strategy - to be implemented by subclasses"""
        logger.info(f"Initializing {self.name} strategy")
        self.is_active = True
    
    def should_analyze_symbol(self, symbol: str, market_data: Dict) -> bool:
        """Determine if this symbol should be analyzed based on strategy criteria"""
        try:
            # Skip if already at max capacity
            if len(self.active_symbols) >= self.max_symbols_to_analyze:
                return symbol in self.active_symbols  # Only analyze if already tracking
            
            # Check symbol-specific filters
            symbol_data = market_data.get(symbol, {})
            
            # Volume filter
            if 'min_volume' in self.symbol_filters:
                volume = symbol_data.get('volume', 0)
                if volume < self.symbol_filters['min_volume']:
                    return False
            
            # Price range filter
            if 'min_price' in self.symbol_filters or 'max_price' in self.symbol_filters:
                ltp = symbol_data.get('ltp', 0)
                if 'min_price' in self.symbol_filters and ltp < self.symbol_filters['min_price']:
                    return False
                if 'max_price' in self.symbol_filters and ltp > self.symbol_filters['max_price']:
                    return False
            
            # Change percent filter (volatility)
            if 'min_change_percent' in self.symbol_filters:
                change_pct = abs(symbol_data.get('change_percent', 0))
                if change_pct < self.symbol_filters['min_change_percent']:
                    return False
            
            # Strategy-specific watchlist
            if self.watchlist and symbol not in self.watchlist:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in symbol filter for {symbol}: {e}")
            return False
    
    def update_active_symbols(self, market_data: Dict):
        """Update list of actively analyzed symbols based on current market conditions"""
        try:
            # Remove symbols with no recent data
            symbols_to_remove = set()
            for symbol in self.active_symbols:
                if symbol not in market_data:
                    symbols_to_remove.add(symbol)
            
            for symbol in symbols_to_remove:
                self.active_symbols.discard(symbol)
                logger.info(f"🔄 Removed {symbol} from active analysis (no data)")
            
            # Add new promising symbols if under capacity
            if len(self.active_symbols) < self.max_symbols_to_analyze:
                # Sort symbols by selection criteria (volume, volatility, etc)
                candidates = []
                for symbol, data in market_data.items():
                    if symbol not in self.active_symbols and self.should_analyze_symbol(symbol, market_data):
                        score = self._calculate_symbol_score(symbol, data)
                        candidates.append((symbol, score))
                
                # Add top candidates
                candidates.sort(key=lambda x: x[1], reverse=True)
                for symbol, score in candidates[:self.max_symbols_to_analyze - len(self.active_symbols)]:
                    self.active_symbols.add(symbol)
                    logger.info(f"➕ Added {symbol} to active analysis (score: {score:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating active symbols: {e}")
    
    def _calculate_symbol_score(self, symbol: str, data: Dict) -> float:
        """Calculate score for symbol selection (higher = better)"""
        try:
            score = 0.0
            
            # Volume score (normalized)
            volume = data.get('volume', 0)
            if volume > 1000000:
                score += 10.0
            elif volume > 500000:
                score += 5.0
            elif volume > 100000:
                score += 2.0
            
            # Volatility score
            change_pct = abs(data.get('change_percent', 0))
            score += min(change_pct * 2, 10.0)  # Cap at 10
            
            # Liquidity score (based on price)
            ltp = data.get('ltp', 0)
            if 100 < ltp < 5000:  # Sweet spot for liquidity
                score += 5.0
            
            # Momentum score
            if data.get('change_percent', 0) > 0:
                score += 2.0  # Slight bias towards gainers
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating score for {symbol}: {e}")
            return 0.0
    
    async def on_market_data(self, data: Dict):
        """Handle incoming market data - to be implemented by subclasses"""
        # Update active symbols before processing
        self.update_active_symbols(data)
        
        # Store historical data only for active symbols
        for symbol in self.active_symbols:
            if symbol in data:
                self._update_historical_data(symbol, data[symbol])
    
    def _update_historical_data(self, symbol: str, data: Dict):
        """Update historical data for a symbol"""
        try:
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            # Add current data point
            data_point = {
                'timestamp': data.get('timestamp', datetime.now()),
                'open': data.get('open', 0),
                'high': data.get('high', 0),
                'low': data.get('low', 0),
                'close': data.get('close', data.get('ltp', 0)),
                'volume': data.get('volume', 0),
                'ltp': data.get('ltp', 0),
                'change_percent': data.get('change_percent', 0)
            }
            
            self.historical_data[symbol].append(data_point)
            
            # Trim history if needed
            if len(self.historical_data[symbol]) > self.max_history:
                self.historical_data[symbol].pop(0)
                
        except Exception as e:
            logger.error(f"Error updating historical data for {symbol}: {e}")
        
        pass
    
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 

    def _get_options_premium(self, options_symbol: str, underlying_symbol: str) -> float:
        """Get real-time premium for options symbol with enhanced fallbacks"""
        if not self._is_trading_hours():
            logger.warning(f"⚠️ Market closed - cannot get options premium for {options_symbol}")
            return 0.0
        
        # REMOVED: Stock options restriction - fixing root LTP issue instead
        # Users confirmed stock options should work, need to debug actual LTP failures
        
        try:
            # NEW: Dynamic fetch for zerodha_client if missing
            if not hasattr(self, 'zerodha_client') or self.zerodha_client is None:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator:
                    self.zerodha_client = orchestrator.zerodha_client
                    logger.info(f"✅ Dynamically fetched Zerodha client for {self.name}")
                else:
                    logger.warning(f"⚠️ Could not fetch Zerodha client dynamically - skipping Zerodha fallback")
            
            # Primary - Zerodha LTP (sync version)
            if self.zerodha_client:
                logger.info(f"🔍 DEBUGGING: Fetching Zerodha LTP for {options_symbol}")
                zerodha_ltp = self.zerodha_client.get_options_ltp_sync(options_symbol)
                logger.info(f"📊 Zerodha LTP Response: {zerodha_ltp} for {options_symbol}")
                if zerodha_ltp and zerodha_ltp > 0:
                    logger.info(f"✅ Primary Zerodha LTP for {options_symbol}: ₹{zerodha_ltp}")
                    
                    # 🚨 CRITICAL: Reject ultra-low premium options (< ₹1.00)
                    if zerodha_ltp < 1.00:
                        logger.warning(f"⚠️ REJECTING LOW PREMIUM: {options_symbol} premium ₹{zerodha_ltp:.2f} < ₹1.00 minimum")
                        logger.warning(f"   Reason: Insufficient liquidity and tick size constraints for proper risk management")
                        return 0.0  # Return 0 to trigger rejection
                    
                    return zerodha_ltp
                else:
                    logger.warning(f"⚠️ Zerodha LTP is zero or None: {zerodha_ltp} for {options_symbol}")
            else:
                logger.warning(f"⚠️ No Zerodha client available for LTP fetching")
            
            # Primary Fallback: Zerodha bid/ask average
            if self.zerodha_client:
                try:
                    full_symbol = f"NFO:{options_symbol}"
                    quote = self.zerodha_client.kite.quote(full_symbol)
                    if quote and full_symbol in quote:
                        data = quote[full_symbol]
                        bid = data.get('depth', {}).get('buy', [{}])[0].get('price', 0)
                        ask = data.get('depth', {}).get('sell', [{}])[0].get('price', 0)
                        if bid > 0 and ask > 0:
                            avg_price = (bid + ask) / 2
                            logger.info(f"✅ Zerodha bid/ask average (primary fallback) for {options_symbol}: ₹{avg_price} (bid: ₹{bid}, ask: ₹{ask})")
                            return avg_price
                        elif bid > 0:
                            logger.info(f"✅ Using Zerodha bid price (primary fallback) for {options_symbol}: ₹{bid}")
                            return bid
                        elif ask > 0:
                            logger.info(f"✅ Using Zerodha ask price (primary fallback) for {options_symbol}: ₹{ask}")
                            return ask
                    logger.warning(f"⚠️ Zerodha quote primary fallback returned zero for {options_symbol}")
                except Exception as quote_err:
                    logger.warning(f"⚠️ Zerodha quote primary fallback failed for {options_symbol}: {quote_err}")
            
            # 🚨 INVESTIGATION: Log detailed error information for debugging
            logger.error(f"❌ ALL ZERODHA METHODS FAILED for {options_symbol}")
            logger.error(f"   - LTP method failed")
            logger.error(f"   - Quote method failed")
            logger.error(f"   - Need to investigate specific API endpoint issues")
            return 0.0
        
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR getting options premium for {options_symbol}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return 0.0
    
    def _round_to_tick_size(self, price: float) -> float:
        """Round options price to proper tick size (₹0.05 for options)"""
        try:
            from src.utils.helpers import round_price_to_tick
            return round_price_to_tick(price, 0.05)  # Options tick size is ₹0.05
        except ImportError:
            # Fallback if import fails
            return round(price / 0.05) * 0.05

    
    def _calculate_options_levels(self, options_entry_price: float, original_stop_loss: float, 
                                 original_target: float, option_type: str, action: str, underlying_symbol: str) -> tuple:
        """Dynamically calculate stop_loss and target for options premium using REAL ATR"""
        try:
            # CRITICAL FIX: Calculate REAL ATR for the underlying symbol
            atr = None
            atr_percent = None
            
            # Try to get live market data for ATR calculation
            try:
                from data.truedata_client import live_market_data
                if underlying_symbol in live_market_data:
                    market_data = live_market_data[underlying_symbol]
                    high = float(market_data.get('high', 0))
                    low = float(market_data.get('low', 0))
                    ltp = float(market_data.get('ltp', 0))
                    
                    if high > 0 and low > 0 and ltp > 0:
                        atr = self.calculate_atr(underlying_symbol, high, low, ltp)
                        atr_percent = (atr / ltp) * 100 if ltp > 0 else 0
                        logger.info(f"📊 ATR-BASED RISK: {underlying_symbol} - ATR=₹{atr:.2f} ({atr_percent:.2f}%)")
            except Exception as atr_err:
                logger.debug(f"Could not calculate ATR for {underlying_symbol}: {atr_err}")
            
            # If ATR calculation succeeded, use it; otherwise use volatility-based fallback
            if atr_percent and 0.5 <= atr_percent <= 10:  # Sanity check: 0.5% - 10% range
                # 🚨 OPTIONS FIX: Much tighter stops - options decay fast, can't afford wide stops
                # Max 6% stop loss (was 10%) - options need quick exits on wrong direction
                base_risk_percent = min(atr_percent * 0.7, 0.06)  # 0.7x ATR (was 1.0x), max 6% (was 10%)
                logger.info(f"✅ USING ATR: {underlying_symbol} - Risk={base_risk_percent*100:.1f}% (0.7x ATR, TIGHT OPTIONS STOP)")
            else:
                # Fallback: Even tighter for options without ATR data
                base_risk_percent = min(self._get_dynamic_risk_percentage(underlying_symbol, options_entry_price), 0.06)
                logger.info(f"⚠️ FALLBACK: {underlying_symbol} - Risk={base_risk_percent*100:.1f}% (capped at 6%)")
            
            # DYNAMIC FIX: Use market-based reward-to-risk ratio for quality trading
            target_risk_reward_ratio = self._get_dynamic_target_risk_reward_ratio(underlying_symbol, options_entry_price, option_type)
            
            # Calculate risk and reward amounts
            risk_amount = options_entry_price * base_risk_percent
            reward_amount = risk_amount * target_risk_reward_ratio
            
            # For BUY actions (all our options signals):
            # - stop_loss = Lower premium (cut losses)
            # - target = Higher premium (take profits)
            options_stop_loss = options_entry_price - risk_amount
            options_target = options_entry_price + reward_amount
            
            # Ensure stop_loss doesn't go too low (minimum 5% of entry price)
            min_stop_loss = options_entry_price * 0.05  # Max 95% loss
            options_stop_loss = max(options_stop_loss, min_stop_loss)
            
            # Recalculate actual risk/reward after bounds
            actual_risk = options_entry_price - options_stop_loss
            actual_reward = options_target - options_entry_price
            actual_ratio = actual_reward / actual_risk if actual_risk > 0 else 2.1
            actual_risk_percent = (actual_risk / options_entry_price) * 100
            actual_reward_percent = (actual_reward / options_entry_price) * 100
            
            logger.info(f"📊 OPTIONS LEVELS (ATR-DYNAMIC):")
            logger.info(f"   Entry: ₹{options_entry_price:.2f}")
            logger.info(f"   Stop Loss: ₹{options_stop_loss:.2f} (Risk: ₹{actual_risk:.2f} = {actual_risk_percent:.1f}%)")
            logger.info(f"   Target: ₹{options_target:.2f} (Reward: ₹{actual_reward:.2f} = {actual_reward_percent:.1f}%)")
            logger.info(f"   R:R Ratio = 1:{actual_ratio:.2f} (Target: 1:{target_risk_reward_ratio})")
            
            return options_stop_loss, options_target
            
        except Exception as e:
            logger.error(f"Error calculating options levels: {e}")
            # 🚨 OPTIONS FIX: Tight fallback for fast exits
            base_risk_percent = 0.05  # 5% fallback risk (was 8%)
            risk_amount = options_entry_price * base_risk_percent  
            target_ratio = 2.0  # Realistic 2:1 ratio (was 2.5)
            reward_amount = risk_amount * target_ratio
            stop_loss = options_entry_price - risk_amount
            target = options_entry_price + reward_amount
            # Ensure minimum stop loss - max 15% loss (was 90%)
            stop_loss = max(stop_loss, options_entry_price * 0.85)
            return stop_loss, target
    
    def _calculate_dynamic_options_multiplier(self, option_type: str, options_entry_price: float) -> float:
        """Calculate dynamic options multiplier based on market conditions"""
        try:
            # Base multiplier starts at 2.0
            base_multiplier = 2.0
            
            # Adjust based on option premium level (higher premium = lower multiplier)
            if options_entry_price > 200:
                premium_adjustment = 0.8  # Deep ITM options move less
            elif options_entry_price > 100:
                premium_adjustment = 1.0  # ATM options
            else:
                premium_adjustment = 1.2  # OTM options move more
            
            # Adjust based on option type and market conditions
            type_adjustment = 1.0  # Base adjustment
            
            # Final multiplier
            multiplier = base_multiplier * premium_adjustment * type_adjustment
            return max(1.5, min(multiplier, 5.0))  # Bounds between 1.5x and 5x
            
        except Exception as e:
            logger.error(f"Error calculating dynamic multiplier: {e}")
            return 2.5  # Fallback
    
    def _calculate_dynamic_volatility_factor(self, underlying_price: float) -> float:
        """Calculate dynamic volatility factor based on market conditions"""
        try:
            # This would ideally use historical price data to calculate actual volatility
            # For now, use a market-condition based approach
            
            # Base volatility factor
            base_volatility = 0.02  # 2% base
            
            # Adjust based on market hours and conditions
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11 or 14 <= current_hour <= 15:  # High volatility hours
                time_adjustment = 1.3
            else:
                time_adjustment = 1.0
            
            # Adjust based on underlying price level (higher price = potentially lower volatility)
            if underlying_price > 10000:
                price_adjustment = 0.8
            elif underlying_price > 1000:
                price_adjustment = 1.0
            else:
                price_adjustment = 1.2
            
            volatility_factor = base_volatility * time_adjustment * price_adjustment
            return max(0.01, min(volatility_factor, 0.1))  # Between 1% and 10%
            
        except Exception as e:
            logger.error(f"Error calculating volatility factor: {e}")
            return 0.03  # 3% fallback
    
    def _extract_strike_from_symbol(self, options_symbol: str) -> float:
        """Extract strike price from options symbol - FIXED REGEX"""
        try:
            import re
            
            # 🎯 CORRECT FORMAT: SYMBOL + YYMMM + STRIKE + TYPE
            # Examples: ASIANPAINT25AUG2450CE, TCS25AUG3000PE
            
            # Pattern: Any letters + YYMMM + NUMBERS + CE/PE
            match = re.search(r'([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)$', options_symbol)
            
            if match:
                symbol_part = match.group(1)    # e.g., "ASIANPAINT" 
                date_part = match.group(2)      # e.g., "25AUG"
                strike_part = match.group(3)    # e.g., "2450"
                option_type = match.group(4)    # e.g., "CE"
                
                logger.info(f"🔍 STRIKE EXTRACTION: {options_symbol}")
                logger.info(f"   Symbol: {symbol_part}, Date: {date_part}, Strike: {strike_part}, Type: {option_type}")
                
                return float(strike_part)
            
            # If regex fails, use fallback
            logger.error(f"❌ Could not extract strike from {options_symbol}")
            return 2500.0  # Safe fallback
            
        except Exception as e:
            logger.error(f"Error extracting strike from {options_symbol}: {e}")
            return 2500.0  # Fallback
    
    def _get_dynamic_min_risk_reward_ratio(self, symbol: str, price: float) -> float:
        """Calculate minimum risk-reward ratio based on market volatility and symbol characteristics"""
        try:
            # Get market volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base minimum ratio (conservative)
            base_ratio = 1.2
            
            # Adjust based on volatility:
            # High volatility = lower minimum ratio (easier to achieve)  
            # Low volatility = higher minimum ratio (need better setups)
            if volatility_multiplier > 2.0:
                return base_ratio * 0.8  # 0.96 for high volatility
            elif volatility_multiplier > 1.5:
                return base_ratio * 0.9  # 1.08 for medium volatility  
            else:
                return base_ratio * 1.0  # 1.20 for low volatility (FIXED: was 1.1 = 1.32)
                
        except Exception as e:
            logger.error(f"Error calculating dynamic min R:R ratio: {e}")
            return 1.2  # Conservative fallback
    
    def _get_dynamic_target_risk_reward_ratio(self, symbol: str, price: float, option_type: str = 'CE') -> float:
        """Calculate target risk-reward ratio based on market conditions and symbol characteristics"""
        try:
            # Get market volatility and momentum indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base target ratio
            base_ratio = 2.0
            
            # Adjust based on volatility:
            # High volatility = higher target ratio (bigger moves possible)
            # Low volatility = lower target ratio (smaller moves expected)
            if volatility_multiplier > 2.5:
                target_ratio = base_ratio * 1.3  # 2.6 for very high volatility
            elif volatility_multiplier > 2.0:
                target_ratio = base_ratio * 1.2  # 2.4 for high volatility
            elif volatility_multiplier > 1.5:
                target_ratio = base_ratio * 1.1  # 2.2 for medium volatility
            else:
                target_ratio = base_ratio * 0.9  # 1.8 for low volatility
            
            # Options-specific adjustments
            if option_type in ['CE', 'PE']:
                # 🚨 MATHEMATICAL FIX: Higher minimum R:R for options to justify risk
                # Need at least 2:1 to overcome theta decay and slippage
                target_ratio *= 1.2  # Increased from 1.1
            
            # 🚨 STRICTER BOUNDS: Minimum 2:1 R:R for options (was 1.5:1)
            return max(2.0, min(target_ratio, 3.5))
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target R:R ratio: {e}")
            return 2.2  # Conservative fallback
    
    def _get_dynamic_risk_percentage(self, symbol: str, price: float) -> float:
        """
        🚨 DAVID VS GOLIATH: Ultra-tight risk for options survival
        4 days of losses = need MUCH tighter stops
        """
        try:
            # Get volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # 🚨 DRASTIC REDUCTION: 8% → 5% base risk
            # Options decay FAST, we need to exit losers IMMEDIATELY
            base_risk = 0.05  # 5% base risk (was 8%, was 12% before that)
            
            # Adjust based on volatility (even tighter):
            # High volatility = VERY tight stops (options will whipsaw)
            # Low volatility = still tight but slightly more room
            if volatility_multiplier > 2.0:
                risk_percent = base_risk * 0.75  # 3.75% for high vol (was 6.8%)
            elif volatility_multiplier > 1.5:
                risk_percent = base_risk * 0.90  # 4.5% for medium vol (was 8.0%)
            else:
                risk_percent = base_risk * 1.0  # 5.0% for low vol (was 8.8%)
            
            # 🚨 ULTRA-TIGHT BOUNDS: 3-7% max (was 6-12%)
            # Example: ₹60 premium option
            #   3% = ₹1.80 stop (exit FAST if wrong)
            #   7% = ₹4.20 stop (maximum allowed loss)
            return max(0.03, min(risk_percent, 0.07))  # Between 3% and 7%
            
        except Exception as e:
            logger.error(f"Error calculating dynamic risk percentage: {e}")
            return 0.05  # 🚨 ULTRA-TIGHT: 5% fallback (was 8%)
    
    def _get_volatility_multiplier(self, symbol: str, price: float) -> float:
        """Get volatility multiplier for the symbol based on recent price action"""
        try:
            # Try to get actual volatility data from TrueData
            from data.truedata_client import live_market_data
            
            if symbol in live_market_data:
                market_data = live_market_data[symbol]
                
                # Calculate intraday volatility
                high = market_data.get('high', price)
                low = market_data.get('low', price)
                open_price = market_data.get('open', price)
                
                if high > 0 and low > 0 and open_price > 0:
                    # Calculate percentage range
                    day_range = ((high - low) / open_price) * 100
                    
                    # Convert to volatility multiplier
                    if day_range > 4.0:
                        return 2.5  # Very high volatility
                    elif day_range > 3.0:
                        return 2.0  # High volatility
                    elif day_range > 2.0:
                        return 1.5  # Medium volatility
                    else:
                        return 1.0  # Low volatility
            
            # Fallback: Use symbol characteristics
            # Major indices tend to be less volatile than individual stocks
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                return 1.8  # Index volatility
            else:
                return 1.5  # Stock volatility
                
        except Exception as e:
            logger.error(f"Error calculating volatility multiplier for {symbol}: {e}")
            return 1.5  # Moderate fallback
    
    def _calculate_days_to_expiry(self, options_symbol: str) -> int:
        """Calculate days to expiry from options symbol"""
        try:
            # Extract date from symbol and calculate days remaining
            import re
            from datetime import datetime, timedelta
            
            # Look for date pattern in symbol (e.g., 31JUL25)
            date_match = re.search(r'(\d{1,2})([A-Z]{3})(\d{2})', options_symbol)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)
                year = int(date_match.group(3)) + 2000
                
                month_map = {
                    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                }
                month = month_map.get(month_str, 1)
                
                expiry_date = datetime(year, month, day)
                days_remaining = (expiry_date - datetime.now()).days
                return max(1, days_remaining)  # At least 1 day
            
            # Fallback: assume 7 days
            return 7
            
        except Exception as e:
            logger.error(f"Error calculating expiry for {options_symbol}: {e}")
            return 7  # 1 week fallback
    
    def _get_dynamic_lot_size(self, options_symbol: str, underlying_symbol: str) -> int:
        """🎯 ROBUST LOT SIZE: Zerodha API with hardcoded fallbacks for major F&O stocks"""
        try:
            # Try to get actual lot size from Zerodha instruments API
            actual_lot_size = self._fetch_zerodha_lot_size(underlying_symbol)
            if actual_lot_size:
                logger.info(f"✅ DYNAMIC LOT SIZE: {underlying_symbol} = {actual_lot_size} (from Zerodha API)")
                return actual_lot_size
            
            # 🚨 HARDCODED FALLBACK: Common F&O symbols with standard lot sizes
            common_lot_sizes = {
                'DMART': 150,
                'FEDERALBNK': 5000,
                'TATACONSUM': 550,
                'DRREDDY': 625,
                'APOLLOTYRE': 2000,  # Actually equity-only
                'TATASTEEL': 3500,
                'RELIANCE': 250,
                'HDFCBANK': 1100,
                'ICICIBANK': 700,
                'KOTAKBANK': 400,
                'SBIN': 1500,
                'AXISBANK': 1200,
                'INDUSINDBK': 900,
                'BAJFINANCE': 125,
                'MARUTI': 100,
                'INFY': 300,
                'TCS': 150,
                'WIPRO': 3000,
                'LT': 225,
                'SUNPHARMA': 400,
                'CIPLA': 350,
                'BHARTIARTL': 475,
                'TITAN': 300,
                'ASIANPAINT': 150,
                'NESTLEIND': 50,
                'HINDUNILVR': 300,
                'ITC': 3200,
                'COALINDIA': 4000,
                'ONGC': 4200,
                'NTPC': 2000,
                'POWERGRID': 1800,
                'TATAMOTORS': 1500,
                'HINDALCO': 1700,
                'VEDL': 1150,
                'JSWSTEEL': 800,
                'SAIL': 6000,
                'NMDC': 1300,
                'GAIL': 2200,
                'IOC': 3500,
                'BPCL': 600,
                'HPCL': 1050
            }
            
            fallback_lot_size = common_lot_sizes.get(underlying_symbol)
            if fallback_lot_size:
                logger.info(f"✅ FALLBACK LOT SIZE: {underlying_symbol} = {fallback_lot_size} (hardcoded)")
                return fallback_lot_size
            
            # If no fallback available, treat as equity
            logger.warning(f"⚠️ NO LOT SIZE available for {underlying_symbol} - treating as EQUITY only")
            logger.info(f"🔄 FALLBACK: {underlying_symbol} should use EQUITY trading instead of F&O")
            return None
                
        except Exception as e:
            logger.error(f"Error getting dynamic lot size for {options_symbol}: {e}")
            return None
    
    def _map_truedata_to_zerodha_symbol(self, truedata_symbol: str) -> str:
        """Map TrueData symbol format to Zerodha format"""
        # Direct mapping for common indices
        symbol_mapping = {
            'NIFTY-I': 'NIFTY',
            'BANKNIFTY-I': 'BANKNIFTY', 
            'FINNIFTY-I': 'FINNIFTY',
            'MIDCPNIFTY-I': 'MIDCPNIFTY',
            'SENSEX-I': 'SENSEX',
            'BANKEX-I': 'BANKEX'
        }
        
        # Check direct mapping first
        if truedata_symbol in symbol_mapping:
            return symbol_mapping[truedata_symbol]
        
        # For regular stocks, remove any suffixes and clean
        cleaned_symbol = truedata_symbol.replace('-I', '').replace('-EQ', '').strip()
        
        return cleaned_symbol
    
    def _fetch_zerodha_lot_size(self, underlying_symbol: str) -> int:
        """🎯 DYNAMIC: Fetch actual lot size from Zerodha instruments API"""
        try:
            # 🔥 CRITICAL FIX: Hardcoded index lot sizes (these are well-known and rarely change)
            # Zerodha API sometimes returns stale data, so override for indices
            # 🔧 UPDATED Dec 2024
            INDEX_LOT_SIZES = {
                'NIFTY': 65,      # Corrected Dec 2024 - user confirmed
                'BANKNIFTY': 35,  # Corrected Dec 2024 - user confirmed
                'FINNIFTY': 40,   # Changed from 25 to 40 (Nov 2024)
                'MIDCPNIFTY': 50, # Standard lot size
                'SENSEX': 10,     # Lot size = 10
                'BANKEX': 15,     # Lot size = 15
            }
            
            # Log symbol mapping for debugging
            clean_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            
            # Check if it's an index with hardcoded lot size
            if clean_underlying in INDEX_LOT_SIZES:
                lot_size = INDEX_LOT_SIZES[clean_underlying]
                logger.info(f"✅ INDEX LOT SIZE (hardcoded): {clean_underlying} = {lot_size}")
                return lot_size
            if clean_underlying != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {clean_underlying}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.debug(f"⚠️ Zerodha client not available for lot size lookup: {underlying_symbol}")
                return None
            
            # Try to get instruments data
            if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                try:
                    # Get NFO instruments (F&O contracts)
                    instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                    logger.debug(f"🔍 Searching for lot size: {underlying_symbol} → {clean_underlying}")
                    
                    # Look for the underlying symbol in F&O instruments
                    for instrument in instruments:
                        trading_symbol = instrument.get('tradingsymbol', '')
                        segment = instrument.get('segment', '')
                        name = instrument.get('name', '')
                        
                        # 🚨 ENHANCED MATCHING: Multiple matching strategies
                        symbol_matches = (
                            trading_symbol.startswith(clean_underlying) or  # RELIANCE25SEP...
                            (name and clean_underlying in name.upper()) or  # Company name in 'name' field
                            (clean_underlying in trading_symbol and len(clean_underlying) > 3)  # Partial match for longer symbols
                        )
                        
                        if (symbol_matches and 
                            segment == 'NFO-OPT' and  # Options only
                            ('CE' in trading_symbol or 'PE' in trading_symbol)):
                            
                            lot_size = instrument.get('lot_size', 0)
                            if lot_size > 0:
                                logger.info(f"✅ ZERODHA LOT SIZE: {underlying_symbol} = {lot_size}")
                                logger.debug(f"   Matched instrument: {trading_symbol} (segment: {segment})")
                                return lot_size
                    
                    logger.debug(f"🔍 No F&O lot size found for {underlying_symbol} in Zerodha instruments")
                    return None
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error fetching Zerodha instruments for {underlying_symbol}: {e}")
                    return None
            else:
                logger.debug(f"⚠️ Zerodha KiteConnect not initialized for lot size lookup")
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching Zerodha lot size for {underlying_symbol}: {e}")
            return None
    
    
    # REMOVED: Duplicate function - using the complete implementation below
            # For options: margin is typically much less than premium cost
            premium_per_lot = lot_size * entry_price
            
            # Try to get actual margin requirement from Zerodha
            try:
                if hasattr(self, 'zerodha_client') and self.zerodha_client:
                    # Use Zerodha's margin calculation if available
                    estimated_margin_per_lot = self.zerodha_client.get_required_margin_for_order(
                        symbol=options_symbol, quantity=lot_size, price=entry_price, 
                        transaction_type='BUY', product='MIS'
                    )
                    if estimated_margin_per_lot and estimated_margin_per_lot > 0:
                        logger.info(f"📊 ZERODHA MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
                    else:
                        # Fallback: estimate margin as percentage of premium
                        estimated_margin_per_lot = premium_per_lot * 0.3  # ~30% margin for options
                        logger.info(f"📊 ESTIMATED MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
                else:
                    # Fallback: estimate margin as percentage of premium  
                    estimated_margin_per_lot = premium_per_lot * 0.3  # ~30% margin for options
                    logger.info(f"📊 ESTIMATED MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
            except Exception as e:
                # Conservative fallback
                estimated_margin_per_lot = premium_per_lot * 0.3
                logger.debug(f"Margin calculation fallback for {options_symbol}: {e}")
            
            # Apply 25% margin allocation limit
            max_margin_allowed = available_capital * max_margin_per_trade_pct
            max_affordable_lots = int(max_margin_allowed / estimated_margin_per_lot) if estimated_margin_per_lot > 0 else 0
            
            if max_affordable_lots < 1:
                logger.warning(
                    f"❌ OPTIONS REJECTED: {options_symbol} 1 lot needs ₹{estimated_margin_per_lot:,.0f} margin, "
                    f"exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                )
                return 0
            
            final_lots = max_affordable_lots
            total_margin = final_lots * estimated_margin_per_lot
            
            logger.info(f"✅ OPTIONS MARGIN OK: {final_lots} lots, Est. Margin ₹{total_margin:,.0f}")
            return final_lots * lot_size
        
        else:  # Equity
            if entry_price <= 0:
                return 0
            min_trade_value = 25000.0  # Minimum ₹25,000 trade value for stocks
            
            # Check if we can afford minimum trade value
            if available_capital < min_trade_value:
                return 0
                
            # 🎯 CRITICAL: Calculate shares needed for MINIMUM ₹25,000 trade value
            min_shares_required = int(min_trade_value / entry_price)
            cost_for_min_shares = min_shares_required * entry_price
            
            # 🚨 MARGIN-BASED POSITION SIZING: Use ACTUAL Zerodha margin (not hardcoded 25%)
            # Different stocks have different margin requirements (25%-75%)
            # Default to 60% (conservative) if API unavailable
            estimated_margin_factor = 0.60  # Conservative default
            
            # 🔥 CRITICAL FIX: Try to get actual margin from Zerodha API
            zerodha_client = None
            try:
                orchestrator = getattr(self, 'orchestrator', None)
                if not orchestrator:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'zerodha_client'):
                    zerodha_client = orchestrator.zerodha_client
            except Exception:
                pass
            
            # Calculate max margin we can allocate to this trade
            max_margin_allowed = available_capital * max_margin_per_trade_pct
            
            # Try to get actual margin per share from Zerodha
            actual_margin_per_share = entry_price * estimated_margin_factor  # Default
            if zerodha_client and hasattr(zerodha_client, 'get_required_margin_for_order'):
                try:
                    # Get margin for 1 share to calculate per-share margin
                    test_margin = zerodha_client.get_required_margin_for_order(
                        symbol=underlying_symbol, quantity=100, order_type='BUY', product='MIS'
                    )
                    if test_margin > 0:
                        actual_margin_per_share = test_margin / 100
                        estimated_margin_factor = actual_margin_per_share / entry_price
                        logger.debug(f"💰 ZERODHA MARGIN: {underlying_symbol} = ₹{actual_margin_per_share:.2f}/share ({estimated_margin_factor:.1%})")
                except Exception as margin_err:
                    logger.debug(f"Could not get Zerodha margin for {underlying_symbol}: {margin_err}")
            
            # Calculate maximum affordable shares based on actual margin
            max_affordable_shares = int(max_margin_allowed / actual_margin_per_share) if actual_margin_per_share > 0 else 0
            max_affordable_cost = max_affordable_shares * entry_price
            
            # Use the higher of: minimum trade value OR maximum affordable within margin limits
            if max_affordable_cost >= min_trade_value:
                # We can afford more than minimum - use maximum affordable
                final_quantity = max_affordable_shares
                cost = max_affordable_cost
                estimated_margin = final_quantity * actual_margin_per_share
                
                logger.debug(f"✅ MARGIN-OPTIMIZED: {underlying_symbol} = {final_quantity} shares")
                logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                logger.debug(f"   💳 Est. Margin: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital:.1%} of capital)")
                logger.debug(f"   📊 Leverage: ~{cost/estimated_margin:.1f}x")
                return final_quantity
            else:
                # Can only afford minimum - check if it fits in margin allocation
                min_estimated_margin = min_shares_required * actual_margin_per_share
                
                if min_estimated_margin <= max_margin_allowed:
                    logger.debug(f"✅ MINIMUM VIABLE: {underlying_symbol} = {min_shares_required} shares")
                    logger.debug(f"   💰 Trade Value: ₹{cost_for_min_shares:,.0f}")
                    logger.debug(f"   💳 Est. Margin: ₹{min_estimated_margin:,.0f}")
                    return min_shares_required
                else:
                    logger.warning(
                        f"❌ EQUITY REJECTED: {underlying_symbol} min trade ₹{min_trade_value:,.0f} "
                        f"needs ₹{min_estimated_margin:,.0f} margin, exceeds limit ₹{max_margin_allowed:,.0f}"
                    )
                    return 0
    
    def _get_available_capital(self) -> float:
        """🎯 DYNAMIC: Get available capital from Zerodha margins API in real-time"""
        try:
            # First check if we have orchestrator set on this instance
            orchestrator = getattr(self, 'orchestrator', None)
            
            # If not, try to get from global instance
            if not orchestrator:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                
            # 🔥 CRITICAL FIX: ALWAYS prefer orchestrator's zerodha_client (it gets updated on token refresh)
            # Old bug: Strategy cached zerodha_client at init, then token refresh created NEW instance
            # Strategy still used OLD instance where kite=None
            zerodha_client = None
            
            # Priority 1: Get FRESH client from orchestrator (handles token refresh properly)
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                zerodha_client = orchestrator.zerodha_client
                # Verify kite is initialized
                if hasattr(zerodha_client, 'kite') and zerodha_client.kite:
                    logger.debug("✅ Using orchestrator's Zerodha client (kite initialized)")
                else:
                    logger.warning("⚠️ Orchestrator's Zerodha client has kite=None")
            
            # Priority 2: Fallback to self.zerodha_client only if orchestrator doesn't have one
            if not zerodha_client:
                zerodha_client = getattr(self, 'zerodha_client', None)
                if zerodha_client:
                    logger.debug("⚠️ Using strategy's cached Zerodha client (orchestrator unavailable)")
            
            if zerodha_client:
                try:
                    # Try to get margins (available cash) from Zerodha
                    if hasattr(zerodha_client, 'get_margins'):
                        # Use async method if available
                        import asyncio
                        loop = asyncio.get_event_loop()
                        
                        if loop.is_running():
                            # 🚨 CRITICAL FIX: Use synchronous method in async context
                            if hasattr(zerodha_client, 'get_margins_sync'):
                                real_available = zerodha_client.get_margins_sync()
                                if real_available > 0:
                                    logger.info(f"✅ REAL-TIME CAPITAL: ₹{real_available:,.2f} (sync from Zerodha)")
                                    # Cache the value
                                    self._last_known_capital = real_available
                                    return float(real_available)
                        else:
                            # Run async method to get live margins
                            margins = loop.run_until_complete(zerodha_client.get_margins())
                            if margins and isinstance(margins, (int, float)) and margins > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{margins:,.2f} (live from Zerodha)")
                                self._last_known_capital = margins
                                return float(margins)
                    
                    # Fallback: Try sync method if available
                    if hasattr(zerodha_client, 'kite') and zerodha_client.kite:
                        try:
                            margins = zerodha_client.kite.margins()
                            equity_cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
                            if equity_cash > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{equity_cash:,.2f} (from Zerodha equity margins)")
                                self._last_known_capital = equity_cash
                                return float(equity_cash)
                        except Exception as margin_error:
                            logger.debug(f"⚠️ Error fetching Zerodha margins: {margin_error}")
                            
                except Exception as zerodha_error:
                    logger.debug(f"⚠️ Error accessing Zerodha for capital: {zerodha_error}")
            
            # Fallback to cached or config capital if API fails
            if hasattr(self, '_last_known_capital') and self._last_known_capital > 0:
                logger.info(f"✅ Using last known capital: ₹{self._last_known_capital:,.2f}")
                return self._last_known_capital
            
            # Use config capital as fallback
            try:
                # 🚨 DEFENSIVE: Use self.config if available, otherwise import
                if hasattr(self, 'config') and self.config:
                    config_capital = self.config.get('available_capital', 75000)
                    logger.info(f"✅ Using strategy config capital: ₹{config_capital:,.2f}")
                    return float(config_capital)
                else:
                    from config import config
                    config_capital = config.get('available_capital', 75000)
                    logger.info(f"✅ Using global config capital: ₹{config_capital:,.2f}")
                    return float(config_capital)
            except (ImportError, AttributeError) as config_error:
                # Hardcoded fallback if config import fails
                logger.warning(f"⚠️ Config access failed ({config_error}), using hardcoded capital: ₹75,000")
                return 75000.0
            
        except Exception as e:
            logger.error(f"Error getting dynamic available capital: {e}")
            # Return hardcoded capital on error
            return 75000.0

    def _get_base_capital_for_sizing(self) -> float:
        """
        🔥 BASE CAPITAL FOR CONSISTENT POSITION SIZING

        Problem:
        - We currently size trades off *available margin* (Zerodha equity.net).
        - After each order, net margin reduces, so later trades are sized smaller.
        - This causes inconsistent sizing and frequent rejections against MIN_ORDER_VALUE.

        Fix:
        - Use a fixed "base capital" once per IST trading day for sizing math.
        - Still cap by *real-time* available margin for feasibility.
        """
        try:
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            today = datetime.now(ist).date()

            # Optional: allow config override (stable base, e.g. your starting capital)
            configured_base = None
            try:
                if hasattr(self, 'config') and self.config:
                    configured_base = self.config.get('base_capital') or self.config.get('available_capital')
                else:
                    from config import config as _global_config
                    configured_base = _global_config.get('base_capital') or _global_config.get('available_capital')
            except Exception:
                configured_base = None

            # Refresh base capital once per day (or if not set)
            if not self._base_capital_date or self._base_capital_date != today or self._base_capital <= 0:
                current_available = self._get_available_capital()
                candidates = [c for c in [configured_base, current_available] if isinstance(c, (int, float)) and c > 0]
                self._base_capital = float(max(candidates)) if candidates else 0.0
                self._base_capital_date = today
                if self._base_capital > 0:
                    logger.info(f"🎯 BASE CAPITAL (sizing) set to ₹{self._base_capital:,.2f} for {today}")
                else:
                    logger.warning("⚠️ BASE CAPITAL (sizing) unavailable - sizing may be inconsistent")

            return float(self._base_capital) if self._base_capital > 0 else float(self._get_available_capital())

        except Exception as e:
            logger.error(f"❌ Error computing base capital for sizing: {e}")
            # Fallback to available capital so system can still trade
            return float(self._get_available_capital())
    
    def _get_base_capital_for_sizing(self) -> float:
        """
        🔥 BASE CAPITAL FOR CONSISTENT POSITION SIZING
        
        Problem: When trades are taken, available margin decreases. This causes
        later trades to have smaller position sizes that fail MIN_ORDER_VALUE check.
        
        Solution: Use a fixed "base capital" that is set once per trading day.
        This ensures ALL trades are sized consistently based on starting capital,
        not the dynamically decreasing available margin.
        
        Returns:
            Base capital for position sizing (consistent throughout the day)
        """
        try:
            import pytz
            from datetime import date
            
            ist = pytz.timezone('Asia/Kolkata')
            today = datetime.now(ist).date()
            
            # Check if we need to refresh base capital (new day or not set)
            if self._base_capital <= 0 or self._base_capital_date != today:
                # Get current available capital from Zerodha
                current_capital = self._get_available_capital()
                
                if current_capital > 0:
                    # Set base capital for the day
                    self._base_capital = current_capital
                    self._base_capital_date = today
                    logger.info(f"🎯 BASE CAPITAL SET: ₹{self._base_capital:,.2f} for {today}")
                else:
                    # Fallback to config or hardcoded
                    self._base_capital = 100000.0
                    logger.warning(f"⚠️ BASE CAPITAL FALLBACK: ₹{self._base_capital:,.2f}")
            
            return self._base_capital
            
        except Exception as e:
            logger.error(f"❌ Error getting base capital: {e}")
            # Return cached or fallback
            if self._base_capital > 0:
                return self._base_capital
            return 100000.0

    async def _get_volume_based_strike(self, underlying_symbol: str, current_price: float, expiry: str, action: str) -> int:
        """
        🎯 ALGORITHMIC FIX: Select OTM strikes for better risk/reward
        
        WHY OTM?
        - ATM options are expensive (high premium = high risk)
        - OTM options: cheaper premium, higher % gain on direction move
        - 1-2 strikes OTM gives good delta (0.3-0.4) with lower cost
        
        LOGIC:
        - For CALLS (bullish): Select strike ABOVE current price (1-2 strikes OTM)
        - For PUTS (bearish): Select strike BELOW current price (1-2 strikes OTM)
        """
        try:
            # First get ATM strike as baseline
            atm_strike = self._get_atm_strike_for_stock(current_price)
            
            # Determine strike interval for this underlying
            strike_interval = self._get_strike_interval(underlying_symbol, current_price)
            
            # 🎯 KEY ALGO CHANGE: Select OTM strike (1-2 strikes out of the money)
            # Number of strikes OTM depends on market volatility
            otm_offset = 1  # Default 1 strike OTM
            
            # Check if high volatility day - if so, go 2 strikes OTM for cheaper entry
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'market_volatility'):
                    if orchestrator.market_volatility == 'HIGH':
                        otm_offset = 2  # 2 strikes OTM in high vol
                        logger.info(f"📈 HIGH VOLATILITY: Using 2 strikes OTM for cheaper entry")
            except:
                pass
            
            # Calculate OTM strike based on direction
            if action.upper() == 'BUY':
                # Bullish = BUY CALL = strike ABOVE current price (OTM call)
                otm_strike = atm_strike + (strike_interval * otm_offset)
                logger.info(f"🎯 OTM CALL: ATM={atm_strike} + {otm_offset} strikes = {otm_strike}")
            else:
                # Bearish = BUY PUT = strike BELOW current price (OTM put)
                otm_strike = atm_strike - (strike_interval * otm_offset)
                logger.info(f"🎯 OTM PUT: ATM={atm_strike} - {otm_offset} strikes = {otm_strike}")

            logger.info(f"🎯 STRIKE SELECTION for {underlying_symbol}")
            logger.info(f"   Current Price: ₹{current_price:.2f}, ATM: {atm_strike}, OTM Target: {otm_strike}")
            logger.info(f"   Strike Interval: {strike_interval}, OTM Offset: {otm_offset}")

            # Get orchestrator to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()

            if orchestrator and orchestrator.zerodha_client:
                try:
                    # Map symbol to Zerodha format
                    zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)

                    # Find closest available strike to our OTM target
                    try:
                        closest_strike = await orchestrator.zerodha_client.find_closest_available_strike(
                            zerodha_symbol, otm_strike, expiry  # Use OTM target, not ATM
                        )

                        # 🚨 DEFENSIVE: Validate the response from find_closest_available_strike
                        if closest_strike is None:
                            logger.warning(f"⚠️ find_closest_available_strike returned None for {zerodha_symbol}")
                            return otm_strike
                        elif isinstance(closest_strike, int):
                            if closest_strike > 0:
                                logger.info(f"✅ Using OTM strike: {closest_strike} (target was {otm_strike})")
                                return closest_strike
                            else:
                                logger.warning(f"⚠️ Invalid strike value: {closest_strike}, using OTM: {otm_strike}")
                                return otm_strike
                        else:
                            logger.error(f"❌ find_closest_available_strike returned {type(closest_strike)} instead of int: {closest_strike}")
                            return otm_strike

                    except Exception as strike_error:
                        logger.error(f"❌ ERROR calling find_closest_available_strike for {zerodha_symbol}: {strike_error}")
                        logger.error(f"   Error type: {type(strike_error)}")
                        if "can't be used in 'await' expression" in str(strike_error):
                            logger.error(f"🚨 CRITICAL: Zerodha API returned non-coroutine in strike lookup")
                        return otm_strike

                except Exception as zerodha_err:
                    logger.warning(f"⚠️ Error accessing Zerodha strikes: {zerodha_err}")
                    return otm_strike
            else:
                logger.warning("⚠️ Zerodha client not available, using calculated OTM strike")
            return otm_strike

        except Exception as e:
            logger.error(f"Error in OTM strike selection: {e}")
            # Fallback to ATM (safer than random)
            atm_strike = self._get_atm_strike_for_stock(current_price)
            logger.warning(f"⚠️ Fallback to ATM strike: {atm_strike}")
            return atm_strike
    
    def _get_strike_interval(self, symbol: str, price: float) -> int:
        """Get the strike interval for a symbol"""
        symbol_upper = symbol.upper()
        
        # Index options - fixed intervals
        if symbol_upper == 'NIFTY':
            return 50
        elif symbol_upper == 'BANKNIFTY':
            return 100
        elif symbol_upper == 'FINNIFTY':
            return 50
        elif symbol_upper == 'SENSEX':
            return 100
        else:
            # Stock options - interval based on price
            if price > 5000:
                return 100
            elif price > 1000:
                return 50
            elif price > 500:
                return 25
            elif price > 100:
                return 10
            else:
                return 5
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {}
    
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                # 🚨 CRITICAL FIX: Map TrueData symbol to Zerodha symbol (NIFTY-I → NIFTY)
                zerodha_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_underlying}")
                
                base_lot_size = self._get_dynamic_lot_size(options_symbol, zerodha_underlying)
                if base_lot_size is None:
                    logger.warning(f"⚠️ NO LOT SIZE for {zerodha_underlying} - FALLING BACK to EQUITY trading")
                    # 🎯 AUTOMATIC FALLBACK: Calculate equity quantity instead of rejecting
                    is_options = False  # Switch to equity mode
                
            if is_options:
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price BEFORE margin calculation
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {options_symbol}")
                    logger.error(f"   Cannot calculate margin/quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🚨 CRITICAL FIX: Get REAL margin requirement from Zerodha API
                margin_required = 0.0
                
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        # Get actual margin requirement from Zerodha
                        if hasattr(orchestrator.zerodha_client, 'get_required_margin_for_order'):
                            # Use the actual F&O symbol for margin calculation
                            actual_symbol = options_symbol if options_symbol else underlying_symbol
                            margin_required = orchestrator.zerodha_client.get_required_margin_for_order(
                                symbol=actual_symbol,
                                quantity=base_lot_size,
                                order_type='BUY',
                                product='MIS'  # Intraday
                            )
                            logger.info(f"📊 Dynamic margin from Zerodha: ₹{margin_required:,.2f} for {actual_symbol}")
                except Exception as e:
                    logger.debug(f"Could not get dynamic margin: {e}")
                
                # Fallback if dynamic margin not available
                if margin_required <= 0:
                    if 'CE' in options_symbol or 'PE' in options_symbol:
                        # Options: Premium estimate (no caps - based on actual lot size)
                        margin_required = base_lot_size * 50  # Remove capital percentage cap
                        logger.info(f"📊 Options margin estimate: ₹{margin_required:,.2f}")
                    else:
                        # Futures: 10-15% of contract value
                        contract_value = base_lot_size * entry_price
                        margin_required = contract_value * 0.10  # 10% margin estimate
                        logger.info(f"📊 Futures margin estimate: ₹{margin_required:,.2f}")
                
                # 🎯 MARGIN-BASED ALLOCATION: 80% margin limit per trade (allow high-value positions)
                max_margin_per_trade_pct = 0.80  # 80% of available capital per trade  
                max_margin_allowed = available_capital * max_margin_per_trade_pct

                # CRITICAL: Options should ALWAYS be 1 lot (as per user requirement)
                lots_needed_for_min = 1  # Always 1 lot for options/F&O
                logger.info(f"🎯 OPTIONS LOT SIZE: Fixed to 1 lot for {zerodha_underlying}")

                total_margin = margin_required * lots_needed_for_min if margin_required > 0 else margin_required

                # Check if we can afford it within margin limits
                if total_margin <= max_margin_allowed and total_margin <= available_capital:
                    total_qty = base_lot_size * lots_needed_for_min
                    logger.info(
                        f"✅ F&O ORDER: {zerodha_underlying} = {lots_needed_for_min} lot(s) × {base_lot_size} = {total_qty} qty"
                    )
                    logger.info(
                        f"   💰 Margin: ₹{total_margin:,.0f} (per lot ₹{margin_required:,.0f}) / Available: ₹{available_capital:,.0f}"
                    )
                    return total_qty

                # If even 1 lot is too expensive, reject early
                logger.warning(
                    f"❌ F&O REJECTED: {zerodha_underlying} exceeds capital limits "
                    f"(needed ₹{total_margin:,.0f}, available ₹{available_capital:,.0f})"
                )
                return 0
            else:
                # 🎯 EQUITY: Use share-based calculation with minimum trade value
                # CRITICAL FIX: Reduce minimum trade value to work with available capital
                min_trade_value = 20000.0  # Reduced from ₹25,000 to ₹20,000 for capital efficiency
                
                # Check if we can afford minimum trade value
                if available_capital < min_trade_value:
                    logger.warning(
                        f"❌ EQUITY REJECTED: {underlying_symbol} insufficient capital for min trade value "
                        f"(need ₹{min_trade_value:,.0f}, available ₹{available_capital:,.0f})"
                    )
                    return 0
                
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {underlying_symbol}")
                    logger.error(f"   Cannot calculate quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🎯 CRITICAL: Calculate shares needed for MINIMUM ₹25,000 trade value
                min_shares_required = int(min_trade_value / entry_price)
                cost_for_min_shares = min_shares_required * entry_price
                
                # 🚨 MARGIN-BASED POSITION SIZING: Use 25% of available margin
                estimated_margin_factor = 0.25  # Conservative estimate for MIS margin requirement
                max_margin_per_trade_pct = 0.25  # 25% of available margin per trade
                max_margin_allowed = available_capital * max_margin_per_trade_pct
                
                # Calculate maximum trade value we can afford with 25% margin allocation
                max_affordable_trade_value = max_margin_allowed / estimated_margin_factor
                max_affordable_shares = int(max_affordable_trade_value / entry_price)
                max_affordable_cost = max_affordable_shares * entry_price
                
                # Use the higher of: minimum trade value OR maximum affordable within margin limits
                if max_affordable_cost >= min_trade_value:
                    # We can afford more than minimum - use maximum affordable
                    final_quantity = max_affordable_shares
                    cost = max_affordable_cost
                    estimated_margin = cost * estimated_margin_factor
                    
                    logger.debug(f"✅ MARGIN-OPTIMIZED: {underlying_symbol} = {final_quantity} shares")
                    logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                    logger.debug(f"   💳 Est. Margin: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital:.1%} of capital)")
                    logger.debug(f"   📊 Leverage: ~{cost/estimated_margin:.1f}x")
                else:
                    # Can only afford minimum - check if it fits in margin allocation
                    min_estimated_margin = cost_for_min_shares * estimated_margin_factor
                    
                    if min_estimated_margin <= max_margin_allowed:
                        final_quantity = min_shares_required
                        cost = cost_for_min_shares
                        logger.debug(f"✅ MINIMUM VIABLE: {underlying_symbol} = {final_quantity} shares")
                        logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                        logger.debug(f"   💳 Est. Margin: ₹{cost * estimated_margin_factor:,.0f}")
                    else:
                        logger.warning(
                            f"❌ EQUITY REJECTED: {underlying_symbol} min trade ₹{min_trade_value:,.0f} "
                            f"needs ₹{min_estimated_margin:,.0f} margin, exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                        )
                        return 0

                logger.debug(f"✅ EQUITY ORDER: {underlying_symbol} = {final_quantity} shares")
                logger.debug(f"   💰 Cost: ₹{cost:,.0f} / Available: ₹{available_capital:,.0f} ({cost/available_capital:.1%})")
                
                # CRITICAL DEBUG: Log final quantity calculation
                if final_quantity == 0:
                    logger.error(f"🚨 CRITICAL: Quantity calculation returned 0 for {underlying_symbol}")
                    logger.error(f"   This should NOT happen for equity signals with valid entry price ₹{entry_price}")
                
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {}
    
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                # 🚨 CRITICAL FIX: Map TrueData symbol to Zerodha symbol (NIFTY-I → NIFTY)
                zerodha_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_underlying}")
                
                base_lot_size = self._get_dynamic_lot_size(options_symbol, zerodha_underlying)
                if base_lot_size is None:
                    logger.warning(f"⚠️ NO LOT SIZE for {zerodha_underlying} - FALLING BACK to EQUITY trading")
                    # 🎯 AUTOMATIC FALLBACK: Calculate equity quantity instead of rejecting
                    is_options = False  # Switch to equity mode
                
            if is_options:
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price BEFORE margin calculation
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {options_symbol}")
                    logger.error(f"   Cannot calculate margin/quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🚨 CRITICAL FIX: Get REAL margin requirement from Zerodha API
                margin_required = 0.0
                
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        # Get actual margin requirement from Zerodha
                        if hasattr(orchestrator.zerodha_client, 'get_required_margin_for_order'):
                            # Use the actual F&O symbol for margin calculation
                            actual_symbol = options_symbol if options_symbol else underlying_symbol
                            margin_required = orchestrator.zerodha_client.get_required_margin_for_order(
                                symbol=actual_symbol,
                                quantity=base_lot_size,
                                order_type='BUY',
                                product='MIS'  # Intraday
                            )
                            logger.info(f"📊 Dynamic margin from Zerodha: ₹{margin_required:,.2f} for {actual_symbol}")
                except Exception as e:
                    logger.debug(f"Could not get dynamic margin: {e}")
                
                # Fallback if dynamic margin not available
                if margin_required <= 0:
                    if 'CE' in options_symbol or 'PE' in options_symbol:
                        # Options: Premium estimate (no caps - based on actual lot size)
                        margin_required = base_lot_size * 50  # Remove capital percentage cap
                        logger.info(f"📊 Options margin estimate: ₹{margin_required:,.2f}")
                    else:
                        # Futures: 10-15% of contract value
                        contract_value = base_lot_size * entry_price
                        margin_required = contract_value * 0.10  # 10% margin estimate
                        logger.info(f"📊 Futures margin estimate: ₹{margin_required:,.2f}")
                
                # 🎯 MARGIN-BASED ALLOCATION: 80% margin limit per trade (allow high-value positions)
                max_margin_per_trade_pct = 0.80  # 80% of available capital per trade  
                max_margin_allowed = available_capital * max_margin_per_trade_pct

                # CRITICAL: Options should ALWAYS be 1 lot (as per user requirement)
                lots_needed_for_min = 1  # Always 1 lot for options/F&O
                logger.info(f"🎯 OPTIONS LOT SIZE: Fixed to 1 lot for {zerodha_underlying}")

                total_margin = margin_required * lots_needed_for_min if margin_required > 0 else margin_required

                # Check if we can afford it within margin limits
                if total_margin <= max_margin_allowed and total_margin <= available_capital:
                    total_qty = base_lot_size * lots_needed_for_min
                    logger.info(
                        f"✅ F&O ORDER: {zerodha_underlying} = {lots_needed_for_min} lot(s) × {base_lot_size} = {total_qty} qty"
                    )
                    logger.info(
                        f"   💰 Margin: ₹{total_margin:,.0f} (per lot ₹{margin_required:,.0f}) / Available: ₹{available_capital:,.0f}"
                    )
                    return total_qty

                # If even 1 lot is too expensive, reject early
                logger.warning(
                    f"❌ F&O REJECTED: {zerodha_underlying} exceeds capital limits "
                    f"(needed ₹{total_margin:,.0f}, available ₹{available_capital:,.0f})"
                )
                return 0
            else:
                # 🔥 INTRADAY EQUITY POSITION SIZING (2025-12-03)
                # ================================================
                # Key Rules:
                # 1. Intraday leverage = 4x (MIS product)
                # 2. Max loss per trade = 2% of portfolio
                # 3. Position Size = Max Loss / (Entry - StopLoss)
                # 
                # Example: ₹50k capital
                # - Tradeable value = ₹50k × 4 = ₹2L
                # - Max loss = 2% of ₹50k = ₹1,000
                # - SBIN @ ₹950, SL @ ₹931 (2% SL)
                # - Risk per share = ₹950 - ₹931 = ₹19
                # - Max shares = ₹1,000 / ₹19 = 52 shares
                # - Position value = 52 × ₹950 = ₹49,400 (using ~1x of 4x available)
                
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {underlying_symbol}")
                    return 0
                
                # 🎯 INTRADAY LEVERAGE: 4x margin for MIS product
                INTRADAY_LEVERAGE = 4.0
                max_tradeable_value = available_capital * INTRADAY_LEVERAGE
                
                # 🎯 MAX LOSS PER TRADE: 2% of portfolio
                MAX_LOSS_PCT = 0.02
                max_loss_amount = available_capital * MAX_LOSS_PCT
                
                # 🎯 CALCULATE STOP LOSS DISTANCE (assume 2% if not provided in context)
                # This will be validated later with actual signal stop_loss
                assumed_stop_loss_pct = 0.02  # 2% stop loss
                risk_per_share = entry_price * assumed_stop_loss_pct
                
                # 🎯 POSITION SIZE = Max Loss / Risk Per Share
                max_shares_by_risk = int(max_loss_amount / risk_per_share) if risk_per_share > 0 else 0
                
                # 🎯 Also check we don't exceed tradeable value
                max_shares_by_capital = int(max_tradeable_value / entry_price) if entry_price > 0 else 0
                
                # Use the smaller of the two (risk-based or capital-based limit)
                final_quantity = min(max_shares_by_risk, max_shares_by_capital)
                
                # Ensure minimum viable quantity (at least 1 share)
                if final_quantity < 1:
                    logger.warning(f"❌ EQUITY REJECTED: {underlying_symbol} - calculated quantity too small")
                    return 0
                
                cost = final_quantity * entry_price
                estimated_margin = cost / INTRADAY_LEVERAGE  # MIS margin = Position / 4
                
                logger.info(f"✅ INTRADAY EQUITY: {underlying_symbol} = {final_quantity} shares")
                logger.info(f"   💰 Position Value: ₹{cost:,.0f} (using {cost/max_tradeable_value*100:.0f}% of 4x leverage)")
                logger.info(f"   💳 Margin Required: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital*100:.1f}% of capital)")
                logger.info(f"   🎯 Max Loss @ 2% SL: ₹{final_quantity * risk_per_share:,.0f} ({MAX_LOSS_PCT*100:.0f}% of capital)")
                
                # CRITICAL DEBUG: Log final quantity calculation
                if final_quantity == 0:
                    logger.error(f"🚨 CRITICAL: Quantity calculation returned 0 for {underlying_symbol}")
                    logger.error(f"   This should NOT happen for equity signals with valid entry price ₹{entry_price}")
                
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {} 
    
    # ==================================================================================
    # OPTION CHAIN UTILITIES - Access and analyze comprehensive option chain data
    # ==================================================================================
    
    def get_option_chain(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get option chain data for a given underlying from market data
        
        Returns:
            Dict with structure:
            {
                'underlying': str,
                'expiry': str,
                'atm_strike': float,
                'spot_price': float,
                'chain': {'calls': {...}, 'puts': {...}},
                'analytics': {'pcr': float, 'max_pain': float, 'iv_mean': float, ...}
            }
        """
        try:
            if '_option_chains' not in market_data:
                return None
            
            option_chains = market_data['_option_chains']
            return option_chains.get(underlying_symbol)
            
        except Exception as e:
            logger.debug(f"Error getting option chain for {underlying_symbol}: {e}")
            return None
    
    def get_pcr_ratio(self, underlying_symbol: str, market_data: Dict[str, Any]) -> float:
        """
        Get Put-Call Ratio (OI based) for underlying
        PCR > 1.0 indicates more puts than calls (bearish sentiment)
        PCR < 1.0 indicates more calls than puts (bullish sentiment)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('pcr', 0)
            return 0
        except:
            return 0
    
    def get_max_pain_strike(self, underlying_symbol: str, market_data: Dict[str, Any]) -> float:
        """
        Get max pain strike - where option writers lose least
        Price tends to gravitate towards max pain near expiry
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('max_pain', 0)
            return 0
        except:
            return 0
    
    def get_option_support_resistance(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Get support and resistance levels based on max OI
        
        Returns:
            (support_strike, resistance_strike)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                analytics = chain['analytics']
                support = analytics.get('support', 0)
                resistance = analytics.get('resistance', 0)
                return (support, resistance)
            return (0, 0)
        except:
            return (0, 0)
    
    def get_iv_skew(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get IV skew data
        Positive skew means OTM puts have higher IV than OTM calls (fear/protection buying)
        Negative skew means OTM calls have higher IV (unusual, indicates bullish speculation)
        
        Returns:
            {'otm_call_iv': float, 'otm_put_iv': float, 'skew': float}
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('iv_skew', {})
            return {}
        except:
            return {}
    
    def is_high_iv_environment(self, underlying_symbol: str, market_data: Dict[str, Any], threshold: float = 25.0) -> bool:
        """
        Check if we're in a high IV environment
        High IV is good for option selling, low IV for option buying
        
        Args:
            threshold: IV percentage threshold (default 25%)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                iv_mean = chain['analytics'].get('iv_mean', 0)
                return iv_mean > threshold
            return False
        except:
            return False
    
    def get_option_greeks(self, options_symbol: str, underlying_symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get Greeks (delta, gamma, theta, vega) for a specific option
        
        Returns:
            {'delta': float, 'gamma': float, 'theta': float, 'vega': float}
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if not chain or 'chain' not in chain:
                return {}
            
            # Parse option symbol to get strike and type
            import re
            match = re.match(r"([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)", options_symbol)
            if not match:
                return {}
            
            _, _, strike_str, option_type = match.groups()
            strike = float(strike_str)
            
            # Get the option data
            option_data = None
            if option_type == 'CE':
                option_data = chain['chain']['calls'].get(strike)
            else:
                option_data = chain['chain']['puts'].get(strike)
            
            if option_data and 'greeks' in option_data:
                return option_data['greeks']
            
            return {}
            
        except Exception as e:
            logger.debug(f"Error getting Greeks for {options_symbol}: {e}")
            return {}
    
    def should_avoid_option_trade_based_on_chain(self, underlying_symbol: str, action: str, 
                                                  market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Use option chain analytics to filter out bad trade setups
        
        Args:
            underlying_symbol: Underlying symbol
            action: 'BUY' or 'SELL'
            market_data: Market data with option chain
        
        Returns:
            (should_avoid: bool, reason: str)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if not chain:
                return (False, "")
            
            analytics = chain.get('analytics', {})
            spot_price = chain.get('spot_price', 0)
            max_pain = analytics.get('max_pain', 0)
            pcr = analytics.get('pcr', 0)
            support, resistance = self.get_option_support_resistance(underlying_symbol, market_data)
            
            # Rule 1: Avoid buying calls near resistance
            if action == 'BUY' and resistance > 0:
                distance_to_resistance = (resistance - spot_price) / spot_price * 100
                if 0 < distance_to_resistance < 1.0:  # Within 1% of resistance
                    return (True, f"Near resistance at {resistance} (OI-based)")
            
            # Rule 2: Avoid buying puts near support
            if action == 'SELL' and support > 0:
                distance_to_support = (spot_price - support) / spot_price * 100
                if 0 < distance_to_support < 1.0:  # Within 1% of support
                    return (True, f"Near support at {support} (OI-based)")
            
            # Rule 3: Consider max pain - price gravitates towards it near expiry
            if max_pain > 0:
                distance_to_max_pain = abs(spot_price - max_pain) / spot_price * 100
                if distance_to_max_pain > 5.0:  # More than 5% away from max pain
                    # If we're above max pain and buying calls, be cautious
                    if action == 'BUY' and spot_price > max_pain:
                        return (True, f"Spot â‚¹{spot_price:.0f} far above max pain â‚¹{max_pain:.0f}")
                    # If we're below max pain and buying puts, be cautious
                    if action == 'SELL' and spot_price < max_pain:
                        return (True, f"Spot â‚¹{spot_price:.0f} far below max pain â‚¹{max_pain:.0f}")
            
            # Rule 4: Extreme PCR can indicate reversals
            if pcr > 2.0:  # Very high PCR - oversold, potential reversal up
                if action == 'SELL':
                    return (True, f"Extreme PCR {pcr:.2f} indicates potential reversal (avoid shorts)")
            elif pcr < 0.5:  # Very low PCR - overbought, potential reversal down
                if action == 'BUY':
                    return (True, f"Extreme PCR {pcr:.2f} indicates potential reversal (avoid longs)")
            
            return (False, "")
            
        except Exception as e:
            logger.debug(f"Error checking option chain filters: {e}")
            return (False, "")
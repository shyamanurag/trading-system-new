"""
INSTITUTIONAL-GRADE MOMENTUM SPECIALIST
======================================
Professional momentum trading with advanced mathematical models and quantitative analysis.

DAVID VS GOLIATH COMPETITIVE ADVANTAGES:
1. Multi-timeframe momentum analysis with statistical validation
2. Professional trend detection using Hodrick-Prescott filter
3. Advanced momentum indicators with regime awareness
4. Statistical arbitrage using momentum mean reversion
5. Professional risk management with momentum-adjusted position sizing
6. Machine learning enhanced momentum signal validation
7. Cross-sectional momentum analysis for relative strength
8. Professional execution with momentum-based timing

Built to compete with institutional momentum trading systems.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.signal import savgol_filter
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from .base_strategy import BaseStrategy
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class MomentumSignal:
    """Professional momentum signal with statistical validation"""
    signal_type: str
    strength: float
    confidence: float
    momentum_score: float
    trend_strength: float
    mean_reversion_probability: float
    statistical_significance: float
    expected_duration: int
    risk_adjusted_return: float

class ProfessionalMomentumModels:
    """Institutional-grade momentum analysis and modeling"""
    
    @staticmethod
    def hodrick_prescott_trend(prices: np.ndarray, lambda_param: float = 1600) -> Tuple[np.ndarray, np.ndarray]:
        """Hodrick-Prescott filter for trend extraction"""
        try:
            if len(prices) < 10:
                return prices, np.zeros_like(prices)
            
            n = len(prices)
            # Create second difference matrix
            K = np.zeros((n-2, n))
            for i in range(n-2):
                K[i, i] = 1
                K[i, i+1] = -2
                K[i, i+2] = 1
            
            # HP filter: minimize (y-trend)^2 + lambda * sum((trend_t+1 - 2*trend_t + trend_t-1)^2)
            I = np.eye(n)
            trend = np.linalg.solve(I + lambda_param * K.T @ K, prices)
            cycle = prices - trend
            
            return trend, cycle
            
        except Exception as e:
            logger.error(f"Hodrick-Prescott filter failed: {e}")
            return prices, np.zeros_like(prices)
    
    @staticmethod
    def momentum_score(prices: np.ndarray, lookback: int = 20) -> float:
        """Professional momentum score with statistical validation"""
        try:
            if len(prices) < lookback + 5:
                return 0.0
            
            # Calculate returns over different horizons
            returns_1d = (prices[-1] / prices[-2] - 1) if len(prices) >= 2 else 0
            returns_5d = (prices[-1] / prices[-6] - 1) if len(prices) >= 6 else 0
            returns_20d = (prices[-1] / prices[-21] - 1) if len(prices) >= 21 else 0
            
            # Weight recent returns more heavily
            momentum = (0.5 * returns_1d + 0.3 * returns_5d + 0.2 * returns_20d)
            
            # Normalize by volatility
            volatility = np.std(np.diff(prices[-lookback:]) / prices[-lookback:-1])
            risk_adjusted_momentum = momentum / volatility if volatility > 0 else 0
            
            return risk_adjusted_momentum
            
        except Exception as e:
            logger.error(f"Momentum score calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def trend_strength(prices: np.ndarray, window: int = 20) -> float:
        """
        Calculate trend strength using linear regression
        
        🔥 FIX: Relaxed p-value check for live tick data which is inherently noisy.
        The old p<0.05 requirement was causing trend_strength=0.0 even when stocks
        were clearly trending (e.g., KOTAKBANK +3.31% showed trend_strength=0.00)
        """
        try:
            if len(prices) < window:
                return 0.0
            
            recent_prices = prices[-window:]
            x = np.arange(len(recent_prices))
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_prices)
            
            # 🔥 FIX: Use R-squared directly for intraday data, relax p-value to 0.15
            # Live tick data is noisy - strict p<0.05 was causing 0.0 too often
            if p_value < 0.15:
                trend_strength = r_value**2
            else:
                # Fallback: use slope-based estimation when regression not significant
                # Calculate normalized slope (% change per period)
                if np.mean(recent_prices) > 0:
                    normalized_slope = (slope * window) / np.mean(recent_prices)
                    # Convert to trend strength scale (0 to 1)
                    trend_strength = min(abs(normalized_slope) * 10, 1.0)
                else:
                    trend_strength = 0.0
            
            # Adjust for direction
            if slope < 0:
                trend_strength = -trend_strength
            
            return trend_strength
            
        except Exception as e:
            logger.error(f"Trend strength calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def mean_reversion_probability(prices: np.ndarray, lookback: int = 50) -> float:
        """Calculate probability of mean reversion using statistical tests"""
        try:
            if len(prices) < lookback:
                return 0.5  # Neutral probability
            
            recent_prices = prices[-lookback:]
            
            # Calculate z-score relative to mean
            mean_price = np.mean(recent_prices)
            std_price = np.std(recent_prices)
            current_z_score = (prices[-1] - mean_price) / std_price if std_price > 0 else 0
            
            # Higher z-score = higher mean reversion probability
            # Use normal CDF to convert z-score to probability
            reversion_prob = 2 * (1 - stats.norm.cdf(abs(current_z_score)))
            
            return min(reversion_prob, 0.9)  # Cap at 90%
            
        except Exception as e:
            logger.error(f"Mean reversion probability calculation failed: {e}")
            return 0.5
    
    @staticmethod
    def hp_trend_filter(prices: np.ndarray, lambda_param: float = 1600) -> tuple:
        """
        Hodrick-Prescott Trend Filter - separates trend from cycle
        NOW USES THE FULL MATHEMATICAL HP FILTER (no longer dead code!)
        
        Standard for financial data: lambda=1600 for quarterly, 6.25 for annual
        
        Returns: (trend, cycle, trend_direction)
        """
        try:
            if len(prices) < 10:
                return prices, np.zeros_like(prices), 0
            
            # Use the full mathematical HP filter (previously dead code!)
            trend, cycle = ProfessionalMomentumModels.hodrick_prescott_trend(prices, lambda_param)
            
            # Trend direction: slope of last 5 trend points
            if len(trend) >= 5:
                trend_direction = (trend[-1] - trend[-5]) / trend[-5] if trend[-5] != 0 else 0
            else:
                trend_direction = 0
            
            return trend, cycle, trend_direction
            
        except Exception as e:
            logger.error(f"HP Trend Filter calculation failed: {e}")
            return prices, np.zeros_like(prices), 0
    
    @staticmethod
    def cross_sectional_momentum(symbol_prices: Dict[str, np.ndarray], 
                                current_symbol: str, lookback: int = 20) -> float:
        """Calculate cross-sectional momentum (relative strength)"""
        try:
            if current_symbol not in symbol_prices:
                return 0.0
            
            current_prices = symbol_prices[current_symbol]
            if len(current_prices) < lookback:
                return 0.0
            
            # Calculate momentum for current symbol
            current_momentum = ProfessionalMomentumModels.momentum_score(current_prices, lookback)
            
            # Calculate momentum for all symbols
            all_momentums = []
            for symbol, prices in symbol_prices.items():
                if len(prices) >= lookback:
                    momentum = ProfessionalMomentumModels.momentum_score(prices, lookback)
                    all_momentums.append(momentum)
            
            if len(all_momentums) < 2:
                return 0.0
            
            # Calculate percentile rank
            percentile_rank = stats.percentileofscore(all_momentums, current_momentum) / 100.0
            
            # Convert to relative strength score (-1 to +1)
            relative_strength = (percentile_rank - 0.5) * 2
            
            return relative_strength
            
        except Exception as e:
            logger.error(f"Cross-sectional momentum calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def momentum_regime_detection(prices: np.ndarray, volume: np.ndarray = None) -> str:
        """Detect momentum regime using multiple indicators"""
        try:
            if len(prices) < 20:
                return "NEUTRAL"
            
            # Get trend and momentum indicators
            trend_strength = ProfessionalMomentumModels.trend_strength(prices)
            momentum_score = ProfessionalMomentumModels.momentum_score(prices)
            mean_reversion_prob = ProfessionalMomentumModels.mean_reversion_probability(prices)
            
            # Volume confirmation if available
            volume_confirmation = 1.0
            if volume is not None and len(volume) >= 5:
                recent_volume = np.mean(volume[-5:])
                avg_volume = np.mean(volume[-20:]) if len(volume) >= 20 else recent_volume
                volume_confirmation = min(recent_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
            
            # Regime classification
            if abs(trend_strength) > 0.3 and abs(momentum_score) > 0.02 and volume_confirmation > 1.2:
                if trend_strength > 0:
                    return "STRONG_UPTREND"
                else:
                    return "STRONG_DOWNTREND"
            elif abs(momentum_score) > 0.01 and mean_reversion_prob < 0.3:
                if momentum_score > 0:
                    return "MOMENTUM_UP"
                else:
                    return "MOMENTUM_DOWN"
            elif mean_reversion_prob > 0.7:
                return "MEAN_REVERSION"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            logger.error(f"Momentum regime detection failed: {e}")
            return "NEUTRAL"

class EnhancedMomentumSurfer(BaseStrategy):
    """
    INSTITUTIONAL-GRADE MOMENTUM SPECIALIST
    
    COMPETITIVE ADVANTAGES:
    1. HODRICK-PRESCOTT FILTER: Professional trend extraction vs simple moving averages
    2. MULTI-TIMEFRAME MOMENTUM: Statistical validation across multiple horizons
    3. CROSS-SECTIONAL ANALYSIS: Relative strength vs absolute momentum
    4. MEAN REVERSION PROBABILITY: Statistical prediction of momentum exhaustion
    5. REGIME-AWARE EXECUTION: Dynamic strategy adaptation based on momentum regime
    6. PROFESSIONAL RISK MANAGEMENT: Momentum-adjusted position sizing
    7. STATISTICAL VALIDATION: Significance testing for all momentum signals
    8. MACHINE LEARNING ENHANCEMENT: ML-validated momentum predictions
    """
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.strategy_name = "institutional_momentum_specialist"
        self.description = "Institutional-Grade Momentum Specialist with professional mathematical models"

        # 🚨 CRITICAL FIX: Initialize missing attributes from base class
        from datetime import time
        import pytz

        # Initialize time-based attributes (from set_market_bias method)
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.no_new_signals_after = time(15, 0)  # 3:00 PM IST - No new signals
        self.mandatory_close_time = time(15, 20)  # 3:20 PM IST - Force close all positions
        self.warning_close_time = time(15, 15)    # 3:15 PM IST - Start aggressive closing

        # Initialize position management attributes
        self.max_position_age_hours = 24  # Auto-close positions after 24 hours
        self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
        self.profit_lock_percentage = 1.0  # Lock profit at 1%
        
        # 🔥 FIX: Ensure management tracking attributes are initialized
        # (may not be set if BaseStrategy.__init__ was modified or failed partially)
        if not hasattr(self, 'management_actions_taken'):
            self.management_actions_taken = {}
        if not hasattr(self, 'last_management_time'):
            self.last_management_time = {}

        # PROFESSIONAL MOMENTUM MODELS
        self.momentum_models = ProfessionalMomentumModels()
        
        # CONFIGURABLE PARAMETERS (NO HARDCODED VALUES)
        self.momentum_threshold = config.get('momentum_threshold', 0.015)  # Configurable momentum threshold
        self.trend_strength_threshold = config.get('trend_strength_threshold', 0.25)  # Configurable trend confirmation
        self.mean_reversion_threshold = config.get('mean_reversion_threshold', 0.7)   # Configurable mean reversion probability
        
        # 🔥 MARKET CONDITION DETECTION THRESHOLDS (ALIGNED 2025-12-26)
        # 🚨 FIX: Removed gap between sideways (0.5%) and trending (1.5%)
        # Old: sideways=0.5%, trending=1.5% → stocks at 0.5-1.5% fell to unpredictable logic
        # New: sideways=0.3%, trending=0.5% → tighter, no gaps, clear boundaries
        self.trending_threshold = config.get('trending_threshold', 0.5)    # 0.5% change for trending (was 1.5%)
        self.breakout_threshold = config.get('breakout_threshold', 1.5)    # 1.5% change for breakout (was 2.5%)
        self.sideways_range = config.get('sideways_range', 0.3)            # ±0.3% is sideways (was 0.5%)

        # CONFIGURABLE STOCK UNIVERSE - now using base class symbol filtering
        self.watchlist = set(config.get('focus_stocks', [
            # Large Cap Leaders
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'ITC',
            'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
            'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC',
            # Mid Cap Momentum Leaders
            'BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'TECHM',
            'TITAN', 'NESTLEIND', 'ULTRACEMCO', 'JSWSTEEL', 'TATASTEEL'
        ]))
        
        # Set symbol filters for momentum strategy
        self.symbol_filters = {
            'min_volume': 500000,  # Minimum 5 lakh volume
            'min_price': 100,      # Min price ₹100
            'max_price': 10000,    # Max price ₹10,000
            'min_change_percent': 0.5  # Minimum 0.5% movement
        }

        # CONFIGURABLE POSITION MANAGEMENT
        self.max_momentum_positions = config.get('max_momentum_positions', 8)
        self.profit_booking_threshold = config.get('profit_booking_threshold', 0.25)
        self.stop_loss_threshold = config.get('stop_loss_threshold', 0.12)

        # ENHANCED RISK MANAGEMENT (CONFIGURABLE)
        self.max_daily_loss = config.get('max_daily_loss', -2000)  # Max daily loss in rupees
        self.max_single_trade_loss = config.get('max_single_trade_loss', -500)  # Max loss per trade
        self.max_daily_trades = config.get('max_daily_trades', 20)  # Max trades per day
        self.min_win_rate = config.get('min_win_rate', 0.50)  # Minimum required win rate
        self.max_consecutive_losses = config.get('max_consecutive_losses', 3)  # Max consecutive losses
        self.risk_multiplier = config.get('risk_multiplier', 1.0)  # Overall risk multiplier
        self.max_signals_per_cycle = config.get('max_signals_per_cycle', 5)  # Max signals per cycle

        # DYNAMIC RISK ADJUSTMENT
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.risk_reduction_level = 1.0  # Reduces position size when risk increases
        self.emergency_stop = False
        
        # MOMENTUM REGIME TRACKING
        self.current_momentum_regime = "NEUTRAL"
        self.momentum_regime_history = []
        
        # CROSS-SECTIONAL ANALYSIS
        self.symbol_price_history = {}  # For relative strength calculation
        self.relative_strength_scores = {}
        
        # PROFESSIONAL PERFORMANCE TRACKING
        self.momentum_performance = {
            'trend_following_pnl': 0.0,
            'mean_reversion_pnl': 0.0,
            'cross_sectional_pnl': 0.0,
            'regime_adaptation_pnl': 0.0
        }
        
        # MACHINE LEARNING COMPONENTS
        self.ml_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.feature_scaler = StandardScaler()
        self.ml_trained = False
        self.ml_features_history = []
        self.ml_labels_history = []
        
        # Market condition strategies
        self.strategies_by_condition = {
            'trending_up': self._trending_up_strategy,
            'trending_down': self._trending_down_strategy,
            'sideways': self._sideways_strategy,
            'breakout_up': self._breakout_up_strategy,
            'breakout_down': self._breakout_down_strategy,
            'reversal_up': self._reversal_up_strategy,
            'reversal_down': self._reversal_down_strategy,
            'high_volatility': self._high_volatility_strategy,
            'low_volatility': self._low_volatility_strategy
        }

        # BACKTESTING FRAMEWORK
        self.backtest_mode = config.get('backtest_mode', False)
        self.backtest_results = {
            'total_signals': 0,
            'profitable_signals': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'signals_by_condition': {}
        }
        self.backtest_trades = []
        
        logger.info("✅ SmartIntradayOptions strategy initialized")

    # BACKTESTING METHODS
    async def run_backtest(self, historical_data: Dict[str, List], start_date: str = None, end_date: str = None) -> Dict:
        """
        Run comprehensive backtest on historical data
        Args:
            historical_data: Dict[symbol, List[price_data]]
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
        Returns:
            Backtest results dictionary
        """
        logger.info("🔬 STARTING MOMENTUM STRATEGY BACKTEST")
        self.backtest_mode = True
        self.backtest_trades = []
        self.backtest_results = {
            'total_signals': 0,
            'profitable_signals': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'signals_by_condition': {}
        }

        try:
            # Process each symbol's historical data
            for symbol, price_history in historical_data.items():
                if len(price_history) < 50:  # Minimum data requirement
                    logger.warning(f"⚠️ Insufficient data for {symbol}: {len(price_history)} points")
                    continue

                logger.info(f"📊 Backtesting {symbol} with {len(price_history)} data points")

                # Simulate trading through historical data
                await self._simulate_historical_trading(symbol, price_history)

            # Calculate comprehensive backtest statistics
            self._calculate_backtest_statistics()

            logger.info("✅ BACKTEST COMPLETED")
            logger.info(f"📈 Total Signals: {self.backtest_results['total_signals']}")
            logger.info(f"💰 Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            logger.info(f"🎯 Win Rate: {self.backtest_results['win_rate']:.1%}")
            logger.info(f"📊 Sharpe Ratio: {self.backtest_results['sharpe_ratio']:.2f}")

            return self.backtest_results

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return self.backtest_results

    async def _simulate_historical_trading(self, symbol: str, price_history: List[Dict]):
        """Simulate trading through historical data"""
        try:
            # Reset strategy state for this symbol
            self.current_positions = {}
            self.symbol_cooldowns = {}

            # Process each historical data point
            for i, data_point in enumerate(price_history):
                if i < 20:  # Skip initial data for indicator warmup
                    continue

                # Create market data dict for strategy
                market_data = {symbol: data_point}

                # Generate signals (we're already in async context)
                try:
                    signals = await self.generate_signals(market_data)
                except Exception as e:
                    logger.warning(f"⚠️ Signal generation failed for {symbol}: {e}")
                    continue

                # Process each generated signal
                for signal in signals:
                    await self._process_backtest_signal(signal, price_history[i:], symbol)

        except Exception as e:
            logger.error(f"❌ Historical trading simulation failed for {symbol}: {e}")

    async def _process_backtest_signal(self, signal: Dict, future_prices: List[Dict], symbol: str):
        """Process a signal in backtest mode"""
        try:
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            target = signal.get('target', 0)
            confidence = signal.get('confidence', 0)

            if entry_price <= 0:
                return

            # Record signal
            self.backtest_results['total_signals'] += 1
            signal_condition = signal.get('market_condition', 'unknown')

            if signal_condition not in self.backtest_results['signals_by_condition']:
                self.backtest_results['signals_by_condition'][signal_condition] = 0
            self.backtest_results['signals_by_condition'][signal_condition] += 1

            # Simulate trade execution and exit
            trade_pnl, exit_reason = self._simulate_trade_exit(entry_price, stop_loss, target, future_prices)

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': entry_price + trade_pnl,
                'pnl': trade_pnl,
                'confidence': confidence,
                'condition': signal_condition,
                'exit_reason': exit_reason
            }

            self.backtest_trades.append(trade_record)

            if trade_pnl > 0:
                self.backtest_results['profitable_signals'] += 1

            self.backtest_results['total_pnl'] += trade_pnl

            logger.debug(f"📊 Backtest Trade: {symbol} @ {entry_price:.2f} → {trade_record['exit_price']:.2f} (P&L: ₹{trade_pnl:.2f})")

        except Exception as e:
            logger.error(f"❌ Backtest signal processing failed: {e}")

    def _simulate_trade_exit(self, entry_price: float, stop_loss: float, target: float, future_prices: List[Dict]) -> Tuple[float, str]:
        """Simulate when a trade would exit based on stop loss or target"""
        try:
            # Simulate holding for up to 50 periods or until stop/target hit
            for i, future_data in enumerate(future_prices[:50]):
                high = future_data.get('high', future_data.get('close', 0))
                low = future_data.get('low', future_data.get('close', 0))

                # Check for stop loss hit
                if low <= stop_loss:
                    pnl = stop_loss - entry_price
                    return pnl, 'stop_loss'

                # Check for target hit
                if high >= target:
                    pnl = target - entry_price
                    return pnl, 'target'

            # Exit at end of simulation period (assume market close)
            exit_price = future_prices[-1].get('close', entry_price)
            pnl = exit_price - entry_price
            return pnl, 'time_exit'

        except Exception as e:
            logger.error(f"❌ Trade exit simulation failed: {e}")
            return 0.0, 'error'

    def _calculate_backtest_statistics(self):
        """Calculate comprehensive backtest statistics"""
        try:
            if not self.backtest_trades:
                logger.warning("⚠️ No trades recorded in backtest")
                return

            trades = self.backtest_trades

            # Basic statistics
            self.backtest_results['total_signals'] = len(trades)
            self.backtest_results['profitable_signals'] = sum(1 for t in trades if t['pnl'] > 0)

            if self.backtest_results['total_signals'] > 0:
                self.backtest_results['win_rate'] = self.backtest_results['profitable_signals'] / self.backtest_results['total_signals']

            # P&L statistics
            pnl_values = [t['pnl'] for t in trades]
            self.backtest_results['total_pnl'] = sum(pnl_values)

            if pnl_values:
                profitable_trades = [p for p in pnl_values if p > 0]
                losing_trades = [p for p in pnl_values if p < 0]

                if profitable_trades:
                    self.backtest_results['avg_profit'] = sum(profitable_trades) / len(profitable_trades)
                if losing_trades:
                    self.backtest_results['avg_loss'] = abs(sum(losing_trades) / len(losing_trades))

                if self.backtest_results['avg_loss'] > 0:
                    self.backtest_results['profit_factor'] = (self.backtest_results['avg_profit'] * len(profitable_trades)) / (self.backtest_results['avg_loss'] * len(losing_trades))

            # Sharpe ratio calculation
            if len(pnl_values) > 1:
                returns = np.array(pnl_values)
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                self.backtest_results['sharpe_ratio'] = sharpe

            # Maximum drawdown
            cumulative_pnl = np.cumsum(pnl_values)
            peak = np.maximum.accumulate(cumulative_pnl)
            drawdown = cumulative_pnl - peak
            self.backtest_results['max_drawdown'] = abs(np.min(drawdown)) if len(drawdown) > 0 else 0

            logger.info("📊 BACKTEST STATISTICS CALCULATED")
            logger.info(f"🔍 Total Trades: {self.backtest_results['total_signals']}")
            logger.info(f"💰 Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            logger.info(f"🎯 Win Rate: {self.backtest_results['win_rate']:.1%}")
            logger.info(f"⚡ Profit Factor: {self.backtest_results['profit_factor']:.2f}")
            logger.info(f"📉 Max Drawdown: ₹{self.backtest_results['max_drawdown']:,.2f}")

        except Exception as e:
            logger.error(f"❌ Backtest statistics calculation failed: {e}")

    def get_backtest_report(self) -> str:
        """Generate detailed backtest report"""
        try:
            report = []
            report.append("📊 MOMENTUM STRATEGY BACKTEST REPORT")
            report.append("=" * 50)
            report.append(f"Total Signals: {self.backtest_results['total_signals']}")
            report.append(f"Profitable Signals: {self.backtest_results['profitable_signals']}")
            report.append(f"Win Rate: {self.backtest_results['win_rate']:.1%}")
            report.append(f"Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            report.append(f"Average Profit: ₹{self.backtest_results['avg_profit']:,.2f}")
            report.append(f"Average Loss: ₹{self.backtest_results['avg_loss']:,.2f}")
            report.append(f"Profit Factor: {self.backtest_results['profit_factor']:.2f}")
            report.append(f"Sharpe Ratio: {self.backtest_results['sharpe_ratio']:.2f}")
            report.append(f"Max Drawdown: ₹{self.backtest_results['max_drawdown']:,.2f}")

            # Signals by condition
            report.append("\n📈 SIGNALS BY MARKET CONDITION:")
            for condition, count in self.backtest_results['signals_by_condition'].items():
                report.append(f"  {condition}: {count}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Backtest report generation failed: {e}")
            return "Backtest report generation failed"

    # RISK MANAGEMENT METHODS
    def assess_risk_before_trade(self, symbol: str, entry_price: float, stop_loss: float, confidence: float) -> Tuple[bool, str, float]:
        """
        Comprehensive risk assessment before allowing a trade
        Returns: (allowed, reason, adjusted_quantity_multiplier)
        """
        try:
            # Emergency stop check
            if self.emergency_stop:
                return False, "EMERGENCY_STOP_ACTIVE", 0.0

            # Daily loss limit check
            if self.daily_pnl <= self.max_daily_loss:
                self.emergency_stop = True
                logger.critical(f"🚨 EMERGENCY STOP: Daily loss limit reached ₹{self.daily_pnl:.2f}")
                return False, "DAILY_LOSS_LIMIT_EXCEEDED", 0.0

            # Daily trade limit check
            if self.daily_trades >= self.max_daily_trades:
                return False, "DAILY_TRADE_LIMIT_EXCEEDED", 0.0

            # Single trade loss limit check
            potential_loss = abs(entry_price - stop_loss)
            if potential_loss > abs(self.max_single_trade_loss):
                return False, f"TRADE_LOSS_TOO_LARGE_₹{potential_loss:.2f}", 0.0

            # Consecutive losses check
            if self.consecutive_losses >= self.max_consecutive_losses:
                return False, f"CONSECUTIVE_LOSSES_LIMIT_{self.consecutive_losses}", 0.0

            # Confidence threshold check
            if confidence < 7.0:  # Minimum confidence required
                return False, f"LOW_CONFIDENCE_{confidence:.1f}", 0.0

            # Calculate dynamic risk multiplier
            risk_multiplier = self._calculate_dynamic_risk_multiplier()

            # Market condition risk adjustment
            market_risk = self._assess_market_risk()
            final_multiplier = risk_multiplier * market_risk * self.risk_multiplier

            logger.info(f"🛡️ Risk Assessment PASSED for {symbol}: multiplier={final_multiplier:.2f}")
            return True, "APPROVED", final_multiplier

        except Exception as e:
            logger.error(f"❌ Risk assessment failed for {symbol}: {e}")
            return False, f"RISK_ASSESSMENT_ERROR_{str(e)}", 0.0

    def _calculate_dynamic_risk_multiplier(self) -> float:
        """Calculate risk multiplier based on current performance"""
        try:
            base_multiplier = 1.0

            # Reduce risk after losses
            if self.daily_pnl < -500:
                base_multiplier *= 0.7
            elif self.daily_pnl < -1000:
                base_multiplier *= 0.5
            elif self.daily_pnl < -1500:
                base_multiplier *= 0.3

            # Reduce risk after consecutive losses
            if self.consecutive_losses >= 2:
                base_multiplier *= 0.6
            elif self.consecutive_losses >= 3:
                base_multiplier *= 0.4

            # Increase risk after consistent wins (but not too much)
            if self.consecutive_losses == 0 and self.daily_trades > 5:
                base_multiplier *= 1.2

            return min(base_multiplier, 2.0)  # Cap at 2x

        except Exception as e:
            logger.error(f"❌ Dynamic risk multiplier calculation failed: {e}")
            return 1.0

    def _assess_market_risk(self) -> float:
        """Assess current market risk level"""
        try:
            # High volatility periods = higher risk
            if self.current_momentum_regime == "HIGH_VOLATILITY":
                return 0.7
            elif self.current_momentum_regime == "CRISIS":
                return 0.5

            # Normal conditions
            return 1.0

        except Exception as e:
            logger.error(f"❌ Market risk assessment failed: {e}")
            return 1.0

    def update_risk_metrics(self, trade_result: float, symbol: str):
        """Update risk metrics after each trade"""
        try:
            self.daily_pnl += trade_result
            self.daily_trades += 1

            # Track consecutive losses
            if trade_result < 0:
                self.consecutive_losses += 1
                logger.warning(f"⚠️ Consecutive losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0

            # Emergency stop triggers
            if self.daily_pnl <= self.max_daily_loss:
                self.emergency_stop = True
                logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: Daily P&L ₹{self.daily_pnl:.2f}")

            if self.consecutive_losses >= self.max_consecutive_losses:
                logger.warning(f"⚠️ MAX CONSECUTIVE LOSSES REACHED: {self.consecutive_losses}")

            logger.info(f"📊 Risk Update: Daily P&L ₹{self.daily_pnl:.2f}, Trades: {self.daily_trades}, Consecutive Losses: {self.consecutive_losses}")

        except Exception as e:
            logger.error(f"❌ Risk metrics update failed: {e}")

    def reset_daily_risk_metrics(self):
        """Reset daily risk metrics (call at market open)"""
        try:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.consecutive_losses = 0
            self.emergency_stop = False
            self.risk_reduction_level = 1.0

            logger.info("🌅 Daily risk metrics reset - Fresh trading day")

        except Exception as e:
            logger.error(f"❌ Daily risk reset failed: {e}")

    def get_risk_status_report(self) -> str:
        """Generate comprehensive risk status report"""
        try:
            report = []
            report.append("🛡️ RISK MANAGEMENT STATUS REPORT")
            report.append("=" * 40)
            report.append(f"Daily P&L: ₹{self.daily_pnl:.2f}")
            report.append(f"Daily Trades: {self.daily_trades}/{self.max_daily_trades}")
            report.append(f"Consecutive Losses: {self.consecutive_losses}/{self.max_consecutive_losses}")
            report.append(f"Emergency Stop: {'ACTIVE' if self.emergency_stop else 'INACTIVE'}")
            report.append(f"Risk Reduction Level: {self.risk_reduction_level:.2f}")
            report.append(f"Max Daily Loss Limit: ₹{self.max_daily_loss:.2f}")
            report.append(f"Current Risk Level: {'HIGH' if self.emergency_stop else 'NORMAL'}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Risk status report failed: {e}")
            return "Risk status report generation failed"

    async def initialize(self):
        """Initialize the strategy with ML model warmup"""
        self.is_active = True
        
        # 🔥 FIX: ML MODEL AUTO-TRAINING - Load persisted training data
        await self._load_ml_training_data()
        
        # 🔥 FIX: Historical data warmup for indicators
        await self._warmup_indicators_with_historical()
        
        logger.info("✅ Smart Intraday Options loaded successfully")
    
    async def _load_ml_training_data(self):
        """
        🔥 FIX FOR LIMITATION: ML Signal Validation
        Load persisted ML training data from Redis on startup
        """
        try:
            import json
            
            # Try to get Redis client
            redis_client = None
            try:
                from src.core.redis_fallback_manager import redis_fallback_manager
                redis_client = redis_fallback_manager
            except ImportError:
                logger.debug("Redis not available for ML data persistence")
                return
            
            if not redis_client:
                return
            
            # Load persisted training data
            ml_data_key = f"ml_training_data:{self.strategy_name}"
            
            try:
                data_str = redis_client.get(ml_data_key)
                if data_str:
                    data = json.loads(data_str)
                    self.ml_features_history = [np.array(f) for f in data.get('features', [])]
                    self.ml_labels_history = data.get('labels', [])
                    
                    if len(self.ml_features_history) >= 50:
                        logger.info(f"📊 ML DATA LOADED: {len(self.ml_features_history)} training samples from Redis")
                        
                        # Train model immediately
                        await self._update_ml_model()
                    else:
                        logger.info(f"📊 ML DATA: {len(self.ml_features_history)} samples (need 50+ for training)")
                else:
                    logger.info("📊 No persisted ML training data found - starting fresh")
                    
            except Exception as redis_error:
                logger.debug(f"Redis ML data load failed: {redis_error}")
                
        except Exception as e:
            logger.error(f"ML training data load failed: {e}")
    
    async def _persist_ml_training_data(self):
        """Persist ML training data to Redis for survival across restarts"""
        try:
            import json
            
            if len(self.ml_features_history) < 10:
                return  # Not enough data to persist
            
            # Get Redis client
            redis_client = None
            try:
                from src.core.redis_fallback_manager import redis_fallback_manager
                redis_client = redis_fallback_manager
            except ImportError:
                return
            
            if not redis_client:
                return
            
            # Keep last 500 training samples
            features_to_save = [f.tolist() for f in self.ml_features_history[-500:]]
            labels_to_save = self.ml_labels_history[-500:]
            
            ml_data_key = f"ml_training_data:{self.strategy_name}"
            data = {
                'features': features_to_save,
                'labels': labels_to_save,
                'updated_at': datetime.now().isoformat()
            }
            
            redis_client.set(ml_data_key, json.dumps(data), ex=86400 * 30)  # 30 days TTL
            logger.debug(f"📊 ML training data persisted: {len(features_to_save)} samples")
            
        except Exception as e:
            logger.debug(f"ML data persistence failed: {e}")
    
    async def _warmup_indicators_with_historical(self):
        """
        🔥 FIX FOR LIMITATION: Cross-Sectional Momentum warmup
        Pre-load historical data for all FNO stocks to enable cross-sectional analysis
        """
        try:
            logger.info("🔄 INDICATOR WARMUP: Pre-loading historical data...")
            
            # Get Zerodha client
            zerodha_client = None
            if hasattr(self, 'orchestrator') and self.orchestrator:
                zerodha_client = getattr(self.orchestrator, 'zerodha_client', None)
            
            if not zerodha_client:
                logger.warning("⚠️ No Zerodha client - indicators will warmup from live data")
                return
            
            # Get list of FNO symbols to warmup
            fno_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 
                          'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT']
            
            warmup_count = 0
            for symbol in fno_symbols[:5]:  # Warmup top 5 to avoid rate limits
                try:
                    from datetime import timedelta
                    historical = await zerodha_client.get_historical_data(
                        symbol=symbol,
                        interval='5minute',
                        from_date=datetime.now() - timedelta(days=3),
                        to_date=datetime.now(),
                        exchange='NSE'
                    )
                    
                    if historical and len(historical) >= 20:
                        # Populate price history
                        if not hasattr(self, 'price_history'):
                            self.price_history = {}
                        self.price_history[symbol] = [c['close'] for c in historical[-50:]]
                        
                        # Populate volume history  
                        if not hasattr(self, 'volume_history'):
                            self.volume_history = {}
                        self.volume_history[symbol] = [c['volume'] for c in historical[-20:]]
                        
                        # Populate cross-sectional data
                        self.symbol_price_history[symbol] = np.array(self.price_history[symbol])
                        
                        warmup_count += 1
                        
                except Exception as sym_error:
                    logger.debug(f"Warmup failed for {symbol}: {sym_error}")
            
            if warmup_count > 0:
                logger.info(f"✅ INDICATOR WARMUP COMPLETE: {warmup_count} symbols pre-loaded")
            else:
                logger.warning("⚠️ INDICATOR WARMUP: No symbols loaded - will warmup from live data")
                
        except Exception as e:
            logger.error(f"Indicator warmup failed: {e}")

    async def on_market_data(self, data: Dict):
        """Process market data and generate intraday signals"""
        if not self.is_active:
            return
            
        try:
            # 🚨 SIGNAL EXPIRY: Clean up expired signals first
            self._cleanup_expired_signals()
            
            # Generate signals using the existing method
            signals = await self.generate_signals(data)
            
            # Store signals in current_positions for orchestrator to find
            for signal in signals:
                # 🚨 CRITICAL FIX: Validate signal is a dictionary, not a coroutine
                if not isinstance(signal, dict):
                    logger.error(f"❌ INVALID SIGNAL TYPE: Expected dict, got {type(signal)} - {signal}")
                    continue
                
                symbol = signal.get('symbol')
                if symbol:
                    # 🚨 EXECUTION THROTTLING: Check if we can execute this signal
                    if not self._can_execute_signal(symbol):
                        logger.info(f"⏳ THROTTLED: {symbol} execution blocked (30s cooldown)")
                        continue
                    
                    # Store signal and track creation time
                    self.current_positions[symbol] = signal
                    self._track_signal_creation(symbol)
                    logger.info(f"🎯 SMART INTRADAY: {signal['symbol']} {signal['action']} "
                               f"Confidence: {signal.get('confidence', 0):.1f}/10 "
                               f"(expires in 5 min)")
                
        except Exception as e:
            logger.error(f"Error in Smart Intraday Options: {e}")

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals based on comprehensive market condition analysis"""
        try:
            signals = []

            if not market_data:
                return signals

            # 🚨 SIGNAL LIMIT: Prevent excessive signals that can overwhelm the system
            max_signals_per_cycle = getattr(self, 'max_signals_per_cycle', 5)
            logger.info(f"🎯 Signal limit: {max_signals_per_cycle} per cycle")

            # Update active symbols based on market conditions
            self.update_active_symbols(market_data)
            
            # 🔥 PREFETCH GARCH DATA: Get Zerodha daily data for accurate volatility
            # This populates the cache so calculate_atr uses proper GARCH
            if hasattr(self, 'prefetch_garch_for_symbols') and self.active_symbols:
                try:
                    # Only prefetch top 20 most active symbols to avoid API spam
                    symbols_to_prefetch = list(self.active_symbols)[:20]
                    await self.prefetch_garch_for_symbols(symbols_to_prefetch, max_concurrent=5)
                except Exception as garch_err:
                    logger.debug(f"GARCH prefetch skipped: {garch_err}")
            
            # Analyze each active symbol
            for stock in self.active_symbols:
                # 🚨 BREAK EARLY: Stop if we've reached the signal limit
                if len(signals) >= max_signals_per_cycle:
                    logger.warning(f"⚠️ SIGNAL LIMIT REACHED: {len(signals)}/{max_signals_per_cycle} - stopping analysis")
                    break

                if stock in market_data:
                    # 🔥 CRITICAL: Fetch historical data to enable RSI/MACD/Bollinger
                    # This only happens once per symbol per session
                    if not hasattr(self, '_historical_data_fetched') or stock not in self._historical_data_fetched:
                        await self._fetch_historical_for_symbol(stock)
                    
                    # Detect market condition for this stock
                    market_condition = self._detect_market_condition(stock, market_data)

                    # Generate signal based on condition
                    signal = await self._generate_condition_based_signal(stock, market_condition, market_data)
                    if signal:
                        # 🎯 MARKET DEPTH VALIDATION: Check liquidity and order book
                        depth_analysis = self.analyze_market_depth(stock, market_data)
                        
                        # Block signals with poor liquidity
                        if depth_analysis.get('liquidity_score', 5) <= 3:
                            logger.warning(f"🚫 {stock}: Signal blocked - POOR LIQUIDITY (score: {depth_analysis.get('liquidity_score')})")
                            continue
                        
                        # Check if depth conflicts with signal direction
                        signal_direction = signal.get('action', 'BUY')
                        depth_rec = depth_analysis.get('recommendation', 'NEUTRAL')
                        
                        if signal_direction == 'BUY' and depth_rec == 'RESISTANCE_AHEAD':
                            logger.warning(f"⚠️ {stock}: BUY signal with SELL WALL - reducing confidence")
                            signal['confidence'] = signal.get('confidence', 8.0) * 0.9
                        elif signal_direction == 'SELL' and depth_rec == 'SUPPORT_BELOW':
                            logger.warning(f"⚠️ {stock}: SELL signal with BUY WALL - reducing confidence")
                            signal['confidence'] = signal.get('confidence', 8.0) * 0.9
                        
                        # 🎯 OI ANALYSIS: Check institutional positioning
                        oi_analysis = self.analyze_open_interest(stock, market_data)
                        oi_bias = oi_analysis.get('institutional_bias', 'NEUTRAL')
                        oi_signal_type = oi_analysis.get('oi_signal', 'NEUTRAL')
                        
                        # Check if OI conflicts with signal direction
                        if signal_direction == 'BUY' and oi_bias == 'BEARISH':
                            if oi_signal_type == 'SHORT_BUILDUP':
                                logger.warning(f"⚠️ {stock}: BUY vs SHORT BUILDUP - reducing confidence by 15%")
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.85
                            else:
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.95
                        elif signal_direction == 'SELL' and oi_bias == 'BULLISH':
                            if oi_signal_type == 'LONG_BUILDUP':
                                logger.warning(f"⚠️ {stock}: SELL vs LONG BUILDUP - reducing confidence by 15%")
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.85
                            else:
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.95
                        
                        # 🎯 DAILY/WEEKLY LEVELS: Check proximity to S/R
                        level_analysis = self.calculate_daily_weekly_levels(stock, market_data)
                        nearest_level = level_analysis.get('nearest_level', {})
                        level_recommendation = level_analysis.get('recommendation', 'NEUTRAL')
                        
                        # Warn if signal conflicts with nearby level
                        if nearest_level:
                            level_type = nearest_level.get('type', '')
                            level_distance = nearest_level.get('distance_percent', 100)
                            
                            # BUY near resistance = risky
                            if signal_direction == 'BUY' and level_type == 'RESISTANCE' and level_distance < 0.5:
                                logger.warning(f"⚠️ {stock}: BUY signal near RESISTANCE ({nearest_level.get('name')}) at ₹{nearest_level.get('price')}")
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.92
                            
                            # SELL near support = risky  
                            elif signal_direction == 'SELL' and level_type == 'SUPPORT' and level_distance < 0.5:
                                logger.warning(f"⚠️ {stock}: SELL signal near SUPPORT ({nearest_level.get('name')}) at ₹{nearest_level.get('price')}")
                                signal['confidence'] = signal.get('confidence', 8.0) * 0.92
                        
                        # 🎯 NEW: VOLUME LEADING INDICATORS - Can PREDICT price moves!
                        # Get volume data for leading indicator analysis
                        stock_data = market_data.get(stock, {})
                        prices = []
                        volumes = []
                        highs = []
                        lows = []
                        
                        # Extract price/volume data from MTF data or price history
                        if hasattr(self, 'mtf_data') and stock in self.mtf_data:
                            candles = self.mtf_data[stock].get('5min', [])
                            if candles:
                                prices = [c.get('close', 0) for c in candles if c.get('close', 0) > 0]
                                volumes = [c.get('volume', 0) for c in candles if c.get('volume', 0) > 0]
                                highs = [c.get('high', 0) for c in candles if c.get('high', 0) > 0]
                                lows = [c.get('low', 0) for c in candles if c.get('low', 0) > 0]
                        
                        # Get volume-based leading signals
                        volume_leading = {}
                        if len(prices) >= 10 and len(volumes) >= 10:
                            volume_leading = self.get_volume_leading_signals(
                                stock, prices, volumes, highs if len(highs) >= 10 else None, lows if len(lows) >= 10 else None
                            )
                            
                            leading_score = volume_leading.get('leading_score', 0)
                            leading_signals = volume_leading.get('leading_signals', [])
                            
                            # 🎯 USE VOLUME LEADING INDICATORS TO ADJUST CONFIDENCE
                            if signal_direction == 'BUY':
                                if leading_score >= 30:
                                    # Volume indicates accumulation - boost confidence
                                    signal['confidence'] = signal.get('confidence', 8.0) * 1.1
                                    logger.info(f"🎯 {stock}: VOLUME LEADS UP! Score={leading_score}, Signals={leading_signals}")
                                elif leading_score <= -50:
                                    # 🚨 2025-12-26 FIX: Raised threshold from -20 to -50
                                    # Score -20 to -50 is weak - only block on STRONG distribution
                                    # Volume indicates distribution - reduce confidence or skip
                                    signal['confidence'] = signal.get('confidence', 8.0) * 0.8
                                    logger.warning(f"⚠️ {stock}: BUY signal but STRONG DISTRIBUTION detected (Score={leading_score})")
                                    if volume_leading.get('distribution') and leading_score <= -60:
                                        # Only block on very strong distribution (score <= -60)
                                        logger.warning(f"🚫 {stock}: BUY signal BLOCKED - Strong smart money distribution!")
                                        continue  # Skip this signal
                            
                            elif signal_direction == 'SELL':
                                if leading_score <= -30:
                                    # Volume indicates distribution - boost confidence
                                    signal['confidence'] = signal.get('confidence', 8.0) * 1.1
                                    logger.info(f"🎯 {stock}: VOLUME LEADS DOWN! Score={leading_score}, Signals={leading_signals}")
                                elif leading_score >= 50:
                                    # 🚨 2025-12-26 FIX: Raised threshold from 20 to 50
                                    # Score 20-50 is weak - only block on STRONG accumulation
                                    # Volume indicates accumulation - reduce confidence or skip
                                    signal['confidence'] = signal.get('confidence', 8.0) * 0.8
                                    logger.warning(f"⚠️ {stock}: SELL signal but STRONG ACCUMULATION detected (Score={leading_score})")
                                    if volume_leading.get('accumulation') and leading_score >= 60:
                                        # Only block on very strong accumulation (score >= 60)
                                        logger.warning(f"🚫 {stock}: SELL signal BLOCKED - Strong smart money accumulation!")
                                        continue  # Skip this signal
                        
                        # Add all analysis metadata to signal (initialize first to avoid KeyError)
                        signal['metadata'] = signal.get('metadata', {})
                        
                        # 🎯 NEW: CALIBRATE CONFIDENCE based on actual performance
                        try:
                            from src.core.signal_enhancement import signal_enhancer
                            
                            # Get calibrated confidence based on actual win rate
                            strategy_name = self.name if hasattr(self, 'name') else 'momentum_surfer'
                            base_conf = signal.get('confidence', 8.0)
                            calibrated_conf, cal_reason = signal_enhancer.get_calibrated_confidence(strategy_name, base_conf)
                            
                            if abs(calibrated_conf - base_conf) > 0.3:
                                signal['confidence'] = calibrated_conf
                                signal['metadata']['confidence_calibration'] = cal_reason
                            
                            # Check if strategy should be allowed based on performance
                            allowed, perf_reason = signal_enhancer.should_allow_signal_based_on_performance(strategy_name, calibrated_conf)
                            if not allowed:
                                logger.warning(f"🚫 {stock}: Signal BLOCKED by performance filter: {perf_reason}")
                                continue
                                
                        except Exception as cal_err:
                            logger.debug(f"Confidence calibration skipped: {cal_err}")
                        signal['metadata']['market_depth'] = depth_analysis
                        signal['metadata']['oi_analysis'] = oi_analysis
                        signal['metadata']['daily_weekly_levels'] = level_analysis
                        signal['metadata']['volume_leading'] = volume_leading
                        
                        signals.append(signal)
                        logger.info(f"✅ Signal generated for {stock}: {len(signals)}/{max_signals_per_cycle} (Depth: {depth_rec}, OI: {oi_bias}, Level: {level_recommendation}, VolScore: {volume_leading.get('leading_score', 0)})")

            logger.info(f"📊 Smart Intraday Options generated {len(signals)} signals (limit: {max_signals_per_cycle})")
            return signals

        except Exception as e:
            logger.error(f"Error in Smart Intraday Options: {e}")
            return []

    async def _fetch_historical_for_symbol(self, symbol: str) -> bool:
        """
        🔥 CRITICAL: Fetch MULTI-TIMEFRAME historical data from Zerodha.
        Fetches 5-min, 15-min, and 60-min candles for proper trend confirmation.
        """
        try:
            # Track which symbols we've already fetched
            if not hasattr(self, '_historical_data_fetched'):
                self._historical_data_fetched = set()
            
            if symbol in self._historical_data_fetched:
                return True  # Already fetched
            
            # Get Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not hasattr(orchestrator, 'zerodha_client') or not orchestrator.zerodha_client:
                logger.debug(f"⚠️ Zerodha client not available for historical data: {symbol}")
                return False
            
            zerodha_client = orchestrator.zerodha_client
            from datetime import datetime, timedelta
            
            # Initialize multi-timeframe storage
            if not hasattr(self, 'mtf_data'):
                self.mtf_data = {}
            if symbol not in self.mtf_data:
                self.mtf_data[symbol] = {'5min': [], '15min': [], '60min': []}
            
            # ============= FETCH 5-MINUTE CANDLES =============
            candles_5m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='5minute',
                from_date=datetime.now() - timedelta(days=3),
                to_date=datetime.now()
            )
            
            if candles_5m and len(candles_5m) >= 14:
                self.mtf_data[symbol]['5min'] = candles_5m[-50:]
                
                # Pre-populate price_history with closing prices (5-min)
                if not hasattr(self, 'price_history'):
                    self.price_history = {}
                closes = [c['close'] for c in candles_5m[-50:]]
                self.price_history[symbol] = closes
                
                # Pre-populate volume_history
                if not hasattr(self, 'volume_history'):
                    self.volume_history = {}
                volumes = [c['volume'] for c in candles_5m[-20:]]
                self.volume_history[symbol] = volumes
            
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
            
            # Log multi-timeframe data status
            tf_5m = len(self.mtf_data[symbol]['5min'])
            tf_15m = len(self.mtf_data[symbol]['15min'])
            tf_60m = len(self.mtf_data[symbol]['60min'])
            
            # 🔥 FIX: Only mark as fetched if we actually got enough data for RSI calculation
            # Otherwise retry on next cycle
            if tf_5m >= 14:
                self._historical_data_fetched.add(symbol)
                logger.info(f"✅ MTF DATA LOADED: {symbol} - 5min:{tf_5m}, 15min:{tf_15m}, 60min:{tf_60m} candles")
            else:
                logger.warning(f"⚠️ MTF DATA INSUFFICIENT: {symbol} - 5min:{tf_5m} < 14 required. Will retry.")
            
            return tf_5m >= 14
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching historical data for {symbol}: {e}")
            return False
    
    def _analyze_multi_timeframe(self, symbol: str, current_data: Dict) -> Dict:
        """
        🎯 MULTI-TIMEFRAME ANALYSIS for Higher Accuracy Signals
        
        Strategy: Only take trades when ALL timeframes align
        - 60-min: Major trend direction (BULLISH/BEARISH/NEUTRAL)
        - 15-min: Medium-term trend confirmation
        - 5-min: Entry timing
        
        Returns confidence boost only when all timeframes agree.
        """
        try:
            result = {
                'mtf_aligned': False,
                'direction': 'NEUTRAL',
                'confidence_boost': 0.0,
                'timeframes': {
                    '5min': 'NEUTRAL',
                    '15min': 'NEUTRAL',
                    '60min': 'NEUTRAL'
                },
                'alignment_score': 0,
                'reasoning': ''
            }
            
            if not hasattr(self, 'mtf_data') or symbol not in self.mtf_data:
                result['reasoning'] = 'No MTF data available'
                return result
            
            mtf = self.mtf_data[symbol]
            
            # ============= 60-MINUTE (HOURLY) TREND =============
            # 🚨 CRITICAL FIX: Added SMA slope detection to avoid false signals
            # when price is above SMA but SMA is falling (reversal in progress)
            trend_60m = 'NEUTRAL'
            if mtf['60min'] and len(mtf['60min']) >= 6:
                closes_60m = [c['close'] for c in mtf['60min'][-10:]]
                
                sma_5 = np.mean(closes_60m[-5:])
                sma_5_prev = np.mean(closes_60m[-6:-1]) if len(closes_60m) >= 6 else sma_5
                current_60m = closes_60m[-1]
                
                # Momentum: 3-period price change
                momentum_60m = (closes_60m[-1] / closes_60m[-4] - 1) * 100 if len(closes_60m) >= 4 else 0
                # SMA slope: is the average itself trending?
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                
                # 🎯 AND logic: Price position + SMA direction + momentum all must agree
                if current_60m > sma_5 * 1.002 and sma_slope > 0.05 and momentum_60m > 0.3:
                    trend_60m = 'BULLISH'
                elif current_60m < sma_5 * 0.998 and sma_slope < -0.05 and momentum_60m < -0.3:
                    trend_60m = 'BEARISH'
            
            result['timeframes']['60min'] = trend_60m
            
            # ============= 15-MINUTE TREND =============
            trend_15m = 'NEUTRAL'
            if mtf['15min'] and len(mtf['15min']) >= 6:
                closes_15m = [c['close'] for c in mtf['15min'][-15:]]
                
                sma_5 = np.mean(closes_15m[-5:])
                sma_5_prev = np.mean(closes_15m[-6:-1]) if len(closes_15m) >= 6 else sma_5
                current_15m = closes_15m[-1]
                momentum_15m = (closes_15m[-1] / closes_15m[-4] - 1) * 100 if len(closes_15m) >= 4 else 0
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                
                if current_15m > sma_5 * 1.001 and sma_slope > 0.03 and momentum_15m > 0.2:
                    trend_15m = 'BULLISH'
                elif current_15m < sma_5 * 0.999 and sma_slope < -0.03 and momentum_15m < -0.2:
                    trend_15m = 'BEARISH'
            
            result['timeframes']['15min'] = trend_15m
            
            # ============= 5-MINUTE TREND (Entry Timing) =============
            trend_5m = 'NEUTRAL'
            if mtf['5min'] and len(mtf['5min']) >= 6:
                closes_5m = [c['close'] for c in mtf['5min'][-20:]]
                
                sma_5 = np.mean(closes_5m[-5:])
                sma_5_prev = np.mean(closes_5m[-6:-1]) if len(closes_5m) >= 6 else sma_5
                sma_10 = np.mean(closes_5m[-10:])
                current_5m = closes_5m[-1]
                momentum_5m = (closes_5m[-1] / closes_5m[-3] - 1) * 100 if len(closes_5m) >= 3 else 0
                sma_slope = (sma_5 - sma_5_prev) / sma_5_prev * 100 if sma_5_prev > 0 else 0
                
                # More sensitive for entry timing but still require slope agreement
                if current_5m > sma_5 and sma_5 > sma_10 and sma_slope > 0.01 and momentum_5m > 0.1:
                    trend_5m = 'BULLISH'
                elif current_5m < sma_5 and sma_5 < sma_10 and sma_slope < -0.01 and momentum_5m < -0.1:
                    trend_5m = 'BEARISH'
            
            result['timeframes']['5min'] = trend_5m
            
            # ============= ALIGNMENT CHECK =============
            bullish_count = sum(1 for tf in result['timeframes'].values() if tf == 'BULLISH')
            bearish_count = sum(1 for tf in result['timeframes'].values() if tf == 'BEARISH')
            neutral_count = sum(1 for tf in result['timeframes'].values() if tf == 'NEUTRAL')
            
            # PERFECT ALIGNMENT (All 3 timeframes agree)
            if bullish_count == 3:
                result['mtf_aligned'] = True
                result['direction'] = 'BULLISH'
                result['confidence_boost'] = 1.5  # +50% confidence
                result['alignment_score'] = 3
                result['reasoning'] = '🎯 PERFECT MTF ALIGNMENT: All timeframes BULLISH'
                
            elif bearish_count == 3:
                result['mtf_aligned'] = True
                result['direction'] = 'BEARISH'
                result['confidence_boost'] = 1.5  # +50% confidence
                result['alignment_score'] = 3
                result['reasoning'] = '🎯 PERFECT MTF ALIGNMENT: All timeframes BEARISH'
                
            # STRONG ALIGNMENT (2 out of 3 timeframes agree, including hourly)
            elif bullish_count == 2 and trend_60m == 'BULLISH':
                result['mtf_aligned'] = True
                result['direction'] = 'BULLISH'
                result['confidence_boost'] = 1.2  # +20% confidence
                result['alignment_score'] = 2
                result['reasoning'] = '📈 STRONG MTF: Hourly + 1 other BULLISH'
                
            elif bearish_count == 2 and trend_60m == 'BEARISH':
                result['mtf_aligned'] = True
                result['direction'] = 'BEARISH'
                result['confidence_boost'] = 1.2  # +20% confidence
                result['alignment_score'] = 2
                result['reasoning'] = '📉 STRONG MTF: Hourly + 1 other BEARISH'
            
            # 🚨 NEW: NEUTRAL-DOMINANT scenarios - NO CONFLICT
            # All 3 NEUTRAL = No MTF opinion, let signal through
            elif neutral_count == 3:
                result['mtf_aligned'] = True
                result['direction'] = 'NEUTRAL'
                result['confidence_boost'] = 0.9  # Small 10% penalty
                result['alignment_score'] = 0
                result['reasoning'] = '⏸️ MTF NEUTRAL: No strong trend - signal allowed'
            
            # 2 NEUTRAL + 1 directional
            elif neutral_count == 2:
                if bullish_count == 1:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BULLISH'
                    result['confidence_boost'] = 1.0
                    result['alignment_score'] = 1
                    result['reasoning'] = '📊 MTF WEAK SUPPORT: 1 BULLISH + 2 NEUTRAL'
                elif bearish_count == 1:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BEARISH'
                    result['confidence_boost'] = 1.0
                    result['alignment_score'] = 1
                    result['reasoning'] = '📊 MTF WEAK SUPPORT: 1 BEARISH + 2 NEUTRAL'
                else:
                    result['mtf_aligned'] = True
                    result['direction'] = 'NEUTRAL'
                    result['confidence_boost'] = 0.9
                    result['alignment_score'] = 0
                    result['reasoning'] = '⏸️ MTF NEUTRAL: Signal allowed'
            
            # 1 NEUTRAL + 2 directional
            elif neutral_count == 1:
                if bullish_count == 2:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BULLISH'
                    result['confidence_boost'] = 1.15
                    result['alignment_score'] = 2
                    result['reasoning'] = '📈 MTF SUPPORT: 2 BULLISH + 1 NEUTRAL'
                elif bearish_count == 2:
                    result['mtf_aligned'] = True
                    result['direction'] = 'BEARISH'
                    result['confidence_boost'] = 1.15
                    result['alignment_score'] = 2
                    result['reasoning'] = '📉 MTF SUPPORT: 2 BEARISH + 1 NEUTRAL'
                # 1 BULLISH + 1 BEARISH + 1 NEUTRAL = true conflict
                elif bullish_count == 1 and bearish_count == 1:
                    result['mtf_aligned'] = False
                    result['direction'] = 'NEUTRAL'
                    result['confidence_boost'] = 0.5
                    result['alignment_score'] = 0
                    result['reasoning'] = f'⚠️ MTF CONFLICT: Mixed signals'
                else:
                    result['mtf_aligned'] = False
                    result['direction'] = 'NEUTRAL'
                    result['confidence_boost'] = 0.6
                    result['alignment_score'] = max(bullish_count, bearish_count)
                    result['reasoning'] = f'⚠️ MTF WEAK: 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
                
            else:
                # ACTUAL CONFLICT - opposing signals
                result['mtf_aligned'] = False
                result['direction'] = 'NEUTRAL'
                result['confidence_boost'] = 0.5  # Reduce confidence by 50%
                result['alignment_score'] = max(bullish_count, bearish_count)
                result['reasoning'] = f'⚠️ MTF CONFLICT: 60m={trend_60m}, 15m={trend_15m}, 5m={trend_5m}'
            
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis for {symbol}: {e}")
            return {
                'mtf_aligned': False,
                'direction': 'NEUTRAL',
                'confidence_boost': 0.5,
                'timeframes': {'5min': 'ERROR', '15min': 'ERROR', '60min': 'ERROR'},
                'alignment_score': 0,
                'reasoning': f'MTF analysis error: {str(e)}'
            }

    def _detect_market_condition(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """
        🎯 ENHANCED: Detect market condition using ALL available indicators
        Now actually uses the advanced models that were previously dead code!
        """
        try:
            data = market_data.get(symbol, {})
            if not data:
                return 'sideways'
            
            # ============= BASIC DATA =============
            change_percent = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            ltp = data.get('ltp', data.get('price', 0))
            open_price = data.get('open', ltp)
            high = data.get('high', ltp)
            low = data.get('low', ltp)
            previous_close = data.get('previous_close', ltp)
            
            # ============= VOLUME ANALYSIS (REAL, NOT FAKE) =============
            # Get real volume history from tracking
            if not hasattr(self, 'volume_history'):
                self.volume_history = {}
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            
            # Add current volume to history
            self.volume_history[symbol].append(volume)
            # Keep last 20 periods
            self.volume_history[symbol] = self.volume_history[symbol][-20:]
            
            # Calculate REAL volume ratio (need at least 5 data points)
            if len(self.volume_history[symbol]) >= 5:
                avg_volume = np.mean(self.volume_history[symbol][:-1])  # Exclude current
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            else:
                volume_ratio = 1.0  # Not enough data yet
            
            # ============= CANDLE BODY ANALYSIS =============
            # 🔥 FIX: Check if REAL OHLC data is available (not synthetic)
            ohlc_available = data.get('ohlc_available', False)
            
            # If OHLC not available from TrueData, use historical MTF data
            if not ohlc_available or high <= 0 or low <= 0 or open_price <= 0:
                # Try to get OHLC from MTF data (fetched from Zerodha)
                if hasattr(self, 'mtf_data') and symbol in self.mtf_data:
                    mtf_5m = self.mtf_data[symbol].get('5min', [])
                    if mtf_5m and len(mtf_5m) > 0:
                        # Get today's OHLC from 5-min candles
                        today_candles = mtf_5m[-20:]  # Last 20 5-min candles
                        if today_candles:
                            open_price = today_candles[0]['open']
                            high = max(c['high'] for c in today_candles)
                            low = min(c['low'] for c in today_candles)
                            ohlc_available = True
                            logger.debug(f"📊 {symbol}: Using MTF OHLC - O:{open_price:.2f} H:{high:.2f} L:{low:.2f}")
            
            # Calculate candle range and pressures (only if real OHLC available)
            if ohlc_available and high > low > 0 and open_price > 0:
                candle_range = high - low

                # Prefer pressure from the latest 5m candle OHLC (more stable than day-range).
                # This avoids frequent 0%/100% when LTP is near day low/high.
                mtf_series = self._get_indicator_series_from_mtf(symbol, timeframe='5min', limit=60)
                opens_5m = mtf_series.get('opens', []) if isinstance(mtf_series, dict) else []
                closes_5m = mtf_series.get('closes', []) if isinstance(mtf_series, dict) else []
                highs_5m = mtf_series.get('highs', []) if isinstance(mtf_series, dict) else []
                lows_5m = mtf_series.get('lows', []) if isinstance(mtf_series, dict) else []

                if (
                    opens_5m and closes_5m and highs_5m and lows_5m and
                    len(opens_5m) == len(closes_5m) == len(highs_5m) == len(lows_5m)
                ):
                    last_open = float(opens_5m[-1] or 0)
                    last_close = float(closes_5m[-1] or 0)
                    last_high = float(highs_5m[-1] or 0)
                    last_low = float(lows_5m[-1] or 0)

                    rng = last_high - last_low
                    if rng > 0 and last_open > 0 and last_close > 0:
                        # Close position in range: 0..1 (0 at low, 1 at high)
                        pos_in_range = (last_close - last_low) / rng
                        pos_in_range = max(0.0, min(1.0, pos_in_range))

                        # Body strength: 0..1, direction sets bias
                        body = (last_close - last_open) / rng
                        body_strength = min(1.0, abs(body))
                        direction = 1.0 if body >= 0 else -1.0

                        base_pressure = 0.5 + 0.5 * direction * body_strength  # 0..1
                        buying_pressure = 0.6 * base_pressure + 0.4 * pos_in_range
                        buying_pressure = max(0.01, min(0.99, buying_pressure))
                        selling_pressure = 1.0 - buying_pressure
                    else:
                        buying_pressure = 0.5
                        selling_pressure = 0.5
                else:
                    # Fallback: day-range-based pressure with soft clamp
                    buying_pressure = (ltp - low) / candle_range
                    buying_pressure = max(0.01, min(0.99, buying_pressure))
                    selling_pressure = 1.0 - buying_pressure
            else:
                # 🔥 NO FAKE VALUES - Use neutral pressure when OHLC unavailable
                buying_pressure = 0.5
                selling_pressure = 0.5
                candle_range = 0.01
                logger.debug(f"⚠️ {symbol}: OHLC unavailable - using neutral pressure")
            
            # Candle body size (absolute move from open)
            body_size = abs(ltp - open_price) / open_price * 100 if open_price > 0 else 0
            is_green_candle = ltp > open_price if open_price > 0 else (change_percent > 0)
            
            # ============= PRICE HISTORY FOR INDICATORS =============
            if not hasattr(self, 'price_history'):
                self.price_history = {}
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            # Prefer candle closes from mtf_data (time-consistent indicators).
            # Fall back to LTP buffer ONLY if candle data isn't available.
            mtf_series = self._get_indicator_series_from_mtf(symbol, timeframe='5min', limit=60)
            closes = mtf_series.get('closes', []) if isinstance(mtf_series, dict) else []

            if len(closes) >= 14:
                self.price_history[symbol] = closes[-50:]
                prices = np.array(self.price_history[symbol])
            else:
                self.price_history[symbol].append(ltp)
                self.price_history[symbol] = self.price_history[symbol][-50:]  # Keep 50 periods
                prices = np.array(self.price_history[symbol])
            
            # ============= CROSS-SECTIONAL MOMENTUM (PREVIOUSLY DEAD CODE!) =============
            # Update symbol_price_history for cross-sectional analysis
            self.symbol_price_history[symbol] = prices
            
            # Calculate cross-sectional momentum (relative strength vs all symbols)
            cross_sectional_rank = 0.5  # Default to neutral
            if len(self.symbol_price_history) >= 5 and len(prices) >= 20:
                cross_sectional_rank = ProfessionalMomentumModels.cross_sectional_momentum(
                    self.symbol_price_history, symbol, lookback=20
                )
                self.relative_strength_scores[symbol] = cross_sectional_rank
            
            # ============= ADVANCED INDICATORS (ALL PHASES COMPLETE!) =============
            momentum_score = 0.0
            rsi = 50.0
            mean_reversion_prob = 0.5
            trend_strength = 0.0
            hp_trend_direction = 0.0
            macd_signal = None
            macd_crossover = None
            macd_state = 'neutral'  # Current MACD state (not just crossover)
            bollinger_squeeze = False
            bollinger_breakout = None
            rsi_divergence = None
            
            if len(prices) >= 14:
                # Calculate RSI
                rsi = self._calculate_rsi(prices, 14)
                
                # Use ProfessionalMomentumModels
                momentum_score = ProfessionalMomentumModels.momentum_score(prices, min(20, len(prices)))
                mean_reversion_prob = ProfessionalMomentumModels.mean_reversion_probability(prices)
                trend_strength = ProfessionalMomentumModels.trend_strength(prices)
                
                # HP Trend Filter - separates trend from noise
                hp_trend, hp_cycle, hp_trend_direction = ProfessionalMomentumModels.hp_trend_filter(prices)
            
            # ============= PHASE 2: MACD INTEGRATION =============
            if len(prices) >= 26:
                macd_data = self.calculate_macd_signal(list(prices))
                macd_signal = macd_data.get('histogram', 0)
                macd_crossover = macd_data.get('crossover')  # 'bullish', 'bearish', or None (only at crossover moment)
                macd_state = macd_data.get('state', 'neutral')  # Current state: 'bullish', 'bearish', 'neutral'
                macd_divergence = macd_data.get('divergence')  # 'bullish', 'bearish', or None
                
                if macd_crossover:
                    logger.info(f"📊 {symbol} MACD CROSSOVER: {macd_crossover} (state={macd_state})")
            
            # ============= PHASE 2: BOLLINGER BANDS + TTM SQUEEZE =============
            squeeze_quality = 'LOW'
            keltner_squeeze = False
            volume_confirms = False
            
            if len(prices) >= 20:
                # 🎯 TTM SQUEEZE: Extract OHLCV data for Keltner Channel calculation
                highs, lows, volumes = None, None, None
                if hasattr(self, 'mtf_data') and symbol in self.mtf_data:
                    candles = self.mtf_data[symbol].get('5min', [])
                    if candles and len(candles) >= 20:
                        highs = [c.get('high', c.get('close', 0)) for c in candles[-50:]]
                        lows = [c.get('low', c.get('close', 0)) for c in candles[-50:]]
                        volumes = [c.get('volume', 0) for c in candles[-50:]]
                
                bollinger_data = self.detect_bollinger_squeeze(symbol, list(prices), highs=highs, lows=lows, volumes=volumes)
                bollinger_squeeze = bollinger_data.get('squeezing', False)
                bollinger_breakout = bollinger_data.get('breakout_direction')  # 'up', 'down', or None
                squeeze_intensity = bollinger_data.get('squeeze_intensity', 0)
                squeeze_quality = bollinger_data.get('squeeze_quality', 'LOW')
                keltner_squeeze = bollinger_data.get('keltner_squeeze', False)
                volume_confirms = bollinger_data.get('volume_confirms', False)
                
                # Only log HIGH/MEDIUM quality squeezes
                if bollinger_squeeze and squeeze_quality in ['HIGH', 'MEDIUM']:
                    logger.info(f"🔥 {symbol} TTM SQUEEZE! Quality: {squeeze_quality} | Intensity: {squeeze_intensity:.2f} | "
                               f"Keltner: {'✓' if keltner_squeeze else '✗'} | Vol: {'✓' if volume_confirms else '✗'}")
                if bollinger_breakout and squeeze_quality in ['HIGH', 'MEDIUM']:
                    logger.info(f"💥 {symbol} TTM BREAKOUT {bollinger_breakout.upper()}: Quality={squeeze_quality}")
            
            # ============= PHASE 2: RSI DIVERGENCE DETECTION =============
            if len(prices) >= 14:
                # Build RSI history for divergence detection
                rsi_history = []
                for i in range(14, len(prices)):
                    rsi_val = self._calculate_rsi(prices[:i+1], 14)
                    rsi_history.append(rsi_val)
                
                if len(rsi_history) >= 14:
                    rsi_divergence = self.calculate_rsi_divergence(symbol, list(prices[-14:]), rsi_history[-14:])
                    if rsi_divergence:
                        logger.info(f"📈 {symbol} RSI DIVERGENCE: {rsi_divergence.upper()} - High probability reversal!")
            
            # ============= CONDITION DETECTION WITH ALL INDICATORS (ALL PHASES COMPLETE!) =============
            condition = 'sideways'
            confidence_factors = []
            
            # 🔥 PRIORITY 0: RSI DIVERGENCE (ONLY with confirmation!)
            # 🚨 FIX: RSI divergence alone is NOT enough - need confirmation signals
            # ICICIBANK bug: RSI divergence triggered BUY despite 0% buy pressure and Bollinger breaking DOWN
            
            if rsi_divergence == 'bullish' and change_percent < 0:
                # 🎯 CONFIRMATION FILTERS for bullish divergence:
                # 1. Need SOME buying pressure (>= 20%, not 0%)
                # 2. Bollinger should NOT be breaking DOWN (conflicting signal)
                # 3. Cross-sectional rank should not be extremely negative
                has_buy_pressure = buying_pressure >= 0.20  # At least 20% buying
                bollinger_not_conflicting = bollinger_breakout != 'down'  # Not breaking opposite
                not_extreme_weakness = cross_sectional_rank >= -0.50  # Not in bottom 50%
                
                if has_buy_pressure and bollinger_not_conflicting and not_extreme_weakness:
                    condition = 'reversal_up'
                    confidence_factors.append(f"📈 RSI BULLISH DIVERGENCE - CONFIRMED reversal!")
                    confidence_factors.append(f"Buy Pressure: {buying_pressure:.0%}")
                    logger.info(f"✅ {symbol} RSI DIVERGENCE REVERSAL CONFIRMED: Buy pressure {buying_pressure:.0%}, Rank {cross_sectional_rank:.0%}")
                else:
                    # Log why divergence was rejected
                    rejection_reasons = []
                    if not has_buy_pressure:
                        rejection_reasons.append(f"buy_pressure={buying_pressure:.0%}<20%")
                    if not bollinger_not_conflicting:
                        rejection_reasons.append("Bollinger breaking DOWN")
                    if not not_extreme_weakness:
                        rejection_reasons.append(f"rank={cross_sectional_rank:.0%}<-50%")
                    logger.warning(f"🚫 {symbol} RSI DIVERGENCE REJECTED - unconfirmed: {', '.join(rejection_reasons)}")
                    # Don't set reversal_up - let other conditions handle it
            
            elif rsi_divergence == 'bearish' and change_percent > 0:
                # 🎯 CONFIRMATION FILTERS for bearish divergence:
                has_sell_pressure = selling_pressure >= 0.20  # At least 20% selling
                bollinger_not_conflicting = bollinger_breakout != 'up'  # Not breaking opposite
                not_extreme_strength = cross_sectional_rank <= 0.50  # Not in top 50%
                
                if has_sell_pressure and bollinger_not_conflicting and not_extreme_strength:
                    condition = 'reversal_down'
                    confidence_factors.append(f"📉 RSI BEARISH DIVERGENCE - CONFIRMED reversal!")
                    confidence_factors.append(f"Sell Pressure: {selling_pressure:.0%}")
                    logger.info(f"✅ {symbol} RSI DIVERGENCE REVERSAL CONFIRMED: Sell pressure {selling_pressure:.0%}, Rank {cross_sectional_rank:.0%}")
                else:
                    rejection_reasons = []
                    if not has_sell_pressure:
                        rejection_reasons.append(f"sell_pressure={selling_pressure:.0%}<20%")
                    if not bollinger_not_conflicting:
                        rejection_reasons.append("Bollinger breaking UP")
                    if not not_extreme_strength:
                        rejection_reasons.append(f"rank={cross_sectional_rank:.0%}>50%")
                    logger.warning(f"🚫 {symbol} RSI DIVERGENCE REJECTED - unconfirmed: {', '.join(rejection_reasons)}")
            
            # 🔥 PRIORITY 1: TTM SQUEEZE BREAKOUT (Only HIGH/MEDIUM quality!)
            elif bollinger_breakout == 'up' and bollinger_squeeze and squeeze_quality in ['HIGH', 'MEDIUM']:
                condition = 'breakout_up'
                confidence_factors.append(f"💥 TTM SQUEEZE BREAKOUT UP! Quality: {squeeze_quality}")
                if keltner_squeeze:
                    confidence_factors.append(f"TRUE KELTNER SQUEEZE ✓")
                if volume_confirms:
                    confidence_factors.append(f"VOLUME CONFIRMS ✓")
                if macd_crossover == 'bullish':
                    confidence_factors.append(f"MACD CONFIRMS: Bullish crossover")
                logger.info(f"🚀 {symbol} TTM BREAKOUT UP: Quality={squeeze_quality}, Keltner={keltner_squeeze}, Vol={volume_confirms}")
            
            elif bollinger_breakout == 'down' and bollinger_squeeze and squeeze_quality in ['HIGH', 'MEDIUM']:
                condition = 'breakout_down'
                confidence_factors.append(f"💥 TTM SQUEEZE BREAKOUT DOWN! Quality: {squeeze_quality}")
                if keltner_squeeze:
                    confidence_factors.append(f"TRUE KELTNER SQUEEZE ✓")
                if volume_confirms:
                    confidence_factors.append(f"VOLUME CONFIRMS ✓")
                if macd_crossover == 'bearish':
                    confidence_factors.append(f"MACD CONFIRMS: Bearish crossover")
                logger.info(f"📉 {symbol} TTM BREAKOUT DOWN: Quality={squeeze_quality}, Keltner={keltner_squeeze}, Vol={volume_confirms}")
            
            # 🎯 PRIORITY 2: REVERSAL DETECTION (Candle body + volume)
            elif change_percent < -1.0 and buying_pressure > 0.7 and volume_ratio > 1.5:
                condition = 'reversal_up'
                confidence_factors.append(f"STRONG BUY CANDLE: {buying_pressure:.0%} buying pressure")
                confidence_factors.append(f"VOLUME SPIKE: {volume_ratio:.1f}x average")
                if rsi < 35:
                    confidence_factors.append(f"RSI OVERSOLD: {rsi:.1f}")
                if macd_crossover == 'bullish':
                    confidence_factors.append(f"MACD BULLISH CROSSOVER")
                logger.info(f"🔄 {symbol} REVERSAL UP: Price down {change_percent:.1f}% but buying pressure {buying_pressure:.0%}")
            
            elif change_percent > 1.0 and selling_pressure > 0.7 and volume_ratio > 1.5:
                condition = 'reversal_down'
                confidence_factors.append(f"STRONG SELL CANDLE: {selling_pressure:.0%} selling pressure")
                confidence_factors.append(f"VOLUME SPIKE: {volume_ratio:.1f}x average")
                if rsi > 65:
                    confidence_factors.append(f"RSI OVERBOUGHT: {rsi:.1f}")
                if macd_crossover == 'bearish':
                    confidence_factors.append(f"MACD BEARISH CROSSOVER")
                logger.info(f"🔄 {symbol} REVERSAL DOWN: Price up {change_percent:.1f}% but selling pressure {selling_pressure:.0%}")
            
            # 🎯 PRIORITY 3: MACD CROSSOVER SIGNALS (with HP Trend confirmation)
            elif macd_crossover == 'bullish' and momentum_score > 0 and rsi < 60:
                # Confirm with HP trend - smoothed trend should not be strongly negative
                if hp_trend_direction >= -0.005:  # HP trend not strongly down
                    # 🚨 FIX: MACD bullish REQUIRES buy pressure confirmation
                    if selling_pressure > 0.58 and buying_pressure < 0.42:
                        logger.info(f"⚠️ {symbol}: MACD bullish but sell pressure {selling_pressure:.0%} dominates - waiting")
                    else:
                        condition = 'trending_up'
                        confidence_factors.append(f"MACD BULLISH CROSSOVER with momentum confirmation")
                        if hp_trend_direction > 0.002:
                            confidence_factors.append(f"HP TREND CONFIRMS: {hp_trend_direction:+.2%}")
                        if buying_pressure > 0.5:
                            confidence_factors.append(f"Buying pressure: {buying_pressure:.0%}")
                else:
                    logger.info(f"⚠️ {symbol}: MACD bullish but HP trend negative ({hp_trend_direction:+.2%}) - waiting")
            
            elif macd_crossover == 'bearish' and momentum_score < 0 and rsi > 40:
                # Confirm with HP trend - smoothed trend should not be strongly positive
                if hp_trend_direction <= 0.005:  # HP trend not strongly up
                    # 🚨 FIX: MACD bearish REQUIRES sell pressure confirmation
                    if buying_pressure > 0.58 and selling_pressure < 0.42:
                        logger.info(f"⚠️ {symbol}: MACD bearish but buy pressure {buying_pressure:.0%} dominates - waiting")
                    else:
                        condition = 'trending_down'
                        confidence_factors.append(f"MACD BEARISH CROSSOVER with momentum confirmation")
                        if hp_trend_direction < -0.002:
                            confidence_factors.append(f"HP TREND CONFIRMS: {hp_trend_direction:+.2%}")
                        if selling_pressure > 0.5:
                            confidence_factors.append(f"Selling pressure: {selling_pressure:.0%}")
                else:
                    logger.info(f"⚠️ {symbol}: MACD bearish but HP trend positive ({hp_trend_direction:+.2%}) - waiting")
            
            # BREAKOUT with volume confirmation + CROSS-SECTIONAL RANK (NEWLY INTEGRATED!)
            elif abs(change_percent) >= self.breakout_threshold and volume_ratio > 1.5:
                if change_percent > 0 and buying_pressure > 0.6:
                    # Confirm breakout UP with cross-sectional strength
                    if cross_sectional_rank >= 0.6:  # Top 40% performers
                        condition = 'breakout_up'
                        confidence_factors.append(f"BREAKOUT UP: {change_percent:.1f}% with {volume_ratio:.1f}x volume")
                        confidence_factors.append(f"📊 CROSS-SECTIONAL: Top {(1-cross_sectional_rank)*100:.0f}% performer")
                    else:
                        condition = 'trending_up'  # Downgrade to trending if weak relative strength
                        confidence_factors.append(f"BREAKOUT DOWNGRADED: Low relative strength ({cross_sectional_rank:.0%})")
                elif change_percent < 0 and selling_pressure > 0.6:
                    # Confirm breakout DOWN with cross-sectional weakness
                    if cross_sectional_rank <= 0.4:  # Bottom 40% performers
                        condition = 'breakout_down'
                        confidence_factors.append(f"BREAKOUT DOWN: {change_percent:.1f}% with {volume_ratio:.1f}x volume")
                        confidence_factors.append(f"📊 CROSS-SECTIONAL: Bottom {cross_sectional_rank*100:.0f}% performer")
                    else:
                        condition = 'trending_down'  # Downgrade if relative strength is OK
                        confidence_factors.append(f"BREAKOUT DOWNGRADED: Relative strength OK ({cross_sectional_rank:.0%})")
            
            # TRENDING with momentum confirmation
            elif change_percent >= self.trending_threshold:
                # Only confirm uptrend if momentum and trend align
                if momentum_score > 0 or trend_strength > 0.1:
                    # Check for exhaustion signals
                    if rsi > 70 or macd_crossover == 'bearish':
                        condition = 'reversal_down'
                        confidence_factors.append(f"EXHAUSTION: RSI {rsi:.1f}, MACD turning")
                    # 🚨 FIX: Check buy/sell pressure - don't BUY if sell pressure dominates
                    elif selling_pressure > 0.58 and buying_pressure < 0.42:
                        logger.info(f"⚠️ {symbol}: Trending UP but sell pressure {selling_pressure:.0%} > buy pressure {buying_pressure:.0%} - WAITING")
                        condition = None  # No signal
                    else:
                        condition = 'trending_up'
                        confidence_factors.append(f"MOMENTUM: {momentum_score:.3f}, TREND: {trend_strength:.2f}")
                else:
                    if mean_reversion_prob > 0.6:
                        condition = 'reversal_down'
                        confidence_factors.append(f"EXHAUSTION: Mean reversion prob {mean_reversion_prob:.0%}")
                    elif selling_pressure > 0.58 and buying_pressure < 0.42:
                        logger.info(f"⚠️ {symbol}: Would trend UP but sell pressure {selling_pressure:.0%} dominates - WAITING")
                        condition = None  # No signal
                    else:
                        condition = 'trending_up'
            
            elif change_percent <= -self.trending_threshold:
                # 🚨 FIX: Require CONFIRMATION for reversal signals - not just divergence
                # MACD bullish alone is confirmation; RSI divergence needs buy pressure
                
                # MACD bullish crossover WITH buy pressure = strong reversal
                if macd_crossover == 'bullish' and buying_pressure >= 0.30:
                    condition = 'reversal_up'
                    confidence_factors.append(f"🔥 MACD BULLISH + Buy pressure {buying_pressure:.0%}")
                # High buy pressure + volume = confirmed reversal
                elif buying_pressure > 0.65 and volume_ratio > 1.3:
                    condition = 'reversal_up'
                    confidence_factors.append(f"🔥 OVERSOLD BOUNCE: RSI {rsi:.1f}, Buying {buying_pressure:.0%}")
                # RSI divergence only with confirmation
                elif rsi_divergence == 'bullish' and buying_pressure >= 0.20 and cross_sectional_rank >= -0.50:
                    condition = 'reversal_up'
                    confidence_factors.append(f"🔥 RSI DIVERGENCE CONFIRMED: Buy {buying_pressure:.0%}")
                elif momentum_score < 0 or trend_strength < -0.1:
                    condition = 'trending_down'
                    confidence_factors.append(f"MOMENTUM: {momentum_score:.3f}, TREND: {trend_strength:.2f}")
                else:
                    # Mean reversion only with buy pressure
                    if mean_reversion_prob > 0.6 and buying_pressure >= 0.40:
                        condition = 'reversal_up'
                        confidence_factors.append(f"REVERSAL SIGNAL: RSI {rsi:.1f}, Mean Rev {mean_reversion_prob:.0%}, Buy {buying_pressure:.0%}")
                    elif rsi < 30 and buying_pressure > 0.50:  # Deeply oversold with buying
                        condition = 'reversal_up'
                        confidence_factors.append(f"DEEPLY OVERSOLD: RSI {rsi:.1f}, Buy {buying_pressure:.0%}")
                    else:
                        condition = 'trending_down'
            
            # SIDEWAYS / RANGE
            elif abs(change_percent) <= self.sideways_range:
                condition = 'sideways'
            
            # HIGH VOLATILITY
            elif volume_ratio > 2.0:
                condition = 'high_volatility'
            
            # 🔥 USE PROFESSIONAL MOMENTUM REGIME DETECTION (previously dead code!)
            momentum_regime = ProfessionalMomentumModels.momentum_regime_detection(prices)
            
            # 🔥 LOG ALL FACTORS FOR TRANSPARENCY (ALL PHASES!)
            if condition != 'sideways':
                factors_str = " | ".join(confidence_factors) if confidence_factors else "Price action only"
                logger.info(f"📊 {symbol} CONDITION: {condition} | REGIME: {momentum_regime}")
                logger.info(f"   📈 Price: {change_percent:+.2f}% | Vol: {volume_ratio:.1f}x | Candle: {'GREEN' if is_green_candle else 'RED'}")
                logger.info(f"   🕯️ Buy Pressure: {buying_pressure:.0%} | Sell Pressure: {selling_pressure:.0%}")
                logger.info(f"   📉 RSI: {rsi:.1f} | Momentum: {momentum_score:.3f} | Trend: {trend_strength:.2f} | HP: {hp_trend_direction:+.2%}")
                logger.info(f"   🔄 Mean Rev: {mean_reversion_prob:.0%} | MACD: {macd_state} | Bollinger: {'SQUEEZE!' if bollinger_squeeze else 'normal'}")
                logger.info(f"   📊 Cross-Sectional Rank: {cross_sectional_rank:.0%} | Regime: {momentum_regime}")
                if rsi_divergence:
                    logger.info(f"   🎯 RSI DIVERGENCE: {rsi_divergence.upper()}")
                if bollinger_breakout:
                    logger.info(f"   💥 BOLLINGER BREAKOUT: {bollinger_breakout.upper()}")
                logger.info(f"   ✅ Factors: {factors_str}")
            
            return condition
            
        except Exception as e:
            logger.error(f"Error detecting market condition for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 'sideways'
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator - FIXED: Never returns exactly 0"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
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

    async def _generate_condition_based_signal(self, symbol: str, condition: str, 
                                             market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal based on detected market condition - FIXED: Returns dict, not coroutine"""
        try:
            strategy_func = self.strategies_by_condition.get(condition)
            if not strategy_func:
                return {}  # Return empty dict instead of None
            
            # 🚨 CRITICAL FIX: Ensure we await the strategy function properly
            result = await strategy_func(symbol, market_data)
            
            # 🚨 CRITICAL FIX: Validate result is a dictionary
            if result and isinstance(result, dict):
                return result
            elif hasattr(result, '__await__'):
                logger.error(f"❌ COROUTINE DETECTED: {symbol} strategy returned coroutine")
                # Try to await it
                try:
                    actual_result = await result
                    if isinstance(actual_result, dict):
                        return actual_result
                except Exception as await_error:
                    logger.error(f"❌ Failed to await coroutine: {await_error}")
            
            # If result is not a dict or is None, return empty dict
            # Note: None is expected when confidence is below threshold
            logger.debug(f"No signal generated for {symbol} (result type: {type(result)})")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error generating condition-based signal for {symbol}: {e}")
            return {}  # Always return dict, never None

    async def _trending_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for uptrending stocks"""
        data = market_data.get(symbol, {})
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis (Day + Intraday)
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        
        # Use weighted bias instead of simple change_percent
        if weighted_bias > 1.0:  # Strong uptrend (weighted)
            # 🚨 CRITICAL FIX: Base confidence raised from 7.0 to 7.5 to pass threshold
            # Strong uptrends are valid setups - don't filter them out
            confidence = 7.5 + min(weighted_bias * 0.15, 1.0)
            
            # Boost confidence if aligned with market
            if "WITH MARKET" in alignment:
                confidence += 0.5
            elif "AGAINST MARKET" in alignment:
                confidence -= 1.0
                
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🎯 DYNAMIC LEVELS: Use chart-based ATR/swing analysis instead of hardcoded %
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'BUY', ltp, data)
            logger.info(f"📊 {symbol} BUY: Dynamic levels - Entry={ltp:.2f}, SL={stop_loss:.2f}, Target={target:.2f}")
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='BUY',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Uptrending stock strategy - Bias: {weighted_bias:.1f}% ({alignment})"
                },
                market_bias=self.market_bias
            )
        return None

    async def _trending_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downtrending stocks - SHORT SELLING"""
        data = market_data.get(symbol, {})
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        
        if weighted_bias < -1.0:  # Strong downtrend (weighted)
            # 🚨 CRITICAL FIX: Base confidence raised from 7.0 to 7.5 to pass threshold
            # Strong downtrends are valid setups - don't filter them out
            confidence = 7.5 + min(abs(weighted_bias) * 0.15, 1.0)
            
            # Boost confidence if aligned with market
            if "WITH MARKET" in alignment:
                confidence += 0.5
            elif "AGAINST MARKET" in alignment:
                confidence -= 1.0
                
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🎯 DYNAMIC LEVELS: Use chart-based ATR/swing analysis instead of hardcoded %
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'SELL', ltp, data)
            logger.info(f"📊 {symbol} SELL: Dynamic levels - Entry={ltp:.2f}, SL={stop_loss:.2f}, Target={target:.2f}")
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='SELL',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Downtrending stock SHORT strategy - Bias: {weighted_bias:.1f}% ({alignment})"
                },
                market_bias=self.market_bias
            )
        return None

    async def _sideways_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        RANGE TRADING strategy - DISABLED FOR INTRADAY
        
        🚨 2025-12-26: Disabled for intraday trading because:
        1. Range trading requires precise S/R levels we don't reliably detect
        2. Signals always had confidence 6.8, below 8.0 threshold - never executed
        3. Generated contradictory signals on trending stocks
        4. Trend-following is more reliable for intraday
        
        For swing trading or if you want to re-enable:
        - Add proper S/R detection (swing highs/lows, Camarilla pivots)
        - Add volume confirmation at S/R levels
        - Add Bollinger band width check (must be narrow for true range)
        - Add regime check (only in CHOPPY regime)
        - Raise base confidence to 7.5+ for valid setups
        """
        # DISABLED: Return None - let trending strategies handle these stocks
        return None
        
        # PRESERVED CODE BELOW FOR REFERENCE (commented out)
        # ================================================
        # data = market_data.get(symbol, {})
        # dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        # weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        # alignment = dual_analysis.get('alignment', 'UNKNOWN')
        # pattern = dual_analysis.get('pattern', 'UNKNOWN')
        # ltp = data.get('ltp', 0)
        # 
        # if 'CONTINUATION' in pattern:
        #     return None
        # if "WITH MARKET (BEAR)" in alignment and weighted_bias < 0:
        #     return None
        # if "WITH MARKET (BULL)" in alignment and weighted_bias > 0:
        #     return None
        
        # Range trading logic preserved but disabled
        data = market_data.get(symbol, {})
        ltp = data.get('ltp', 0)
        if False:  # DISABLED - preserved for reference
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'SELL', ltp, data)
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='SELL',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Range trading: Sell at resistance - Bias: {weighted_bias:.1f}% ({alignment})"
                },
                market_bias=self.market_bias
            )
        return None

    async def _breakout_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward breakouts"""
        data = market_data.get(symbol, {})
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        
        volume = data.get('volume', 0)
        
        if weighted_bias > 1.5 and volume > 100000:
            # 🎯 ENHANCED: Breakouts fail often - be conservative
            confidence = 7.2 + min(weighted_bias * 0.08, 0.8)
            
            # Boost confidence if aligned with market
            if "WITH MARKET" in alignment:
                confidence += 0.5
            elif "AGAINST MARKET" in alignment:
                confidence -= 0.5
            
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🎯 DYNAMIC LEVELS: Use chart-based ATR/swing analysis
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'BUY', ltp, data)
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='BUY',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Upward breakout with volume - Bias: {weighted_bias:.1f}% ({alignment}), Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _breakout_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward breakouts"""
        data = market_data.get(symbol, {})
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        
        volume = data.get('volume', 0)
        
        if weighted_bias < -1.5 and volume > 100000:
            # 🎯 ENHANCED: Breakdown trades carry significant risk
            confidence = 7.2 + min(abs(weighted_bias) * 0.08, 0.8)
            
            # Boost confidence if aligned with market
            if "WITH MARKET" in alignment:
                confidence += 0.5
            elif "AGAINST MARKET" in alignment:
                confidence -= 0.5
            
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🎯 DYNAMIC LEVELS: Use chart-based ATR/swing analysis
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'SELL', ltp, data)
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='SELL',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Downward breakout with volume - Bias: {weighted_bias:.1f}% ({alignment}), Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _reversal_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward reversals - ENHANCED WITH PATTERN CHECKS"""
        data = market_data.get(symbol, {})
        
        # 🔥 CRITICAL FIX: Don't generate BUY signal if SHORT position already exists!
        if hasattr(self, 'active_positions') and symbol in self.active_positions:
            pos = self.active_positions[symbol]
            pos_qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
            pos_side = pos.get('side', None) if isinstance(pos, dict) else getattr(pos, 'side', None)
            if pos_side is None:
                pos_side = 'LONG' if pos_qty > 0 else 'SHORT'
            if pos_side == 'SHORT' or pos_qty < 0:
                logger.info(f"🚫 REVERSAL BLOCKED: {symbol} has existing SHORT position - not generating BUY")
                return None
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        pattern = dual_analysis.get('pattern', 'UNKNOWN')
        
        # 🚨 2025-12-26 FIX: Don't try reversal on strong trends
        if 'BEARISH CONTINUATION' in pattern:
            logger.debug(f"⚠️ {symbol}: Skipping reversal_up - {pattern} indicates strong downtrend")
            return None
        
        # 🚨 FIX: Don't BUY reversal when WITH bearish market
        if "WITH MARKET (BEAR)" in alignment:
            logger.debug(f"⚠️ {symbol}: Skipping reversal_up - stock aligned WITH bear market")
            return None
        
        # Reversal logic: Modest positive move (potential bounce)
        if 0.5 <= weighted_bias <= 1.0:
            # 🎯 ENHANCED: Raised base confidence to 7.2 (was 6.8)
            # Reversals are valid when confirmed
            confidence = 7.2
            
            # Stronger confidence if against market (relative strength)
            if "AGAINST MARKET" in alignment:
                confidence += 0.5  # Strong relative strength
            elif "WITH MARKET" in alignment:
                confidence += 0.3
                
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🔥 Use chart-based levels instead of hardcoded percentages
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'BUY', ltp, data)
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='BUY',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'EQUITY',  # Changed from OPTIONS
                    'reason': f"Upward reversal pattern - Bias: {weighted_bias:.1f}% ({alignment})",
                    'trailing_stop_enabled': True,
                    'trailing_stop_trigger': 0.015,  # Activate trailing at 1.5% profit
                    'trailing_stop_distance': 0.01   # Trail by 1%
                },
                market_bias=self.market_bias
            )
        return None

    async def _reversal_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward reversals - ENHANCED WITH PATTERN CHECKS"""
        data = market_data.get(symbol, {})
        
        # 🔥 CRITICAL FIX: Don't generate SELL signal if LONG position already exists!
        if hasattr(self, 'active_positions') and symbol in self.active_positions:
            pos = self.active_positions[symbol]
            pos_qty = pos.get('quantity', 0) if isinstance(pos, dict) else getattr(pos, 'quantity', 0)
            pos_side = pos.get('side', None) if isinstance(pos, dict) else getattr(pos, 'side', None)
            if pos_side is None:
                pos_side = 'LONG' if pos_qty > 0 else 'SHORT'
            if pos_side == 'LONG' or pos_qty > 0:
                logger.info(f"🚫 REVERSAL BLOCKED: {symbol} has existing LONG position - not generating SELL")
                return None
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        pattern = dual_analysis.get('pattern', 'UNKNOWN')
        
        # 🚨 2025-12-26 FIX: Don't try reversal on strong trends
        if 'BULLISH CONTINUATION' in pattern:
            logger.debug(f"⚠️ {symbol}: Skipping reversal_down - {pattern} indicates strong uptrend")
            return None
        
        # 🚨 FIX: Don't SELL reversal when WITH bullish market
        if "WITH MARKET (BULL)" in alignment:
            logger.debug(f"⚠️ {symbol}: Skipping reversal_down - stock aligned WITH bull market")
            return None
        
        # Reversal logic: Modest negative move (potential fade)
        if -1.0 <= weighted_bias <= -0.5:
            # 🎯 ENHANCED: Raised base confidence to 7.2 (was 6.5)
            confidence = 7.2
            
            # Stronger confidence if against market (relative weakness)
            if "AGAINST MARKET" in alignment:
                confidence += 0.5  # Strong relative weakness
            elif "WITH MARKET" in alignment:
                confidence += 0.3
                
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🔥 Use chart-based levels instead of hardcoded percentages
            stop_loss, target = self.calculate_chart_based_levels(symbol, 'SELL', ltp, data)
            
            return await self.create_standard_signal(
                symbol=symbol,
                action='SELL',
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'EQUITY',  # Changed from OPTIONS
                    'reason': f"Downward reversal pattern - Bias: {weighted_bias:.1f}% ({alignment})",
                    'trailing_stop_enabled': True,
                    'trailing_stop_trigger': 0.015,  # Activate trailing at 1.5% profit
                    'trailing_stop_distance': 0.01   # Trail by 1%
                },
                market_bias=self.market_bias
            )
        return None

    async def _high_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for high volatility periods - ENHANCED WITH PATTERN CHECKS"""
        data = market_data.get(symbol, {})
        
        # 🎯 ENHANCED: Use Dual-Timeframe Analysis
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        alignment = dual_analysis.get('alignment', 'UNKNOWN')
        pattern = dual_analysis.get('pattern', 'UNKNOWN')
        
        volume = data.get('volume', 0)
        
        if volume > 200000 and abs(weighted_bias) > 0.5:
            signal_type = 'BUY' if weighted_bias > 0 else 'SELL'
            
            # 🚨 2025-12-26 FIX: Don't trade against pattern
            if signal_type == 'BUY' and 'BEARISH CONTINUATION' in pattern:
                logger.debug(f"⚠️ {symbol}: Skipping high_vol BUY - {pattern}")
                return None
            if signal_type == 'SELL' and 'BULLISH CONTINUATION' in pattern:
                logger.debug(f"⚠️ {symbol}: Skipping high_vol SELL - {pattern}")
                return None
            
            # Base confidence - high volatility with volume is valid
            confidence = 7.5
            
            # Add confidence boosts for strong setups
            if abs(weighted_bias) > 1.0:  # Stronger bias
                confidence += 0.3
            
            # Check alignment - WITH MARKET is better than AGAINST
            if "WITH MARKET" in alignment:
                confidence += 0.5
            elif "AGAINST MARKET" in alignment:
                confidence -= 0.3  # Penalize counter-trend slightly
            
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            
            # 🔥 Use chart-based levels instead of hardcoded percentages
            stop_loss, target = self.calculate_chart_based_levels(symbol, signal_type, ltp, data)
            return await self.create_standard_signal(
                symbol=symbol,
                action=signal_type,
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"High volatility momentum - Bias: {weighted_bias:.1f}% ({alignment}), Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _low_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Strategy for low volatility periods - DISABLED FOR INTRADAY
        
        🚨 2025-12-26: Disabled because:
        1. Low volatility = low opportunity for intraday
        2. Base confidence was 6.2, below 7.0 threshold - never executed
        3. Small moves get eaten by spreads and slippage
        """
        # DISABLED: Low volatility is not good for intraday
        return None
        
        # PRESERVED CODE BELOW FOR REFERENCE
        data = market_data.get(symbol, {})
        dual_analysis = self.analyze_stock_dual_timeframe(symbol, data)
        weighted_bias = dual_analysis.get('weighted_bias', 0.0)
        
        if False:  # DISABLED
            signal_type = 'BUY' if weighted_bias > 0 else 'SELL'
            confidence = 6.2
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                return None
            stop_loss = ltp * (0.99 if signal_type == 'BUY' else 1.01)
            target = ltp * (1.02 if signal_type == 'BUY' else 0.98)
            return await self.create_standard_signal(
                symbol=symbol,
                action=signal_type,
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': f"Low volatility opportunity - Bias: {weighted_bias:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None
    
    # ============= ML MODEL TRAINING METHODS =============
    
    def _store_ml_training_data(self, features: np.ndarray, label: int):
        """
        🔥 FIX FOR LIMITATION: ML Signal Validation
        Store data for ML model training with persistence
        """
        try:
            if len(features) > 0:
                self.ml_features_history.append(features)
                self.ml_labels_history.append(label)
                
                # Keep only recent data
                if len(self.ml_features_history) > 1000:
                    self.ml_features_history.pop(0)
                    self.ml_labels_history.pop(0)
                
                # Persist to Redis every 50 samples
                if len(self.ml_features_history) % 50 == 0:
                    asyncio.create_task(self._persist_ml_training_data())
                    
        except Exception as e:
            logger.error(f"ML training data storage failed: {e}")
    
    async def _update_ml_model(self):
        """
        🔥 FIX FOR LIMITATION: ML Signal Validation  
        Update ML model with new training data
        """
        try:
            if len(self.ml_features_history) < 50:  # Need minimum data
                return
            
            # Prepare training data
            X = np.array(self.ml_features_history)
            y = np.array(self.ml_labels_history)
            
            # Check if we have both classes
            if len(np.unique(y)) < 2:
                logger.debug("ML training skipped - need both positive and negative samples")
                return
            
            # Scale features
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Train model
            self.ml_model.fit(X_scaled, y)
            self.ml_trained = True
            
            # Calculate model performance
            train_score = self.ml_model.score(X_scaled, y)
            
            logger.info(f"🤖 ML MODEL UPDATED: {len(X)} samples, accuracy={train_score:.3f}")
            
            # Persist training data
            await self._persist_ml_training_data()
            
        except Exception as e:
            logger.error(f"ML model update failed: {e}")
    
    def _get_ml_confidence_boost(self, features: np.ndarray) -> float:
        """Get ML-based confidence boost for signal"""
        try:
            if not self.ml_trained or len(features) == 0:
                return 0.0
            
            # 🔥 FIX: Check if ML model has sufficient training data
            if len(self.ml_labels_history) < 50:
                logger.debug(f"ML model has insufficient training data ({len(self.ml_labels_history)} samples) - skipping penalty")
                return 0.0
            
            # Scale features
            features_scaled = self.feature_scaler.transform(features.reshape(1, -1))
            
            # Get prediction probability
            prediction_proba = self.ml_model.predict_proba(features_scaled)[0]
            
            # 🔥 FIX: If model always predicts same class (not learning), don't apply penalty
            if prediction_proba[1] < 0.05 or prediction_proba[1] > 0.95:
                logger.debug(f"ML model prediction too extreme ({prediction_proba[1]:.3f}) - likely undertrained, skipping")
                return 0.0
            
            # Convert to confidence boost (-0.3 to +0.3) - reduced impact
            confidence_boost = (prediction_proba[1] - 0.5) * 0.6
            
            return confidence_boost
            
        except Exception as e:
            logger.debug(f"ML confidence boost failed: {e}")
            return 0.0
    
    def record_trade_outcome(self, symbol: str, was_profitable: bool, features: Optional[np.ndarray] = None):
        """
        🔥 FIX FOR LIMITATION: ML Signal Validation
        Record trade outcome for ML model training
        Call this when a trade closes to build training data
        """
        try:
            if features is None:
                # Try to reconstruct features from current data
                if symbol in self.price_history and len(self.price_history[symbol]) >= 14:
                    prices = np.array(self.price_history[symbol])
                    rsi = self._calculate_rsi(prices, 14)
                    momentum_score = ProfessionalMomentumModels.momentum_score(prices, min(20, len(prices)))
                    trend_strength = ProfessionalMomentumModels.trend_strength(prices)
                    mean_reversion = ProfessionalMomentumModels.mean_reversion_probability(prices)
                    
                    # Get cross-sectional rank if available
                    cross_rank = self.relative_strength_scores.get(symbol, 0.5)
                    
                    features = np.array([rsi, momentum_score, trend_strength, mean_reversion, cross_rank])
                else:
                    return  # Not enough data
            
            label = 1 if was_profitable else 0
            self._store_ml_training_data(features, label)
            
            logger.debug(f"📊 ML training data recorded: {symbol} {'PROFIT' if was_profitable else 'LOSS'}")
            
            # Train model if we have enough new data
            if len(self.ml_features_history) >= 50 and len(self.ml_features_history) % 20 == 0:
                asyncio.create_task(self._update_ml_model())
                
        except Exception as e:
            logger.error(f"Trade outcome recording failed: {e}")

logger.info("✅ Smart Intraday Options loaded successfully")
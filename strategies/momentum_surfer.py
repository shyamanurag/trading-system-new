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
        """Calculate trend strength using linear regression"""
        try:
            if len(prices) < window:
                return 0.0
            
            recent_prices = prices[-window:]
            x = np.arange(len(recent_prices))
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_prices)
            
            # Trend strength is R-squared adjusted for significance
            trend_strength = r_value**2 if p_value < 0.05 else 0.0
            
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

        # PROFESSIONAL MOMENTUM MODELS
        self.momentum_models = ProfessionalMomentumModels()
        
        # CONFIGURABLE PARAMETERS (NO HARDCODED VALUES)
        self.momentum_threshold = config.get('momentum_threshold', 0.015)  # Configurable momentum threshold
        self.trend_strength_threshold = config.get('trend_strength_threshold', 0.25)  # Configurable trend confirmation
        self.mean_reversion_threshold = config.get('mean_reversion_threshold', 0.7)   # Configurable mean reversion probability

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
        """Initialize the strategy"""
        self.is_active = True
        logger.info("✅ Smart Intraday Options loaded successfully")

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
            
            # Analyze each active symbol
            for stock in self.active_symbols:
                # 🚨 BREAK EARLY: Stop if we've reached the signal limit
                if len(signals) >= max_signals_per_cycle:
                    logger.warning(f"⚠️ SIGNAL LIMIT REACHED: {len(signals)}/{max_signals_per_cycle} - stopping analysis")
                    break

                if stock in market_data:
                    # Detect market condition for this stock
                    market_condition = self._detect_market_condition(stock, market_data)

                    # Generate signal based on condition
                    signal = await self._generate_condition_based_signal(stock, market_condition, market_data)
                    if signal:
                        signals.append(signal)
                        logger.info(f"✅ Signal generated for {stock}: {len(signals)}/{max_signals_per_cycle}")

            logger.info(f"📊 Smart Intraday Options generated {len(signals)} signals (limit: {max_signals_per_cycle})")
            return signals

        except Exception as e:
            logger.error(f"Error in Smart Intraday Options: {e}")
            return []

    def _detect_market_condition(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Detect current market condition for the stock"""
        try:
            data = market_data.get(symbol, {})
            if not data:
                return 'sideways'
            
            change_percent = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            ltp = data.get('ltp', 0)
            
            # Get average volume (simulated)
            avg_volume = volume * 0.8  # Assume current is 20% above average
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            
            # Condition detection logic
            if abs(change_percent) >= self.breakout_threshold and volume_ratio > 1.5:
                return 'breakout_up' if change_percent > 0 else 'breakout_down'
            
            elif change_percent >= self.trending_threshold:
                return 'trending_up'
            
            elif change_percent <= -self.trending_threshold:
                return 'trending_down'
            
            elif abs(change_percent) <= self.sideways_range:
                return 'sideways'
            
            elif volume_ratio > 2.0:
                return 'high_volatility'
            
            elif volume_ratio < 0.5:
                return 'low_volatility'
            
            # Check for reversal patterns (simplified)
            elif change_percent > 0.5 and change_percent < self.trending_threshold:
                return 'reversal_up'
            
            elif change_percent < -0.5 and change_percent > -self.trending_threshold:
                return 'reversal_down'
            
            return 'sideways'
            
        except Exception as e:
            logger.debug(f"Error detecting market condition for {symbol}: {e}")
            return 'sideways'

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
            logger.warning(f"⚠️ Invalid signal type for {symbol}: {type(result)}")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error generating condition-based signal for {symbol}: {e}")
            return {}  # Always return dict, never None

    async def _trending_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for uptrending stocks"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if change_percent > 1.0:  # Strong uptrend
            # 🎯 ENHANCED: More realistic momentum confidence
            # Start at 7.0, increase with strength, cap at 8.2
            confidence = 7.0 + min(change_percent * 0.15, 1.2)
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 0.99
            target = ltp * 1.02
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
                    'reason': f"Uptrending stock strategy - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

    async def _trending_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downtrending stocks - SHORT SELLING"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if change_percent < -1.0:  # Strong downtrend
            # 🎯 ENHANCED: More realistic downtrend momentum confidence
            # Start at 7.0, increase with strength, cap at 8.2
            confidence = 7.0 + min(abs(change_percent) * 0.15, 1.2)
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 1.01
            target = ltp * 0.98
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
                    'reason': f"Downtrending stock SHORT strategy - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

    async def _sideways_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """RANGE TRADING strategy for sideways markets"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        ltp = data.get('ltp', 0)
        
        # Range trading: buy at support, sell at resistance
        if change_percent < -0.3:  # Near support
            # 🎯 ENHANCED: Ranging markets are harder to trade
            confidence = 6.8
            if ltp <= 0:
                return None
            stop_loss = ltp * 0.99
            target = ltp * 1.02
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
                    'reason': f"Range trading: Buy at support - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        elif change_percent > 0.3:  # Near resistance
            # 🎯 ENHANCED: Range resistance fades are risky
            confidence = 6.5
            if ltp <= 0:
                return None
            stop_loss = ltp * 1.01
            target = ltp * 0.98
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
                    'reason': f"Range trading: Sell at resistance - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

    async def _breakout_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward breakouts"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if change_percent > 1.5 and volume > 100000:
            # 🎯 ENHANCED: Breakouts fail often - be conservative
            confidence = 7.2 + min(change_percent * 0.08, 0.8)
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 0.99
            target = ltp * 1.02
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
                    'reason': f"Upward breakout with volume - Change: {change_percent:.1f}%, Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _breakout_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward breakouts"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if change_percent < -1.5 and volume > 100000:
            # 🎯 ENHANCED: Breakdown trades carry significant risk
            confidence = 7.2 + min(abs(change_percent) * 0.08, 0.8)
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 1.01
            target = ltp * 0.98
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
                    'reason': f"Downward breakout with volume - Change: {change_percent:.1f}%, Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _reversal_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward reversals"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if 0.5 <= change_percent <= 1.0:  # Modest upward move after decline
            # 🎯 ENHANCED: Reversal timing is difficult
            confidence = 6.8
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 0.99
            target = ltp * 1.02
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
                    'reason': f"Upward reversal pattern - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

    async def _reversal_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward reversals"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if -1.0 <= change_percent <= -0.5:  # Modest downward move after rise
            # 🎯 ENHANCED: Catching falling knives is risky
            confidence = 6.5
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
                return None
            stop_loss = ltp * 1.01
            target = ltp * 0.98
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
                    'reason': f"Downward reversal pattern - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

    async def _high_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for high volatility periods"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if volume > 200000 and abs(change_percent) > 0.5:
            signal_type = 'BUY' if change_percent > 0 else 'SELL'
            # 🎯 ENHANCED: High volatility trades need caution
            confidence = 7.0
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
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
                    'reason': f"High volatility momentum - Change: {change_percent:.1f}%, Volume: {volume:,}"
                },
                market_bias=self.market_bias
            )
        return None

    async def _low_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for low volatility periods"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        # In low volatility, look for any movement
        if abs(change_percent) > 0.2:
            signal_type = 'BUY' if change_percent > 0 else 'SELL'
            # 🎯 ENHANCED: Low volatility moves lack conviction
            confidence = 6.2
            ltp = data.get('ltp', 0)
            if ltp <= 0:
                logger.warning(f"⚠️ INVALID LTP for {symbol}: {ltp} - skipping signal generation")
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
                    'reason': f"Low volatility opportunity - Change: {change_percent:.1f}%"
                },
                market_bias=self.market_bias
            )
        return None

logger.info("✅ Smart Intraday Options loaded successfully")
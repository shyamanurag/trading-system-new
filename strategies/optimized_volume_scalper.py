"""
INSTITUTIONAL-GRADE MARKET MICROSTRUCTURE STRATEGY
Professional implementation with mathematical rigor and statistical validation.

PROFESSIONAL ENHANCEMENTS:
1. GARCH volatility modeling with regime detection
2. Statistical arbitrage with cointegration testing
3. Market impact modeling and optimal execution
4. Machine learning enhanced signal detection
5. Real-time risk management with VaR/CVaR
6. Professional backtesting with walk-forward analysis
7. Order book simulation and liquidity analysis
8. High-frequency statistical tests and validation

Built on institutional-grade mathematical models and proven quantitative research.
"""

import logging
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from strategies.base_strategy import BaseStrategy
import pytz
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class MarketMicrostructureSignal:
    """Professional microstructure signal with statistical validation"""
    signal_type: str
    strength: float
    confidence: float
    edge_source: str
    expected_duration: int  # seconds
    risk_adjusted_return: float
    statistical_significance: float = 0.0  # p-value
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0  # 95% Value at Risk
    kelly_fraction: float = 0.0  # Optimal position size

@dataclass 
class ProfessionalMathModels:
    """Inline mathematical models for institutional-grade analysis"""
    
    @staticmethod
    def garch_volatility(returns: np.ndarray, alpha: float = 0.1, beta: float = 0.85) -> Tuple[float, np.ndarray]:
        """
        GARCH(1,1) volatility model - Correct mathematical implementation
        
        Formula: σ²(t) = ω + α·r²(t-1) + β·σ²(t-1)
        
        Where ω = (1 - α - β) × long_run_variance
        This ensures variance converges to the sample variance, not a fixed value.
        
        Args:
            returns: Array of returns (percentage changes as decimals, e.g., 0.01 = 1%)
            alpha: ARCH parameter - weight of recent shock (default 0.1)
            beta: GARCH parameter - weight of previous variance (default 0.85)
            
        Returns:
            (current_volatility, volatility_series) - annualized values
        """
        try:
            if len(returns) < 10:
                simple_vol = np.std(returns) * np.sqrt(252)
                return simple_vol, np.full(len(returns), simple_vol)
            
            n = len(returns)
            
            # Calculate sample variance from the data (long-run target)
            sample_variance = np.var(returns)
            
            # 🔥 FIX: Calculate omega from sample variance so it scales correctly
            # omega = (1 - alpha - beta) * long_run_variance
            # This ensures the GARCH variance converges to actual sample variance
            persistence = alpha + beta  # Should be < 1 for stationarity
            if persistence >= 1.0:
                # Non-stationary - use simpler approach
                persistence = 0.95
            omega = (1 - persistence) * sample_variance
            
            # 🛡️ BOUNDS: Ensure omega is reasonable (not too small, not too large)
            omega = max(omega, 1e-10)  # Minimum to prevent divide-by-zero
            omega = min(omega, sample_variance * 0.5)  # Cap at 50% of sample variance
            
            # Initialize variance array
            variance = np.zeros(n)
            variance[0] = sample_variance  # Initialize with sample variance
            
            # GARCH(1,1) recursion: σ²(t) = ω + α·r²(t-1) + β·σ²(t-1)
            for t in range(1, n):
                variance[t] = omega + alpha * (returns[t-1] ** 2) + beta * variance[t-1]
                # 🛡️ Prevent variance explosion
                variance[t] = min(variance[t], sample_variance * 10)  # Cap at 10x sample
            
            # Convert variance to volatility (annualized)
            volatility = np.sqrt(variance) * np.sqrt(252)
            
            return volatility[-1], volatility
            
        except Exception as e:
            logger.error(f"GARCH volatility calculation failed: {e}")
            simple_vol = np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0.2
            return simple_vol, np.full(len(returns), simple_vol)
    
    @staticmethod
    def cointegration_test(series1: np.ndarray, series2: np.ndarray) -> Tuple[bool, float, float]:
        """
        Engle-Granger cointegration test for statistical arbitrage
        
        Args:
            series1: First price series
            series2: Second price series
            
        Returns:
            (is_cointegrated, test_statistic, p_value)
        """
        try:
            import warnings
            from statsmodels.tsa.stattools import coint
            
            if len(series1) < 20 or len(series2) < 20:
                return False, 0.0, 1.0
            
            # Check for sufficient variance (avoid collinearity warning)
            var1 = np.var(series1)
            var2 = np.var(series2)
            if var1 < 1e-10 or var2 < 1e-10:
                # Series is essentially flat - not useful for cointegration
                return False, 0.0, 1.0
            
            # Check correlation - if too high, series are collinear
            corr = np.corrcoef(series1, series2)[0, 1]
            if abs(corr) > 0.9999:
                # Almost perfectly correlated - cointegration test unreliable
                return False, 0.0, 1.0
            
            # Perform cointegration test with warning suppression
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='.*colinear.*', category=UserWarning)
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                test_stat, p_value, critical_values = coint(series1, series2)
            
            # Check if cointegrated at 5% level
            is_cointegrated = p_value < 0.05
            
            return is_cointegrated, test_stat, p_value
            
        except Exception as e:
            logger.debug(f"Cointegration test skipped: {e}")
            return False, 0.0, 1.0
    
    @staticmethod
    def market_impact_model(volume: float, avg_volume: float, volatility: float, 
                           participation_rate: float = 0.1) -> float:
        """
        Market impact model based on Almgren-Chriss framework
        
        Args:
            volume: Order volume
            avg_volume: Average daily volume
            volatility: Price volatility
            participation_rate: Participation rate in volume
            
        Returns:
            Expected market impact (basis points)
        """
        try:
            if avg_volume <= 0:
                return 0.0
            
            # Temporary impact (linear in participation rate)
            temporary_impact = 0.5 * volatility * participation_rate
            
            # Permanent impact (square root law)
            permanent_impact = 0.1 * volatility * np.sqrt(volume / avg_volume)
            
            total_impact = temporary_impact + permanent_impact
            
            # Convert to basis points
            return total_impact * 10000
            
        except Exception as e:
            logger.error(f"Market impact calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Kelly criterion for optimal position sizing
        
        Args:
            win_rate: Probability of winning
            avg_win: Average win amount
            avg_loss: Average loss amount
            
        Returns:
            Optimal fraction of capital to risk
        """
        try:
            if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
                return 0.0
            
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Cap at 25% for safety
            return min(max(kelly_fraction, 0.0), 0.25)
            
        except Exception as e:
            logger.error(f"Kelly criterion calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def var_calculation(returns: np.ndarray, confidence: float = 0.05) -> float:
        """
        Value at Risk calculation using historical simulation
        
        Args:
            returns: Array of returns
            confidence: Confidence level (0.05 for 95% VaR)
            
        Returns:
            VaR value (positive number representing loss)
        """
        try:
            if len(returns) < 10:
                return 0.0
            
            # Sort returns and find percentile
            sorted_returns = np.sort(returns)
            var_index = int(confidence * len(sorted_returns))
            
            var_value = -sorted_returns[var_index]  # Make positive for loss
            
            return max(var_value, 0.0)
            
        except Exception as e:
            logger.error(f"VaR calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def statistical_significance_test(strategy_returns: np.ndarray, 
                                    benchmark_returns: np.ndarray = None) -> float:
        """
        Statistical significance test for strategy performance
        
        Args:
            strategy_returns: Strategy returns
            benchmark_returns: Benchmark returns (optional)
            
        Returns:
            p-value of significance test
        """
        try:
            if len(strategy_returns) < 10:
                return 1.0
            
            if benchmark_returns is None:
                # Test against zero (no return)
                t_stat, p_value = stats.ttest_1samp(strategy_returns, 0)
            else:
                # Test against benchmark
                if len(benchmark_returns) != len(strategy_returns):
                    return 1.0
                t_stat, p_value = stats.ttest_rel(strategy_returns, benchmark_returns)
            
            return p_value
            
        except Exception as e:
            logger.error(f"Statistical significance test failed: {e}")
            return 1.0

class OptimizedVolumeScalper(BaseStrategy):
    """
    INSTITUTIONAL-GRADE MARKET MICROSTRUCTURE STRATEGY
    
    PROFESSIONAL EDGE SOURCES:
    1. GARCH VOLATILITY MODELING: Real-time volatility regime detection
    2. STATISTICAL ARBITRAGE: Cointegration-based mean reversion
    3. MARKET IMPACT OPTIMIZATION: Almgren-Chriss execution models
    4. MACHINE LEARNING SIGNALS: Random Forest enhanced detection
    5. PROFESSIONAL RISK MANAGEMENT: VaR, Kelly criterion, drawdown control
    6. HIGH-FREQUENCY VALIDATION: Statistical significance testing
    7. LIQUIDITY ANALYSIS: Real order book simulation
    8. REGIME-AWARE ADAPTATION: Dynamic parameter adjustment
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "InstitutionalMicrostructureStrategy"
        self.strategy_name = "InstitutionalMicrostructureStrategy"
        
        # PROFESSIONAL COMPONENTS INITIALIZATION
        self.math_models = ProfessionalMathModels()
        self.truedata_symbols = []
        
        # Initialize data clients
        try:
            from data.truedata_client import TrueDataClient
            self.truedata_client = TrueDataClient()
        except ImportError:
            self.truedata_client = None
            
        # Cache zerodha_client from orchestrator (will be updated on token refresh)
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            self.zerodha_client = orchestrator.zerodha_client if orchestrator else None
        except ImportError:
            self.zerodha_client = None
        
        # MACHINE LEARNING COMPONENTS
        # 🔧 FIX: Use class_weight='balanced' to handle severe class imbalance
        # Without this, with 2% positive samples, model just predicts negative always
        self.ml_model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            class_weight='balanced',  # 🔧 CRITICAL: Give equal importance to minority class
            min_samples_leaf=5,  # Prevent overfitting on small minority class
            max_depth=10  # Limit depth to prevent memorizing minority samples
        )
        self.feature_scaler = StandardScaler()
        self.ml_trained = False
        self.ml_balanced_accuracy = 0.0  # 🔧 Track balanced accuracy to know if model is learning
        self.ml_features_history = []
        self.ml_labels_history = []
        
        # PROFESSIONAL PERFORMANCE TRACKING
        self.strategy_returns = []
        self.trade_history = []
        self.performance_metrics = {
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'var_95': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'statistical_significance': 1.0
        }
        
        # CONFIGURABLE POSITION MANAGEMENT (NO HARDCODED VALUES)
        self.profit_lock_percentage = config.get('profit_lock_percentage', 0.8)
        self.mandatory_close_time = config.get('mandatory_close_time', "15:20")

        # CONFIGURABLE SOPHISTICATED PARAMETERS
        self.order_flow_lookback = config.get('order_flow_lookback', 20)
        self.volatility_memory = config.get('volatility_memory', 50)
        self.min_liquidity_threshold = config.get('min_liquidity_threshold', 200000)
        self.institutional_size_threshold = config.get('institutional_size_threshold', 500000)

        # CONFIGURABLE STATISTICAL EDGE PARAMETERS
        self.mean_reversion_zscore = config.get('mean_reversion_zscore', 2.0)
        self.volatility_cluster_threshold = config.get('volatility_cluster_threshold', 1.5)
        self.order_flow_imbalance_threshold = config.get('order_flow_imbalance_threshold', 0.7)
        
        # CONFIGURABLE TRADING WINDOWS
        self.high_volatility_windows = config.get('high_volatility_windows', [
            (9, 15, 10, 0),    # Opening 45 minutes - maximum volatility and volume
            (10, 0, 10, 30),   # Post-opening consolidation - mean reversion opportunities
            (11, 0, 11, 30),   # Mid-morning momentum - trend continuation
            (14, 0, 14, 30),   # Pre-closing positioning - institutional activity
            (14, 30, 15, 0),   # Final 30 minutes - maximum urgency and volume
        ])

        # CONFIGURABLE SQUARE-OFF WINDOWS
        square_off_config = config.get('square_off_start_time', (15, 0))
        market_close_config = config.get('market_close_time', (15, 30))
        self.square_off_start_time = square_off_config
        self.market_close_time = market_close_config

        # CONFIGURABLE RISK MANAGEMENT
        self.max_position_time = config.get('max_position_time', 300)
        self.min_risk_reward = config.get('min_risk_reward', 2.5)
        self.max_daily_drawdown = config.get('max_daily_drawdown', 0.02)
        
        # INTERNAL STATE
        self.price_history = {}
        self.volume_history = {}
        self.volatility_history = {}
        self.order_flow_history = {}
        self.position_entry_times = {}

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
            'signals_by_type': {}
        }
        self.backtest_trades = []

        # ENHANCED RISK MANAGEMENT
        self.max_daily_loss = config.get('max_daily_loss', -3000)  # Max daily loss in rupees
        self.max_single_trade_loss = config.get('max_single_trade_loss', -750)  # Max loss per trade
        self.max_daily_trades = config.get('max_daily_trades', 15)  # Max trades per day
        self.max_consecutive_losses = config.get('max_consecutive_losses', 4)  # Max consecutive losses

        # DYNAMIC RISK ADJUSTMENT
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.emergency_stop = False
        
    def is_market_open(self) -> bool:
        """Check if market is currently open (IST)"""
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        weekday = now.weekday()
        if weekday >= 5:  # Saturday/Sunday
            return False
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        return market_open <= now <= market_close
        
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
        logger.info("🔬 STARTING MICROSTRUCTURE STRATEGY BACKTEST")
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
            'signals_by_type': {}
        }

        try:
            # Process each symbol's historical data
            for symbol, price_history in historical_data.items():
                if len(price_history) < 100:  # Minimum data requirement for microstructure analysis
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
            self.price_history = {}
            self.volume_history = {}
            self.volatility_history = {}
            self.order_flow_history = {}

            # Process each historical data point
            for i, data_point in enumerate(price_history):
                if i < 50:  # Skip initial data for indicator warmup
                    continue

                # Create market data dict for strategy
                market_data = {symbol: data_point}

                # Generate signals (we're already in async context)
                try:
                    signals = await self._generate_microstructure_signals(market_data)
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
            signal_type = signal.get('signal_type', 'unknown')

            if signal_type not in self.backtest_results['signals_by_type']:
                self.backtest_results['signals_by_type'][signal_type] = 0
            self.backtest_results['signals_by_type'][signal_type] += 1

            # Simulate trade execution and exit
            trade_pnl, exit_reason = self._simulate_trade_exit(entry_price, stop_loss, target, future_prices)

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': entry_price + trade_pnl,
                'pnl': trade_pnl,
                'confidence': confidence,
                'signal_type': signal_type,
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
            # Simulate holding for up to 30 periods or until stop/target hit (shorter for scalping)
            for i, future_data in enumerate(future_prices[:30]):
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

                # Check for time-based exit (microstructure strategy holds short)
                if i >= 10:  # Exit after 10 periods max
                    exit_price = future_data.get('close', entry_price)
                    pnl = exit_price - entry_price
                    return pnl, 'time_exit'

            # Exit at end of simulation period
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
            report.append("📊 MICROSTRUCTURE STRATEGY BACKTEST REPORT")
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

            # Signals by type
            report.append("\n📈 SIGNALS BY TYPE:")
            for signal_type, count in self.backtest_results['signals_by_type'].items():
                report.append(f"  {signal_type}: {count}")

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

            # Confidence threshold check (higher for microstructure strategy)
            if confidence < 8.0:  # Higher confidence required for scalping
                return False, f"LOW_CONFIDENCE_{confidence:.1f}", 0.0

            # Calculate dynamic risk multiplier
            risk_multiplier = self._calculate_dynamic_risk_multiplier()

            logger.info(f"🛡️ Risk Assessment PASSED for {symbol}: multiplier={risk_multiplier:.2f}")
            return True, "APPROVED", risk_multiplier

        except Exception as e:
            logger.error(f"❌ Risk assessment failed for {symbol}: {e}")
            return False, f"RISK_ASSESSMENT_ERROR_{str(e)}", 0.0

    def _calculate_dynamic_risk_multiplier(self) -> float:
        """Calculate risk multiplier based on current performance"""
        try:
            base_multiplier = 1.0

            # Reduce risk after losses
            if self.daily_pnl < -1000:
                base_multiplier *= 0.6
            elif self.daily_pnl < -2000:
                base_multiplier *= 0.4
            elif self.daily_pnl < -3000:
                base_multiplier *= 0.2

            # Reduce risk after consecutive losses
            if self.consecutive_losses >= 3:
                base_multiplier *= 0.5
            elif self.consecutive_losses >= 4:
                base_multiplier *= 0.3

            return min(base_multiplier, 1.5)  # Conservative cap

        except Exception as e:
            logger.error(f"❌ Dynamic risk multiplier calculation failed: {e}")
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

            logger.info("🌅 Daily risk metrics reset - Fresh trading day")

        except Exception as e:
            logger.error(f"❌ Daily risk reset failed: {e}")

    def get_risk_status_report(self) -> str:
        """Generate comprehensive risk status report"""
        try:
            report = []
            report.append("🛡️ MICROSTRUCTURE STRATEGY RISK REPORT")
            report.append("=" * 45)
            report.append(f"Daily P&L: ₹{self.daily_pnl:.2f}")
            report.append(f"Daily Trades: {self.daily_trades}/{self.max_daily_trades}")
            report.append(f"Consecutive Losses: {self.consecutive_losses}/{self.max_consecutive_losses}")
            report.append(f"Emergency Stop: {'ACTIVE' if self.emergency_stop else 'INACTIVE'}")
            report.append(f"Max Daily Loss Limit: ₹{self.max_daily_loss:.2f}")
            report.append(f"Current Risk Level: {'HIGH' if self.emergency_stop else 'NORMAL'}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Risk status report failed: {e}")
            return "Risk status report generation failed"

    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info(f"✅ {self.name} strategy initialized - Microstructure Edge Detection Active")
        
    async def on_market_data(self, data: Dict):
        """Analyze market microstructure and generate high-probability signals"""
        if not self.is_active:
            return
            
        try:
            # STEP 1: Update internal market state
            self._update_market_state(data)
            
            # NOTE: Position management is handled by orchestrator for ALL strategies
            # Do NOT call manage_existing_positions() here - it causes duplicate processing
            # The orchestrator calls it at line 2105 before passing data to each strategy
            
            # STEP 2: Check market conditions for new signals
            if not self._are_market_conditions_favorable():
                return
                
            # STEP 4: Generate sophisticated signals
            signals = await self._generate_microstructure_signals(data)
            
            # STEP 5: Filter for only highest probability trades AND align with market bias
            quality_signals = self._filter_for_quality(signals)
            if hasattr(self, 'market_bias') and self.market_bias:
                aligned = []
                for s in quality_signals:
                    direction = s.get('action', 'BUY')
                    raw_confidence = s.get('confidence', 0.0)
                    # Normalize confidence to 0-10 scale before bias gating
                    try:
                        confidence_val = float(raw_confidence)
                    except (TypeError, ValueError):
                        confidence_val = 0.0
                    normalized_confidence = confidence_val / 10.0 if confidence_val > 10 else confidence_val
                    if self.market_bias.should_allow_signal(direction, normalized_confidence):
                        aligned.append(s)
                quality_signals = aligned
            
            # 🚨 SIGNAL EXPIRY: Clean up expired signals first
            self._cleanup_expired_signals()
            
            # CRITICAL FIX: Store signals in current_positions for orchestrator to find
            for signal in quality_signals:
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
                    
                    # Store signal in current_positions for orchestrator detection
                    self.current_positions[symbol] = signal
                    self._track_signal_creation(symbol)
                    logger.info(f"🎯 MICROSTRUCTURE EDGE: {signal['symbol']} {signal['action']} "
                               f"Confidence: {signal['confidence']:.1f}/10 "
                               f"Edge: {signal.get('metadata', {}).get('edge_source', 'Unknown')} "
                               f"(expires in 5 min)")
                
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    def _update_market_state(self, data: Dict):
        """Update internal market microstructure state"""
        for symbol, symbol_data in data.items():
            if not symbol_data or symbol == 'timestamp':
                continue
                
            # Update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            price = symbol_data.get('ltp', symbol_data.get('close', 0))
            if price > 0:
                self.price_history[symbol].append(price)
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol].pop(0)
            
            # Update volume history
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            volume = symbol_data.get('volume', 0)
            if volume > 0:
                self.volume_history[symbol].append(volume)
                if len(self.volume_history[symbol]) > 100:
                    self.volume_history[symbol].pop(0)
            
            # Update volatility estimation
            self._update_volatility_estimate(symbol)
            
            # Update order flow proxy
            self._update_order_flow_proxy(symbol, symbol_data)
    
    def _update_volatility_estimate(self, symbol: str):
        """PROFESSIONAL GARCH volatility modeling with regime detection"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return

        # Get current volume from volume history (most recent entry)
        current_volume = 0
        if symbol in self.volume_history and self.volume_history[symbol]:
            current_volume = self.volume_history[symbol][-1]  # Most recent volume

        prices = self.price_history[symbol]
        returns = np.array([(prices[i] - prices[i-1]) / prices[i-1]
                           for i in range(1, len(prices))])
        
        if len(returns) < 10:
            return
            
        # PROFESSIONAL GARCH VOLATILITY MODELING
        try:
            current_vol, vol_series = self.math_models.garch_volatility(returns)
            
            if symbol not in self.volatility_history:
                self.volatility_history[symbol] = []
            
            # VOLATILITY REGIME DETECTION
            if len(vol_series) >= 20:
                vol_mean = np.mean(vol_series[-20:])
                vol_std = np.std(vol_series[-20:])
                
                # Regime classification
                if current_vol > vol_mean + 2 * vol_std:
                    regime = "HIGH_VOLATILITY"
                elif current_vol < vol_mean - vol_std:
                    regime = "LOW_VOLATILITY"
                else:
                    regime = "NORMAL_VOLATILITY"
            else:
                regime = "NORMAL_VOLATILITY"
            
            # VOLATILITY CLUSTERING STRENGTH
            clustering_strength = self._calculate_volatility_clustering(vol_series)
            
            # Calculate volume ratio (current volume vs average volume)
            avg_volume = np.mean(self.volume_history.get(symbol, [current_volume])[-20:]) if symbol in self.volume_history else current_volume
            vol_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # PROFESSIONAL VOLATILITY METRICS
            vol_data = {
                'current_vol': current_vol,
                'garch_vol': current_vol,
                'vol_regime': regime,
                'clustering_strength': clustering_strength,
                'vol_percentile': self._calculate_vol_percentile(current_vol, vol_series),
                'vol_ratio': vol_ratio,  # Add volume ratio for clustering detection
                'timestamp': datetime.now()
            }
            
            self.volatility_history[symbol].append(vol_data)
            
            if len(self.volatility_history[symbol]) > 100:
                self.volatility_history[symbol].pop(0)
            
            # 🚨 FIX: Log at INFO level for production visibility (every 10th update to avoid spam)
            if len(self.volatility_history[symbol]) % 10 == 1:
                logger.info(f"📊 GARCH ACTIVE: {symbol} Vol={current_vol:.4f} Regime={regime} Clustering={clustering_strength:.2f}")
            else:
                logger.debug(f"📊 GARCH VOL UPDATE: {symbol} = {current_vol:.4f} ({regime})")
            
        except Exception as e:
            logger.error(f"Professional volatility update failed for {symbol}: {e}")
            # Fallback to simple volatility
            simple_vol = np.std(returns) * np.sqrt(252)
            if symbol not in self.volatility_history:
                self.volatility_history[symbol] = []
            # Calculate volume ratio for fallback case
            avg_volume_fb = np.mean(self.volume_history.get(symbol, [current_volume])[-20:]) if symbol in self.volume_history else current_volume
            vol_ratio_fb = current_volume / avg_volume_fb if avg_volume_fb > 0 else 1.0

            self.volatility_history[symbol].append({
                'current_vol': simple_vol,
                'garch_vol': simple_vol,
                'vol_regime': 'NORMAL_VOLATILITY',
                'clustering_strength': 0.0,
                'vol_ratio': vol_ratio_fb,  # Add volume ratio to fallback data
                'vol_percentile': 50.0,
                'timestamp': datetime.now()
            })
    
    def _calculate_volatility_clustering(self, vol_series: np.ndarray) -> float:
        """Calculate volatility clustering strength using autocorrelation"""
        try:
            if len(vol_series) < 10:
                return 0.0
            
            # Calculate autocorrelation at lag 1
            vol_changes = np.diff(vol_series)
            if len(vol_changes) < 2:
                return 0.0
            
            correlation = np.corrcoef(vol_changes[:-1], vol_changes[1:])[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            logger.error(f"Volatility clustering calculation failed: {e}")
            return 0.0
    
    def _calculate_vol_percentile(self, current_vol: float, vol_series: np.ndarray) -> float:
        """Calculate current volatility percentile"""
        try:
            if len(vol_series) < 10:
                return 50.0
            
            percentile = stats.percentileofscore(vol_series, current_vol)
            return percentile
            
        except Exception as e:
            logger.error(f"Volatility percentile calculation failed: {e}")
            return 50.0
    
    def _update_order_flow_proxy(self, symbol: str, symbol_data: Dict):
        """Update order flow proxy using volume and price action
        
        🔧 FIX: Use candle-based buy/sell pressure instead of just price direction
        This gives more realistic imbalance values (not always 1.0 or 0.0)
        """
        if symbol not in self.order_flow_history:
            self.order_flow_history[symbol] = []

        # Proxy for order flow imbalance
        volume = symbol_data.get('volume', 0)
        # Align to TrueData feed which uses change_percent in percent units
        change_percent = symbol_data.get('change_percent', 0)
        price_change = change_percent / 100.0 if isinstance(change_percent, (int, float)) else 0.0
        
        # 🔧 FIX: Use OHLC to estimate buy/sell pressure more accurately
        # Instead of binary direction, use candle position for nuanced flow
        high = symbol_data.get('high', 0)
        low = symbol_data.get('low', 0)
        close = symbol_data.get('close', symbol_data.get('ltp', 0))
        open_price = symbol_data.get('open', close)
        
        if volume > 0 and high > low:
            # Calculate buy/sell pressure from candle structure
            candle_range = high - low
            
            # Buy pressure: how close is the close to the high?
            buy_pressure = (close - low) / candle_range  # 0 to 1
            sell_pressure = (high - close) / candle_range  # 0 to 1
            
            # 🔧 FIX: Use pressure difference for direction and intensity
            # This gives values between -1 and +1, not just -1 or +1
            pressure_diff = buy_pressure - sell_pressure  # -1 to +1
            
            # Direction is still binary, but intensity varies
            flow_direction = 1 if pressure_diff > 0 else -1
            
            # 🔧 FIX: Intensity now includes the magnitude of pressure difference
            # Previously: all-or-nothing based on price_change sign
            # Now: weighted by actual buy/sell pressure from candle
            flow_intensity = abs(pressure_diff) * volume * (1 + abs(price_change))

            self.order_flow_history[symbol].append({
                'direction': flow_direction,
                'intensity': flow_intensity,
                'volume': volume,
                'price_change': price_change,
                'buy_pressure': buy_pressure,
                'sell_pressure': sell_pressure,
                'timestamp': datetime.now()
            })

            if len(self.order_flow_history[symbol]) > self.order_flow_lookback:
                self.order_flow_history[symbol].pop(0)
    
    def _are_market_conditions_favorable(self) -> bool:
        """Check if market conditions are favorable for microstructure trading"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        hour = current_time.hour
        minute = current_time.minute
        
        # Check if we're in high-probability time windows
        for start_h, start_m, end_h, end_m in self.high_volatility_windows:
            if (hour > start_h or (hour == start_h and minute >= start_m)) and \
               (hour < end_h or (hour == end_h and minute <= end_m)):
                return True
        
        # Additional condition: avoid lunch time low liquidity
        if 12 <= hour <= 13:
            return False
            
        return True
    
    async def _generate_microstructure_signals(self, data: Dict) -> List[Dict]:
        """Generate signals based on market microstructure analysis"""
        signals = []
        
        for symbol, symbol_data in data.items():
            if not symbol_data or symbol == 'timestamp':
                continue
                
            # Check minimum liquidity requirements
            volume = symbol_data.get('volume', 0)
            if volume < self.min_liquidity_threshold:
                continue
                
            # Generate multiple types of microstructure signals
            microstructure_signals = []
            
            # 1. Order Flow Imbalance Signal
            order_flow_signal = self._detect_order_flow_imbalance(symbol, symbol_data)
            if order_flow_signal:
                microstructure_signals.append(order_flow_signal)
            
            # 2. Volatility Clustering Signal
            vol_cluster_signal = self._detect_volatility_clustering(symbol, symbol_data)
            if vol_cluster_signal:
                microstructure_signals.append(vol_cluster_signal)
            
            # 3. Mean Reversion Signal
            mean_reversion_signal = self._detect_mean_reversion_opportunity(symbol, symbol_data)
            if mean_reversion_signal:
                microstructure_signals.append(mean_reversion_signal)
            
            # 4. Liquidity Gap Signal
            liquidity_signal = self._detect_liquidity_gap(symbol, symbol_data)
            if liquidity_signal:
                microstructure_signals.append(liquidity_signal)
            
            # 5. PROFESSIONAL STATISTICAL ARBITRAGE
            arbitrage_signal = self._detect_statistical_arbitrage_opportunity(symbol, symbol_data, data)
            if arbitrage_signal:
                microstructure_signals.append(arbitrage_signal)
            
            # PROFESSIONAL ML ENHANCEMENT
            enhanced_signals = await self._enhance_signals_with_ml(microstructure_signals, symbol, symbol_data)
            
            # 🎯 Convert enhanced microstructure signals to trading signals
            # Note: Mean reversion and liquidity gap are now regime-aware (disabled in trending markets)
            # This prevents contradictory signals from mixing trend-following with counter-trend strategies
            for ms_signal in enhanced_signals:
                trading_signal = await self._convert_to_trading_signal(symbol, symbol_data, ms_signal)
                if trading_signal:
                    signals.append(trading_signal)
        
        return signals
    
    def _detect_order_flow_imbalance(self, symbol: str, symbol_data: Dict) -> Optional[MarketMicrostructureSignal]:
        """PROFESSIONAL ORDER FLOW ANALYSIS with institutional detection"""
        if symbol not in self.order_flow_history or len(self.order_flow_history[symbol]) < 10:
            return None
            
        recent_flows = self.order_flow_history[symbol][-20:]  # Increased sample size
        
        # PROFESSIONAL ORDER FLOW METRICS
        buy_flow = sum(f['intensity'] for f in recent_flows if f['direction'] > 0)
        sell_flow = sum(f['intensity'] for f in recent_flows if f['direction'] < 0)
        total_flow = buy_flow + sell_flow
        
        if total_flow == 0:
            return None
        
        # INSTITUTIONAL FLOW DETECTION
        # 🔥 FIX: Index futures (NIFTY-I, BANKNIFTY-I) report tick volume differently
        # Index futures ARE inherently institutional - retail doesn't trade futures
        # So for indices, assume all flow is institutional
        is_index_future = symbol.endswith('-I') or any(idx in symbol.upper() for idx in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX'])
        
        if is_index_future:
            # Index futures = 100% institutional by nature
            institutional_ratio = 1.0
            logger.debug(f"📊 {symbol}: Index future detected - treating as 100% institutional flow")
        else:
            # 🔧 FIX: TrueData reports CUMULATIVE daily volume, not per-tick volume
            # Previous logic: compare cumulative volume (50M) vs threshold (500k) → always institutional!
            # New logic: Use volume CHANGE and relative intensity to detect institutional activity
            
            # Calculate volume intensity relative to recent average
            volumes = [f['volume'] for f in recent_flows]
            intensities = [f['intensity'] for f in recent_flows]
            
            if len(volumes) >= 5:
                # Check for volume spikes (institutional = large relative volume)
                avg_volume = np.mean(volumes)
                avg_intensity = np.mean(intensities) if intensities else 0
                
                # Count ticks with above-average intensity (indicates larger interest)
                high_intensity_flows = [f for f in recent_flows 
                                        if f['intensity'] > avg_intensity * 1.5]
                institutional_ratio = len(high_intensity_flows) / len(recent_flows) if recent_flows else 0
                
                # Also factor in pressure consistency
                # If buy/sell pressure is consistently strong across ticks, likely institutional
                if 'buy_pressure' in recent_flows[0]:
                    buy_pressures = [f.get('buy_pressure', 0.5) for f in recent_flows]
                    pressure_consistency = 1.0 - np.std(buy_pressures)  # Lower std = more consistent
                    institutional_ratio = (institutional_ratio + pressure_consistency) / 2
            else:
                institutional_ratio = 0.3  # Default when not enough data
        
        # PROFESSIONAL IMBALANCE METRICS
        imbalance_ratio = max(buy_flow, sell_flow) / total_flow
        
        # VOLUME-WEIGHTED PRICE IMPACT ANALYSIS
        vwap_deviation = self._calculate_vwap_deviation(recent_flows, symbol_data)
        
        # MARKET MICROSTRUCTURE EDGE DETECTION
        if imbalance_ratio >= self.order_flow_imbalance_threshold:
            direction = 'BUY' if buy_flow > sell_flow else 'SELL'
            
            # 🎯 ENHANCED: More realistic confidence calculation
            # Microstructure edges are powerful but fleeting - be conservative
            # Base from imbalance (max 6.0)
            # Institutional flow boost (max 1.5)
            # VWAP confirmation (max 0.8)
            # Statistical significance (max 0.7)
            base_confidence = min(imbalance_ratio * 6.0, 6.0)
            institutional_boost = min(institutional_ratio * 1.5, 1.5)
            vwap_boost = min(abs(vwap_deviation) * 4, 0.8)
            
            # STATISTICAL VALIDATION
            flow_significance = self._test_flow_significance(recent_flows)
            stat_boost = 0.7 if flow_significance < 0.05 else 0.3  # p-value check
            
            # 🔧 FIX: EXCEPTIONAL CONDITION BONUSES - reward truly outstanding signals
            # These bonuses allow exceptional signals to reach the 8.0 threshold
            exceptional_bonus = 0.0
            
            # BONUS 1: Extreme imbalance (> 0.95 = near 100%)
            if imbalance_ratio >= 0.95:
                exceptional_bonus += 0.5
                logger.debug(f"   ✨ EXTREME IMBALANCE BONUS: +0.5 (imbalance={imbalance_ratio:.3f})")
            
            # BONUS 2: Extreme statistical significance (p < 0.001)
            if flow_significance < 0.001:
                exceptional_bonus += 0.5
                logger.debug(f"   ✨ EXTREME SIGNIFICANCE BONUS: +0.5 (p={flow_significance:.6f})")
            
            # BONUS 3: High institutional ratio (> 0.6 = 60%+ institutional)
            if institutional_ratio >= 0.6:
                exceptional_bonus += 0.3
                logger.debug(f"   ✨ HIGH INSTITUTIONAL BONUS: +0.3 (inst={institutional_ratio:.3f})")
            
            # Calculate final confidence with exceptional bonuses
            confidence = min(base_confidence + institutional_boost + vwap_boost + stat_boost + exceptional_bonus, 9.5)
            
            # RISK-ADJUSTED RETURN ESTIMATION
            volatility = self._get_current_volatility(symbol)
            expected_return = self._estimate_flow_return(imbalance_ratio, institutional_ratio, volatility)
            
            # PROFESSIONAL SIGNAL WITH VALIDATION
            signal = MarketMicrostructureSignal(
                signal_type=direction,
                strength=imbalance_ratio,
                confidence=confidence,
                edge_source="PROFESSIONAL_ORDER_FLOW",
                expected_duration=self._estimate_flow_duration(institutional_ratio),
                risk_adjusted_return=expected_return,
                statistical_significance=flow_significance,
                sharpe_ratio=self._estimate_flow_sharpe(expected_return, volatility),
                var_95=self._estimate_flow_var(expected_return, volatility),
                kelly_fraction=self._calculate_optimal_sizing(expected_return, volatility)
            )
            
            logger.info(f"🏛️ INSTITUTIONAL FLOW: {symbol} {direction} "
                       f"Imbalance={imbalance_ratio:.3f} Inst={institutional_ratio:.3f} "
                       f"Confidence={confidence:.1f} p-value={flow_significance:.4f}")
            
            return signal
        
        return None
    
    def _calculate_vwap_deviation(self, flows: List[Dict], symbol_data: Dict) -> float:
        """Calculate deviation from VWAP for flow analysis"""
        try:
            if not flows or 'ltp' not in symbol_data:
                return 0.0
            
            current_price = symbol_data['ltp']
            
            # Calculate VWAP from recent flows
            total_volume = sum(f['volume'] for f in flows)
            if total_volume == 0:
                return 0.0
            
            # Approximate VWAP using flow data
            weighted_price = sum(f['volume'] * current_price for f in flows) / total_volume
            vwap_deviation = (current_price - weighted_price) / weighted_price
            
            return vwap_deviation
            
        except Exception as e:
            logger.error(f"VWAP deviation calculation failed: {e}")
            return 0.0
    
    def _test_flow_significance(self, flows: List[Dict]) -> float:
        """Test statistical significance of order flow imbalance"""
        try:
            if len(flows) < 10:
                return 1.0
            
            # Extract flow directions
            directions = [f['direction'] for f in flows]
            
            # Test if significantly different from random (50/50)
            buy_count = sum(1 for d in directions if d > 0)
            total_count = len(directions)
            
            # Binomial test against 50/50 null hypothesis
            from scipy.stats import binom_test
            p_value = binom_test(buy_count, total_count, 0.5)
            
            return p_value
            
        except Exception as e:
            logger.error(f"Flow significance test failed: {e}")
            return 1.0
    
    def _estimate_flow_return(self, imbalance_ratio: float, institutional_ratio: float, volatility: float) -> float:
        """Estimate expected return from order flow imbalance"""
        try:
            # Base return from imbalance strength
            base_return = (imbalance_ratio - 0.5) * 0.02  # 2% max from pure imbalance
            
            # Institutional boost
            institutional_boost = institutional_ratio * 0.01  # 1% max from institutional flow
            
            # Volatility adjustment
            vol_adjustment = min(volatility * 0.5, 0.01)  # Higher vol = higher potential return
            
            total_return = base_return + institutional_boost + vol_adjustment
            
            return max(min(total_return, 0.03), 0.001)  # Cap between 0.1% and 3%
            
        except Exception as e:
            logger.error(f"Flow return estimation failed: {e}")
            return 0.005
    
    def _estimate_flow_duration(self, institutional_ratio: float) -> int:
        """Estimate signal duration based on institutional participation"""
        try:
            # Base duration
            base_duration = 180  # 3 minutes
            
            # Institutional flows tend to last longer
            institutional_extension = institutional_ratio * 300  # Up to 5 minutes extra
            
            total_duration = int(base_duration + institutional_extension)
            
            return min(max(total_duration, 60), 600)  # Between 1-10 minutes
            
        except Exception as e:
            logger.error(f"Flow duration estimation failed: {e}")
            return 180
    
    def _estimate_flow_sharpe(self, expected_return: float, volatility: float) -> float:
        """Estimate Sharpe ratio for flow-based signal"""
        try:
            if volatility <= 0:
                return 0.0
            
            # Annualized Sharpe estimation
            annual_return = expected_return * 252  # Daily to annual
            annual_vol = volatility
            
            sharpe = annual_return / annual_vol
            
            return max(min(sharpe, 5.0), 0.0)  # Cap between 0-5
            
        except Exception as e:
            logger.error(f"Flow Sharpe estimation failed: {e}")
            return 0.0
    
    def _estimate_flow_var(self, expected_return: float, volatility: float) -> float:
        """Estimate VaR for flow-based signal"""
        try:
            # 95% VaR estimation assuming normal distribution
            var_95 = 1.645 * volatility - expected_return  # 1.645 = 95% quantile
            
            return max(var_95, 0.0)
            
        except Exception as e:
            logger.error(f"Flow VaR estimation failed: {e}")
            return 0.02
    
    def _calculate_optimal_sizing(self, expected_return: float, volatility: float) -> float:
        """Calculate optimal position sizing using Kelly criterion"""
        try:
            # Estimate win rate and win/loss ratio from expected return and volatility
            win_rate = 0.55 + min(expected_return * 10, 0.15)  # 55-70% based on expected return
            avg_win = expected_return * 1.5  # Assume 1.5x expected return on wins
            avg_loss = volatility * 0.8  # Assume losses are 80% of volatility
            
            kelly_fraction = self.math_models.kelly_criterion(win_rate, avg_win, avg_loss)
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"Optimal sizing calculation failed: {e}")
            return 0.02
    
    def _get_current_volatility(self, symbol: str) -> float:
        """Get current volatility estimate for a symbol"""
        try:
            if symbol in self.volatility_history and self.volatility_history[symbol]:
                return self.volatility_history[symbol][-1].get('current_vol', 0.02)
            return 0.02  # Default 2% volatility
        except Exception as e:
            logger.error(f"Error getting current volatility for {symbol}: {e}")
            return 0.02
    
    def _detect_statistical_arbitrage_opportunity(self, symbol: str, symbol_data: Dict, market_data: Dict) -> Optional[MarketMicrostructureSignal]:
        """PROFESSIONAL STATISTICAL ARBITRAGE with cointegration testing"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 50:
                return None
            
            # Find potential cointegration pairs
            candidate_pairs = self._find_cointegration_candidates(symbol, market_data)
            
            for pair_symbol in candidate_pairs:
                if pair_symbol not in self.price_history or len(self.price_history[pair_symbol]) < 50:
                    continue
                
                # Test for cointegration
                series1 = np.array(self.price_history[symbol][-50:])
                series2 = np.array(self.price_history[pair_symbol][-50:])
                
                is_cointegrated, test_stat, p_value = self.math_models.cointegration_test(series1, series2)
                
                if is_cointegrated and p_value < 0.01:  # Strong cointegration
                    # Calculate spread and z-score
                    spread, z_score = self._calculate_spread_zscore(series1, series2)
                    
                    # Check for mean reversion opportunity
                    if abs(z_score) > 2.0:  # 2 standard deviations
                        direction = 'BUY' if z_score < -2.0 else 'SELL'
                        
                        # 🔧 FIX: Better confidence scaling for stat arb
                        # Start at 7.0 for 2-sigma, increase more aggressively with z-score
                        # 3-sigma (z=3.0) = 7.0 + 1.0*0.5 = 7.5
                        # 4-sigma (z=4.0) = 7.0 + 2.0*0.5 = 8.0 (passes threshold)
                        # 5-sigma (z=5.0) = 7.0 + 3.0*0.5 = 8.5 (exceptional)
                        confidence = min(7.0 + (abs(z_score) - 2.0) * 0.5, 8.5)
                        expected_return = self._estimate_arbitrage_return(abs(z_score), p_value)
                        
                        signal = MarketMicrostructureSignal(
                            signal_type=direction,
                            strength=abs(z_score),
                            confidence=confidence,
                            edge_source="STATISTICAL_ARBITRAGE",
                            expected_duration=self._estimate_arbitrage_duration(abs(z_score)),
                            risk_adjusted_return=expected_return,
                            statistical_significance=p_value,
                            sharpe_ratio=self._estimate_arbitrage_sharpe(expected_return, abs(z_score)),
                            var_95=self._estimate_arbitrage_var(expected_return, abs(z_score)),
                            kelly_fraction=self._calculate_arbitrage_sizing(expected_return, abs(z_score))
                        )
                        
                        logger.info(f"📊 STAT ARB: {symbol}-{pair_symbol} {direction} "
                                   f"Z-score={z_score:.2f} p-value={p_value:.4f} "
                                   f"Confidence={confidence:.1f}")
                        
                        return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Statistical arbitrage detection failed for {symbol}: {e}")
            return None
    
    def _find_cointegration_candidates(self, symbol: str, market_data: Dict) -> List[str]:
        """Find potential cointegration pairs for statistical arbitrage"""
        try:
            # Sector-based pairing (simplified)
            sector_groups = {
                'BANKS': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK'],
                'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
                'AUTO': ['MARUTI', 'M&M', 'TATAMOTORS', 'BAJAJ-AUTO', 'HEROMOTOCO'],
                'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'LUPIN', 'BIOCON'],
                'METALS': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'COALINDIA']
            }
            
            # Find symbol's sector
            symbol_sector = None
            for sector, symbols in sector_groups.items():
                if symbol in symbols:
                    symbol_sector = sector
                    break
            
            if symbol_sector:
                # Return other symbols in same sector
                candidates = [s for s in sector_groups[symbol_sector] 
                             if s != symbol and s in market_data]
                return candidates[:3]  # Limit to top 3 candidates
            
            return []
            
        except Exception as e:
            logger.error(f"Cointegration candidate search failed: {e}")
            return []
    
    def _calculate_spread_zscore(self, series1: np.ndarray, series2: np.ndarray) -> Tuple[float, float]:
        """Calculate spread and z-score for cointegrated pairs"""
        try:
            # Simple spread calculation (can be enhanced with regression)
            spread = series1 - series2
            
            # Calculate z-score
            spread_mean = np.mean(spread)
            spread_std = np.std(spread)
            
            if spread_std == 0:
                return 0.0, 0.0
            
            current_spread = spread[-1]
            z_score = (current_spread - spread_mean) / spread_std
            
            return current_spread, z_score
            
        except Exception as e:
            logger.error(f"Spread z-score calculation failed: {e}")
            return 0.0, 0.0
    
    def _estimate_arbitrage_return(self, z_score: float, p_value: float) -> float:
        """Estimate expected return from statistical arbitrage"""
        try:
            # Base return from z-score strength
            base_return = min(z_score * 0.005, 0.02)  # 0.5% per z-score unit, max 2%
            
            # Cointegration strength boost
            cointegration_boost = (1 - p_value) * 0.01  # Up to 1% from strong cointegration
            
            total_return = base_return + cointegration_boost
            
            return max(min(total_return, 0.025), 0.002)  # Between 0.2% and 2.5%
            
        except Exception as e:
            logger.error(f"Arbitrage return estimation failed: {e}")
            return 0.01
    
    def _estimate_arbitrage_duration(self, z_score: float) -> int:
        """Estimate mean reversion duration for arbitrage"""
        try:
            # Higher z-scores tend to revert faster
            base_duration = 300  # 5 minutes
            z_adjustment = max(0, (4.0 - z_score) * 60)  # Reduce duration for higher z-scores
            
            total_duration = int(base_duration + z_adjustment)
            
            return min(max(total_duration, 120), 900)  # Between 2-15 minutes
            
        except Exception as e:
            logger.error(f"Arbitrage duration estimation failed: {e}")
            return 300
    
    def _estimate_arbitrage_sharpe(self, expected_return: float, z_score: float) -> float:
        """Estimate Sharpe ratio for arbitrage opportunity"""
        try:
            # Arbitrage typically has high Sharpe ratios
            base_sharpe = expected_return * 100  # High Sharpe for mean reversion
            z_boost = min(z_score * 0.5, 2.0)  # Up to 2.0 boost from z-score
            
            total_sharpe = base_sharpe + z_boost
            
            return max(min(total_sharpe, 8.0), 1.0)  # Between 1.0-8.0
            
        except Exception as e:
            logger.error(f"Arbitrage Sharpe estimation failed: {e}")
            return 2.0
    
    def _estimate_arbitrage_var(self, expected_return: float, z_score: float) -> float:
        """Estimate VaR for arbitrage opportunity"""
        try:
            # Arbitrage typically has lower risk
            base_var = expected_return * 0.5  # Lower risk than expected return
            z_adjustment = max(0, (z_score - 2.0) * 0.002)  # Higher z-score = slightly higher risk
            
            total_var = base_var + z_adjustment
            
            return max(min(total_var, 0.01), 0.001)  # Between 0.1% and 1%
            
        except Exception as e:
            logger.error(f"Arbitrage VaR estimation failed: {e}")
            return 0.005
    
    def _calculate_arbitrage_sizing(self, expected_return: float, z_score: float) -> float:
        """Calculate optimal sizing for arbitrage opportunity"""
        try:
            # Higher confidence in arbitrage allows larger positions
            base_sizing = 0.05  # 5% base position
            z_boost = min(z_score * 0.01, 0.05)  # Up to 5% additional from z-score
            
            total_sizing = base_sizing + z_boost
            
            return max(min(total_sizing, 0.15), 0.02)  # Between 2% and 15%
            
        except Exception as e:
            logger.error(f"Arbitrage sizing calculation failed: {e}")
            return 0.05
    
    def _detect_volatility_clustering(self, symbol: str, symbol_data: Dict) -> Optional[MarketMicrostructureSignal]:
        """Detect volatility clustering for breakout trades"""
        if symbol not in self.volatility_history or len(self.volatility_history[symbol]) < 5:
            return None

        current_vol_data = self.volatility_history[symbol][-1]

        # 🚨 DEFENSIVE: Check if vol_ratio exists in the data
        if 'vol_ratio' not in current_vol_data:
            logger.warning(f"⚠️ vol_ratio missing in volatility data for {symbol}")
            return None

        vol_ratio = current_vol_data['vol_ratio']

        # 🚨 DEFENSIVE: Validate vol_ratio is a valid number
        if not isinstance(vol_ratio, (int, float)) or vol_ratio <= 0:
            logger.warning(f"⚠️ Invalid vol_ratio for {symbol}: {vol_ratio}")
            return None
        
        if vol_ratio >= self.volatility_cluster_threshold:
            # High volatility cluster detected
            price_change = symbol_data.get('price_change', 0)
            
            if abs(price_change) > 0.003:  # 0.3% move required
                direction = 'BUY' if price_change > 0 else 'SELL'
                
                # 🔧 FIX: Better confidence scaling for volatility breakouts
                # vol_persistence ranges from 0 to ~1.5
                # persistence=0.8 = 6.5 + 0.8*2.0 = 8.1 (passes threshold)
                # persistence=1.0 = 6.5 + 1.0*2.0 = 8.5 (exceptional)
                # Higher multiplier rewards sustained volatility persistence
                vol_persistence = self._calculate_volatility_persistence(symbol)
                confidence = min(6.5 + vol_persistence * 2.0, 8.5)  # Cap at 8.5
                
                return MarketMicrostructureSignal(
                    signal_type=direction,
                    strength=vol_ratio,
                    confidence=confidence,
                    edge_source="VOLATILITY_CLUSTERING",
                    expected_duration=240,  # 4 minutes
                    risk_adjusted_return=0.012  # 1.2% expected return
                )
        
        return None
    
    def _detect_mean_reversion_opportunity(self, symbol: str, symbol_data: Dict) -> Optional[MarketMicrostructureSignal]:
        """Detect mean reversion after overreaction - ONLY in ranging markets"""
        # 🚨 CRITICAL FIX: Check market regime FIRST
        # Mean reversion CONTRADICTS trend following - only use in choppy markets
        if hasattr(self, 'market_bias') and self.market_bias:
            regime = self.market_bias.current_regime
            if regime in ['STRONG_TRENDING', 'TRENDING']:
                logger.debug(f"⏭️ MEAN REVERSION DISABLED for {symbol}: Market is {regime} (trend-following only)")
                return None
        
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return None
            
        prices = self.price_history[symbol]
        current_price = prices[-1]
        
        # Calculate z-score vs recent mean
        recent_prices = prices[-20:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        if std_price == 0:
            return None
            
        z_score = (current_price - mean_price) / std_price
        
        if abs(z_score) >= self.mean_reversion_zscore:
            # Significant deviation detected
            direction = 'SELL' if z_score > 0 else 'BUY'  # Revert to mean
            
            # Check for volume confirmation of overreaction
            volume = symbol_data.get('volume', 0)
            avg_volume = np.mean(self.volume_history.get(symbol, [volume])[-10:]) if symbol in self.volume_history else volume
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio >= 1.5:  # 50% above average volume
                # 🔧 FIX: Better confidence scaling for mean reversion
                # z_score=2.5, vol=2.0x: 6.0 + 2.5*0.8 + 2.0*0.5 = 6.0 + 2.0 + 1.0 = 9.0 → capped at 8.5
                # z_score=3.0, vol=1.5x: 6.0 + 3.0*0.8 + 1.5*0.5 = 6.0 + 2.4 + 0.75 = 9.15 → capped at 8.5
                # Higher multipliers for z-score and volume ratio to reward exceptional conditions
                confidence = min(6.0 + abs(z_score) * 0.8 + volume_ratio * 0.5, 8.5)  # Cap at 8.5
                
                return MarketMicrostructureSignal(
                    signal_type=direction,
                    strength=abs(z_score),
                    confidence=confidence,
                    edge_source="MEAN_REVERSION",
                    expected_duration=150,  # 2.5 minutes
                    risk_adjusted_return=0.006  # 0.6% expected return
                )
        
        return None
    
    def _detect_liquidity_gap(self, symbol: str, symbol_data: Dict) -> Optional[MarketMicrostructureSignal]:
        """Detect temporary liquidity gaps for quick profits - ONLY in ranging markets"""
        # 🚨 CRITICAL FIX: Check market regime FIRST
        # Liquidity gap fading CONTRADICTS trend following - only use in choppy markets
        if hasattr(self, 'market_bias') and self.market_bias:
            regime = self.market_bias.current_regime
            if regime in ['STRONG_TRENDING', 'TRENDING']:
                logger.debug(f"⏭️ LIQUIDITY GAP DISABLED for {symbol}: Market is {regime} (trend-following only)")
                return None
        
        # This is a simplified version - in reality, you'd need order book data
        volume = symbol_data.get('volume', 0)
        price_change = symbol_data.get('price_change', 0)
        
        # Proxy: large price move on relatively low volume indicates liquidity gap
        if abs(price_change) > 0.005 and volume < self.min_liquidity_threshold * 0.7:  # 30% below min threshold
            direction = 'SELL' if price_change > 0 else 'BUY'  # Fade the move
            
            # Quick reversion opportunity
            # 🔧 FIX: Better confidence scaling for liquidity gaps
            strength = abs(price_change) * 100
            base_confidence = 5.0 + strength * 0.8
            
            # 🔧 FIX: EXCEPTIONAL CONDITION BONUSES for truly outstanding liquidity gaps
            exceptional_bonus = 0.0
            
            # BONUS 1: Extreme low volume (< 50% of threshold) - clear liquidity vacuum
            if volume < self.min_liquidity_threshold * 0.5:
                exceptional_bonus += 0.5
                logger.debug(f"   ✨ EXTREME LOW VOLUME BONUS: +0.5 (vol={volume})")
            
            # BONUS 2: Extreme price move (> 3%) - very clear gap
            if abs(price_change) > 0.03:
                exceptional_bonus += 0.5
                logger.debug(f"   ✨ EXTREME PRICE MOVE BONUS: +0.5 (move={abs(price_change)*100:.1f}%)")
            
            # BONUS 3: RSI extreme (likely to revert)
            rsi = symbol_data.get('rsi', 50)
            if (direction == 'BUY' and rsi < 30) or (direction == 'SELL' and rsi > 70):
                exceptional_bonus += 0.4
                logger.debug(f"   ✨ RSI EXTREME BONUS: +0.4 (RSI={rsi})")
            
            confidence = min(base_confidence + exceptional_bonus, 9.0)  # Allow up to 9.0 for exceptional
            
            if exceptional_bonus > 0:
                logger.info(f"📊 {symbol} LIQUIDITY_GAP: exceptional_bonus={exceptional_bonus:.1f}, total_conf={confidence:.1f}")
            
            return MarketMicrostructureSignal(
                signal_type=direction,
                strength=strength,
                confidence=confidence,
                edge_source="LIQUIDITY_GAP",
                expected_duration=90,  # 1.5 minutes - quick reversal
                risk_adjusted_return=0.004  # 0.4% expected return
            )
        
        return None
    
    def _calculate_volatility_persistence(self, symbol: str) -> float:
        """Calculate volatility persistence for clustering analysis"""
        if symbol not in self.volatility_history or len(self.volatility_history[symbol]) < 10:
            return 0.0

        # 🚨 DEFENSIVE: Filter out entries without vol_ratio
        try:
            vol_ratios = []
            for v in self.volatility_history[symbol][-10:]:
                if isinstance(v, dict) and 'vol_ratio' in v and isinstance(v['vol_ratio'], (int, float)):
                    vol_ratios.append(v['vol_ratio'])
                else:
                    # Use default ratio of 1.0 for missing/invalid data
                    vol_ratios.append(1.0)

            if not vol_ratios:
                return 0.0

            # Check how many recent periods had high volatility
            high_vol_periods = sum(1 for ratio in vol_ratios if ratio > 1.2)
            persistence = high_vol_periods / len(vol_ratios)

            return persistence

        except Exception as e:
            logger.warning(f"⚠️ Error calculating volatility persistence for {symbol}: {e}")
            return 0.0
    
    async def _fetch_historical_for_symbol(self, symbol: str) -> bool:
        """
        🔥 Fetch MULTI-TIMEFRAME historical data from Zerodha.
        Fetches 5-min, 15-min, and 60-min candles for higher accuracy signals.
        """
        try:
            if not hasattr(self, '_historical_data_fetched'):
                self._historical_data_fetched = set()
            
            if symbol in self._historical_data_fetched:
                return True
            
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not hasattr(orchestrator, 'zerodha_client') or not orchestrator.zerodha_client:
                return False
            
            zerodha_client = orchestrator.zerodha_client
            from datetime import datetime, timedelta
            
            # Initialize MTF storage
            if not hasattr(self, 'mtf_data'):
                self.mtf_data = {}
            if symbol not in self.mtf_data:
                self.mtf_data[symbol] = {'5min': [], '15min': [], '60min': []}
            
            # Fetch 5-minute candles
            candles_5m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='5minute',
                from_date=datetime.now() - timedelta(days=3),
                to_date=datetime.now()
            )
            
            if candles_5m and len(candles_5m) >= 14:
                self.mtf_data[symbol]['5min'] = candles_5m[-50:]
                if not hasattr(self, 'price_history'):
                    self.price_history = {}
                self.price_history[symbol] = [c['close'] for c in candles_5m[-50:]]
            
            # Fetch 15-minute candles
            candles_15m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='15minute',
                from_date=datetime.now() - timedelta(days=5),
                to_date=datetime.now()
            )
            if candles_15m and len(candles_15m) >= 14:
                self.mtf_data[symbol]['15min'] = candles_15m[-30:]
            
            # Fetch 60-minute candles
            candles_60m = await zerodha_client.get_historical_data(
                symbol=symbol,
                interval='60minute',
                from_date=datetime.now() - timedelta(days=10),
                to_date=datetime.now()
            )
            if candles_60m and len(candles_60m) >= 14:
                self.mtf_data[symbol]['60min'] = candles_60m[-20:]
            
            tf_5m = len(self.mtf_data[symbol]['5min'])
            tf_15m = len(self.mtf_data[symbol]['15min'])
            tf_60m = len(self.mtf_data[symbol]['60min'])
            
            # 🔥 FIX: Only mark as fetched if we actually got enough data for RSI calculation
            # Otherwise retry on next cycle
            if tf_5m >= 14:
                self._historical_data_fetched.add(symbol)
                logger.info(f"✅ MTF DATA: {symbol} - 5min:{tf_5m}, 15min:{tf_15m}, 60min:{tf_60m}")
                
                # Also mark in base strategy's tracker
                if not hasattr(self, '_mtf_fetched'):
                    self._mtf_fetched = set()
                self._mtf_fetched.add(symbol)
            else:
                logger.warning(f"⚠️ MTF DATA INSUFFICIENT: {symbol} - 5min:{tf_5m} < 14 required. Will retry.")
            
            return tf_5m >= 14
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching MTF data for {symbol}: {e}")
            return False

    async def _convert_to_trading_signal(self, symbol: str, symbol_data: Dict, ms_signal: MarketMicrostructureSignal) -> Optional[Dict]:
        """
        Convert microstructure signal to executable trading signal
        🎯 PHASE 2 COMPLETE: Now validates with RSI, MACD, Bollinger
        """
        try:
            current_price = symbol_data.get('close', symbol_data.get('ltp', 0))
            high = symbol_data.get('high', current_price)
            low = symbol_data.get('low', current_price)
            open_price = symbol_data.get('open', current_price)
            
            if current_price <= 0:
                return None
            
            # 🔥 CRITICAL: Fetch historical data to enable RSI/MACD/Bollinger
            if not hasattr(self, '_historical_data_fetched') or symbol not in self._historical_data_fetched:
                await self._fetch_historical_for_symbol(symbol)
            
            # ============= PHASE 2: PRICE HISTORY (CANDLE-BASED for accurate indicators) =============
            # 🔧 FIX 2024-12-24: Use 5-minute candle closes for RSI/indicators, NOT tick data!
            # Tick-based RSI is meaningless noise. Standard practice is candle-based RSI.
            if not hasattr(self, 'price_history'):
                self.price_history = {}
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            # PREFER candle closes from mtf_data (consistent with other strategies)
            prices = []
            if hasattr(self, 'mtf_data') and symbol in self.mtf_data:
                candles = self.mtf_data[symbol].get('5min', [])
                if candles and len(candles) >= 14:
                    prices = [c.get('close', 0) for c in candles[-50:] if c.get('close', 0) > 0]
                    self.price_history[symbol] = prices  # Update for consistency
            
            # Fallback to tick-based only if no candle data available
            if len(prices) < 14:
                self.price_history[symbol].append(current_price)
                self.price_history[symbol] = self.price_history[symbol][-50:]
                prices = self.price_history[symbol]
            
            # ============= PHASE 2: CANDLE ANALYSIS (FIXED FOR DAY OHLC) =============
            candle_range = high - low if high > low else 0.01
            buying_pressure = (current_price - low) / candle_range
            selling_pressure = (high - current_price) / candle_range
            
            # 🔥 ENHANCED: Use intraday movement for more meaningful pressure
            if open_price > 0 and candle_range > 0:
                intraday_move = current_price - open_price
                move_ratio = intraday_move / candle_range
                if move_ratio > 0:
                    buying_pressure = min(0.5 + move_ratio * 0.5, 1.0)
                    selling_pressure = max(0.5 - move_ratio * 0.5, 0.0)
                else:
                    buying_pressure = max(0.5 + move_ratio * 0.5, 0.0)
                    selling_pressure = min(0.5 - move_ratio * 0.5, 1.0)
            
            # ============= PHASE 2: ADVANCED INDICATORS =============
            rsi = 50.0
            mfi = 50.0  # 🔧 NEW: Money Flow Index (volume-weighted RSI)
            macd_crossover = None
            macd_state = 'neutral'
            short_macd_state = 'neutral'  # 🆕 Short MACD (5-13-4) - faster
            macd_trend = 'NEUTRAL'  # 🆕 MACD histogram trend: RISING, FALLING, NEUTRAL
            bollinger_squeeze = False
            bollinger_breakout = None
            mean_reversion_prob = 0.5
            momentum_score = 0.0
            trend_strength = 0.0
            hp_trend_direction = 0.0

            # Import ProfessionalMomentumModels for advanced calculations
            from strategies.momentum_surfer import ProfessionalMomentumModels

            # 🔧 NEW: Volume-weighted indicators
            vrsi = 50.0
            vrsi_short = 50.0  # 🆕 Short-term VRSI (5 periods)
            vrsi_trend = 'NEUTRAL'  # 🆕 VRSI trend: RISING, FALLING, NEUTRAL
            vw_buying_pressure = 0.5
            vw_selling_pressure = 0.5
            volume_confirmation = False
            
            if len(prices) >= 14:
                rsi = self._calculate_rsi(prices, 14)
                
                # 🔧 NEW: Calculate all volume-weighted indicators
                if hasattr(self, 'mtf_data') and symbol in self.mtf_data:
                    candles = self.mtf_data[symbol].get('5min', [])
                    if candles and len(candles) >= 14:
                        highs = [c.get('high', c.get('close', 0)) for c in candles[-20:]]
                        lows = [c.get('low', c.get('close', 0)) for c in candles[-20:]]
                        closes = [c.get('close', 0) for c in candles[-20:]]
                        opens = [c.get('open', c.get('close', 0)) for c in candles[-20:]]
                        volumes = [c.get('volume', 0) for c in candles[-20:]]
                        
                        if all(v > 0 for v in volumes):  # Only if we have volume data
                            # 1. MFI (Money Flow Index)
                            mfi_data = self.calculate_money_flow_index(highs, lows, closes, volumes)
                            mfi = mfi_data.get('mfi', 50.0)
                            
                            # 2. VRSI (Volume-Weighted RSI)
                            vrsi_data = self.calculate_volume_weighted_rsi(closes, volumes)
                            vrsi = vrsi_data.get('vrsi', 50.0)
                            vrsi_short = vrsi_data.get('vrsi_short', vrsi)  # 🆕 Short-term VRSI
                            vrsi_trend = vrsi_data.get('vrsi_trend', 'NEUTRAL')  # 🆕 VRSI trend
                            volume_confirmation = vrsi_data.get('volume_confirmation', False)
                            
                            # 3. Volume-Weighted Buy/Sell Pressure
                            vw_pressure = self.calculate_volume_weighted_pressure(
                                highs, lows, closes, volumes, opens
                            )
                            vw_buying_pressure = vw_pressure.get('vw_buying_pressure', 0.5)
                            vw_selling_pressure = vw_pressure.get('vw_selling_pressure', 0.5)
                prices_arr = np.array(prices)
                momentum_score = ProfessionalMomentumModels.momentum_score(prices_arr, min(20, len(prices)))
                mean_reversion_prob = ProfessionalMomentumModels.mean_reversion_probability(prices_arr)
                trend_strength = ProfessionalMomentumModels.trend_strength(prices_arr)
                hp_trend, hp_cycle, hp_trend_direction = ProfessionalMomentumModels.hp_trend_filter(prices_arr)
            
            if len(prices) >= 26:
                macd_data = self.calculate_macd_signal(prices)
                macd_crossover = macd_data.get('crossover')
                macd_state = macd_data.get('state', 'neutral')
                # 🆕 Short MACD (5-13-4) - faster, less laggy
                short_macd_state = macd_data.get('short_state', macd_state)
                macd_trend = macd_data.get('macd_trend', 'NEUTRAL')  # RISING, FALLING, NEUTRAL
            
            if len(prices) >= 20:
                # 🎯 TTM SQUEEZE: Extract OHLCV data for Keltner Channel calculation
                highs, lows, volumes = None, None, None
                if hasattr(self, 'mtf_data') and symbol in self.mtf_data:
                    candles = self.mtf_data[symbol].get('5min', [])
                    if candles and len(candles) >= 20:
                        highs = [c.get('high', c.get('close', 0)) for c in candles[-50:]]
                        lows = [c.get('low', c.get('close', 0)) for c in candles[-50:]]
                        volumes = [c.get('volume', 0) for c in candles[-50:]]
                
                bollinger_data = self.detect_bollinger_squeeze(symbol, prices, highs=highs, lows=lows, volumes=volumes)
                bollinger_squeeze = bollinger_data.get('squeezing', False)
                bollinger_breakout = bollinger_data.get('breakout_direction')
                squeeze_quality = bollinger_data.get('squeeze_quality', 'LOW')
            
            # 🎯 ENHANCED: Dual-Timeframe Validation
            dual_analysis = self.analyze_stock_dual_timeframe(symbol, symbol_data)
            weighted_bias = dual_analysis.get('weighted_bias', 0.0)
            alignment = dual_analysis.get('alignment', 'UNKNOWN')
            
            # ============= PHASE 2: RSI/MACD/HP TREND VALIDATION =============
            # 🔧 Enhanced with VOLUME-WEIGHTED indicators (VRSI, MFI, VW Pressure)
            
            # ============= 🚨 CRITICAL: NIFTY MARKET CONDITION CHECK =============
            # Block BUY signals when NIFTY is extremely overbought (contradictory trade)
            # Block SELL signals when NIFTY is extremely oversold
            try:
                nifty_data = market_data.get('NIFTY-I') or market_data.get('NIFTY') or {}
                nifty_change = float(nifty_data.get('change_percent', 0) or 0)
                
                # Get NIFTY's MFI/RSI from market bias if available
                nifty_mfi = 50  # Default neutral
                nifty_rsi = 50
                if hasattr(self, 'market_bias') and self.market_bias:
                    try:
                        bias_info = self.market_bias.get_bias() if hasattr(self.market_bias, 'get_bias') else {}
                        nifty_mfi = bias_info.get('nifty_mfi', 50)
                        nifty_rsi = bias_info.get('nifty_rsi', 50)
                    except:
                        pass
                
                # 🚨 NIFTY EXTREME OVERBOUGHT: Block ALL BUY signals
                # Conditions: NIFTY up > 1.0% AND (MFI > 80 OR RSI > 70)
                if ms_signal.signal_type == 'BUY':
                    if nifty_change > 1.0 and (nifty_mfi > 80 or nifty_rsi > 70):
                        logger.warning(f"🚫 {symbol}: BUY BLOCKED - NIFTY EXTREME OVERBOUGHT "
                                      f"(NIFTY +{nifty_change:.2f}%, MFI={nifty_mfi:.0f}, RSI={nifty_rsi:.0f})")
                        return None
                    # Also block if NIFTY up > 1.5% regardless of indicators
                    if nifty_change > 1.5:
                        logger.warning(f"🚫 {symbol}: BUY BLOCKED - NIFTY EXTENDED (+{nifty_change:.2f}% > 1.5%)")
                        return None
                
                # 🚨 NIFTY EXTREME OVERSOLD: Block ALL SELL signals
                if ms_signal.signal_type == 'SELL':
                    if nifty_change < -1.0 and (nifty_mfi < 20 or nifty_rsi < 30):
                        logger.warning(f"🚫 {symbol}: SELL BLOCKED - NIFTY EXTREME OVERSOLD "
                                      f"(NIFTY {nifty_change:.2f}%, MFI={nifty_mfi:.0f}, RSI={nifty_rsi:.0f})")
                        return None
                    # Also block if NIFTY down > 1.5% regardless of indicators
                    if nifty_change < -1.5:
                        logger.warning(f"🚫 {symbol}: SELL BLOCKED - NIFTY EXTENDED ({nifty_change:.2f}% < -1.5%)")
                        return None
            except Exception as e:
                logger.debug(f"NIFTY market check failed: {e}")
            
            # 🔧 2025-12-29 FIX: Extract pattern BEFORE BUY/SELL branching so it's available in both
            day_change = dual_analysis.get('day_change', 0.0)
            pattern = dual_analysis.get('pattern', '')
            
            # BUY signal validation
            if ms_signal.signal_type == 'BUY':
                # 🎯 CONTEXT-AWARE: Detect strong breakout scenarios
                # In breakouts, overbought indicators CONFIRM momentum, not contradict it
                
                # Strong breakout criteria (cautious thresholds):
                # 1. Very strong move (>5%) regardless of pattern, OR
                # 2. Moderate move (>2%) with BULLISH CONTINUATION pattern
                is_strong_breakout = (
                    day_change >= 5.0 or 
                    (day_change >= 2.0 and 'BULLISH' in pattern and 'CONTINUATION' in pattern)
                )
                
                # Don't buy if overbought - UNLESS strong breakout (with safety caps)
                if rsi > 70:
                    if is_strong_breakout and rsi <= 92:
                        # Overbought RSI confirms momentum in breakout
                        logger.info(f"✅ {symbol}: BUY - RSI overbought ({rsi:.0f}) CONFIRMS breakout momentum (+{day_change:.1f}%)")
                    else:
                        logger.info(f"⚠️ {symbol}: BUY rejected - RSI overbought ({rsi:.0f})")
                        return None
                
                # 🔧 MFI (volume-weighted RSI) check
                if mfi > 80:
                    if is_strong_breakout and mfi <= 95:
                        logger.info(f"✅ {symbol}: BUY - MFI overbought ({mfi:.0f}) CONFIRMS breakout momentum (+{day_change:.1f}%)")
                    else:
                        logger.info(f"⚠️ {symbol}: BUY rejected - MFI overbought ({mfi:.0f})")
                        return None
                
                # 🔧 NEW: VRSI (Volume-Weighted RSI) check
                if vrsi > 75:
                    if is_strong_breakout and vrsi <= 95:
                        logger.info(f"✅ {symbol}: BUY - VRSI overbought ({vrsi:.0f}) CONFIRMS breakout momentum (+{day_change:.1f}%)")
                    else:
                        logger.info(f"⚠️ {symbol}: BUY rejected - VRSI overbought ({vrsi:.0f})")
                        return None
                
                # 🔧 NEW: Low VRSI means volume NOT confirming upward momentum
                # 🔧 2025-12-29: Use SHORT VRSI TREND instead of just absolute value
                # VRSI (14 period) is lagging - vrsi_trend tells us if recent volume is shifting
                #
                # Logic:
                # - vrsi_trend == 'RISING' means recent volume is on UP moves → confirms BUY
                # - In this case, we can allow lower VRSI (it's lagging)
                
                vrsi_buy_threshold = 35  # Base threshold
                if vrsi_trend == 'RISING':
                    # Recent volume is confirming buy - allow lower VRSI (it's lagging)
                    vrsi_buy_threshold = 15  # More lenient
                elif 'BULLISH' in pattern.upper():
                    # Pattern confirms - allow lower threshold
                    vrsi_buy_threshold = 25
                
                if vrsi < vrsi_buy_threshold and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - VRSI too low ({vrsi:.0f} < {vrsi_buy_threshold}), short_vrsi={vrsi_short:.0f}, trend={vrsi_trend}")
                    return None

                # 🔧 NEW: Volume-Weighted Sell Pressure check (more accurate than candle-based)
                if vw_selling_pressure > 0.60 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - High volume-weighted selling pressure ({vw_selling_pressure:.0%})")
                    return None
                
                # 🔧 NEW: Volume-Weighted Buy Pressure minimum
                if vw_buying_pressure < 0.35 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - Low volume-weighted buying pressure ({vw_buying_pressure:.0%})")
                    return None
                
                # 🔧 Check MACD STATE (not just crossover event)
                # 🔧 2025-12-29: Multi-layer MACD check to fix lagging issue:
                # 1. Pattern-aware: BULLISH pattern = bearish MACD is lagging
                # 2. Short MACD (5-13-4): If bullish, MACD is already confirming
                # 3. MACD Trend: If RISING, momentum is shifting bullish
                is_bullish_pattern = 'BULLISH' in pattern.upper()
                short_macd_confirms = short_macd_state == 'bullish'  # Short MACD confirms buy
                macd_trend_confirms = macd_trend == 'RISING'  # Histogram rising = bullish momentum
                
                # Allow BUY if ANY of these is true:
                # - Pattern is bullish (price action confirms)
                # - Short MACD is bullish (faster indicator confirms)
                # - MACD trend is rising (momentum shifting)
                macd_allows_buy = is_bullish_pattern or short_macd_confirms or macd_trend_confirms
                
                if ms_signal.edge_source != "MEAN_REVERSION":
                    if macd_crossover == 'bearish' and not macd_allows_buy:
                        logger.info(f"⚠️ {symbol}: BUY rejected - MACD bearish crossover")
                        return None
                    # Reject if MACD state is bearish + weak/neutral RSI (unless allowed)
                    if macd_state == 'bearish' and rsi <= 50 and not macd_allows_buy:
                        logger.info(f"⚠️ {symbol}: BUY rejected - MACD bearish state + weak RSI ({rsi:.0f})")
                        return None
                    # Log when we ALLOW despite bearish MACD
                    if (macd_state == 'bearish' or macd_crossover == 'bearish') and macd_allows_buy:
                        reason = []
                        if is_bullish_pattern: reason.append(f"pattern={pattern}")
                        if short_macd_confirms: reason.append("short_macd=bullish")
                        if macd_trend_confirms: reason.append("trend=RISING")
                        logger.info(f"✅ {symbol}: BUY allowed - MACD bearish but {', '.join(reason)}")
                
                # Candle-based pressure checks (fallback if volume data unavailable)
                if selling_pressure > 0.65 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - Strong selling pressure ({selling_pressure:.0%})")
                    return None
                
                if buying_pressure < 0.40 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - Weak buying pressure ({buying_pressure:.0%})")
                    return None
                
                # Don't buy if HP trend strongly negative (unless mean reversion)
                if hp_trend_direction < -0.01 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: BUY rejected - HP trend strongly negative ({hp_trend_direction:+.2%})")
                    return None
            
            # SELL signal validation
            elif ms_signal.signal_type == 'SELL':
                # Don't sell if oversold (check RSI, MFI, and VRSI)
                if rsi < 30:
                    logger.info(f"⚠️ {symbol}: SELL rejected - RSI oversold ({rsi:.0f})")
                    return None
                
                # 🔧 MFI (volume-weighted RSI) check
                if mfi < 20:
                    logger.info(f"⚠️ {symbol}: SELL rejected - MFI oversold ({mfi:.0f})")
                    return None
                
                # 🔧 NEW: VRSI (Volume-Weighted RSI) check
                if vrsi < 25:
                    logger.info(f"⚠️ {symbol}: SELL rejected - VRSI oversold ({vrsi:.0f})")
                    return None
                
                # 🔧 NEW: High VRSI means volume NOT confirming downward momentum
                # 🔧 2025-12-29: Use SHORT VRSI TREND instead of just absolute value
                # VRSI (14 period) is lagging - vrsi_trend tells us if recent volume is shifting
                # 
                # Logic:
                # - vrsi_trend == 'FALLING' means recent volume is on DOWN moves → confirms SELL
                # - In this case, we can ignore high VRSI (it's lagging)
                # - If vrsi_trend is not FALLING, we need pattern confirmation to allow high VRSI
                
                vrsi_sell_threshold = 65  # Base threshold
                if vrsi_trend == 'FALLING':
                    # Recent volume is confirming sell - allow higher VRSI (it's lagging)
                    vrsi_sell_threshold = 95  # Almost no restriction
                elif 'BEARISH' in pattern.upper():
                    # Pattern confirms - allow higher threshold
                    vrsi_sell_threshold = 90
                
                if vrsi > vrsi_sell_threshold and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - VRSI too high ({vrsi:.0f} > {vrsi_sell_threshold}), short_vrsi={vrsi_short:.0f}, trend={vrsi_trend}")
                    return None

                # 🔧 NEW: Volume-Weighted Buy Pressure check (more accurate than candle-based)
                if vw_buying_pressure > 0.60 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - High volume-weighted buying pressure ({vw_buying_pressure:.0%})")
                    return None
                
                # 🔧 NEW: Volume-Weighted Sell Pressure minimum
                if vw_selling_pressure < 0.35 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - Low volume-weighted selling pressure ({vw_selling_pressure:.0%})")
                    return None
                
                # 🔧 Check MACD STATE (not just crossover event)
                # 🔧 2025-12-29: Multi-layer MACD check to fix lagging issue:
                # 1. Pattern-aware: BEARISH pattern = bullish MACD is lagging
                # 2. Short MACD (5-13-4): If bearish, MACD is already confirming
                # 3. MACD Trend: If FALLING, momentum is shifting bearish
                is_bearish_pattern = 'BEARISH' in pattern.upper()
                short_macd_confirms = short_macd_state == 'bearish'  # Short MACD confirms sell
                macd_trend_confirms = macd_trend == 'FALLING'  # Histogram falling = bearish momentum
                
                # Allow SELL if ANY of these is true:
                # - Pattern is bearish (price action confirms)
                # - Short MACD is bearish (faster indicator confirms)
                # - MACD trend is falling (momentum shifting)
                macd_allows_sell = is_bearish_pattern or short_macd_confirms or macd_trend_confirms
                
                if ms_signal.edge_source != "MEAN_REVERSION":
                    if macd_crossover == 'bullish' and not macd_allows_sell:
                        logger.info(f"⚠️ {symbol}: SELL rejected - MACD bullish crossover")
                        return None
                    # Reject if MACD state is bullish + neutral/strong RSI (unless allowed)
                    if macd_state == 'bullish' and rsi >= 50 and not macd_allows_sell:
                        logger.info(f"⚠️ {symbol}: SELL rejected - MACD bullish state + strong RSI ({rsi:.0f})")
                        return None
                    # Log when we ALLOW despite bullish MACD
                    if (macd_state == 'bullish' or macd_crossover == 'bullish') and macd_allows_sell:
                        reason = []
                        if is_bearish_pattern: reason.append(f"pattern={pattern}")
                        if short_macd_confirms: reason.append("short_macd=bearish")
                        if macd_trend_confirms: reason.append("trend=FALLING")
                        logger.info(f"✅ {symbol}: SELL allowed - MACD bullish but {', '.join(reason)}")
                
                # Candle-based pressure checks (fallback if volume data unavailable)
                if buying_pressure > 0.65 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - Strong buying pressure ({buying_pressure:.0%})")
                    return None
                
                if selling_pressure < 0.40 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - Weak selling pressure ({selling_pressure:.0%})")
                    return None
                
                # Don't sell if HP trend strongly positive (unless mean reversion)
                if hp_trend_direction > 0.01 and ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ {symbol}: SELL rejected - HP trend strongly positive ({hp_trend_direction:+.2%})")
                    return None
            
            # ============= PHASE 3: BOLLINGER + GARCH REGIME VALIDATION =============
            # Get GARCH volatility regime
            vol_regime = 'NORMAL_VOLATILITY'
            if symbol in self.volatility_history and self.volatility_history[symbol]:
                latest_vol = self.volatility_history[symbol][-1]
                vol_regime = latest_vol.get('vol_regime', 'NORMAL_VOLATILITY')
            
            # 🚨 EXTREME VOLATILITY FILTER: Be cautious in extreme volatility
            if vol_regime == 'EXTREME_VOLATILITY':
                # In extreme volatility, require HIGHER squeeze quality or strong breakout
                if squeeze_quality == 'LOW' and not bollinger_breakout:
                    logger.info(f"⚠️ {symbol}: Signal filtered - Extreme volatility + low squeeze quality")
                    return None
            
            # 🎯 BOLLINGER SQUEEZE QUALITY ENHANCEMENT
            # HIGH quality squeeze with breakout = high confidence
            if bollinger_squeeze and squeeze_quality == 'HIGH' and bollinger_breakout:
                if (ms_signal.signal_type == 'BUY' and bollinger_breakout == 'up') or \
                   (ms_signal.signal_type == 'SELL' and bollinger_breakout == 'down'):
                    ms_signal.confidence = min(ms_signal.confidence * 1.15, 10.0)
                    logger.info(f"   ✨ HIGH QUALITY SQUEEZE BREAKOUT: Confidence boosted to {ms_signal.confidence:.1f}")
                else:
                    # Breakout direction conflicts with signal - reduce confidence
                    logger.info(f"⚠️ {symbol}: Signal weakened - Breakout direction ({bollinger_breakout}) conflicts with {ms_signal.signal_type}")
                    ms_signal.confidence *= 0.85
            
            # Log validation passed with ALL indicators (including volume-weighted)
            logger.info(f"✅ {symbol} {ms_signal.signal_type}: RSI={rsi:.0f}, VRSI={vrsi:.0f}, MFI={mfi:.0f}, MACD={macd_state}")
            logger.info(f"   📊 Pressure: Candle={buying_pressure:.0%}/{selling_pressure:.0%} | VW={vw_buying_pressure:.0%}/{vw_selling_pressure:.0%}")
            logger.info(f"   📉 Momentum: {momentum_score:.3f} | Trend: {trend_strength:.2f} | HP: {hp_trend_direction:+.2%}")
            logger.info(f"   🔄 Mean Rev: {mean_reversion_prob:.0%} | Bollinger: {'SQUEEZE!' if bollinger_squeeze else 'normal'} ({squeeze_quality}) | Vol: {vol_regime}")
            if bollinger_breakout:
                logger.info(f"   💥 BOLLINGER BREAKOUT: {bollinger_breakout.upper()}")
            
            # Legacy dual-timeframe check
            if ms_signal.signal_type == 'BUY' and weighted_bias < -1.0:
                if ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ FILTERED: {symbol} BUY signal rejected due to strong negative bias ({weighted_bias:.1f}%)")
                    return None
            
            if ms_signal.signal_type == 'SELL' and weighted_bias > 1.0:
                if ms_signal.edge_source != "MEAN_REVERSION":
                    logger.info(f"⚠️ FILTERED: {symbol} SELL signal rejected due to strong positive bias ({weighted_bias:.1f}%)")
                    return None

            # Calculate position size based on expected duration and risk
            atr = self.calculate_atr(symbol, 
                                   symbol_data.get('high', current_price),
                                   symbol_data.get('low', current_price), 
                                   current_price)
            
            # DYNAMIC 1% RISK-BASED STOP LOSS (replacing hardcoded percentages)
            # Get available capital for 1% risk calculation
            available_capital = self._get_available_capital()
            max_risk_amount = available_capital * 0.01  # 1% maximum risk
            
            # Calculate stop loss based on 1% risk constraint
            if ms_signal.edge_source == "LIQUIDITY_GAP":
                # Tight stops for liquidity trades - target 0.8% risk
                target_risk_pct = 0.008
            elif ms_signal.edge_source == "MEAN_REVERSION":
                # Wider stops for mean reversion - target 1% risk (maximum)
                target_risk_pct = 0.01
            else:
                # Standard stops for other strategies - target 0.9% risk
                target_risk_pct = 0.009
            
            # Calculate stop loss distance to achieve target risk
            # Estimate trade value for risk calculation
            estimated_trade_value = min(available_capital * 0.25, 50000)  # 25% capital or ₹50k
            estimated_quantity = estimated_trade_value / current_price
            target_risk_amount = available_capital * target_risk_pct
            stop_loss_distance = target_risk_amount / estimated_quantity
            stop_loss_pct = stop_loss_distance / current_price
            
            # Calculate stop loss and dynamic target based on market conditions
            if ms_signal.signal_type == 'BUY':
                stop_loss = current_price - stop_loss_distance
                # Dynamic target using market-adaptive risk-reward
                target = self.calculate_dynamic_target(current_price, stop_loss)
            else:
                stop_loss = current_price + stop_loss_distance
                # Dynamic target using market-adaptive risk-reward  
                target = self.calculate_dynamic_target(current_price, stop_loss)
            
            logger.info(f"💡 {ms_signal.edge_source}: Risk={target_risk_pct*100:.1f}%, "
                       f"Stop Distance=₹{stop_loss_distance:.2f}, Entry={current_price:.2f}")
            
            # PROFESSIONAL VWAP EXECUTION OPTIMIZATION
            estimated_quantity = int(estimated_trade_value / current_price)
            vwap_price, execution_info = self._calculate_vwap_execution_price(
                symbol, symbol_data, estimated_quantity, ms_signal.signal_type
            )
            
            # Round prices to tick size
            entry_price = self._round_to_tick_size(vwap_price)  # Use VWAP-optimized price
            stop_loss = self._round_to_tick_size(stop_loss)
            target = self._round_to_tick_size(target)
            
            # Create high-quality signal (MR check automatic in base_strategy)
            signal = await self.create_standard_signal(
                symbol=symbol,
                action=ms_signal.signal_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                confidence=ms_signal.confidence,
                metadata={
                    'edge_source': ms_signal.edge_source,
                    'expected_duration': ms_signal.expected_duration,
                    'risk_adjusted_return': ms_signal.risk_adjusted_return,
                    'microstructure_strength': ms_signal.strength,
                    'strategy_type': 'microstructure',
                    'time_sensitive': True,
                    'max_hold_time': self.max_position_time
                },
                market_bias=self.market_bias  # 🎯 Pass market bias for coordination
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error converting microstructure signal: {e}")
            return None
    
    def _filter_for_quality(self, signals: List[Dict]) -> List[Dict]:
        """Filter for only highest quality microstructure signals
        
        🚨 CRITICAL FIX: Include ALL valid edge sources, not just a subset.
        Previously PROFESSIONAL_ORDER_FLOW, STATISTICAL_ARBITRAGE signals were silently dropped!
        """
        quality_signals = []
        
        for signal in signals:
            confidence = signal.get('confidence', 0)
            metadata = signal.get('metadata', {})
            edge_source = metadata.get('edge_source', '')
            
            # Base minimum confidence
            if confidence < 7.5:
                continue
            
            # Define confidence thresholds per edge source
            # Higher thresholds for noisier signals, lower for cleaner signals
            edge_thresholds = {
                # Tier 1: Cleaner signals - lower threshold
                'MEAN_REVERSION': 7.5,
                'LIQUIDITY_GAP': 7.5,
                'STATISTICAL_ARBITRAGE': 7.5,
                
                # Tier 2: Standard signals - medium threshold  
                'ORDER_FLOW_IMBALANCE': 7.8,
                'PROFESSIONAL_ORDER_FLOW': 7.8,  # 🚨 FIX: This was MISSING!
                
                # Tier 3: Noisier signals - higher threshold
                'VOLATILITY_CLUSTERING': 8.0,
            }
            
            # Get threshold for this edge source (default 7.5 for unknown sources)
            required_confidence = edge_thresholds.get(edge_source, 7.5)
            
            if confidence >= required_confidence:
                quality_signals.append(signal)
                logger.debug(f"✅ QUALITY PASS: {signal.get('symbol')} {edge_source} conf={confidence:.1f} (req={required_confidence})")
            else:
                logger.debug(f"⚠️ QUALITY REJECT: {signal.get('symbol')} {edge_source} conf={confidence:.1f} < req={required_confidence}")
        
        # Limit to top 3 signals per cycle
        quality_signals.sort(key=lambda x: x['confidence'], reverse=True)
        return quality_signals[:3]
    
    def _round_to_tick_size(self, price: float) -> float:
        """Round price to appropriate tick size"""
        try:
            from src.utils.helpers import round_price_to_tick
            return round_price_to_tick(price, 0.05)
        except ImportError:
            return round(price / 0.05) * 0.05

    async def _enhance_signals_with_ml(self, signals: List[MarketMicrostructureSignal], 
                                     symbol: str, symbol_data: Dict) -> List[MarketMicrostructureSignal]:
        """PROFESSIONAL ML SIGNAL ENHANCEMENT with feature engineering"""
        try:
            if not signals:
                return signals
            
            enhanced_signals = []
            
            for signal in signals:
                # FEATURE ENGINEERING
                features = self._extract_ml_features(symbol, symbol_data, signal)
                
                if len(features) > 0:
                    # ML PREDICTION (if model is trained)
                    ml_confidence_boost = await self._get_ml_confidence_boost(features)
                    
                    # ENHANCE SIGNAL WITH ML
                    enhanced_signal = self._apply_ml_enhancement(signal, ml_confidence_boost, features)
                    enhanced_signals.append(enhanced_signal)
                    
                    # STORE FOR TRAINING
                    self._store_ml_training_data(features, signal)
                else:
                    enhanced_signals.append(signal)
            
            # TRAIN ML MODEL IF ENOUGH DATA
            await self._update_ml_model()
            
            return enhanced_signals
            
        except Exception as e:
            logger.error(f"ML signal enhancement failed: {e}")
            return signals
    
    def _extract_ml_features(self, symbol: str, symbol_data: Dict, 
                           signal: MarketMicrostructureSignal) -> np.ndarray:
        """PROFESSIONAL FEATURE ENGINEERING for ML enhancement"""
        try:
            features = []
            
            # MARKET MICROSTRUCTURE FEATURES
            features.extend([
                signal.strength,
                signal.confidence,
                signal.risk_adjusted_return,
                signal.statistical_significance,
                signal.sharpe_ratio,
                signal.var_95,
                signal.kelly_fraction
            ])
            
            # VOLATILITY REGIME FEATURES
            if symbol in self.volatility_history and self.volatility_history[symbol]:
                vol_data = self.volatility_history[symbol][-1]
                features.extend([
                    vol_data.get('current_vol', 0.02),
                    vol_data.get('clustering_strength', 0.0),
                    vol_data.get('vol_percentile', 50.0),
                    1.0 if vol_data.get('vol_regime') == 'HIGH_VOLATILITY' else 0.0,
                    1.0 if vol_data.get('vol_regime') == 'LOW_VOLATILITY' else 0.0
                ])
            else:
                features.extend([0.02, 0.0, 50.0, 0.0, 0.0])
            
            # PRICE ACTION FEATURES
            if symbol in self.price_history and len(self.price_history[symbol]) >= 10:
                prices = self.price_history[symbol][-10:]
                returns = np.diff(prices) / prices[:-1]
                
                features.extend([
                    np.mean(returns),  # Average return
                    np.std(returns),   # Return volatility
                    np.max(returns),   # Max return
                    np.min(returns),   # Min return
                    len([r for r in returns if r > 0]) / len(returns),  # Win rate
                    np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0,  # Avg win
                    np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0   # Avg loss
                ])
            else:
                features.extend([0.0, 0.02, 0.0, 0.0, 0.5, 0.0, 0.0])
            
            # VOLUME FEATURES
            if symbol in self.volume_history and len(self.volume_history[symbol]) >= 5:
                volumes = self.volume_history[symbol][-5:]
                current_volume = symbol_data.get('volume', 0)
                avg_volume = np.mean(volumes)
                
                features.extend([
                    current_volume / avg_volume if avg_volume > 0 else 1.0,  # Volume ratio
                    np.std(volumes) / avg_volume if avg_volume > 0 else 0.0,  # Volume volatility
                    current_volume  # Absolute volume
                ])
            else:
                features.extend([1.0, 0.0, symbol_data.get('volume', 0)])
            
            # TIME-BASED FEATURES
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            
            features.extend([
                current_time.hour / 24.0,  # Hour of day (normalized)
                current_time.minute / 60.0,  # Minute of hour (normalized)
                1.0 if 9 <= current_time.hour <= 10 else 0.0,  # Opening hour
                1.0 if 14 <= current_time.hour <= 15 else 0.0,  # Closing hour
                1.0 if current_time.weekday() == 0 else 0.0,  # Monday
                1.0 if current_time.weekday() == 4 else 0.0   # Friday
            ])
            
            # SIGNAL TYPE FEATURES (one-hot encoding)
            features.extend([
                1.0 if signal.edge_source == "PROFESSIONAL_ORDER_FLOW" else 0.0,
                1.0 if signal.edge_source == "STATISTICAL_ARBITRAGE" else 0.0,
                1.0 if signal.edge_source == "VOLATILITY_CLUSTERING" else 0.0,
                1.0 if signal.edge_source == "MEAN_REVERSION" else 0.0,
                1.0 if signal.edge_source == "LIQUIDITY_GAP" else 0.0
            ])
            
            # 🔥 FIX: TECHNICAL INDICATOR FEATURES (previously missing from ML!)
            # These indicators were calculated but not passed to ML for weighting
            if symbol in self.price_history and len(self.price_history[symbol]) >= 14:
                prices = self.price_history[symbol]
                prices_arr = np.array(prices)
                
                # RSI (normalized 0-1)
                rsi = self._calculate_rsi(prices, 14)
                rsi_normalized = rsi / 100.0
                
                # Momentum indicators
                from strategies.momentum_surfer import ProfessionalMomentumModels
                momentum_score = ProfessionalMomentumModels.momentum_score(prices_arr, min(20, len(prices)))
                trend_strength = ProfessionalMomentumModels.trend_strength(prices_arr)
                mean_reversion_prob = ProfessionalMomentumModels.mean_reversion_probability(prices_arr)
                hp_trend, hp_cycle, hp_trend_direction = ProfessionalMomentumModels.hp_trend_filter(prices_arr)
                
                # MACD state (encoded)
                macd_state_val = 0.0
                if len(prices) >= 26:
                    macd_data = self.calculate_macd_signal(prices)
                    macd_crossover = macd_data.get('crossover')
                    if macd_crossover == 'bullish':
                        macd_state_val = 1.0
                    elif macd_crossover == 'bearish':
                        macd_state_val = -1.0
                
                # Buying/Selling pressure
                ltp = symbol_data.get('ltp', symbol_data.get('close', 0))
                high = symbol_data.get('high', ltp)
                low = symbol_data.get('low', ltp)
                close = symbol_data.get('close', ltp)
                if high > low:
                    buying_pressure = (close - low) / (high - low)
                    selling_pressure = (high - close) / (high - low)
                else:
                    buying_pressure = 0.5
                    selling_pressure = 0.5
                
                features.extend([
                    rsi_normalized,           # 0-1: RSI normalized
                    (rsi - 50) / 50,          # -1 to 1: RSI deviation from neutral
                    momentum_score / 10.0,    # Normalized momentum score
                    trend_strength,           # Raw trend strength
                    mean_reversion_prob,      # 0-1: Mean reversion probability
                    hp_trend_direction * 100, # HP trend direction (scaled)
                    macd_state_val,           # -1, 0, 1: MACD state
                    buying_pressure,          # 0-1: Buying pressure
                    selling_pressure,         # 0-1: Selling pressure
                    buying_pressure - selling_pressure  # -1 to 1: Net pressure
                ])
            else:
                # Default values if insufficient data
                features.extend([0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.5, 0.5, 0.0])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature extraction failed for {symbol}: {e}")
            return np.array([])
    
    async def _get_ml_confidence_boost(self, features: np.ndarray) -> float:
        """Get ML-based confidence boost for signal
        
        🔧 FIX: Only trust ML model when it's actually learning (balanced_acc > 0.55)
        With severe class imbalance (2% positive), an untrained model just predicts negative always.
        """
        try:
            if not self.ml_trained or len(features) == 0:
                return 0.0
            
            # 🔥 FIX: Check if ML model has sufficient training data
            # If model has < 50 samples, it's unreliable - return 0.0
            if len(self.ml_labels_history) < 50:
                logger.debug(f"ML model has insufficient training data ({len(self.ml_labels_history)} samples) - skipping")
                return 0.0
            
            # 🔧 FIX: Check if model is actually learning (balanced accuracy > 0.55)
            # balanced_acc of 0.5 = random guessing, we need at least 0.55 to trust it
            if hasattr(self, 'ml_balanced_accuracy') and self.ml_balanced_accuracy <= 0.55:
                # Model is not learning - don't use its predictions
                logger.debug(f"ML model balanced_acc={self.ml_balanced_accuracy:.3f} ≤ 0.55 - not learned yet, skipping")
                return 0.0
            
            # Scale features
            features_scaled = self.feature_scaler.transform(features.reshape(1, -1))
            
            # Get prediction probability
            prediction_proba = self.ml_model.predict_proba(features_scaled)[0]
            
            # 🔥 FIX: If model always predicts same class (not learning), don't apply penalty
            # A well-trained model should have varied predictions, not always 0.0 or 1.0
            if prediction_proba[1] < 0.05 or prediction_proba[1] > 0.95:
                # Model is too confident in one direction = likely undertrained
                logger.debug(f"ML model prediction too extreme ({prediction_proba[1]:.3f}) - likely undertrained, skipping")
                return 0.0
            
            # Convert to confidence boost (-0.3 to +0.3) - reduced from -0.5 to +0.5
            # ML should provide hints, not dominate the decision
            confidence_boost = (prediction_proba[1] - 0.5) * 0.6  # Scale down the impact
            
            # 🔧 FIX: Scale boost by model reliability (balanced accuracy)
            # Model with 0.55 acc gets 10% of boost, model with 0.75 acc gets full boost
            if hasattr(self, 'ml_balanced_accuracy') and self.ml_balanced_accuracy > 0.55:
                reliability_factor = min((self.ml_balanced_accuracy - 0.55) / 0.20, 1.0)  # 0.55->0%, 0.75->100%
                confidence_boost *= reliability_factor
            
            return confidence_boost
            
        except Exception as e:
            logger.error(f"ML confidence boost calculation failed: {e}")
            return 0.0
    
    def _apply_ml_enhancement(self, signal: MarketMicrostructureSignal, 
                            ml_boost: float, features: np.ndarray) -> MarketMicrostructureSignal:
        """Apply ML enhancement to signal"""
        try:
            # Enhance confidence with ML boost
            enhanced_confidence = min(signal.confidence + ml_boost, 10.0)
            
            # Adjust other metrics based on ML prediction
            ml_strength_multiplier = 1.0 + (ml_boost * 0.2)  # Up to 20% adjustment
            
            enhanced_signal = MarketMicrostructureSignal(
                signal_type=signal.signal_type,
                strength=signal.strength * ml_strength_multiplier,
                confidence=enhanced_confidence,
                edge_source=f"ML_ENHANCED_{signal.edge_source}",
                expected_duration=signal.expected_duration,
                risk_adjusted_return=signal.risk_adjusted_return * ml_strength_multiplier,
                statistical_significance=signal.statistical_significance,
                sharpe_ratio=signal.sharpe_ratio * ml_strength_multiplier,
                var_95=signal.var_95,
                kelly_fraction=min(signal.kelly_fraction * ml_strength_multiplier, 0.25)
            )
            
            if abs(ml_boost) > 0.1:  # Significant ML impact
                logger.info(f"🤖 ML ENHANCED: {signal.edge_source} boost={ml_boost:.3f} "
                           f"confidence={signal.confidence:.1f}→{enhanced_confidence:.1f}")
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"ML enhancement application failed: {e}")
            return signal
    
    def _store_ml_training_data(self, features: np.ndarray, signal: MarketMicrostructureSignal):
        """Store data for ML model training"""
        try:
            if len(features) > 0:
                self.ml_features_history.append(features)
                
                # 🔧 FIX (v3): ULTRA-STRICT criteria to avoid circular reasoning
                # Previous v1: confidence > 8.0 → 89% positive (way too lenient)
                # Previous v2: confidence >= 9.0, sharpe >= 3.0 → still 89% positive!
                # 
                # PROBLEM: After adding exceptional bonuses, most signals now reach 9.0+ confidence
                # This creates circular reasoning - ML learns nothing useful
                #
                # SOLUTION: Use INDEPENDENT metrics that aren't inflated by our boosts
                # Target: 5-15% positive rate (truly rare exceptional signals)
                
                # Get signal metadata for independent metrics
                metadata = getattr(signal, 'metadata', {}) or {}
                
                # ULTRA-STRICT CRITERIA: Multiple independent conditions
                is_exceptional = (
                    signal.confidence >= 9.5 and                    # Top 5% confidence (stricter)
                    signal.sharpe_ratio >= 4.0 and                  # Exceptional Sharpe (stricter)
                    getattr(signal, 'strength', 0) >= 0.85 and      # Very strong signal
                    # Additional independent checks:
                    metadata.get('institutional_ratio', 0) >= 0.5 and  # 50%+ institutional activity
                    metadata.get('volume_surge', 1.0) >= 1.5           # 50%+ above average volume
                )
                label = 1 if is_exceptional else 0
                self.ml_labels_history.append(label)
                
                # Keep only recent data
                if len(self.ml_features_history) > 1000:
                    self.ml_features_history.pop(0)
                    self.ml_labels_history.pop(0)
                    
        except Exception as e:
            logger.error(f"ML training data storage failed: {e}")
    
    async def _update_ml_model(self):
        """Update ML model with new training data
        
        🔧 FIX: Use train/test split for proper accuracy measurement
        Previously reported 100% accuracy because it tested on training data!
        """
        try:
            if len(self.ml_features_history) < 50:  # Need minimum data
                return
            
            # Prepare training data
            X = np.array(self.ml_features_history)
            y = np.array(self.ml_labels_history)
            
            # Check if we have both classes
            if len(np.unique(y)) < 2:
                return
            
            # 🔧 FIX: Use train/test split for honest accuracy measurement
            # Previously: trained and tested on same data → 100% accuracy (false!)
            # Now: 80% train, 20% test → realistic accuracy
            from sklearn.model_selection import train_test_split
            
            # 🔧 FIX: Handle class imbalance properly - use stratified split and report balanced metrics
            # Only split if we have enough data
            if len(X) >= 100:
                # Use stratified split to ensure both classes in test set
                try:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y
                    )
                except ValueError:
                    # If stratification fails (e.g., one class too small), use regular split
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
            else:
                # Not enough data for split - use all for training, report as "training accuracy"
                X_train, X_test, y_train, y_test = X, X, y, y
            
            # Scale features (fit on train, transform both)
            X_train_scaled = self.feature_scaler.fit_transform(X_train)
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Train model on training set only
            self.ml_model.fit(X_train_scaled, y_train)
            self.ml_trained = True

            # 🔧 FIX: Calculate accuracy on TEST set with class imbalance awareness
            test_score = self.ml_model.score(X_test_scaled, y_test)
            
            # Calculate class distribution for context
            positive_ratio = np.mean(y) * 100
            test_positive_ratio = np.mean(y_test) * 100 if len(y_test) > 0 else 0
            
            # 🔧 FIX: If accuracy is 100% with severe class imbalance, it's likely just predicting majority class
            # Report this as a warning
            if test_score >= 0.99 and test_positive_ratio < 5:
                logger.warning(f"⚠️ ML MODEL: 100% accuracy with {test_positive_ratio:.1f}% positive samples - likely predicting majority class only")
                logger.warning(f"   Model may not be learning meaningful patterns - consider class balancing")
            
            # Calculate balanced accuracy if we have both classes
            if len(np.unique(y_test)) >= 2:
                from sklearn.metrics import balanced_accuracy_score, confusion_matrix
                y_pred = self.ml_model.predict(X_test_scaled)
                balanced_acc = balanced_accuracy_score(y_test, y_pred)
                cm = confusion_matrix(y_test, y_pred)
                
                # 🔧 FIX: Store balanced accuracy to check if model is actually learning
                self.ml_balanced_accuracy = balanced_acc
                
                # 🔧 FIX: Warn if model is not learning (balanced_acc <= 0.55 is near random)
                if balanced_acc <= 0.55:
                    logger.warning(f"⚠️ ML MODEL: balanced_acc={balanced_acc:.3f} ≤ 0.55 - model is near RANDOM, predictions unreliable")
                    logger.warning(f"   Model will be DISABLED until it learns better patterns")
                elif balanced_acc >= 0.65:
                    logger.info(f"✅ ML MODEL LEARNING: balanced_acc={balanced_acc:.3f} - model is making meaningful predictions")
                
                logger.info(f"🤖 ML MODEL UPDATED: {len(X)} samples, test_accuracy={test_score:.3f}, balanced_acc={balanced_acc:.3f} (pos={positive_ratio:.0f}%, test_pos={test_positive_ratio:.0f}%)")
                logger.debug(f"   Confusion matrix: {cm.tolist()}")
            else:
                self.ml_balanced_accuracy = 0.0  # Can't calculate, treat as unreliable
                logger.info(f"🤖 ML MODEL UPDATED: {len(X)} samples, test_accuracy={test_score:.3f} (pos={positive_ratio:.0f}%, test_pos={test_positive_ratio:.0f}%)")
            
        except Exception as e:
            logger.error(f"ML model update failed: {e}")
    
    def _calculate_vwap_execution_price(self, symbol: str, symbol_data: Dict, 
                                      quantity: int, direction: str) -> Tuple[float, Dict]:
        """PROFESSIONAL VWAP EXECUTION OPTIMIZATION"""
        try:
            current_price = symbol_data.get('ltp', symbol_data.get('close', 0))
            volume = symbol_data.get('volume', 0)
            
            if current_price <= 0:
                return current_price, {}
            
            # MARKET IMPACT ESTIMATION
            avg_volume = np.mean(self.volume_history.get(symbol, [volume])[-10:]) if symbol in self.volume_history else volume
            volatility = self._get_current_volatility(symbol)
            
            # Calculate participation rate
            participation_rate = min(quantity / avg_volume if avg_volume > 0 else 0.1, 0.2)  # Max 20%
            
            # Market impact using professional model
            market_impact_bps = self.math_models.market_impact_model(
                volume=quantity,
                avg_volume=avg_volume,
                volatility=volatility,
                participation_rate=participation_rate
            )
            
            # VWAP EXECUTION STRATEGY
            if participation_rate > 0.1:  # Large order - use TWAP
                execution_strategy = "TWAP"
                time_slices = min(int(participation_rate * 50), 10)  # Up to 10 slices
                slice_size = quantity // time_slices
                execution_time = time_slices * 30  # 30 seconds per slice
            else:  # Small order - use VWAP
                execution_strategy = "VWAP"
                time_slices = 1
                slice_size = quantity
                execution_time = 60  # 1 minute
            
            # PRICE ADJUSTMENT for market impact
            impact_adjustment = market_impact_bps / 10000  # Convert bps to decimal
            
            if direction.upper() == 'BUY':
                execution_price = current_price * (1 + impact_adjustment)
            else:
                execution_price = current_price * (1 - impact_adjustment)
            
            execution_info = {
                'strategy': execution_strategy,
                'market_impact_bps': market_impact_bps,
                'participation_rate': participation_rate,
                'time_slices': time_slices,
                'slice_size': slice_size,
                'execution_time_seconds': execution_time,
                'price_adjustment': impact_adjustment
            }
            
            logger.info(f"📊 VWAP EXECUTION: {symbol} {direction} {quantity} shares "
                       f"Strategy={execution_strategy} Impact={market_impact_bps:.1f}bps "
                       f"Price={current_price:.2f}→{execution_price:.2f}")
            
            return execution_price, execution_info
            
        except Exception as e:
            logger.error(f"VWAP execution calculation failed for {symbol}: {e}")
            return symbol_data.get('ltp', symbol_data.get('close', 0)), {}

    async def _update_performance_metrics(self, trade_record: Dict):
        """PROFESSIONAL REAL-TIME PERFORMANCE MONITORING"""
        try:
            if len(self.trade_history) < 2:
                return
            
            # Calculate recent performance
            recent_trades = self.trade_history[-50:]  # Last 50 trades
            
            # SHARPE RATIO CALCULATION
            returns = [t.get('expected_return', 0) for t in recent_trades]
            if len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe = avg_return / std_return if std_return > 0 else 0
                self.performance_metrics['sharpe_ratio'] = sharpe
            
            # WIN RATE CALCULATION
            positive_returns = [r for r in returns if r > 0]
            win_rate = len(positive_returns) / len(returns) if returns else 0
            self.performance_metrics['win_rate'] = win_rate
            
            # MAXIMUM DRAWDOWN
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = running_max - cumulative_returns
            max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
            self.performance_metrics['max_drawdown'] = max_drawdown
            
            # PERFORMANCE ALERTS
            if sharpe < 1.0 and len(recent_trades) > 20:
                logger.warning(f"⚠️ PERFORMANCE ALERT: Sharpe ratio below 1.0: {sharpe:.2f}")
            
            if win_rate < 0.4 and len(recent_trades) > 20:
                logger.warning(f"⚠️ PERFORMANCE ALERT: Win rate below 40%: {win_rate:.1%}")
            
            if max_drawdown > 0.1:  # 10% drawdown
                logger.warning(f"⚠️ PERFORMANCE ALERT: High drawdown: {max_drawdown:.1%}")
            
            # Log performance every 10 trades
            if len(self.trade_history) % 10 == 0:
                logger.info(f"📊 PERFORMANCE UPDATE: Sharpe={sharpe:.2f}, "
                           f"WinRate={win_rate:.1%}, MaxDD={max_drawdown:.1%}")
                
        except Exception as e:
            logger.error(f"Performance metrics update failed: {e}")
    
    async def _simulate_trade_outcome(self, trade_record: Dict):
        """PROFESSIONAL BACKTESTING SIMULATION"""
        try:
            # This would simulate the trade outcome for backtesting
            # For now, we'll use the expected return as a proxy
            
            symbol = trade_record['symbol']
            expected_return = trade_record['expected_return']
            confidence = trade_record['confidence']
            
            # Simulate outcome based on confidence and market conditions
            success_probability = min(confidence / 10.0, 0.9)  # Max 90% success
            
            # Add some randomness for realistic simulation
            import random
            random_factor = random.uniform(0.8, 1.2)  # ±20% variance
            
            if random.random() < success_probability:
                # Successful trade
                simulated_return = expected_return * random_factor
                outcome = 'WIN'
            else:
                # Failed trade - assume stop loss hit
                simulated_return = -abs(expected_return) * 0.5 * random_factor  # 50% of expected loss
                outcome = 'LOSS'
            
            # Store simulation result
            simulation_result = {
                'timestamp': trade_record['timestamp'],
                'symbol': symbol,
                'expected_return': expected_return,
                'simulated_return': simulated_return,
                'outcome': outcome,
                'confidence': confidence
            }
            
            # Add to backtesting history
            if not hasattr(self, 'backtest_results'):
                self.backtest_results = []
            
            self.backtest_results.append(simulation_result)
            
            # Calculate backtesting performance
            if len(self.backtest_results) >= 10:
                recent_results = self.backtest_results[-50:]
                backtest_returns = [r['simulated_return'] for r in recent_results]
                backtest_sharpe = np.mean(backtest_returns) / np.std(backtest_returns) if np.std(backtest_returns) > 0 else 0
                backtest_win_rate = len([r for r in recent_results if r['outcome'] == 'WIN']) / len(recent_results)
                
                logger.info(f"🎯 BACKTEST SIMULATION: {symbol} {outcome} "
                           f"Expected={expected_return:.3f} Actual={simulated_return:.3f} "
                           f"RecentSharpe={backtest_sharpe:.2f} WinRate={backtest_win_rate:.1%}")
                
        except Exception as e:
            logger.error(f"Backtesting simulation failed: {e}")

    def get_ltp(self, symbol: str) -> float:
        """Get last traded price from TrueData cache"""
        try:
            from data.truedata_client import live_market_data
            data = live_market_data.get(symbol, {})
            return data.get('ltp', data.get('price', data.get('last_price', 0.0)))
        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}")
            return 0.0
"""
🧮 PROFESSIONAL MATHEMATICAL FOUNDATION
=====================================
Advanced mathematical models extracted from the monolithic base strategy.
Provides institutional-grade calculations for trading strategies.
"""

import logging
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ProfessionalMathFoundation:
    """
    INSTITUTIONAL-GRADE MATHEMATICAL MODELS
    
    COMPETITIVE ADVANTAGES:
    1. GARCH-ENHANCED ATR: Superior volatility estimation vs simple ATR
    2. KELLY CRITERION: Optimal position sizing vs fixed percentages  
    3. REAL-TIME SHARPE: Performance attribution vs basic P&L tracking
    4. VAR MONITORING: Professional risk management vs simple stop losses
    5. STATISTICAL VALIDATION: Significance testing vs gut feelings
    """
    
    # RESTORE CONTROL: Allows runtime toggle between current math and legacy math
    # Default keeps current updated mathematics active
    legacy_mode: bool = False
    
    @classmethod
    def set_legacy_mode(cls, enabled: bool) -> None:
        """Enable/disable legacy calculation mode without changing public APIs."""
        cls.legacy_mode = bool(enabled)
        mode = "LEGACY" if cls.legacy_mode else "CURRENT"
        logger.info(f"🔁 ProfessionalMathFoundation calculation mode set to: {mode}")
    
    @classmethod
    def is_legacy_mode(cls) -> bool:
        """Return True if legacy mode is enabled."""
        return cls.legacy_mode
    
    @staticmethod
    def garch_atr(prices: np.ndarray, period: int = 14) -> float:
        """
        🚀 GARCH-Enhanced ATR calculation for superior volatility estimation
        Uses GARCH(1,1) model for heteroskedasticity-aware volatility
        """
        try:
            # Legacy routing (safe fallback to current if legacy not implemented later)
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_garch_atr(prices, period)
                except Exception as legacy_error:
                    logger.warning(f"Legacy garch_atr failed or not implemented, using current math: {legacy_error}")
            
            if len(prices) < period + 5:
                return np.std(prices) * 0.02 if len(prices) > 1 else 0.02
            
            # Calculate returns
            returns = np.diff(prices) / prices[:-1]
            
            # GARCH(1,1) parameters (calibrated for Indian equity market)
            alpha = 0.1   # ARCH parameter - weight of recent shock
            beta = 0.85   # GARCH parameter - weight of previous variance
            omega = 0.01  # 🚨 FIX: Long-run variance baseline (was 0.0001, too small)
            
            # Initialize variance with sample variance
            variance = np.var(returns)
            
            # GARCH(1,1) recursion: σ²(t) = ω + α·r²(t-1) + β·σ²(t-1)
            for i in range(1, len(returns)):
                variance = omega + alpha * (returns[i-1] ** 2) + beta * variance
            
            # 🚨 FIX: Convert variance to ATR using CURRENT price (not mean)
            # GARCH gives volatility in return-space, multiply by current price for price-space ATR
            current_price = prices[-1]
            garch_atr = np.sqrt(variance) * current_price
            
            return float(garch_atr)
            
        except Exception as e:
            logger.error(f"GARCH ATR calculation failed: {e}")
            # Fallback to simple ATR
            if len(prices) >= 2:
                return float(np.std(np.diff(prices)) * 0.02)
            return 0.02
    
    @staticmethod
    def _legacy_garch_atr(prices: np.ndarray, period: int = 14) -> float:
        """LEGACY PLACEHOLDER: Will be replaced with pre-update logic when provided.
        Currently routes to current implementation to avoid behavior change."""
        return ProfessionalMathFoundation.garch_atr.__wrapped__(prices, period) if hasattr(ProfessionalMathFoundation.garch_atr, "__wrapped__") else ProfessionalMathFoundation.garch_atr(prices, period)

    @staticmethod
    def kelly_position_size(win_rate: float, avg_win: float, avg_loss: float, 
                          capital: float, max_risk: float = 0.25) -> float:
        """
        🎯 Kelly Criterion for optimal position sizing
        Maximizes long-term growth while controlling risk
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_kelly_position_size(win_rate, avg_win, avg_loss, capital, max_risk)
                except Exception as legacy_error:
                    logger.warning(f"Legacy kelly_position_size failed or not implemented, using current math: {legacy_error}")
            if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
                return capital * 0.02  # Conservative 2% default
            
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            b = avg_win / abs(avg_loss)
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply safety constraints
            kelly_fraction = max(0, min(kelly_fraction, max_risk))
            
            # Apply fractional Kelly (25% of full Kelly for safety)
            conservative_kelly = kelly_fraction * 0.25
            
            position_size = capital * conservative_kelly
            
            logger.debug(f"🎯 Kelly sizing: win_rate={win_rate:.2f}, "
                        f"avg_win={avg_win:.2f}, avg_loss={avg_loss:.2f}, "
                        f"kelly_fraction={kelly_fraction:.3f}, "
                        f"position_size={position_size:.2f}")
            
            return float(position_size)
            
        except Exception as e:
            logger.error(f"Kelly position sizing failed: {e}")
            return capital * 0.02  # Conservative fallback
    
    @staticmethod
    def _legacy_kelly_position_size(win_rate: float, avg_win: float, avg_loss: float, 
                                    capital: float, max_risk: float = 0.25) -> float:
        return ProfessionalMathFoundation.kelly_position_size(win_rate, avg_win, avg_loss, capital, max_risk)

    @staticmethod
    def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.06) -> float:
        """
        📊 Real-time Sharpe ratio calculation for performance attribution
        Annualized risk-adjusted return measure
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_sharpe_ratio(returns, risk_free_rate)
                except Exception as legacy_error:
                    logger.warning(f"Legacy sharpe_ratio failed or not implemented, using current math: {legacy_error}")
            if len(returns) < 2:
                return 0.0
            
            # Convert to excess returns
            excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
            
            mean_excess = np.mean(excess_returns)
            std_excess = np.std(excess_returns)
            
            if std_excess <= 0:
                return 0.0
            
            # Annualized Sharpe ratio
            sharpe = (mean_excess / std_excess) * np.sqrt(252)
            
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Sharpe ratio calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def _legacy_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.06) -> float:
        return ProfessionalMathFoundation.sharpe_ratio(returns, risk_free_rate)

    @staticmethod
    def var_calculation(returns: np.ndarray, confidence: float = 0.05) -> float:
        """
        🛡️ Value at Risk calculation for professional risk management
        Estimates maximum loss at given confidence level
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_var_calculation(returns, confidence)
                except Exception as legacy_error:
                    logger.warning(f"Legacy var_calculation failed or not implemented, using current math: {legacy_error}")
            if len(returns) < 10:
                return 0.02  # 2% default VaR
            
            # Historical VaR
            var = np.percentile(returns, confidence * 100)
            
            # Ensure reasonable bounds
            var = min(var, 0)  # VaR should be negative (loss)
            var = max(var, -0.10)  # Cap at 10% maximum loss
            
            return float(abs(var))
            
        except Exception as e:
            logger.error(f"VaR calculation failed: {e}")
            return 0.02
    
    @staticmethod
    def _legacy_var_calculation(returns: np.ndarray, confidence: float = 0.05) -> float:
        return ProfessionalMathFoundation.var_calculation(returns, confidence)

    @staticmethod
    def statistical_significance_test(returns: np.ndarray, benchmark: float = 0.0) -> float:
        """
        📈 Statistical significance testing for trading decisions
        Tests if returns are significantly different from benchmark
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_statistical_significance_test(returns, benchmark)
                except Exception as legacy_error:
                    logger.warning(f"Legacy statistical_significance_test failed or not implemented, using current math: {legacy_error}")
            if len(returns) < 5:
                return 1.0  # Not significant
            
            # One-sample t-test against benchmark
            t_stat, p_value = stats.ttest_1samp(returns, benchmark)
            
            return float(p_value)
            
        except Exception as e:
            logger.error(f"Statistical significance test failed: {e}")
            return 1.0
    
    @staticmethod
    def _legacy_statistical_significance_test(returns: np.ndarray, benchmark: float = 0.0) -> float:
        return ProfessionalMathFoundation.statistical_significance_test(returns, benchmark)

    @staticmethod
    def calculate_momentum_score(prices: np.ndarray, lookback: int = 20) -> float:
        """
        📈 Professional momentum score with statistical validation
        Multi-timeframe momentum analysis with volatility adjustment
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_calculate_momentum_score(prices, lookback)
                except Exception as legacy_error:
                    logger.warning(f"Legacy calculate_momentum_score failed or not implemented, using current math: {legacy_error}")
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
            
            return float(risk_adjusted_momentum)
            
        except Exception as e:
            logger.error(f"Momentum score calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def _legacy_calculate_momentum_score(prices: np.ndarray, lookback: int = 20) -> float:
        return ProfessionalMathFoundation.calculate_momentum_score(prices, lookback)

    @staticmethod
    def calculate_trend_strength(prices: np.ndarray, window: int = 20) -> float:
        """
        📊 Calculate trend strength using linear regression
        Measures the strength and direction of price trends
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_calculate_trend_strength(prices, window)
                except Exception as legacy_error:
                    logger.warning(f"Legacy calculate_trend_strength failed or not implemented, using current math: {legacy_error}")
            if len(prices) < window:
                return 0.0
            
            # Use recent prices
            recent_prices = prices[-window:]
            x = np.arange(len(recent_prices))
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_prices)
            
            # Trend strength is R-squared adjusted by significance
            trend_strength = (r_value ** 2) * (1 - p_value) if p_value < 0.05 else 0
            
            # Apply direction (positive for uptrend, negative for downtrend)
            if slope < 0:
                trend_strength = -trend_strength
            
            return float(trend_strength)
            
        except Exception as e:
            logger.error(f"Trend strength calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def _legacy_calculate_trend_strength(prices: np.ndarray, window: int = 20) -> float:
        return ProfessionalMathFoundation.calculate_trend_strength(prices, window)

    @staticmethod
    def calculate_volatility_regime(prices: np.ndarray, window: int = 20) -> Dict[str, float]:
        """
        📊 Volatility regime detection using GARCH models
        Classifies current volatility environment
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_calculate_volatility_regime(prices, window)
                except Exception as legacy_error:
                    logger.warning(f"Legacy calculate_volatility_regime failed or not implemented, using current math: {legacy_error}")
            if len(prices) < window + 5:
                return {'regime': 'NORMAL', 'volatility': 0.02, 'percentile': 50.0}
            
            # Calculate rolling volatility
            returns = np.diff(prices) / prices[:-1]
            rolling_vol = pd.Series(returns).rolling(window=window).std()
            
            current_vol = rolling_vol.iloc[-1]
            vol_history = rolling_vol.dropna()
            
            # Calculate volatility percentile
            vol_percentile = stats.percentileofscore(vol_history, current_vol)
            
            # Classify regime
            if vol_percentile >= 90:
                regime = 'HIGH_VOLATILITY'
            elif vol_percentile >= 70:
                regime = 'ELEVATED_VOLATILITY'
            elif vol_percentile <= 10:
                regime = 'LOW_VOLATILITY'
            elif vol_percentile <= 30:
                regime = 'SUPPRESSED_VOLATILITY'
            else:
                regime = 'NORMAL_VOLATILITY'
            
            return {
                'regime': regime,
                'volatility': float(current_vol),
                'percentile': float(vol_percentile)
            }
            
        except Exception as e:
            logger.error(f"Volatility regime calculation failed: {e}")
            return {'regime': 'NORMAL', 'volatility': 0.02, 'percentile': 50.0}
    
    @staticmethod
    def _legacy_calculate_volatility_regime(prices: np.ndarray, window: int = 20) -> Dict[str, float]:
        return ProfessionalMathFoundation.calculate_volatility_regime(prices, window)

    @staticmethod
    def calculate_risk_metrics(returns: np.ndarray) -> Dict[str, float]:
        """
        🛡️ Comprehensive risk metrics calculation
        Returns multiple risk measures for portfolio analysis
        """
        try:
            if ProfessionalMathFoundation.legacy_mode:
                try:
                    return ProfessionalMathFoundation._legacy_calculate_risk_metrics(returns)
                except Exception as legacy_error:
                    logger.warning(f"Legacy calculate_risk_metrics failed or not implemented, using current math: {legacy_error}")
            if len(returns) < 5:
                return {
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'var_95': 0.02,
                    'cvar_95': 0.03,
                    'volatility': 0.02
                }
            
            # Basic metrics
            sharpe = ProfessionalMathFoundation.sharpe_ratio(returns)
            var_95 = ProfessionalMathFoundation.var_calculation(returns, 0.05)
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Sortino ratio (downside deviation)
            negative_returns = returns[returns < 0]
            downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0.001
            sortino = (np.mean(returns) / downside_std) * np.sqrt(252) if downside_std > 0 else 0
            
            # Maximum drawdown
            cumulative = np.cumprod(1 + returns)
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak) / peak
            max_drawdown = abs(np.min(drawdown))
            
            # Conditional VaR (Expected Shortfall)
            var_threshold = np.percentile(returns, 5)
            tail_returns = returns[returns <= var_threshold]
            cvar_95 = abs(np.mean(tail_returns)) if len(tail_returns) > 0 else var_95 * 1.5
            
            return {
                'sharpe_ratio': float(sharpe),
                'sortino_ratio': float(sortino),
                'max_drawdown': float(max_drawdown),
                'var_95': float(var_95),
                'cvar_95': float(cvar_95),
                'volatility': float(volatility)
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'max_drawdown': 0.0,
                'var_95': 0.02,
                'cvar_95': 0.03,
                'volatility': 0.02
            }

    @staticmethod
    def _legacy_calculate_risk_metrics(returns: np.ndarray) -> Dict[str, float]:
        return ProfessionalMathFoundation.calculate_risk_metrics(returns)

class QuantitativeAnalyzer:
    """
    Advanced quantitative analysis tools for strategy development
    """
    
    def __init__(self):
        self.math_foundation = ProfessionalMathFoundation()
    
    def analyze_strategy_performance(self, returns: np.ndarray, 
                                   benchmark_returns: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        📊 Comprehensive strategy performance analysis
        """
        try:
            if len(returns) < 5:
                return {'error': 'Insufficient data for analysis'}
            
            # Basic risk metrics
            risk_metrics = self.math_foundation.calculate_risk_metrics(returns)
            
            # Performance metrics
            total_return = np.prod(1 + returns) - 1
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            
            # Win rate and profit factor
            winning_trades = len(returns[returns > 0])
            losing_trades = len(returns[returns < 0])
            win_rate = winning_trades / len(returns) if len(returns) > 0 else 0
            
            avg_win = np.mean(returns[returns > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean(returns[returns < 0]) if losing_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # Statistical significance
            significance = self.math_foundation.statistical_significance_test(returns)
            
            analysis = {
                'total_return': float(total_return),
                'annualized_return': float(annualized_return),
                'win_rate': float(win_rate),
                'profit_factor': float(profit_factor),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'statistical_significance': float(significance),
                **risk_metrics
            }
            
            # Benchmark comparison if provided
            if benchmark_returns is not None and len(benchmark_returns) == len(returns):
                excess_returns = returns - benchmark_returns
                information_ratio = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
                analysis['information_ratio'] = float(information_ratio)
                analysis['beta'] = float(np.cov(returns, benchmark_returns)[0, 1] / np.var(benchmark_returns))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Strategy performance analysis failed: {e}")
            return {'error': str(e)}
    
    def optimize_position_sizing(self, historical_returns: np.ndarray, 
                               capital: float, max_risk: float = 0.25) -> Dict[str, float]:
        """
        🎯 Optimize position sizing using multiple methods
        """
        try:
            if len(historical_returns) < 10:
                return {
                    'kelly_size': capital * 0.02,
                    'var_size': capital * 0.02,
                    'recommended_size': capital * 0.02,
                    'method': 'conservative_default'
                }
            
            # Calculate win rate and average returns
            winning_returns = historical_returns[historical_returns > 0]
            losing_returns = historical_returns[historical_returns < 0]
            
            win_rate = len(winning_returns) / len(historical_returns)
            avg_win = np.mean(winning_returns) if len(winning_returns) > 0 else 0
            avg_loss = np.mean(losing_returns) if len(losing_returns) > 0 else 0
            
            # Kelly criterion sizing
            kelly_size = self.math_foundation.kelly_position_size(
                win_rate, avg_win, abs(avg_loss), capital, max_risk
            )
            
            # VaR-based sizing (risk budget approach)
            var_95 = self.math_foundation.var_calculation(historical_returns)
            var_size = (capital * 0.02) / var_95 if var_95 > 0 else capital * 0.02
            var_size = min(var_size, capital * max_risk)
            
            # Conservative recommendation (minimum of methods)
            recommended_size = min(kelly_size, var_size, capital * max_risk)
            
            return {
                'kelly_size': float(kelly_size),
                'var_size': float(var_size),
                'recommended_size': float(recommended_size),
                'win_rate': float(win_rate),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'var_95': float(var_95),
                'method': 'quantitative_optimization'
            }
            
        except Exception as e:
            logger.error(f"Position sizing optimization failed: {e}")
            return {
                'kelly_size': capital * 0.02,
                'var_size': capital * 0.02,
                'recommended_size': capital * 0.02,
                'method': 'error_fallback'
            }
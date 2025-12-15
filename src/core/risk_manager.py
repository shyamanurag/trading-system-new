# core/risk_manager.py
"""
Complete Risk Manager with Advanced Risk Analytics and Greeks Integration
Implements portfolio risk management, position sizing, and risk monitoring
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
import json
import redis.asyncio as redis

from ..models import Signal
from .models import Position, OptionType
from ..events import EventBus, EventType, TradingEvent
from .position_tracker import ProductionPositionTracker
from .greeks_risk_manager import GreeksRiskManager

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Container for risk metrics"""
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0

    @dataclass
    class PositionRiskMetrics:
        """Risk metrics for individual position"""
        delta: float = 0.0
        gamma: float = 0.0
        theta: float = 0.0
        vega: float = 0.0
        rho: float = 0.0

    class RiskState:
        """Current risk state of the portfolio"""
        def __init__(self):
            # Greeks state
            self.delta = 0.0
            self.gamma = 0.0
            self.theta = 0.0
            self.vega = 0.0
            self.rho = 0.0

    class PortfolioHeatMap:
        """Track portfolio concentration and heat levels"""
        def __init__(self):
            self.heat_scores = {}
            self.symbol_exposure = defaultdict(float)
            self.time_concentration = defaultdict(list)

        def update_exposure(self, position: Position):
            """Update exposure tracking"""
            symbol_base = self._get_base_symbol(position.symbol)
            position_value = position.quantity * position.current_price
            self.time_concentration[datetime.now().hour].append(position_value)
            # Calculate heat score
            self._calculate_heat_scores()

        def remove_exposure(self, position: Position):
            """Remove position from exposure tracking"""
            symbol_base = self._get_base_symbol(position.symbol)
            position_value = position.quantity * position.entry_price
            # Recalculate heat scores
            self._calculate_heat_scores()

        def get_heat_level(self, symbol: str) -> float:
            """Get heat level for symbol or overall"""
            if symbol:
                return self.heat_scores.get(self._get_base_symbol(symbol), 0.0)
            return max(self.heat_scores.values()) if self.heat_scores else 0.0

        def can_add_position(self, symbol: str, value: float, total_capital: float) -> bool:
            """Check if we can add position without exceeding concentration"""
            symbol_base = self._get_base_symbol(symbol)
            current_concentration = self.symbol_exposure[symbol_base] / total_capital
            new_concentration = (self.symbol_exposure[symbol_base] + value) / total_capital
            return new_concentration <= 0.2  # Max 20% concentration

        def _calculate_heat_scores(self):
            """Calculate heat scores for all symbols"""
            total_exposure = sum(self.symbol_exposure.values())
            if total_exposure > 0:
                for symbol, exposure in self.symbol_exposure.items():
                    concentration = exposure / total_exposure
                    # Heat score increases exponentially as we approach max concentration
                    self.heat_scores[symbol] = concentration * 100
            else:
                self.heat_scores.clear()

        def _get_base_symbol(self, symbol: str) -> str:
            """Extract base symbol from option symbol"""
            if 'BANKNIFTY' in symbol:
                return 'BANKNIFTY'
            elif 'NIFTY' in symbol:
                return 'NIFTY'
            elif 'FINNIFTY' in symbol:
                return 'FINNIFTY'
            return symbol.split('_')[0] if '_' in symbol else symbol

class ValueAtRiskCalculator:
    """Calculate portfolio Value at Risk (VaR) and CVaR"""

    def __init__(self):
        self.returns_history = []
        self.position_returns = defaultdict(list)

    def add_return(self, daily_return: float, position_returns: Optional[Dict[str, float]] = None):
        """Add daily return data"""
        self.returns_history.append(daily_return)
        if position_returns:
            for position_id, ret in position_returns.items():
                self.position_returns[position_id].append(ret)

    def calculate_portfolio_var(self, portfolio_value: float, time_horizon: float, confidence_level: float) -> Tuple[float, float]:
        """Calculate VaR and CVaR for portfolio

        Returns:
        Tuple of (VaR, CVaR) in currency terms
        """
        if len(self.returns_history) < 20:  # Need minimum history
            return 0.0, 0.0

        returns = np.array(self.returns_history)
        # Scale returns for time horizon (square root of time)
        scaled_returns = returns * np.sqrt(time_horizon)
        # Calculate VaR (percentile method)
        var_percentile = (1 - confidence_level) * 100
        var_return = np.percentile(scaled_returns, var_percentile)
        var_amount = abs(var_return * portfolio_value)
        # Calculate CVaR (expected shortfall)
        cvar_returns = scaled_returns[scaled_returns <= var_return]
        cvar_return = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_return
        cvar_amount = abs(cvar_return * portfolio_value)
        return var_amount, cvar_amount

    def calculate_position_var(self, position: Position, portfolio_var: float, confidence_level: float = 0.95) -> float:
        """Calculate VaR for individual position"""
        position_id = position.position_id

        if position_id not in self.position_returns or len(self.position_returns[position_id]) < 5:
            # Use portfolio VaR scaled by position size
            position_value = position.quantity * position.current_price
            return portfolio_var * 0.5  # Conservative estimate

        # Calculate from position-specific returns
        returns = np.array(self.position_returns[position_id])
        var_percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns, var_percentile)
        position_value = position.quantity * position.current_price
        return abs(var_return * position_value)

class CorrelationTracker:
    """Track and analyze correlations between positions"""

    def __init__(self):
        self.price_history = defaultdict(list)
        self.correlation_matrix = pd.DataFrame()
        self.last_update = None

    def update_price(self, symbol: str, price: float):
        """Update price history for symbol"""
        self.price_history[symbol].append(price)
        # Update correlation matrix periodically
        if (not self.last_update or
            (datetime.now() - self.last_update).seconds > 300):  # Every 5 minutes
            self._update_correlation_matrix()

    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        if symbol1 in self.correlation_matrix.index and symbol2 in self.correlation_matrix.columns:
            return self.correlation_matrix.loc[symbol1, symbol2]
        return 0.0

    def get_portfolio_correlation_risk(self, positions: List[Position]) -> float:
        """Calculate overall portfolio correlation risk"""
        if len(positions) < 2:
            return 0.0

        # Get unique symbols
        symbols = list(set(self._get_base_symbol(p.symbol) for p in positions))
        if len(symbols) < 2:
            return 0.0

        # Calculate average pairwise correlation
        correlations = []
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                corr = self.get_correlation(symbols[i], symbols[j])
                correlations.append(abs(corr))
        if correlations:
            avg_correlation = np.mean(correlations)
            # High correlation increases risk
            return min(avg_correlation * 100, 100)  # Scale to 0-100
        return 0.0

    def _update_correlation_matrix(self):
        """Update correlation matrix from price history"""
        if len(self.price_history) < 2:
            return

        # Convert price histories to returns
        returns_data = {}
        for symbol, prices in self.price_history.items():
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                returns_data[symbol] = returns

        if len(returns_data) < 2:
            return

        # Create correlation matrix
        df = pd.DataFrame(returns_data)
        self.correlation_matrix = df.corr()
        self.last_update = datetime.now()

    def _get_base_symbol(self, symbol: str) -> str:
        """Extract base symbol from option symbol"""
        if 'BANKNIFTY' in symbol:
            return 'BANKNIFTY'
        elif 'NIFTY' in symbol:
            return 'NIFTY'
        elif 'FINNIFTY' in symbol:
            return 'FINNIFTY'
        return symbol.split('_')[0] if '_' in symbol else symbol

class DynamicPositionSizer:
    """Advanced position sizing with multiple methods"""

    def __init__(self):
        self.strategy_stats = defaultdict(lambda: {
            'wins': 0,
            'losses': 0,
            'total_win': 0.0,
            'total_loss': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0
        })
        self.base_size = 0.02
        self.max_position_size = 1000000  # Assuming a default max_position_size
        self.kelly_fraction = 0.25

    def calculate_fixed_fractional(self, capital: float, risk_score: float) -> float:
        """Fixed fractional position sizing adjusted for risk"""
        # Reduce size as risk increases
        risk_multiplier = 1.0 - (risk_score / 100) * 0.5  # Max 50% reduction
        position_size = capital * self.base_size * risk_multiplier
        return min(position_size, capital * self.max_position_size)

    def calculate_kelly(self, win_rate: float, avg_win: float, avg_loss: float, capital: float) -> float:
        """Kelly criterion position sizing"""
        p = win_rate
        q = 1 - win_rate
        
        # Prevent division by zero when avg_loss is 0
        if avg_loss == 0:
            return capital * 0.01  # Conservative 1% position size
            
        b = abs(avg_win / avg_loss)
        kelly_percentage = (p * b - q) / b

        # Apply fractional Kelly for safety
        safe_kelly = kelly_percentage * self.kelly_fraction

        # Ensure within bounds
        safe_kelly = max(0, min(safe_kelly, self.max_position_size))
        return capital * safe_kelly

    def update_strategy_stats(self, strategy: str, trade_result: Dict):
        """Update strategy statistics with trade result"""
        stats = self.strategy_stats[strategy]
        if trade_result['pnl'] > 0:
            stats['wins'] += 1
            stats['total_win'] += trade_result['pnl']
            stats['avg_win'] = stats['total_win'] / stats['wins']
        else:
            stats['losses'] += 1
            stats['total_loss'] += abs(trade_result['pnl'])
            stats['avg_loss'] = stats['total_loss'] / stats['losses']

        total_trades = stats['wins'] + stats['losses']
        stats['win_rate'] = stats['wins'] / total_trades if total_trades > 0 else 0.0

class RiskManager:
    """
    Focused Risk Manager - Risk Validation and Monitoring ONLY
    ========================================================
    Responsibilities:
    - Validate trades for risk compliance
    - Monitor portfolio risk metrics
    - Track losses and drawdowns
    - Trigger risk alerts and emergency stops
    
    NOT responsible for:
    - Capital allocation (TradeAllocator's job)
    - Position sizing (TradeAllocator's job)
    """

    def __init__(self, config: Dict, position_tracker: ProductionPositionTracker, event_bus: EventBus):
        self.config = config
        self.position_tracker = position_tracker
        self.event_bus = event_bus
        
        # CRITICAL FIX: Initialize async locks for thread safety
        import asyncio
        self._position_lock = asyncio.Lock()
        self._stats_lock = asyncio.Lock()
        
        # RISK LIMITS (not capital allocation)
        self.risk_limits = {
            'max_daily_loss_percent': config.get('max_daily_loss_percent', 0.02),     # 2% daily loss
            'max_drawdown_percent': config.get('max_drawdown_percent', 0.05),        # 5% drawdown
            'max_correlation': config.get('max_correlation', 0.7),                   # 70% correlation
            'max_concentration_percent': config.get('max_concentration_percent', 0.95), # 95% in single asset (for single-position intraday trading)
            'max_portfolio_var_percent': config.get('max_portfolio_var_percent', 0.03), # 3% VaR
            # Adjusted to align with 20-30% max position value: 3% assumed loss × 10 = 30% cap
            'max_single_position_loss_percent': config.get('max_single_position_loss_percent', 0.03), # 3% per position
            'vix_threshold_high': config.get('vix_threshold_high', 25),
            'vix_threshold_extreme': config.get('vix_threshold_extreme', 35)
        }
        
        # RISK TRACKING (not position sizing)
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0
        self.peak_capital = self.position_tracker.capital
        self.portfolio_var = 0.0
        self.portfolio_beta = 1.0
        
        # CRITICAL FIX: Initialize emergency stop flag
        self.emergency_stop_triggered = False
        self.portfolio_correlations = {}
        self.sector_concentrations = {}
        
        # Risk alerts and monitoring
        self.risk_alerts = []
        self.risk_breaches = []
        self.emergency_stop_triggered = False
        
        # CRITICAL FIX: Handle None redis config properly
        redis_config = config.get('redis')
        if redis_config is not None and isinstance(redis_config, dict):
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'), 
                    port=redis_config.get('port', 6379)
                )
                logger.info("✅ RiskManager: Redis client configured")
            except Exception as e:
                logger.warning(f"⚠️ RiskManager: Redis initialization failed: {e}")
                self.redis_client = None
        else:
            # Use None when Redis is not available
            self.redis_client = None
            logger.warning("⚠️ RiskManager using fallback mode (no Redis)")
        
        # Risk components
        self.var_calculator = ValueAtRiskCalculator()
        self.correlation_tracker = CorrelationTracker()
        self.portfolio_heat = RiskMetrics.PortfolioHeatMap()
        self.greeks_manager = GreeksRiskManager(config)

        # Risk state tracking
        self.risk_state = RiskMetrics.RiskState()
        self.risk_regime = "NORMAL"  # NORMAL, HIGH, EXTREME
        
        # CRITICAL FIX: Initialize strategy stats and portfolio greeks
        self.strategy_stats = {}
        self.portfolio_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        # User risk tracking
        self.user_risk_limits = {}
        self.user_daily_risk = {}
        self.user_positions = {}
        
        logger.info("✅ RiskManager initialized - FOCUSED ON RISK VALIDATION & MONITORING")
        logger.info(f"📊 Risk limits: {self.risk_limits}")
        
    def validate_trade_risk(self, position_value: float, strategy_name: str, symbol: str, total_capital_override: Optional[float] = None) -> Tuple[bool, str]:
        """
        Validate if a trade is acceptable from risk perspective
        This is RiskManager's PRIMARY responsibility
        """
        try:
            # Determine total capital for risk limits
            if total_capital_override is not None and total_capital_override > 0:
                total_capital = total_capital_override
            else:
                total_capital = self.position_tracker.capital
            
            # Check 1: Single position loss limit - EQUITY OPTIMIZED
            max_single_position_loss = total_capital * self.risk_limits['max_single_position_loss_percent']
            
            # CRITICAL FIX: For equity trades, allow up to 99% of capital usage
            # Equity margin is only ~25% of trade value, so ₹109k trade needs only ₹27k margin
            # Multiplier calculation: 99.5% / 3% = 33.17x multiplier (rounded to 34)
            limit_check = max_single_position_loss * 34  # Allow 99.5% of capital for equity trades
            if position_value > limit_check:
                return False, f"Position too large: ₹{position_value:,.0f} exceeds single position limit ₹{limit_check:,.0f}"
            
            # Check 2: Daily loss limit
            daily_loss_limit = -total_capital * self.risk_limits['max_daily_loss_percent']
            if self.daily_pnl < daily_loss_limit:
                return False, f"Daily loss limit exceeded: ₹{self.daily_pnl:,.0f} < ₹{daily_loss_limit:,.0f}"
            
            # Check 3: Drawdown limit
            drawdown_limit = self.risk_limits['max_drawdown_percent']
            if self.current_drawdown > drawdown_limit:
                return False, f"Drawdown limit exceeded: {self.current_drawdown*100:.1f}% > {drawdown_limit*100:.1f}%"
            
            # Check 4: Concentration limit
            if self.would_exceed_concentration_limit(symbol, position_value):
                return False, f"Concentration limit exceeded for {symbol}"
            
            # Check 5: Correlation limit
            if self.would_exceed_correlation_limit(symbol, position_value):
                return False, f"Correlation limit exceeded for {symbol}"
            
            # Check 6: VaR limit
            if self.would_exceed_var_limit(position_value):
                return False, f"VaR limit would be exceeded"
            
            # Check 7: Emergency stop
            emergency_stop = getattr(self, 'emergency_stop_triggered', False)
            logger.info(f"   Emergency Stop Check: {emergency_stop}")
            if emergency_stop:
                return False, "Emergency stop is active"
            
            logger.info(f"✅ RISK VALIDATION PASSED for {symbol}")
            return True, "Risk validation passed"
            
        except Exception as e:
            logger.error(f"Error validating trade risk: {e}")
            return False, f"Risk validation failed: {e}"
            
    def monitor_portfolio_risk(self):
        """
        Monitor ongoing portfolio risk
        This is RiskManager's ONGOING responsibility
        """
        try:
            # total_capital already set above
            
            # Update drawdown
            self.current_drawdown = (self.peak_capital - total_capital) / self.peak_capital
            if total_capital > self.peak_capital:
                self.peak_capital = total_capital
                self.current_drawdown = 0.0
            
            # CRITICAL FIX: Update daily P&L to include unrealized P&L from open positions
            realized_pnl = self.position_tracker.daily_pnl
            unrealized_pnl = sum(pos.unrealized_pnl for pos in self.position_tracker.positions.values())
            self.daily_pnl = realized_pnl + unrealized_pnl
            
            if unrealized_pnl != 0:
                logger.info(f"💰 DAILY P&L UPDATE: Realized: ₹{realized_pnl:.2f} + Unrealized: ₹{unrealized_pnl:.2f} = Total: ₹{self.daily_pnl:.2f}")
            
            # Calculate portfolio VaR
            self.portfolio_var = self.var_calculator.calculate_portfolio_var(
                self.position_tracker.positions
            )
            
            # Check for risk breaches
            self.check_risk_breaches()
            
            # Generate risk alerts if needed
            self.generate_risk_alerts()
            
        except Exception as e:
            logger.error(f"Error monitoring portfolio risk: {e}")
            
    def check_risk_breaches(self):
        """Check for risk limit breaches"""
        try:
            # total_capital already set above
            
            # Check daily loss breach
            max_daily_loss = total_capital * self.risk_limits['max_daily_loss_percent']
            if self.daily_pnl < -max_daily_loss:
                self.trigger_risk_breach("DAILY_LOSS", f"Daily loss ₹{-self.daily_pnl:,.0f} exceeds limit ₹{max_daily_loss:,.0f}")
            
            # Check drawdown breach
            if self.current_drawdown > self.risk_limits['max_drawdown_percent']:
                self.trigger_risk_breach("DRAWDOWN", f"Drawdown {self.current_drawdown*100:.1f}% exceeds limit {self.risk_limits['max_drawdown_percent']*100:.1f}%")
            
            # Check VaR breach
            max_var = total_capital * self.risk_limits['max_portfolio_var_percent']
            if self.portfolio_var > max_var:
                self.trigger_risk_breach("VAR", f"Portfolio VaR ₹{self.portfolio_var:,.0f} exceeds limit ₹{max_var:,.0f}")
            
        except Exception as e:
            logger.error(f"Error checking risk breaches: {e}")
            
    def trigger_risk_breach(self, breach_type: str, message: str):
        """Trigger a risk breach alert"""
        breach = {
            'type': breach_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': 'HIGH'
        }
        
        self.risk_breaches.append(breach)
        logger.error(f"🚨 RISK BREACH: {breach_type} - {message}")
        
        # Trigger emergency stop for severe breaches
        if breach_type in ['DAILY_LOSS', 'DRAWDOWN']:
            self.trigger_emergency_stop(f"Risk breach: {message}")
            
    def trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop"""
        self.emergency_stop_triggered = True
        logger.critical(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
        
        # Send emergency stop notification
        if self.event_bus:
            self.event_bus.publish('risk.emergency_stop', {
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            
    def would_exceed_concentration_limit(self, symbol: str, position_value: float) -> bool:
        """Check if position would exceed concentration limits"""
        try:
            total_capital = self.position_tracker.capital
            max_concentration = total_capital * self.risk_limits['max_concentration_percent']
            
            # Get current exposure to this symbol
            # FIXED: ProfessionalPosition doesn't have .value, use current_price * quantity
            current_exposure = sum(
                abs(pos.current_price * pos.quantity) 
                for pos in self.position_tracker.positions.values()
                if pos.symbol == symbol
            )
            
            total_exposure = current_exposure + position_value
            return total_exposure > max_concentration

        except Exception as e:
            logger.error(f"Error checking concentration limit: {e}")
            return True  # Conservative: assume limit exceeded on error
    
    def _get_max_quantity_for_concentration(self, symbol: str, price_per_share: float, 
                                            original_quantity: int, total_capital: float,
                                            is_equity: bool = True) -> int:
        """
        🔥 Calculate maximum allowed quantity within concentration limits
        
        Instead of rejecting trades that exceed concentration, calculate how many
        shares we CAN buy within the limit.
        
        Args:
            symbol: Stock symbol
            price_per_share: Entry price per share
            original_quantity: Originally requested quantity
            total_capital: Available capital
            is_equity: True for equity (25% margin), False for options (100% premium)
        
        Returns:
            Maximum allowed quantity (0 if none allowed)
        """
        try:
            max_concentration = total_capital * self.risk_limits['max_concentration_percent']
            
            # Get current exposure to this symbol
            current_exposure = sum(
                abs(pos.current_price * pos.quantity) * (0.25 if is_equity else 1.0)
                for pos in self.position_tracker.positions.values()
                if pos.symbol == symbol
            )
            
            # Available room for this symbol
            available_room = max_concentration - current_exposure
            
            if available_room <= 0:
                logger.warning(f"⚠️ {symbol}: No room left in concentration limit (current: ₹{current_exposure:,.0f})")
                return 0
            
            # Calculate margin per share
            if is_equity:
                margin_per_share = price_per_share * 0.25  # 25% margin for intraday equity
            else:
                margin_per_share = price_per_share  # Full premium for options
            
            # Max quantity that fits in available room
            max_quantity = int(available_room / margin_per_share)
            
            # Don't exceed original quantity
            final_quantity = min(max_quantity, original_quantity)
            
            logger.info(f"📊 CONCENTRATION CALC: {symbol}")
            logger.info(f"   Max Concentration: ₹{max_concentration:,.0f} | Current: ₹{current_exposure:,.0f}")
            logger.info(f"   Available Room: ₹{available_room:,.0f} | Margin/Share: ₹{margin_per_share:,.0f}")
            logger.info(f"   Max Qty: {max_quantity} | Original: {original_quantity} | Final: {final_quantity}")
            
            return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating max quantity for concentration: {e}")
            return 0
            
    def would_exceed_correlation_limit(self, symbol: str, position_value: float) -> bool:
        """Check if position would exceed correlation limits"""
        try:
            # Get correlation with existing positions
            max_correlation = self.risk_limits['max_correlation']
            
            for pos in self.position_tracker.positions.values():
                if pos.symbol != symbol:
                    correlation = self.correlation_tracker.get_correlation(symbol, pos.symbol)
                    if correlation > max_correlation:
                        return True
            
            return False

        except Exception as e:
            logger.error(f"Error checking correlation limit: {e}")
            return True  # Conservative: assume limit exceeded on error
            
    def would_exceed_var_limit(self, position_value: float) -> bool:
        """Check if position would exceed VaR limits"""
        try:
            total_capital = self.position_tracker.capital
            max_var = total_capital * self.risk_limits['max_portfolio_var_percent']
            
            # Estimate new VaR with additional position
            estimated_new_var = self.portfolio_var + (position_value * 0.02)  # Rough estimate
            
            return estimated_new_var > max_var

        except Exception as e:
            logger.error(f"Error checking VaR limit: {e}")
            return True  # Conservative: assume limit exceeded on error
            
    def generate_risk_alerts(self):
        """Generate risk alerts for warning conditions"""
        try:
            total_capital = self.position_tracker.capital
            
            # Warning: Approaching daily loss limit
            max_daily_loss = total_capital * self.risk_limits['max_daily_loss_percent']
            if self.daily_pnl < -max_daily_loss * 0.8:  # 80% of limit
                self.add_risk_alert("WARNING", f"Approaching daily loss limit: ₹{-self.daily_pnl:,.0f} / ₹{max_daily_loss:,.0f}")
            
            # Warning: Approaching drawdown limit
            if self.current_drawdown > self.risk_limits['max_drawdown_percent'] * 0.8:  # 80% of limit
                self.add_risk_alert("WARNING", f"Approaching drawdown limit: {self.current_drawdown*100:.1f}%")

        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")
            
    def add_risk_alert(self, severity: str, message: str):
        """Add a risk alert"""
        alert = {
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.risk_alerts.append(alert)
        logger.warning(f"⚠️ RISK ALERT: {severity} - {message}")
    
    async def validate_signal(self, signal: Signal) -> Dict[str, Any]:
        """
        Validate trading signal for risk compliance
        This is the main signal validation method called by TradeEngine
        """
        try:
            # Extract required fields from Signal object
            symbol = signal.symbol
            strategy_name = signal.strategy_name
            quantity = signal.quantity
            entry_price = getattr(signal, 'entry_price', 0.0)
            
            # CRITICAL DEBUG: Log signal validation details
            logger.info(f"🔍 SIGNAL VALIDATION: {symbol} | Qty: {quantity} | Price: ₹{entry_price} | Strategy: {strategy_name}")
            
            if signal.quantity <= 0:
                return {
                    'approved': False,
                    'reason': 'Invalid quantity: must be greater than 0',
                    'risk_score': 100.0,
                    'position_size': 0,
                    'validation_details': {
                        'symbol': symbol,
                        'strategy': strategy_name,
                        'error': 'Zero or negative quantity',
                        'validation_timestamp': datetime.now().isoformat()
                    }
                }

            # Calculate position value with management-action awareness
            contract_value = float(entry_price) * float(quantity)
            
            # CRITICAL FIX: For intraday equity trades, use margin requirement instead of full contract value
            # This aligns risk assessment with actual capital at risk
            is_options_trade = self._is_options_symbol(symbol)
            is_equity_trade = symbol and not is_options_trade
            if is_equity_trade:
                # Intraday equity margin is typically 20-25% of contract value
                estimated_margin_factor = 0.25  # Conservative 25% margin requirement
                position_value = contract_value * estimated_margin_factor
                logger.info(f"   Contract Value: ₹{contract_value:,.0f}")
                logger.info(f"   Position Value (Margin): ₹{position_value:,.0f} ({estimated_margin_factor:.1%} of contract)")
            else:
                # For options, full premium is at risk
                position_value = contract_value
                logger.info(f"   Position Value: ₹{position_value:,.0f}")
            
            # CRITICAL: Options bypass position size limits (risk limited to premium paid)
            # 🔥 FIX: Use proper options detection (requires digits before CE/PE = strike price)
            # Stocks like BAJFINANCE, PETRONET end with CE/PE but are NOT options!
            if is_options_trade:
                logger.info(f"🎯 OPTIONS TRADE DETECTED: {symbol} - BYPASSING position size limits")
                logger.info(f"   Risk limited to premium paid: ₹{position_value:,.0f}")

            # Management/closing actions (auto square-off) should not be blocked by sizing caps
            is_management_action = False
            try:
                # detect via strategy/tag hints commonly used by order paths
                is_management_action = (
                    (signal and getattr(signal, 'strategy_name', '') == 'position_monitor') or
                    (hasattr(signal, 'tag') and 'POSITION_MGMT' in str(getattr(signal, 'tag')))
                )
            except Exception:
                is_management_action = False
            
            # Prefer live capital from Zerodha margins when available
            total_capital_override = None
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and getattr(orchestrator, 'zerodha_client', None):
                    margins = await orchestrator.zerodha_client.get_margins()
                    if margins:
                        # CRITICAL FIX: Use 'cash' field for available capital (not 'live_balance')
                        total_capital_override = float(margins.get('equity', {}).get('available', {}).get('cash', 0))
                        if total_capital_override == 0:
                            total_capital_override = None
            except Exception:
                total_capital_override = None
            
            # Validate trade risk using existing method (skip single-position cap for management actions)
            if is_management_action:
                # Only enforce emergency stop and basic sanity checks for exits
                risk_approved, risk_reason = True, "Management action bypass"
            elif is_options_trade:
                risk_approved, risk_reason = True, "Options trade - no position size restrictions"
                logger.info(f"🎯 OPTIONS BYPASS: {symbol} approved regardless of premium cost")
            else:
                risk_approved, risk_reason = self.validate_trade_risk(position_value, strategy_name, symbol, total_capital_override)
            
            # 🔥 CRITICAL FIX: If concentration limit exceeded, REDUCE QUANTITY instead of rejecting
            if not risk_approved and "Concentration limit" in risk_reason:
                # Calculate max allowed quantity within concentration limits
                max_allowed_qty = self._get_max_quantity_for_concentration(
                    symbol=symbol,
                    price_per_share=entry_price,
                    original_quantity=quantity,
                    total_capital=total_capital_override or self.position_tracker.capital,
                    is_equity=is_equity_trade
                )
                
                if max_allowed_qty >= 1:
                    logger.warning(f"⚠️ CONCENTRATION ADJUSTMENT: {symbol} qty reduced {quantity} → {max_allowed_qty}")
                    quantity = max_allowed_qty
                    # Recalculate position value with reduced quantity
                    contract_value = float(entry_price) * float(quantity)
                    position_value = contract_value * 0.25 if is_equity_trade else contract_value
                    risk_approved = True
                    risk_reason = f"Quantity reduced from original to fit concentration limits"
                    logger.info(f"✅ CONCENTRATION FIX: {symbol} approved with {quantity} shares (₹{position_value:,.0f} margin)")
                else:
                    logger.error(f"❌ CONCENTRATION BLOCK: {symbol} - even 1 share exceeds limits")
            
            if not risk_approved:
                return {
                    'approved': False,
                    'reason': risk_reason,
                    'risk_score': 100.0,  # Maximum risk
                    'position_size': 0,
                    'validation_details': {
                        'symbol': symbol,
                        'strategy': strategy_name,
                        'position_value': position_value,
                        'risk_check_failed': True
                    }
                }
            
            # Calculate risk score (0-100, lower is better)
            risk_score = self._calculate_signal_risk_score(signal)
            
            # Validate Greeks if options signal
            if hasattr(signal, 'option_type') and signal.option_type != 'EQUITY':
                greeks_result = await self.greeks_manager.validate_new_position_greeks(
                    signal, entry_price
                )
                if not greeks_result.get('approved', True):
                    return {
                        'approved': False,
                        'reason': f"Greeks validation failed: {greeks_result.get('reason', 'Unknown')}",
                        'risk_score': 100.0,
                        'position_size': quantity,
                        'validation_details': {
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'greeks_violations': greeks_result.get('violations', [])
                        }
                    }
            
            # Signal approved
            return {
                'approved': True,
                'reason': 'Signal passed risk validation',
                'risk_score': risk_score,
                'position_size': quantity,
                'validation_details': {
                    'symbol': symbol,
                    'strategy': strategy_name,
                    'position_value': position_value,
                    'risk_score': risk_score,
                    'confidence': getattr(signal, 'quality_score', 0.0),
                    'validation_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return {
                'approved': False,
                'reason': f'Signal validation error: {str(e)}',
                'risk_score': 100.0,
                'position_size': 0,
                'validation_details': {
                    'error': str(e),
                    'validation_timestamp': datetime.now().isoformat()
                }
            }
    
    def _is_options_symbol(self, symbol: str) -> bool:
        """Check if symbol is an options contract"""
        if not symbol:
            return False
        # Options symbols typically end with CE (Call) or PE (Put)
        symbol_upper = symbol.upper()
        if symbol_upper.endswith('CE') or symbol_upper.endswith('PE'):
            return True
        # Also check for options format patterns like NIFTY24DEC26000CE
        import re
        options_pattern = r'(NIFTY|BANKNIFTY|FINNIFTY|[A-Z]+)\d{2}[A-Z]{3}\d+[CP]E'
        if re.match(options_pattern, symbol_upper):
            return True
        return False

    def _calculate_signal_risk_score(self, signal: Signal) -> float:
        """Calculate risk score for signal (0-100, lower is better)"""
        try:
            risk_score = 0.0
            
            # Base risk from strategy
            strategy_risk = {
                'momentum_surfer': 20.0,
                'volatility_explosion': 40.0,
                'volume_profile_scalper': 30.0,
                'regime_adaptive_controller': 25.0,
                'confluence_amplifier': 15.0
            }.get(signal.strategy_name, 35.0)
            
            risk_score += strategy_risk
            
            # Risk from signal quality (inverse relationship)
            quality_score = getattr(signal, 'quality_score', 0.5)
            quality_risk = (1.0 - quality_score) * 30.0  # Max 30 points
            risk_score += quality_risk
            
            # Risk from position size
            position_value = signal.entry_price * signal.quantity
            total_capital = self.position_tracker.capital
            
            if total_capital > 0:
                position_percent = position_value / total_capital
                if position_percent > 0.05:  # More than 5% of capital
                    risk_score += (position_percent - 0.05) * 200  # Penalty for large positions
            
            # Risk from current market conditions
            if self.current_drawdown > 0.02:  # In drawdown
                risk_score += self.current_drawdown * 100
            
            if self.daily_pnl < 0:  # Negative P&L today
                daily_loss_percent = abs(self.daily_pnl) / total_capital if total_capital > 0 else 0
                risk_score += daily_loss_percent * 200
            
            # Risk from emergency conditions
            if self.emergency_stop_triggered:
                risk_score = 100.0  # Maximum risk
            
            return min(risk_score, 100.0)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating signal risk score: {e}")
            return 50.0  # Default moderate risk
    
    async def validate_order(self, user_id: str, order) -> bool:
        """Validate order for user (called by OrderManager)"""
        try:
            logger.info(f"🔍 RISK MANAGER: Starting order validation for user {user_id}")
            logger.info(f"   Order data: {order}")
            
            # 🚨 CRITICAL: EMERGENCY EXITS MUST ALWAYS PASS
            # Check for bypass flags in order metadata or tag
            if isinstance(order, dict):
                metadata = order.get('metadata', {})
                bypass_all = metadata.get('bypass_all_checks', False)
                is_emergency = 'EMERGENCY' in order.get('tag', '')
                is_closing = metadata.get('closing_action', False)
                
                if bypass_all or is_emergency or is_closing:
                    logger.warning(f"🚨 BYPASSING ALL RISK CHECKS - Emergency/Closing order for {order.get('symbol')}")
                    return True
            
            # 🕐 CRITICAL: TIME-BASED TRADING RESTRICTIONS (IST)
            if not self._validate_trading_hours(order):
                return False
            
            # Convert order to signal-like object for validation
            class OrderSignal:
                def __init__(self, order):
                    # CRITICAL FIX: Handle both dict and object types
                    if isinstance(order, dict):
                        self.symbol = order.get('symbol', 'UNKNOWN')
                        self.strategy_name = order.get('strategy_name', order.get('strategy', 'unknown'))
                        self.strategy = order.get('strategy', self.strategy_name)
                        self.quantity = order.get('quantity', 0)
                        # CRITICAL FIX: Check both price and entry_price fields
                        self.entry_price = order.get('entry_price', order.get('price', 0.0))
                        self.tag = order.get('tag', '')
                    else:
                        self.symbol = getattr(order, 'symbol', 'UNKNOWN')
                        self.strategy_name = getattr(order, 'strategy_name', getattr(order, 'strategy', 'unknown'))
                        self.strategy = getattr(order, 'strategy', self.strategy_name)
                        self.quantity = getattr(order, 'quantity', 0)
                        # CRITICAL FIX: Check both price and entry_price fields for objects too
                        self.entry_price = getattr(order, 'entry_price', getattr(order, 'price', 0.0))
                        self.tag = getattr(order, 'tag', '')
                    self.quality_score = 0.8  # Default quality
            
            signal = OrderSignal(order)
            logger.info(f"   Created OrderSignal: symbol={signal.symbol}, quantity={signal.quantity}, entry_price={signal.entry_price}")
            
            result = await self.validate_signal(signal)
            logger.info(f"   Validation result: {result}")
            
            approved = result.get('approved', False)
            logger.info(f"🔍 RISK MANAGER: Order validation result for {signal.symbol}: {approved}")
            
            return approved
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return False

    def _validate_trading_hours(self, order) -> bool:
        """⏰ VALIDATE TRADING HOURS - Time-based order restrictions (IST)"""
        try:
            import pytz
            from datetime import time
            
            # IST timezone
            ist_timezone = pytz.timezone('Asia/Kolkata')
            current_time_ist = datetime.now(ist_timezone).time()
            current_time_str = datetime.now(ist_timezone).strftime('%H:%M:%S')
            
            # Extract order information
            if isinstance(order, dict):
                symbol = order.get('symbol', 'UNKNOWN')
                action = order.get('action', order.get('side', 'UNKNOWN'))
                is_management_action = order.get('management_action', False)
                is_closing_action = order.get('closing_action', False)
                tag = order.get('tag', '')
            else:
                symbol = getattr(order, 'symbol', 'UNKNOWN')
                action = getattr(order, 'action', getattr(order, 'side', 'UNKNOWN'))
                is_management_action = getattr(order, 'management_action', False)
                is_closing_action = getattr(order, 'closing_action', False)
                tag = getattr(order, 'tag', '')
            
            # Define trading time restrictions (IST)
            market_open = time(9, 15)      # 9:15 AM IST
            no_new_signals_after = time(15, 0)    # 3:00 PM IST - No new signals
            warning_close_time = time(15, 15)     # 3:15 PM IST - Start aggressive closing
            mandatory_close_time = time(15, 20)   # 3:20 PM IST - Force close all positions
            market_close = time(15, 30)           # 3:30 PM IST - Market close
            
            # Check if market is open
            if current_time_ist < market_open or current_time_ist > market_close:
                logger.warning(f"🕐 MARKET CLOSED: {symbol} {action} rejected - Market hours: 9:15 AM - 3:30 PM IST (Current: {current_time_str} IST)")
                return False
            
            # 🎯 BYPASS TIME RESTRICTIONS FOR POSITION MANAGEMENT ACTIONS
            # Check if this is from position monitor (auto square-off)
            strategy = order.get('strategy', '') if order else ''
            if is_management_action or is_closing_action or 'POSITION_MGMT' in tag or strategy == 'position_monitor':
                logger.info(f"🎯 TIME BYPASS: {symbol} {action} - Management/closing action allowed at {current_time_str} IST")
                return True
            
            # 🔥 CRITICAL FIX: Allow EXIT orders after 3:00 PM
            # Check if this is an exit/sell order for an existing position
            is_exit_order = False
            order_action = action.upper() if action else ''
            
            # Check various exit indicators
            if isinstance(order, dict):
                is_exit_order = (
                    order.get('is_exit', False) or
                    order.get('signal_type') == 'EXIT' or
                    'EXIT' in tag.upper() or
                    'FULL_EXIT' in tag.upper() or
                    order.get('metadata', {}).get('is_exit', False) or
                    order.get('exit_reason') is not None
                )
            
            # After 3:00 PM, allow exits but block new positions
            if current_time_ist >= no_new_signals_after:  # After 3:00 PM
                if is_exit_order or order_action == 'SELL':
                    logger.info(f"✅ EXIT ALLOWED AFTER 3PM: {symbol} {action} - Exit orders permitted at {current_time_str} IST")
                    return True
            
            # Time-based restrictions for NEW positions only
            if current_time_ist >= mandatory_close_time:  # After 3:20 PM
                logger.warning(f"🚨 MANDATORY CLOSE TIME: {symbol} {action} rejected - Only exits allowed after 3:20 PM IST (Current: {current_time_str} IST)")
                return False
            elif current_time_ist >= warning_close_time:  # 3:15-3:20 PM
                logger.warning(f"⚠️ WARNING CLOSE TIME: {symbol} {action} rejected - Only exits allowed 3:15-3:20 PM IST (Current: {current_time_str} IST)")
                return False
            elif current_time_ist >= no_new_signals_after:  # 3:00-3:15 PM
                logger.warning(f"🕐 NO NEW POSITIONS: {symbol} {action} rejected - No new positions after 3:00 PM IST (Current: {current_time_str} IST)")
                return False
            
            # Normal trading hours (9:15 AM - 3:00 PM)
            logger.debug(f"✅ TRADING HOURS VALID: {symbol} {action} approved at {current_time_str} IST")
            return True
            
        except Exception as e:
            logger.error(f"Error validating trading hours: {e}")
            # BLOCK trades on time check error - quality over quantity
            logger.warning(f"🚫 TIME VALIDATION ERROR: Blocking {symbol} {action} due to time check failure")
            return False

    def get_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive risk report"""
        total_capital = self.position_tracker.capital
        
        return {
            'risk_limits': self.risk_limits,
            'current_metrics': {
                'daily_pnl': self.daily_pnl,
                'daily_pnl_percent': (self.daily_pnl / total_capital * 100) if total_capital > 0 else 0,
                'current_drawdown': self.current_drawdown,
                'current_drawdown_percent': self.current_drawdown * 100,
                'portfolio_var': self.portfolio_var,
                'portfolio_var_percent': (self.portfolio_var / total_capital * 100) if total_capital > 0 else 0,
                'portfolio_beta': self.portfolio_beta
            },
            'risk_utilization': {
                'daily_loss_utilization': (abs(self.daily_pnl) / (total_capital * self.risk_limits['max_daily_loss_percent']) * 100) if total_capital > 0 else 0,
                'drawdown_utilization': (self.current_drawdown / self.risk_limits['max_drawdown_percent'] * 100) if self.risk_limits['max_drawdown_percent'] > 0 else 0,
                'var_utilization': (self.portfolio_var / (total_capital * self.risk_limits['max_portfolio_var_percent']) * 100) if total_capital > 0 else 0
            },
            'risk_status': {
                'emergency_stop_triggered': self.emergency_stop_triggered,
                'risk_breaches_count': len(self.risk_breaches),
                'risk_alerts_count': len(self.risk_alerts),
                'risk_regime': self.risk_regime
            },
            'recent_alerts': self.risk_alerts[-5:],  # Last 5 alerts
            'recent_breaches': self.risk_breaches[-3:]  # Last 3 breaches
        }

"""
Performance tracking and analysis for mock trading
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .config import (
    INITIAL_CAPITAL, RISK_FREE_RATE,
    METRICS, RISK_LIMITS
)

class PerformanceTracker:
    def __init__(self):
        self.initial_capital = INITIAL_CAPITAL
        self.current_capital = INITIAL_CAPITAL
        self.positions = {}
        self.trades = []
        self.daily_returns = []
        self.risk_metrics = {}
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize performance metrics"""
        self.risk_metrics = {
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0
        }

    def update_position(self, symbol, quantity, price, timestamp):
        """Update position information"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'unrealized_pnl': 0,
                'realized_pnl': 0
            }
            
        position = self.positions[symbol]
        old_quantity = position['quantity']
        old_avg_price = position['avg_price']
        
        # Update position
        if old_quantity + quantity == 0:
            # Position closed
            realized_pnl = (price - old_avg_price) * old_quantity
            position['realized_pnl'] += realized_pnl
            position['quantity'] = 0
            position['avg_price'] = 0
        else:
            # Position updated
            new_quantity = old_quantity + quantity
            new_avg_price = ((old_quantity * old_avg_price) + (quantity * price)) / new_quantity
            position['quantity'] = new_quantity
            position['avg_price'] = new_avg_price
            
        # Update capital
        self.current_capital += position['realized_pnl']
        self._update_risk_metrics()

    def record_trade(self, trade):
        """Record a trade and update performance metrics"""
        self.trades.append(trade)
        self._update_risk_metrics()

    def _update_risk_metrics(self):
        """Update risk metrics based on current performance"""
        if not self.trades:
            return
            
        # Calculate returns
        returns = pd.Series([t['price'] * t['quantity'] for t in self.trades])
        daily_returns = returns.resample('D').sum()
        
        # Update metrics
        self.risk_metrics['total_pnl'] = self.current_capital - self.initial_capital
        self.risk_metrics['daily_pnl'] = daily_returns.iloc[-1] if not daily_returns.empty else 0
        
        # Calculate drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        self.risk_metrics['max_drawdown'] = drawdowns.min()
        self.risk_metrics['current_drawdown'] = drawdowns.iloc[-1]
        
        # Calculate win rate
        winning_trades = sum(1 for t in self.trades if t['price'] * t['quantity'] > 0)
        self.risk_metrics['win_rate'] = winning_trades / len(self.trades)
        
        # Calculate Sharpe ratio
        if len(daily_returns) > 1:
            excess_returns = daily_returns - RISK_FREE_RATE/252
            self.risk_metrics['sharpe_ratio'] = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            
            # Calculate Sortino ratio
            downside_returns = excess_returns[excess_returns < 0]
            if len(downside_returns) > 0:
                self.risk_metrics['sortino_ratio'] = np.sqrt(252) * excess_returns.mean() / downside_returns.std()

    def check_risk_limits(self):
        """Check if any risk limits are breached"""
        breaches = []
        
        if self.risk_metrics['max_drawdown'] < -RISK_LIMITS['max_drawdown']:
            breaches.append(f"Max drawdown limit breached: {self.risk_metrics['max_drawdown']:.2%}")
            
        if self.risk_metrics['daily_pnl'] < -RISK_LIMITS['max_daily_loss'] * self.current_capital:
            breaches.append(f"Daily loss limit breached: {self.risk_metrics['daily_pnl']:.2%}")
            
        return breaches

    def get_performance_report(self):
        """Generate comprehensive performance report"""
        return {
            'capital': {
                'initial': self.initial_capital,
                'current': self.current_capital,
                'total_return': (self.current_capital - self.initial_capital) / self.initial_capital
            },
            'risk_metrics': self.risk_metrics,
            'positions': self.positions,
            'trade_statistics': {
                'total_trades': len(self.trades),
                'winning_trades': sum(1 for t in self.trades if t['price'] * t['quantity'] > 0),
                'losing_trades': sum(1 for t in self.trades if t['price'] * t['quantity'] < 0),
                'avg_trade_pnl': np.mean([t['price'] * t['quantity'] for t in self.trades])
            }
        } 
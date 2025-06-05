"""
Visualization tools for mock trading results
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class TradingVisualizer:
    def __init__(self, performance_tracker, market_simulator):
        self.performance = performance_tracker
        self.market = market_simulator
        self.setup_style()

    def setup_style(self):
        """Set up visualization style"""
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
    def plot_equity_curve(self, save_path=None):
        """Plot equity curve with drawdown"""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03, subplot_titles=('Equity Curve', 'Drawdown'),
                           row_heights=[0.7, 0.3])

        # Calculate equity curve
        trades_df = pd.DataFrame(self.performance.trades)
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df['pnl'] = trades_df['price'] * trades_df['quantity']
        equity_curve = trades_df.set_index('timestamp')['pnl'].cumsum() + self.performance.initial_capital
        
        # Calculate drawdown
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max * 100

        # Plot equity curve
        fig.add_trace(
            go.Scatter(x=equity_curve.index, y=equity_curve.values,
                      name='Equity', line=dict(color='blue')),
            row=1, col=1
        )

        # Plot drawdown
        fig.add_trace(
            go.Scatter(x=drawdown.index, y=drawdown.values,
                      name='Drawdown', line=dict(color='red')),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title='Portfolio Performance',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            height=800,
            showlegend=True
        )

        if save_path:
            fig.write_html(save_path)
        return fig

    def plot_trade_distribution(self, save_path=None):
        """Plot trade PnL distribution"""
        trades_df = pd.DataFrame(self.performance.trades)
        trades_df['pnl'] = trades_df['price'] * trades_df['quantity']
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=trades_df['pnl'],
            name='Trade PnL',
            nbinsx=50,
            histnorm='probability'
        ))
        
        fig.update_layout(
            title='Trade PnL Distribution',
            xaxis_title='PnL ($)',
            yaxis_title='Frequency',
            showlegend=True
        )
        
        if save_path:
            fig.write_html(save_path)
        return fig

    def plot_position_heatmap(self, save_path=None):
        """Plot position heatmap by symbol and time"""
        positions = pd.DataFrame(self.performance.positions).T
        positions['exposure'] = positions['quantity'] * positions['avg_price']
        
        fig = go.Figure(data=go.Heatmap(
            z=positions['exposure'].values.reshape(-1, 1),
            x=['Exposure'],
            y=positions.index,
            colorscale='RdBu',
            showscale=True
        ))
        
        fig.update_layout(
            title='Position Exposure by Symbol',
            xaxis_title='',
            yaxis_title='Symbol',
            height=400
        )
        
        if save_path:
            fig.write_html(save_path)
        return fig

    def plot_risk_metrics(self, save_path=None):
        """Plot key risk metrics"""
        metrics = self.performance.risk_metrics
        
        fig = make_subplots(rows=2, cols=2,
                           subplot_titles=('Sharpe Ratio', 'Sortino Ratio',
                                         'Win Rate', 'Max Drawdown'))
        
        # Sharpe Ratio
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics['sharpe_ratio'],
                title={'text': "Sharpe Ratio"},
                gauge={'axis': {'range': [0, 3]}},
            ),
            row=1, col=1
        )
        
        # Sortino Ratio
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics['sortino_ratio'],
                title={'text': "Sortino Ratio"},
                gauge={'axis': {'range': [0, 3]}},
            ),
            row=1, col=2
        )
        
        # Win Rate
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics['win_rate'] * 100,
                title={'text': "Win Rate (%)"},
                gauge={'axis': {'range': [0, 100]}},
            ),
            row=2, col=1
        )
        
        # Max Drawdown
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=abs(metrics['max_drawdown'] * 100),
                title={'text': "Max Drawdown (%)"},
                gauge={'axis': {'range': [0, 50]}},
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        
        if save_path:
            fig.write_html(save_path)
        return fig

    def generate_report(self, save_dir='mock_trading/reports'):
        """Generate comprehensive trading report with all visualizations"""
        import os
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate all plots
        self.plot_equity_curve(f'{save_dir}/equity_curve.html')
        self.plot_trade_distribution(f'{save_dir}/trade_distribution.html')
        self.plot_position_heatmap(f'{save_dir}/position_heatmap.html')
        self.plot_risk_metrics(f'{save_dir}/risk_metrics.html')
        
        # Generate summary report
        report = self.performance.get_performance_report()
        
        # Save report to HTML
        html_content = f"""
        <html>
        <head>
            <title>Trading Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin: 10px 0; }}
                .value {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Trading Performance Report</h1>
            <h2>Capital</h2>
            <div class="metric">Initial Capital: <span class="value">${report['capital']['initial']:,.2f}</span></div>
            <div class="metric">Current Capital: <span class="value">${report['capital']['current']:,.2f}</span></div>
            <div class="metric">Total Return: <span class="value">{report['capital']['total_return']:.2%}</span></div>
            
            <h2>Risk Metrics</h2>
            <div class="metric">Sharpe Ratio: <span class="value">{report['risk_metrics']['sharpe_ratio']:.2f}</span></div>
            <div class="metric">Sortino Ratio: <span class="value">{report['risk_metrics']['sortino_ratio']:.2f}</span></div>
            <div class="metric">Max Drawdown: <span class="value">{report['risk_metrics']['max_drawdown']:.2%}</span></div>
            <div class="metric">Win Rate: <span class="value">{report['risk_metrics']['win_rate']:.2%}</span></div>
            
            <h2>Trade Statistics</h2>
            <div class="metric">Total Trades: <span class="value">{report['trade_statistics']['total_trades']}</span></div>
            <div class="metric">Winning Trades: <span class="value">{report['trade_statistics']['winning_trades']}</span></div>
            <div class="metric">Losing Trades: <span class="value">{report['trade_statistics']['losing_trades']}</span></div>
            <div class="metric">Average Trade PnL: <span class="value">${report['trade_statistics']['avg_trade_pnl']:,.2f}</span></div>
            
            <h2>Visualizations</h2>
            <iframe src="equity_curve.html" width="100%" height="600px"></iframe>
            <iframe src="trade_distribution.html" width="100%" height="600px"></iframe>
            <iframe src="position_heatmap.html" width="100%" height="600px"></iframe>
            <iframe src="risk_metrics.html" width="100%" height="600px"></iframe>
        </body>
        </html>
        """
        
        with open(f'{save_dir}/report.html', 'w') as f:
            f.write(html_content)
        
        return f'{save_dir}/report.html' 
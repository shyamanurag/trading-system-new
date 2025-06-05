"""
Main script to run mock trading simulation
"""
import logging
import pandas as pd
from datetime import datetime
from .market_simulator import MarketSimulator
from .performance_tracker import PerformanceTracker
from .visualization import TradingVisualizer
from .order_manager import OrderManager, Order, OrderType
from .config import LOGGING, DATA_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING['level'],
    format=LOGGING['format'],
    filename=LOGGING['file']
)
logger = logging.getLogger(__name__)

def run_mock_trading():
    """Run the mock trading simulation"""
    logger.info("Starting mock trading simulation")
    
    # Initialize components
    market = MarketSimulator()
    performance = PerformanceTracker()
    visualizer = TradingVisualizer(performance, market)
    order_manager = OrderManager(market)
    
    try:
        while True:
            # Get current market data
            for symbol in DATA_CONFIG['symbols']:
                market_data = market.get_market_data(symbol)
                current_price = market_data['close'].iloc[-1]
                
                # Update trailing stops
                order_manager.update_trailing_stops(symbol, current_price)
                
                # TODO: Implement your trading strategy here
                # This is where you would:
                # 1. Analyze market data
                # 2. Generate trading signals
                # 3. Calculate position sizes
                # 4. Execute trades
                
                # Example trade execution with advanced order types
                if market_data['close'].iloc[-1] > market_data['close'].iloc[-2]:
                    # Create OCO order (take profit and stop loss)
                    take_profit_price = current_price * 1.02  # 2% profit target
                    stop_loss_price = current_price * 0.98    # 2% stop loss
                    
                    limit_id, stop_id = order_manager.create_oco_order(
                        symbol=symbol,
                        quantity=100,
                        limit_price=take_profit_price,
                        stop_price=stop_loss_price
                    )
                    
                    # Create trailing stop for additional protection
                    trail_id = order_manager.create_trailing_stop(
                        symbol=symbol,
                        quantity=100,
                        trailing_percent=0.01,  # 1% trailing stop
                        initial_price=current_price
                    )
                    
                    # Execute the entry order
                    entry_order = Order(
                        order_id=order_manager._generate_order_id(),
                        symbol=symbol,
                        order_type=OrderType.MARKET,
                        quantity=100
                    )
                    
                    execution = order_manager.execute_order(entry_order)
                    performance.record_trade(execution)
                    performance.update_position(
                        symbol=symbol,
                        quantity=execution['quantity'],
                        price=execution['price'],
                        timestamp=execution['timestamp']
                    )
            
            # Check risk limits
            risk_breaches = performance.check_risk_limits()
            if risk_breaches:
                logger.warning("Risk limits breached:")
                for breach in risk_breaches:
                    logger.warning(f"- {breach}")
            
            # Advance time
            market.advance_time()
            
    except StopIteration:
        logger.info("Simulation completed")
        
    # Generate final report and visualizations
    report_path = visualizer.generate_report()
    logger.info(f"Performance report generated: {report_path}")
    
    # Get performance metrics
    report = performance.get_performance_report()
    logger.info("Final Performance Report:")
    logger.info(f"Total Return: {report['capital']['total_return']:.2%}")
    logger.info(f"Sharpe Ratio: {report['risk_metrics']['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown: {report['risk_metrics']['max_drawdown']:.2%}")
    logger.info(f"Win Rate: {report['risk_metrics']['win_rate']:.2%}")
    
    return report, report_path

if __name__ == "__main__":
    report, report_path = run_mock_trading()
    print(f"\nTrading simulation completed. View the full report at: {report_path}") 
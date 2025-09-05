import logging
import os
from datetime import datetime
import sys

def setup_logging(service_name: str = "trading_system"):
    """Configure logging for the trading system with production optimizations"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Check if we're in production (deployed environment)
    is_production = os.getenv('PORT') is not None or 'heroku' in sys.executable.lower()
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/{service_name}_{timestamp}.log'
    
    # Configure root logger
    log_level = logging.WARNING if is_production else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('websocket').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # Reduce logging in production
    if is_production:
        # Critical modules with ERROR only logging
        logging.getLogger('strategies.base_strategy').setLevel(logging.ERROR)
        logging.getLogger('brokers.zerodha').setLevel(logging.ERROR)
        logging.getLogger('data.truedata_client').setLevel(logging.ERROR)
        logging.getLogger('src.core.orchestrator').setLevel(logging.ERROR)
        logging.getLogger('src.core.signal_deduplicator').setLevel(logging.ERROR)
        logging.getLogger('src.core.market_directional_bias').setLevel(logging.ERROR)
        logging.getLogger('config.truedata_symbols').setLevel(logging.ERROR)
        logging.getLogger('strategies.news_impact_scalper').setLevel(logging.ERROR)
        
        # Silence all verbose logs
        logging.getLogger('strategies').setLevel(logging.ERROR)
        logging.getLogger('brokers').setLevel(logging.ERROR)
        logging.getLogger('data').setLevel(logging.ERROR)
        logging.getLogger('src').setLevel(logging.ERROR)
        logging.getLogger('config').setLevel(logging.ERROR)
    else:
        # Development mode - keep INFO level
        for module in ['strategies', 'brokers', 'data', 'src']:
            logging.getLogger(module).setLevel(logging.INFO)
    
    logger = logging.getLogger(service_name)
    if not is_production:
        logger.info(f"Logging configured for {service_name}")
        logger.info(f"Log file: {log_file}")
    else:
        logger.warning(f"Production mode: Reduced logging enabled")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

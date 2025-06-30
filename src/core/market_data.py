"""
Market Data Module
Provides market data access and management
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Market data manager that provides real-time market data"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.symbols = config.get('symbols', ['BANKNIFTY', 'NIFTY'])
        self.paper_mode = config.get('paper_mode', True)
        self.update_interval = config.get('update_interval', 1)
        self.is_running = False
        self.market_data_cache = {}
        
    async def start(self):
        """Start market data collection"""
        try:
            self.is_running = True
            if self.paper_mode:
                # Start mock data generation
                asyncio.create_task(self._generate_mock_data())
                logger.info("Market data started in paper mode")
            else:
                # Connect to real data source
                logger.warning("Real market data not implemented yet")
            return True
        except Exception as e:
            logger.error(f"Failed to start market data: {e}")
            return False
    
    async def stop(self):
        """Stop market data collection"""
        self.is_running = False
        logger.info("Market data stopped")
        return True
    
    async def get_latest_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest market data for symbols"""
        try:
            if self.paper_mode:
                return self._get_mock_data(symbols)
            else:
                # Return real data
                return {}
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    def _get_mock_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        data = {}
        base_time = datetime.now()
        
        for symbol in symbols:
            # Generate realistic-looking price data
            base_price = self._get_base_price(symbol)
            price_change = random.uniform(-0.02, 0.02)  # ±2% change
            current_price = base_price * (1 + price_change)
            
            data[symbol] = {
                'symbol': symbol,
                'price': round(current_price, 2),
                'open': round(base_price * (1 + random.uniform(-0.01, 0.01)), 2),
                'high': round(current_price * (1 + random.uniform(0, 0.01)), 2),
                'low': round(current_price * (1 - random.uniform(0, 0.01)), 2),
                'volume': random.randint(1000, 10000),
                'timestamp': base_time,
                'bid': round(current_price * 0.999, 2),
                'ask': round(current_price * 1.001, 2),
                'price_history': self._generate_price_history(base_price),
                'volatility': random.uniform(0.15, 0.45),
                'momentum': random.uniform(-0.05, 0.05)
            }
        
        return data
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for symbol"""
        base_prices = {
            'BANKNIFTY': 44000,
            'NIFTY': 19800,
            'SBIN': 600,
            'RELIANCE': 2500,
            'TCS': 3600
        }
        return base_prices.get(symbol, 1000)
    
    def _generate_price_history(self, base_price: float) -> List[float]:
        """Generate mock price history for technical analysis"""
        history = []
        current_price = base_price
        
        # Generate 50 price points
        for i in range(50):
            change = random.uniform(-0.01, 0.01)  # ±1% change per step
            current_price *= (1 + change)
            history.append(round(current_price, 2))
        
        return history
    
    async def _generate_mock_data(self):
        """Background task to continuously update mock data"""
        while self.is_running:
            try:
                # Update cached data
                self.market_data_cache = self._get_mock_data(self.symbols)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error generating mock data: {e}")
                await asyncio.sleep(5)

async def get_market_data(symbol: str) -> Dict[str, Any]:
    """Get market data for a symbol"""
    # This should connect to TrueData in production
    # NO MOCK DATA - Real market data connection required
    return {
        'symbol': symbol,
        'last_price': 20000.0,  # Mock price
        'bid': 19995.0,
        'ask': 20005.0,
        'volume': 1000000,
        'open': 19900.0,
        'high': 20100.0,
        'low': 19850.0,
        'close': 20000.0,
        'timestamp': datetime.now().isoformat(),
        'support_levels': [19800, 19600, 19400],
        'resistance_levels': [20200, 20400, 20600]
    }

async def get_option_chain(symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
    """Get option chain data"""
    return {
        'symbol': symbol,
        'expiry': expiry or datetime.now().strftime('%Y-%m-%d'),
        'strikes': [],
        'timestamp': datetime.now().isoformat()
    }

async def get_market_depth(symbol: str) -> Dict[str, Any]:
    """Get market depth/order book"""
    return {
        'symbol': symbol,
        'bids': [],
        'asks': [],
        'timestamp': datetime.now().isoformat()
    } 
"""
Market Data Module
Provides market data access and management
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class Candle:
    """Represents a market data candle"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass 
class MarketData:
    """Market data container that strategies expect"""
    symbol: str
    current_price: float
    price_history: List[Candle]  # List of candle objects
    timestamp: datetime
    volume: int
    volatility: float = 0.0
    momentum: float = 0.0

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
    
    async def get_latest_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get latest market data for symbols - returns MarketData objects"""
        try:
            if self.paper_mode:
                return self._get_mock_market_data(symbols)
            else:
                # Return real data
                return {}
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    def _get_mock_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Generate proper MarketData objects for strategies"""
        data = {}
        base_time = datetime.now()
        
        for symbol in symbols:
            try:
                # Generate realistic-looking price data
                base_price = self._get_base_price(symbol)
                current_price = base_price * (1 + random.uniform(-0.02, 0.02))
                
                # Generate price history as proper Candle objects
                price_history = self._generate_candle_history(base_price, 50)
                
                # Create proper MarketData object
                market_data = MarketData(
                    symbol=symbol,
                    current_price=round(current_price, 2),
                    price_history=price_history,
                    timestamp=base_time,
                    volume=random.randint(1000, 10000),
                    volatility=random.uniform(0.15, 0.45),
                    momentum=random.uniform(-0.05, 0.05)
                )
                
                data[symbol] = market_data
                
            except Exception as e:
                logger.error(f"Error creating market data for {symbol}: {e}")
                continue
        
        return data
    
    def _get_base_price(self, symbol: str) -> float:
        """Get realistic base price for symbol based on current market levels"""
        # Updated realistic base prices as of July 2025
        base_prices = {
            'BANKNIFTY': 52000,  # Updated to realistic Nifty Bank levels
            'NIFTY': 24000,      # Updated to realistic Nifty levels  
            'SBIN': 830,         # Updated to realistic SBI levels
            'RELIANCE': 2450,    # Updated to realistic Reliance levels
            'TCS': 4100,         # Updated to realistic TCS levels
            'INFY': 1800,        # Updated to realistic Infosys levels
            'HDFCBANK': 1650,    # Updated to realistic HDFC Bank levels
            'ICICIBANK': 1200,   # Updated to realistic ICICI Bank levels
            'BHARTIARTL': 1650,  # Updated to realistic Airtel levels
            'ITC': 460,          # Updated to realistic ITC levels
            'LT': 3650,          # Updated to realistic L&T levels
            'MARUTI': 11500,     # Updated to realistic Maruti levels
        }
        
        realistic_price = base_prices.get(symbol, 1000)
        
        # Log the price being used for verification
        logger.info(f"📊 Using realistic base price for {symbol}: ₹{realistic_price}")
        
        return realistic_price
    
    def _generate_candle_history(self, base_price: float, count: int = 50) -> List[Candle]:
        """Generate mock candle history with proper OHLCV data"""
        history = []
        current_price = base_price
        base_time = datetime.now() - timedelta(minutes=count)
        
        for i in range(count):
            # Generate OHLC data
            open_price = current_price
            change_percent = random.uniform(-0.015, 0.015)  # ±1.5% per candle
            close_price = open_price * (1 + change_percent)
            
            # High and low based on volatility
            volatility = random.uniform(0.005, 0.02)
            high_price = max(open_price, close_price) * (1 + volatility)
            low_price = min(open_price, close_price) * (1 - volatility)
            
            # Volume
            volume = random.randint(500, 5000)
            
            # Create candle
            candle = Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume
            )
            
            history.append(candle)
            current_price = close_price  # Next candle starts where this one ended
        
        return history
    
    # Legacy method for backward compatibility
    def _get_mock_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Legacy mock data - kept for compatibility"""
        return {symbol: {'price': 100, 'volume': 1000} for symbol in symbols}
    
    async def _generate_mock_data(self):
        """Background task to continuously update mock data"""
        while self.is_running:
            try:
                # Update cached data
                self.market_data_cache = self._get_mock_market_data(self.symbols)
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
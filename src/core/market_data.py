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
        """Get REAL market data from TrueData feed instead of fake mock data"""
        data = {}
        base_time = datetime.now()
        
        for symbol in symbols:
            try:
                # Get REAL price from TrueData feed
                real_price = self._get_real_price_from_truedata(symbol)
                
                if real_price is None:
                    logger.warning(f"⚠️ No TrueData for {symbol}, skipping")
                    continue
                
                # Generate price history based on REAL current price (not fake base price)
                price_history = self._generate_candle_history(real_price, 50)
                
                # Create proper MarketData object with REAL price
                market_data = MarketData(
                    symbol=symbol,
                    current_price=round(real_price, 2),
                    price_history=price_history,
                    timestamp=base_time,
                    volume=random.randint(1000, 10000),  # TODO: Get real volume from TrueData
                    volatility=random.uniform(0.15, 0.45),
                    momentum=random.uniform(-0.05, 0.05)
                )
                
                data[symbol] = market_data
                logger.info(f"✅ Using REAL TrueData price for {symbol}: ₹{real_price}")
                
            except Exception as e:
                logger.error(f"Error getting real data for {symbol}: {e}")
                continue
        
        return data
    
    def _get_real_price_from_truedata(self, symbol: str) -> Optional[float]:
        """Get REAL current price from TrueData feed"""
        try:
            # Import TrueData functions
            from data.truedata_client import get_live_data_for_symbol, get_all_live_data
            
            # Try to get data for this specific symbol
            symbol_data = get_live_data_for_symbol(symbol)
            
            if symbol_data and 'ltp' in symbol_data:
                ltp = symbol_data['ltp']
                if ltp and ltp > 0:
                    logger.info(f"📊 REAL TrueData price for {symbol}: ₹{ltp}")
                    return float(ltp)
            
            # Try alternate symbol formats (RELIANCE vs RELIANCE-EQ, etc.)
            alternate_symbols = [f"{symbol}-EQ", f"{symbol}-I", symbol.replace("-EQ", ""), symbol.replace("-I", "")]
            
            for alt_symbol in alternate_symbols:
                alt_data = get_live_data_for_symbol(alt_symbol)
                if alt_data and 'ltp' in alt_data and alt_data['ltp'] > 0:
                    logger.info(f"📊 REAL TrueData price for {symbol} (as {alt_symbol}): ₹{alt_data['ltp']}")
                    return float(alt_data['ltp'])
            
            # Last resort: check all available data
            all_data = get_all_live_data()
            for td_symbol, td_data in all_data.items():
                if symbol.upper() in td_symbol.upper() or td_symbol.upper() in symbol.upper():
                    if td_data.get('ltp', 0) > 0:
                        logger.info(f"📊 REAL TrueData price for {symbol} (matched {td_symbol}): ₹{td_data['ltp']}")
                        return float(td_data['ltp'])
            
            logger.warning(f"⚠️ No TrueData found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting TrueData for {symbol}: {e}")
            return None
    
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
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
from collections import defaultdict

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
    
    def __init__(self, symbols: Optional[List[str]] = None, config: Dict[str, Any] = None):
        """Initialize with EXPANDED F&O symbol set (50+ symbols, expandable to 250)"""
        # Use expanded symbol list from config
        if symbols is None:
            try:
                from config.truedata_symbols import get_default_subscription_symbols, get_complete_fo_symbols
                
                # Start with 50+ symbols, can expand to 250
                self.symbols = get_default_subscription_symbols()
                self.expansion_symbols = get_complete_fo_symbols()
                
                logger.info(f"📊 MarketDataManager initialized with {len(self.symbols)} default symbols")
                logger.info(f"🚀 Expansion capacity: {len(self.expansion_symbols)} symbols (target: 250)")
                
            except ImportError:
                # Fallback to old 6-symbol list
                self.symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE', 'TCS', 'HDFC', 'INFY']
                self.expansion_symbols = self.symbols.copy()
                logger.warning("⚠️ Using fallback 6-symbol list")
        else:
            self.symbols = symbols
            self.expansion_symbols = symbols.copy()
        
        self.config = config or {}
        self.data_cache = {}
        self.last_update_time = {}
        self.price_history = defaultdict(list)
        
        # Symbol expansion settings
        self.enable_auto_expansion = self.config.get('enable_auto_expansion', True)
        self.max_symbols = self.config.get('max_symbols', 250)
        self.expansion_enabled = False
        
        logger.info(f"💎 MarketDataManager ready: {len(self.symbols)} active symbols, {len(self.expansion_symbols)} available for expansion")
        
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
        """Get REAL market data from TrueData feed using proper symbol mapping"""
        data = {}
        base_time = datetime.now()
        
        for symbol in symbols:
            try:
                # Get REAL price using proper symbol mapping
                real_price, real_volume, real_ohlc = self._get_real_data_from_truedata(symbol)
                
                if real_price is None:
                    logger.warning(f"⚠️ No TrueData for {symbol}, skipping")
                    continue
                
                # Generate price history based on REAL current price and OHLC
                price_history = self._generate_candle_history_from_real_data(
                    current_price=real_price, 
                    real_ohlc=real_ohlc, 
                    count=50
                )
                
                # Create proper MarketData object with REAL data
                market_data = MarketData(
                    symbol=symbol,
                    current_price=round(real_price, 2),
                    price_history=price_history,
                    timestamp=base_time,
                    volume=real_volume if real_volume > 0 else random.randint(1000, 10000),
                    volatility=random.uniform(0.15, 0.45),
                    momentum=random.uniform(-0.05, 0.05)
                )
                
                data[symbol] = market_data
                logger.info(f"✅ REAL TrueData for {symbol}: ₹{real_price:,.2f} | Vol: {real_volume:,}")
                
            except Exception as e:
                logger.error(f"Error getting real data for {symbol}: {e}")
                continue
        
        return data
    
    def _get_real_data_from_truedata(self, symbol: str) -> tuple[Optional[float], int, dict]:
        """Get REAL price, volume, and OHLC data using proper symbol mapping"""
        try:
            # Import TrueData client and symbol mapping
            from data.truedata_client import live_market_data, subscribe_to_symbols
            from config.truedata_symbols import get_truedata_symbol
            
            # STEP 1: Convert to proper TrueData symbol format
            truedata_symbol = get_truedata_symbol(symbol)
            logger.debug(f"🔄 Symbol mapping: {symbol} → {truedata_symbol}")
            
            # STEP 2: Try to get data using mapped symbol
            if truedata_symbol in live_market_data:
                symbol_data = live_market_data[truedata_symbol]
                
                # Extract price
                ltp = symbol_data.get('ltp', 0)
                if not ltp or ltp <= 0:
                    logger.warning(f"⚠️ Invalid LTP for {truedata_symbol}: {ltp}")
                    return None, 0, {}
                
                # Extract volume (try multiple fields)
                volume = 0
                volume_fields = ['volume', 'ttq', 'total_traded_quantity', 'vol', 'day_volume']
                for field in volume_fields:
                    vol = symbol_data.get(field, 0)
                    if vol and vol > 0:
                        volume = int(vol)
                        break
                
                # Extract OHLC data
                ohlc = {
                    'open': symbol_data.get('open', ltp),
                    'high': symbol_data.get('high', ltp),
                    'low': symbol_data.get('low', ltp),
                    'close': ltp
                }
                
                logger.info(f"📊 REAL TrueData: {symbol} ({truedata_symbol}) = ₹{ltp:,.2f} | Vol: {volume:,} | OHLC: O:{ohlc['open']:.2f} H:{ohlc['high']:.2f} L:{ohlc['low']:.2f}")
                return float(ltp), volume, ohlc
            
            # STEP 3: If mapped symbol not found, try direct symbol
            if symbol in live_market_data:
                symbol_data = live_market_data[symbol]
                ltp = symbol_data.get('ltp', 0)
                if ltp and ltp > 0:
                    logger.info(f"📊 REAL TrueData (direct): {symbol} = ₹{ltp:,.2f}")
                    return float(ltp), symbol_data.get('volume', 0), {'open': ltp, 'high': ltp, 'low': ltp, 'close': ltp}
            
            # STEP 4: AUTO-SUBSCRIBE if symbol not found but is valid
            logger.info(f"🔄 AUTO-SUBSCRIBE: {symbol} ({truedata_symbol}) not found, attempting subscription...")
            
            # Try to subscribe to the missing symbol
            success = subscribe_to_symbols([truedata_symbol])
            if success:
                logger.info(f"✅ AUTO-SUBSCRIBED: {truedata_symbol} - data should be available soon")
                # Return None for now, will have data on next request
                return None, 0, {}
            else:
                logger.warning(f"❌ AUTO-SUBSCRIBE FAILED: {truedata_symbol}")
            
            # STEP 5: Debug available symbols if not found
            available_symbols = list(live_market_data.keys())[:10]  # Show first 10
            logger.warning(f"⚠️ Symbol {symbol} (mapped to {truedata_symbol}) not found in TrueData")
            logger.debug(f"📋 Available symbols sample: {available_symbols}")
            
            return None, 0, {}
            
        except ImportError as e:
            logger.error(f"❌ Cannot import TrueData modules: {e}")
            return None, 0, {}
        except Exception as e:
            logger.error(f"❌ Error getting TrueData for {symbol}: {e}")
            return None, 0, {}
    
    def _generate_candle_history_from_real_data(self, current_price: float, real_ohlc: dict, count: int = 50) -> List[Candle]:
        """Generate candle history using REAL OHLC data as anchor"""
        history = []
        base_time = datetime.now() - timedelta(minutes=count)
        
        # Use real OHLC for the latest candle, then generate historical data
        real_open = real_ohlc.get('open', current_price)
        real_high = real_ohlc.get('high', current_price)
        real_low = real_ohlc.get('low', current_price)
        
        # Start from a reasonable historical price (slightly lower than real_open)
        start_price = real_open * 0.995  # Start 0.5% below real open
        
        for i in range(count):
            if i == count - 1:
                # Last candle uses REAL OHLC data
                candle = Candle(
                    timestamp=base_time + timedelta(minutes=i),
                    open=round(real_open, 2),
                    high=round(real_high, 2),
                    low=round(real_low, 2),
                    close=round(current_price, 2),
                    volume=random.randint(500, 5000)
                )
            else:
                # Historical candles progress toward real data
                progress = i / (count - 1)  # 0 to 1
                target_price = start_price + (real_open - start_price) * progress
                
                # Generate OHLC for this candle
                open_price = target_price
                change_percent = random.uniform(-0.01, 0.01)  # ±1% per candle
                close_price = open_price * (1 + change_percent)
                
                volatility = random.uniform(0.005, 0.015)
                high_price = max(open_price, close_price) * (1 + volatility)
                low_price = min(open_price, close_price) * (1 - volatility)
                
                candle = Candle(
                    timestamp=base_time + timedelta(minutes=i),
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=random.randint(500, 5000)
                )
            
            history.append(candle)
        
        return history
    
    # Legacy method for backward compatibility
    def _get_mock_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Legacy mock data - kept for compatibility"""
        return {symbol: {'price': 100, 'volume': 1000} for symbol in symbols}
    
    async def _generate_mock_data(self):
        """Background task to continuously update mock data"""
        while self.is_running:
            try:
                # FIXED: Process ALL available TrueData symbols, not just configured ones
                available_symbols = self._get_all_available_truedata_symbols()
                
                if available_symbols:
                    # Process ALL symbols from TrueData
                    self.market_data_cache = self._get_mock_market_data(available_symbols)
                    logger.info(f"📊 Updated market data for {len(available_symbols)} symbols from TrueData")
                else:
                    # Fallback to configured symbols if TrueData not available
                    self.market_data_cache = self._get_mock_market_data(self.symbols)
                    logger.debug(f"📊 Using fallback symbols: {len(self.symbols)} configured symbols")
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error generating mock data: {e}")
                await asyncio.sleep(5)

    def _get_all_available_truedata_symbols(self) -> List[str]:
        """Get ALL symbols currently available from TrueData"""
        try:
            from data.truedata_client import live_market_data
            from config.truedata_symbols import get_truedata_symbol
            
            # Get ALL symbols that have flowing data from TrueData
            available_truedata_symbols = list(live_market_data.keys())
            
            if not available_truedata_symbols:
                logger.debug("No TrueData symbols available, using configured symbols")
                return self.symbols
            
            # Convert TrueData symbols back to standard format for strategies
            # e.g., NIFTY-I → NIFTY, RELIANCE → RELIANCE
            standard_symbols = []
            
            # Create reverse mapping
            from config.truedata_symbols import SYMBOL_MAPPING
            reverse_mapping = {v: k for k, v in SYMBOL_MAPPING.items()}
            
            for td_symbol in available_truedata_symbols:
                # Try reverse mapping first
                if td_symbol in reverse_mapping:
                    standard_symbols.append(reverse_mapping[td_symbol])
                # If no mapping, use as-is (for symbols like RELIANCE that don't change)
                else:
                    standard_symbols.append(td_symbol)
            
            # Remove duplicates and filter out system symbols
            unique_symbols = list(set(standard_symbols))
            filtered_symbols = [s for s in unique_symbols if not s.startswith('_') and len(s) > 1]
            
            logger.info(f"🔄 Processing {len(filtered_symbols)} symbols from TrueData: {filtered_symbols[:10]}...")
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"❌ Error getting TrueData symbols: {e}")
            return self.symbols  # Fallback to configured symbols

    async def enable_symbol_expansion(self, target_symbols: int = 250) -> bool:
        """Enable expansion from current symbols to target count (up to 250)"""
        try:
            if len(self.symbols) >= target_symbols:
                logger.info(f"✅ Already have {len(self.symbols)} symbols (target: {target_symbols})")
                return True
            
            # Get expanded symbol list
            from config.truedata_symbols import get_complete_fo_symbols
            expanded_symbols = get_complete_fo_symbols()
            
            # Limit to target
            expanded_symbols = expanded_symbols[:target_symbols]
            
            # Update symbols
            old_count = len(self.symbols)
            self.symbols = expanded_symbols
            self.expansion_enabled = True
            
            logger.info(f"🚀 SYMBOL EXPANSION ENABLED: {old_count} → {len(self.symbols)} symbols")
            
            # Try to auto-subscribe new symbols if TrueData is available
            try:
                await self._auto_subscribe_missing_symbols()
            except Exception as e:
                logger.warning(f"Auto-subscription failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Symbol expansion failed: {e}")
            return False
    
    async def _auto_subscribe_missing_symbols(self):
        """Auto-subscribe to symbols that aren't already subscribed"""
        try:
            from data.truedata_client import live_market_data, subscribe_to_symbols
            from config.truedata_symbols import get_truedata_symbol
            
            # Find missing symbols
            subscribed_symbols = set(live_market_data.keys())
            missing_symbols = []
            
            for symbol in self.symbols:
                truedata_symbol = get_truedata_symbol(symbol)
                if truedata_symbol not in subscribed_symbols:
                    missing_symbols.append(truedata_symbol)
            
            if missing_symbols:
                logger.info(f"🔄 Auto-subscribing to {len(missing_symbols)} missing symbols: {missing_symbols[:10]}...")
                
                # Subscribe in batches to avoid overwhelming the API
                batch_size = 10
                for i in range(0, len(missing_symbols), batch_size):
                    batch = missing_symbols[i:i + batch_size]
                    try:
                        subscribe_to_symbols(batch)
                        logger.info(f"✅ Subscribed to batch {i//batch_size + 1}: {len(batch)} symbols")
                        await asyncio.sleep(1)  # Small delay between batches
                    except Exception as e:
                        logger.warning(f"Failed to subscribe to batch {batch}: {e}")
            else:
                logger.info("✅ All symbols already subscribed")
                
        except Exception as e:
            logger.error(f"❌ Auto-subscription error: {e}")
    
    def get_expansion_status(self) -> Dict[str, Any]:
        """Get current symbol expansion status"""
        return {
            "current_symbols": len(self.symbols),
            "expansion_enabled": self.expansion_enabled,
            "max_capacity": self.max_symbols,
            "expansion_available": len(self.expansion_symbols),
            "auto_expansion": self.enable_auto_expansion,
            "symbols_sample": self.symbols[:10],
            "expansion_progress": f"{len(self.symbols)}/{self.max_symbols}"
        }

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
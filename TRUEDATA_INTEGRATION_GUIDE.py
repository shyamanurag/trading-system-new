#!/usr/bin/env python3
"""
TrueData Integration Guide & Implementation
==========================================

This file provides a complete guide and implementation for integrating TrueData
market data services into your trading software. It includes configuration,
connection management, data handling, and usage examples.

Author: Trading System Team
Date: 2024
"""

import asyncio
import logging
import json
import os
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

@dataclass
class TrueDataConfig:
    """
    TrueData Configuration Class
    
    This class manages all TrueData connection parameters and settings.
    Modify these values according to your TrueData account credentials.
    """
    
    # Connection Settings
    username: str = "your_username"  # Replace with your TrueData username
    password: str = "your_password"  # Replace with your TrueData password
    url: str = "push.truedata.in"    # TrueData server URL
    port: int = 8084                 # WebSocket port
    live_port: int = 8086            # Live data port
    
    # Connection Behavior
    reconnect_delay: int = 5         # Seconds between reconnection attempts
    max_reconnect_attempts: int = 5  # Maximum reconnection attempts
    connection_timeout: int = 30     # Connection timeout in seconds
    
    # Data Settings
    symbol_limit: int = 50           # Maximum symbols for trial account
    data_timeout: int = 60           # Data freshness timeout in seconds
    cache_duration: int = 300        # Cache duration in seconds
    
    # Logging
    log_level: int = logging.INFO
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    @property
    def ws_url(self) -> str:
        """Get WebSocket URL"""
        return f"wss://{self.url}:{self.port}"
    
    @property
    def live_url(self) -> str:
        """Get live data URL"""
        return f"wss://{self.url}:{self.live_port}"
    
    def validate_symbols(self, symbols: List[str]) -> bool:
        """Validate if number of symbols is within limit"""
        return len(symbols) <= self.symbol_limit
    
    def get_symbol_mapping(self, symbol: str) -> str:
        """Map symbol to TrueData format"""
        if not symbol.endswith(('-EQ', '-I', '-F')):
            return f"{symbol}-EQ"
        return symbol

# =============================================================================
# DATA MODELS
# =============================================================================

class MarketDataType(Enum):
    """Market data types"""
    TICK = "tick"
    OHLC = "ohlc"
    DEPTH = "depth"
    OPTION_CHAIN = "option_chain"

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    timestamp: datetime
    data_type: MarketDataType
    price: Optional[float] = None
    volume: Optional[int] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_volume: Optional[int] = None
    ask_volume: Optional[int] = None
    raw_data: Optional[Dict] = None

@dataclass
class ConnectionStatus:
    """Connection status information"""
    connected: bool = False
    last_connected: Optional[datetime] = None
    connection_attempts: int = 0
    last_error: Optional[str] = None
    subscribed_symbols: List[str] = None

# =============================================================================
# CORE TRUEDATA FEED IMPLEMENTATION
# =============================================================================

class TrueDataFeed:
    """
    TrueData WebSocket Feed Implementation
    
    This class handles real-time market data streaming from TrueData.
    It manages WebSocket connections, subscriptions, and data processing.
    """
    
    def __init__(self, config: TrueDataConfig):
        self.config = config
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.subscribers: Dict[str, List[Callable]] = {}
        self.status = ConnectionStatus()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("TrueDataFeed")
        logger.setLevel(self.config.log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config.log_format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def connect(self) -> bool:
        """
        Establish connection to TrueData WebSocket
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to TrueData at {self.config.ws_url}")
            
            self.websocket = await websockets.connect(
                self.config.ws_url,
                ssl=True,
                extra_headers={
                    'Authorization': f'Basic {self.config.username}:{self.config.password}'
                },
                ping_interval=30,
                ping_timeout=10
            )
            
            self.connected = True
            self.status.connected = True
            self.status.last_connected = datetime.now()
            self.status.connection_attempts = 0
            self.status.last_error = None
            
            self.logger.info("✅ Successfully connected to TrueData")
            return True
            
        except Exception as e:
            self.status.last_error = str(e)
            self.status.connection_attempts += 1
            self.logger.error(f"❌ Failed to connect to TrueData: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from TrueData WebSocket
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.websocket:
                await self.websocket.close()
            
            self.connected = False
            self.status.connected = False
            self.logger.info("🔌 Disconnected from TrueData")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """
        Subscribe to market data for given symbols
        
        Args:
            symbols: List of symbols to subscribe to
            
        Returns:
            bool: True if subscription successful
        """
        if not self.connected:
            if not await self.connect():
                return False
        
        # Validate symbol limit
        if not self.config.validate_symbols(symbols):
            self.logger.error(f"Symbol limit exceeded. Max: {self.config.symbol_limit}")
            return False
        
        try:
            # Map symbols to TrueData format
            mapped_symbols = [self.config.get_symbol_mapping(sym) for sym in symbols]
            
            subscription_msg = {
                "type": "subscribe",
                "symbols": mapped_symbols
            }
            
            await self.websocket.send(json.dumps(subscription_msg))
            
            # Update status
            self.status.subscribed_symbols = symbols
            
            self.logger.info(f"📡 Subscribed to symbols: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to symbols: {e}")
            return False
    
    async def unsubscribe(self, symbols: List[str]) -> bool:
        """
        Unsubscribe from market data for given symbols
        
        Args:
            symbols: List of symbols to unsubscribe from
            
        Returns:
            bool: True if unsubscription successful
        """
        if not self.connected:
            return False
        
        try:
            mapped_symbols = [self.config.get_symbol_mapping(sym) for sym in symbols]
            
            unsubscribe_msg = {
                "type": "unsubscribe",
                "symbols": mapped_symbols
            }
            
            await self.websocket.send(json.dumps(unsubscribe_msg))
            
            # Update status
            if self.status.subscribed_symbols:
                for sym in symbols:
                    if sym in self.status.subscribed_symbols:
                        self.status.subscribed_symbols.remove(sym)
            
            self.logger.info(f"📡 Unsubscribed from symbols: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from symbols: {e}")
            return False
    
    async def add_subscriber(self, symbol: str, callback: Callable):
        """
        Add a callback function for a symbol
        
        Args:
            symbol: Symbol to subscribe to
            callback: Function to call when data is received
        """
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.logger.info(f"Added subscriber for {symbol}")
    
    async def remove_subscriber(self, symbol: str, callback: Callable):
        """
        Remove a callback function for a symbol
        
        Args:
            symbol: Symbol to unsubscribe from
            callback: Function to remove
        """
        if symbol in self.subscribers and callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)
            self.logger.info(f"Removed subscriber for {symbol}")
    
    async def process_message(self, message: str):
        """
        Process incoming WebSocket message
        
        Args:
            message: Raw message from WebSocket
        """
        try:
            data = json.loads(message)
            symbol = data.get('symbol')
            
            if symbol and symbol in self.subscribers:
                # Create market data object
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    data_type=MarketDataType.TICK,
                    price=data.get('price'),
                    volume=data.get('volume'),
                    raw_data=data
                )
                
                # Call all subscribers
                for callback in self.subscribers[symbol]:
                    try:
                        await callback(market_data)
                    except Exception as e:
                        self.logger.error(f"Error in subscriber callback: {e}")
                        
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to TrueData
        
        Returns:
            bool: True if reconnection successful
        """
        if self.status.connection_attempts >= self.config.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return False
        
        self.status.connection_attempts += 1
        self.logger.info(f"🔄 Attempting to reconnect (attempt {self.status.connection_attempts})")
        
        await asyncio.sleep(self.config.reconnect_delay)
        return await self.connect()
    
    async def start(self):
        """
        Start the TrueData feed - main event loop
        
        This method runs continuously, handling incoming data and reconnections.
        """
        self.logger.info("🚀 Starting TrueData feed...")
        
        while True:
            try:
                if not self.connected:
                    if not await self.connect():
                        await asyncio.sleep(self.config.reconnect_delay)
                        continue
                
                # Listen for messages
                async for message in self.websocket:
                    await self.process_message(message)
                    
            except websockets.ConnectionClosed:
                self.logger.warning("Connection to TrueData closed")
                self.connected = False
                self.status.connected = False
                await self.reconnect()
                
            except Exception as e:
                self.logger.error(f"Error in TrueData feed: {e}")
                self.connected = False
                self.status.connected = False
                await self.reconnect()
    
    async def stop(self):
        """Stop the TrueData feed"""
        self.logger.info("🛑 Stopping TrueData feed...")
        await self.disconnect()

# =============================================================================
# HISTORICAL DATA PROVIDER
# =============================================================================

class TrueDataHistorical:
    """
    TrueData Historical Data Provider
    
    This class handles historical market data retrieval from TrueData.
    """
    
    def __init__(self, config: TrueDataConfig):
        self.config = config
        self.logger = logging.getLogger("TrueDataHistorical")
        
    async def get_historical_data(self, 
                                symbol: str,
                                start_time: datetime,
                                end_time: datetime,
                                bar_size: str = "1 min") -> pd.DataFrame:
        """
        Get historical data for symbol
        
        Args:
            symbol: Symbol to get data for
            start_time: Start time for data
            end_time: End time for data
            bar_size: Bar size (1 min, 5 min, 1 day, etc.)
            
        Returns:
            pd.DataFrame: Historical data
        """
        try:
            # This is a placeholder - you would integrate with TrueData's historical API
            # For now, we'll return sample data
            
            self.logger.info(f"Getting historical data for {symbol} from {start_time} to {end_time}")
            
            # Sample data structure
            data = {
                'timestamp': pd.date_range(start=start_time, end=end_time, freq='1min'),
                'open': [100.0] * 100,
                'high': [101.0] * 100,
                'low': [99.0] * 100,
                'close': [100.5] * 100,
                'volume': [1000] * 100
            }
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()

# =============================================================================
# MAIN TRUEDATA PROVIDER CLASS
# =============================================================================

class TrueDataProvider:
    """
    Main TrueData Provider Class
    
    This is the main class that combines real-time and historical data
    functionality. Use this class for most TrueData operations.
    """
    
    def __init__(self, config: TrueDataConfig):
        self.config = config
        self.feed = TrueDataFeed(config)
        self.historical = TrueDataHistorical(config)
        self.logger = logging.getLogger("TrueDataProvider")
        
    async def connect(self) -> bool:
        """Connect to TrueData services"""
        return await self.feed.connect()
    
    async def disconnect(self) -> bool:
        """Disconnect from TrueData services"""
        return await self.feed.disconnect()
    
    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """Subscribe to market data for symbols"""
        return await self.feed.subscribe(symbols)
    
    async def unsubscribe_market_data(self, symbols: List[str]) -> bool:
        """Unsubscribe from market data for symbols"""
        return await self.feed.unsubscribe(symbols)
    
    async def get_historical_data(self, 
                                symbol: str,
                                start_time: datetime,
                                end_time: datetime,
                                bar_size: str = "1 min") -> pd.DataFrame:
        """Get historical data for symbol"""
        return await self.historical.get_historical_data(symbol, start_time, end_time, bar_size)
    
    async def add_data_callback(self, symbol: str, callback: Callable):
        """Add callback for real-time data"""
        await self.feed.add_subscriber(symbol, callback)
    
    async def remove_data_callback(self, symbol: str, callback: Callable):
        """Remove callback for real-time data"""
        await self.feed.remove_subscriber(symbol, callback)
    
    def get_connection_status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self.feed.status
    
    async def start_feed(self):
        """Start the real-time data feed"""
        await self.feed.start()
    
    async def stop_feed(self):
        """Stop the real-time data feed"""
        await self.feed.stop()

# =============================================================================
# USAGE EXAMPLES AND INTEGRATION GUIDE
# =============================================================================

async def example_basic_usage():
    """
    Basic Usage Example
    
    This example shows how to set up TrueData integration with basic
    real-time data subscription and historical data retrieval.
    """
    print("📚 Basic TrueData Integration Example")
    print("=" * 50)
    
    # 1. Create configuration
    config = TrueDataConfig(
        username="your_username",  # Replace with your credentials
        password="your_password",
        symbol_limit=50
    )
    
    # 2. Create provider
    provider = TrueDataProvider(config)
    
    # 3. Connect to TrueData
    connected = await provider.connect()
    if not connected:
        print("❌ Failed to connect to TrueData")
        return
    
    print("✅ Connected to TrueData")
    
    # 4. Define data callback
    async def on_market_data(data: MarketData):
        print(f"📊 {data.symbol}: {data.price} at {data.timestamp}")
    
    # 5. Subscribe to symbols
    symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE-EQ']
    await provider.subscribe_market_data(symbols)
    
    # 6. Add callbacks
    for symbol in symbols:
        await provider.add_data_callback(symbol, on_market_data)
    
    # 7. Get historical data
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    historical_data = await provider.get_historical_data(
        symbol='NIFTY-I',
        start_time=start_time,
        end_time=end_time,
        bar_size='1 day'
    )
    
    print(f"📈 Historical data points: {len(historical_data)}")
    
    # 8. Cleanup
    await provider.disconnect()
    print("✅ Basic example completed")

async def example_advanced_usage():
    """
    Advanced Usage Example
    
    This example shows advanced features like connection monitoring,
    error handling, and data processing.
    """
    print("\n🚀 Advanced TrueData Integration Example")
    print("=" * 50)
    
    # 1. Create configuration with custom settings
    config = TrueDataConfig(
        username="your_username",
        password="your_password",
        reconnect_delay=3,
        max_reconnect_attempts=10,
        symbol_limit=50
    )
    
    # 2. Create provider
    provider = TrueDataProvider(config)
    
    # 3. Advanced data callback with error handling
    async def advanced_market_data_callback(data: MarketData):
        try:
            # Process market data
            if data.price:
                # Calculate simple moving average (example)
                print(f"📊 {data.symbol}: Price={data.price}, Volume={data.volume}")
                
                # You can add your trading logic here
                if data.price > 100:  # Example condition
                    print(f"🚨 {data.symbol} price above threshold: {data.price}")
                    
        except Exception as e:
            print(f"❌ Error processing market data: {e}")
    
    # 4. Connection monitoring
    async def monitor_connection():
        while True:
            status = provider.get_connection_status()
            print(f"🔍 Connection Status: {status.connected}")
            print(f"   Subscribed Symbols: {status.subscribed_symbols}")
            print(f"   Connection Attempts: {status.connection_attempts}")
            
            if status.last_error:
                print(f"   Last Error: {status.last_error}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    # 5. Start connection monitoring
    monitor_task = asyncio.create_task(monitor_connection())
    
    # 6. Connect and subscribe
    await provider.connect()
    
    symbols = ['NIFTY-I', 'BANKNIFTY-I']
    await provider.subscribe_market_data(symbols)
    
    for symbol in symbols:
        await provider.add_data_callback(symbol, advanced_market_data_callback)
    
    # 7. Run for a while
    print("🔄 Running for 60 seconds...")
    await asyncio.sleep(60)
    
    # 8. Cleanup
    monitor_task.cancel()
    await provider.disconnect()
    print("✅ Advanced example completed")

# =============================================================================
# INTEGRATION CHECKLIST
# =============================================================================

def integration_checklist():
    """
    Integration Checklist
    
    Use this checklist to ensure proper TrueData integration.
    """
    print("\n📋 TrueData Integration Checklist")
    print("=" * 50)
    
    checklist = [
        "✅ Install required packages: websockets, pandas, asyncio",
        "✅ Get TrueData account credentials",
        "✅ Configure environment variables or config file",
        "✅ Test connection with TrueData servers",
        "✅ Validate symbol limits for your account type",
        "✅ Implement error handling and reconnection logic",
        "✅ Set up logging for debugging",
        "✅ Test with sample symbols before production",
        "✅ Implement data validation and processing",
        "✅ Set up monitoring and health checks",
        "✅ Handle connection timeouts and failures",
        "✅ Implement proper cleanup on shutdown",
        "✅ Test with your trading logic",
        "✅ Monitor data quality and latency",
        "✅ Set up alerts for connection issues"
    ]
    
    for item in checklist:
        print(item)

# =============================================================================
# CONFIGURATION EXAMPLES
# =============================================================================

def configuration_examples():
    """
    Configuration Examples
    
    Different configuration examples for various use cases.
    """
    print("\n⚙️ Configuration Examples")
    print("=" * 50)
    
    # Example 1: Trial Account
    print("1. Trial Account Configuration:")
    trial_config = TrueDataConfig(
        username="trial_user",
        password="trial_pass",
        symbol_limit=50,
        reconnect_delay=5
    )
    print(f"   Username: {trial_config.username}")
    print(f"   Symbol Limit: {trial_config.symbol_limit}")
    print(f"   Reconnect Delay: {trial_config.reconnect_delay}s")
    
    # Example 2: Production Account
    print("\n2. Production Account Configuration:")
    prod_config = TrueDataConfig(
        username="prod_user",
        password="prod_pass",
        symbol_limit=500,  # Higher limit for paid accounts
        reconnect_delay=2,
        max_reconnect_attempts=20,
        connection_timeout=60
    )
    print(f"   Username: {prod_config.username}")
    print(f"   Symbol Limit: {prod_config.symbol_limit}")
    print(f"   Max Reconnect Attempts: {prod_config.max_reconnect_attempts}")
    
    # Example 3: High-Frequency Trading
    print("\n3. High-Frequency Trading Configuration:")
    hft_config = TrueDataConfig(
        username="hft_user",
        password="hft_pass",
        reconnect_delay=1,
        max_reconnect_attempts=50,
        connection_timeout=10,
        data_timeout=5
    )
    print(f"   Reconnect Delay: {hft_config.reconnect_delay}s")
    print(f"   Connection Timeout: {hft_config.connection_timeout}s")
    print(f"   Data Timeout: {hft_config.data_timeout}s")

# =============================================================================
# TROUBLESHOOTING GUIDE
# =============================================================================

def troubleshooting_guide():
    """
    Troubleshooting Guide
    
    Common issues and solutions for TrueData integration.
    """
    print("\n🔧 Troubleshooting Guide")
    print("=" * 50)
    
    issues = {
        "Connection Failed": [
            "Check username and password",
            "Verify server URL and port",
            "Check internet connection",
            "Ensure account is active",
            "Try different port numbers"
        ],
        "Symbol Limit Exceeded": [
            "Reduce number of subscribed symbols",
            "Upgrade to paid account for higher limits",
            "Use symbol rotation if needed"
        ],
        "Data Not Receiving": [
            "Check symbol format (add -EQ suffix for equities)",
            "Verify subscription was successful",
            "Check callback functions",
            "Monitor connection status"
        ],
        "High Latency": [
            "Check internet connection quality",
            "Use closer server locations if available",
            "Optimize data processing",
            "Consider dedicated connection"
        ],
        "Frequent Disconnections": [
            "Increase reconnect delay",
            "Check network stability",
            "Monitor server status",
            "Implement exponential backoff"
        ]
    }
    
    for issue, solutions in issues.items():
        print(f"\n❌ {issue}:")
        for solution in solutions:
            print(f"   • {solution}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """
    Main execution function
    
    This function demonstrates the complete TrueData integration flow.
    """
    print("🚀 TrueData Integration Guide & Examples")
    print("=" * 60)
    
    # Show configuration examples
    configuration_examples()
    
    # Show integration checklist
    integration_checklist()
    
    # Show troubleshooting guide
    troubleshooting_guide()
    
    # Run examples (commented out to avoid actual connections)
    print("\n📚 Running Examples (commented out for safety)")
    print("Uncomment the lines below to run actual examples:")
    print("# await example_basic_usage()")
    print("# await example_advanced_usage()")
    
    print("\n✅ Integration guide completed!")
    print("\n📖 Next Steps:")
    print("1. Replace 'your_username' and 'your_password' with your credentials")
    print("2. Test connection with a few symbols")
    print("3. Implement your trading logic in the callbacks")
    print("4. Add proper error handling and monitoring")
    print("5. Deploy to production with appropriate settings")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 
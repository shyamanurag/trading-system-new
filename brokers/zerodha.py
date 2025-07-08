"""
Zerodha Broker Integration
Handles trading operations with Zerodha broker
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time
from kiteconnect import KiteConnect

logger = logging.getLogger(__name__)

class ZerodhaIntegration:
    """Enhanced Zerodha integration with real API support"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.user_id = config.get('user_id')
        self.access_token = config.get('access_token')
        self.pin = config.get('pin')
        
        # Initialize KiteConnect
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            if self.access_token:
                self.kite.set_access_token(self.access_token)
        else:
            self.kite = None
            logger.warning("Zerodha API key not provided - using mock mode")
        
        self.is_connected = False
        self.mock_mode = config.get('mock_mode', True)  # Default to mock for safety
        self.mock_orders = {}
        self.mock_positions = {}
        
        # Rate limiting
        self.last_order_time = 0
        self.order_rate_limit = 1.0  # 1 second between orders
        
    async def connect(self) -> bool:
        """Connect to Zerodha API"""
        try:
            if self.mock_mode:
                logger.info("🔧 Zerodha running in MOCK mode")
                self.is_connected = True
                return True
            
            if not self.kite or not self.access_token:
                logger.error("❌ Zerodha connection failed: Missing API credentials")
                return False
            
            # Test connection with a simple API call
            profile = await self._async_api_call(self.kite.profile)
            if profile:
                self.is_connected = True
                logger.info(f"✅ Connected to Zerodha API for user: {profile.get('user_name', 'Unknown')}")
                return True
            else:
                logger.error("❌ Zerodha connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Zerodha connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Zerodha"""
        self.is_connected = False
        logger.info("🔌 Disconnected from Zerodha")
    
    async def _async_api_call(self, func, *args, **kwargs):
        """Execute Zerodha API call asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Zerodha API call failed: {e}")
            raise
    
    async def place_order(self, order_params: Dict) -> Optional[str]:
        """
        Place order with Zerodha - REAL IMPLEMENTATION
        Args:
            order_params: Order parameters
        Returns:
            Order ID if successful
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Not connected to Zerodha")
            
            # Rate limiting
            current_time = time.time()
            if (current_time - self.last_order_time) < self.order_rate_limit:
                await asyncio.sleep(self.order_rate_limit - (current_time - self.last_order_time))
            
            order_id = f"ORDER_{int(time.time())}"
            
            if self.mock_mode:
                # Enhanced mock mode for testing
                order = {
                    'order_id': order_id,
                    'tradingsymbol': order_params.get('symbol'),
                    'transaction_type': order_params.get('transaction_type'),
                    'quantity': order_params.get('quantity'),
                    'price': order_params.get('price'),
                    'order_type': order_params.get('order_type', 'MARKET'),
                    'status': 'COMPLETE',
                    'timestamp': datetime.now().isoformat(),
                    'average_price': order_params.get('price', 0),
                    'filled_quantity': order_params.get('quantity', 0)
                }
                self.mock_orders[order_id] = order
                logger.info(f"🔧 MOCK order placed: {order_id} for {order_params.get('symbol')}")
                self.last_order_time = time.time()
                return order_id
            else:
                # REAL Zerodha API implementation
                if not self.kite:
                    raise Exception("KiteConnect not initialized")
                
                # Validate parameters
                if not self._validate_order_params(order_params):
                    logger.error(f"Invalid order parameters: {order_params}")
                    return None
                
                # Map internal symbol to exchange symbol
                exchange_symbol = self._map_symbol_to_exchange(order_params['symbol'])
                if not exchange_symbol:
                    logger.error(f"Symbol mapping failed: {order_params['symbol']}")
                    return None
                
                # Prepare Kite order parameters
                kite_params = {
                    'variety': 'regular',
                    'exchange': self._get_exchange_for_symbol(order_params['symbol']),
                    'tradingsymbol': exchange_symbol,
                    'transaction_type': order_params['transaction_type'],
                    'quantity': order_params['quantity'],
                    'product': 'MIS',  # Intraday
                    'order_type': order_params.get('order_type', 'MARKET'),
                    'validity': 'DAY',
                    'tag': f"AI_TRADING_{self.user_id}"
                }
                
                # Add price for limit orders
                if 'price' in order_params and order_params['price']:
                    kite_params['price'] = order_params['price']
                
                # Add trigger price for SL orders
                if 'trigger_price' in order_params and order_params['trigger_price']:
                    kite_params['trigger_price'] = order_params['trigger_price']
                
                # Place order through Kite API
                result = await self._async_api_call(self.kite.place_order, **kite_params)
                
                if result and 'order_id' in result:
                    logger.info(f"✅ Real order placed: {result['order_id']} for {order_params['symbol']}")
                    self.last_order_time = time.time()
                    return result['order_id']
                else:
                    logger.error(f"❌ Order placement failed: {result}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
    
    def _validate_order_params(self, order_params: Dict) -> bool:
        """Validate order parameters"""
        required_fields = ['symbol', 'transaction_type', 'quantity']
        for field in required_fields:
            if field not in order_params:
                logger.error(f"Missing required field: {field}")
                return False
        
        if order_params['quantity'] <= 0:
            logger.error(f"Invalid quantity: {order_params['quantity']}")
            return False
        
        if order_params['transaction_type'] not in ['BUY', 'SELL']:
            logger.error(f"Invalid transaction type: {order_params['transaction_type']}")
            return False
        
        return True
    
    def _map_symbol_to_exchange(self, symbol: str) -> str:
        """Map internal symbol to exchange format"""
        # Index symbols
        if symbol.endswith('-I'):
            return symbol.replace('-I', '')  # NIFTY-I -> NIFTY
        
        # Regular equity symbols
        return symbol
    
    def _get_exchange_for_symbol(self, symbol: str) -> str:
        """Get appropriate exchange for symbol"""
        if symbol.endswith('-I'):
            return 'NSE'  # Indices
        return 'NSE'  # Default to NSE for equities
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status"""
        try:
            if self.mock_mode:
                return self.mock_orders.get(order_id)
            else:
                if not self.kite:
                    return None
                return await self._async_api_call(self.kite.order_history, order_id)
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            if self.mock_mode:
                if order_id in self.mock_orders:
                    self.mock_orders[order_id]['status'] = 'CANCELLED'
                    return True
                return False
            else:
                if not self.kite:
                    return False
                result = await self._async_api_call(self.kite.cancel_order, 'regular', order_id)
                return bool(result)
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    async def get_positions(self) -> Dict:
        """Get current positions"""
        try:
            if self.mock_mode:
                return {'net': [], 'day': []}
            else:
                if not self.kite:
                    return {'net': [], 'day': []}
                return await self._async_api_call(self.kite.positions)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'net': [], 'day': []}
    
    async def get_margins(self) -> Dict:
        """Get margin information"""
        try:
            if self.mock_mode:
                return {'equity': {'available': {'cash': 100000}}}
            else:
                if not self.kite:
                    return {'equity': {'available': {'cash': 0}}}
                return await self._async_api_call(self.kite.margins)
        except Exception as e:
            logger.error(f"Error getting margins: {e}")
            return {'equity': {'available': {'cash': 0}}}
    
    async def initialize(self) -> bool:
        """Initialize the Zerodha client"""
        return await self.connect()
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        # Simple check - market open 9:15 AM to 3:30 PM on weekdays
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        
        return market_open <= now <= market_close

    async def modify_order(self, order_id: str, order_params: Dict) -> Dict:
        """Modify an existing order"""
        if not self.is_connected:
            raise ConnectionError("Not connected to Zerodha")
        
        if self.mock_mode:
            if order_id in self.mock_orders:
                self.mock_orders[order_id].update(order_params)
                self.mock_orders[order_id]['modified_at'] = datetime.now().isoformat()
                logger.info(f"Mock order modified: {order_id}")
                return self.mock_orders[order_id]
            else:
                raise ValueError(f"Order {order_id} not found")
        else:
            # Real implementation would call Zerodha API
            raise NotImplementedError("Real Zerodha order modification not implemented")
    
    async def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.is_connected:
            return {}
        
        if self.mock_mode:
            return {
                'user_id': self.user_id or 'MOCK_USER',
                'broker': 'Zerodha',
                'account_type': 'MIS',
                'exchange': 'NSE',
                'products': ['CNC', 'MIS', 'NRML'],
                'order_types': ['MARKET', 'LIMIT', 'SL', 'SL-M'],
                'last_updated': datetime.now().isoformat()
            }
        else:
            # Real implementation would fetch from Zerodha API
            return {}
    
    async def get_holdings(self) -> Dict:
        """Get current holdings"""
        if not self.is_connected:
            return {}
        
        if self.mock_mode:
            return {
                'holdings': self.mock_positions,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Real implementation would call Zerodha API
            return {}
    
    async def _initialize_websocket(self):
        """Initialize WebSocket connection for real-time data"""
        if self.mock_mode:
            self.is_connected = True
            logger.info("Mock WebSocket connection established")
        else:
            # Real WebSocket implementation would go here
            logger.info("Real WebSocket connection not implemented")
    
    def get_connection_status(self) -> Dict:
        """Get connection status"""
        return {
            'is_connected': self.is_connected,
            'mock_mode': self.mock_mode
        } 
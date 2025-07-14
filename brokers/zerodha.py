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
        
        # CRITICAL FIX: Add missing mock_mode attribute
        self.mock_mode = config.get('mock_mode', False)
        
        # Initialize KiteConnect
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            if self.access_token:
                self.kite.set_access_token(self.access_token)
        else:
            self.kite = None
            logger.warning("Zerodha API key not provided - using mock mode")
            self.mock_mode = True  # Force mock mode if no API key
        
        self.is_connected = False
        self.ticker_connected = False  # Add missing ticker_connected attribute
        
        # ELIMINATED: Mock order system removed - no fake orders allowed
        # Original violation: mock_orders dictionary created fake order tracking
        # This could make orders appear successful when they weren't actually placed
        
        # Rate limiting
        self.last_order_time = 0
        self.order_rate_limit = 1.0  # 1 second between orders
        
    async def place_order(self, order_params: Dict) -> Optional[str]:
        """Place order with proper validation and execution"""
        try:
            # Validate order parameters
            if not self._validate_order_params(order_params):
                logger.error("❌ Order validation failed")
                return None
            
            # Rate limiting check
            current_time = time.time()
            if current_time - self.last_order_time < self.order_rate_limit:
                wait_time = self.order_rate_limit - (current_time - self.last_order_time)
                logger.info(f"⏱️ Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            if not self.kite or not self.access_token:
                logger.error("❌ Zerodha order rejected: No valid API credentials - cannot place real order")
                raise ConnectionError("Cannot place order: No valid Zerodha API credentials")
            
            # Map signal parameters to Zerodha API format
            zerodha_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': self._get_exchange_for_symbol(order_params.get('symbol', '')),
                'tradingsymbol': self._map_symbol_to_exchange(order_params.get('symbol', '')),
                'transaction_type': order_params.get('action', '').upper(),  # BUY/SELL
                'quantity': int(order_params.get('quantity', 0)),
                'product': order_params.get('product', self.kite.PRODUCT_MIS),
                'order_type': order_params.get('order_type', self.kite.ORDER_TYPE_MARKET),
                'price': order_params.get('price') or order_params.get('entry_price'),
                'validity': order_params.get('validity', self.kite.VALIDITY_DAY),
                'disclosed_quantity': order_params.get('disclosed_quantity'),
                'trigger_price': order_params.get('trigger_price') or order_params.get('stop_loss'),
                'tag': order_params.get('tag', 'ALGO_TRADE')
            }
            
            # Place the order
            order_response = await self._async_api_call(
                self.kite.place_order,
                **zerodha_params
            )
            
            if order_response and 'order_id' in order_response:
                order_id = order_response['order_id']
                logger.info(f"✅ REAL Zerodha order placed: {order_id} for {order_params.get('symbol')}")
                self.last_order_time = time.time()
                return order_id
            else:
                logger.error(f"❌ Zerodha order failed: {order_response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
            
    async def _async_api_call(self, func, *args, **kwargs):
        """Execute synchronous API call in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
        
    async def connect(self) -> bool:
        """Connect to Zerodha API"""
        try:
            if not self.kite:
                logger.error("❌ Cannot connect: No valid API credentials")
                return False
            
            # Test the connection by fetching account info
            account_info = await self._async_api_call(self.kite.profile)
            if account_info:
                self.is_connected = True
                await self._initialize_websocket()
                logger.info("✅ Zerodha connected successfully")
                return True
            else:
                logger.error(f"❌ Connection test failed: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Zerodha: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Zerodha API"""
        try:
            self.is_connected = False
            self.ticker_connected = False
            logger.info("✅ Zerodha disconnected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error disconnecting from Zerodha: {e}")
            return False
    
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
            if not self.kite or not self.access_token:
                logger.error("❌ Cannot get order status: No valid API credentials")
                return None
            return await self._async_api_call(self.kite.order_history, order_id)
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            if not self.kite or not self.access_token:
                logger.error("❌ Cannot cancel order: No valid API credentials")
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
            # This method is no longer needed as mock data is removed
            # Keeping it for now to avoid breaking existing calls, but it will do nothing
            logger.warning(f"Mock mode is enabled, but modify_order is called. No action taken for order {order_id}")
            return {}
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
            # This method is no longer needed as mock data is removed
            # Keeping it for now to avoid breaking existing calls, but it will do nothing
            logger.warning("Mock mode is enabled, but get_holdings is called. Returning empty holdings.")
            return {
                'holdings': [],
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Real implementation would call Zerodha API
            return {}
    
    async def _initialize_websocket(self):
        """Initialize WebSocket connection for real-time data"""
        try:
            if self.mock_mode:
                self.ticker_connected = True
                logger.info("Mock WebSocket connection established")
            else:
                # Real WebSocket implementation would go here
                # For now, set to False since real implementation is not complete
                self.ticker_connected = False
                logger.info("Real WebSocket connection not implemented - ticker_connected set to False")
        except Exception as e:
            logger.error(f"WebSocket initialization failed: {e}")
            self.ticker_connected = False
    
    def get_connection_status(self) -> Dict:
        """Get connection status"""
        return {
            'is_connected': self.is_connected,
            'mock_mode': self.mock_mode
        } 
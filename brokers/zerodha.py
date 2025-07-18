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
import os

try:
    from kiteconnect import KiteConnect
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("KiteConnect not available - running in mock mode")
    KiteConnect = None

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
        self.sandbox_mode = config.get('sandbox_mode', False)
        self.allow_token_update = config.get('allow_token_update', True)
        
        # Initialize KiteConnect for REAL trading
        if self.api_key and KiteConnect:
            self.kite = KiteConnect(api_key=self.api_key)
            logger.info("🔴 Zerodha initialized for REAL trading")
                
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                logger.info("✅ Zerodha access token set")
            else:
                logger.info("🔧 Zerodha initialized without token - awaiting frontend authentication")
        else:
            self.kite = None
            logger.warning("Zerodha API key not provided or KiteConnect not available")
            self.mock_mode = True  # Force mock mode if no API key
        
        self.is_connected = False
        self.ticker_connected = False
        
        # Rate limiting
        self.last_order_time = 0
        self.order_rate_limit = 1.0  # 1 second between orders
        
    def update_access_token(self, access_token: str):
        """Update access token after frontend authentication"""
        try:
            if self.kite and access_token:
                self.access_token = access_token
                self.kite.set_access_token(access_token)
                logger.info(f"✅ Zerodha access token updated: {access_token[:10]}...")
                
                # Test the connection
                profile = self.kite.profile()
                logger.info(f"✅ Zerodha connection verified - User: {profile.get('user_name', 'Unknown')}")
                self.is_connected = True
                return True
            else:
                logger.error("❌ Cannot update token - KiteConnect not initialized or token invalid")
                return False
        except Exception as e:
            logger.error(f"❌ Error updating Zerodha access token: {e}")
            return False
            
    async def place_order(self, order_params: Dict) -> Optional[str]:
        """Place REAL order on Zerodha"""
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
            
            # Check if we have valid Zerodha connection
            if not self.kite or not self.access_token:
                logger.error("❌ Zerodha order rejected: No valid API credentials")
                return None
            
            # Map signal parameters to Zerodha API format
            action = order_params.get('action', '').upper()
            if not action:
                action = order_params.get('transaction_type', '').upper()
            if not action:
                action = order_params.get('side', '').upper()
            if not action:
                action = 'BUY'  # Default to BUY if no action specified
                
            symbol = order_params.get('symbol', '')
            quantity = int(order_params.get('quantity', 0))
            
            # Build Zerodha order parameters
            zerodha_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': self._get_exchange_for_symbol(symbol),
                'tradingsymbol': self._map_symbol_to_exchange(symbol),
                'transaction_type': action,
                'quantity': quantity,
                'product': order_params.get('product', self.kite.PRODUCT_MIS),
                'order_type': order_params.get('order_type', self.kite.ORDER_TYPE_MARKET),
                'validity': order_params.get('validity', self.kite.VALIDITY_DAY),
                'tag': order_params.get('tag', 'ALGO_TRADE')
            }
            
            # Add price for limit orders
            if zerodha_params['order_type'] != self.kite.ORDER_TYPE_MARKET:
                price = order_params.get('price') or order_params.get('entry_price')
                if price:
                    zerodha_params['price'] = float(price)
            
            # Add trigger price for stop loss orders
            trigger_price = order_params.get('trigger_price') or order_params.get('stop_loss')
            if trigger_price:
                zerodha_params['trigger_price'] = float(trigger_price)
            
            # Add disclosed quantity if specified
            disclosed_quantity = order_params.get('disclosed_quantity')
            if disclosed_quantity:
                zerodha_params['disclosed_quantity'] = int(disclosed_quantity)
            
            logger.info(f"🔄 Placing REAL Zerodha order: {symbol} {action} {quantity}")
            logger.info(f"   Exchange: {zerodha_params['exchange']}, Product: {zerodha_params['product']}")
            
            # Place the REAL order
            order_response = await self._async_api_call(
                self.kite.place_order,
                **zerodha_params
            )
            
            if order_response and 'order_id' in order_response:
                order_id = order_response['order_id']
                logger.info(f"✅ REAL Zerodha order placed successfully: {order_id}")
                logger.info(f"   Symbol: {symbol}, Action: {action}, Quantity: {quantity}")
                self.last_order_time = time.time()
                return order_id
            else:
                logger.error(f"❌ Zerodha order failed: {order_response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing REAL order: {e}")
            return None
            
    async def _async_api_call(self, func, *args, **kwargs):
        """Execute synchronous API call in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        
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
                # REMOVED: Misleading success message - let resilient wrapper handle connection status
                return True
            else:
                logger.error("❌ Connection test failed: No account info returned")
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
        # Check for symbol
        if 'symbol' not in order_params:
            logger.error("Missing required field: symbol")
            return False
        
        # Check for quantity
        if 'quantity' not in order_params:
            logger.error("Missing required field: quantity")
            return False
            
        quantity = order_params['quantity']
        if quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}")
            return False
        
        # Check for transaction type (can be action, transaction_type, or side)
        action = order_params.get('action', '').upper()
        if not action:
            action = order_params.get('transaction_type', '').upper()
        if not action:
            action = order_params.get('side', '').upper()
        
        if not action:
            logger.error("Missing required field: action/transaction_type/side")
            return False
            
        if action not in ['BUY', 'SELL']:
            logger.error(f"Invalid transaction type: {action}")
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
        if not self.is_connected or not self.kite:
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
            # FIXED: Implement real API call instead of returning empty dict
            try:
                # Fetch actual profile from Zerodha API
                profile = await self._async_api_call(self.kite.profile)
                if profile:
                    return {
                        'user_id': profile.get('user_id', self.user_id),
                        'user_name': profile.get('user_name', ''),
                        'email': profile.get('email', ''),
                        'broker': 'Zerodha',
                        'exchanges': profile.get('exchanges', []),
                        'products': profile.get('products', ['CNC', 'MIS', 'NRML']),
                        'order_types': profile.get('order_types', ['MARKET', 'LIMIT', 'SL', 'SL-M']),
                        'avatar_url': profile.get('avatar_url', ''),
                        'last_updated': datetime.now().isoformat(),
                        'connection_status': 'connected'
                    }
                else:
                    logger.warning("⚠️ Zerodha profile returned empty - connection may be invalid")
                    return {}
            except Exception as e:
                logger.error(f"❌ Failed to fetch Zerodha account info: {e}")
                # Return empty dict to indicate connection issue
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
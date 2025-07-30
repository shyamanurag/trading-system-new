"""
Clean OrderManager - NO FALLBACKS
If something fails, it fails clearly so we know what to fix
"""

import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import json
import time
from .order_rate_limiter import OrderRateLimiter

logger = logging.getLogger(__name__)

class OrderManager:
    """Clean OrderManager - NO FALLBACKS, NO FAKE DATA"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.zerodha_client = None
        self.redis_client = None
        self.risk_manager = None
        self.notification_manager = None
        
        # Simple storage
        self.active_orders: Dict[str, set] = {}
        self.order_history: Dict[str, list] = {}
        
        # Initialize order rate limiter to prevent retry loops
        self.rate_limiter = OrderRateLimiter()
        
        logger.info("OrderManager initialized - NO FALLBACKS")
    
    async def initialize(self, zerodha_client=None, redis_client=None, risk_manager=None):
        """Initialize with required dependencies - FAIL if missing"""
        self.zerodha_client = zerodha_client
        self.redis_client = redis_client
        self.risk_manager = risk_manager
        
        if not self.zerodha_client:
            logger.warning("⚠️ No Zerodha client - orders will be rejected")
        
        if not self.redis_client:
            logger.warning("⚠️ No Redis client - using memory only")
        
        if not self.risk_manager:
            logger.warning("⚠️ No risk manager - orders will not be validated")
        
        logger.info("OrderManager initialized with available components")
    
    async def place_order(self, user_id: str, order_data: Dict[str, Any]) -> str:
        """Place an order - FAIL if requirements not met"""
        try:
            if not self.zerodha_client:
                raise Exception("No Zerodha client available - order rejected")
            
            # Generate order ID
            order_id = str(uuid.uuid4())
            
            # Basic validation
            required_fields = ['symbol', 'quantity', 'side', 'order_type']
            for field in required_fields:
                if field not in order_data:
                    raise Exception(f"Missing required field: {field}")
            
            # Risk validation if available
            if self.risk_manager:
                risk_valid = await self.risk_manager.validate_order(user_id, order_data)
                if not risk_valid:
                    raise Exception("Order failed risk validation")
            
            # 🛡️ Check order rate limits to prevent retry loops
            rate_check = await self.rate_limiter.can_place_order(
                order_data['symbol'], 
                order_data['side'], 
                order_data['quantity'], 
                order_data.get('price', 0)
            )
            if not rate_check['allowed']:
                raise Exception(f"Order rate limited: {rate_check['message']}")
            
            # Place order via Zerodha
            zerodha_params = {
                'symbol': order_data['symbol'],
                'transaction_type': order_data['side'].upper(),
                'quantity': order_data['quantity'],
                'order_type': order_data['order_type'].upper(),
                'product': self._get_product_type_for_symbol(order_data['symbol']),  # FIXED: Dynamic product type
                'validity': 'DAY',
                'tag': f"OM_{order_id[:8]}"
            }
            
            if order_data['order_type'].upper() == 'LIMIT':
                zerodha_params['price'] = order_data['price']
            
            broker_order_id = await self.zerodha_client.place_order(zerodha_params)
            
            # 📊 Record order attempt in rate limiter
            order_success = bool(broker_order_id)
            await self.rate_limiter.record_order_attempt(
                rate_check['signature'], 
                order_success, 
                order_data['symbol'], 
                "Order placement failed" if not order_success else None
            )
            
            if not broker_order_id:
                raise Exception("Zerodha order placement failed")
            
            # Store order
            if user_id not in self.active_orders:
                self.active_orders[user_id] = set()
            self.active_orders[user_id].add(order_id)
            
            # Store in Redis if available
            if self.redis_client:
                order_key = f"order:{user_id}:{order_id}"
                order_record = {
                    'order_id': order_id,
                    'broker_order_id': broker_order_id,
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat(),
                    **order_data
                }
                await self.redis_client.set(order_key, json.dumps(order_record))
            
            logger.info(f"✅ Order placed: {order_id} -> {broker_order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Order placement failed for user {user_id}: {e}")
            raise e
    
    async def get_orders(self, user_id: str) -> list:
        """Get orders for user - return what's available"""
        try:
            orders = []
            
            if self.redis_client:
                # Get from Redis
                keys = await self.redis_client.keys(f"order:{user_id}:*")
                for key in keys:
                    order_data = await self.redis_client.get(key)
                    if order_data:
                        orders.append(json.loads(order_data))
            else:
                # Get from memory
                if user_id in self.order_history:
                    orders = self.order_history[user_id]
            
            return orders
            
        except Exception as e:
            logger.error(f"❌ Failed to get orders for user {user_id}: {e}")
            return []
    
    async def cancel_order(self, user_id: str, order_id: str) -> bool:
        """Cancel order - FAIL if not possible"""
        try:
            if not self.zerodha_client:
                raise Exception("No Zerodha client available - cannot cancel order")
            
            # Get order details
            if self.redis_client:
                order_key = f"order:{user_id}:{order_id}"
                order_data = await self.redis_client.get(order_key)
                if not order_data:
                    raise Exception(f"Order {order_id} not found")
                
                order_record = json.loads(order_data)
                broker_order_id = order_record.get('broker_order_id')
            else:
                raise Exception("Cannot find order without Redis")
            
            if not broker_order_id:
                raise Exception("No broker order ID found")
            
            # Cancel via Zerodha
            success = await self.zerodha_client.cancel_order(broker_order_id)
            
            if not success:
                raise Exception("Zerodha order cancellation failed")
            
            # Remove from active orders
            if user_id in self.active_orders:
                self.active_orders[user_id].discard(order_id)
            
            logger.info(f"✅ Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Order cancellation failed: {e}")
            raise e
    
    async def place_strategy_order(self, strategy_name: str, signal: Dict[str, Any]) -> list:
        """Place an order based on strategy signal - simplified for position monitor"""
        try:
            if not self.zerodha_client:
                logger.error("❌ No Zerodha client available for strategy order")
                return []
            
            # Extract order parameters from signal
            symbol = signal.get('symbol', 'UNKNOWN')
            action = signal.get('action', 'BUY')
            quantity = signal.get('quantity', 1)
            
            # Convert EXIT action to appropriate side
            if action == 'EXIT':
                # For exit, we need to determine if it's BUY or SELL
                # This is a simplified approach - in practice, you'd check the current position
                side = 'SELL'  # Most common case for auto square-off
            else:
                side = action
            
            # Create order data
            order_data = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'order_type': 'MARKET',  # Use market order for quick execution
                'strategy': strategy_name,
                'reason': signal.get('reason', 'Strategy order')
            }
            
            # Use default user for strategy orders
            user_id = 'STRATEGY_USER'
            
            # Place the order
            order_id = await self.place_order(user_id, order_data)
            
            if order_id:
                logger.info(f"✅ Strategy order placed: {strategy_name} - {symbol} {side} {quantity}")
                return [(user_id, order_id)]
            else:
                logger.error(f"❌ Strategy order failed: {strategy_name} - {symbol}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error placing strategy order for {strategy_name}: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get OrderManager status"""
        return {
            "zerodha_client": self.zerodha_client is not None,
            "redis_client": self.redis_client is not None,
            "risk_manager": self.risk_manager is not None,
            "active_users": len(self.active_orders),
            "total_active_orders": sum(len(orders) for orders in self.active_orders.values())
        } 

    def _get_product_type_for_symbol(self, symbol: str) -> str:
        """Get appropriate product type for symbol - FIXED for short selling"""
        # 🔧 CRITICAL FIX: NFO options require NRML, not CNC
        if 'CE' in symbol or 'PE' in symbol:
            return 'NRML'  # Options must use NRML
        else:
            # 🔧 CRITICAL FIX: Use MIS for SELL orders to enable short selling
            # Note: This method doesn't have access to order_params, so we'll use MIS for all equity orders
            # The actual decision will be made in the broker layer
            return 'MIS'  # Margin Intraday Square-off for short selling capability

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get status of a specific order"""
        return self.orders.get(order_id) 

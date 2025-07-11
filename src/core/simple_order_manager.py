"""
Simple Order Manager for degraded mode when Redis is not available.
This provides basic order management without external dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleOrderManager:
    """Simple order manager for degraded mode operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.zerodha_client = config.get('zerodha_client')
        self.orders = {}
        self.order_history = []
        self.is_initialized = True
        
        logger.info("✅ SimpleOrderManager initialized for degraded mode")
        
        # Basic attributes for compatibility
        self.user_tracker = None
        self.risk_manager = None
        self.notification_manager = None
        self.trade_allocator = None
        self.system_evolution = None
        self.capital_manager = None
        
    async def async_initialize_components(self):
        """Initialize async components - minimal implementation"""
        logger.info("✅ SimpleOrderManager async components initialized")
        
    async def process_signal(self, signal: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process trading signal - minimal implementation"""
        try:
            logger.info(f"📝 SimpleOrderManager processing signal: {signal['symbol']} {signal['action']}")
            
            # Basic signal processing
            order_id = f"simple_{datetime.now().timestamp()}"
            
            # Store order
            self.orders[order_id] = {
                'order_id': order_id,
                'symbol': signal['symbol'],
                'action': signal['action'],
                'quantity': signal.get('quantity', 1),
                'price': signal.get('price', 0),
                'user_id': user_id,
                'timestamp': datetime.now(),
                'status': 'PENDING'
            }
            
            # Add to history
            self.order_history.append(self.orders[order_id])
            
            logger.info(f"✅ Order {order_id} processed in degraded mode")
            
            return {
                'success': True,
                'order_id': order_id,
                'message': 'Order processed in degraded mode',
                'degraded_mode': True
            }
            
        except Exception as e:
            logger.error(f"❌ SimpleOrderManager error processing signal: {e}")
            return {
                'success': False,
                'error': str(e),
                'degraded_mode': True
            }
            
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        if order_id in self.orders:
            return self.orders[order_id]
        return {'status': 'NOT_FOUND'}
        
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return self.order_history
        
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get active orders"""
        return [order for order in self.orders.values() if order['status'] == 'PENDING']
        
    async def place_strategy_order(self, signal: Dict[str, Any], user_id: str = "system") -> Dict[str, Any]:
        """Place strategy order - compatibility method"""
        return await self.process_signal(signal, user_id) 
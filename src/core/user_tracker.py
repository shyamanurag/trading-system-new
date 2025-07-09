"""
User-specific Order and Position Tracking
Manages user-specific order and position tracking with Redis or in-memory fallback
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class UserTracker:
    """Tracks user-specific orders and positions"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis: Optional[Any] = None
        self.redis_available = False
        
        # Check if Redis is available
        redis_url = config.get('redis_url')
        if redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(redis_url)
                self.redis_available = True
                logger.info("UserTracker: Redis connection configured")
            except Exception as e:
                logger.warning(f"UserTracker: Redis connection failed: {e}")
                self.redis_available = False
        
        # In-memory fallback storage
        if not self.redis_available:
            self.memory_store = {
                'orders': {},
                'positions': {},
                'active_orders': {},
                'active_positions': {},
                'daily_orders': {},
                'daily_positions': {}
            }
            logger.info("UserTracker: Using in-memory fallback storage")
        
    async def track_order(self, user_id: str, order_data: Dict):
        """Track a new order"""
        try:
            order_with_timestamp = {
                **order_data,
                'tracked_at': datetime.now().isoformat()
            }
            
            if self.redis_available and self.redis:
                # Redis storage
                await self.redis.hset(
                    f"user:{user_id}:orders",
                    order_data['order_id'],
                    json.dumps(order_with_timestamp)
                )
                
                if order_data['status'] in ['PENDING', 'OPEN']:
                    await self.redis.sadd(f"user:{user_id}:active_orders", order_data['order_id'])
                    
                date_key = datetime.now().strftime('%Y%m%d')
                await self.redis.sadd(f"user:{user_id}:orders:{date_key}", order_data['order_id'])
            else:
                # In-memory storage
                user_orders_key = f"user:{user_id}:orders"
                if user_orders_key not in self.memory_store['orders']:
                    self.memory_store['orders'][user_orders_key] = {}
                
                self.memory_store['orders'][user_orders_key][order_data['order_id']] = order_with_timestamp
                
                if order_data['status'] in ['PENDING', 'OPEN']:
                    active_key = f"user:{user_id}:active_orders"
                    if active_key not in self.memory_store['active_orders']:
                        self.memory_store['active_orders'][active_key] = set()
                    self.memory_store['active_orders'][active_key].add(order_data['order_id'])
                    
                date_key = datetime.now().strftime('%Y%m%d')
                daily_key = f"user:{user_id}:orders:{date_key}"
                if daily_key not in self.memory_store['daily_orders']:
                    self.memory_store['daily_orders'][daily_key] = set()
                self.memory_store['daily_orders'][daily_key].add(order_data['order_id'])
            
            logger.info(f"Order tracked for user {user_id}: {order_data['order_id']}")
            
        except Exception as e:
            logger.error(f"Failed to track order for user {user_id}: {e}")
            
    async def update_order(self, user_id: str, order_id: str, update_data: Dict):
        """Update order status"""
        try:
            if self.redis_available and self.redis:
                # Redis storage
                order_data = await self.redis.hget(f"user:{user_id}:orders", order_id)
                if not order_data:
                    logger.warning(f"Order {order_id} not found for user {user_id}")
                    return
                    
                order = json.loads(order_data)
                order.update(update_data)
                order['updated_at'] = datetime.now().isoformat()
                
                await self.redis.hset(
                    f"user:{user_id}:orders",
                    order_id,
                    json.dumps(order)
                )
                
                if update_data.get('status') in ['FILLED', 'CANCELLED', 'REJECTED']:
                    await self.redis.srem(f"user:{user_id}:active_orders", order_id)
            else:
                # In-memory storage
                user_orders_key = f"user:{user_id}:orders"
                if user_orders_key not in self.memory_store['orders'] or order_id not in self.memory_store['orders'][user_orders_key]:
                    logger.warning(f"Order {order_id} not found for user {user_id}")
                    return
                    
                self.memory_store['orders'][user_orders_key][order_id].update(update_data)
                self.memory_store['orders'][user_orders_key][order_id]['updated_at'] = datetime.now().isoformat()
                
                if update_data.get('status') in ['FILLED', 'CANCELLED', 'REJECTED']:
                    active_key = f"user:{user_id}:active_orders"
                    if active_key in self.memory_store['active_orders']:
                        self.memory_store['active_orders'][active_key].discard(order_id)
                
            logger.info(f"Order updated for user {user_id}: {order_id}")
            
        except Exception as e:
            logger.error(f"Failed to update order for user {user_id}: {e}")
            
    async def track_position(self, user_id: str, position_data: Dict):
        """Track a new position"""
        try:
            position_with_timestamp = {
                **position_data,
                'tracked_at': datetime.now().isoformat()
            }
            
            if self.redis_available and self.redis:
                # Redis storage
                await self.redis.hset(
                    f"user:{user_id}:positions",
                    position_data['symbol'],
                    json.dumps(position_with_timestamp)
                )
                
                if position_data['quantity'] != 0:
                    await self.redis.sadd(f"user:{user_id}:active_positions", position_data['symbol'])
                    
                date_key = datetime.now().strftime('%Y%m%d')
                await self.redis.sadd(f"user:{user_id}:positions:{date_key}", position_data['symbol'])
            else:
                # In-memory storage
                user_positions_key = f"user:{user_id}:positions"
                if user_positions_key not in self.memory_store['positions']:
                    self.memory_store['positions'][user_positions_key] = {}
                
                self.memory_store['positions'][user_positions_key][position_data['symbol']] = position_with_timestamp
                
                if position_data['quantity'] != 0:
                    active_key = f"user:{user_id}:active_positions"
                    if active_key not in self.memory_store['active_positions']:
                        self.memory_store['active_positions'][active_key] = set()
                    self.memory_store['active_positions'][active_key].add(position_data['symbol'])
                    
                date_key = datetime.now().strftime('%Y%m%d')
                daily_key = f"user:{user_id}:positions:{date_key}"
                if daily_key not in self.memory_store['daily_positions']:
                    self.memory_store['daily_positions'][daily_key] = set()
                self.memory_store['daily_positions'][daily_key].add(position_data['symbol'])
            
            logger.info(f"Position tracked for user {user_id}: {position_data['symbol']}")
            
        except Exception as e:
            logger.error(f"Failed to track position for user {user_id}: {e}")
            
    async def update_position(self, user_id: str, symbol: str, update_data: Dict):
        """Update position"""
        try:
            if self.redis_available and self.redis:
                # Redis storage
                position_data = await self.redis.hget(f"user:{user_id}:positions", symbol)
                if not position_data:
                    logger.warning(f"Position {symbol} not found for user {user_id}")
                    return
                    
                position = json.loads(position_data)
                position.update(update_data)
                position['updated_at'] = datetime.now().isoformat()
                
                await self.redis.hset(
                    f"user:{user_id}:positions",
                    symbol,
                    json.dumps(position)
                )
                
                if update_data.get('quantity') == 0:
                    await self.redis.srem(f"user:{user_id}:active_positions", symbol)
            else:
                # In-memory storage
                user_positions_key = f"user:{user_id}:positions"
                if user_positions_key not in self.memory_store['positions'] or symbol not in self.memory_store['positions'][user_positions_key]:
                    logger.warning(f"Position {symbol} not found for user {user_id}")
                    return
                    
                self.memory_store['positions'][user_positions_key][symbol].update(update_data)
                self.memory_store['positions'][user_positions_key][symbol]['updated_at'] = datetime.now().isoformat()
                
                if update_data.get('quantity') == 0:
                    active_key = f"user:{user_id}:active_positions"
                    if active_key in self.memory_store['active_positions']:
                        self.memory_store['active_positions'][active_key].discard(symbol)
                
            logger.info(f"Position updated for user {user_id}: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to update position for user {user_id}: {e}")
            
    async def get_user_orders(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get user's orders"""
        try:
            if self.redis_available and self.redis:
                # Redis storage
                orders = await self.redis.hgetall(f"user:{user_id}:orders")
                
                if status:
                    return [
                        json.loads(order_data)
                        for order_data in orders.values()
                        if json.loads(order_data)['status'] == status
                    ]
                
                return [json.loads(order_data) for order_data in orders.values()]
            else:
                # In-memory storage
                user_orders_key = f"user:{user_id}:orders"
                if user_orders_key not in self.memory_store['orders']:
                    return []
                
                orders = self.memory_store['orders'][user_orders_key]
                
                if status:
                    return [
                        order_data
                        for order_data in orders.values()
                        if order_data['status'] == status
                    ]
                
                return list(orders.values())
                
        except Exception as e:
            logger.error(f"Failed to get orders for user {user_id}: {e}")
            return []
            
    async def get_user_positions(self, user_id: str, active_only: bool = False) -> List[Dict]:
        """Get user's positions"""
        try:
            if self.redis_available and self.redis:
                # Redis storage
                if active_only:
                    active_symbols = await self.redis.smembers(f"user:{user_id}:active_positions")
                    positions = []
                    for symbol in active_symbols:
                        position_data = await self.redis.hget(f"user:{user_id}:positions", symbol)
                        if position_data:
                            positions.append(json.loads(position_data))
                    return positions
                else:
                    positions = await self.redis.hgetall(f"user:{user_id}:positions")
                    return [json.loads(position_data) for position_data in positions.values()]
            else:
                # In-memory storage
                user_positions_key = f"user:{user_id}:positions"
                if user_positions_key not in self.memory_store['positions']:
                    return []
                
                if active_only:
                    active_key = f"user:{user_id}:active_positions"
                    if active_key not in self.memory_store['active_positions']:
                        return []
                    
                    active_symbols = self.memory_store['active_positions'][active_key]
                    positions = []
                    for symbol in active_symbols:
                        if symbol in self.memory_store['positions'][user_positions_key]:
                            positions.append(self.memory_store['positions'][user_positions_key][symbol])
                    return positions
                else:
                    return list(self.memory_store['positions'][user_positions_key].values())
            
        except Exception as e:
            logger.error(f"Failed to get positions for user {user_id}: {e}")
            return []
            
    async def get_user_daily_summary(self, user_id: str, date: Optional[str] = None) -> Dict:
        """Get user's daily trading summary"""
        try:
            date_key = date or datetime.now().strftime('%Y%m%d')
            
            if self.redis_available and self.redis:
                # Redis storage
                order_ids = await self.redis.smembers(f"user:{user_id}:orders:{date_key}")
                orders = []
                for order_id in order_ids:
                    order_data = await self.redis.hget(f"user:{user_id}:orders", order_id)
                    if order_data:
                        orders.append(json.loads(order_data))
                        
                position_symbols = await self.redis.smembers(f"user:{user_id}:positions:{date_key}")
                positions = []
                for symbol in position_symbols:
                    position_data = await self.redis.hget(f"user:{user_id}:positions", symbol)
                    if position_data:
                        positions.append(json.loads(position_data))
            else:
                # In-memory storage
                daily_orders_key = f"user:{user_id}:orders:{date_key}"
                daily_positions_key = f"user:{user_id}:positions:{date_key}"
                
                orders = []
                if daily_orders_key in self.memory_store['daily_orders']:
                    user_orders_key = f"user:{user_id}:orders"
                    if user_orders_key in self.memory_store['orders']:
                        for order_id in self.memory_store['daily_orders'][daily_orders_key]:
                            if order_id in self.memory_store['orders'][user_orders_key]:
                                orders.append(self.memory_store['orders'][user_orders_key][order_id])
                
                positions = []
                if daily_positions_key in self.memory_store['daily_positions']:
                    user_positions_key = f"user:{user_id}:positions"
                    if user_positions_key in self.memory_store['positions']:
                        for symbol in self.memory_store['daily_positions'][daily_positions_key]:
                            if symbol in self.memory_store['positions'][user_positions_key]:
                                positions.append(self.memory_store['positions'][user_positions_key][symbol])
                    
            # Calculate summary
            total_trades = len(orders)
            filled_trades = len([o for o in orders if o['status'] == 'FILLED'])
            total_volume = sum(o['quantity'] for o in orders if o['status'] == 'FILLED')
            total_pnl = sum(p.get('pnl', 0) for p in positions)
            
            return {
                'date': date_key,
                'total_trades': total_trades,
                'filled_trades': filled_trades,
                'total_volume': total_volume,
                'total_pnl': total_pnl,
                'orders': orders,
                'positions': positions
            }
            
        except Exception as e:
            logger.error(f"Failed to get daily summary for user {user_id}: {e}")
            return {
                'date': date_key,
                'total_trades': 0,
                'filled_trades': 0,
                'total_volume': 0,
                'total_pnl': 0,
                'orders': [],
                'positions': []
            }
            
    async def cleanup_old_data(self, user_id: str, days_to_keep: int = 30):
        """Clean up old data - simplified for in-memory fallback"""
        try:
            if self.redis_available and self.redis:
                # Redis cleanup (existing logic)
                current_date = datetime.now()
                for i in range(days_to_keep, days_to_keep + 30):
                    old_date = current_date - timedelta(days=i)
                    date_key = old_date.strftime('%Y%m%d')
                    
                    # Clean up old daily data
                    await self.redis.delete(f"user:{user_id}:orders:{date_key}")
                    await self.redis.delete(f"user:{user_id}:positions:{date_key}")
            else:
                # In-memory cleanup - just clear old entries
                logger.info(f"In-memory cleanup for user {user_id} - clearing old data")
                # For in-memory, we'll just keep recent data and clear old references
                pass
            
        except Exception as e:
            logger.error(f"Failed to cleanup data for user {user_id}: {e}") 
        except Exception as e:
            logger.error(f"Failed to get orders for user {user_id}: {e}")
            return []
            
    async def get_user_positions(self, user_id: str, active_only: bool = False) -> List[Dict]:
        """Get user's positions"""
        try:
            if self.redis_available and self.redis:
                # Redis storage
                if active_only:
                    active_symbols = await self.redis.smembers(f"user:{user_id}:active_positions")
                    positions = []
                    for symbol in active_symbols:
                        position_data = await self.redis.hget(f"user:{user_id}:positions", symbol)
                        if position_data:
                            positions.append(json.loads(position_data))
                    return positions
                else:
                    positions = await self.redis.hgetall(f"user:{user_id}:positions")
                    return [json.loads(position_data) for position_data in positions.values()]
            else:
                # In-memory storage
                user_positions_key = f"user:{user_id}:positions"
                if user_positions_key not in self.memory_store['positions']:
                    return []
                
                if active_only:
                    active_key = f"user:{user_id}:active_positions"
                    if active_key not in self.memory_store['active_positions']:
                        return []
                    
                    active_symbols = self.memory_store['active_positions'][active_key]
                    positions = []
                    for symbol in active_symbols:
                        if symbol in self.memory_store['positions'][user_positions_key]:
                            positions.append(self.memory_store['positions'][user_positions_key][symbol])
                    return positions
                else:
                    return list(self.memory_store['positions'][user_positions_key].values())
            
        except Exception as e:
            logger.error(f"Failed to get positions for user {user_id}: {e}")
            return []
            
    async def get_user_daily_summary(self, user_id: str, date: Optional[str] = None) -> Dict:
        """Get user's daily trading summary"""
        try:
            date_key = date or datetime.now().strftime('%Y%m%d')
            
            if self.redis_available and self.redis:
                # Redis storage
                order_ids = await self.redis.smembers(f"user:{user_id}:orders:{date_key}")
                orders = []
                for order_id in order_ids:
                    order_data = await self.redis.hget(f"user:{user_id}:orders", order_id)
                    if order_data:
                        orders.append(json.loads(order_data))
                        
                position_symbols = await self.redis.smembers(f"user:{user_id}:positions:{date_key}")
                positions = []
                for symbol in position_symbols:
                    position_data = await self.redis.hget(f"user:{user_id}:positions", symbol)
                    if position_data:
                        positions.append(json.loads(position_data))
            else:
                # In-memory storage
                daily_orders_key = f"user:{user_id}:orders:{date_key}"
                daily_positions_key = f"user:{user_id}:positions:{date_key}"
                
                orders = []
                if daily_orders_key in self.memory_store['daily_orders']:
                    user_orders_key = f"user:{user_id}:orders"
                    if user_orders_key in self.memory_store['orders']:
                        for order_id in self.memory_store['daily_orders'][daily_orders_key]:
                            if order_id in self.memory_store['orders'][user_orders_key]:
                                orders.append(self.memory_store['orders'][user_orders_key][order_id])
                
                positions = []
                if daily_positions_key in self.memory_store['daily_positions']:
                    user_positions_key = f"user:{user_id}:positions"
                    if user_positions_key in self.memory_store['positions']:
                        for symbol in self.memory_store['daily_positions'][daily_positions_key]:
                            if symbol in self.memory_store['positions'][user_positions_key]:
                                positions.append(self.memory_store['positions'][user_positions_key][symbol])
                    
            # Calculate summary
            total_trades = len(orders)
            filled_trades = len([o for o in orders if o['status'] == 'FILLED'])
            total_volume = sum(o['quantity'] for o in orders if o['status'] == 'FILLED')
            total_pnl = sum(p.get('pnl', 0) for p in positions)
            
            return {
                'date': date_key,
                'total_trades': total_trades,
                'filled_trades': filled_trades,
                'total_volume': total_volume,
                'total_pnl': total_pnl,
                'orders': orders,
                'positions': positions
            }
            
        except Exception as e:
            logger.error(f"Failed to get daily summary for user {user_id}: {e}")
            return {
                'date': date_key,
                'total_trades': 0,
                'filled_trades': 0,
                'total_volume': 0,
                'total_pnl': 0,
                'orders': [],
                'positions': []
            }
            
    async def cleanup_old_data(self, user_id: str, days_to_keep: int = 30):
        """Clean up old data - simplified for in-memory fallback"""
        try:
            if self.redis_available and self.redis:
                # Redis cleanup (existing logic)
                current_date = datetime.now()
                for i in range(days_to_keep, days_to_keep + 30):
                    old_date = current_date - timedelta(days=i)
                    date_key = old_date.strftime('%Y%m%d')
                    
                    # Clean up old daily data
                    await self.redis.delete(f"user:{user_id}:orders:{date_key}")
                    await self.redis.delete(f"user:{user_id}:positions:{date_key}")
            else:
                # In-memory cleanup - just clear old entries
                logger.info(f"In-memory cleanup for user {user_id} - clearing old data")
                # For in-memory, we'll just keep recent data and clear old references
                pass
            
        except Exception as e:
            logger.error(f"Failed to cleanup data for user {user_id}: {e}") 
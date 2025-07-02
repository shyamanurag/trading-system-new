# f_and_o_scalping_system/core/position_tracker.py
"""
Position Tracking and Management System
Handles all position lifecycle operations with proper state management
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import redis.asyncio as redis
import pandas as pd

from src.models.trading_models import PositionModel as Position, PositionStatus
from src.events import EventBus, EventType, TradingEvent

logger = logging.getLogger(__name__)

class PositionTracker:
    """
    Centralized position tracking with:
    - Real-time P&L calculation
    - Risk metrics computation
    - Event-driven updates
    - Redis persistence
    """

    def __init__(self, event_bus: EventBus, redis_client: redis.Redis):
        self.event_bus = event_bus
        self.redis = redis_client
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        self.position_concentration: Dict[str, float] = defaultdict(float)
        self.total_exposure: float = 0.0
        self.capital: float = 0.0
        self.peak_capital: float = 0.0
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.max_positions: int = 10
        self._lock = asyncio.Lock()
        
        # Performance metrics
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'largest_win': 0.0,
            'largest_loss': 0.0
        }
        
        # Setup event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event subscriptions"""
        self.event_bus.subscribe(
            EventType.ORDER_FILLED,
            self._handle_order_filled
        )
        self.event_bus.subscribe(
            EventType.POSITION_UPDATED,
            self._handle_position_update
        )

    @asyncio.Lock()
    async def add_position(self, position: Position) -> bool:
        """Add a new position"""
        async with self._lock:
            # Check position limits
            if len(self.positions) >= self.max_positions:
                logger.warning(f"Max positions ({self.max_positions}) reached")
                return False

            # Add position
            self.positions[position.position_id] = position

            # Update exposure
            position_value = position.quantity * position.entry_price
            self.total_exposure += position_value

            # Update concentration
            symbol_base = self._get_symbol_base(position.symbol)
            self.position_concentration[symbol_base] += position_value

            # Persist to Redis
            await self._save_position_to_redis(position)

            # Publish event
            await self.event_bus.publish(TradingEvent(
                EventType.POSITION_ADDED,
                {
                    'position': position.to_dict()
                }
            ))

            logger.info(f"Position added: {position.position_id} - {position.symbol}")
            return True

    @asyncio.Lock()
    async def update_position(self, position_id: str, updates: Dict) -> bool:
        """Update an existing position"""
        async with self._lock:
            position = self.positions.get(position_id)
            if not position:
                logger.warning(f"Position {position_id} not found")
                return False

            # Update position fields
            for key, value in updates.items():
                if hasattr(position, key):
                    setattr(position, key, value)

            # Update P&L if price changed
            if 'current_price' in updates:
                position.update_pnl(updates['current_price'])

            # Persist changes
            await self._save_position_to_redis(position)

            # Publish update event
            await self.event_bus.publish(TradingEvent(
                EventType.POSITION_UPDATED,
                {
                    'position_id': position_id,
                    'updates': updates,
                    'position': position.to_dict()
                }
            ))

            return True

    @asyncio.Lock()
    async def close_position(self, position_id: str, exit_price: float, reason: str = "manual") -> bool:
        """Close a position"""
        async with self._lock:
            position = self.positions.get(position_id)
            if not position:
                logger.warning(f"Position {position_id} not found")
                return False

            # Close position
            position.close(exit_price)

            # Update metrics
            self._update_metrics_on_close(position)

            # Update exposure
            position_value = position.quantity * position.entry_price
            self.total_exposure -= position_value

            # Update concentration
            symbol_base = self._get_symbol_base(position.symbol)
            self.position_concentration[symbol_base] -= position_value

            # Move to history
            self.position_history.append(position)
            del self.positions[position_id]

            # Persist changes
            await self._save_position_to_redis(position)
            await self._save_trade_to_history(position)

            # Publish event
            await self.event_bus.publish(TradingEvent(
                EventType.POSITION_CLOSED,
                {
                    'position': position.to_dict(),
                    'reason': reason
                }
            ))

            logger.info(f"Position closed: {position_id} - P&L: {position.realized_pnl:.2f} "
                       f"({position.pnl_percent:.2f}%)")
            return True

    async def update_all_positions(self, market_data: Dict[str, float]):
        """Update all positions with current market prices"""
        update_tasks = []
        for position in self.positions.values():
            if position.symbol in market_data:
                update_tasks.append(
                    self.update_position(
                        position.position_id,
                        {'current_price': market_data[position.symbol]}
                    )
                )
        if update_tasks:
            await asyncio.gather(*update_tasks)

    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())

    def get_position(self, position_id: str) -> Optional[Position]:
        """Get specific position"""
        return self.positions.get(position_id)

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get positions for a specific symbol"""
        return [p for p in self.positions.values() if p.symbol == symbol]

    def get_positions_by_strategy(self, strategy: str) -> List[Position]:
        """Get positions for a specific strategy"""
        return [p for p in self.positions.values() if p.strategy == strategy]

    def get_real_time_pnl(self) -> Dict:
        """Calculate real-time P&L metrics"""
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        realized_pnl = self.daily_pnl
        total_pnl = unrealized_pnl + realized_pnl

        return {
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': realized_pnl,
            'total_pnl': total_pnl,
            'daily_pnl': self.daily_pnl,
            'pnl_percent': (total_pnl / self.capital) * 100 if self.capital else 0,
            'open_positions': len(self.positions),
            'total_trades': self.metrics['total_trades'],
            'win_rate': self._calculate_win_rate(),
            'winners': self.metrics['winning_trades'],
            'losers': self.metrics['losing_trades']
        }

    def get_risk_metrics(self) -> Dict:
        """Calculate risk metrics"""
        # Position concentration
        max_concentration = max(self.position_concentration.values()) if self.position_concentration else 0

        # Exposure metrics
        exposure_percent = (self.total_exposure / self.capital) * 100 if self.capital else 0

        # Drawdown calculation
        current_capital = self.capital + self.total_pnl
        drawdown = 0
        if current_capital < self.peak_capital:
            drawdown = ((self.peak_capital - current_capital) / self.peak_capital) * 100

        # Risk per position
        avg_position_size = self.total_exposure / len(self.positions) if self.positions else 0

        return {
            'total_exposure': self.total_exposure,
            'exposure_percent': exposure_percent,
            'max_concentration': max_concentration,
            'position_count': len(self.positions),
            'avg_position_size': avg_position_size,
            'current_drawdown': drawdown,
            'capital_at_risk': self.total_exposure,
            'potential_loss': sum(p.current_risk for p in self.positions.values())
        }

    def _update_metrics_on_close(self, position: Position):
        """Update performance metrics when position closes"""
        self.metrics['total_trades'] += 1
        
        if position.realized_pnl > 0:
            self.metrics['winning_trades'] += 1
            self.metrics['consecutive_wins'] += 1
            self.metrics['consecutive_losses'] = 0
            self.metrics['largest_win'] = max(self.metrics['largest_win'], position.realized_pnl)
        else:
            self.metrics['losing_trades'] += 1
            self.metrics['consecutive_losses'] += 1
            self.metrics['consecutive_wins'] = 0
            self.metrics['largest_loss'] = min(self.metrics['largest_loss'], position.realized_pnl)

    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        total = self.metrics['winning_trades'] + self.metrics['losing_trades']
        if total == 0:
            return 0.0
        return (self.metrics['winning_trades'] / total) * 100

    def _get_symbol_base(self, symbol: str) -> str:
        """Extract base symbol from option symbol"""
        if 'NIFTY' in symbol and 'BANKNIFTY' not in symbol:
            return 'NIFTY'
        elif 'BANKNIFTY' in symbol:
            return 'BANKNIFTY'
        else:
            # Remove numbers and CE/PE
            import re
            return re.sub(r'[0-9]+|CE|PE', '', symbol).strip()

    async def _save_position_to_redis(self, position: Position):
        """Save position to Redis"""
        try:
            key = f"position:{position.position_id}"
            await self.redis.hset(
                key,
                mapping=position.to_dict()
            )
            await self.redis.expire(key, 86400)  # 24 hour expiry

            # Also update positions set
            await self.redis.sadd(
                f"positions:{datetime.now().strftime('%Y%m%d')}",
                position.position_id
            )
        except Exception as e:
            logger.error(f"Error saving position to Redis: {e}")

    async def _save_trade_to_history(self, position: Position):
        """Save closed trade to history"""
        try:
            key = f"trade_history:{datetime.now().strftime('%Y%m%d')}"
            trade_data = {
                'position_id': position.position_id,
                'symbol': position.symbol,
                'entry_price': position.entry_price,
                'exit_price': position.exit_price,
                'quantity': position.quantity,
                'pnl': position.realized_pnl,
                'pnl_percent': position.pnl_percent,
                'strategy': position.strategy,
                'entry_time': position.entry_time.isoformat(),
                'exit_time': position.exit_time.isoformat()
            }
            await self.redis.rpush(key, json.dumps(trade_data))
            await self.redis.expire(key, 604800)  # 7 day expiry
        except Exception as e:
            logger.error(f"Error saving trade to history: {e}")

    async def _handle_order_filled(self, event: TradingEvent):
        """Handle order filled event"""
        try:
            order_data = event.data
            position_id = order_data.get('position_id')
            if position_id:
                position = self.get_position(position_id)
                if position:
                    await self.update_position(position_id, {
                        'current_price': order_data.get('fill_price'),
                        'status': PositionStatus.FILLED
                    })
        except Exception as e:
            logger.error(f"Error handling order filled event: {e}")

    async def _handle_position_update(self, event: TradingEvent):
        """Handle position update event"""
        try:
            update_data = event.data
            position_id = update_data.get('position_id')
            if position_id:
                position = self.get_position(position_id)
                if position:
                    await self.update_position(position_id, update_data.get('updates', {}))
        except Exception as e:
            logger.error(f"Error handling position update event: {e}")

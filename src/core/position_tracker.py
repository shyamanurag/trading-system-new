﻿"""
Production-Level Position Tracker
=================================
Tracks trading positions with Redis persistence and proper error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Trading position data structure"""
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    unrealized_pnl: float
    side: str  # 'long' or 'short'
    entry_time: datetime
    last_updated: datetime
    
    # Risk management fields for auto square-off
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    trailing_stop: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'current_price': self.current_price,
            'pnl': self.pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'side': self.side,
            'entry_time': self.entry_time.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'stop_loss': self.stop_loss,
            'target': self.target,
            'trailing_stop': self.trailing_stop
        }

class ProductionPositionTracker:
    """
    Production-Level Position Tracker
    ================================
    Tracks trading positions with proper error handling and performance tracking.
    """
    
    def __init__(self, redis_client=None, event_bus=None):
        self.redis_client = redis_client
        self.event_bus = event_bus
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
        # Capital management - CRITICAL for RiskManager
        self.capital = 0.0  # Will be dynamically set from broker account
        self.peak_capital = self.capital
        self.previous_capital = self.capital  # For VaR calculations
        
        # Market regime tracking - CRITICAL for RiskManager
        self.current_regime = "NORMAL"  # NORMAL, HIGH, EXTREME
        
        # Performance tracking
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
    async def initialize(self) -> bool:
        """Initialize position tracker"""
        try:
            # Initialize Redis client if available
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    self.logger.info("Position tracker initialized with Redis")
                except:
                    self.logger.warning("Redis not available, using memory-only mode")
                    self.redis_client = None
            else:
                self.logger.info("Position tracker initialized in memory-only mode")
            
            self.is_initialized = True
            self.logger.info(f"Position tracker initialized with {len(self.positions)} positions")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize position tracker: {e}")
            return False
    
    async def update_position(self, symbol: str, quantity: int, price: float, 
                            side: str = 'long') -> bool:
        """Update position for a symbol"""
        try:
            now = datetime.now()
            
            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]
                
                # Calculate new average price
                total_quantity = position.quantity + quantity
                if total_quantity != 0:
                    new_avg_price = ((position.average_price * position.quantity) + 
                                   (price * quantity)) / total_quantity
                else:
                    new_avg_price = price
                
                # Update position
                position.quantity = total_quantity
                position.average_price = new_avg_price
                position.current_price = price
                position.last_updated = now
                position.side = side
                
                # Calculate PnL
                if side == 'long':
                    position.unrealized_pnl = (price - position.average_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.average_price - price) * position.quantity
                
            else:
                # Create new position
                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=price,
                    current_price=price,
                    pnl=0.0,
                    unrealized_pnl=0.0,
                    side=side,
                    entry_time=now,
                    last_updated=now,
                    stop_loss=None,  # Will be set by trade engine
                    target=None,     # Will be set by trade engine
                    trailing_stop=None  # Will be set by trade engine
                )
                self.positions[symbol] = position
            
            # Publish position update event
            if self.event_bus:
                await self.event_bus.publish('position_updated', {
                    'symbol': symbol,
                    'position': position.to_dict()
                })
            
            self.logger.info(f"Updated position for {symbol}: {quantity} @ {price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update position for {symbol}: {e}")
            return False
    
    async def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """Close a position and calculate realized PnL"""
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position found for {symbol}")
                return None
            
            position = self.positions[symbol]
            
            # Calculate realized PnL
            if position.side == 'long':
                realized_pnl = (exit_price - position.average_price) * position.quantity
            else:
                realized_pnl = (position.average_price - exit_price) * position.quantity
            
            # Update performance metrics
            self.total_pnl += realized_pnl
            self.daily_pnl += realized_pnl
            self.total_trades += 1
            
            # Update capital tracking
            current_portfolio_value = self.capital + self.total_pnl
            if current_portfolio_value > self.peak_capital:
                self.peak_capital = current_portfolio_value
            
            if realized_pnl > 0:
                self.winning_trades += 1
            
            # Calculate win rate
            if self.total_trades > 0:
                self.win_rate = self.winning_trades / self.total_trades
            
            # Remove position
            del self.positions[symbol]
            
            # Publish position closed event
            if self.event_bus:
                await self.event_bus.publish('position_closed', {
                    'symbol': symbol,
                    'realized_pnl': realized_pnl,
                    'exit_price': exit_price
                })
            
            self.logger.info(f"Closed position for {symbol}: PnL = {realized_pnl:.2f}")
            return realized_pnl
            
        except Exception as e:
            self.logger.error(f"Failed to close position for {symbol}: {e}")
            return None
    
    async def update_market_prices(self, market_data: Dict[str, float]):
        """Update current market prices for all positions"""
        try:
            for symbol, position in self.positions.items():
                if symbol in market_data:
                    new_price = market_data[symbol]
                    position.current_price = new_price
                    position.last_updated = datetime.now()
                    
                    # Update unrealized PnL
                    if position.side == 'long':
                        position.unrealized_pnl = (new_price - position.average_price) * position.quantity
                    else:
                        position.unrealized_pnl = (position.average_price - new_price) * position.quantity
                
        except Exception as e:
            self.logger.error(f"Failed to update market prices: {e}")
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        return self.positions.get(symbol)
    
    async def get_all_positions(self) -> Dict[str, Position]:
        """Get all current positions"""
        return self.positions.copy()
    
    def get_open_positions(self) -> Dict[str, Position]:
        """Get all open positions (alias for get_all_positions for RiskManager compatibility)"""
        return self.positions.copy()
    
    async def get_positions_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_invested = sum(abs(pos.average_price * pos.quantity) for pos in self.positions.values())
            
            return {
                'total_positions': len(self.positions),
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_realized_pnl': self.total_pnl,
                'daily_pnl': self.daily_pnl,
                'total_invested': total_invested,
                'win_rate': self.win_rate,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'max_drawdown': self.max_drawdown,
                'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get positions summary: {e}")
            return {}
    
    async def set_capital(self, capital: float) -> bool:
        """Set trading capital"""
        try:
            self.capital = capital
            if self.peak_capital < capital:
                self.peak_capital = capital
            self.logger.info(f"Capital set to: ₹{capital:,.2f}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set capital: {e}")
            return False
    
    async def get_capital(self) -> float:
        """Get current capital"""
        return self.capital
    
    async def get_portfolio_value(self) -> float:
        """Get current portfolio value (capital + PnL)"""
        return self.capital + self.total_pnl
    
    async def get_risk_exposure(self) -> Dict[str, Any]:
        """Get current risk exposure"""
        try:
            total_long_exposure = sum(
                pos.current_price * pos.quantity 
                for pos in self.positions.values() 
                if pos.side == 'long' and pos.quantity > 0
            )
            
            total_short_exposure = sum(
                pos.current_price * abs(pos.quantity) 
                for pos in self.positions.values() 
                if pos.side == 'short' and pos.quantity < 0
            )
            
            net_exposure = total_long_exposure - total_short_exposure
            gross_exposure = total_long_exposure + total_short_exposure
            
            return {
                'total_long_exposure': total_long_exposure,
                'total_short_exposure': total_short_exposure,
                'net_exposure': net_exposure,
                'gross_exposure': gross_exposure,
                'position_count': len(self.positions),
                'leverage_ratio': gross_exposure / max(net_exposure, 1) if net_exposure > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk exposure: {e}")
            return {}

    async def clear_all_positions(self):
        """Clear all positions from tracker"""
        try:
            self.positions.clear()
            
            # Clear from Redis if available
            if self.redis_client:
                try:
                    await self.redis_client.delete("positions:*")
                    self.logger.info("🧹 Cleared all positions from Redis")
                except Exception as e:
                    self.logger.warning(f"Could not clear Redis positions: {e}")
            
            self.logger.info("🧹 Cleared all positions from tracker")
            
        except Exception as e:
            self.logger.error(f"❌ Error clearing positions: {e}")
    
    async def sync_with_zerodha_positions(self, zerodha_positions: Dict):
        """Sync position tracker with actual Zerodha positions"""
        try:
            # First, clear all existing positions to avoid stale data
            await self.clear_all_positions()
            
            # Add only the actual Zerodha positions
            for symbol, pos_data in zerodha_positions.items():
                quantity = pos_data.get('quantity', 0)
                if quantity != 0:  # Only add positions with actual quantity
                    position = Position(
                        symbol=symbol,
                        quantity=abs(quantity),
                        average_price=pos_data.get('average_price', 0),
                        current_price=pos_data.get('ltp', pos_data.get('average_price', 0)),
                        pnl=pos_data.get('pnl', 0),
                        unrealized_pnl=pos_data.get('unrealized_pnl', 0),
                        side='long' if quantity > 0 else 'short',
                        entry_time=datetime.now(),
                        last_updated=datetime.now()
                    )
                    
                    self.positions[symbol] = position
                    
                    # Store in Redis if available
                    if self.redis_client:
                        try:
                            await self.redis_client.set(
                                f"position:{symbol}", 
                                json.dumps(position.to_dict()),
                                ex=3600  # 1 hour expiry
                            )
                        except Exception as e:
                            self.logger.warning(f"Could not store position in Redis: {e}")
            
            self.logger.info(f"✅ Synced position tracker with {len(self.positions)} actual Zerodha positions")
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing with Zerodha positions: {e}")

    async def get_position_count(self) -> int:
        """Get the count of tracked positions"""
        return len(self.positions)

# Global position tracker instance
position_tracker = ProductionPositionTracker()

async def get_position_tracker() -> ProductionPositionTracker:
    """Get position tracker instance"""
    if not position_tracker.is_initialized:
        await position_tracker.initialize()
    return position_tracker

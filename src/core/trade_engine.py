"""
Trade Engine
Handles trading logic and strategy execution
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import uuid
import os
from dataclasses import dataclass
import pandas as pd
import time
import json
from collections import defaultdict, deque

from brokers.zerodha import ZerodhaIntegration
from .risk_manager import RiskManager
from .position_manager import PositionManager
from .market_data import MarketDataManager
from .config import settings
from .models import Order, OrderType, OrderSide, Trade, Signal, OptionType, ExecutionStrategy, OrderState, OrderStatus
from .exceptions import OrderError, RiskError
from .trade_allocator import TradeAllocator

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Trading signal from strategy"""
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    strategy_id: str
    metadata: Dict[str, Any]

class TradeEngine:
    """Enhanced trade engine with OCO orders and rate limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trade_allocator = None  # Will be set by orchestrator if needed
        self.risk_manager = None  # Will be set by orchestrator
        self.zerodha_client = None
        
        # OCO Order Management
        self.oco_groups = {}  # group_id -> {'orders': [order_ids], 'executed': False}
        self.order_to_oco_group = {}  # order_id -> group_id
        self.pending_orders = {}  # order_id -> order_info
        
        # Rate Limiting (7 trades per second)
        self.max_trades_per_second = config.get('rate_limit', {}).get('max_trades_per_second', 7)
        self.trade_timestamps = deque(maxlen=self.max_trades_per_second)
        self.rate_limit_lock = asyncio.Lock()
        
        # Batch Processing
        self.batch_size = config.get('batch_processing', {}).get('size', 5)
        self.batch_timeout = config.get('batch_processing', {}).get('timeout', 0.5)  # 500ms
        self.signal_queue = asyncio.Queue()
        self.batch_processor_task = None
        
        # Order tracking
        self.active_orders = {}  # order_id -> order_details
        self.executed_trades = {}  # trade_id -> trade_details
        
        # Statistics
        self.stats = {
            'signals_processed': 0,
            'orders_placed': 0,
            'orders_cancelled': 0,
            'oco_executions': 0,
            'rate_limit_delays': 0
        }
        
        # Batch processor will be started when needed
        logger.info("📦 TradeEngine initialized (batch processor will start when trading begins)")
    
    async def initialize(self) -> bool:
        """Initialize the trade engine asynchronously"""
        try:
            logger.info("🚀 Initializing TradeEngine async components...")
            
            # Start batch processor if needed
            if not self.batch_processor_task:
                self.start_batch_processor()
            
            # Initialize any async components here
            logger.info("✅ TradeEngine initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ TradeEngine initialization failed: {e}")
            return False
    
    def start_batch_processor(self):
        """Start the batch signal processor"""
        if self.batch_processor_task is None:
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
            logger.info("🚀 Batch signal processor started")
    
    async def stop_batch_processor(self):
        """Stop the batch signal processor"""
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
            try:
                await self.batch_processor_task
            except asyncio.CancelledError:
                pass
            self.batch_processor_task = None
            logger.info("🛑 Batch signal processor stopped")
    
    async def _batch_processor(self):
        """Background task that processes signals in batches"""
        while True:
            try:
                batch_signals = []
                start_time = time.time()
                
                # Collect signals for batch processing
                while len(batch_signals) < self.batch_size:
                    try:
                        # Wait for signal with timeout
                        remaining_time = self.batch_timeout - (time.time() - start_time)
                        if remaining_time <= 0:
                            break
                        
                        signal = await asyncio.wait_for(
                            self.signal_queue.get(), 
                            timeout=remaining_time
                        )
                        batch_signals.append(signal)
                        
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if we have signals
                if batch_signals:
                    await self._process_signal_batch(batch_signals)
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)
    
    async def process_signals(self, signals: List[Dict[str, Any]]):
        """Queue signals for batch processing"""
        try:
            for signal in signals:
                await self.signal_queue.put(signal)
                self.stats['signals_processed'] += 1
            
            logger.info(f"📬 Queued {len(signals)} signals for batch processing")
            
        except Exception as e:
            logger.error(f"Error queuing signals: {e}")
    
    async def _process_signal_batch(self, signals: List[Dict[str, Any]]):
        """Process a batch of signals with OCO and rate limiting"""
        try:
            batch_start_time = time.time()
            
            # Group signals by symbol for OCO processing
            symbol_signals = defaultdict(list)
            for signal in signals:
                symbol_signals[signal['symbol']].append(signal)
            
            # Process each symbol's signals
            for symbol, symbol_signals_list in symbol_signals.items():
                await self._process_symbol_signals(symbol, symbol_signals_list)
            
            batch_time = (time.time() - batch_start_time) * 1000
            logger.info(f"⚡ Processed batch of {len(signals)} signals in {batch_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error processing signal batch: {e}")
    
    def _validate_signal_structure(self, signal_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Comprehensive signal validation to catch field mismatches early
        Returns (is_valid, error_message)
        """
        try:
            # Required fields validation
            required_fields = ['symbol', 'quantity', 'entry_price']
            missing_fields = [field for field in required_fields if field not in signal_dict]
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"
            
            # Action/Direction field validation (handle both)
            if 'action' not in signal_dict and 'direction' not in signal_dict:
                return False, "Missing 'action' or 'direction' field"
            
            action_value = signal_dict.get('action') or signal_dict.get('direction', '')
            if action_value.upper() not in ['BUY', 'SELL']:
                return False, f"Invalid action/direction value: {action_value}"
            
            # Strategy field validation (handle both)
            if 'strategy' not in signal_dict and 'strategy_name' not in signal_dict:
                return False, "Missing 'strategy' or 'strategy_name' field"
            
            # Numeric field validation
            numeric_fields = ['quantity', 'entry_price']
            for field in numeric_fields:
                if field in signal_dict:
                    try:
                        value = float(signal_dict[field])
                        if value <= 0:
                            return False, f"Field '{field}' must be positive, got: {value}"
                    except (ValueError, TypeError):
                        return False, f"Field '{field}' must be numeric, got: {signal_dict[field]}"
            
            # Optional numeric field validation
            optional_numeric = ['stop_loss', 'target', 'confidence', 'quality_score', 'strike']
            for field in optional_numeric:
                if field in signal_dict:
                    try:
                        float(signal_dict[field])
                    except (ValueError, TypeError):
                        return False, f"Field '{field}' must be numeric, got: {signal_dict[field]}"
            
            # Confidence/Quality score range validation
            confidence = signal_dict.get('confidence') or signal_dict.get('quality_score', 1.0)
            if not (0.0 <= confidence <= 1.0):
                return False, f"Confidence/quality_score must be between 0.0 and 1.0, got: {confidence}"
            
            # Symbol validation
            symbol = signal_dict.get('symbol', '')
            if not symbol or not isinstance(symbol, str):
                return False, f"Invalid symbol: {symbol}"
            
            # Signal ID validation (if present)
            if 'signal_id' in signal_dict and not signal_dict['signal_id']:
                return False, "signal_id cannot be empty"
            
            return True, "Signal validation passed"
            
        except Exception as e:
            return False, f"Signal validation error: {str(e)}"

    def _dict_to_signal(self, signal_dict: Dict[str, Any]) -> Signal:
        """Convert dict signal to Signal object"""
        try:
            # Extract required fields with proper mapping
            signal_id = signal_dict.get('signal_id', f"signal_{datetime.now().timestamp()}")
            
            # CRITICAL FIX: Map strategy field names consistently
            strategy_name = signal_dict.get('strategy_name') or signal_dict.get('strategy', 'unknown')
            
            symbol = signal_dict.get('symbol', '')
            
            # CRITICAL FIX: Map action/direction fields consistently
            action_value = signal_dict.get('action') or signal_dict.get('direction', 'BUY')
            action = OrderSide.BUY if action_value.upper() == 'BUY' else OrderSide.SELL
            
            quantity = signal_dict.get('quantity', 1)
            entry_price = signal_dict.get('entry_price', 0.0)
            stop_loss = signal_dict.get('stop_loss', 0.0)
            target = signal_dict.get('target', 0.0)
            
            # CRITICAL FIX: Map confidence/quality_score consistently
            quality_score = signal_dict.get('quality_score') or signal_dict.get('confidence', 0.8)
            
            # Calculate percentages for stop loss and target
            stop_loss_percent = 0.0
            target_percent = 0.0
            
            if entry_price > 0:
                if stop_loss > 0:
                    stop_loss_percent = abs((stop_loss - entry_price) / entry_price) * 100
                if target > 0:
                    target_percent = abs((target - entry_price) / entry_price) * 100
            
            # CRITICAL FIX: Handle option_type mapping
            option_type = OptionType.CALL  # Default for stocks
            if 'option_type' in signal_dict:
                try:
                    option_type = OptionType(signal_dict['option_type'])
                except (ValueError, AttributeError):
                    option_type = OptionType.CALL
            
            # CRITICAL FIX: Handle strike price
            strike = signal_dict.get('strike', 0.0)
            
            # Create Signal object with all required fields properly mapped
            signal_obj = Signal(
                signal_id=signal_id,
                strategy_name=strategy_name,
                symbol=symbol,
                option_type=option_type,
                strike=strike,
                action=action,
                quality_score=quality_score,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss_percent=stop_loss_percent,
                target_percent=target_percent,
                metadata=signal_dict.get('metadata', {}),
                timestamp=datetime.now()
            )
            
            # CRITICAL FIX: Add expected_price attribute that RiskManager needs
            signal_obj.expected_price = entry_price
            
            # CRITICAL FIX: Add original signal data for backward compatibility
            signal_obj.original_signal = signal_dict.copy()
            
            return signal_obj
            
        except Exception as e:
            logger.error(f"Error converting dict to Signal: {e}")
            logger.error(f"Signal dict: {signal_dict}")
            
            # Return a minimal valid Signal with error information
            error_signal = Signal(
                signal_id=f"error_signal_{datetime.now().timestamp()}",
                strategy_name=signal_dict.get('strategy', 'error'),
                symbol=signal_dict.get('symbol', 'UNKNOWN'),
                option_type=OptionType.CALL,
                strike=0.0,
                action=OrderSide.BUY,
                quality_score=0.0,
                quantity=1,
                entry_price=0.0,
                stop_loss_percent=0.0,
                target_percent=0.0,
                metadata={'error': str(e), 'original_signal': signal_dict},
                timestamp=datetime.now()
            )
            
            # Add expected_price for error signal too
            error_signal.expected_price = 0.0
            error_signal.original_signal = signal_dict.copy()
            
            return error_signal

    def _create_order_from_signal(self, signal_dict: Dict[str, Any]) -> Order:
        """Create Order object from signal dict"""
        try:
            # Get user_id from signal or environment
            user_id = signal_dict.get('user_id')
            if not user_id:
                user_id = os.getenv('ACTIVE_USER_ID', 'system')
            
            return Order(
                order_id=f"ORDER_{uuid.uuid4()}",
                user_id=user_id,
                signal_id=signal_dict.get('signal_id'),
                broker_order_id=None,
                parent_order_id=None,
                symbol=signal_dict.get('symbol', ''),
                option_type=OrderType.MARKET,
                strike=0.0,
                quantity=signal_dict.get('quantity', 1),
                order_type=OrderType.MARKET,
                side=OrderSide.BUY if signal_dict.get('action', 'BUY').upper() == 'BUY' else OrderSide.SELL,
                price=signal_dict.get('entry_price'),
                execution_strategy=ExecutionStrategy.MARKET,
                slice_number=None,
                total_slices=None,
                state=OrderState.CREATED,
                status=OrderStatus.PENDING,
                strategy_name=signal_dict.get('strategy', 'unknown'),
                metadata=signal_dict.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Error creating order from signal: {e}")
            # Return minimal order
            return Order(
                order_id=f"ERROR_{uuid.uuid4()}",
                user_id='system',
                signal_id=None,
                broker_order_id=None,
                parent_order_id=None,
                symbol=signal_dict.get('symbol', 'UNKNOWN'),
                option_type=OrderType.MARKET,
                strike=0.0,
                quantity=1,
                order_type=OrderType.MARKET,
                side=OrderSide.BUY,
                price=0.0,
                execution_strategy=ExecutionStrategy.MARKET,
                slice_number=None,
                total_slices=None,
                state=OrderState.CREATED,
                status=OrderStatus.PENDING,
                strategy_name='error',
                metadata={'error': str(e)}
            )

    async def _process_symbol_signals(self, symbol: str, signals: List[Dict[str, Any]]):
        """Process signals for a single symbol with OCO logic"""
        try:
            # Check if we already have positions or orders for this symbol
            existing_orders = self._get_active_orders_for_symbol(symbol)
            
            # If we have existing orders, evaluate OCO cancellation
            if existing_orders:
                await self._evaluate_oco_for_symbol(symbol, signals, existing_orders)
            
            # Process new signals
            for signal_dict in signals:
                # CRITICAL FIX: Validate signal structure first
                is_valid, validation_error = self._validate_signal_structure(signal_dict)
                if not is_valid:
                    logger.error(f"❌ Signal validation failed for {signal_dict.get('symbol', 'unknown')}: {validation_error}")
                    logger.error(f"Invalid signal: {signal_dict}")
                    continue
                
                # Convert dict to Signal object for risk validation
                signal_obj = self._dict_to_signal(signal_dict)
                
                # Risk check first (if risk manager is available)
                should_skip = False
                if self.risk_manager:
                    risk_result = await self.risk_manager.validate_signal(signal_obj)
                    if not risk_result.get('approved', False):
                        logger.warning(f"⚠️ Signal rejected by risk manager: {signal_dict.get('symbol', 'unknown')} - {risk_result.get('reason', 'Unknown')}")
                        should_skip = True
                else:
                    logger.info(f"ℹ️ Processing signal without risk validation (risk manager not set): {signal_dict.get('symbol', 'unknown')}")
                
                if should_skip:
                    continue
                
                # Create OCO group if multiple signals for same symbol
                if len(signals) > 1:
                    oco_group_id = f"OCO_{symbol}_{int(time.time())}"
                    if oco_group_id not in self.oco_groups:
                        self.oco_groups[oco_group_id] = {'orders': [], 'executed': False}
                else:
                    oco_group_id = None
                
                # Allocate trades (with fallback if allocator not available)
                if self.trade_allocator and hasattr(self.trade_allocator, 'allocate_trade_optimized'):
                    allocated_orders = await self.trade_allocator.allocate_trade_optimized(
                        signal_dict['strategy'], signal_dict
                    )
                else:
                    # Fallback allocation - use proper user_id from environment
                    user_id = signal_dict.get('user_id') or os.getenv('ACTIVE_USER_ID', 'system')
                    allocated_orders = [(user_id, self._create_order_from_signal(signal_dict))]
                
                # Place orders with rate limiting
                for user_id, order in allocated_orders:
                    order_id = await self._place_order_with_rate_limit(
                        user_id, order, oco_group_id
                    )
                    
                    if order_id and oco_group_id:
                        self.oco_groups[oco_group_id]['orders'].append(order_id)
                        self.order_to_oco_group[order_id] = oco_group_id
            
        except Exception as e:
            logger.error(f"Error processing signals for {symbol}: {e}")
    
    async def _place_order_with_rate_limit(self, user_id: str, order: Order, oco_group_id: Optional[str] = None) -> Optional[str]:
        """Place order with rate limiting (7 trades per second)"""
        try:
            async with self.rate_limit_lock:
                # Check rate limit
                current_time = time.time()
                
                # Remove old timestamps (older than 1 second)
                while self.trade_timestamps and (current_time - self.trade_timestamps[0]) > 1.0:
                    self.trade_timestamps.popleft()
                
                # Check if we're at the limit
                if len(self.trade_timestamps) >= self.max_trades_per_second:
                    # Calculate delay needed
                    oldest_timestamp = self.trade_timestamps[0]
                    delay = 1.0 - (current_time - oldest_timestamp)
                    
                    if delay > 0:
                        logger.info(f"⏱️ Rate limit hit, delaying {delay:.3f}s")
                        await asyncio.sleep(delay)
                        self.stats['rate_limit_delays'] += 1
                
                # Record this trade attempt
                self.trade_timestamps.append(time.time())
                
                # Place the order
                if self.zerodha_client:
                    order_params = self._convert_order_to_zerodha_params(order)
                    order_id = await self.zerodha_client.place_order(order_params)
                    
                    if order_id:
                        # Track the order
                        self.active_orders[order_id] = {
                            'order': order,
                            'user_id': user_id,
                            'oco_group': oco_group_id,
                            'placed_at': datetime.now(),
                            'status': 'PENDING'
                        }
                        
                        self.stats['orders_placed'] += 1
                        logger.info(f"📋 Order placed: {order_id} for user {user_id}")
                        
                        # Start monitoring this order
                        asyncio.create_task(self._monitor_order(order_id))
                        
                        return order_id
                    else:
                        logger.error(f"❌ Failed to place order for user {user_id}")
                        return None
                else:
                    logger.error("❌ Zerodha client not available")
                    return None
                    
        except Exception as e:
            logger.error(f"Error placing order with rate limit: {e}")
            return None
    
    async def _monitor_order(self, order_id: str):
        """Monitor order status and handle OCO logic"""
        try:
            max_checks = 60  # Monitor for 60 seconds
            check_interval = 1.0  # Check every second
            
            for _ in range(max_checks):
                if order_id not in self.active_orders:
                    break
                
                # Get order status
                if self.zerodha_client:
                    status = await self.zerodha_client.get_order_status(order_id)
                    
                    if status:
                        order_status = status.get('status', 'UNKNOWN')
                        self.active_orders[order_id]['status'] = order_status
                        
                        # Check if order is executed
                        if order_status in ['COMPLETE', 'EXECUTED']:
                            await self._handle_order_execution(order_id, status)
                            break
                        elif order_status in ['CANCELLED', 'REJECTED']:
                            await self._handle_order_cancellation(order_id, status)
                            break
                
                await asyncio.sleep(check_interval)
            
        except Exception as e:
            logger.error(f"Error monitoring order {order_id}: {e}")
    
    async def _handle_order_execution(self, order_id: str, status: Dict):
        """Handle order execution and OCO cancellation"""
        try:
            order_info = self.active_orders.get(order_id)
            if not order_info:
                return
            
            logger.info(f"✅ Order executed: {order_id}")
            
            # Check if this order is part of an OCO group
            oco_group_id = order_info.get('oco_group')
            if oco_group_id and oco_group_id in self.oco_groups:
                oco_group = self.oco_groups[oco_group_id]
                
                if not oco_group['executed']:
                    # Mark group as executed
                    oco_group['executed'] = True
                    
                    # Cancel all other orders in the group
                    other_orders = [oid for oid in oco_group['orders'] if oid != order_id]
                    for other_order_id in other_orders:
                        if other_order_id in self.active_orders:
                            await self._cancel_order(other_order_id, "OCO cancellation")
                    
                    self.stats['oco_executions'] += 1
                    logger.info(f"🔄 OCO group {oco_group_id} executed, cancelled {len(other_orders)} orders")
            
            # Record the trade
            trade_id = f"TRADE_{order_id}"
            self.executed_trades[trade_id] = {
                'order_id': order_id,
                'user_id': order_info['user_id'],
                'symbol': order_info['order'].symbol,
                'action': order_info['order'].side.value,
                'quantity': order_info['order'].quantity,
                'price': status.get('average_price', 0),
                'executed_at': datetime.now(),
                'status': status
            }
            
            # Remove from active orders
            del self.active_orders[order_id]
            
        except Exception as e:
            logger.error(f"Error handling order execution: {e}")
    
    async def _handle_order_cancellation(self, order_id: str, status: Dict):
        """Handle order cancellation"""
        try:
            order_info = self.active_orders.get(order_id)
            if not order_info:
                return
            
            logger.info(f"❌ Order cancelled: {order_id}")
            
            # Remove from active orders
            del self.active_orders[order_id]
            
            # Remove from OCO group if applicable
            oco_group_id = order_info.get('oco_group')
            if oco_group_id and oco_group_id in self.oco_groups:
                oco_group = self.oco_groups[oco_group_id]
                if order_id in oco_group['orders']:
                    oco_group['orders'].remove(order_id)
                
                if order_id in self.order_to_oco_group:
                    del self.order_to_oco_group[order_id]
            
            self.stats['orders_cancelled'] += 1
            
        except Exception as e:
            logger.error(f"Error handling order cancellation: {e}")
    
    async def _cancel_order(self, order_id: str, reason: str = "Manual cancellation"):
        """Cancel an order"""
        try:
            if self.zerodha_client and order_id in self.active_orders:
                success = await self.zerodha_client.cancel_order(order_id)
                if success:
                    logger.info(f"🚫 Order cancelled: {order_id} - {reason}")
                else:
                    logger.error(f"❌ Failed to cancel order: {order_id}")
                    
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
    
    def _get_active_orders_for_symbol(self, symbol: str) -> List[str]:
        """Get active orders for a specific symbol"""
        return [
            order_id for order_id, info in self.active_orders.items()
            if info['order'].symbol == symbol
        ]
    
    async def _evaluate_oco_for_symbol(self, symbol: str, new_signals: List[Dict], existing_orders: List[str]):
        """Evaluate if existing orders should be cancelled for new signals"""
        try:
            # Simple logic: if new signals have higher confidence, cancel existing
            if existing_orders:
                max_new_confidence = max(signal.get('confidence', 0) for signal in new_signals)
                
                # If new signals are significantly better, cancel existing
                if max_new_confidence > 0.8:  # High confidence threshold
                    for order_id in existing_orders:
                        await self._cancel_order(order_id, "Replaced by higher confidence signal")
                    
                    logger.info(f"🔄 Cancelled {len(existing_orders)} existing orders for {symbol} (new confidence: {max_new_confidence:.2f})")
                    
        except Exception as e:
            logger.error(f"Error evaluating OCO for {symbol}: {e}")
    
    def _convert_order_to_zerodha_params(self, order: Order) -> Dict:
        """Convert internal order to Zerodha parameters"""
        return {
            'symbol': order.symbol,
            'transaction_type': 'BUY' if order.side == OrderSide.BUY else 'SELL',
            'quantity': order.quantity,
            'price': order.price,
            'order_type': 'MARKET' if order.order_type == OrderType.MARKET else 'LIMIT',
            'trigger_price': getattr(order, 'trigger_price', None)
        }
    
    def get_statistics(self) -> Dict:
        """Get trade engine statistics"""
        return {
            **self.stats,
            'active_orders': len(self.active_orders),
            'active_oco_groups': len([g for g in self.oco_groups.values() if not g['executed']]),
            'executed_trades': len(self.executed_trades),
            'queue_size': self.signal_queue.qsize()
        }
    
    async def set_zerodha_client(self, client):
        """Set the Zerodha client"""
        self.zerodha_client = client
        logger.info("✅ Zerodha client connected to trade engine")
    
    async def emergency_cancel_all_orders(self) -> int:
        """Emergency cancellation of all active orders"""
        try:
            cancelled_count = 0
            order_ids = list(self.active_orders.keys())
            
            for order_id in order_ids:
                await self._cancel_order(order_id, "Emergency cancellation")
                cancelled_count += 1
            
            logger.warning(f"🚨 Emergency cancelled {cancelled_count} orders")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Error in emergency cancellation: {e}")
            return 0 
"""
Trade Engine - Handles order execution and management
"""

import asyncio
import logging
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from src.core.paper_trading_user_manager import PaperTradingUserManager
from src.core.database_schema_manager import DatabaseSchemaManager
from sqlalchemy import text

class TradeEngine:
    """Enhanced trade engine with paper trading support"""
    
    def __init__(self, db_config, order_manager, position_tracker, performance_tracker, notification_manager, config=None):
        """Initialize trade engine with all required components and configuration"""
        self.db_config = db_config
        self.order_manager = order_manager
        self.position_tracker = position_tracker
        self.performance_tracker = performance_tracker
        self.notification_manager = notification_manager
        self.logger = logging.getLogger(__name__)
        
        # Handle configuration with defaults
        self.config = config or {}
        
        # CRITICAL FIX: Initialize paper trading mode from configuration  
        self.paper_trading_enabled = self.config.get('paper_trading', False)  # Default to LIVE TRADING for real money
        
        # CRITICAL FIX: Initialize all missing attributes
        self.paper_orders = {}  # Store paper trading orders
        self.pending_signals = []  # Store pending signals
        self.signal_rate_limit = 10.0  # Max 10 signals per second
        self.last_signal_time = 0.0  # Last signal processing time
        
        # Initialize additional required attributes
        self.zerodha_client = None  # Will be set by orchestrator
        self.risk_manager = None  # Will be set by orchestrator
        
        # Ensure precise database schema
        self._ensure_database_schema()
        
        # Initialize paper trading user manager (no arguments needed - it uses static methods)
        self.paper_user_manager = PaperTradingUserManager()
        
        # Initialize statistics
        self.statistics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'last_trade_time': None
        }
        
        # Status tracking
        self.is_active = True
        self.last_error = None
        
        self.logger.info(f"✅ TradeEngine initialized - Paper trading: {self.paper_trading_enabled}")
    
    def _ensure_database_schema(self):
        """Ensure database has precise schema - this is the definitive approach"""
        try:
            schema_manager = DatabaseSchemaManager(self.db_config.database_url)
            result = schema_manager.ensure_precise_schema()
            
            if result['status'] == 'success':
                self.logger.info("Trade engine: Database schema verified")
            else:
                self.logger.error(f"Trade engine: Database schema issues: {result['errors']}")
                
        except Exception as e:
            self.logger.error(f"Trade engine: Error ensuring database schema: {e}")
    
    async def initialize(self):
        """Initialize trade engine"""
        try:
            self.logger.info("✅ Trade Engine initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Trade Engine initialization failed: {e}")
            return False
    
    async def process_signal(self, signal: Dict):
        """Process trading signal with paper trading support"""
        try:
            # Check if paper trading is enabled
            if self.paper_trading_enabled:
                return await self._process_paper_signal(signal)
            else:
                return await self._process_live_signal(signal)
                
        except Exception as e:
            self.logger.error(f"❌ Error processing signal: {e}")
            return None
    
    async def process_signals(self, signals: List[Dict]):
        """Process trading signals and track execution results"""
        if not signals:
            return []
        
        self.logger.info(f"🔍 Processing {len(signals)} signals for execution")
        execution_results = []
        
        for signal in signals:
            try:
                if self.paper_trading_enabled:
                    result = await self._process_paper_signal(signal)
                else:
                    result = await self._process_live_signal(signal)
                
                if result:
                    execution_results.append(result)
                    # TRACK: Signal executed successfully
                    self._track_signal_executed(signal)
                    self.logger.info(f"✅ Signal executed: {signal.get('symbol')} {signal.get('action')}")
                else:
                    execution_results.append(None)
                    # TRACK: Signal execution failed
                    self._track_signal_execution_failed(signal, "Execution returned None")
                    self.logger.error(f"❌ Signal execution failed: {signal.get('symbol')} {signal.get('action')}")
                    
            except Exception as e:
                execution_results.append(None)
                # TRACK: Signal execution failed with exception
                self._track_signal_execution_failed(signal, str(e))
                self.logger.error(f"❌ Signal processing failed: {signal.get('symbol')} {signal.get('action')} - {e}")
        
        # Update pending signals list
        if hasattr(self, 'pending_signals'):
            self.pending_signals.extend([s for s, r in zip(signals, execution_results) if r is None])
        
        return execution_results
    
    def _track_signal_executed(self, signal: Dict):
        """Track successful signal execution"""
        try:
            # Get orchestrator instance to update stats
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'signal_stats'):
                orchestrator.signal_stats['executed'] += 1
                
                strategy = signal.get('strategy', 'unknown')
                if strategy in orchestrator.signal_stats['by_strategy']:
                    orchestrator.signal_stats['by_strategy'][strategy]['executed'] += 1
                
                self.logger.info(f"📊 EXECUTION TRACKED: Total executed: {orchestrator.signal_stats['executed']}")
                
        except Exception as e:
            self.logger.error(f"Error tracking signal execution: {e}")
    
    def _track_signal_execution_failed(self, signal: Dict, reason: str):
        """Track failed signal execution"""
        try:
            # Get orchestrator instance to update stats
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, '_track_signal_failed'):
                orchestrator._track_signal_failed(signal, reason)
            else:
                self.logger.error(f"📊 EXECUTION FAILED: {signal.get('symbol')} - {reason}")
                
        except Exception as e:
            self.logger.error(f"Error tracking signal execution failure: {e}")
    
    async def _process_paper_signal(self, signal: Dict):
        """Process signal in paper trading mode with REAL Zerodha API and P&L tracking"""
        try:
            self.logger.info(f"📊 Processing paper signal for {signal.get('symbol', 'UNKNOWN')}")
            
            # CRITICAL FIX: Use real Zerodha API even in paper mode
            if self.zerodha_client:
                # Create order for Zerodha API (sandbox mode)
                order_data = {
                    'symbol': signal.get('symbol'),
                    'quantity': signal.get('quantity', 50),
                    'side': signal.get('side', 'BUY'),
                    'order_type': 'MARKET',
                    'product': 'MIS',  # Intraday
                    'validity': 'DAY'
                }
                
                # Place order through Zerodha (sandbox)
                result = await self.zerodha_client.place_order(order_data)
                
                if result and result.get('success'):
                    order_id = result.get('order_id', f"PAPER_{int(time.time())}")
                    execution_price = result.get('price', signal.get('price', 0))
                    
                    # CRITICAL FIX: Never store trades with zero or invalid prices
                    if not execution_price or execution_price <= 0:
                        self.logger.error(f"❌ INVALID EXECUTION PRICE: {execution_price} for {signal.get('symbol')}")
                        self.logger.error("❌ REJECTED: Cannot store trade with zero/invalid price - violates no-mock-data policy")
                        return None
                    
                    # Create trade record with real execution data
                    trade_record = {
                        'trade_id': order_id,
                        'symbol': signal.get('symbol'),
                        'side': signal.get('side', 'BUY'), 
                        'quantity': signal.get('quantity', 50),
                        'price': execution_price,
                        'strategy': signal.get('strategy', 'unknown'),
                        'status': 'EXECUTED',
                        'executed_at': datetime.now(),
                        'user_id': 'PAPER_TRADER_001'
                    }
                    
                    # Update position tracker
                    if self.position_tracker:
                        await self.position_tracker.update_position(
                            symbol=trade_record['symbol'],
                            quantity=trade_record['quantity'],
                            price=execution_price,
                            side=trade_record['side'].lower()
                        )
                    
                    # CRITICAL FIX: Calculate real P&L and store to database
                    await self._calculate_and_store_trade_pnl(trade_record)
                    
                    self.logger.info(f"✅ Paper trade executed via Zerodha API: {order_id}")
                    return trade_record
                
            # SAFETY: When Zerodha fails, STOP trading - no fallback execution
            self.logger.error("❌ CRITICAL: Zerodha client not available - STOPPING trade execution")
            self.logger.error("❌ NO FALLBACK EXECUTION - Real broker required for all trades")
            self.logger.error(f"❌ Signal REJECTED: {signal.get('symbol')} {signal.get('side')} {signal.get('quantity')}")
            
            # Return None to indicate trade execution failed - no fake trades created
            return None
                
        except Exception as e:
            self.logger.error(f"❌ Error processing paper signal: {e}")
            return None

    async def _calculate_and_store_trade_pnl(self, trade_record: Dict):
        """Calculate real-time P&L and store trade to database"""
        try:
            symbol = trade_record['symbol']
            entry_price = float(trade_record['price'])
            quantity = trade_record['quantity']
            side = trade_record['side']
            
            # Get current market price from TrueData
            current_price = await self._get_current_market_price(symbol)
            if not current_price:
                current_price = entry_price  # Fallback to entry price
            
            # Calculate P&L
            if side.upper() == 'BUY':
                pnl = (current_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - current_price) * quantity
            
            # Calculate P&L percentage
            position_value = entry_price * quantity
            pnl_percent = (pnl / position_value) * 100 if position_value > 0 else 0
            
            # Update trade record
            trade_record['pnl'] = round(pnl, 2)
            trade_record['pnl_percent'] = round(pnl_percent, 2)
            trade_record['current_price'] = current_price
            
            # Store to database
            await self._store_trade_to_database(trade_record)
            
            self.logger.info(f"💰 P&L calculated and stored for {symbol}: ₹{pnl:.2f} ({pnl_percent:.2f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating and storing P&L: {e}")

    async def _get_current_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price from TrueData cache"""
        try:
            # Try to get from TrueData cache
            from data.truedata_client import live_market_data
            if symbol in live_market_data:
                market_data = live_market_data[symbol]
                # Use LTP (Last Traded Price) or Close price
                return float(market_data.get('ltp', market_data.get('close', 0)))
            
            # Try Redis cache
            if hasattr(self, 'redis_client') and self.redis_client:
                cached_price = await self.redis_client.get(f"price:{symbol}")
                if cached_price:
                    return float(cached_price)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market price for {symbol}: {e}")
            return None

    async def _store_trade_to_database(self, trade_record: Dict):
        """Store trade to database with P&L data"""
        try:
            from src.config.database import get_db
            db_session = next(get_db())
            
            if db_session:
                from sqlalchemy import text
                insert_query = text("""
                    INSERT INTO trades (
                        order_id, user_id, symbol, trade_type, quantity, price,
                        strategy, pnl, pnl_percent, status, executed_at
                    ) VALUES (
                        :order_id, :user_id, :symbol, :trade_type, :quantity, :price,
                        :strategy, :pnl, :pnl_percent, :status, :executed_at
                    )
                """)
                
                # Get user_id (ensure it exists)
                user_query = text("SELECT id FROM users WHERE username = 'PAPER_TRADER_001' LIMIT 1")
                user_result = db_session.execute(user_query)
                user_row = user_result.fetchone()
                user_id = user_row.id if user_row else 1
                
                db_session.execute(insert_query, {
                    'order_id': trade_record['trade_id'],  # Store the order reference in order_id field
                    'user_id': user_id,
                    'symbol': trade_record['symbol'],
                    'trade_type': trade_record['side'].lower(),
                    'quantity': trade_record['quantity'],
                    'price': trade_record['price'],
                    'strategy': trade_record['strategy'],
                    'pnl': trade_record.get('pnl', 0),
                    'pnl_percent': trade_record.get('pnl_percent', 0),
                    'status': trade_record['status'],
                    'executed_at': trade_record['executed_at']
                })
                
                db_session.commit()
                self.logger.info(f"✅ Trade stored to database with order_id: {trade_record['trade_id']}")
                
        except Exception as e:
            self.logger.error(f"❌ Error storing trade to database: {e}")
    
    async def _process_live_signal(self, signal: Dict):
        """Process signal in live trading mode"""
        try:
            # Check rate limiting
            current_time = time.time()
            if current_time - self.last_signal_time < (1.0 / self.signal_rate_limit):
                wait_time = (1.0 / self.signal_rate_limit) - (current_time - self.last_signal_time)
                self.logger.info(f"⏱️ Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            # Process through order manager if available
            if self.order_manager:
                return await self._process_signal_through_order_manager(signal)
            elif self.zerodha_client:
                return await self._process_signal_through_zerodha(signal)
            else:
                self.logger.warning("❌ No order execution method available")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error processing live signal: {e}")
            return None
    
    async def _process_signal_through_order_manager(self, signal: Dict):
        """Process signal through order manager"""
        try:
            # Create order from signal
            order = self._create_order_from_signal(signal)
            
            # Submit order
            order_id = await self.order_manager.place_order(order)
            
            # Log order placement
            self.logger.info(f"📋 Order placed: {order_id} for user {signal.get('user_id', 'system')}")
            
            # Update rate limiting
            self.last_signal_time = time.time()
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"❌ Error processing signal through order manager: {e}")
            return None
    
    async def _process_signal_through_zerodha(self, signal: Dict):
        """Process signal through direct Zerodha integration"""
        try:
            if not self.zerodha_client:
                self.logger.warning("❌ No Zerodha client available")
                return None
                
            # Create order
            order = self._create_order_from_signal(signal)
            
            # Place order through Zerodha
            order_id = await self.zerodha_client.place_order(order)
            
            if order_id:
                self.logger.info(f"📋 Zerodha order placed: {order_id}")
                self.last_signal_time = time.time()
                return order_id
            else:
                self.logger.error("❌ Zerodha order failed")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error processing signal through Zerodha: {e}")
            return None
    
    def _create_order_from_signal(self, signal: Dict) -> Dict:
        """Create order parameters from signal"""
        return {
            'symbol': signal.get('symbol'),
            'action': signal.get('action', 'BUY'),
            'transaction_type': signal.get('action', 'BUY'),
            'quantity': signal.get('quantity', 0),
            'price': signal.get('entry_price'),
            'entry_price': signal.get('entry_price'),
            'order_type': signal.get('order_type', 'MARKET'),
            'product': signal.get('product', 'MIS'),
            'validity': signal.get('validity', 'DAY'),
            'tag': 'ALGO_TRADE',
            'user_id': signal.get('user_id', 'system')
        }
    
    def get_paper_orders(self) -> Dict:
        """Get all paper trading orders"""
        return self.paper_orders
    
    def get_paper_order_status(self, order_id: str) -> Optional[Dict]:
        """Get paper order status"""
        return self.paper_orders.get(order_id)
    
    async def cancel_paper_order(self, order_id: str) -> bool:
        """Cancel paper order"""
        if order_id in self.paper_orders:
            self.paper_orders[order_id]['status'] = 'CANCELLED'
            self.logger.info(f"📋 Paper order cancelled: {order_id}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trade engine statistics"""
        try:
            executed_count = len([order for order in self.paper_orders.values() if order.get('status') == 'EXECUTED'])
            pending_count = len([order for order in self.paper_orders.values() if order.get('status') == 'PENDING'])
            cancelled_count = len([order for order in self.paper_orders.values() if order.get('status') == 'CANCELLED'])
            
            return {
                'total_orders': len(self.paper_orders),
                'executed_trades': executed_count,
                'pending_orders': pending_count,
                'cancelled_orders': cancelled_count,
                'paper_trading_enabled': self.paper_trading_enabled,
                'signals_processed': len(self.pending_signals),
                'rate_limit_per_second': self.signal_rate_limit,
                'last_signal_time': self.last_signal_time,
                'engine_status': 'active' if hasattr(self, 'is_running') and getattr(self, 'is_running', False) else 'inactive'
            }
        except Exception as e:
            self.logger.error(f"Error getting trade engine statistics: {e}")
            return {
                'total_orders': 0,
                'executed_trades': 0,
                'pending_orders': 0,
                'cancelled_orders': 0,
                'paper_trading_enabled': self.paper_trading_enabled,
                'signals_processed': 0,
                'rate_limit_per_second': self.signal_rate_limit,
                'last_signal_time': self.last_signal_time,
                'engine_status': 'error'
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get trade engine status (async version)"""
        stats = self.get_statistics()
        stats.update({
            'initialized': hasattr(self, 'is_initialized') and getattr(self, 'is_initialized', False),
            'running': hasattr(self, 'is_running') and getattr(self, 'is_running', False),
            'order_manager_available': self.order_manager is not None,
            'zerodha_client_available': self.zerodha_client is not None,
            'risk_manager_available': self.risk_manager is not None,
            'timestamp': datetime.now().isoformat()
        })
        return stats 

    async def save_paper_trade(self, trade_data: dict) -> bool:
        """Save paper trade to database with precise schema handling"""
        try:
            # Get paper trading user
            user = self.paper_user_manager.get_or_create_paper_user()
            if not user:
                self.logger.error("Failed to get paper trading user")
                return False
                
            # Create paper trade record with precise schema
            paper_trade = {
                'user_id': user['id'],  # Use the precise id field
                'symbol': trade_data.get('symbol'),
                'action': trade_data.get('action'),
                'quantity': trade_data.get('quantity'),
                'price': trade_data.get('price'),
                'timestamp': trade_data.get('timestamp', datetime.now()),
                'status': trade_data.get('status', 'executed'),
                'order_id': trade_data.get('order_id'),
                'pnl': trade_data.get('pnl', 0.0),
                'strategy': trade_data.get('strategy'),
                'created_at': datetime.now()
            }
            
            # Save to database
            async with self.db_config.get_session() as session:
                # Use text query for precise control
                insert_query = text("""
                    INSERT INTO paper_trades (
                        user_id, symbol, action, quantity, price, timestamp,
                        status, order_id, pnl, strategy, created_at
                    ) VALUES (
                        :user_id, :symbol, :action, :quantity, :price, :timestamp,
                        :status, :order_id, :pnl, :strategy, :created_at
                    )
                """)
                
                await session.execute(insert_query, paper_trade)
                await session.commit()
                
                self.logger.info(f"Paper trade saved: {trade_data['symbol']} {trade_data['action']} {trade_data['quantity']}@{trade_data['price']}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving paper trade: {e}")
            # Try to rollback if possible
            try:
                await session.rollback()
            except:
                pass
            return False 
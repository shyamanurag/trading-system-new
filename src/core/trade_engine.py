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
from src.core.order_rate_limiter import OrderRateLimiter
from sqlalchemy import text

class TradeEngine:
    """Enhanced trade engine with paper trading support"""
    
    def __init__(self, db_config, order_manager, position_tracker, performance_tracker, notification_manager, config=None):
        """Initialize trade engine with all required components and configuration"""
        self.db_config = db_config
        self.order_manager = order_manager
        self.position_tracker = position_tracker
        
        # Initialize order rate limiter to prevent retry loops
        self.rate_limiter = OrderRateLimiter()
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
        
        # 🚨 CRITICAL FIX: Add batch rate limiting to prevent API overwhelming
        if len(signals) > 5:
            self.logger.warning(f"⚠️ LARGE BATCH DETECTED: {len(signals)} signals - applying strict rate limiting")
            batch_delay = 2.0  # 2 seconds between orders for large batches
        else:
            batch_delay = 1.0  # 1 second for normal batches
            
        execution_results = []
        
        for i, signal in enumerate(signals):
            try:
                # 🚨 BATCH RATE LIMITING: Add delay between signals to prevent API overwhelm
                if i > 0:  # Skip delay for first signal
                    self.logger.info(f"⏱️ BATCH RATE LIMIT: Waiting {batch_delay}s before processing signal {i+1}/{len(signals)}")
                    await asyncio.sleep(batch_delay)
                
                if self.paper_trading_enabled:
                    result = await self._process_paper_signal(signal)
                else:
                    result = await self._process_live_signal(signal)
                
                if result:
                    execution_results.append(result)
                    # TRACK: Signal executed successfully
                    self._track_signal_executed(signal)
                    # 🚨 CRITICAL FIX: Mark signal as executed to prevent duplicates across deploys
                    await self._mark_signal_executed_in_deduplicator(signal)
                    self.logger.info(f"✅ Signal executed: {signal.get('symbol')} {signal.get('action')} ({i+1}/{len(signals)})")
                else:
                    execution_results.append(None)
                    # TRACK: Signal execution failed
                    self._track_signal_execution_failed(signal, "Execution returned None")
                    self.logger.error(f"❌ Signal execution failed: {signal.get('symbol')} {signal.get('action')} ({i+1}/{len(signals)})")
                    
            except Exception as e:
                execution_results.append(None)
                # TRACK: Signal execution failed with exception
                self._track_signal_execution_failed(signal, str(e))
                self.logger.error(f"❌ Signal processing failed: {signal.get('symbol')} {signal.get('action')} - {e} ({i+1}/{len(signals)})")
        
        # Update pending signals list
        if hasattr(self, 'pending_signals'):
            self.pending_signals.extend([s for s, r in zip(signals, execution_results) if r is None])
        
        successful_executions = len([r for r in execution_results if r is not None])
        self.logger.info(f"📊 BATCH COMPLETED: {successful_executions}/{len(signals)} signals executed successfully")
        
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
        """Track failed signal execution and route high-confidence orders to elite recommendations"""
        try:
            # Get orchestrator instance to update stats
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, '_track_signal_failed'):
                orchestrator._track_signal_failed(signal, reason)
            else:
                self.logger.error(f"📊 EXECUTION FAILED: {signal.get('symbol')} - {reason}")
            
            # CRITICAL: Route high-confidence failed orders to Elite Recommendations
            confidence = signal.get('confidence', 0)
            if confidence >= 9.0:
                self._route_failed_order_to_elite(signal, reason)
                
        except Exception as e:
            self.logger.error(f"Error tracking signal execution failure: {e}")
    
    def _route_failed_order_to_elite(self, signal: Dict, reason: str):
        """Route failed high-confidence order to Elite Recommendations"""
        try:
            import requests
            import asyncio
            
            # Prepare failed order data
            failed_order_data = {
                **signal,
                'failure_reason': reason,
                'failed_at': datetime.now().isoformat(),
                'routed_to_elite': True
            }
            
            # Try to send to Elite Recommendations API
            try:
                response = requests.post(
                    'http://localhost:8000/api/elite-recommendations/add-failed-order',
                    json=failed_order_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    self.logger.info(f"📋 ELITE ROUTED: Failed order {signal.get('symbol')} "
                                   f"(confidence: {signal.get('confidence', 0):.1f}) added to Elite Recommendations")
                else:
                    self.logger.warning(f"Failed to route {signal.get('symbol')} to Elite API: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Elite API unavailable for {signal.get('symbol')}: {e}")
                # Continue without Elite routing - not critical for execution
                
        except Exception as e:
            self.logger.error(f"Error routing failed order to elite: {e}")
            # Don't let this failure affect main execution flow
    
    async def _try_get_zerodha_client_from_orchestrator(self):
        """Try to get Zerodha client from orchestrator if not set"""
        try:
            # CRITICAL FIX: Use correct function name
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                self.zerodha_client = orchestrator.zerodha_client
                self.logger.info("✅ Successfully retrieved Zerodha client from orchestrator")
                return True
            else:
                self.logger.error("❌ No Zerodha client available in orchestrator")
                # CRITICAL DEBUG: Log orchestrator state
                if orchestrator:
                    self.logger.error(f"❌ Orchestrator exists but zerodha_client is: {getattr(orchestrator, 'zerodha_client', 'MISSING')}")
                else:
                    self.logger.error("❌ No orchestrator instance found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error getting Zerodha client from orchestrator: {e}")
            return False
    
    async def _mark_signal_executed_in_deduplicator(self, signal: Dict):
        """Mark signal as executed in deduplicator to prevent duplicates across deploys"""
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'signal_deduplicator') and orchestrator.signal_deduplicator:
                await orchestrator.signal_deduplicator.mark_signal_executed(signal)
                self.logger.debug(f"✅ Signal marked as executed in deduplicator: {signal.get('symbol')}")
            else:
                # 🔧 FIX: Try to initialize signal deduplicator if not available
                if orchestrator and not hasattr(orchestrator, 'signal_deduplicator'):
                    try:
                        from src.core.signal_deduplicator import SignalDeduplicator
                        orchestrator.signal_deduplicator = SignalDeduplicator()
                        await orchestrator.signal_deduplicator.initialize()
                        await orchestrator.signal_deduplicator.mark_signal_executed(signal)
                        self.logger.info("✅ Signal deduplicator initialized and signal marked")
                        return
                    except Exception as init_error:
                        self.logger.warning(f"⚠️ Could not initialize signal deduplicator: {init_error}")
                
                self.logger.debug("⚠️ Signal deduplicator not available - skipping duplicate marking")
                
        except Exception as e:
            self.logger.error(f"❌ Error marking signal as executed: {e}")
    
    async def _process_paper_signal(self, signal: Dict):
        """Process paper trading signal - ONLY store if actually executed by Zerodha"""
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', 'BUY')
            quantity = signal.get('quantity', 50)
            strategy = signal.get('strategy', 'unknown')
            
            self.logger.info(f"📊 Processing paper signal for {symbol}")
            self.logger.info(f"🔄 Signal: {symbol} {action} → Order: {symbol} {action}")
            
            # 🚨 CRITICAL FIX: Attempt to get Zerodha client if not available
            if not self.zerodha_client:
                self.logger.warning("⚠️ Zerodha client not set, attempting to retrieve from orchestrator")
                await self._try_get_zerodha_client_from_orchestrator()
            
            # CRITICAL FIX: Only execute if Zerodha client is available
            if not self.zerodha_client:
                self.logger.error("❌ CRITICAL: Zerodha client is None - NO FALLBACK EXECUTION")
                self.logger.error("❌ NO FALLBACK EXECUTION - Real broker required for all trades") 
                self.logger.error("🚨 SYSTEM DESIGNED TO FAIL WHEN BROKER UNAVAILABLE - FIX ZERODHA CONNECTION")
                return None
            elif not self.zerodha_client.is_connected:
                self.logger.error(f"❌ CRITICAL: Zerodha client not connected - State: {getattr(self.zerodha_client, 'connection_state', 'UNKNOWN')}")
                self.logger.error(f"❌ Kite object: {self.zerodha_client.kite is not None}")
                self.logger.error(f"❌ Access token: {self.zerodha_client.access_token is not None}")
                self.logger.error("❌ NO FALLBACK EXECUTION - Real broker required for all trades")
                self.logger.error("🚨 SYSTEM DESIGNED TO FAIL WHEN BROKER UNAVAILABLE - FIX ZERODHA CONNECTION")
                return None
            
            # CRITICAL: Check actual Zerodha wallet balance before placing order
            estimated_order_value = signal.get('entry_price', 100) * quantity
            
            if not await self._check_available_capital(estimated_order_value):
                self.logger.error(f"❌ ORDER REJECTED: Insufficient Zerodha wallet balance for {symbol}")
                self.logger.error(f"❌ Required: ₹{estimated_order_value:,.2f} - Check your Zerodha account balance")
                return None
            
            # CRITICAL: Check for existing position BEFORE placing order
            if symbol and await self._check_existing_position(symbol, action):
                self.logger.error(f"❌ DUPLICATE ORDER BLOCKED: Existing position found for {symbol} {action}")
                return None
            
            # 🛡️ CRITICAL: Check order rate limits to prevent retry loops
            rate_check = await self.rate_limiter.can_place_order(symbol, action, quantity, signal.get('entry_price', 0))
            if not rate_check['allowed']:
                self.logger.error(f"🚫 ORDER RATE LIMITED: {rate_check['message']}")
                self.logger.error(f"🚫 Reason: {rate_check['reason']}")
                return None
            
            # Place order via Zerodha (real execution)
            # 🚨 CRITICAL FIX: Use LIMIT orders for stock options to avoid Zerodha blocking
            order_type = 'MARKET'  # Default to MARKET
            if symbol:  # Add null check for symbol
                if (symbol.endswith('CE') or symbol.endswith('PE')) and not any(index in symbol for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']):
                    order_type = 'LIMIT'
            
            order_params = {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'order_type': order_type,
                'strategy': strategy
            }
            
            # Add price for LIMIT orders (stock options)
            if order_type == 'LIMIT' and symbol:
                # Use entry price from signal or calculate a reasonable limit price
                limit_price = signal.get('entry_price', 0)
                if limit_price > 0:
                    order_params['price'] = limit_price
                    self.logger.info(f"🔧 Using LIMIT order for stock option: {symbol} @ ₹{limit_price}")
                else:
                    self.logger.warning(f"⚠️ No entry price for LIMIT order: {symbol} - using MARKET as fallback")
                    order_params['order_type'] = 'MARKET'
            
            result = await self.zerodha_client.place_order(order_params)
            
            # 📊 Record order attempt in rate limiter
            order_success = result and isinstance(result, str)
            await self.rate_limiter.record_order_attempt(
                rate_check['signature'], 
                order_success, 
                symbol, 
                str(result) if not order_success else None
            )
            
            # CRITICAL FIX: Only store trades that were ACTUALLY executed by Zerodha
            if order_success:
                # ZerodhaIntegration returns order_id string directly - this means REAL execution
                order_id = result
                execution_price = signal.get('entry_price', 0)
                
                # CRITICAL FIX: Never store trades with zero or invalid prices
                if not execution_price or execution_price <= 0:
                    self.logger.error(f"❌ INVALID EXECUTION PRICE: {execution_price} for {symbol}")
                    self.logger.error("❌ REJECTED: Cannot store trade with zero/invalid price - violates no-mock-data policy")
                    return None
                
                # CRITICAL FIX: Only create trade record for REAL Zerodha executions
                trade_record = {
                    'trade_id': order_id,
                    'symbol': symbol,
                    'side': action,
                    'quantity': quantity,
                    'price': execution_price,
                    'strategy': strategy,
                    'status': 'EXECUTED',  # ✅ REAL execution confirmed by Zerodha
                    'executed_at': datetime.now(),
                    'user_id': os.environ.get('ZERODHA_USER_ID', 'QSW899')  # Dynamic user ID
                }
                
                # Update position tracker with stop loss and target
                if self.position_tracker:
                    # Get stop loss and target directly from strategy signal - NO FALLBACKS
                    stop_loss_price = signal.get('stop_loss', 0)
                    target_price = signal.get('target', 0)
                    
                    # Only proceed if strategy provided both values
                    if stop_loss_price and target_price and execution_price > 0:
                        # Update position with strategy-provided stop loss and target
                        position = await self.position_tracker.get_position(symbol)
                        if position:
                            position.stop_loss = stop_loss_price
                            position.target = target_price
                            position.trailing_stop = stop_loss_price  # Initialize trailing stop
                            
                            self.logger.info(f"🎯 Position risk levels set for {symbol} (from strategy):")
                            self.logger.info(f"   Entry: ₹{execution_price:.2f}")
                            self.logger.info(f"   Stop Loss: ₹{stop_loss_price:.2f} (from strategy)")
                            self.logger.info(f"   Target: ₹{target_price:.2f} (from strategy)")
                        else:
                            self.logger.warning(f"⚠️ Position not found for {symbol} - cannot set risk levels")
                    else:
                        self.logger.error(f"❌ Strategy didn't provide stop_loss/target for {symbol} - NO RISK LEVELS SET")
                        self.logger.error(f"   stop_loss: {stop_loss_price}, target: {target_price}")
                    
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
            else:
                # CRITICAL FIX: Don't store failed or non-executed trades
                self.logger.warning(f"⚠️ Signal not executed: {symbol} {action} - No Zerodha execution")
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
            
            # CRITICAL FIX: Get REAL current market price from TrueData
            current_price = await self._get_current_market_price(symbol)
            if not current_price or current_price <= 0:
                self.logger.warning(f"⚠️ No real-time price for {symbol}, using entry price as fallback")
                current_price = entry_price  # Fallback only
            
            # CRITICAL FIX: Ensure we have different prices for meaningful P&L calculation
            if current_price == entry_price:
                self.logger.warning(f"⚠️ Same price for {symbol}: Entry ₹{entry_price} = Current ₹{current_price}")
                # Try to get a different price from market data
                from data.truedata_client import live_market_data
                if symbol in live_market_data:
                    market_data = live_market_data[symbol]
                    if 'ltp' in market_data and market_data['ltp'] != entry_price:
                        current_price = market_data['ltp']
                        self.logger.info(f"✅ Updated current price for {symbol}: ₹{current_price}")
            
            # Calculate P&L based on real market movement
            if side.upper() == 'BUY':
                pnl = (current_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - current_price) * quantity
            
            # Calculate P&L percentage
            position_value = entry_price * quantity
            pnl_percent = (pnl / position_value) * 100 if position_value > 0 else 0
            
            # Update trade record with REAL market data
            trade_record['pnl'] = round(pnl, 2)
            trade_record['pnl_percent'] = round(pnl_percent, 2)
            trade_record['current_price'] = current_price
            trade_record['entry_price'] = entry_price  # Keep original entry
            
            # Store to database
            await self._store_trade_to_database(trade_record)
            
            # Start background price monitoring for this trade
            asyncio.create_task(self._monitor_trade_price_updates(trade_record))
            
            self.logger.info(f"💰 P&L calculated for {symbol}: Entry ₹{entry_price:.2f} → Current ₹{current_price:.2f} = ₹{pnl:.2f} ({pnl_percent:.2f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating and storing P&L: {e}")
    
    async def _monitor_trade_price_updates(self, trade_record: Dict):
        """Background task to continuously update trade prices and P&L"""
        symbol = trade_record['symbol']
        trade_id = trade_record['trade_id']
        
        try:
            while True:
                # Get fresh market price
                current_price = await self._get_current_market_price(symbol)
                
                if current_price and current_price > 0:
                    # Recalculate P&L with new price
                    entry_price = float(trade_record['price'])
                    quantity = trade_record['quantity']
                    side = trade_record['side']
                    
                    if side.upper() == 'BUY':
                        pnl = (current_price - entry_price) * quantity
                    else:  # SELL
                        pnl = (entry_price - current_price) * quantity
                    
                    position_value = entry_price * quantity
                    pnl_percent = (pnl / position_value) * 100 if position_value > 0 else 0
                    
                    # Update database with new P&L
                    await self._update_trade_pnl_in_database(trade_id, current_price, pnl, pnl_percent)
                    
                    self.logger.debug(f"📊 Updated {symbol}: ₹{current_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_percent:.2f}%)")
                
                # Update every 30 seconds during market hours
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            self.logger.info(f"⏹️ Stopped price monitoring for {symbol}")
        except Exception as e:
            self.logger.error(f"❌ Error in price monitoring for {symbol}: {e}")
    
    async def _update_trade_pnl_in_database(self, trade_id: str, current_price: float, pnl: float, pnl_percent: float):
        """Update trade P&L in database with real-time data"""
        try:
            from src.config.database import get_db
            db_session = next(get_db())
            
            if db_session:
                from sqlalchemy import text
                # FIXED: Remove current_price and updated_at updates since trades table doesn't have these columns
                # Only update pnl and pnl_percent fields which exist in the schema
                update_query = text("""
                    UPDATE trades 
                    SET pnl = :pnl, 
                        pnl_percent = :pnl_percent
                    WHERE order_id = :trade_id
                """)
                
                db_session.execute(update_query, {
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'trade_id': trade_id
                })
                db_session.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Error updating trade P&L in database: {e}")
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()
    
    async def sync_actual_zerodha_trades(self):
        """CRITICAL: Fetch ACTUAL executed trades from Zerodha API"""
        try:
            if not self.zerodha_client:
                self.logger.warning("⚠️ No Zerodha client for trade sync")
                return
            
            self.logger.info("🔄 Syncing actual executed trades from Zerodha...")
            
            # Get actual orders from Zerodha API
            zerodha_orders = await self.zerodha_client.get_orders()
            
            if not zerodha_orders:
                self.logger.warning("⚠️ No orders returned from Zerodha API")
                return
            
            executed_trades = []
            for order in zerodha_orders:
                if order.get('status') == 'COMPLETE':
                    # This is an ACTUAL executed trade
                    executed_trade = {
                        'trade_id': order.get('order_id'),
                        'symbol': order.get('tradingsymbol'),
                        'side': order.get('transaction_type'),
                        'quantity': order.get('filled_quantity', order.get('quantity')),
                        'price': order.get('average_price', order.get('price')),
                        'status': 'EXECUTED',
                        'executed_at': order.get('order_timestamp'),
                        'exchange_time': order.get('exchange_timestamp')
                    }
                    executed_trades.append(executed_trade)
            
            self.logger.info(f"✅ Found {len(executed_trades)} actual executed trades from Zerodha")
            
            # Update our records with ACTUAL execution data
            for trade in executed_trades:
                await self._update_with_actual_execution_data(trade)
            
            return executed_trades
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing actual Zerodha trades: {e}")
            return []
    
    async def _update_with_actual_execution_data(self, actual_trade: Dict):
        """Update internal trade records with ACTUAL execution data from Zerodha"""
        try:
            trade_id = actual_trade['trade_id']
            
            # Update database with ACTUAL execution data
            from src.config.database import get_db
            db_session = next(get_db())
            
            if db_session:
                from sqlalchemy import text
                
                # Check if trade exists in our database
                check_query = text("SELECT order_id FROM trades WHERE order_id = :trade_id")
                existing = db_session.execute(check_query, {'trade_id': trade_id}).fetchone()
                
                if existing:
                    # Update with actual execution data
                    update_query = text("""
                        UPDATE trades 
                        SET quantity = :quantity,
                            price = :price,
                            executed_at = :executed_at
                        WHERE order_id = :trade_id
                    """)
                    
                    db_session.execute(update_query, {
                        'quantity': actual_trade['quantity'],
                        'price': actual_trade['price'],
                        'executed_at': actual_trade['executed_at'],
                        'trade_id': trade_id
                    })
                else:
                    # Insert new ACTUAL trade that we didn't track before
                    insert_query = text("""
                        INSERT INTO trades (
                            order_id, symbol, trade_type, quantity, price,
                            status, executed_at, user_id
                        ) VALUES (
                            :trade_id, :symbol, :side, :quantity, :price,
                            :status, :executed_at, :user_id
                        )
                    """)
                    
                    db_session.execute(insert_query, {
                        'trade_id': trade_id,
                        'symbol': actual_trade['symbol'],
                        'side': actual_trade['side'],
                        'quantity': actual_trade['quantity'],
                        'price': actual_trade['price'],
                        'status': actual_trade['status'],
                        'executed_at': actual_trade['executed_at'],
                        'user_id': 1  # Changed from 'ZERODHA_SYNC' to 1
                    })
                
                db_session.commit()
                self.logger.info(f"✅ Updated trade {trade_id} with ACTUAL execution data")
                
        except Exception as e:
            self.logger.error(f"❌ Error updating with actual execution data: {e}")
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()
    
    async def sync_actual_zerodha_positions(self):
        """CRITICAL: Fetch ACTUAL positions from Zerodha API for square-off"""
        try:
            if not self.zerodha_client:
                self.logger.warning("⚠️ No Zerodha client for position sync")
                return {}
            
            self.logger.info("🔄 Syncing actual positions from Zerodha for square-off...")
            
            # Get ACTUAL positions from Zerodha API
            positions_data = await self.zerodha_client.get_positions()
            
            if not positions_data:
                self.logger.warning("⚠️ No positions returned from Zerodha API")
                return {}
            
            # Extract net positions (for square-off)
            net_positions = positions_data.get('net', [])
            day_positions = positions_data.get('day', [])
            
            active_positions = {}
            
            # Process net positions (overnight positions)
            for pos in net_positions:
                if pos.get('quantity', 0) != 0:  # Only positions with quantity
                    symbol = pos.get('tradingsymbol')
                    active_positions[symbol] = {
                        'symbol': symbol,
                        'quantity': pos.get('quantity'),
                        'average_price': pos.get('average_price', 0),
                        'ltp': pos.get('last_price', 0),
                        'pnl': pos.get('pnl', 0),
                        'unrealized_pnl': pos.get('unrealized_pnl', 0),
                        'position_type': 'net',
                        'product': pos.get('product'),
                        'exchange': pos.get('exchange')
                    }
            
            # Process day positions (intraday)
            for pos in day_positions:
                if pos.get('quantity', 0) != 0:
                    symbol = pos.get('tradingsymbol')
                    active_positions[symbol] = {
                        'symbol': symbol,
                        'quantity': pos.get('quantity'),
                        'average_price': pos.get('average_price', 0),
                        'ltp': pos.get('last_price', 0),
                        'pnl': pos.get('pnl', 0),
                        'unrealized_pnl': pos.get('unrealized_pnl', 0),
                        'position_type': 'day',
                        'product': pos.get('product'),
                        'exchange': pos.get('exchange')
                    }
            
            self.logger.info(f"✅ Found {len(active_positions)} ACTUAL positions from Zerodha")
            
            # Update position tracker with ACTUAL positions
            if self.position_tracker:
                await self.position_tracker.sync_with_zerodha_positions(active_positions)
            
            return active_positions
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing actual Zerodha positions: {e}")
            return {}
    
    async def _update_position_tracker_with_actual_data(self, actual_positions: Dict):
        """Update position tracker with ACTUAL Zerodha position data"""
        try:
            for symbol, pos_data in actual_positions.items():
                await self.position_tracker.update_position(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    price=pos_data['average_price'],
                    side='long' if pos_data['quantity'] > 0 else 'short'
                )
                
                # Update with real-time LTP for P&L calculation
                if pos_data['ltp'] > 0:
                    market_data = {symbol: pos_data['ltp']}
                    await self.position_tracker.update_market_prices(market_data)
            
            self.logger.info(f"✅ Updated position tracker with {len(actual_positions)} ACTUAL positions")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating position tracker with actual data: {e}")
    
    async def start_real_time_sync(self):
        """Start background tasks for real-time Zerodha data synchronization"""
        self.logger.info("🚀 Starting real-time Zerodha data synchronization...")
        
        # Start trade sync (every 2 minutes)
        asyncio.create_task(self._periodic_trade_sync())
        
        # Start position sync (every 1 minute)  
        asyncio.create_task(self._periodic_position_sync())
        
        self.logger.info("✅ Real-time sync tasks started")
    
    async def _periodic_trade_sync(self):
        """Periodic task to sync actual trades from Zerodha"""
        while True:
            try:
                await self.sync_actual_zerodha_trades()
                await asyncio.sleep(120)  # Every 2 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in periodic trade sync: {e}")
                await asyncio.sleep(120)
    
    async def _periodic_position_sync(self):
        """Periodic task to sync actual positions from Zerodha"""
        while True:
            try:
                await self.sync_actual_zerodha_positions()
                await asyncio.sleep(60)  # Every 1 minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in periodic position sync: {e}")
                await asyncio.sleep(60)
    
    async def _get_current_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price from TrueData cache"""
        try:
            # Try to get from TrueData cache
            from data.truedata_client import live_market_data
            if symbol in live_market_data:
                market_data = live_market_data[symbol]
                # Use LTP (Last Traded Price) or Close price
                return float(market_data.get('ltp', market_data.get('close', 0)))
            
            # Try Redis cache if available
            # Note: redis_client not available in this context
            # if hasattr(self, 'redis_client') and self.redis_client:
            #     cached_price = await self.redis_client.get(f"price:{symbol}")
            #     if cached_price:
            #         return float(cached_price)
            
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
                
                # Get user_id dynamically (ensure it exists)
                dynamic_username = os.environ.get('ZERODHA_USER_ID', 'QSW899')
                user_query = text("SELECT id FROM users WHERE broker_user_id = :broker_user_id LIMIT 1")
                user_result = db_session.execute(user_query, {'broker_user_id': dynamic_username})
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
            # CRITICAL FIX: Attempt to get Zerodha client if not available
            if not self.zerodha_client:
                self.logger.warning("⚠️ Zerodha client not set, attempting to retrieve from orchestrator")
                await self._try_get_zerodha_client_from_orchestrator()
            
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
        # CRITICAL FIX: Properly map signal action to avoid direction reversal
        signal_action = signal.get('action', '').upper()
        if not signal_action:
            signal_action = signal.get('transaction_type', '').upper()
        if not signal_action:
            # Log warning if no action found - don't default to avoid wrong trades
            self.logger.warning(f"⚠️ No action found in signal for {signal.get('symbol', 'UNKNOWN')} - REJECTING")
            signal_action = 'INVALID'
        
        return {
            'symbol': signal.get('symbol'),
            'action': signal_action,  # ✅ FIXED: Primary action field
            'transaction_type': signal_action,  # ✅ FIXED: Zerodha backup field
            'side': signal_action,  # ✅ FIXED: Generic backup field
            'quantity': signal.get('quantity', 0),
            'price': signal.get('entry_price'),
            'entry_price': signal.get('entry_price'),
            'order_type': signal.get('order_type', 'MARKET'),
            'product': self._get_product_type_for_symbol(signal.get('symbol', '')),  # FIXED: Dynamic product type
            'validity': signal.get('validity', 'DAY'),
            'tag': 'ALGO_TRADE',
            'user_id': signal.get('user_id', 'system')
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

    async def _check_available_capital(self, order_value: float) -> bool:
        """
        Check actual Zerodha wallet balance before placing trades
        CRITICAL: Uses real broker data, not hardcoded amounts
        """
        try:
            if not self.zerodha_client:
                self.logger.error("❌ Cannot check capital - Zerodha client not available")
                return False
            
            # Get actual margin data from Zerodha
            margins = await self.zerodha_client.get_margins()
            
            if not margins:
                self.logger.error("❌ Failed to fetch margin data from Zerodha")
                return False
            
            # Extract available cash from Zerodha margins - FIXED: Use correct field path  
            available_cash = float(margins.get('equity', {}).get('available', {}).get('live_balance', 0))
            
            self.logger.info(f"💰 Zerodha Wallet Balance: ₹{available_cash:,.2f}")
            self.logger.info(f"📊 Required for Order: ₹{order_value:,.2f}")
            
            # Check if sufficient balance available
            if available_cash >= order_value:
                self.logger.info(f"✅ Sufficient balance available: ₹{available_cash:,.2f} >= ₹{order_value:,.2f}")
                return True
            else:
                self.logger.error(f"❌ Insufficient balance: ₹{available_cash:,.2f} < ₹{order_value:,.2f}")
                self.logger.error(f"❌ ORDER REJECTED: Need ₹{order_value - available_cash:,.2f} more")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error checking available capital: {e}")
            return False

    async def _check_existing_position(self, symbol: str, action: str) -> bool:
        """
        Check if there is an existing open position for the given symbol and action.
        This prevents placing duplicate orders for the same symbol.
        """
        try:
            if not self.position_tracker:
                self.logger.warning("⚠️ Position tracker not available, cannot check for existing position.")
                return False

            # Get current position for the symbol
            current_position = await self.position_tracker.get_position(symbol)

            if current_position:
                # If a position exists, check if it matches the action
                if action.upper() == 'BUY' and current_position.quantity > 0:
                    self.logger.warning(f"⚠️ Existing BUY position found for {symbol}. Current: {current_position.quantity}")
                    return True
                elif action.upper() == 'SELL' and current_position.quantity < 0:
                    self.logger.warning(f"⚠️ Existing SELL position found for {symbol}. Current: {current_position.quantity}")
                    return True
                else:
                    self.logger.info(f"✅ No duplicate order for {symbol} {action}. Current position: {current_position.quantity}")
                    return False
            else:
                self.logger.info(f"✅ No existing position for {symbol} {action}.")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error checking for existing position: {e}")
            return False

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
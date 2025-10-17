"""
Performance Tracking System
Logs all trades, daily performance, and analytics to PostgreSQL database
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks trading performance in PostgreSQL database
    - Logs every trade with full details
    - Tracks daily performance metrics
    - Strategy performance analytics
    - Real-time position tracking
    - System events logging
    """
    
    def __init__(self, db_config: Dict):
        """
        Initialize performance tracker
        
        Args:
            db_config: Database configuration {host, port, database, user, password}
        """
        self.db_config = db_config
        self.connection = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'trading_system'),
                user=self.db_config.get('user'),
                password=self.db_config.get('password')
            )
            self.connection.autocommit = True
            self.logger.info("✅ Performance tracker connected to database")
            return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("🔌 Performance tracker disconnected")
    
    async def log_trade_entry(self, trade_data: Dict) -> bool:
        """
        Log trade entry to database
        
        Args:
            trade_data: {
                'trade_id': str,
                'symbol': str,
                'instrument_type': 'EQUITY' or 'OPTIONS',
                'entry_time': datetime,
                'entry_price': float,
                'quantity': int,
                'side': 'long' or 'short',
                'entry_order_id': str,
                'strategy_name': str,
                'signal_confidence': float,
                'market_bias': str,
                'market_regime': str,
                'capital_at_entry': float,
                'risk_amount': float,
                'reward_amount': float,
                'risk_reward_ratio': float,
                ...
            }
        """
        try:
            cursor = self.connection.cursor()
            
            # Extract underlying symbol for options
            symbol = trade_data['symbol']
            underlying_symbol = None
            option_type = None
            strike_price = None
            expiry_date = None
            
            if trade_data.get('instrument_type') == 'OPTIONS':
                # Parse options symbol: BHARTIARTL25OCT2000CE
                underlying_symbol = self._extract_underlying(symbol)
                option_type = 'CE' if symbol.endswith('CE') else 'PE'
                # Would need to parse strike and expiry from symbol
            
            query = """
                INSERT INTO trades (
                    trade_id, symbol, underlying_symbol, instrument_type, option_type,
                    strike_price, expiry_date, entry_time, entry_price, quantity, side,
                    entry_order_id, risk_amount, reward_amount, risk_reward_ratio,
                    strategy_name, signal_confidence, market_bias, market_regime,
                    capital_at_entry, position_size_pct, daily_pnl_at_entry, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            position_size_pct = (trade_data.get('entry_price', 0) * trade_data.get('quantity', 0)) / trade_data.get('capital_at_entry', 1) if trade_data.get('capital_at_entry', 0) > 0 else 0
            
            cursor.execute(query, (
                trade_data.get('trade_id'),
                symbol,
                underlying_symbol,
                trade_data.get('instrument_type', 'EQUITY'),
                option_type,
                strike_price,
                expiry_date,
                trade_data.get('entry_time', datetime.now()),
                trade_data.get('entry_price'),
                trade_data.get('quantity'),
                trade_data.get('side', 'long'),
                trade_data.get('entry_order_id'),
                trade_data.get('risk_amount', 0),
                trade_data.get('reward_amount', 0),
                trade_data.get('risk_reward_ratio', 0),
                trade_data.get('strategy_name', 'unknown'),
                trade_data.get('signal_confidence', 0),
                trade_data.get('market_bias', 'neutral'),
                trade_data.get('market_regime', 'unknown'),
                trade_data.get('capital_at_entry', 0),
                position_size_pct,
                trade_data.get('daily_pnl_at_entry', 0),
                'open'
            ))
            
            cursor.close()
            self.logger.info(f"✅ Trade entry logged: {trade_data.get('trade_id')} - {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error logging trade entry: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    async def log_trade_exit(self, trade_id: str, exit_data: Dict) -> bool:
        """
        Log trade exit and calculate P&L
        
        Args:
            trade_id: Trade identifier
            exit_data: {
                'exit_time': datetime,
                'exit_price': float,
                'exit_order_id': str,
                'exit_reason': str,  # 'target', 'stop_loss', 'trailing_stop', 'time_based'
                'commission': float,
                'taxes': float,
                'max_adverse_excursion': float,
                'max_favorable_excursion': float
            }
        """
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Get trade entry details
            cursor.execute("SELECT * FROM trades WHERE trade_id = %s", (trade_id,))
            trade = cursor.fetchone()
            
            if not trade:
                self.logger.error(f"❌ Trade not found: {trade_id}")
                return False
            
            # Calculate P&L
            entry_price = float(trade['entry_price'])
            exit_price = float(exit_data.get('exit_price', 0))
            quantity = int(trade['quantity'])
            side = trade['side']
            
            if side == 'long':
                gross_pnl = (exit_price - entry_price) * quantity
            else:  # short
                gross_pnl = (entry_price - exit_price) * quantity
            
            commission = float(exit_data.get('commission', 0))
            taxes = float(exit_data.get('taxes', 0))
            net_pnl = gross_pnl - commission - taxes
            
            pnl_percent = (net_pnl / (entry_price * quantity)) * 100 if (entry_price * quantity) > 0 else 0
            
            # Update trade with exit details
            update_query = """
                UPDATE trades
                SET exit_time = %s,
                    exit_price = %s,
                    exit_order_id = %s,
                    exit_reason = %s,
                    gross_pnl = %s,
                    commission = %s,
                    taxes = %s,
                    net_pnl = %s,
                    pnl_percent = %s,
                    max_adverse_excursion = %s,
                    max_favorable_excursion = %s,
                    status = 'closed'
                WHERE trade_id = %s
            """
            
            cursor.execute(update_query, (
                exit_data.get('exit_time', datetime.now()),
                exit_price,
                exit_data.get('exit_order_id'),
                exit_data.get('exit_reason', 'unknown'),
                gross_pnl,
                commission,
                taxes,
                net_pnl,
                pnl_percent,
                exit_data.get('max_adverse_excursion', 0),
                exit_data.get('max_favorable_excursion', 0),
                trade_id
            ))
            
            cursor.close()
            
            pnl_emoji = "✅" if net_pnl > 0 else "❌"
            self.logger.info(f"{pnl_emoji} Trade exit logged: {trade_id} - P&L: ₹{net_pnl:.2f} ({pnl_percent:.2f}%)")
            
            # Update daily performance
            await self._update_daily_performance()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error logging trade exit: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    async def update_active_position(self, position_data: Dict) -> bool:
        """
        Update real-time active position tracking
        
        Args:
            position_data: {
                'trade_id': str,
                'symbol': str,
                'current_price': float,
                'unrealized_pnl': float,
                'unrealized_pnl_pct': float,
                'max_profit': float,
                'max_loss': float,
                'stop_loss': float,
                'target': float,
                'trailing_stop': float,
                'partial_exit_done': bool,
                ...
            }
        """
        try:
            cursor = self.connection.cursor()
            
            # Upsert active position
            query = """
                INSERT INTO active_positions (
                    trade_id, symbol, entry_time, entry_price, current_price,
                    quantity, side, stop_loss, target, trailing_stop,
                    unrealized_pnl, unrealized_pnl_pct, max_profit, max_loss,
                    partial_exit_done, original_quantity, partial_exit_quantity,
                    partial_exit_pnl, strategy_name, signal_confidence, last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (trade_id) DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    unrealized_pnl_pct = EXCLUDED.unrealized_pnl_pct,
                    max_profit = EXCLUDED.max_profit,
                    max_loss = EXCLUDED.max_loss,
                    stop_loss = EXCLUDED.stop_loss,
                    target = EXCLUDED.target,
                    trailing_stop = EXCLUDED.trailing_stop,
                    partial_exit_done = EXCLUDED.partial_exit_done,
                    partial_exit_quantity = EXCLUDED.partial_exit_quantity,
                    partial_exit_pnl = EXCLUDED.partial_exit_pnl,
                    last_updated = CURRENT_TIMESTAMP
            """
            
            cursor.execute(query, (
                position_data.get('trade_id'),
                position_data.get('symbol'),
                position_data.get('entry_time', datetime.now()),
                position_data.get('entry_price', 0),
                position_data.get('current_price', 0),
                position_data.get('quantity', 0),
                position_data.get('side', 'long'),
                position_data.get('stop_loss', 0),
                position_data.get('target', 0),
                position_data.get('trailing_stop'),
                position_data.get('unrealized_pnl', 0),
                position_data.get('unrealized_pnl_pct', 0),
                position_data.get('max_profit', 0),
                position_data.get('max_loss', 0),
                position_data.get('partial_exit_done', False),
                position_data.get('original_quantity'),
                position_data.get('partial_exit_quantity'),
                position_data.get('partial_exit_pnl'),
                position_data.get('strategy_name', 'unknown'),
                position_data.get('signal_confidence', 0),
                datetime.now()
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating active position: {e}")
            return False
    
    async def remove_active_position(self, trade_id: str) -> bool:
        """Remove position from active tracking when closed"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM active_positions WHERE trade_id = %s", (trade_id,))
            cursor.close()
            return True
        except Exception as e:
            self.logger.error(f"❌ Error removing active position: {e}")
            return False
    
    async def log_system_event(self, event_data: Dict) -> bool:
        """
        Log system events (errors, breaches, etc.)
        
        Args:
            event_data: {
                'event_type': str,  # 'loss_limit_breach', 'connection_error', etc.
                'severity': str,  # 'info', 'warning', 'error', 'critical'
                'component': str,
                'title': str,
                'description': str,
                'affected_symbols': list,
                'capital_at_event': float,
                'daily_pnl_at_event': float,
                'open_positions_count': int
            }
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO system_events (
                    event_time, event_type, severity, component, title, description,
                    affected_symbols, capital_at_event, daily_pnl_at_event, open_positions_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            import json
            affected_symbols_json = json.dumps(event_data.get('affected_symbols', []))
            
            cursor.execute(query, (
                datetime.now(),
                event_data.get('event_type'),
                event_data.get('severity', 'info'),
                event_data.get('component'),
                event_data.get('title'),
                event_data.get('description'),
                affected_symbols_json,
                event_data.get('capital_at_event', 0),
                event_data.get('daily_pnl_at_event', 0),
                event_data.get('open_positions_count', 0)
            ))
            
            cursor.close()
            
            severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(event_data.get('severity'), "📝")
            self.logger.info(f"{severity_emoji} System event logged: {event_data.get('title')}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error logging system event: {e}")
            return False
    
    async def _update_daily_performance(self):
        """Update daily performance summary after each trade closes"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            today = date.today()
            
            # Calculate today's performance from trades
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(CASE WHEN net_pnl = 0 THEN 1 ELSE 0 END) as breakeven_trades,
                    SUM(CASE WHEN instrument_type = 'OPTIONS' THEN 1 ELSE 0 END) as options_trades,
                    SUM(CASE WHEN instrument_type = 'EQUITY' THEN 1 ELSE 0 END) as equity_trades,
                    COALESCE(SUM(CASE WHEN instrument_type = 'OPTIONS' THEN net_pnl ELSE 0 END), 0) as options_pnl,
                    COALESCE(SUM(CASE WHEN instrument_type = 'EQUITY' THEN net_pnl ELSE 0 END), 0) as equity_pnl,
                    COALESCE(SUM(gross_pnl), 0) as gross_pnl,
                    COALESCE(SUM(commission), 0) as total_commission,
                    COALESCE(SUM(taxes), 0) as total_taxes,
                    COALESCE(SUM(net_pnl), 0) as net_pnl,
                    AVG(CASE WHEN net_pnl > 0 THEN net_pnl ELSE NULL END) as avg_win,
                    AVG(CASE WHEN net_pnl < 0 THEN net_pnl ELSE NULL END) as avg_loss,
                    MAX(net_pnl) as largest_win,
                    MIN(net_pnl) as largest_loss
                FROM trades
                WHERE DATE(entry_time) = %s
                AND status = 'closed'
            """, (today,))
            
            stats = cursor.fetchone()
            
            if stats and stats['total_trades'] > 0:
                # Calculate derived metrics
                win_rate = stats['winning_trades'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
                
                total_wins = stats['winning_trades'] * (stats['avg_win'] or 0)
                total_losses = abs(stats['losing_trades'] * (stats['avg_loss'] or 0))
                profit_factor = total_wins / total_losses if total_losses > 0 else 0
                
                # Get starting capital (from first trade or previous day's ending capital)
                cursor.execute("""
                    SELECT capital_at_entry
                    FROM trades
                    WHERE DATE(entry_time) = %s
                    ORDER BY entry_time ASC
                    LIMIT 1
                """, (today,))
                
                first_trade = cursor.fetchone()
                starting_capital = first_trade['capital_at_entry'] if first_trade else 50000
                
                ending_capital = starting_capital + stats['net_pnl']
                pnl_percent = (stats['net_pnl'] / starting_capital) * 100 if starting_capital > 0 else 0
                
                # Upsert daily_performance
                upsert_query = """
                    INSERT INTO daily_performance (
                        trading_date, starting_capital, ending_capital,
                        total_trades, winning_trades, losing_trades, breakeven_trades,
                        options_trades, equity_trades, options_pnl, equity_pnl,
                        gross_pnl, total_commission, total_taxes, net_pnl, pnl_percent,
                        win_rate, avg_win, avg_loss, largest_win, largest_loss, profit_factor
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (trading_date) DO UPDATE SET
                        ending_capital = EXCLUDED.ending_capital,
                        total_trades = EXCLUDED.total_trades,
                        winning_trades = EXCLUDED.winning_trades,
                        losing_trades = EXCLUDED.losing_trades,
                        breakeven_trades = EXCLUDED.breakeven_trades,
                        options_trades = EXCLUDED.options_trades,
                        equity_trades = EXCLUDED.equity_trades,
                        options_pnl = EXCLUDED.options_pnl,
                        equity_pnl = EXCLUDED.equity_pnl,
                        gross_pnl = EXCLUDED.gross_pnl,
                        total_commission = EXCLUDED.total_commission,
                        total_taxes = EXCLUDED.total_taxes,
                        net_pnl = EXCLUDED.net_pnl,
                        pnl_percent = EXCLUDED.pnl_percent,
                        win_rate = EXCLUDED.win_rate,
                        avg_win = EXCLUDED.avg_win,
                        avg_loss = EXCLUDED.avg_loss,
                        largest_win = EXCLUDED.largest_win,
                        largest_loss = EXCLUDED.largest_loss,
                        profit_factor = EXCLUDED.profit_factor,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                cursor.execute(upsert_query, (
                    today,
                    starting_capital,
                    ending_capital,
                    stats['total_trades'],
                    stats['winning_trades'],
                    stats['losing_trades'],
                    stats['breakeven_trades'],
                    stats['options_trades'],
                    stats['equity_trades'],
                    stats['options_pnl'],
                    stats['equity_pnl'],
                    stats['gross_pnl'],
                    stats['total_commission'],
                    stats['total_taxes'],
                    stats['net_pnl'],
                    pnl_percent,
                    win_rate,
                    stats['avg_win'],
                    stats['avg_loss'],
                    stats['largest_win'],
                    stats['largest_loss'],
                    profit_factor
                ))
                
                self.logger.info(f"📊 Daily performance updated: {stats['total_trades']} trades, P&L: ₹{stats['net_pnl']:.2f}")
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error updating daily performance: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _extract_underlying(self, options_symbol: str) -> str:
        """Extract underlying symbol from options symbol"""
        # BHARTIARTL25OCT2000CE → BHARTIARTL
        import re
        match = re.match(r'^([A-Z]+)', options_symbol)
        return match.group(1) if match else options_symbol
    
    async def get_todays_performance(self) -> Dict:
        """Get today's performance summary"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM current_performance")
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else {}
        except Exception as e:
            self.logger.error(f"❌ Error getting today's performance: {e}")
            return {}
    
    async def get_active_positions(self) -> List[Dict]:
        """Get all currently active positions"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM active_positions ORDER BY entry_time DESC")
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"❌ Error getting active positions: {e}")
            return []


# Global instance (initialized by orchestrator)
performance_tracker: Optional[PerformanceTracker] = None


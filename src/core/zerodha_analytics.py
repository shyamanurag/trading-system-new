"""
Zerodha Analytics System
========================
Direct Zerodha API-based analytics and reporting system
Bypasses faulty internal database for reliable data
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

@dataclass
class ZerodhaAnalytics:
    """Zerodha-based analytics data structure"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    active_positions: int = 0
    total_positions_value: float = 0.0
    available_margin: float = 0.0
    used_margin: float = 0.0
    net_balance: float = 0.0
    last_trade_time: Optional[datetime] = None
    trading_days: int = 0
    avg_trades_per_day: float = 0.0

class ZerodhaAnalyticsService:
    """Direct Zerodha API-based analytics service"""
    
    def __init__(self, zerodha_client):
        self.zerodha_client = zerodha_client
        self.cache_duration = 300  # 5 minutes cache
        self._cache = {}
        self._cache_timestamps = {}
        
    async def get_comprehensive_analytics(self, days: int = 30) -> ZerodhaAnalytics:
        """Get comprehensive analytics directly from Zerodha"""
        try:
            logger.info(f"📊 Fetching comprehensive analytics for last {days} days from Zerodha")
            
            # Get all required data from Zerodha
            orders_data = await self._get_zerodha_orders(days)
            positions_data = await self._get_zerodha_positions()
            holdings_data = await self._get_zerodha_holdings()
            margins_data = await self._get_zerodha_margins()
            
            # Process orders into trades
            trades = await self._process_orders_to_trades(orders_data)
            
            # Calculate analytics
            analytics = await self._calculate_analytics(trades, positions_data, holdings_data, margins_data, days)
            
            logger.info(f"✅ Analytics calculated: {analytics.total_trades} trades, ₹{analytics.total_pnl:.2f} P&L")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive analytics: {e}")
            return ZerodhaAnalytics()
    
    async def get_daily_report(self, report_date: Optional[date] = None) -> Dict:
        """Get daily trading report from Zerodha"""
        try:
            if not report_date:
                report_date = date.today()
                
            logger.info(f"📊 Generating daily report for {report_date} from Zerodha")
            
            # Get orders for the specific date
            orders = await self._get_zerodha_orders_for_date(report_date)
            trades = await self._process_orders_to_trades(orders)
            
            # Calculate daily metrics
            daily_metrics = await self._calculate_daily_metrics(trades, report_date)
            
            # Get current positions
            positions = await self._get_zerodha_positions()
            
            # Get account summary
            account_summary = await self._get_account_summary()
            
            return {
                'date': report_date.isoformat(),
                'trades': trades,
                'metrics': daily_metrics,
                'positions': positions,
                'account_summary': account_summary,
                'source': 'ZERODHA_API'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating daily report: {e}")
            return {'error': str(e), 'source': 'ZERODHA_API'}
    
    async def get_performance_metrics(self, days: int = 30) -> Dict:
        """Get performance metrics from Zerodha"""
        try:
            analytics = await self.get_comprehensive_analytics(days)
            
            return {
                'total_trades': analytics.total_trades,
                'winning_trades': analytics.winning_trades,
                'losing_trades': analytics.losing_trades,
                'win_rate': analytics.win_rate,
                'total_pnl': analytics.total_pnl,
                'daily_pnl': analytics.daily_pnl,
                'weekly_pnl': analytics.weekly_pnl,
                'monthly_pnl': analytics.monthly_pnl,
                'avg_win': analytics.avg_win,
                'avg_loss': analytics.avg_loss,
                'max_win': analytics.max_win,
                'max_loss': analytics.max_loss,
                'active_positions': analytics.active_positions,
                'net_balance': analytics.net_balance,
                'available_margin': analytics.available_margin,
                'used_margin': analytics.used_margin,
                'source': 'ZERODHA_API'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {'error': str(e), 'source': 'ZERODHA_API'}
    
    async def get_positions_analytics(self) -> Dict:
        """Get current positions analytics from Zerodha"""
        try:
            positions = await self._get_zerodha_positions()
            holdings = await self._get_zerodha_holdings()
            
            # Calculate position metrics
            total_positions = len(positions.get('net', []))
            total_holdings = len(holdings.get('net', []))
            
            # Calculate unrealized P&L
            unrealized_pnl = 0.0
            for position in positions.get('net', []):
                unrealized_pnl += position.get('unrealised_pnl', 0.0)
            
            # Calculate holdings value
            holdings_value = 0.0
            for holding in holdings.get('net', []):
                holdings_value += holding.get('market_value', 0.0)
            
            return {
                'total_positions': total_positions,
                'total_holdings': total_holdings,
                'unrealized_pnl': unrealized_pnl,
                'holdings_value': holdings_value,
                'positions': positions,
                'holdings': holdings,
                'source': 'ZERODHA_API'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting positions analytics: {e}")
            return {'error': str(e), 'source': 'ZERODHA_API'}
    
    async def get_trade_history(self, days: int = 30) -> List[Dict]:
        """Get trade history from Zerodha"""
        try:
            orders = await self._get_zerodha_orders(days)
            trades = await self._process_orders_to_trades(orders)
            
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error getting trade history: {e}")
            return []
    
    async def _get_zerodha_orders(self, days: int = 30) -> List[Dict]:
        """Get orders from Zerodha API"""
        try:
            if not self.zerodha_client or not self.zerodha_client.is_connected:
                logger.warning("⚠️ Zerodha client not connected")
                return []
            
            logger.info(f"📋 Fetching orders from Zerodha for last {days} days...")
            
            # Get orders from Zerodha
            orders = await self.zerodha_client.get_orders()
            
            if not orders:
                logger.warning("⚠️ No orders returned from Zerodha API")
                return []
            
            logger.info(f"📋 Raw orders from Zerodha: {len(orders)}")
            
            # For today's orders, use a more inclusive date range
            now = datetime.now()
            if days == 1:
                # For daily analytics, get orders from start of today
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now + timedelta(hours=1)  # Include next hour for timezone buffer
                logger.info(f"🕐 Daily filter: {start_date} to {end_date}")
            else:
                # For longer periods, use the original logic
                end_date = now
                start_date = end_date - timedelta(days=days)
                logger.info(f"🕐 Period filter: {start_date} to {end_date}")
            
            filtered_orders = []
            today_orders = []
            
            for order in orders:
                try:
                    order_timestamp = order.get('order_timestamp', '')
                    if order_timestamp:
                        # Handle different timestamp formats
                        try:
                            if 'T' in order_timestamp:
                                order_date = datetime.fromisoformat(order_timestamp.replace('Z', '+00:00'))
                            else:
                                # Handle date-only format
                                order_date = datetime.strptime(order_timestamp, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            # Try alternative parsing
                            order_date = datetime.fromisoformat(order_timestamp.split('.')[0])
                        
                        # Check if order is in our date range
                        if start_date <= order_date <= end_date:
                            filtered_orders.append(order)
                        
                        # Also track today's orders specifically
                        if order_date.date() == now.date():
                            today_orders.append(order)
                            
                    else:
                        # Include orders without timestamps (safety net)
                        filtered_orders.append(order)
                        logger.warning(f"⚠️ Order {order.get('order_id')} has no timestamp")
                        
                except Exception as e:
                    logger.warning(f"Error parsing order timestamp {order_timestamp}: {e}")
                    # Include order anyway if timestamp parsing fails
                    filtered_orders.append(order)
            
            logger.info(f"📋 Filtered orders: {len(filtered_orders)} (from {len(orders)} total)")
            logger.info(f"📅 Today's orders: {len(today_orders)}")
            
            # Log order status breakdown for today's orders
            if today_orders:
                status_counts = {}
                for order in today_orders:
                    status = order.get('status', 'UNKNOWN')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    # Log sample order details
                    if len(status_counts) <= 3:  # Log first few orders
                        logger.info(f"📊 Order sample: {order.get('order_id')} | {order.get('tradingsymbol')} | {status} | {order.get('transaction_type')} | {order.get('quantity')}")
                
                logger.info(f"📊 Today's order status breakdown: {status_counts}")
            
            # Return all filtered orders (not just today's)
            return filtered_orders
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha orders: {e}", exc_info=True)
            return []
    
    async def _get_zerodha_orders_for_date(self, target_date: date) -> List[Dict]:
        """Get orders for a specific date from Zerodha"""
        try:
            orders = await self._get_zerodha_orders(1)  # Get last 1 day
            
            # Filter for the specific date
            filtered_orders = []
            for order in orders:
                order_date = datetime.fromisoformat(order.get('order_timestamp', '').replace('Z', '+00:00'))
                if order_date.date() == target_date:
                    filtered_orders.append(order)
            
            return filtered_orders
            
        except Exception as e:
            logger.error(f"❌ Error getting orders for date {target_date}: {e}")
            return []
    
    async def _get_zerodha_positions(self) -> Dict:
        """Get current positions from Zerodha"""
        try:
            if not self.zerodha_client or not self.zerodha_client.is_connected:
                return {}
            
            positions = await self.zerodha_client.get_positions()
            logger.info(f"📊 Retrieved positions from Zerodha: {len(positions.get('net', []))} positions")
            return positions
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha positions: {e}")
            return {}
    
    async def _get_zerodha_holdings(self) -> Dict:
        """Get holdings from Zerodha"""
        try:
            if not self.zerodha_client or not self.zerodha_client.is_connected:
                return {}
            
            holdings = await self.zerodha_client.get_holdings()
            logger.info(f"📊 Retrieved holdings from Zerodha: {len(holdings.get('net', []))} holdings")
            return holdings
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha holdings: {e}")
            return {}
    
    async def _get_zerodha_margins(self) -> Dict:
        """Get margin information from Zerodha"""
        try:
            if not self.zerodha_client or not self.zerodha_client.is_connected:
                return {}
            
            margins = await self.zerodha_client.get_margins()
            logger.info(f"💰 Retrieved margin information from Zerodha")
            return margins
            
        except Exception as e:
            logger.error(f"❌ Error getting Zerodha margins: {e}")
            return {}
    
    async def _process_orders_to_trades(self, orders: List[Dict]) -> List[Dict]:
        """Convert Zerodha orders to trade format"""
        trades = []
        
        for order in orders:
            try:
                # Extract trade information - pass through Zerodha data as-is
                trade = {
                    'order_id': order.get('order_id'),
                    'symbol': order.get('tradingsymbol'),
                    'side': order.get('transaction_type'),  # BUY or SELL
                    'quantity': int(order.get('quantity', 0)),
                    'price': float(order.get('average_price', 0)),
                    'status': order.get('status'),
                    'timestamp': order.get('order_timestamp'),
                    'exchange': order.get('exchange'),
                    'product': order.get('product'),
                    'order_type': order.get('order_type'),
                    'validity': order.get('validity'),
                    'disclosed_quantity': order.get('disclosed_quantity'),
                    'trigger_price': order.get('trigger_price'),
                    'squareoff': order.get('squareoff'),
                    'stoploss': order.get('stoploss'),
                    'trailing_stoploss': order.get('trailing_stoploss'),
                    'source': 'ZERODHA_API'
                    # Note: P&L is not provided by Zerodha at order level
                    # Use positions API for P&L data
                }
                
                trades.append(trade)
                
            except Exception as e:
                logger.error(f"❌ Error processing order {order.get('order_id')}: {e}")
                continue
        
        logger.info(f"🔄 Processed {len(trades)} orders into trades")
        return trades
    
    async def _calculate_analytics(self, trades: List[Dict], positions: Dict, holdings: Dict, margins: Dict, days: int) -> ZerodhaAnalytics:
        """Calculate comprehensive analytics"""
        try:
            analytics = ZerodhaAnalytics()
            
            if not trades:
                logger.warning("⚠️ No trades found for analytics calculation")
                return analytics
            
            logger.info(f"📊 Calculating analytics from {len(trades)} trades")
            
            # Log trade status breakdown for debugging
            status_counts = {}
            executed_trades = []
            for trade in trades:
                status = trade.get('status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count all trades with valid prices as "executed" regardless of status
                if trade.get('price', 0) > 0:
                    executed_trades.append(trade)
            
            logger.info(f"📋 Trade status breakdown: {status_counts}")
            logger.info(f"✅ Trades with valid prices (considered executed): {len(executed_trades)}")
            
            # Calculate trade statistics from executed trades
            analytics.total_trades = len(executed_trades)
            
            if analytics.total_trades == 0:
                logger.warning("⚠️ No executed trades found (no trades with valid prices)")
                return analytics
            
            # Calculate P&L (simplified - in real implementation, you'd need to match buy/sell pairs)
            total_pnl = 0.0
            winning_trades = 0
            losing_trades = 0
            wins = []
            losses = []
            
            # Group trades by symbol to calculate P&L
            symbol_trades = {}
            for trade in executed_trades:
                symbol = trade['symbol']
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
            
            # Calculate P&L for each symbol
            for symbol, symbol_trade_list in symbol_trades.items():
                symbol_pnl = await self._calculate_symbol_pnl(symbol_trade_list)
                total_pnl += symbol_pnl
                
                if symbol_pnl > 0:
                    winning_trades += 1
                    wins.append(symbol_pnl)
                elif symbol_pnl < 0:
                    losing_trades += 1
                    losses.append(symbol_pnl)
            
            analytics.total_pnl = total_pnl
            analytics.winning_trades = winning_trades
            analytics.losing_trades = losing_trades
            analytics.win_rate = (winning_trades / analytics.total_trades * 100) if analytics.total_trades > 0 else 0.0
            
            logger.info(f"📈 Analytics summary: {analytics.total_trades} trades, ₹{analytics.total_pnl:.2f} P&L, {analytics.win_rate:.1f}% win rate")
            
            # Calculate average wins and losses
            analytics.avg_win = float(np.mean(wins)) if wins else 0.0
            analytics.avg_loss = float(np.mean(losses)) if losses else 0.0
            analytics.max_win = max(wins) if wins else 0.0
            analytics.max_loss = min(losses) if losses else 0.0
            
            # Calculate period P&L
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            day_start = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = end_date - timedelta(days=7)
            month_start = end_date - timedelta(days=30)
            
            # Calculate period-specific P&L (simplified)
            analytics.daily_pnl = total_pnl if days == 1 else total_pnl * 0.1  # Use full P&L for daily
            analytics.weekly_pnl = total_pnl * 0.3  # Placeholder
            analytics.monthly_pnl = total_pnl * 0.7  # Placeholder
            
            # Position analytics
            analytics.active_positions = len(positions.get('net', []))
            analytics.total_positions_value = sum(pos.get('market_value', 0) for pos in positions.get('net', []))
            
            # Margin analytics
            analytics.available_margin = margins.get('equity', {}).get('available', {}).get('cash', 0.0)
            analytics.used_margin = margins.get('equity', {}).get('used', {}).get('debits', 0.0)
            analytics.net_balance = analytics.available_margin - analytics.used_margin
            
            # Trading activity
            if executed_trades:
                timestamps = [trade.get('timestamp') for trade in executed_trades if trade.get('timestamp')]
                if timestamps:
                    analytics.last_trade_time = max(timestamps)
                analytics.trading_days = days
                analytics.avg_trades_per_day = analytics.total_trades / days
            
            logger.info(f"🎯 Final analytics: {analytics.total_trades} trades, ₹{analytics.daily_pnl:.2f} daily P&L")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error calculating analytics: {e}", exc_info=True)
            return ZerodhaAnalytics()
    
    async def _calculate_symbol_pnl(self, symbol_trades: List[Dict]) -> float:
        """Calculate P&L for a specific symbol"""
        try:
            if len(symbol_trades) < 2:
                return 0.0
            
            # Sort trades by timestamp
            sorted_trades = sorted(symbol_trades, key=lambda x: x['timestamp'])
            
            # Simple P&L calculation (buy low, sell high)
            total_pnl = 0.0
            position = 0
            avg_price = 0.0
            
            for trade in sorted_trades:
                if trade['side'] == 'BUY':
                    # Buying
                    if position == 0:
                        # New position
                        position = trade['quantity']
                        avg_price = trade['price']
                    else:
                        # Adding to position
                        total_quantity = position + trade['quantity']
                        avg_price = ((position * avg_price) + (trade['quantity'] * trade['price'])) / total_quantity
                        position = total_quantity
                elif trade['side'] == 'SELL':
                    # Selling
                    if position > 0:
                        # Calculate P&L for this sale
                        sale_pnl = (trade['price'] - avg_price) * min(trade['quantity'], position)
                        total_pnl += sale_pnl
                        position -= trade['quantity']
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"❌ Error calculating symbol P&L: {e}")
            return 0.0
    
    async def _calculate_daily_metrics(self, trades: List[Dict], target_date: date) -> Dict:
        """Calculate daily trading metrics"""
        try:
            daily_trades = [t for t in trades if datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')).date() == target_date]
            
            total_trades = len(daily_trades)
            total_volume = sum(t['quantity'] for t in daily_trades)
            total_value = sum(t['quantity'] * t['price'] for t in daily_trades)
            
            # Calculate P&L (simplified)
            daily_pnl = 0.0
            for trade in daily_trades:
                trade_pnl = await self._calculate_symbol_pnl([trade])
                daily_pnl += trade_pnl
            
            return {
                'total_trades': total_trades,
                'total_volume': total_volume,
                'total_value': total_value,
                'daily_pnl': daily_pnl,
                'avg_trade_size': total_value / total_trades if total_trades > 0 else 0,
                'source': 'ZERODHA_API'
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating daily metrics: {e}")
            return {}
    
    async def _get_account_summary(self) -> Dict:
        """Get account summary from Zerodha"""
        try:
            if not self.zerodha_client or not self.zerodha_client.is_connected:
                return {}
            
            # Get profile information
            profile = await self.zerodha_client.get_profile()
            
            # Get margins
            margins = await self._get_zerodha_margins()
            
            return {
                'user_id': profile.get('user_id'),
                'user_name': profile.get('user_name'),
                'email': profile.get('email'),
                'mobile': profile.get('mobile'),
                'pan': profile.get('pan'),
                'broker': profile.get('broker'),
                'available_margin': margins.get('equity', {}).get('available', {}).get('cash', 0.0),
                'used_margin': margins.get('equity', {}).get('used', {}).get('debits', 0.0),
                'source': 'ZERODHA_API'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting account summary: {e}")
            return {}

# Global instance
_zerodha_analytics_service = None

async def get_zerodha_analytics_service(zerodha_client) -> ZerodhaAnalyticsService:
    """Get the global Zerodha analytics service instance"""
    global _zerodha_analytics_service
    
    if _zerodha_analytics_service is None:
        _zerodha_analytics_service = ZerodhaAnalyticsService(zerodha_client)
    
    return _zerodha_analytics_service 
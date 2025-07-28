"""
Zerodha Analytics API
=====================
API endpoints for Zerodha-based analytics and reporting
Bypasses faulty internal database for reliable data
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from src.core.zerodha_analytics import get_zerodha_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/zerodha-analytics", tags=["zerodha-analytics"])

# Pydantic models for response validation
class PerformanceMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float
    active_positions: int
    net_balance: float
    available_margin: float
    used_margin: float
    source: str

class PositionsAnalytics(BaseModel):
    total_positions: int
    total_holdings: int
    unrealized_pnl: float
    holdings_value: float
    positions: Dict
    holdings: Dict
    source: str

class DailyReport(BaseModel):
    date: str
    trades: List[Dict]
    metrics: Dict
    positions: Dict
    account_summary: Dict
    source: str

class TradeHistory(BaseModel):
    trades: List[Dict]
    source: str

async def get_zerodha_client():
    """Get Zerodha client from orchestrator"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            raise HTTPException(status_code=503, detail="Zerodha client not available")
        
        return orchestrator.zerodha_client
        
    except Exception as e:
        logger.error(f"❌ Error getting Zerodha client: {e}")
        raise HTTPException(status_code=503, detail="Zerodha client not available")

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    days: int = Query(30, description="Number of days to analyze"),
    zerodha_client = Depends(get_zerodha_client)
):
    """Get performance metrics directly from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        metrics = await analytics_service.get_performance_metrics(days)
        
        if 'error' in metrics:
            raise HTTPException(status_code=500, detail=metrics['error'])
        
        return PerformanceMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"❌ Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=PositionsAnalytics)
async def get_positions_analytics(
    zerodha_client = Depends(get_zerodha_client)
):
    """Get current positions analytics from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        analytics = await analytics_service.get_positions_analytics()
        
        if 'error' in analytics:
            raise HTTPException(status_code=500, detail=analytics['error'])
        
        return PositionsAnalytics(**analytics)
        
    except Exception as e:
        logger.error(f"❌ Error getting positions analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-report", response_model=DailyReport)
async def get_daily_report(
    report_date: str = Query(None, description="Report date (YYYY-MM-DD)"),
    zerodha_client = Depends(get_zerodha_client)
):
    """Get daily trading report from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        
        # Parse date if provided
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        
        report = await analytics_service.get_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return DailyReport(**report)
        
    except Exception as e:
        logger.error(f"❌ Error getting daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade-history", response_model=TradeHistory)
async def get_trade_history(
    days: int = Query(30, description="Number of days to fetch"),
    zerodha_client = Depends(get_zerodha_client)
):
    """Get trade history from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        trades = await analytics_service.get_trade_history(days)
        
        return TradeHistory(trades=trades, source="ZERODHA_API")
        
    except Exception as e:
        logger.error(f"❌ Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comprehensive-analytics")
async def get_comprehensive_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    zerodha_client = Depends(get_zerodha_client)
):
    """Get comprehensive analytics from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        analytics = await analytics_service.get_comprehensive_analytics(days)
        
        return {
            'success': True,
            'data': {
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
                'total_positions_value': analytics.total_positions_value,
                'available_margin': analytics.available_margin,
                'used_margin': analytics.used_margin,
                'net_balance': analytics.net_balance,
                'last_trade_time': analytics.last_trade_time.isoformat() if analytics.last_trade_time else None,
                'trading_days': analytics.trading_days,
                'avg_trades_per_day': analytics.avg_trades_per_day
            },
            'source': 'ZERODHA_API',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting comprehensive analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account-summary")
async def get_account_summary(
    zerodha_client = Depends(get_zerodha_client)
):
    """Get account summary from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        summary = await analytics_service._get_account_summary()
        
        if not summary:
            raise HTTPException(status_code=503, detail="Unable to fetch account summary from Zerodha")
        
        return {
            'success': True,
            'data': summary,
            'source': 'ZERODHA_API',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting account summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/real-time-status")
async def get_real_time_status(
    zerodha_client = Depends(get_zerodha_client)
):
    """Get real-time trading status from Zerodha"""
    try:
        analytics_service = await get_zerodha_analytics_service(zerodha_client)
        
        # Get current positions
        positions = await analytics_service._get_zerodha_positions()
        
        # Get margins
        margins = await analytics_service._get_zerodha_margins()
        
        # Get account summary
        account = await analytics_service._get_account_summary()
        
        return {
            'success': True,
            'data': {
                'zerodha_connected': zerodha_client.is_connected if zerodha_client else False,
                'active_positions': len(positions.get('net', [])),
                'available_margin': margins.get('equity', {}).get('available', {}).get('cash', 0.0),
                'used_margin': margins.get('equity', {}).get('used', {}).get('debits', 0.0),
                'net_balance': account.get('available_margin', 0.0) - account.get('used_margin', 0.0),
                'user_id': account.get('user_id'),
                'user_name': account.get('user_name'),
                'last_updated': datetime.now().isoformat()
            },
            'source': 'ZERODHA_API',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting real-time status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/sync-positions")
async def sync_positions_with_zerodha(
    zerodha_client = Depends(get_zerodha_client)
):
    """Force sync internal position tracker with Zerodha positions"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.trade_engine:
            raise HTTPException(status_code=503, detail="Trade engine not available")
        
        # Force sync positions from Zerodha
        logger.info("🔄 Force syncing positions with Zerodha...")
        actual_positions = await orchestrator.trade_engine.sync_actual_zerodha_positions()
        
        # Get position counts
        zerodha_count = len(actual_positions)
        internal_count = 0
        if orchestrator.trade_engine.position_tracker:
            internal_count = await orchestrator.trade_engine.position_tracker.get_position_count()
        
        return {
            'success': True,
            'data': {
                'zerodha_positions': zerodha_count,
                'internal_positions': internal_count,
                'synced': zerodha_count == internal_count,
                'actual_positions': actual_positions
            },
            'message': f"Synced {zerodha_count} positions from Zerodha",
            'source': 'ZERODHA_API',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing positions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/debug-orders")
async def debug_zerodha_orders(
    zerodha_client = Depends(get_zerodha_client)
):
    """Debug endpoint to see raw Zerodha orders data"""
    try:
        logger.info("🔍 Debugging Zerodha orders...")
        
        # Get raw orders from Zerodha
        orders = await zerodha_client.get_orders()
        
        logger.info(f"📋 Raw orders from Zerodha: {len(orders) if orders else 0}")
        
        # Process and categorize orders
        order_stats = {
            'total_orders': len(orders) if orders else 0,
            'by_status': {},
            'today_orders': 0,
            'recent_orders': [],
            'sample_orders': orders[:5] if orders else []  # First 5 orders for inspection
        }
        
        if orders:
            # Count by status
            for order in orders:
                status = order.get('status', 'UNKNOWN')
                order_stats['by_status'][status] = order_stats['by_status'].get(status, 0) + 1
                
                # Check if order is from today
                try:
                    order_timestamp = order.get('order_timestamp', '')
                    if order_timestamp:
                        order_date = datetime.fromisoformat(order_timestamp.replace('Z', '+00:00'))
                        if order_date.date() == datetime.now().date():
                            order_stats['today_orders'] += 1
                            order_stats['recent_orders'].append({
                                'order_id': order.get('order_id'),
                                'symbol': order.get('tradingsymbol'),
                                'status': order.get('status'),
                                'side': order.get('transaction_type'),
                                'quantity': order.get('quantity'),
                                'price': order.get('price'),
                                'timestamp': order_timestamp
                            })
                except Exception as e:
                    logger.warning(f"Error parsing order timestamp: {e}")
        
        return {
            'success': True,
            'data': order_stats,
            'zerodha_connected': zerodha_client.is_connected if zerodha_client else False,
            'message': f"Found {order_stats['total_orders']} total orders, {order_stats['today_orders']} today",
            'source': 'ZERODHA_API_DEBUG',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error debugging Zerodha orders: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
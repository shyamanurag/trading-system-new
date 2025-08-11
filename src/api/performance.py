from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.responses import BaseResponse, TradeResponse, PositionResponse
from ..core.orchestrator import TradingOrchestrator
from ..core.dependencies import get_orchestrator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/daily-pnl", response_model=BaseResponse)
async def get_daily_pnl(
    date: Optional[str] = None,
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get daily PnL metrics"""
    try:
        if not date:
            date = datetime.utcnow()
        
        # Get real daily performance from trade manager
        try:
            if hasattr(orchestrator, 'trade_manager') and orchestrator.trade_manager:
                # Get today's trades for metrics
                today = datetime.utcnow().date()
                daily_trades = await orchestrator.trade_manager.get_daily_trades(today)
                total_pnl = sum(trade.get('realized_pnl', 0) for trade in daily_trades)
                metrics = {
                    "daily_pnl": total_pnl,
                    "total_trades": len(daily_trades),
                    "win_rate": 0.0  # Calculate later if needed
                }
            else:
                metrics = {"daily_pnl": 0.0, "total_trades": 0, "win_rate": 0.0}
        except Exception as e:
            logger.warning(f"Could not get daily performance: {e}")
            metrics = {"daily_pnl": 0.0, "total_trades": 0, "win_rate": 0.0}
        return BaseResponse(
            success=True,
            message="Daily PnL retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting daily PnL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-pnl-history")
async def get_daily_pnl_history(
    days: int = 30,
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get historical daily PnL data for charts"""
    try:
        logger.info(f"📊 Fetching {days} days of historical P&L data")
        
        # Import here to avoid circular imports  
        from src.core.database import get_session
        
        session = get_session()
        
        query = """
SELECT DATE(created_at) as date,
       SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as profit,
       SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as loss,
       SUM(pnl) as total_pnl,
       COUNT(*) as trades
FROM paper_trades 
WHERE created_at >= NOW() - INTERVAL %s DAY
AND status = 'executed'
GROUP BY DATE(created_at)
ORDER BY date DESC
"""
            
            result = await session.execute(query, days)
            
            daily_history = []
            for row in result:
                daily_history.append({
                    'date': row['date'].isoformat() if row['date'] else None,
                    'total_pnl': float(row['total_pnl']) if row['total_pnl'] else 0,
                    'profit': float(row['profit']) if row['profit'] else 0,
                    'loss': float(row['loss']) if row['loss'] else 0,
                    'trades': int(row['trades']) if row['trades'] else 0
                })
            
            logger.info(f"✅ Retrieved {len(daily_history)} days of P&L history")
            
            return {
                "success": True,
                "daily_history": daily_history,
                "total_days": len(daily_history),
                "timestamp": datetime.now().isoformat(),
                "source": "real_database"
            }
            
    except Exception as e:
        logger.error(f"Error getting daily P&L history: {e}")
        return {
            "success": False,
            "daily_history": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get current positions"""
    try:
        positions = await orchestrator.position_manager.get_all_positions()
        return [
            PositionResponse(
                success=True,
                message="Position retrieved successfully",
                position_id=pos.position_id,
                symbol=pos.symbol,
                quantity=pos.quantity,
                average_price=pos.average_price,
                current_price=pos.current_price,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=pos.realized_pnl,
                status=pos.status,
                metadata=pos.metadata
            )
            for pos in positions
        ]
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    start_date: datetime = None,
    end_date: datetime = None,
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get trade history"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        trades = await orchestrator.trade_manager.get_trades(start_date, end_date)
        return [
            TradeResponse(
                success=True,
                message="Trade retrieved successfully",
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                quantity=trade.quantity,
                price=trade.price,
                side=trade.side,
                status=trade.status,
                execution_time=trade.execution_time,
                fees=trade.fees,
                metadata=trade.metadata
            )
            for trade in trades
        ]
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics():
    """Get comprehensive performance metrics from Zerodha"""
    try:
        # Get Zerodha client
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            return {
                "success": False,
                "message": "Zerodha client not available",
                "data": {}
            }
        
        # Use Zerodha analytics service
        from src.core.zerodha_analytics import get_zerodha_analytics_service
        analytics_service = await get_zerodha_analytics_service(orchestrator.zerodha_client)
        
        # Get comprehensive analytics
        analytics = await analytics_service.get_comprehensive_analytics(30)  # Last 30 days
        
        metrics = {
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
        
        return {
            "success": True,
            "message": "Performance metrics retrieved successfully",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk", response_model=Dict[str, Any])
async def get_risk_metrics(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get risk metrics"""
    try:
        risk_metrics = await orchestrator.risk_manager.get_risk_metrics()
        return {
            "success": True,
            "message": "Risk metrics retrieved successfully",
            "data": risk_metrics
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
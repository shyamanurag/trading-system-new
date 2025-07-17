"""
Positions API - Real position tracking and P&L
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.config.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["positions"])

@router.get("/positions")
async def get_current_positions(db: Session = Depends(get_db)):
    """Get current trading positions with real-time P&L"""
    try:
        # Get current positions by aggregating today's trades
        positions_query = text("""
            SELECT 
                symbol,
                SUM(CASE WHEN trade_type = 'buy' THEN quantity ELSE -quantity END) as net_quantity,
                AVG(CASE WHEN trade_type = 'buy' THEN price ELSE NULL END) as avg_buy_price,
                AVG(CASE WHEN trade_type = 'sell' THEN price ELSE NULL END) as avg_sell_price,
                SUM(pnl) as total_pnl,
                AVG(pnl_percent) as avg_pnl_percent,
                MAX(executed_at) as last_trade_time,
                STRING_AGG(DISTINCT strategy, ', ') as strategies,
                COUNT(*) as trade_count
            FROM trades 
            WHERE DATE(executed_at) = CURRENT_DATE
            AND status = 'EXECUTED'
            GROUP BY symbol
            HAVING SUM(CASE WHEN trade_type = 'buy' THEN quantity ELSE -quantity END) != 0
            ORDER BY MAX(executed_at) DESC
        """)
        
        result = db.execute(positions_query)
        positions = result.fetchall()
        
        position_list = []
        for pos in positions:
            # Determine position side
            side = "LONG" if pos.net_quantity > 0 else "SHORT"
            entry_price = pos.avg_buy_price if pos.avg_buy_price else pos.avg_sell_price
            
            position_list.append({
                "symbol": pos.symbol,
                "quantity": abs(pos.net_quantity),
                "side": side,
                "entry_price": float(entry_price) if entry_price else 0,
                "current_pnl": float(pos.total_pnl) if pos.total_pnl else 0,
                "pnl_percent": float(pos.avg_pnl_percent) if pos.avg_pnl_percent else 0,
                "strategies": pos.strategies,
                "trade_count": pos.trade_count,
                "last_updated": pos.last_trade_time.isoformat() if pos.last_trade_time else None
            })
        
        # Calculate summary
        total_pnl = sum(pos["current_pnl"] for pos in position_list)
        
        return {
            "success": True,
            "data": {
                "positions": position_list,
                "summary": {
                    "total_positions": len(position_list),
                    "total_pnl": round(total_pnl, 2),
                    "long_positions": len([p for p in position_list if p["side"] == "LONG"]),
                    "short_positions": len([p for p in position_list if p["side"] == "SHORT"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "positions": [],
                "summary": {
                    "total_positions": 0,
                    "total_pnl": 0,
                    "long_positions": 0,
                    "short_positions": 0
                }
            }
        }

@router.get("/positions/summary")
async def get_positions_summary(db: Session = Depends(get_db)):
    """Get positions summary with daily P&L"""
    try:
        summary_query = text("""
            SELECT 
                COUNT(DISTINCT symbol) as active_positions,
                SUM(pnl) as daily_pnl,
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(pnl) as avg_pnl_per_trade
            FROM trades 
            WHERE DATE(executed_at) = CURRENT_DATE
            AND status = 'EXECUTED'
        """)
        
        result = db.execute(summary_query)
        summary = result.fetchone()
        
        if summary:
            win_rate = (summary.winning_trades / summary.total_trades * 100) if summary.total_trades > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "active_positions": summary.active_positions or 0,
                    "daily_pnl": float(summary.daily_pnl) if summary.daily_pnl else 0,
                    "total_trades": summary.total_trades or 0,
                    "winning_trades": summary.winning_trades or 0,
                    "win_rate": round(win_rate, 2),
                    "avg_pnl_per_trade": float(summary.avg_pnl_per_trade) if summary.avg_pnl_per_trade else 0
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "active_positions": 0,
                    "daily_pnl": 0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "win_rate": 0,
                    "avg_pnl_per_trade": 0
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting positions summary: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "active_positions": 0,
                "daily_pnl": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "win_rate": 0,
                "avg_pnl_per_trade": 0
            }
        } 
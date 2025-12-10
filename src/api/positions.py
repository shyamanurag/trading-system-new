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
    """Get current trading positions directly from Zerodha"""
    try:
        # 🎯 CRITICAL FIX: Get positions directly from Zerodha
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        # ENHANCED DEBUGGING: Check each step of connection
        logger.info(f"📊 Orchestrator available: {orchestrator is not None}")
        if orchestrator:
            logger.info(f"📊 Zerodha client available: {orchestrator.zerodha_client is not None}")
            if orchestrator.zerodha_client:
                logger.info(f"📊 Zerodha client type: {type(orchestrator.zerodha_client)}")
        
        if not orchestrator or not orchestrator.zerodha_client:
            error_msg = f"Zerodha client not available - orchestrator: {orchestrator is not None}, client: {orchestrator.zerodha_client is not None if orchestrator else False}"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=503, detail=error_msg)
        
        # Get real positions data from Zerodha API
        logger.info("📊 Attempting to fetch real positions from Zerodha API...")
        try:
            positions_data = await orchestrator.zerodha_client.get_positions()
            logger.info(f"📊 Zerodha API response type: {type(positions_data)}")
            logger.info(f"📊 Zerodha API response data: {positions_data}")
        except Exception as zerodha_error:
            logger.error(f"❌ Zerodha API call failed: {zerodha_error}")
            raise HTTPException(status_code=500, detail=f"Zerodha API error: {str(zerodha_error)}")
        
        if not positions_data:
            logger.warning("⚠️ No positions data returned from Zerodha")
            return {
                "success": True,
                "data": {
                    "positions": [],
                    "summary": {
                        "total_positions": 0,
                        "total_pnl": 0.0,
                        "long_positions": 0,
                        "short_positions": 0
                    }
                },
                "source": "ZERODHA_API"
            }
        
        # Process Zerodha net positions
        position_list = []
        net_positions = positions_data.get('net', [])
        
        logger.info(f"📊 Processing {len(net_positions)} net positions from Zerodha")
        
        for position in net_positions:
            try:
                symbol = position.get('tradingsymbol', 'UNKNOWN')
                quantity = position.get('quantity', 0)
                
                # Skip positions with zero quantity
                if quantity == 0:
                    continue
                
                average_price = position.get('average_price', 0)
                last_price = position.get('last_price', average_price)
                
                # 🚨 CRITICAL FIX: Zerodha uses different field names for P&L
                # Try multiple field names: 'pnl', 'm2m', 'unrealised', 'unrealised_pnl'
                unrealized_pnl = (
                    position.get('pnl', 0) or 
                    position.get('m2m', 0) or 
                    position.get('unrealised', 0) or 
                    position.get('unrealised_pnl', 0) or
                    0
                )
                
                # If Zerodha P&L is still 0, calculate manually
                if unrealized_pnl == 0 and average_price > 0 and last_price > 0:
                    unrealized_pnl = (last_price - average_price) * quantity
                    logger.info(f"📊 {symbol}: Calculated P&L manually = ₹{unrealized_pnl:.2f}")
                
                # CRITICAL FIX: For options, use premium-based P&L calculation
                # Check if this is an options symbol (contains CE or PE)
                is_options = 'CE' in symbol or 'PE' in symbol
                
                if is_options:
                    # For OPTIONS: P&L should be based on PREMIUM, not notional value
                    # Zerodha API sometimes gives notional-based P&L for options
                    # Recalculate using premium-based logic
                    position_value = average_price * abs(quantity)  # Premium-based position value
                    manual_pnl = (last_price - average_price) * abs(quantity)  # Premium-based P&L
                    
                    # Use manual calculation for options, Zerodha's for stocks
                    final_pnl = manual_pnl
                    logger.info(f"📊 OPTIONS P&L CALCULATION: {symbol}")
                    logger.info(f"   Entry Premium: ₹{average_price:.2f} × {abs(quantity)} = ₹{position_value:.2f}")
                    logger.info(f"   Current Premium: ₹{last_price:.2f} × {abs(quantity)} = ₹{last_price * abs(quantity):.2f}")
                    logger.info(f"   Manual P&L: ₹{manual_pnl:.2f} | Zerodha P&L: ₹{unrealized_pnl:.2f}")
                else:
                    # For STOCKS: Use Zerodha's P&L directly
                    position_value = average_price * abs(quantity)
                    final_pnl = unrealized_pnl
                
                pnl_percent = (final_pnl / position_value) * 100 if position_value > 0 else 0
                
                position_info = {
                    "symbol": symbol,
                    "quantity": abs(quantity),
                    "side": "LONG" if quantity > 0 else "SHORT",
                    "entry_price": round(average_price, 2),
                    "current_price": round(last_price, 2),
                    "current_pnl": round(unrealized_pnl, 2),
                    "pnl_percent": round(pnl_percent, 2),
                    "strategies": "Zerodha Position",
                    
                    # ENHANCED P&L DISPLAY FIX: Add more detailed financial data
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "realized_pnl": 0.0,  # This would need to be calculated from trade history
                    "total_pnl": round(unrealized_pnl, 2),
                    "position_value": round(position_value, 2),
                    "invested_amount": round(average_price * abs(quantity), 2),
                    "current_value": round(last_price * abs(quantity), 2),
                    
                    # Market data
                    "last_updated": position.get('last_price_timestamp', ''),
                    "exchange": position.get('exchange', 'NSE'),
                    "product": position.get('product', 'MIS'),
                    
                    # Risk metrics
                    "day_change": round(last_price - average_price, 2),
                    "day_change_percent": round(((last_price - average_price) / average_price) * 100, 2) if average_price > 0 else 0,
                    
                    # Status flags
                    "is_active": True,
                    "status": "OPEN",
                    "source": "ZERODHA_API"
                }
                
                position_list.append(position_info)
                
                logger.info(f"📊 Position: {symbol} | Qty: {quantity} | P&L: ₹{unrealized_pnl:.2f} ({pnl_percent:.2f}%)")
                
            except Exception as pos_error:
                logger.error(f"Error processing Zerodha position {symbol}: {pos_error}")
                continue
        
        # Calculate summary
        total_pnl = sum(pos["current_pnl"] for pos in position_list)
        long_count = len([p for p in position_list if p["side"] == "LONG"])
        short_count = len([p for p in position_list if p["side"] == "SHORT"])
        
        logger.info(f"📊 POSITIONS SUMMARY: {len(position_list)} positions, ₹{total_pnl:.2f} total P&L")
        
        return {
            "success": True,
            "data": {
                "positions": position_list,
                "summary": {
                    "total_positions": len(position_list),
                    "total_pnl": round(total_pnl, 2),
                    "long_positions": long_count,
                    "short_positions": short_count
                }
            },
            "source": "ZERODHA_API"
        }
            
    except Exception as e:
        logger.error(f"❌ Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

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
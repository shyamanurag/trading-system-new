from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_all_positions():
    """Get all positions - REAL DATA from Zerodha"""
    try:
        # CRITICAL FIX: Actually fetch real positions from Zerodha instead of returning fake empty data
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        # ENHANCED DEBUGGING: Check each step of connection
        logger.info(f"📊 [REAL POSITIONS] Orchestrator available: {orchestrator is not None}")
        if orchestrator:
            logger.info(f"📊 [REAL POSITIONS] Zerodha client available: {orchestrator.zerodha_client is not None}")
            if orchestrator.zerodha_client:
                logger.info(f"📊 [REAL POSITIONS] Zerodha client type: {type(orchestrator.zerodha_client)}")
        
        if not orchestrator or not orchestrator.zerodha_client:
            error_msg = f"Zerodha client not available - orchestrator: {orchestrator is not None}, client: {orchestrator.zerodha_client is not None if orchestrator else False}"
            logger.error(f"❌ [REAL POSITIONS] {error_msg}")
            return {
                "success": False,
                "positions": [],
                "error": error_msg,
                "count": 0,
                "data_source": "ZERODHA_CONNECTION_FAILED",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get real positions data from Zerodha API
        logger.info("📊 [REAL POSITIONS] Attempting to fetch REAL positions from Zerodha API...")
        try:
            positions_data = await orchestrator.zerodha_client.get_positions()
            logger.info(f"📊 [REAL POSITIONS] Zerodha API response type: {type(positions_data)}")
            logger.info(f"📊 [REAL POSITIONS] Zerodha API response data: {positions_data}")
            
            # ENHANCED DEBUG: Show net vs day positions separately
            net_positions = positions_data.get('net', [])
            day_positions = positions_data.get('day', [])
            logger.info(f"📊 [REAL POSITIONS] NET positions count: {len(net_positions)}")
            logger.info(f"📊 [REAL POSITIONS] DAY positions count: {len(day_positions)}")
            logger.info(f"📊 [REAL POSITIONS] NET positions data: {net_positions}")
            logger.info(f"📊 [REAL POSITIONS] DAY positions data: {day_positions}")
            
            if not positions_data:
                logger.warning("⚠️ [REAL POSITIONS] No positions data returned from Zerodha")
                return {
                    "success": True,
                    "positions": [],
                    "message": "No active positions found in Zerodha account",
                    "count": 0,
                    "data_source": "ZERODHA_API_EMPTY",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process real Zerodha positions - CRITICAL FIX: Use only NET positions to avoid duplicates
            # NET positions = current actual positions in account
            # DAY positions = intraday trades that may include closed positions
            real_positions = []
            net_positions = positions_data.get('net', [])
            
            logger.info(f"📊 [REAL POSITIONS] Using NET positions only to avoid duplicates from DAY positions")
            all_positions = net_positions  # Only use net positions for accuracy
            
            logger.info(f"📊 [REAL POSITIONS] Processing {len(all_positions)} positions from Zerodha")
            
            for position in all_positions:
                quantity = position.get('quantity', 0)
                if quantity != 0:  # Only include active positions
                    symbol = position.get('tradingsymbol', '')
                    # CRITICAL FIX: Use Zerodha's actual unrealised_pnl field for accuracy
                    pnl = float(position.get('unrealised_pnl', 0) or 0)
                    avg_price = float(position.get('average_price', 0) or 0)
                    last_price = float(position.get('last_price', 0) or 0)
                    
                    logger.info(f"📊 [REAL POSITIONS] Raw position data: {position}")
                    
                    real_positions.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "average_price": avg_price,
                        "last_price": last_price,
                        "pnl": round(pnl, 2),
                        "product": position.get('product', ''),
                        "exchange": position.get('exchange', ''),
                        "instrument_token": position.get('instrument_token', '')
                    })
                    
                    logger.info(f"📊 [REAL POSITIONS] Position: {symbol} | Qty: {quantity} | P&L: ₹{pnl:.2f}")
            
            total_pnl = sum(pos["pnl"] for pos in real_positions)
            logger.info(f"📊 [REAL POSITIONS] TOTAL: {len(real_positions)} positions, ₹{total_pnl:.2f} P&L")
            
            return {
                "success": True,
                "positions": real_positions,
                "message": f"Found {len(real_positions)} active positions from Zerodha",
                "count": len(real_positions),
                "total_pnl": round(total_pnl, 2),
                "data_source": "ZERODHA_API_REAL",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as zerodha_error:
            logger.error(f"❌ [REAL POSITIONS] Zerodha API call failed: {zerodha_error}")
            return {
                "success": False,
                "positions": [],
                "error": f"Zerodha API error: {str(zerodha_error)}",
                "count": 0,
                "data_source": "ZERODHA_API_ERROR",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error getting all positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user_positions(user_id: str):
    """Get all positions for a user"""
    try:
        # Return empty list for now
        return {
            "success": True,
            "user_id": user_id,
            "positions": [],
            "message": "No active positions for user"
        }

    except Exception as e:
        logger.error(f"Error getting user positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{position_id}")
async def get_position(position_id: str):
    """Get position details"""
    try:
        # Position not found since we have no positions yet
        raise HTTPException(status_code=404, detail="Position not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{position_id}")
async def update_position(position_id: str, position_update: Dict[str, Any]):
    """Update position details"""
    try:
        # Position not found since we have no positions yet
        raise HTTPException(status_code=404, detail="Position not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_position(position_data: Dict[str, Any]):
    """Create a new position"""
    try:
        # For now, just acknowledge the request
        return {
            "success": True,
            "message": "Position creation acknowledged",
            "data": position_data
        }
    except Exception as e:
        logger.error(f"Error creating position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
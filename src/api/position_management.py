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
            
            # CRITICAL FIX: Include positions with P&L even if quantity is 0 (closed positions)
            unique_positions = {}
            for position in all_positions:
                quantity = position.get('quantity', 0)
                pnl = float(position.get('pnl', 0) or position.get('unrealised_pnl', 0) or position.get('day_pnl', 0) or 0)

                # Include positions that have quantity OR have P&L (for closed positions with P&L)
                if quantity != 0 or pnl != 0:
                    symbol = position.get('tradingsymbol', '')
                    product = position.get('product', '')
                    
                    # Create unique key to prevent duplicates
                    unique_key = f"{symbol}_{quantity}_{product}"
                    
                    # CRITICAL FIX: Use Zerodha's pnl field (try multiple field names)
                    pnl = float(position.get('pnl', 0) or position.get('unrealised_pnl', 0) or position.get('day_pnl', 0) or 0)
                    avg_price = float(position.get('average_price', 0) or 0)
                    last_price = float(position.get('last_price', 0) or 0)
                    
                    # 🚨 CRITICAL DEBUG: Log price data to identify the issue
                    logger.info(f"📊 [REAL POSITIONS] {symbol} PRICE DEBUG:")
                    logger.info(f"   Average Price: ₹{avg_price}")
                    logger.info(f"   Last Price: ₹{last_price}")
                    logger.info(f"   P&L: ₹{pnl}")
                    logger.info(f"   Quantity: {quantity}")
                    
                    # 🚨 CRITICAL FIX: If last_price is 0 or same as avg_price, try to get real-time price
                    if last_price <= 0 or last_price == avg_price:
                        logger.warning(f"⚠️ {symbol} last_price issue: {last_price} (avg: {avg_price})")
                        
                        # Try to get real-time price from TrueData
                        try:
                            from data.truedata_client import live_market_data
                            if symbol in live_market_data:
                                market_ltp = live_market_data[symbol].get('ltp', 0)
                                if market_ltp > 0 and market_ltp != avg_price:
                                    last_price = float(market_ltp)
                                    logger.info(f"✅ {symbol} updated with TrueData LTP: ₹{last_price}")
                        except Exception as e:
                            logger.debug(f"Could not get TrueData price for {symbol}: {e}")
                    
                    logger.info(f"📊 [REAL POSITIONS] Raw position data: {position}")
                    
                    # 🚨 CRITICAL FIX: Recalculate P&L with corrected last_price
                    if last_price > 0 and avg_price > 0 and quantity != 0:
                        # Recalculate P&L based on current vs average price
                        calculated_pnl = (last_price - avg_price) * quantity
                        if abs(calculated_pnl - pnl) > 1:  # If difference > ₹1, use calculated
                            logger.info(f"🔧 {symbol} P&L corrected: Zerodha ₹{pnl} → Calculated ₹{calculated_pnl}")
                            pnl = calculated_pnl
                    
                    # Calculate P&L percentage
                    pnl_percent = 0.0
                    if avg_price > 0 and quantity != 0:
                        position_value = abs(avg_price * quantity)
                        pnl_percent = (pnl / position_value) * 100 if position_value > 0 else 0
                    
                    # Only add if not already seen (deduplication)
                    if unique_key not in unique_positions:
                        position_info = {
                            "symbol": symbol,
                            "quantity": quantity,
                            "average_price": avg_price,
                            "current_price": last_price,  # 🚨 FIXED: Use current_price instead of last_price
                            "last_price": last_price,     # Keep for compatibility
                            "pnl": round(pnl, 2),
                            "pnl_percent": round(pnl_percent, 2),  # 🚨 NEW: Add P&L percentage
                            "product": product,
                            "exchange": position.get('exchange', ''),
                            "instrument_token": position.get('instrument_token', '')
                        }
                        
                        unique_positions[unique_key] = position_info
                        real_positions.append(position_info)
                        
                        logger.info(f"📊 [REAL POSITIONS] Position: {symbol} | Qty: {quantity} | P&L: ₹{pnl:.2f}")
                    else:
                        logger.info(f"📊 [REAL POSITIONS] DUPLICATE SKIPPED: {unique_key}")
            
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
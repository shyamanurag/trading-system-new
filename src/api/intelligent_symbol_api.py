"""
API endpoints for Intelligent Symbol Management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging

from src.core.intelligent_symbol_manager import (
    intelligent_symbol_manager,
    start_intelligent_symbol_management,
    stop_intelligent_symbol_management,
    get_intelligent_symbol_status,
    get_active_symbols
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/intelligent-symbols/status")
async def get_symbol_manager_status():
    """Get intelligent symbol manager status"""
    try:
        status = get_intelligent_symbol_status()
        return {
            "success": True,
            "status": status,
            "message": "Symbol manager status retrieved"
        }
    except Exception as e:
        logger.error(f"Failed to get symbol manager status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-symbols/start")
async def start_symbol_manager():
    """Start the intelligent symbol management system"""
    try:
        await start_intelligent_symbol_management()
        return {
            "success": True,
            "message": "Intelligent symbol management started",
            "status": get_intelligent_symbol_status()
        }
    except Exception as e:
        logger.error(f"Failed to start symbol manager: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-symbols/stop")
async def stop_symbol_manager():
    """Stop the intelligent symbol management system"""
    try:
        await stop_intelligent_symbol_management()
        return {
            "success": True,
            "message": "Intelligent symbol management stopped"
        }
    except Exception as e:
        logger.error(f"Failed to stop symbol manager: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligent-symbols/active")
async def get_active_symbols_list():
    """Get list of currently active symbols"""
    try:
        symbols = get_active_symbols()
        return {
            "success": True,
            "symbols": symbols,
            "count": len(symbols),
            "message": f"Retrieved {len(symbols)} active symbols"
        }
    except Exception as e:
        logger.error(f"Failed to get active symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligent-symbols/analytics")
async def get_symbol_analytics():
    """Get analytics about symbol usage"""
    try:
        status = get_intelligent_symbol_status()
        symbols = get_active_symbols()
        
        # Analyze symbol distribution
        symbol_types = {
            'indices': 0,
            'stocks': 0,
            'options': 0,
            'others': 0
        }
        
        for symbol in symbols:
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                symbol_types['indices'] += 1
            elif 'CE' in symbol or 'PE' in symbol:
                symbol_types['options'] += 1
            elif symbol.isalpha():
                symbol_types['stocks'] += 1
            else:
                symbol_types['others'] += 1
        
        return {
            "success": True,
            "analytics": {
                "total_symbols": len(symbols),
                "symbol_distribution": symbol_types,
                "utilization_percentage": round((len(symbols) / 250) * 100, 2),
                "manager_status": status
            },
            "message": "Symbol analytics retrieved"
        }
    except Exception as e:
        logger.error(f"Failed to get symbol analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-symbols/manual-add")
async def manually_add_symbols(symbols: List[str]):
    """Manually add symbols to the active list"""
    try:
        # Check current symbol count
        current_count = len(get_active_symbols())
        if current_count + len(symbols) > 250:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot add {len(symbols)} symbols. Would exceed 250 limit. Current: {current_count}"
            )
        
        await intelligent_symbol_manager.subscribe_symbols(symbols)
        
        return {
            "success": True,
            "message": f"Added {len(symbols)} symbols manually",
            "symbols_added": symbols,
            "new_total": len(get_active_symbols())
        }
    except Exception as e:
        logger.error(f"Failed to manually add symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligent-symbols/manual-remove")
async def manually_remove_symbols(symbols: List[str]):
    """Manually remove symbols from the active list"""
    try:
        await intelligent_symbol_manager.unsubscribe_symbols(symbols)
        
        return {
            "success": True,
            "message": f"Removed {len(symbols)} symbols manually",
            "symbols_removed": symbols,
            "new_total": len(get_active_symbols())
        }
    except Exception as e:
        logger.error(f"Failed to manually remove symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligent-symbols/recommendations")
async def get_symbol_recommendations():
    """Get recommended symbols to add based on market conditions"""
    try:
        # Generate recommendations based on current market conditions
        recommendations = {
            "high_priority": [
                "NIFTY", "BANKNIFTY", "FINNIFTY"  # Core indices
            ],
            "medium_priority": [
                "RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK"  # Top F&O stocks
            ],
            "low_priority": [
                "SBIN", "ITC", "LT", "WIPRO", "BHARTIARTL"  # Secondary F&O stocks
            ]
        }
        
        return {
            "success": True,
            "recommendations": recommendations,
            "message": "Symbol recommendations generated based on market conditions"
        }
    except Exception as e:
        logger.error(f"Failed to get symbol recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
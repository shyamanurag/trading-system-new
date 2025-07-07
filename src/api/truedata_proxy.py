"""
TrueData Proxy Service
=====================
Serves existing TrueData connection data to autonomous trading system
Solves the "User Already Connected" error by providing HTTP API access
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
import json

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/truedata-proxy", tags=["truedata-proxy"])

class TrueDataProxyService:
    """
    Proxy service to serve existing TrueData connection data
    """
    
    def __init__(self):
        self.cached_data = {}
        self.last_update = None
        self.connection_status = {
            'connected': False,
            'last_heartbeat': None,
            'symbols_count': 0,
            'data_source': 'none'
        }
        
    def update_from_external_source(self, data: Dict[str, Any]) -> bool:
        """Update cached data from external TrueData source"""
        try:
            self.cached_data = data
            self.last_update = datetime.now()
            self.connection_status = {
                'connected': True,
                'last_heartbeat': datetime.now().isoformat(),
                'symbols_count': len(data),
                'data_source': 'external_truedata'
            }
            
            logger.info(f"📊 TrueData proxy updated with {len(data)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating TrueData proxy: {e}")
            return False
    
    def get_market_data(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get market data from proxy cache"""
        try:
            if symbol:
                return self.cached_data.get(symbol, {})
            else:
                return self.cached_data.copy()
                
        except Exception as e:
            logger.error(f"❌ Error getting market data from proxy: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get proxy service status"""
        return {
            'connected': self.connection_status['connected'],
            'symbols_count': self.connection_status['symbols_count'],
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'data_source': self.connection_status['data_source']
        }

# Global proxy instance
truedata_proxy = TrueDataProxyService()

@router.get("/status")
async def get_proxy_status():
    """Get TrueData proxy status"""
    try:
        status = truedata_proxy.get_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting proxy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data")
async def get_all_proxy_data():
    """Get all market data from proxy"""
    try:
        data = truedata_proxy.get_market_data()
        
        if not data:
            raise HTTPException(
                status_code=503,
                detail="No market data available in proxy. TrueData connection may not be established."
            )
        
        return {
            "success": True,
            "data": data,
            "symbol_count": len(data),
            "timestamp": datetime.now().isoformat(),
            "source": "truedata_proxy"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all proxy data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}")
async def get_proxy_symbol_data(symbol: str):
    """Get specific symbol data from proxy"""
    try:
        data = truedata_proxy.get_market_data(symbol)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for symbol {symbol} in proxy"
            )
        
        return {
            "success": True,
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "truedata_proxy"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbol data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-data")
async def update_proxy_data(data: Dict[str, Any]):
    """Update proxy data (for external data sources)"""
    try:
        success = truedata_proxy.update_from_external_source(data)
        
        if success:
            return {
                "success": True,
                "message": f"Proxy updated with {len(data)} symbols",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update proxy data")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating proxy data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_truedata_proxy():
    """Get the global TrueData proxy instance"""
    return truedata_proxy

async def initialize_truedata_proxy():
    """Initialize TrueData proxy service"""
    try:
        logger.info("🔄 Initializing TrueData proxy service...")
        
        # Try to get initial data from any available source
        # This could be populated by external scripts or direct API calls
        
        logger.info("✅ TrueData proxy service initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize TrueData proxy: {e}")
        return False 
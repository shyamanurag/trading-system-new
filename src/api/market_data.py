from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from ..models.schema import MarketData
from ..core.market_data_manager import MarketDataManager
from ..core.technical_indicators import TechnicalIndicators
from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/market/data/{symbol}", response_model=MarketData)
async def get_market_data(
    symbol: str,
    timeframe: str = "1m",
    market_data_manager: MarketDataManager = Depends(),
    current_user = Depends(get_current_user)
):
    """Get current market data for a symbol"""
    try:
        data = await market_data_manager.get_current_data(symbol, timeframe)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        return data

    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/history/{symbol}")
async def get_historical_data(
    symbol: str,
    timeframe: str = "1d",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    market_data_manager: MarketDataManager = Depends(),
    current_user = Depends(get_current_user)
):
    """Get historical market data for a symbol"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        data = await market_data_manager.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return data

    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/quotes")
async def get_real_time_quotes(
    symbols: List[str] = Query(...),
    market_data_manager: MarketDataManager = Depends(),
    current_user = Depends(get_current_user)
):
    """Get real-time quotes for multiple symbols"""
    try:
        quotes = await market_data_manager.get_real_time_quotes(symbols)
        return quotes

    except Exception as e:
        logger.error(f"Error getting real-time quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    timeframe: str = "1d",
    indicators: List[str] = Query(...),
    lookback: int = Query(default=14, le=200),
    market_data_manager: MarketDataManager = Depends(),
    technical_indicators: TechnicalIndicators = Depends(),
    current_user = Depends(get_current_user)
):
    """Get technical indicators for a symbol"""
    try:
        # Get historical data
        data = await market_data_manager.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=lookback
        )
        
        # Calculate indicators
        result = {}
        for indicator in indicators:
            if indicator == "SMA":
                result["SMA"] = technical_indicators.calculate_sma(data, lookback)
            elif indicator == "EMA":
                result["EMA"] = technical_indicators.calculate_ema(data, lookback)
            elif indicator == "RSI":
                result["RSI"] = technical_indicators.calculate_rsi(data, lookback)
            elif indicator == "MACD":
                result["MACD"] = technical_indicators.calculate_macd(data)
            elif indicator == "BB":
                result["BB"] = technical_indicators.calculate_bollinger_bands(data, lookback)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported indicator: {indicator}"
                )
        
        return result

    except Exception as e:
        logger.error(f"Error calculating technical indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/summary")
async def get_market_summary(
    market_data_manager: MarketDataManager = Depends(),
    current_user = Depends(get_current_user)
):
    """Get market summary including major indices and sectors"""
    try:
        summary = await market_data_manager.get_market_summary()
        return summary

    except Exception as e:
        logger.error(f"Error getting market summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/sectors")
async def get_sector_performance(
    market_data_manager: MarketDataManager = Depends(),
    current_user = Depends(get_current_user)
):
    """Get sector performance data"""
    try:
        sectors = await market_data_manager.get_sector_performance()
        return sectors

    except Exception as e:
        logger.error(f"Error getting sector performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
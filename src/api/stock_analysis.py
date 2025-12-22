"""
Stock Analysis API
===================
Provides comprehensive technical analysis for any stock symbol using the trading system's algorithms.
Returns RSI, VRSI, MFI, MACD, Support/Resistance levels, and algo recommendations.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
import json
import redis
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["stock-analysis"])

# Redis client for market data
redis_client = None

def setup_redis():
    """Setup Redis client"""
    global redis_client
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        redis_client.ping()
        logger.info("✅ Stock Analysis Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Stock Analysis Redis connection failed: {e}")
        redis_client = None

setup_redis()

def get_live_data(symbol: str) -> Dict:
    """Get live market data for a symbol from Redis cache"""
    try:
        symbol_upper = symbol.upper().strip()
        
        # Index symbols are stored with -I suffix in TrueData
        index_symbols = {'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX'}
        
        # Try multiple symbol variations
        symbols_to_try = [symbol_upper]
        
        # If it's a known index without -I, add the -I version
        if symbol_upper in index_symbols:
            symbols_to_try.insert(0, f"{symbol_upper}-I")
        
        # If it already has -I, also try without
        if symbol_upper.endswith('-I'):
            base_symbol = symbol_upper[:-2]
            symbols_to_try.append(base_symbol)
        
        if redis_client:
            cached_data = redis_client.hgetall("truedata:live_cache")
            if cached_data:
                for sym in symbols_to_try:
                    if sym in cached_data:
                        logger.debug(f"Found {symbol} as {sym} in Redis cache")
                        return json.loads(cached_data[sym])
        
        # Fallback to direct cache
        from data.truedata_client import live_market_data
        for sym in symbols_to_try:
            if sym in live_market_data:
                logger.debug(f"Found {symbol} as {sym} in direct cache")
                return live_market_data.get(sym, {})
        
        logger.warning(f"Symbol {symbol} not found. Tried: {symbols_to_try}")
        return {}
        
    except Exception as e:
        logger.error(f"Error getting live data for {symbol}: {e}")
        return {}

async def get_zerodha_client():
    """Get Zerodha client from orchestrator"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        if orchestrator and orchestrator.zerodha_client:
            return orchestrator.zerodha_client
    except Exception as e:
        logger.warning(f"Could not get Zerodha client: {e}")
    return None

async def get_historical_candles(symbol: str, interval: str = '5minute', days: int = 3) -> List[Dict]:
    """Fetch historical candles from Zerodha"""
    try:
        zerodha_client = await get_zerodha_client()
        if not zerodha_client:
            return []
            
        candles = await zerodha_client.get_historical_data(
            symbol=symbol,
            interval=interval,
            from_date=datetime.now() - timedelta(days=days),
            to_date=datetime.now()
        )
        return candles if candles else []
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return []

def calculate_rsi(prices: List[float], period: int = 14) -> Dict:
    """Calculate RSI with interpretation"""
    try:
        if len(prices) < period + 1:
            return {"value": 50.0, "interpretation": "NEUTRAL", "error": "Insufficient data"}
        
        prices = np.array(prices)
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Interpretation
        if rsi >= 70:
            interpretation = "OVERBOUGHT"
        elif rsi <= 30:
            interpretation = "OVERSOLD"
        elif rsi >= 60:
            interpretation = "BULLISH"
        elif rsi <= 40:
            interpretation = "BEARISH"
        else:
            interpretation = "NEUTRAL"
        
        return {
            "value": round(rsi, 2),
            "interpretation": interpretation,
            "period": period
        }
        
    except Exception as e:
        return {"value": 50.0, "interpretation": "NEUTRAL", "error": str(e)}

def calculate_vrsi(prices: List[float], volumes: List[float], period: int = 14) -> Dict:
    """Calculate Volume-Weighted RSI"""
    try:
        if len(prices) < period + 1 or len(volumes) < period + 1:
            return {"value": 50.0, "interpretation": "NEUTRAL", "error": "Insufficient data"}
        
        prices = np.array(prices)
        volumes = np.array(volumes)
        
        deltas = np.diff(prices)
        vols = volumes[1:]  # Match with deltas
        
        # Weight changes by volume
        weighted_gains = np.where(deltas > 0, deltas * vols, 0)
        weighted_losses = np.where(deltas < 0, -deltas * vols, 0)
        
        avg_gain = np.mean(weighted_gains[:period])
        avg_loss = np.mean(weighted_losses[:period])
        
        for i in range(period, len(weighted_gains)):
            avg_gain = (avg_gain * (period - 1) + weighted_gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + weighted_losses[i]) / period
        
        if avg_loss == 0:
            vrsi = 100.0
        else:
            rs = avg_gain / avg_loss
            vrsi = 100 - (100 / (1 + rs))
        
        # Interpretation
        if vrsi >= 75:
            interpretation = "STRONG_OVERBOUGHT"
        elif vrsi <= 25:
            interpretation = "STRONG_OVERSOLD"
        elif vrsi >= 60:
            interpretation = "BULLISH"
        elif vrsi <= 40:
            interpretation = "BEARISH"
        else:
            interpretation = "NEUTRAL"
        
        return {
            "value": round(vrsi, 2),
            "interpretation": interpretation,
            "period": period
        }
        
    except Exception as e:
        return {"value": 50.0, "interpretation": "NEUTRAL", "error": str(e)}

def calculate_mfi(highs: List[float], lows: List[float], closes: List[float], 
                  volumes: List[float], period: int = 14) -> Dict:
    """Calculate Money Flow Index"""
    try:
        if len(closes) < period + 1:
            return {"value": 50.0, "interpretation": "NEUTRAL", "error": "Insufficient data"}
        
        highs = np.array(highs)
        lows = np.array(lows)
        closes = np.array(closes)
        volumes = np.array(volumes)
        
        # Typical Price
        typical_price = (highs + lows + closes) / 3
        
        # Raw Money Flow
        raw_money_flow = typical_price * volumes
        
        # Positive and Negative Money Flow
        positive_flow = np.zeros(len(typical_price))
        negative_flow = np.zeros(len(typical_price))
        
        for i in range(1, len(typical_price)):
            if typical_price[i] > typical_price[i-1]:
                positive_flow[i] = raw_money_flow[i]
            elif typical_price[i] < typical_price[i-1]:
                negative_flow[i] = raw_money_flow[i]
        
        # Calculate MFI
        positive_sum = np.sum(positive_flow[-period:])
        negative_sum = np.sum(negative_flow[-period:])
        
        if negative_sum == 0:
            mfi = 100.0
        else:
            money_ratio = positive_sum / negative_sum
            mfi = 100 - (100 / (1 + money_ratio))
        
        # Interpretation
        if mfi >= 80:
            interpretation = "OVERBOUGHT"
        elif mfi <= 20:
            interpretation = "OVERSOLD"
        elif mfi >= 60:
            interpretation = "BULLISH"
        elif mfi <= 40:
            interpretation = "BEARISH"
        else:
            interpretation = "NEUTRAL"
        
        return {
            "value": round(mfi, 2),
            "interpretation": interpretation,
            "period": period
        }
        
    except Exception as e:
        return {"value": 50.0, "interpretation": "NEUTRAL", "error": str(e)}

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """Calculate MACD with state detection"""
    try:
        if len(prices) < slow + signal:
            return {
                "macd_line": 0.0,
                "signal_line": 0.0,
                "histogram": 0.0,
                "state": "NEUTRAL",
                "crossover": None,
                "error": "Insufficient data"
            }
        
        prices = np.array(prices)
        
        # Calculate EMAs
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_values = np.zeros(len(data))
            ema_values[0] = data[0]
            for i in range(1, len(data)):
                ema_values[i] = (data[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
            return ema_values
        
        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_histogram = histogram[-1]
        prev_histogram = histogram[-2] if len(histogram) > 1 else 0
        
        # Determine state
        if current_macd > current_signal and current_macd > 0:
            state = "STRONG_BULLISH"
        elif current_macd > current_signal:
            state = "BULLISH"
        elif current_macd < current_signal and current_macd < 0:
            state = "STRONG_BEARISH"
        elif current_macd < current_signal:
            state = "BEARISH"
        else:
            state = "NEUTRAL"
        
        # Detect crossover
        crossover = None
        if len(histogram) >= 2:
            if prev_histogram < 0 and current_histogram > 0:
                crossover = "BULLISH_CROSSOVER"
            elif prev_histogram > 0 and current_histogram < 0:
                crossover = "BEARISH_CROSSOVER"
        
        return {
            "macd_line": round(current_macd, 4),
            "signal_line": round(current_signal, 4),
            "histogram": round(current_histogram, 4),
            "state": state,
            "crossover": crossover,
            "params": {"fast": fast, "slow": slow, "signal": signal}
        }
        
    except Exception as e:
        return {
            "macd_line": 0.0,
            "signal_line": 0.0,
            "histogram": 0.0,
            "state": "NEUTRAL",
            "crossover": None,
            "error": str(e)
        }

def calculate_support_resistance(highs: List[float], lows: List[float], 
                                   closes: List[float], current_price: float) -> Dict:
    """Calculate Support/Resistance levels using pivot points and swing levels"""
    try:
        if len(closes) < 5:
            return {"error": "Insufficient data"}
        
        # Get previous day's OHLC (approximate from candle data)
        prev_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        prev_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        prev_close = closes[-2] if len(closes) > 1 else closes[-1]
        
        # Calculate Pivot Points
        pivot = (prev_high + prev_low + prev_close) / 3
        
        # Standard Pivot Levels
        r1 = 2 * pivot - prev_low
        r2 = pivot + (prev_high - prev_low)
        r3 = prev_high + 2 * (pivot - prev_low)
        
        s1 = 2 * pivot - prev_high
        s2 = pivot - (prev_high - prev_low)
        s3 = prev_low - 2 * (prev_high - pivot)
        
        # Find swing highs/lows (local extrema)
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(closes) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        # Find nearest support/resistance
        all_resistance = sorted([r1, r2, r3] + swing_highs)
        all_support = sorted([s1, s2, s3] + swing_lows, reverse=True)
        
        nearest_resistance = None
        nearest_support = None
        
        for level in all_resistance:
            if level > current_price * 1.001:  # At least 0.1% above
                nearest_resistance = level
                break
        
        for level in all_support:
            if level < current_price * 0.999:  # At least 0.1% below
                nearest_support = level
                break
        
        # Price position relative to pivot
        if current_price > r1:
            position = "ABOVE_R1"
        elif current_price > pivot:
            position = "ABOVE_PIVOT"
        elif current_price > s1:
            position = "BELOW_PIVOT"
        else:
            position = "BELOW_S1"
        
        return {
            "pivot": round(pivot, 2),
            "resistance": {
                "r1": round(r1, 2),
                "r2": round(r2, 2),
                "r3": round(r3, 2)
            },
            "support": {
                "s1": round(s1, 2),
                "s2": round(s2, 2),
                "s3": round(s3, 2)
            },
            "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
            "nearest_support": round(nearest_support, 2) if nearest_support else None,
            "position": position,
            "swing_highs": [round(x, 2) for x in sorted(swing_highs)[-3:]] if swing_highs else [],
            "swing_lows": [round(x, 2) for x in sorted(swing_lows)[:3]] if swing_lows else []
        }
        
    except Exception as e:
        return {"error": str(e)}

def calculate_volume_analysis(volumes: List[float], closes: List[float]) -> Dict:
    """Analyze volume patterns and buy/sell pressure"""
    try:
        if len(volumes) < 10:
            return {"error": "Insufficient data"}
        
        volumes = np.array(volumes)
        closes = np.array(closes)
        
        # Average volume
        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume trend
        recent_avg = np.mean(volumes[-5:])
        older_avg = np.mean(volumes[-20:-5]) if len(volumes) >= 20 else np.mean(volumes[:-5])
        volume_trend = "INCREASING" if recent_avg > older_avg * 1.1 else \
                       "DECREASING" if recent_avg < older_avg * 0.9 else "STABLE"
        
        # Buy/Sell pressure based on price direction and volume
        buy_volume = 0
        sell_volume = 0
        
        for i in range(1, min(20, len(closes))):
            if closes[-i] > closes[-i-1]:
                buy_volume += volumes[-i]
            else:
                sell_volume += volumes[-i]
        
        total_pressure = buy_volume + sell_volume
        if total_pressure > 0:
            buy_pressure = buy_volume / total_pressure
            sell_pressure = sell_volume / total_pressure
        else:
            buy_pressure = 0.5
            sell_pressure = 0.5
        
        return {
            "current_volume": int(current_volume),
            "average_volume": int(avg_volume),
            "volume_ratio": round(volume_ratio, 2),
            "volume_trend": volume_trend,
            "buy_pressure": round(buy_pressure * 100, 1),
            "sell_pressure": round(sell_pressure * 100, 1),
            "interpretation": "HIGH_BUYING" if buy_pressure > 0.65 else \
                            "HIGH_SELLING" if sell_pressure > 0.65 else "BALANCED"
        }
        
    except Exception as e:
        return {"error": str(e)}

def generate_recommendation(rsi: Dict, vrsi: Dict, mfi: Dict, macd: Dict, 
                            volume: Dict, sr_levels: Dict, current_price: float) -> Dict:
    """Generate overall algorithm recommendation"""
    try:
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        reasons = []
        
        # RSI Analysis
        if rsi.get("value"):
            total_signals += 1
            if rsi["value"] <= 30:
                bullish_signals += 1.5  # Extra weight for oversold
                reasons.append(f"RSI oversold ({rsi['value']})")
            elif rsi["value"] >= 70:
                bearish_signals += 1.5
                reasons.append(f"RSI overbought ({rsi['value']})")
            elif rsi["value"] < 50:
                bearish_signals += 0.5
            else:
                bullish_signals += 0.5
        
        # VRSI Analysis
        if vrsi.get("value"):
            total_signals += 1
            if vrsi["value"] <= 35:
                bullish_signals += 1
                reasons.append(f"VRSI showing volume-backed weakness ({vrsi['value']})")
            elif vrsi["value"] >= 65:
                bearish_signals += 1
                reasons.append(f"VRSI showing volume-backed strength ({vrsi['value']})")
        
        # MFI Analysis
        if mfi.get("value"):
            total_signals += 1
            if mfi["value"] <= 20:
                bullish_signals += 1.5
                reasons.append(f"MFI oversold ({mfi['value']})")
            elif mfi["value"] >= 80:
                bearish_signals += 1.5
                reasons.append(f"MFI overbought ({mfi['value']})")
        
        # MACD Analysis
        if macd.get("state"):
            total_signals += 2  # MACD gets more weight
            if macd["state"] == "STRONG_BULLISH":
                bullish_signals += 2
                reasons.append("MACD strong bullish")
            elif macd["state"] == "BULLISH":
                bullish_signals += 1
                reasons.append("MACD bullish")
            elif macd["state"] == "STRONG_BEARISH":
                bearish_signals += 2
                reasons.append("MACD strong bearish")
            elif macd["state"] == "BEARISH":
                bearish_signals += 1
                reasons.append("MACD bearish")
            
            if macd.get("crossover") == "BULLISH_CROSSOVER":
                bullish_signals += 1
                reasons.append("MACD bullish crossover")
            elif macd.get("crossover") == "BEARISH_CROSSOVER":
                bearish_signals += 1
                reasons.append("MACD bearish crossover")
        
        # Volume Analysis
        if volume.get("buy_pressure"):
            total_signals += 1
            if volume["buy_pressure"] > 65:
                bullish_signals += 1
                reasons.append(f"High buying pressure ({volume['buy_pressure']}%)")
            elif volume["sell_pressure"] > 65:
                bearish_signals += 1
                reasons.append(f"High selling pressure ({volume['sell_pressure']}%)")
        
        # S/R Position
        if sr_levels.get("position"):
            total_signals += 1
            if sr_levels["position"] == "BELOW_S1":
                bullish_signals += 0.5  # Near support = potential bounce
                reasons.append("Price near support levels")
            elif sr_levels["position"] == "ABOVE_R1":
                bearish_signals += 0.5  # Near resistance = potential rejection
                reasons.append("Price near resistance levels")
        
        # Calculate final scores
        total_weight = bullish_signals + bearish_signals
        if total_weight > 0:
            bullish_score = (bullish_signals / total_weight) * 100
            bearish_score = (bearish_signals / total_weight) * 100
        else:
            bullish_score = 50
            bearish_score = 50
        
        # Determine recommendation
        if bullish_score >= 65:
            recommendation = "BUY"
            confidence = min(bullish_score, 95)
        elif bearish_score >= 65:
            recommendation = "SELL"
            confidence = min(bearish_score, 95)
        elif bullish_score > bearish_score + 10:
            recommendation = "WEAK_BUY"
            confidence = bullish_score
        elif bearish_score > bullish_score + 10:
            recommendation = "WEAK_SELL"
            confidence = bearish_score
        else:
            recommendation = "NEUTRAL"
            confidence = 50
        
        return {
            "recommendation": recommendation,
            "confidence": round(confidence, 1),
            "bullish_score": round(bullish_score, 1),
            "bearish_score": round(bearish_score, 1),
            "signals_analyzed": total_signals,
            "key_reasons": reasons[:5]  # Top 5 reasons
        }
        
    except Exception as e:
        return {
            "recommendation": "NEUTRAL",
            "confidence": 50,
            "error": str(e)
        }


@router.get("/stock-analysis/{symbol}")
async def get_stock_analysis(
    symbol: str,
    include_historical: bool = Query(True, description="Include historical data analysis")
):
    """
    Get comprehensive technical analysis for a stock symbol.
    
    Returns RSI, VRSI, MFI, MACD, Support/Resistance levels, volume analysis,
    and algorithm recommendation based on all indicators.
    """
    try:
        symbol = symbol.upper().strip()
        logger.info(f"📊 Analyzing stock: {symbol}")
        
        # Get live market data
        live_data = get_live_data(symbol)
        
        if not live_data:
            raise HTTPException(
                status_code=404,
                detail=f"No live data available for {symbol}. Symbol may not be subscribed."
            )
        
        current_price = live_data.get('ltp', 0)
        
        # Build price data response
        price_data = {
            "symbol": symbol,
            "ltp": current_price,
            "open": live_data.get('open', 0),
            "high": live_data.get('high', 0),
            "low": live_data.get('low', 0),
            "close": live_data.get('close', current_price),
            "change": live_data.get('change', 0),
            "change_percent": live_data.get('change_percent', 0),
            "volume": live_data.get('volume', 0),
            "timestamp": live_data.get('timestamp', datetime.now().isoformat())
        }
        
        # Initialize analysis results
        analysis = {
            "price_data": price_data,
            "indicators": {},
            "support_resistance": {},
            "volume_analysis": {},
            "recommendation": {},
            "data_source": "live",
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Try to get historical data for indicator calculations
        candles = []
        if include_historical:
            candles = await get_historical_candles(symbol, '5minute', 3)
        
        if candles and len(candles) >= 30:
            # Extract OHLCV from candles
            opens = [c.get('open', 0) for c in candles]
            highs = [c.get('high', 0) for c in candles]
            lows = [c.get('low', 0) for c in candles]
            closes = [c.get('close', 0) for c in candles]
            volumes = [c.get('volume', 0) for c in candles]
            
            # Calculate all indicators
            analysis["indicators"]["rsi"] = calculate_rsi(closes)
            analysis["indicators"]["vrsi"] = calculate_vrsi(closes, volumes)
            analysis["indicators"]["mfi"] = calculate_mfi(highs, lows, closes, volumes)
            analysis["indicators"]["macd"] = calculate_macd(closes)
            
            analysis["support_resistance"] = calculate_support_resistance(
                highs, lows, closes, current_price
            )
            
            analysis["volume_analysis"] = calculate_volume_analysis(volumes, closes)
            
            # Generate recommendation
            analysis["recommendation"] = generate_recommendation(
                analysis["indicators"]["rsi"],
                analysis["indicators"]["vrsi"],
                analysis["indicators"]["mfi"],
                analysis["indicators"]["macd"],
                analysis["volume_analysis"],
                analysis["support_resistance"],
                current_price
            )
            
            analysis["data_source"] = "historical"
            analysis["candles_analyzed"] = len(candles)
            
        else:
            # Limited analysis with just live data
            analysis["indicators"]["rsi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["vrsi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["mfi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["macd"] = {"state": None, "error": "No historical data"}
            analysis["support_resistance"] = {"error": "No historical data"}
            analysis["volume_analysis"] = {"error": "No historical data"}
            analysis["recommendation"] = {
                "recommendation": "INSUFFICIENT_DATA",
                "confidence": 0,
                "error": "Historical data required for full analysis"
            }
        
        logger.info(f"✅ Analysis complete for {symbol}: {analysis['recommendation'].get('recommendation', 'N/A')}")
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/stock-analysis/symbols/available")
async def get_available_symbols():
    """Get list of symbols available for analysis (currently subscribed)"""
    try:
        if redis_client:
            cached_data = redis_client.hgetall("truedata:live_cache")
            if cached_data:
                symbols = list(cached_data.keys())
                return {
                    "success": True,
                    "symbols": sorted(symbols),
                    "count": len(symbols),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Fallback
        from data.truedata_client import live_market_data
        symbols = list(live_market_data.keys())
        
        return {
            "success": True,
            "symbols": sorted(symbols),
            "count": len(symbols),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return {
            "success": False,
            "symbols": [],
            "error": str(e)
        }

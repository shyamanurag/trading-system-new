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

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    This fixes the 'numpy.bool_' object is not iterable error.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

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
            client = orchestrator.zerodha_client
            # Check if client is properly initialized
            if hasattr(client, 'kite') and client.kite and hasattr(client, 'is_connected'):
                if client.is_connected:
                    logger.debug(f"✅ Zerodha client available and connected")
                else:
                    logger.warning(f"⚠️ Zerodha client exists but not connected")
            return client
    except Exception as e:
        logger.warning(f"Could not get Zerodha client: {e}")
    return None

async def _get_mtf_data_from_strategies(symbol: str, interval: str = '5minute') -> List[Dict]:
    """
    Get cached MTF candle data from active strategies.
    This is more reliable than direct Zerodha API calls during market hours
    because strategies already have this data fetched and cached.
    """
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator:
            return []
        
        # Map interval to MTF timeframe key
        interval_map = {
            '5minute': '5min',
            '15minute': '15min',
            '60minute': '60min',
            'minute': '5min',  # Fallback
        }
        tf_key = interval_map.get(interval, '5min')
        
        symbol_upper = symbol.upper().strip()
        
        # Try to get MTF data from any active strategy
        strategies_to_check = []
        
        if hasattr(orchestrator, 'active_strategies'):
            strategies_to_check = list(orchestrator.active_strategies.values())
        elif hasattr(orchestrator, 'strategies'):
            strategies_to_check = list(orchestrator.strategies.values())
        
        for strategy in strategies_to_check:
            if not strategy:
                continue
                
            # Check if strategy has MTF data for this symbol
            if hasattr(strategy, 'mtf_data') and strategy.mtf_data:
                mtf = strategy.mtf_data.get(symbol_upper, {})
                candles = mtf.get(tf_key, [])
                
                if candles and len(candles) >= 14:
                    logger.debug(f"Found MTF data for {symbol_upper} in {strategy.__class__.__name__}")
                    return candles
        
        return []
        
    except Exception as e:
        logger.debug(f"Could not get MTF data from strategies: {e}")
        return []

async def get_historical_candles(symbol: str, interval: str = '5minute', days: int = 3) -> List[Dict]:
    """Fetch historical candles from Zerodha or strategy MTF cache"""
    try:
        # First, try to get MTF data from active strategies (already cached and working)
        mtf_candles = await _get_mtf_data_from_strategies(symbol, interval)
        if mtf_candles and len(mtf_candles) >= 14:
            logger.info(f"✅ Using cached MTF data for {symbol}: {len(mtf_candles)} candles")
            return mtf_candles
        
        zerodha_client = await get_zerodha_client()
        if not zerodha_client:
            logger.warning(f"No Zerodha client available for historical data")
            return []
        
        # Check if Zerodha is connected
        if not getattr(zerodha_client, 'is_connected', False):
            logger.warning(f"Zerodha client not connected - cannot fetch historical data for {symbol}")
            return []
        
        # Map internal symbols to Zerodha trading symbols for historical data
        symbol_upper = symbol.upper().strip()
        
        # Index symbols mapping with exchange info
        index_config = {
            'NIFTY-I': ('NIFTY 50', 'NSE'),
            'NIFTY': ('NIFTY 50', 'NSE'),
            'BANKNIFTY-I': ('NIFTY BANK', 'NSE'),
            'BANKNIFTY': ('NIFTY BANK', 'NSE'),
            'FINNIFTY-I': ('NIFTY FIN SERVICE', 'NSE'),
            'FINNIFTY': ('NIFTY FIN SERVICE', 'NSE'),
            'MIDCPNIFTY-I': ('NIFTY MID SELECT', 'NSE'),
            'MIDCPNIFTY': ('NIFTY MID SELECT', 'NSE'),
            'SENSEX-I': ('SENSEX', 'BSE'),
            'SENSEX': ('SENSEX', 'BSE'),
        }
        
        if symbol_upper in index_config:
            zerodha_symbol, exchange = index_config[symbol_upper]
        else:
            zerodha_symbol = symbol_upper
            exchange = 'NSE'
        
        logger.info(f"Fetching historical data: {symbol} -> {zerodha_symbol} ({exchange})")
        
        # Fetch with extended days if initial fetch fails
        candles = await zerodha_client.get_historical_data(
            symbol=zerodha_symbol,
            interval=interval,
            from_date=datetime.now() - timedelta(days=days),
            to_date=datetime.now(),
            exchange=exchange
        )
        
        # If no candles, try fetching more days (some symbols may have gaps)
        if not candles and days < 10:
            logger.info(f"Retrying with extended period for {zerodha_symbol}...")
            candles = await zerodha_client.get_historical_data(
                symbol=zerodha_symbol,
                interval=interval,
                from_date=datetime.now() - timedelta(days=10),
                to_date=datetime.now(),
                exchange=exchange
            )
        
        if candles:
            logger.info(f"✅ Got {len(candles)} candles for {zerodha_symbol}")
        else:
            logger.warning(f"⚠️ No historical candles returned for {zerodha_symbol} - check if symbol exists in {exchange}")
            
        return candles if candles else []
        
    except Exception as e:
        logger.error(f"❌ Error fetching historical data for {symbol}: {e}", exc_info=True)
        return []

async def get_options_analytics(symbol: str) -> Dict:
    """
    Fetch options analytics for indices (NIFTY, BANKNIFTY, etc.)
    Also works for F&O stocks
    Returns PCR, OI data, Max Pain, IV from Zerodha option chain
    """
    try:
        # Known index symbols
        index_symbols = {'NIFTY', 'NIFTY-I', 'BANKNIFTY', 'BANKNIFTY-I', 
                        'FINNIFTY', 'FINNIFTY-I', 'MIDCPNIFTY', 'MIDCPNIFTY-I',
                        'SENSEX', 'SENSEX-I'}
        
        symbol_upper = symbol.upper().strip()
        base_symbol = symbol_upper.replace('-I', '')
        
        # For non-index symbols, still try to get options data if available
        is_index = symbol_upper in index_symbols or base_symbol in index_symbols
        
        zerodha_client = await get_zerodha_client()
        if not zerodha_client:
            return {"available": False, "reason": "Zerodha client not available"}
        
        try:
            # Fetch option chain from Zerodha
            option_chain = await zerodha_client.get_option_chain(base_symbol)
        except Exception as oc_err:
            logger.warning(f"Option chain fetch failed for {symbol}: {oc_err}")
            return {"available": False, "reason": "Option chain not available for this symbol"}
        
        if not option_chain or not option_chain.get('analytics'):
            if not is_index:
                return {"available": False, "reason": "Options analytics only for indices/F&O stocks"}
            return {"available": False, "reason": "Could not fetch option chain"}
        
        analytics = option_chain.get('analytics', {})
        
        # Extract key metrics
        pcr = analytics.get('pcr', 0) or 0
        max_pain = analytics.get('max_pain', 0) or 0
        total_call_oi = analytics.get('total_call_oi', 0) or 0
        total_put_oi = analytics.get('total_put_oi', 0) or 0
        iv_mean = analytics.get('iv_mean', 0) or 0
        iv_skew = analytics.get('iv_skew', {}) or {}
        
        # OI analysis
        oi_interpretation = "NEUTRAL"
        if pcr > 1.2:
            oi_interpretation = "BULLISH"  # High puts = writers expecting up
        elif pcr < 0.8:
            oi_interpretation = "BEARISH"  # High calls = writers expecting down
        elif pcr > 1.0:
            oi_interpretation = "MILDLY_BULLISH"
        else:
            oi_interpretation = "MILDLY_BEARISH"
        
        # Max pain analysis
        spot_price = option_chain.get('spot_price', 0) or 0
        if spot_price > 0 and max_pain > 0:
            distance_to_max_pain = ((max_pain - spot_price) / spot_price) * 100
        else:
            distance_to_max_pain = 0
        
        return {
            "available": True,
            "is_index": is_index,
            "pcr": round(float(pcr), 2),
            "pcr_interpretation": oi_interpretation,
            "total_call_oi": int(total_call_oi),
            "total_put_oi": int(total_put_oi),
            "max_pain": round(float(max_pain), 2),
            "distance_to_max_pain_pct": round(float(distance_to_max_pain), 2),
            "iv_mean": round(float(iv_mean), 2),
            "iv_skew": {
                "atm_call": round(float(iv_skew.get('atm_call', 0) or 0), 2),
                "atm_put": round(float(iv_skew.get('atm_put', 0) or 0), 2),
                "skew": round(float(iv_skew.get('skew', 0) or 0), 2)
            },
            "spot_price": round(float(spot_price), 2),
            "atm_strike": option_chain.get('atm_strike'),
            "expiry": option_chain.get('expiry'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching options analytics for {symbol}: {e}")
        return {"available": False, "reason": str(e)}

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

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict:
    """Calculate Bollinger Bands with squeeze detection"""
    try:
        if len(prices) < period:
            return {"error": "Insufficient data"}
        
        prices = np.array(prices)
        current_price = prices[-1]
        
        # Calculate SMA and Standard Deviation
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        # Bollinger Bands
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        bandwidth = (upper_band - lower_band) / sma * 100  # As percentage
        
        # Position within bands (0 = lower, 100 = upper)
        band_position = ((current_price - lower_band) / (upper_band - lower_band) * 100) if (upper_band - lower_band) > 0 else 50
        
        # Squeeze detection (bandwidth < 4% is typically a squeeze)
        is_squeeze = bandwidth < 4.0
        
        # Historical bandwidth for context
        historical_bandwidths = []
        for i in range(min(10, len(prices) - period)):
            hist_sma = np.mean(prices[-(period+i):-(i) if i > 0 else None])
            hist_std = np.std(prices[-(period+i):-(i) if i > 0 else None])
            if hist_sma > 0:
                historical_bandwidths.append((2 * std_dev * hist_std) / hist_sma * 100)
        
        avg_bandwidth = np.mean(historical_bandwidths) if historical_bandwidths else bandwidth
        squeeze_intensity = max(0, 1 - (bandwidth / avg_bandwidth)) if avg_bandwidth > 0 else 0
        
        # Interpretation
        if current_price > upper_band:
            position_desc = "ABOVE_UPPER"
        elif current_price < lower_band:
            position_desc = "BELOW_LOWER"
        elif current_price > sma:
            position_desc = "UPPER_HALF"
        else:
            position_desc = "LOWER_HALF"
        
        return {
            "upper_band": round(upper_band, 2),
            "middle_band": round(sma, 2),
            "lower_band": round(lower_band, 2),
            "bandwidth": round(bandwidth, 2),
            "band_position": round(band_position, 1),
            "position": position_desc,
            "is_squeeze": is_squeeze,
            "squeeze_intensity": round(squeeze_intensity * 100, 1),
            "interpretation": "SQUEEZE" if is_squeeze else "NORMAL"
        }
        
    except Exception as e:
        return {"error": str(e)}

def calculate_garch_volatility(prices: List[float], period: int = 20) -> Dict:
    """Calculate GARCH(1,1) volatility estimation"""
    try:
        if len(prices) < period + 5:
            return {"error": "Insufficient data"}
        
        prices = np.array(prices)
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        if len(returns) < period:
            return {"error": "Insufficient returns data"}
        
        # GARCH(1,1) parameters (standard values)
        alpha = 0.10  # Weight for recent squared return
        beta = 0.85   # Weight for previous variance
        omega = np.var(returns) * (1 - alpha - beta)  # Long-run variance weight
        
        # GARCH recursion
        n = len(returns)
        variance = np.zeros(n)
        variance[0] = np.var(returns[:min(20, n)])
        
        for t in range(1, n):
            variance[t] = omega + alpha * (returns[t-1] ** 2) + beta * variance[t-1]
        
        # Current volatility (annualized for daily data, or intraday scaled)
        current_variance = variance[-1]
        current_volatility = np.sqrt(current_variance)
        
        # Annualized volatility (assuming 252 trading days)
        annualized_volatility = current_volatility * np.sqrt(252)
        
        # Historical volatility for comparison
        historical_volatility = np.std(returns[-period:]) * np.sqrt(252)
        
        # Volatility regime
        if annualized_volatility > 0.40:
            regime = "EXTREME"
        elif annualized_volatility > 0.25:
            regime = "HIGH"
        elif annualized_volatility > 0.15:
            regime = "NORMAL"
        else:
            regime = "LOW"
        
        # Volatility trend
        recent_vol = np.std(returns[-5:]) if len(returns) >= 5 else current_volatility
        older_vol = np.std(returns[-20:-5]) if len(returns) >= 20 else current_volatility
        vol_trend = "INCREASING" if recent_vol > older_vol * 1.1 else \
                   "DECREASING" if recent_vol < older_vol * 0.9 else "STABLE"
        
        return {
            "garch_volatility": round(annualized_volatility * 100, 2),
            "historical_volatility": round(historical_volatility * 100, 2),
            "current_daily_vol": round(current_volatility * 100, 3),
            "regime": regime,
            "trend": vol_trend,
            "interpretation": f"{regime} volatility, {vol_trend.lower()} trend"
        }
        
    except Exception as e:
        return {"error": str(e)}

def calculate_historical_volatility(prices: List[float], periods: List[int] = [5, 10, 20]) -> Dict:
    """Calculate Historical Volatility for multiple periods"""
    try:
        if len(prices) < max(periods) + 1:
            return {"error": "Insufficient data"}
        
        prices = np.array(prices)
        returns = np.diff(prices) / prices[:-1]
        
        result = {}
        for period in periods:
            if len(returns) >= period:
                period_vol = np.std(returns[-period:]) * np.sqrt(252) * 100  # Annualized %
                result[f"hv_{period}"] = round(period_vol, 2)
        
        # Current vs historical comparison
        if "hv_5" in result and "hv_20" in result:
            if result["hv_5"] > result["hv_20"] * 1.3:
                result["trend"] = "EXPANDING"
            elif result["hv_5"] < result["hv_20"] * 0.7:
                result["trend"] = "CONTRACTING"
            else:
                result["trend"] = "STABLE"
        else:
            result["trend"] = "UNKNOWN"
        
        return result
        
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
                            volume: Dict, sr_levels: Dict, current_price: float,
                            bollinger: Dict = None, garch: Dict = None) -> Dict:
    """Generate overall algorithm recommendation including volatility analysis"""
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
        
        # Bollinger Bands Analysis
        if bollinger and not bollinger.get("error"):
            total_signals += 1
            if bollinger.get("position") == "BELOW_LOWER":
                bullish_signals += 1.5
                reasons.append("Price below lower Bollinger band (oversold)")
            elif bollinger.get("position") == "ABOVE_UPPER":
                bearish_signals += 1.5
                reasons.append("Price above upper Bollinger band (overbought)")
            
            # Squeeze detection
            if bollinger.get("is_squeeze"):
                reasons.append(f"Bollinger squeeze ({bollinger.get('squeeze_intensity', 0):.0f}% intensity)")
        
        # GARCH Volatility Analysis
        if garch and not garch.get("error"):
            total_signals += 0.5  # Lower weight for volatility
            if garch.get("regime") == "EXTREME":
                bearish_signals += 0.5  # Extreme vol = caution
                reasons.append("Extreme volatility regime (caution)")
            elif garch.get("regime") == "LOW":
                bullish_signals += 0.3  # Low vol = potential breakout setup
                reasons.append("Low volatility (potential breakout)")
            
            if garch.get("trend") == "INCREASING":
                bearish_signals += 0.3
                reasons.append("Volatility increasing")
            elif garch.get("trend") == "DECREASING":
                bullish_signals += 0.3
                reasons.append("Volatility decreasing")
        
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
            
            # 🎯 NEW: Bollinger Bands
            analysis["indicators"]["bollinger"] = calculate_bollinger_bands(closes)
            
            # 🎯 NEW: GARCH Volatility
            analysis["indicators"]["garch"] = calculate_garch_volatility(closes)
            
            # 🎯 NEW: Historical Volatility (multiple periods)
            analysis["indicators"]["historical_volatility"] = calculate_historical_volatility(closes)

            analysis["support_resistance"] = calculate_support_resistance(
                highs, lows, closes, current_price
            )

            analysis["volume_analysis"] = calculate_volume_analysis(volumes, closes)
            
            # 🎯 NEW: Options Analytics (for indices only)
            analysis["options_analytics"] = await get_options_analytics(symbol)

            # Generate recommendation (including Bollinger and GARCH)
            analysis["recommendation"] = generate_recommendation(
                analysis["indicators"]["rsi"],
                analysis["indicators"]["vrsi"],
                analysis["indicators"]["mfi"],
                analysis["indicators"]["macd"],
                analysis["volume_analysis"],
                analysis["support_resistance"],
                current_price,
                bollinger=analysis["indicators"]["bollinger"],
                garch=analysis["indicators"]["garch"]
            )

            analysis["data_source"] = "historical"
            analysis["candles_analyzed"] = len(candles)
            
        else:
            # Limited analysis with just live data
            analysis["indicators"]["rsi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["vrsi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["mfi"] = {"value": None, "error": "No historical data"}
            analysis["indicators"]["macd"] = {"state": None, "error": "No historical data"}
            analysis["indicators"]["bollinger"] = {"error": "No historical data"}
            analysis["indicators"]["garch"] = {"error": "No historical data"}
            analysis["indicators"]["historical_volatility"] = {"error": "No historical data"}
            analysis["support_resistance"] = {"error": "No historical data"}
            analysis["volume_analysis"] = {"error": "No historical data"}
            # Still try to get options analytics even without historical data
            analysis["options_analytics"] = await get_options_analytics(symbol)
            analysis["recommendation"] = {
                "recommendation": "INSUFFICIENT_DATA",
                "confidence": 0,
                "error": "Historical data required for full analysis"
            }
        
        logger.info(f"✅ Analysis complete for {symbol}: {analysis['recommendation'].get('recommendation', 'N/A')}")

        # Convert numpy types to native Python types for JSON serialization
        analysis = convert_numpy_types(analysis)

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
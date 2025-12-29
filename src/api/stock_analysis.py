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
        
        # 🚨 2025-12-26 FIX: Don't block on stale is_connected flag
        # Check if kite client exists - that's enough to attempt API call
        # The API call will fail naturally if token is invalid
        if not getattr(zerodha_client, 'kite', None):
            logger.warning(f"Zerodha kite client not initialized - cannot fetch historical data for {symbol}")
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
                                   closes: List[float], current_price: float,
                                   prev_day_high: float = None, prev_day_low: float = None,
                                   prev_day_close: float = None) -> Dict:
    """
    Calculate Camarilla Pivot Points - BEST for Intraday Trading/Scalping.
    
    Uses PREVIOUS DAY's complete daily OHLC (not today's intraday range).
    Camarilla pivots are specifically designed for day trading with 8 precise levels.
    
    Strategy:
    - Price between L3 and H3: Range-bound, mean reversion trades
    - Break above H4: Strong bullish breakout - GO LONG
    - Break below L4: Strong bearish breakdown - GO SHORT
    """
    try:
        if len(closes) < 5:
            return {"error": "Insufficient data"}
        
        # Use PREVIOUS DAY's daily OHLC for professional Camarilla pivots
        if prev_day_high and prev_day_high > 0 and prev_day_low and prev_day_low > 0 and prev_day_close and prev_day_close > 0:
            prev_high = prev_day_high
            prev_low = prev_day_low
            prev_close = prev_day_close
            data_source = "previous_day_daily"
        else:
            # Fallback: estimate from historical candles (less accurate)
            prev_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            prev_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            prev_close = closes[-2] if len(closes) > 1 else closes[-1]
            data_source = "historical_estimate"
        
        # Calculate Camarilla Pivot Levels
        range_val = prev_high - prev_low
        
        # Resistance levels (H1 to H4)
        h4 = prev_close + range_val * 1.1 / 2   # Strong breakout level
        h3 = prev_close + range_val * 1.1 / 4   # Key resistance
        h2 = prev_close + range_val * 1.1 / 6   # Minor resistance
        h1 = prev_close + range_val * 1.1 / 12  # First resistance
        
        # Support levels (L1 to L4)
        l1 = prev_close - range_val * 1.1 / 12  # First support
        l2 = prev_close - range_val * 1.1 / 6   # Minor support
        l3 = prev_close - range_val * 1.1 / 4   # Key support
        l4 = prev_close - range_val * 1.1 / 2   # Strong breakdown level
        
        # Find nearest resistance/support from Camarilla levels
        all_resistance = [h1, h2, h3, h4]
        all_support = [l1, l2, l3, l4]
        
        nearest_resistance = None
        nearest_support = None
        
        for level in sorted(all_resistance):
            if level > current_price * 1.001:  # At least 0.1% above
                nearest_resistance = level
                break
        
        for level in sorted(all_support, reverse=True):
            if level < current_price * 0.999:  # At least 0.1% below
                nearest_support = level
                break
        
        # Price position relative to Camarilla levels
        if current_price > h4:
            position = "ABOVE_H4_BREAKOUT"
            signal = "STRONG_BULLISH"
        elif current_price > h3:
            position = "ABOVE_H3"
            signal = "BULLISH"
        elif current_price > h1:
            position = "ABOVE_H1"
            signal = "SLIGHTLY_BULLISH"
        elif current_price < l4:
            position = "BELOW_L4_BREAKDOWN"
            signal = "STRONG_BEARISH"
        elif current_price < l3:
            position = "BELOW_L3"
            signal = "BEARISH"
        elif current_price < l1:
            position = "BELOW_L1"
            signal = "SLIGHTLY_BEARISH"
        else:
            position = "BETWEEN_L1_H1"
            signal = "RANGE_BOUND"
        
        return {
            "type": "camarilla",
            "resistance": {
                "h4": round(h4, 2),  # Strong breakout level
                "h3": round(h3, 2),  # Key resistance
                "h2": round(h2, 2),  # Minor resistance
                "h1": round(h1, 2)   # First resistance
            },
            "support": {
                "l1": round(l1, 2),  # First support
                "l2": round(l2, 2),  # Minor support
                "l3": round(l3, 2),  # Key support
                "l4": round(l4, 2)   # Strong breakdown level
            },
            "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
            "nearest_support": round(nearest_support, 2) if nearest_support else None,
            "position": position,
            "signal": signal,
            "calculation_inputs": {
                "prev_high": round(prev_high, 2),
                "prev_low": round(prev_low, 2),
                "prev_close": round(prev_close, 2),
                "range": round(range_val, 2),
                "data_source": data_source
            },
            "trading_strategy": {
                "range_bound": f"Price between L3 ({round(l3, 2)}) and H3 ({round(h3, 2)})",
                "bullish_breakout": f"If breaks above H4 ({round(h4, 2)}) - GO LONG",
                "bearish_breakdown": f"If breaks below L4 ({round(l4, 2)}) - GO SHORT"
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

async def get_previous_day_ohlc(symbol: str) -> Dict:
    """
    Fetch PREVIOUS DAY's complete daily OHLC for Camarilla pivot calculation.
    Uses Zerodha API to get yesterday's daily candle.
    """
    try:
        zerodha_client = await get_zerodha_client()
        # 🚨 2025-12-26 FIX: Check kite client exists, not stale is_connected flag
        if not zerodha_client or not getattr(zerodha_client, 'kite', None):
            return {"error": "Zerodha not available"}
        
        symbol_upper = symbol.upper().strip()
        
        # Map index symbols
        index_map = {
            'NIFTY-I': ('NIFTY 50', 'NSE'), 'NIFTY': ('NIFTY 50', 'NSE'),
            'BANKNIFTY-I': ('NIFTY BANK', 'NSE'), 'BANKNIFTY': ('NIFTY BANK', 'NSE'),
            'FINNIFTY-I': ('NIFTY FIN SERVICE', 'NSE'), 'FINNIFTY': ('NIFTY FIN SERVICE', 'NSE'),
            'SENSEX-I': ('SENSEX', 'BSE'), 'SENSEX': ('SENSEX', 'BSE'),
        }
        
        zerodha_symbol, exchange = index_map.get(symbol_upper, (symbol_upper, 'NSE'))
        
        # Fetch last 5 daily candles (handles weekends/holidays)
        candles = await zerodha_client.get_historical_data(
            symbol=zerodha_symbol,
            interval='day',
            from_date=datetime.now() - timedelta(days=7),
            to_date=datetime.now(),
            exchange=exchange
        )
        
        if candles and len(candles) >= 2:
            # Get second-to-last candle (yesterday's complete daily candle)
            yesterday = candles[-2]
            logger.info(f"✅ Previous day OHLC for {symbol}: H={yesterday.get('high')}, L={yesterday.get('low')}, C={yesterday.get('close')}")
            return {
                "high": float(yesterday.get('high', 0)),
                "low": float(yesterday.get('low', 0)),
                "close": float(yesterday.get('close', 0)),
                "date": str(yesterday.get('date', ''))
            }
        
        return {"error": "Insufficient daily data"}
    except Exception as e:
        logger.error(f"Error fetching previous day OHLC for {symbol}: {e}")
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

def calculate_darvas_box(highs: List[float], lows: List[float], closes: List[float], 
                          volumes: List[float], current_price: float, lookback: int = 50) -> Dict:
    """
    REFINED Darvas Box with Intraday Micro Analysis
    
    Improvements over basic implementation:
    1. Multi-box detection (stacking boxes pattern)
    2. Box confirmation period (high must hold 3+ candles)
    3. Intraday micro boxes (recent 12 candles for 5min data = 1 hour)
    4. Box quality scoring
    5. False breakout detection
    6. Breakout retest detection
    7. Target projections using box height
    8. Volume profile at box levels
    """
    try:
        if len(highs) < 20 or len(lows) < 20:
            return {"error": "Insufficient data for Darvas Box"}
        
        # Use more data for better box detection
        data_len = min(lookback, len(highs))
        highs_arr = np.array(highs[-data_len:])
        lows_arr = np.array(lows[-data_len:])
        closes_arr = np.array(closes[-data_len:])
        volumes_arr = np.array(volumes[-data_len:]) if len(volumes) >= data_len else np.array(volumes[-len(volumes):])
        
        # ============= MULTI-BOX DETECTION =============
        # Find ALL valid boxes (not just most recent)
        boxes = []
        min_confirmation = 3  # Box high must hold for 3 candles (Darvas rule)
        
        i = 5
        while i < len(highs_arr) - 3:
            # Check if this is a swing high with confirmation
            window_before = highs_arr[max(0, i-5):i]
            window_after = highs_arr[i+1:min(i+4, len(highs_arr))]
            
            if len(window_before) > 0 and len(window_after) >= min_confirmation:
                is_swing_high = highs_arr[i] >= max(window_before)
                
                # Confirmation: next 3 candles don't exceed this high
                confirmed = all(highs_arr[i] >= h for h in window_after[:min_confirmation])
                
                if is_swing_high and confirmed:
                    box_top = float(highs_arr[i])
                    
                    # Find box bottom: lowest low until next breakout or 15 candles
                    search_end = min(i + 15, len(lows_arr))
                    box_bottom_range = lows_arr[i:search_end]
                    
                    if len(box_bottom_range) > 0:
                        box_bottom = float(min(box_bottom_range))
                        box_height = box_top - box_bottom
                        box_height_pct = (box_height / box_bottom * 100) if box_bottom > 0 else 0
                        
                        # Only count valid boxes (meaningful height)
                        if 0.3 <= box_height_pct <= 15:  # 0.3% to 15% range
                            boxes.append({
                                "top": box_top,
                                "bottom": box_bottom,
                                "height": box_height,
                                "height_pct": box_height_pct,
                                "start_idx": i,
                                "confirmation_candles": min_confirmation
                            })
                            i += 5  # Skip ahead after finding a box
                            continue
            i += 1
        
        # ============= PRIMARY BOX (Most Recent Valid Box) =============
        if boxes:
            primary_box = boxes[-1]  # Most recent
            box_top = primary_box["top"]
            box_bottom = primary_box["bottom"]
            box_height = primary_box["height"]
            box_height_pct = primary_box["height_pct"]
            box_start_idx = primary_box["start_idx"]
        else:
            # Fallback: simple recent range
            recent_highs = highs_arr[-15:]
            recent_lows = lows_arr[-15:]
            box_top = float(max(recent_highs))
            box_bottom = float(min(recent_lows))
            box_height = box_top - box_bottom
            box_height_pct = (box_height / box_bottom * 100) if box_bottom > 0 else 0
            box_start_idx = len(highs_arr) - 15
        
        box_midpoint = (box_top + box_bottom) / 2
        
        # ============= INTRADAY MICRO BOX =============
        # For 5-min data: last 12 candles = 1 hour micro structure
        micro_lookback = min(12, len(highs_arr))
        micro_highs = highs_arr[-micro_lookback:]
        micro_lows = lows_arr[-micro_lookback:]
        micro_volumes = volumes_arr[-micro_lookback:] if len(volumes_arr) >= micro_lookback else volumes_arr
        
        micro_box_top = float(max(micro_highs))
        micro_box_bottom = float(min(micro_lows))
        micro_box_height = micro_box_top - micro_box_bottom
        micro_box_height_pct = (micro_box_height / micro_box_bottom * 100) if micro_box_bottom > 0 else 0
        
        # Micro box position
        if current_price > micro_box_top:
            micro_position = "MICRO_BREAKOUT"
        elif current_price < micro_box_bottom:
            micro_position = "MICRO_BREAKDOWN"
        elif current_price >= (micro_box_top + micro_box_bottom) / 2:
            micro_position = "MICRO_UPPER"
        else:
            micro_position = "MICRO_LOWER"
        
        # ============= BOX STACKING ANALYSIS =============
        # Detect ascending/descending boxes pattern
        box_trend = "NEUTRAL"
        if len(boxes) >= 2:
            recent_boxes = boxes[-3:]  # Last 3 boxes
            tops = [b["top"] for b in recent_boxes]
            bottoms = [b["bottom"] for b in recent_boxes]
            
            # Ascending: each box higher than previous
            if all(tops[i] < tops[i+1] for i in range(len(tops)-1)):
                box_trend = "ASCENDING"
            elif all(tops[i] > tops[i+1] for i in range(len(tops)-1)):
                box_trend = "DESCENDING"
            # Check for stair-step pattern
            elif len(recent_boxes) >= 2 and bottoms[-1] > bottoms[-2]:
                box_trend = "STEPPING_UP"
            elif len(recent_boxes) >= 2 and tops[-1] < tops[-2]:
                box_trend = "STEPPING_DOWN"
        
        # ============= CURRENT POSITION & BREAKOUT ANALYSIS =============
        breakout_pct = 0
        breakout_confirmed = False
        
        if current_price > box_top:
            position = "BREAKOUT"
            breakout_pct = ((current_price - box_top) / box_top * 100) if box_top > 0 else 0
            # Confirmed if breakout > 0.5% beyond box top
            breakout_confirmed = breakout_pct >= 0.5
        elif current_price < box_bottom:
            position = "BREAKDOWN"
            breakout_pct = ((box_bottom - current_price) / box_bottom * 100) if box_bottom > 0 else 0
            breakout_confirmed = breakout_pct >= 0.5
        elif current_price >= box_midpoint:
            position = "UPPER_HALF"
        else:
            position = "LOWER_HALF"
        
        # ============= BREAKOUT RETEST DETECTION =============
        # Check if price broke out then came back to test box top
        is_retest = False
        retest_holding = False
        if position in ["BREAKOUT", "UPPER_HALF"] and len(closes_arr) >= 5:
            recent_closes = closes_arr[-5:]
            # Was above box top, now near it
            was_above = any(c > box_top * 1.005 for c in recent_closes[:-1])
            near_top = abs(current_price - box_top) / box_top < 0.01  # Within 1%
            is_retest = was_above and near_top
            retest_holding = is_retest and current_price >= box_top
        
        # ============= VOLUME ANALYSIS =============
        avg_volume = float(np.mean(volumes_arr)) if len(volumes_arr) > 0 else 0
        recent_volume = float(volumes_arr[-1]) if len(volumes_arr) > 0 else 0
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        volume_surge = volume_ratio > 1.5
        volume_extreme = volume_ratio > 2.5
        
        # Volume at breakout levels
        breakout_volume_score = 0
        if position == "BREAKOUT":
            breakout_volume_score = min(100, volume_ratio * 40)
        elif position == "BREAKDOWN":
            breakout_volume_score = min(100, volume_ratio * 40)
        
        # ============= BOX QUALITY SCORE =============
        # Rate the quality of box formation
        quality_score = 50  # Base
        
        # Tight consolidation is better (lower volatility in box)
        if box_height_pct < 2:
            quality_score += 20
        elif box_height_pct < 4:
            quality_score += 10
        elif box_height_pct > 8:
            quality_score -= 15
        
        # Longer consolidation is better
        box_age = len(highs_arr) - box_start_idx if box_start_idx else 0
        if box_age >= 15:
            quality_score += 15
        elif box_age >= 8:
            quality_score += 8
        elif box_age < 4:
            quality_score -= 10
        
        # Multiple boxes = stronger pattern
        if len(boxes) >= 3:
            quality_score += 10
        
        # Ascending boxes = bullish trend
        if box_trend == "ASCENDING":
            quality_score += 10
        elif box_trend == "DESCENDING":
            quality_score -= 5  # Not necessarily bad for shorts
        
        quality_score = max(0, min(100, quality_score))
        
        # ============= SIGNAL DETERMINATION =============
        if position == "BREAKOUT" and volume_extreme and breakout_confirmed:
            signal = "STRONG_BUY"
            signal_strength = min(100, 80 + breakout_pct * 2 + (quality_score / 10))
        elif position == "BREAKOUT" and (volume_surge or breakout_confirmed):
            signal = "BUY"
            signal_strength = min(90, 65 + breakout_pct * 2 + (quality_score / 15))
        elif position == "BREAKOUT":
            signal = "WEAK_BUY"
            signal_strength = min(75, 55 + breakout_pct + (quality_score / 20))
        elif position == "BREAKDOWN" and volume_extreme and breakout_confirmed:
            signal = "STRONG_SELL"
            signal_strength = min(100, 80 + breakout_pct * 2 + (quality_score / 10))
        elif position == "BREAKDOWN" and (volume_surge or breakout_confirmed):
            signal = "SELL"
            signal_strength = min(90, 65 + breakout_pct * 2 + (quality_score / 15))
        elif position == "BREAKDOWN":
            signal = "WEAK_SELL"
            signal_strength = min(75, 55 + breakout_pct + (quality_score / 20))
        elif position == "UPPER_HALF" and retest_holding:
            signal = "RETEST_BUY"
            signal_strength = 70 + (quality_score / 20)
        elif position == "UPPER_HALF":
            signal = "WATCH_BREAKOUT"
            signal_strength = 50 + (quality_score / 25)
        else:
            signal = "WATCH_BREAKDOWN"
            signal_strength = 45
        
        # ============= TARGET PROJECTIONS =============
        # Classic Darvas: target = breakout point + box height
        target_1 = round(box_top + box_height, 2) if position in ["BREAKOUT", "UPPER_HALF"] else round(box_bottom - box_height, 2)
        target_2 = round(box_top + (box_height * 1.618), 2) if position in ["BREAKOUT", "UPPER_HALF"] else round(box_bottom - (box_height * 1.618), 2)
        
        # ============= CALCULATE DISTANCES =============
        distance_to_top = ((box_top - current_price) / current_price * 100) if current_price > 0 else 0
        distance_to_bottom = ((current_price - box_bottom) / current_price * 100) if current_price > 0 else 0
        
        is_tight_box = box_height_pct < 2.5
        
        return {
            # Primary box
            "box_top": round(box_top, 2),
            "box_bottom": round(box_bottom, 2),
            "box_midpoint": round(box_midpoint, 2),
            "box_height": round(box_height, 2),
            "box_height_pct": round(box_height_pct, 2),
            
            # Micro box (intraday)
            "micro_box_top": round(micro_box_top, 2),
            "micro_box_bottom": round(micro_box_bottom, 2),
            "micro_box_height_pct": round(micro_box_height_pct, 2),
            "micro_position": micro_position,
            
            # Multi-box analysis
            "boxes_detected": len(boxes),
            "box_trend": box_trend,
            
            # Current state
            "current_price": round(current_price, 2),
            "position": position,
            "signal": signal,
            "signal_strength": round(signal_strength, 1),
            
            # Breakout analysis
            "breakout_pct": round(breakout_pct, 2),
            "breakout_confirmed": breakout_confirmed,
            "is_retest": is_retest,
            "retest_holding": retest_holding,
            
            # Volume
            "volume_ratio": round(volume_ratio, 2),
            "volume_surge": volume_surge,
            "volume_extreme": volume_extreme,
            
            # Quality
            "box_quality_score": quality_score,
            "box_age_candles": box_age,
            "is_tight_consolidation": is_tight_box,
            
            # Distances
            "distance_to_top_pct": round(distance_to_top, 2),
            "distance_to_bottom_pct": round(distance_to_bottom, 2),
            
            # Targets
            "target_1": target_1,
            "target_2_fib": target_2,
            
            # Trading guidance
            "trading_hint": _get_darvas_trading_hint(position, signal, box_top, box_bottom, is_tight_box, 
                                                      retest_holding, box_trend, breakout_confirmed)
        }
        
    except Exception as e:
        return {"error": str(e)}

def _get_darvas_trading_hint(position: str, signal: str, box_top: float, box_bottom: float, 
                              is_tight: bool, retest_holding: bool = False, 
                              box_trend: str = "NEUTRAL", breakout_confirmed: bool = False) -> str:
    """Generate professional trading hint based on refined Darvas Box analysis"""
    
    if signal == "STRONG_BUY":
        return f"🚀 CONFIRMED BREAKOUT with volume explosion! BUY with SL at ₹{box_top:.2f}"
    elif signal == "BUY":
        hint = f"Breakout confirmed. BUY with SL at ₹{box_top:.2f}"
        if box_trend == "ASCENDING":
            hint += " (ASCENDING boxes = strong uptrend)"
        return hint
    elif signal == "WEAK_BUY":
        return f"Breakout without volume. Wait for pullback to ₹{box_top:.2f} or volume confirmation"
    elif signal == "RETEST_BUY":
        return f"📍 RETEST of breakout level holding! Good entry at ₹{box_top:.2f} with tight SL"
    elif signal == "STRONG_SELL":
        return f"⚠️ CONFIRMED BREAKDOWN with volume! EXIT/SHORT with SL at ₹{box_bottom:.2f}"
    elif signal == "SELL":
        return f"Breakdown confirmed. EXIT with SL at ₹{box_bottom:.2f}"
    elif signal == "WEAK_SELL":
        return f"Breakdown without volume. May be false - watch for recovery above ₹{box_bottom:.2f}"
    elif position == "UPPER_HALF":
        if is_tight:
            return f"Tight consolidation near resistance. Watch for breakout above ₹{box_top:.2f}"
        return f"In upper half of box. Resistance at ₹{box_top:.2f}"
    else:
        if is_tight:
            return f"Tight consolidation near support. Watch for breakdown below ₹{box_bottom:.2f}"
        return f"In lower half of box. Support at ₹{box_bottom:.2f}"

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
                            bollinger: Dict = None, garch: Dict = None, live_data: Dict = None,
                            darvas_box: Dict = None) -> Dict:
    """Generate overall algorithm recommendation including volatility analysis and Darvas Box"""
    try:
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        reasons = []

        # 🔥 BREAKOUT CONTEXT DETECTION
        # In breakout context, overbought indicators confirm momentum (not bearish)
        change_pct = live_data.get("change_percent", 0) if live_data else 0
        is_bullish_breakout = False
        is_bearish_breakout = False
        
        # Detect breakout from price momentum
        if change_pct > 5:
            is_bullish_breakout = True
        elif change_pct < -5:
            is_bearish_breakout = True
        
        # Detect breakout from Darvas Box
        if darvas_box and not darvas_box.get("error"):
            darvas_signal = darvas_box.get("signal", "")
            if darvas_signal in ["STRONG_BUY", "BUY"]:
                is_bullish_breakout = True
            elif darvas_signal in ["STRONG_SELL", "SELL"]:
                is_bearish_breakout = True

        # 🔥 INTRADAY PRICE MOMENTUM
        if abs(change_pct) > 5:
            total_signals += 2
            if change_pct > 10:
                bullish_signals += 3.0
                reasons.insert(0, f"STRONG BULLISH MOMENTUM: +{change_pct:.1f}% today")
            elif change_pct > 5:
                bullish_signals += 2.0
                reasons.insert(0, f"Strong bullish move: +{change_pct:.1f}% today")
            elif change_pct < -10:
                bearish_signals += 3.0
                reasons.insert(0, f"STRONG BEARISH MOMENTUM: {change_pct:.1f}% today")
            elif change_pct < -5:
                bearish_signals += 2.0
                reasons.insert(0, f"Strong bearish move: {change_pct:.1f}% today")

        # RSI Analysis - CONTEXT AWARE
        if rsi.get("value"):
            total_signals += 1
            rsi_val = rsi["value"]
            if rsi_val <= 30:
                bullish_signals += 1.5
                reasons.append(f"RSI oversold ({rsi_val:.1f})")
            elif rsi_val >= 70:
                # In bullish breakout, overbought RSI = momentum confirmation, not bearish
                if is_bullish_breakout:
                    bullish_signals += 0.5  # Slight bullish (momentum confirmed)
                    reasons.append(f"RSI overbought ({rsi_val:.1f}) - momentum confirmed")
                else:
                    bearish_signals += 1.5
                    reasons.append(f"RSI overbought ({rsi_val:.1f})")
            elif rsi_val < 50:
                bearish_signals += 0.5
            else:
                bullish_signals += 0.5
        
        # VRSI Analysis - CONTEXT AWARE
        if vrsi.get("value"):
            total_signals += 1
            vrsi_val = vrsi["value"]
            if vrsi_val <= 35:
                bullish_signals += 1
                reasons.append(f"🟢 VRSI oversold ({vrsi_val:.1f}) - volume supports bounce")
            elif vrsi_val >= 65:
                # In bullish breakout, high VRSI = strong volume momentum
                if is_bullish_breakout:
                    bullish_signals += 1.0  # Bullish (volume confirming breakout)
                    reasons.append(f"🟢 VRSI ({vrsi_val:.1f}) - volume confirming breakout")
                else:
                    # 🔧 2025-12-29: High VRSI without breakout = overbought on volume
                    bearish_signals += 1
                    reasons.append(f"🔴 VRSI overbought ({vrsi_val:.1f}) - volume exhaustion")
        
        # MFI Analysis - CONTEXT AWARE
        if mfi.get("value"):
            total_signals += 1
            mfi_val = mfi["value"]
            if mfi_val <= 20:
                bullish_signals += 1.5
                reasons.append(f"🟢 MFI oversold ({mfi_val:.1f}) - money flow reversal expected")
            elif mfi_val >= 80:
                # In bullish breakout, overbought MFI = strong money flow
                if is_bullish_breakout:
                    bullish_signals += 0.5  # Slight bullish (money flowing in)
                    reasons.append(f"🟢 MFI ({mfi_val:.1f}) - strong money inflow confirming breakout")
                else:
                    bearish_signals += 1.5
                    reasons.append(f"🔴 MFI overbought ({mfi_val:.1f}) - money flow exhaustion")
        
        # MACD Analysis (reduced weight - lagging indicator shouldn't override price action)
        # 🔧 2025-12-29: Check for DIVERGENCE - MACD lagging behind price action
        # If price has broken down but MACD is still bullish, that's a bearish divergence
        if macd.get("state"):
            total_signals += 1  # Reduced from 2 - MACD is lagging
            
            # Detect Darvas breakdown for divergence check
            darvas_signal = darvas_box.get("signal", "") if darvas_box else ""
            darvas_position = darvas_box.get("position", "") if darvas_box else ""
            is_darvas_breakdown = darvas_signal in ["SELL", "STRONG_SELL", "WEAK_SELL"] or darvas_position == "BREAKDOWN"
            is_darvas_breakout = darvas_signal in ["BUY", "STRONG_BUY", "WEAK_BUY"] or darvas_position == "BREAKOUT"
            
            if macd["state"] == "STRONG_BULLISH":
                if is_darvas_breakdown:
                    # 🔧 DIVERGENCE: MACD bullish but price broke down = lagging indicator
                    bearish_signals += 0.5  # Actually slightly bearish - MACD will catch up
                    reasons.append("⚠️ MACD bullish DIVERGENCE (lagging behind breakdown)")
                else:
                    bullish_signals += 1.5
                    reasons.append("🟢 MACD strong bullish")
            elif macd["state"] == "BULLISH":
                if is_darvas_breakdown:
                    # Divergence - don't add bullish weight
                    reasons.append("⚠️ MACD bullish (lagging - price already broke down)")
                else:
                    bullish_signals += 0.75
                    reasons.append("🟢 MACD bullish")
            elif macd["state"] == "STRONG_BEARISH":
                if is_darvas_breakout:
                    # MACD bearish but price broke out = lagging
                    bullish_signals += 0.5
                    reasons.append("⚠️ MACD bearish DIVERGENCE (lagging behind breakout)")
                else:
                    bearish_signals += 1.5
                    reasons.append("🔴 MACD strong bearish")
            elif macd["state"] == "BEARISH":
                if is_darvas_breakout:
                    reasons.append("⚠️ MACD bearish (lagging - price already broke out)")
                else:
                    bearish_signals += 0.75
                    reasons.append("🔴 MACD bearish")
            
            if macd.get("crossover") == "BULLISH_CROSSOVER":
                if not is_darvas_breakdown:  # Only count if not contradicting
                    bullish_signals += 0.75
                    reasons.append("🟢 MACD bullish crossover")
            elif macd.get("crossover") == "BEARISH_CROSSOVER":
                if not is_darvas_breakout:  # Only count if not contradicting
                    bearish_signals += 0.75
                    reasons.append("🔴 MACD bearish crossover")
        
        # Volume Analysis
        # 🔧 2025-12-29: Buy/sell pressure is based on 20 candles (lagging)
        # If price action contradicts, note the divergence instead
        if volume.get("buy_pressure"):
            total_signals += 1
            if volume["buy_pressure"] > 65:
                # Check if this contradicts bearish breakdown
                if is_bearish_breakout or change_pct < -2:
                    # High buy pressure but price falling = selling pressure now dominating
                    bearish_signals += 0.5
                    reasons.append(f"🔴 Buy pressure WAS high ({volume['buy_pressure']}%) but price now falling")
                else:
                    bullish_signals += 1
                    reasons.append(f"🟢 High buying pressure ({volume['buy_pressure']}%)")
            elif volume["sell_pressure"] > 65:
                # Check if this contradicts bullish breakout
                if is_bullish_breakout or change_pct > 2:
                    bullish_signals += 0.5
                    reasons.append(f"🟢 Sell pressure WAS high ({volume['sell_pressure']}%) but price now rising")
                else:
                    bearish_signals += 1
                    reasons.append(f"🔴 High selling pressure ({volume['sell_pressure']}%)")
        
        # S/R Position with Camarilla breakout detection
        if sr_levels.get("position"):
            total_signals += 2  # Camarilla is important for intraday, weight it higher
            
            # 🚀 CRITICAL: Camarilla H4 breakout = STRONG BULLISH signal
            if sr_levels["position"] == "ABOVE_H4_BREAKOUT":
                bullish_signals += 2.5  # Strong bullish weight for H4 breakout
                reasons.append("STRONG BULLISH: H4 breakout (Camarilla)")
            # 📉 CRITICAL: Camarilla L4 breakdown = STRONG BEARISH signal
            elif sr_levels["position"] == "BELOW_L4_BREAKDOWN":
                bearish_signals += 2.5  # Strong bearish weight for L4 breakdown
                reasons.append("STRONG BEARISH: L4 breakdown (Camarilla)")
            # Near support = potential bounce
            elif sr_levels["position"] == "BELOW_S1":
                bullish_signals += 0.5
                reasons.append("Price near support levels")
            # Near resistance = potential rejection
            elif sr_levels["position"] == "ABOVE_R1":
                bearish_signals += 0.5
                reasons.append("Price near resistance levels")
            # Range-bound between L3-H3
            elif "BETWEEN" in sr_levels["position"]:
                # Neutral - no strong directional bias
                bullish_signals += 0.5
                bearish_signals += 0.5
        
        # Bollinger Bands Analysis - CONTEXT AWARE
        if bollinger and not bollinger.get("error"):
            total_signals += 1
            if bollinger.get("position") == "BELOW_LOWER":
                # In bearish breakout, below lower band confirms momentum
                if is_bearish_breakout:
                    bearish_signals += 0.5
                    reasons.append("Price below lower Bollinger (breakdown confirmed)")
                else:
                    bullish_signals += 1.5
                    reasons.append("Price below lower Bollinger band (oversold)")
            elif bollinger.get("position") == "ABOVE_UPPER":
                # In bullish breakout, above upper band = momentum, not overbought
                if is_bullish_breakout:
                    bullish_signals += 0.5
                    reasons.append("Price above upper Bollinger (breakout momentum)")
                else:
                    bearish_signals += 1.5
                    reasons.append("Price above upper Bollinger band (overbought)")
            
            # Squeeze detection
            if bollinger.get("is_squeeze"):
                reasons.append(f"Bollinger squeeze ({bollinger.get('squeeze_intensity', 0):.0f}% intensity)")
        
        # GARCH Volatility Analysis
        # 🔧 2025-12-29: Volatility is direction-agnostic - don't add directional bias
        # Low volatility means potential breakout (UP or DOWN), not necessarily bullish
        if garch and not garch.get("error"):
            total_signals += 0.5  # Lower weight for volatility
            if garch.get("regime") == "EXTREME":
                bearish_signals += 0.5  # Extreme vol = caution
                reasons.append("Extreme volatility regime (caution)")
            elif garch.get("regime") == "LOW":
                # 🔧 FIX: Don't add bullish bias for low volatility - it's neutral
                reasons.append("Low volatility (potential breakout)")
            
            if garch.get("trend") == "INCREASING":
                bearish_signals += 0.3
                reasons.append("Volatility increasing")
            elif garch.get("trend") == "DECREASING":
                # 🔧 FIX: Don't add bullish bias for decreasing vol - it's neutral
                reasons.append("Volatility decreasing")
        
        # 📦 Darvas Box Analysis - Important for breakout/breakdown detection
        if darvas_box and not darvas_box.get("error"):
            total_signals += 1.5  # Darvas Box is important for trend confirmation
            signal = darvas_box.get("signal", "")
            position = darvas_box.get("position", "")
            volume_surge = darvas_box.get("volume_surge", False)
            signal_strength = darvas_box.get("signal_strength", 50) / 100  # Normalize to 0-1
            
            # 🔧 2025-12-29: Use max(base, scaled) to ensure minimum weight for confirmed signals
            # Confirmed breakout/breakdown should have minimum weight regardless of signal_strength
            if signal == "STRONG_BUY":
                weight = max(2.0, 2.0 * signal_strength)  # Minimum 2.0
                bullish_signals += weight
                reasons.append(f"Darvas Box BREAKOUT with volume (strength: {darvas_box.get('signal_strength', 0):.0f}%)")
            elif signal == "BUY":
                weight = max(1.5, 1.5 * signal_strength)  # Minimum 1.5
                bullish_signals += weight
                reasons.append(f"Darvas Box breakout (strength: {darvas_box.get('signal_strength', 0):.0f}%)")
            elif signal == "STRONG_SELL":
                weight = max(2.5, 2.0 * signal_strength)  # Minimum 2.5 - breakdown is more urgent
                bearish_signals += weight
                reasons.append(f"Darvas Box BREAKDOWN with volume (strength: {darvas_box.get('signal_strength', 0):.0f}%)")
            elif signal == "SELL":
                weight = max(2.0, 1.5 * signal_strength)  # Minimum 2.0 - breakdown is confirmed
                bearish_signals += weight
                reasons.append(f"Darvas Box breakdown (strength: {darvas_box.get('signal_strength', 0):.0f}%)")
            elif position == "UPPER_HALF":
                bullish_signals += 0.5
                reasons.append("Darvas Box: Price in upper half (watch for breakout)")
            elif position == "LOWER_HALF":
                bearish_signals += 0.5
                reasons.append("Darvas Box: Price in lower half (watch for breakdown)")
            
            # Tight consolidation = potential explosive move
            if darvas_box.get("is_tight_consolidation"):
                reasons.append("Darvas Box: Tight consolidation (potential explosive move)")
        
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
            
            # 🎯 Historical Volatility (multiple periods)
            analysis["indicators"]["historical_volatility"] = calculate_historical_volatility(closes)
            
            # 🎯 Darvas Box Analysis
            analysis["darvas_box"] = calculate_darvas_box(highs, lows, closes, volumes, current_price)

            # 🎯 Camarilla Pivots - Fetch yesterday's DAILY candle for professional intraday pivots
            prev_day_ohlc = await get_previous_day_ohlc(symbol)
            
            if "error" not in prev_day_ohlc:
                # Use proper previous day's daily OHLC
                analysis["support_resistance"] = calculate_support_resistance(
                    highs, lows, closes, current_price,
                    prev_day_high=prev_day_ohlc.get("high"),
                    prev_day_low=prev_day_ohlc.get("low"),
                    prev_day_close=prev_day_ohlc.get("close")
                )
                logger.info(f"✅ Camarilla pivots for {symbol} using {prev_day_ohlc.get('date')}")
            else:
                # Fallback to historical estimate
                logger.warning(f"⚠️ Using historical estimate for {symbol}: {prev_day_ohlc.get('error')}")
                analysis["support_resistance"] = calculate_support_resistance(
                    highs, lows, closes, current_price
                )

            analysis["volume_analysis"] = calculate_volume_analysis(volumes, closes)
            
            # 🎯 NEW: Options Analytics (for indices only)
            analysis["options_analytics"] = await get_options_analytics(symbol)

            # Generate recommendation (including Bollinger and GARCH and live_data for price momentum)
            analysis["recommendation"] = generate_recommendation(
                analysis["indicators"]["rsi"],
                analysis["indicators"]["vrsi"],
                analysis["indicators"]["mfi"],
                analysis["indicators"]["macd"],
                analysis["volume_analysis"],
                analysis["support_resistance"],
                current_price,
                bollinger=analysis["indicators"]["bollinger"],
                garch=analysis["indicators"]["garch"],
                live_data=live_data,
                darvas_box=analysis.get("darvas_box")
            )

            analysis["data_source"] = "historical"
            analysis["candles_analyzed"] = len(candles)
            
            # Include OHLC candles for frontend charting (last 100 candles for performance)
            chart_candles = candles[-100:] if len(candles) > 100 else candles
            analysis["chart_data"] = [
                {
                    "time": c.get('date', c.get('timestamp', '')),
                    "open": float(c.get('open', 0)),
                    "high": float(c.get('high', 0)),
                    "low": float(c.get('low', 0)),
                    "close": float(c.get('close', 0)),
                    "volume": int(c.get('volume', 0))
                }
                for c in chart_candles
            ]
            
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
            analysis["chart_data"] = []
            analysis["darvas_box"] = {"error": "No historical data"}
        
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
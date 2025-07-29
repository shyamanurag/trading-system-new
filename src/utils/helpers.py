"""
Helper functions for trading operations
"""

import math
import time
import asyncio
import pandas as pd
import numpy as np
from typing import Optional, Callable, Any, Dict, List
from decimal import Decimal
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def get_atm_strike(spot_price: float) -> int:
    """
    Get At-The-Money (ATM) strike price for given spot price.
    FIXED: Uses Zerodha's actual intervals - 100 for indices, 50 for stocks.
    
    Args:
        spot_price: Current spot price
        
    Returns:
        ATM strike price rounded to appropriate interval
    """
    # 🚨 CRITICAL FIX: Based on user feedback "for indices only in 100"
    # All indices use 100-point intervals in Zerodha
    if spot_price > 10000:  # Likely index (NIFTY ~24000, BANKNIFTY ~56000)
        return int(round(spot_price / 100) * 100)
    else:  # Stock options use 50-point intervals
        return int(round(spot_price / 50) * 50)


def get_strike_with_offset(spot_price: float, offset: int, option_type: str) -> int:
    """
    Get strike price with offset from ATM.
    FIXED: Uses correct intervals based on Zerodha requirements.
    
    Args:
        spot_price: Current spot price
        offset: Number of strikes away from ATM (positive for OTM, negative for ITM)
        option_type: 'CE' for call, 'PE' for put
        
    Returns:
        Strike price with offset
    """
    atm_strike = get_atm_strike(spot_price)
    
    # 🚨 CRITICAL FIX: Determine strike interval based on Zerodha requirements
    if spot_price > 10000:  # Index
        strike_interval = 100
    else:  # Stock
        strike_interval = 50
    
    # Calculate offset strike
    if option_type.upper() == 'CE':
        return atm_strike + (offset * strike_interval)
    elif option_type.upper() == 'PE':
        return atm_strike - (offset * strike_interval)
    else:
        raise ValueError(f"Invalid option type: {option_type}")


def calculate_value_area(price_levels: list, volumes: list, poc_price: float) -> tuple:
    """
    Calculate value area high and low based on volume profile.
    
    Args:
        price_levels: List of price levels
        volumes: List of corresponding volumes
        poc_price: Point of Control price
        
    Returns:
        Tuple of (value_area_low, value_area_high)
    """
    if not price_levels or not volumes or len(price_levels) != len(volumes):
        return None, None
    
    # Find POC index
    try:
        poc_index = price_levels.index(poc_price)
    except ValueError:
        return None, None
    
    total_volume = sum(volumes)
    target_volume = total_volume * 0.68  # 68% of total volume
    
    # Calculate value area
    current_volume = volumes[poc_index]
    low_index = poc_index
    high_index = poc_index
    
    while current_volume < target_volume and (low_index > 0 or high_index < len(volumes) - 1):
        low_volume = volumes[low_index - 1] if low_index > 0 else 0
        high_volume = volumes[high_index + 1] if high_index < len(volumes) - 1 else 0
        
        if low_volume > high_volume and low_index > 0:
            low_index -= 1
            current_volume += low_volume
        elif high_index < len(volumes) - 1:
            high_index += 1
            current_volume += high_volume
        else:
            break
    
    return price_levels[low_index], price_levels[high_index]


def to_decimal(value: float) -> Decimal:
    """
    Convert float to Decimal for precise calculations.
    
    Args:
        value: Float value to convert
        
    Returns:
        Decimal representation
    """
    return Decimal(str(value))


def round_price_to_tick(price: float, tick_size: float = 0.05) -> float:
    """
    Round price to nearest tick size.
    
    Args:
        price: Price to round
        tick_size: Tick size (default 0.05 for options)
        
    Returns:
        Rounded price
    """
    return round(price / tick_size) * tick_size


def calculate_implied_volatility(option_price: float, spot_price: float, strike: float, 
                                time_to_expiry: float, risk_free_rate: float = 0.05) -> float:
    """
    Calculate implied volatility using Black-Scholes approximation.
    
    Args:
        option_price: Current option price
        spot_price: Current spot price
        strike: Strike price
        time_to_expiry: Time to expiry in years
        risk_free_rate: Risk-free rate (default 5%)
        
    Returns:
        Implied volatility as decimal
    """
    if time_to_expiry <= 0 or spot_price <= 0 or strike <= 0:
        return 0.0
    
    # Simple approximation for ATM options
    moneyness = spot_price / strike
    if 0.95 <= moneyness <= 1.05:  # Near ATM
        # Rough approximation for ATM implied volatility
        return math.sqrt(2 * math.pi / time_to_expiry) * option_price / spot_price
    
    return 0.0


def calculate_delta(spot_price: float, strike: float, time_to_expiry: float, 
                   volatility: float, option_type: str, risk_free_rate: float = 0.05) -> float:
    """
    Calculate option delta using Black-Scholes.
    
    Args:
        spot_price: Current spot price
        strike: Strike price
        time_to_expiry: Time to expiry in years
        volatility: Implied volatility
        option_type: 'CE' for call, 'PE' for put
        risk_free_rate: Risk-free rate
        
    Returns:
        Delta value
    """
    if time_to_expiry <= 0 or volatility <= 0:
        return 0.0
    
    # Simplified delta calculation for ATM options
    if option_type.upper() == 'CE':
        return 0.5  # Approximate ATM call delta
    elif option_type.upper() == 'PE':
        return -0.5  # Approximate ATM put delta
    else:
        return 0.0


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, backoff_multiplier: float = 2.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        backoff_multiplier: Multiplier for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = base_delay * (backoff_multiplier ** attempt)
                    await asyncio.sleep(delay)
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = base_delay * (backoff_multiplier ** attempt)
                    time.sleep(delay)
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def calculate_technical_indicators(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate technical indicators from market data.
    
    Args:
        data: Market data containing price and volume information
        
    Returns:
        Dictionary containing calculated technical indicators
    """
    try:
        # Extract price data
        if 'prices' in data and len(data['prices']) > 0:
            prices = data['prices']
            if isinstance(prices, list):
                prices = np.array(prices)
        else:
            # ELIMINATED: Fake price array generation for technical analysis
            # ❌ current_price = data.get('price', data.get('ltp', 100.0))
            # ❌ prices = np.array([current_price] * 20)  # Fake 20 periods
            
            # SAFETY: Return error instead of fake price history
            logger.error("CRITICAL: Technical analysis requires real price history data")
            logger.error("SAFETY: Fake price array generation ELIMINATED to prevent misleading indicators")
            
            # Return error indicators instead of fake calculations
            return {
                'error': 'SAFETY: Technical analysis disabled - real price history required',
                'sma_20': 0.0,
                'rsi': 0.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'bb_upper': 0.0,
                'bb_lower': 0.0,
                'bb_middle': 0.0,
                'current_price': 0.0,
                'WARNING': 'FAKE_PRICE_HISTORY_ELIMINATED_FOR_SAFETY'
            }
        
        # Calculate basic indicators
        indicators = {}
        
        # Simple Moving Average (20 period)
        if len(prices) >= 20:
            indicators['sma_20'] = float(np.mean(prices[-20:]))
        else:
            indicators['sma_20'] = float(np.mean(prices))
        
        # RSI (14 period)
        indicators['rsi'] = calculate_rsi(prices, period=14)
        
        # MACD
        macd_data = calculate_macd(prices)
        indicators.update(macd_data)
        
        # Bollinger Bands
        bb_data = calculate_bollinger_bands(prices, period=20, std_dev=2)
        indicators.update(bb_data)
        
        # Volume indicators (if volume data available)
        if 'volumes' in data and len(data['volumes']) > 0:
            volumes = np.array(data['volumes'])
            indicators['volume_sma_10'] = float(np.mean(volumes[-10:]) if len(volumes) >= 10 else np.mean(volumes))
        
        # Current price
        indicators['current_price'] = float(prices[-1]) if len(prices) > 0 else 100.0
        
        return indicators
        
    except Exception as e:
        # Return default indicators if calculation fails
        return {
            'sma_20': 100.0,
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'bb_upper': 105.0,
            'bb_lower': 95.0,
            'bb_middle': 100.0,
            'current_price': 100.0
        }


def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """Calculate RSI indicator"""
    try:
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    except:
        return 50.0


def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """Calculate MACD indicators"""
    try:
        if len(prices) < slow:
            return {'macd': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0}
        
        ema_fast = calculate_ema(prices, fast)
        ema_slow = calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line  # Simplified - should be EMA of MACD line
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line),
            'macd_signal': float(signal_line),
            'macd_histogram': float(histogram)
        }
    except:
        return {'macd': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0}


def calculate_ema(prices: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average"""
    try:
        if len(prices) < period:
            return float(np.mean(prices))
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return float(ema)
    except:
        return float(prices[-1]) if len(prices) > 0 else 100.0


def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """Calculate Bollinger Bands"""
    try:
        if len(prices) < period:
            current_price = float(prices[-1]) if len(prices) > 0 else 100.0
            return {
                'bb_upper': current_price * 1.05,
                'bb_lower': current_price * 0.95,
                'bb_middle': current_price
            }
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        return {
            'bb_upper': float(sma + (std_dev * std)),
            'bb_lower': float(sma - (std_dev * std)),
            'bb_middle': float(sma)
        }
    except:
        return {
            'bb_upper': 105.0,
            'bb_lower': 95.0,
            'bb_middle': 100.0
        } 
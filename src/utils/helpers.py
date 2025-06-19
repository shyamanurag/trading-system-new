"""
Helper functions for trading operations
"""

import math
from typing import Optional
from decimal import Decimal


def get_atm_strike(spot_price: float) -> int:
    """
    Get At-The-Money (ATM) strike price for given spot price.
    Rounds to nearest 50 for NIFTY and 100 for BANKNIFTY.
    
    Args:
        spot_price: Current spot price
        
    Returns:
        ATM strike price rounded to appropriate interval
    """
    # For NIFTY, round to nearest 50
    if spot_price < 20000:  # Likely NIFTY
        return int(round(spot_price / 50) * 50)
    # For BANKNIFTY, round to nearest 100
    else:
        return int(round(spot_price / 100) * 100)


def get_strike_with_offset(spot_price: float, offset: int, option_type: str) -> int:
    """
    Get strike price with offset from ATM.
    
    Args:
        spot_price: Current spot price
        offset: Number of strikes away from ATM (positive for OTM, negative for ITM)
        option_type: 'CE' for call, 'PE' for put
        
    Returns:
        Strike price with offset
    """
    atm_strike = get_atm_strike(spot_price)
    
    # Determine strike interval based on price range
    if spot_price < 20000:  # NIFTY
        strike_interval = 50
    else:  # BANKNIFTY
        strike_interval = 100
    
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
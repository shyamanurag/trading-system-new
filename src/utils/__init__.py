# Trading System Utilities

def get_atm_strike(spot_price: float, strike_interval: float = None) -> float:
    """Get At-The-Money strike price with automatic interval detection"""
    if strike_interval is None:
        # Auto-detect interval based on Zerodha requirements
        if spot_price > 10000:  # Index
            strike_interval = 100.0
        else:  # Stock
            strike_interval = 50.0
    return round(spot_price / strike_interval) * strike_interval

def get_strike_with_offset(atm_strike: float, offset: int, strike_interval: float = None) -> float:
    """Get strike price with offset from ATM with automatic interval detection"""
    if strike_interval is None:
        # Auto-detect interval based on price level
        if atm_strike > 10000:  # Index
            strike_interval = 100.0
        else:  # Stock
            strike_interval = 50.0
    return atm_strike + (offset * strike_interval)
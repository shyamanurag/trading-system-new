"""
TrueData Symbol Mapping Configuration
Official symbol formats for TrueData API integration
"""

from typing import List

# Index symbols (use -I suffix for TrueData)
INDEX_SYMBOLS = {
    'NIFTY': 'NIFTY-I',
    'BANKNIFTY': 'BANKNIFTY-I', 
    'FINNIFTY': 'FINNIFTY-I',
    'MIDCPNIFTY': 'MIDCPNIFTY-I',
    'SENSEX': 'SENSEX-I'
}

# Equity symbols (direct format for TrueData)
EQUITY_SYMBOLS = {
    'RELIANCE': 'RELIANCE',
    'TCS': 'TCS',
    'HDFC': 'HDFC',
    'INFY': 'INFY',
    'ICICIBANK': 'ICICIBANK',
    'HDFCBANK': 'HDFCBANK',
    'ITC': 'ITC',
    'BHARTIARTL': 'BHARTIARTL',
    'KOTAKBANK': 'KOTAKBANK',
    'LT': 'LT'
}

# Complete symbol mapping
SYMBOL_MAPPING = {
    **INDEX_SYMBOLS,
    **EQUITY_SYMBOLS
}

# Default symbols to subscribe on connection
DEFAULT_SYMBOLS = [
    # Core Indices (Always include)
    'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
    
    # Top 10 F&O Stocks (Highest volume)
    'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
    'BHARTIARTL', 'KOTAKBANK', 'LT',
    
    # Next 20 High-volume F&O Stocks
    'SBIN', 'WIPRO', 'AXISBANK', 'MARUTI', 'ASIANPAINT', 'HCLTECH',
    'POWERGRID', 'NTPC', 'COALINDIA', 'TECHM', 'TATAMOTORS', 'ADANIPORTS',
    'ULTRACEMCO', 'NESTLEIND', 'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY',
    'SUNPHARMA', 'CIPLA',
    
    # Next 20 Medium-volume F&O Stocks  
    'APOLLOHOSP', 'DIVISLAB', 'HINDUNILVR', 'BRITANNIA', 'DABUR',
    'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'JSWSTEEL', 'TATASTEEL',
    'HINDALCO', 'VEDL', 'GODREJCP', 'BAJAJFINSV', 'BAJAJ-AUTO',
    'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'ASHOKLEY', 'MCDOWELL-N'
]

# TOP F&O STOCKS - Most liquid futures & options (for expansion)
TOP_FO_STOCKS = [
    'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
    'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
    'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
    'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND',
    'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA',
    'APOLLOHOSP', 'DIVISLAB', 'HINDUNILVR', 'BRITANNIA', 'DABUR',
    'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'JSWSTEEL', 'TATASTEEL',
    'HINDALCO', 'VEDL', 'GODREJCP', 'BAJAJFINSV', 'BAJAJ-AUTO',
    'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'ASHOKLEY', 'MCDOWELL-N'
]

# ADDITIONAL LIQUID STOCKS (for 250-symbol expansion)
LIQUID_STOCKS = [
    'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB',
    'CANBK', 'BANKBARODA', 'IOC', 'BPCL', 'ONGC', 'GAIL', 'OIL',
    'SAIL', 'NMDC', 'MOIL', 'NALCO', 'GRASIM', 'RAMCOCEM',
    'SHREECEM', 'ACC', 'AMBUJACEM', 'PIDILITIND', 'BERGER',
    'INDIGO', 'SPICEJET', 'IRCTC', 'CONCOR', 'ZOMATO', 'NYKAA',
    'IRFC', 'PAYTM', 'POLICYBZR', 'RBLBANK', 'YESBANK', 'IDEA',
    'BALKRISIND', 'APOLLOTYRE', 'MRF', 'CEAT', 'JK_TYRE',
    'ESCORTS', 'FORCE', 'TATAPOWER', 'TORNTPOWER', 'NHPC'
]

def get_truedata_symbol(standard_symbol: str) -> str:
    """Convert standard symbol to TrueData format"""
    return SYMBOL_MAPPING.get(standard_symbol, standard_symbol)

def get_display_name(truedata_symbol: str) -> str:
    """Get display name for TrueData symbol"""
    return DISPLAY_NAMES.get(truedata_symbol, truedata_symbol)

def get_default_subscription_symbols() -> list[str]:
    """Get the default symbols to subscribe to (50+ most liquid F&O)"""
    return DEFAULT_SYMBOLS.copy()

def get_complete_fo_symbols() -> list[str]:
    """Get complete F&O symbol pool for 250-symbol expansion"""
    expanded_symbols = DEFAULT_SYMBOLS.copy()
    
    # Add additional liquid stocks
    for symbol in LIQUID_STOCKS:
        if symbol not in expanded_symbols:
            expanded_symbols.append(symbol)
    
    # Ensure we don't exceed 250 symbols  
    return expanded_symbols[:250]

def enable_full_symbol_expansion() -> list[str]:
    """Enable full 250-symbol expansion by including all F&O stocks"""
    return get_complete_fo_symbols()

# Mapping for display names
DISPLAY_NAMES = {
    'NIFTY-I': 'NIFTY 50',
    'BANKNIFTY-I': 'BANK NIFTY',
    'FINNIFTY-I': 'FINNIFTY',
    'RELIANCE': 'RELIANCE',
    'TCS': 'TCS',
    'HDFC': 'HDFC BANK',
    'INFY': 'INFOSYS'
} 
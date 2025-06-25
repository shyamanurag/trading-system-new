"""
TrueData Symbol Mapping Configuration
Official symbol formats for TrueData API integration
"""

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
    'NIFTY-I',      # Nifty 50 Index
    'BANKNIFTY-I',  # Bank Nifty Index
    'RELIANCE',     # Reliance Industries
    'TCS',          # Tata Consultancy Services
    'HDFC',         # HDFC Bank
    'INFY'          # Infosys
]

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

def get_truedata_symbol(standard_symbol: str) -> str:
    """Convert standard symbol to TrueData format"""
    return SYMBOL_MAPPING.get(standard_symbol, standard_symbol)

def get_display_name(truedata_symbol: str) -> str:
    """Get display name for TrueData symbol"""
    return DISPLAY_NAMES.get(truedata_symbol, truedata_symbol)

def get_default_subscription_symbols() -> list:
    """Get list of default symbols to subscribe to"""
    return DEFAULT_SYMBOLS.copy() 
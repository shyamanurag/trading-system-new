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
    'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'INDIGO', 'SPICEJET'
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
    'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'INDIGO', 'SPICEJET'
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

def get_default_subscription_symbols():
    """Get default symbols for immediate subscription (50+ F&O symbols)"""
    return [
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
        'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'INDIGO', 'SPICEJET'
    ]

def get_complete_fo_symbols():
    """Get complete F&O symbol list (up to 250 symbols)"""
    base_symbols = get_default_subscription_symbols()
    
    # Additional F&O symbols for expansion to 250
    additional_symbols = [
        'INDUSINDBK', 'FEDERALBNK', 'BANKBARODA', 'PNB', 'CANBK',
        'YESBANK', 'BANDHANBNK', 'IDFCFIRSTB', 'AUBANK', 'RBLBANK',
        'BHARATFORG', 'BHEL', 'BEL', 'HAL', 'SAIL',
        'ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL',
        'NMDC', 'JINDALSTEL', 'NATIONALUM', 'MOIL', 'RATNAMANI',
        'ASHOKLEY', 'BALKRISIND', 'CESC', 'DLF', 'GODREJIND',
        'HAVELLS', 'IBULHSGFIN', 'LICHSGFIN', 'MFSL', 'MOTHERSUMI',
        'PAGEIND', 'PIDILITIND', 'RAMCOCEM', 'SHREECEM', 'SIEMENS',
        'TORNTPHARM', 'VOLTAS', 'WHIRLPOOL', 'ZEEL', 'AUROPHARMA',
        'BATINDIA', 'BERGEPAINT', 'CADILAHC', 'COLPAL', 'CONCOR',
        'CUMMINSIND', 'ESCORTS', 'EXIDEIND', 'GLENMARK', 'GRASIM',
        'GSPL', 'HINDPETRO', 'IPCALAB', 'JUBLFOOD', 'KAJARIACER',
        'KPITTECH', 'LALPATHLAB', 'LUPIN', 'MARICO', 'MGL',
        'MPHASIS', 'MRF', 'NAVINFLUOR', 'OFSS', 'PERSISTENT',
        'PETRONET', 'PFIZER', 'PIIND', 'PVR', 'RELAXO',
        'SBILIFE', 'SRTRANSFIN', 'STAR', 'SYNGENE', 'TATACHEM',
        'TATACOMM', 'TRENT', 'TVSMOTOR', 'UBL', 'UJJIVAN',
        'UPL', 'VOLTAS', 'WOCKPHARMA', 'ZYDUSLIFE'
    ]
    
    # Combine and limit to 250
    all_symbols = base_symbols + additional_symbols
    return all_symbols[:250]

# Override DEFAULT_SYMBOLS with expanded list
DEFAULT_SYMBOLS = get_default_subscription_symbols()

# Function to get symbol count for monitoring
def get_symbol_expansion_status():
    """Get current symbol expansion status"""
    default_count = len(get_default_subscription_symbols())
    complete_count = len(get_complete_fo_symbols())
    
    return {
        "default_symbols": default_count,
        "complete_symbols": complete_count,
        "expansion_ratio": f"{default_count}→{complete_count}",
        "target_reached": complete_count >= 250
    }

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
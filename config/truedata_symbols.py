"""
TrueData Symbol Mapping Configuration
Official symbol formats for TrueData API integration
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

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
    """Get complete F&O symbol list (EXPANDED TO FULL 250 symbols)"""
    base_symbols = get_default_subscription_symbols()
    
    # EXPANDED: Additional F&O symbols for 250 symbol capacity
    additional_symbols = [
        # Major Banks & Financial Services (15 symbols)
        'INDUSINDBK', 'FEDERALBNK', 'BANKBARODA', 'PNB', 'CANBK',
        'YESBANK', 'BANDHANBNK', 'IDFCFIRSTB', 'AUBANK', 'RBLBANK',
        'MUTHOOTFIN', 'MANAPPURAM', 'CHOLAFIN', 'BAJAJHLDNG', 'IIFL',
        
        # Energy & Oil (15 symbols)
        'ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL',
        'HINDPETRO', 'PETRONET', 'CASTROLIND', 'MRPL', 'GSPL',
        'ADANIGAS', 'IGL', 'MGL', 'ATGL', 'AEGISCHEM',
        
        # Metals & Mining (15 symbols)
        'NMDC', 'JINDALSTEL', 'NATIONALUM', 'MOIL', 'RATNAMANI',
        'BHARATFORG', 'BHEL', 'BEL', 'HAL', 'SAIL',
        'WELCORP', 'WELSPUNIND', 'HINDZINC', 'NALCO', 'COALINDIA',
        
        # Auto & Auto Components (15 symbols)  
        'ASHOKLEY', 'BALKRISIND', 'MOTHERSUMI', 'BOSCHLTD', 'EICHERMOT',
        'BAJAJ-AUTO', 'HEROMOTOCO', 'TVSMOTOR', 'ESCORTS', 'FORCEMOT',
        'MAHINDCIE', 'APOLLOTYRE', 'MRF', 'CEAT', 'BHARATGEAR',
        
        # IT & Technology (15 symbols)
        'MPHASIS', 'PERSISTENT', 'KPITTECH', 'LTTS', 'MINDTREE',
        'OFSS', 'CYIENT', 'ROLTA', 'ZENSAR', 'NELCO',
        'NIITTECH', 'INFIBEAM', 'JUSTDIAL', 'INFO', 'ONMOBILE',
        
        # Pharma & Healthcare (15 symbols)
        'BIOCON', 'CADILAHC', 'GLENMARK', 'LUPIN', 'TORNTPHARM',
        'AUROPHARMA', 'DRREDDY', 'SUNPHARMA', 'CIPLA', 'DIVISLAB',
        'PFIZER', 'ALKEM', 'AUROBINDO', 'LALPATHLAB', 'FORTIS',
        
        # Consumer Goods (15 symbols)
        'COLPAL', 'MARICO', 'GODREJCP', 'BATINDIA', 'DABUR',
        'HINDUNILVR', 'BRITANNIA', 'NESTLEIND', 'VBL', 'TATACONSUM',
        'EMAMILTD', 'JYOTHYLAB', 'DIXON', 'VOLTAS', 'WHIRLPOOL',
        
        # Construction & Real Estate (10 symbols)
        'DLF', 'GODREJPROP', 'PRESTIGE', 'SOBHA', 'BRIGADE',
        'PHOENIXLTD', 'OBEROIRLTY', 'MAHLIFE', 'SUNTECK', 'LODHA',
        
        # Textiles & Apparel (10 symbols)
        'RAYMOND', 'ADITYADHOAP', 'GRASIM', 'WELSPUNIND', 'TRIDENT',
        'VARDHMANTEXT', 'ARVIND', 'SPENCERS', 'SHOPPERSSTOP', 'TRENT',
        
        # Infrastructure & Power (10 symbols)
        'ADANIPOWER', 'NTPC', 'POWERGRID', 'TORNTPOWER', 'CESC',
        'JSWENERGY', 'ADANIGREEN', 'SUZLON', 'ORIENTELEC', 'THERMAX',
        
        # Chemicals & Fertilizers (10 symbols)
        'UPL', 'PI', 'AARTI', 'DEEPAKNTR', 'BALRAMCHIN',
        'TATACHEM', 'CHAMBLFERT', 'COROMANDEL', 'KANSAINER', 'NAVINFLUOR',
        
        # Aviation & Logistics (10 symbols)
        'INDIGO', 'SPICEJET', 'CONCOR', 'GATI', 'MAHLOG',
        'BLUEDART', 'DTDC', 'TCI', 'VTL', 'SNOWMAN',
        
        # Media & Entertainment (10 symbols)
        'ZEEL', 'SUNTV', 'PVRINOX', 'INOXLEISUR', 'EROS',
        'BALAJITELE', 'TVTODAY', 'JAGRAN', 'HT', 'NAVNETEDUL',
        
        # Retail & E-commerce (10 symbols)
        'DMART', 'JUBLFOOD', 'WESTLIFE', 'SPECIALITY', 'KAJARIACER',
        'RELAXO', 'BATA', 'PAGEIND', 'PIDILITIND', 'ASTRAZEN',
        
        # Diversified (5 symbols)
        'SIEMENS', 'ABB', 'HONAUT', 'STAR', 'SYNGENE'
    ]
    
    # Combine and ensure we reach 250 symbols
    all_symbols = base_symbols + additional_symbols
    
    # If still under 250, add more liquid F&O stocks
    if len(all_symbols) < 250:
        extra_symbols = [
            'RAMCOCEM', 'SHREECEM', 'ULTRACEMCO', 'AMBUJACAM', 'ACC',
            'JKCEMENT', 'HEIDELBERG', 'PRISMCEM', 'JKLAKSHMI', 'ORIENT',
            'HAVELLS', 'CROMPTON', 'POLYCAB', 'KEI', 'FINOLEX',
            'EXIDEIND', 'AMARAJABAT', 'AMETEK', 'EVEREADY', 'HEG'
        ]
        all_symbols.extend(extra_symbols)
    
    # Return exactly 250 symbols
    final_symbols = all_symbols[:250]
    
    # Log the expansion for monitoring
    logger.info(f"🚀 EXPANDED F&O SYMBOLS: Generated {len(final_symbols)} symbols for trading")
    
    return final_symbols

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
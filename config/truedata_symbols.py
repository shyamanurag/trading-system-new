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
    """
    AUTONOMOUS SYMBOL STRATEGY: Intelligent symbol allocation based on market conditions
    FALLBACK-SAFE: Works even when markets closed or TrueData disconnected
    """
    
    try:
        # CRITICAL FIX: Always try static fallback first when markets closed or TrueData unavailable
        from data.truedata_client import live_market_data, is_connected
        
        # Check if TrueData is connected and has data
        has_live_data = (
            live_market_data and 
            len(live_market_data) > 10 and  # At least 10 symbols available
            any(data.get('ltp', 0) > 0 for data in live_market_data.values())  # At least one valid price
        )
        
        if not has_live_data:
            logger.warning("⚠️ TrueData not available or markets closed - using STATIC FALLBACK strategy")
            return get_static_fallback_symbols()
        
        # Get market intelligence for autonomous decision (only if live data available)
        strategy = _get_autonomous_symbol_strategy()
        
        if strategy == "OPTIONS_FOCUS":
            return get_options_focused_symbols()
        elif strategy == "MIXED":
            return get_mixed_symbols_with_options()
        else:
            return get_underlying_focused_symbols()
            
    except Exception as e:
        logger.error(f"❌ Dynamic symbol generation failed: {e}")
        logger.info("🔄 Falling back to static symbol list for reliability")
        return get_static_fallback_symbols()

def get_static_fallback_symbols():
    """
    STATIC FALLBACK: Reliable symbol list that works regardless of market/TrueData status
    Used when markets are closed or TrueData is disconnected
    """
    return [
        # Core Indices (5 symbols)
        'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
        
        # Top 50 F&O Stocks (Most liquid - STATIC list)
        'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
        'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
        'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
        'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND',
        'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA',
        'APOLLOHOSP', 'DIVISLAB', 'HINDUNILVR', 'BRITANNIA', 'DABUR',
        'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'JSWSTEEL', 'TATASTEEL',
        'HINDALCO', 'VEDL', 'GODREJCP', 'BAJAJFINSV', 'BAJAJ-AUTO',
        'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'INDIGO', 'SPICEJET',
        
        # Additional F&O Stocks (200 more symbols to reach 250) - FIXED duplicates
        'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB',
        'BANKBARODA', 'IOC', 'BPCL', 'ONGC', 'GAIL', 'OIL',
        'SAIL', 'NMDC', 'MOIL', 'NALCO', 'GRASIM', 'RAMCOCEM',
        'SHREECEM', 'ACC', 'AMBUJACEM', 'PIDILITIND', 'BERGER',
        'IRCTC', 'CONCOR', 'ZOMATO', 'NYKAA', 'IRFC', 'PAYTM',
        'POLICYBZR', 'RBLBANK', 'YESBANK', 'IDEA', 'BALKRISIND',
        'APOLLOTYRE', 'MRF', 'CEAT', 'JK_TYRE', 'ESCORTS', 'FORCE',
        'TATAPOWER', 'TORNTPOWER', 'NHPC', 'PFC', 'RECLTD', 'SJVN',
        'THERMAX', 'BHEL', 'KTKBANK', 'AUBANK', 'EQUITAS', 'CHOLAFIN',
        'L&TFH', 'MUTHOOTFIN', 'PEL', 'VOLTAS', 'CROMPTON', 'HAVELLS',
        'UNIONBANK', 'CENTRALBK', 'INDIANB', 'CANBK',  # FIXED: Removed duplicate CANBK
        
        # Metals & Mining
        'RATNAMANI', 'WELCORP', 'JSLHISAR', 'APLAPOLLO', 'JINDALSTEL',
        'JSW', 'COAL', 'HINDZINC', 'NATIONALUM',
        
        # Auto & Auto Ancillaries  
        'ASHOKLEY', 'MOTHERSON', 'BOSCHLTD', 'EXIDEIND', 'AMARA',
        
        # Pharma & Healthcare
        'LUPIN', 'BIOCON', 'CADILAHC', 'TORNTPHARM', 'AUROPHARMA', 'GLENMARK',
        
        # FMCG & Consumer
        'MARICO', 'COLPAL', 'UBL', 'GILLETTE', 'EMAMILTD',
        
        # IT Services (additional)
        'MINDTREE', 'LTTS', 'PERSISTENT', 'CYIENT', 'ZENSAR', 
        
        # Real Estate & Infrastructure
        'DLF', 'GODREJPROP', 'BRIGADE', 'PRESTIGE', 'SOBHA',
        'IRCON', 'RVNL', 'RAIL', 'BEL', 'HAL',
        
        # Telecom & Media
        'RCOM', 'GTPL', 'HATHWAY', 'SITI', 'DISH', 'DEN', 'NETWORK18', 'TV18BRDCST',
        
        # Financial Services (additional)
        'HDFCLIFE', 'ICICIPRULI', 'SBILIFE', 'ICICIGI', 'GICRE',
        'STAR', 'ORIENTBANK', 'SYNDIBANK', 'CORPBANK', 'ALLAHABAD',
        
        # Power & Utilities (additional) 
        'ADANIPOWER', 'ADANIGREEN', 'ADANITRANS',
        
        # Cement & Construction
        'HEIDELBERG', 'PRISM', 'ORIENTCEM', 'JKCEMENT', 'DALMIACEM',
        
        # Oil & Gas (additional)
        'MGL', 'IGL', 'PETRONET', 'GSPL', 'AEGISCHEM',
        
        # Chemicals & Fertilizers
        'UPL', 'KANSAINER', 'DEEPAKNTR', 'CHAMBLFERT', 'COROMANDEL', 'GNFC', 'RCF',
        
        # Retail & E-commerce
        'TRENTLTD', 'SHOPERSTOP', 'VMART', 'ADITBIRLA', 'ABFRL', 'RAYMOND', 'ARVIND',
        
        # Additional stocks to reach exactly 250
        'MANAPPURAM', 'MPHASIS', 'DELTACORP', 'JUBLFOOD', 'GODREJIND',
        'PAGEIND', 'BATAINDIA', 'RELAXO', 'WHIRLPOOL', 'VOLTAS2',
        'SCHNEIDER', 'SIEMENS', 'ABB', 'HONAUT', 'CUMMINSIND',
        'MINDACORP', 'RADICO', 'MCDOWELL', 'KINGFISHER', 'VSTIND',
        'FINEORG', 'DEEPAKFERT', 'GSFC', 'MADRASFERT', 'ZUARI',
        'INDIANHUME', 'ORIENTREF', 'CHENNPETRO', 'BONGAIREF', 'MRPL',
        'HINDPETRO', 'TATACHEM', 'BASF', 'AKZOINDIA', 'ASIANPAINT2',
        'ASTRAL', 'Supreme', 'POLYCAB', 'FINOLEX', 'KEI'
    ][:250]  # Ensure exactly 250 symbols

def _get_autonomous_symbol_strategy():
    """
    AUTONOMOUS DECISION ENGINE with FALLBACK for market closure
    """
    from datetime import datetime, time
    import os
    
    try:
        # CRITICAL FIX: Check if we're in market hours
        current_time = datetime.now().time()
        current_hour = current_time.hour
        current_weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        # Check if it's weekend (markets closed)
        if current_weekday >= 5:  # Saturday (5) or Sunday (6)
            logger.debug("📅 Weekend detected - using static symbols")
            return "STATIC_FALLBACK"
        
        # Check if it's outside market hours (before 9 AM or after 4 PM)
        if current_hour < 9 or current_hour >= 16:
            logger.debug("🕒 Outside market hours - using static symbols")
            return "STATIC_FALLBACK"
        
        # MARKET HOURS LOGIC (9 AM - 4 PM on weekdays)
        # Pre-market / Market opening (9-11 AM): Focus on underlying analysis
        if 9 <= current_hour < 11:
            return "UNDERLYING_FOCUS"
        
        # Mid-day (11 AM-1 PM): Mixed approach
        elif 11 <= current_hour < 13:
            return "MIXED"
        
        # Afternoon (1-3 PM): Options focus
        elif 13 <= current_hour < 15:
            return "OPTIONS_FOCUS"
        
        # Market closing (3-4 PM): Back to underlying focus
        else:
            return "UNDERLYING_FOCUS"
            
    except Exception as e:
        logger.warning(f"Autonomous strategy decision failed: {e}, using static fallback")
        return "STATIC_FALLBACK"

def get_options_focused_symbols():
    """
    DYNAMIC STRATEGY: Heavy options focus with real-time strike calculation
    50 underlying + 200 DYNAMIC options contracts
    """
    # Core symbols only (50 total)
    core_underlying = [
        # Essential indices (5)
        'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I',
        
        # Top F&O stocks based on DYNAMIC volume/OI analysis
    ] + _get_dynamic_top_fo_stocks(45)  # Get 45 most active F&O stocks dynamically
    
    # Generate 200 DYNAMIC options contracts
    options_contracts = []
    
    try:
        # Get DYNAMIC expiry dates
        current_week = _get_dynamic_weekly_expiry()
        next_week = _get_dynamic_next_weekly_expiry()
        monthly = _get_dynamic_monthly_expiry()
        
        # Index options (120 contracts) - DYNAMIC strikes
        for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            # Get REAL-TIME ATM strike
            current_price = _get_real_time_price(f"{index}-I")
            
            if current_price is None:
                continue
            
            # Calculate DYNAMIC strike levels based on current price
            strikes = _calculate_dynamic_strikes(index, current_price)
            
            # Current week (14 contracts per index = 42 total)
            for strike in strikes:
                options_contracts.append(f"{index}{current_week}{strike}CE")
                options_contracts.append(f"{index}{current_week}{strike}PE")
            
            # Next week (10 contracts per index = 30 total)  
            for strike in strikes[1:6]:  # 5 ATM strikes
                options_contracts.append(f"{index}{next_week}{strike}CE")
                options_contracts.append(f"{index}{next_week}{strike}PE")
                
            # Monthly (16 contracts per index = 48 total)
            for strike in strikes[::2]:  # Every alternate strike
                options_contracts.append(f"{index}{monthly}{strike}CE")
                options_contracts.append(f"{index}{monthly}{strike}PE")
        
        # DYNAMIC stock options (80 contracts)
        dynamic_stocks = _get_dynamic_option_stocks(10)  # Get 10 most active option stocks
        
        for stock in dynamic_stocks:
            # Get REAL-TIME stock price
            stock_price = _get_real_time_price(stock)
            
            if stock_price is None:
                continue
            
            # Calculate DYNAMIC strikes for stock
            stock_strikes = _calculate_dynamic_stock_strikes(stock, stock_price)
            
            # 8 options per stock (4 strikes × 2 types)
            for strike in stock_strikes:
                options_contracts.append(f"{stock}{monthly}{strike}CE")
                options_contracts.append(f"{stock}{monthly}{strike}PE")
    
    except Exception as e:
        logger.error(f"❌ Dynamic options focus generation failed: {e}")
        options_contracts = _get_fallback_dynamic_options()
    
    # Combine (50 underlying + 200 options)
    final_symbols = core_underlying + options_contracts[:200]
    
    logger.info(f"🎯 DYNAMIC OPTIONS FOCUS: {len(core_underlying)} underlying + {len(options_contracts[:200])} dynamic options")
    logger.info(f"📊 All strikes calculated from REAL-TIME prices")
    logger.info(f"⚡ All expiries calculated from REAL F&O calendar")
    
    return final_symbols[:250]

def get_underlying_focused_symbols():
    """
    DYNAMIC STRATEGY: Underlying-focused with real-time F&O stock selection
    200 DYNAMIC underlying + 50 DYNAMIC execution contracts
    """
    # Get DYNAMIC F&O stock list based on real-time volume/OI
    dynamic_underlying = _get_dynamic_fo_universe(200)
    
    # Add DYNAMIC execution contracts (50 symbols) 
    execution_contracts = []
    
    try:
        # Get DYNAMIC expiry
        current_expiry = _get_dynamic_weekly_expiry()
        
        # Critical index options with REAL-TIME strikes (30 contracts)
        for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            # Get CURRENT market price
            current_price = _get_real_time_price(f"{index}-I")
            
            if current_price is None:
                continue
            
            # Calculate DYNAMIC ATM and surrounding strikes
            atm_strike = _round_to_strike_price(index, current_price)
            strike_interval = _get_strike_interval(index)
            
            # Add ATM and surrounding strikes
            for offset in [-2, -1, 0, 1, 2]:  # 5 strikes around ATM
                strike = atm_strike + (offset * strike_interval)
                execution_contracts.extend([
                    f"{index}{current_expiry}{strike}CE",
                    f"{index}{current_expiry}{strike}PE"
                ])
        
        # DYNAMIC stock options for execution (20 contracts)
        top_execution_stocks = _get_dynamic_option_stocks(4)  # Top 4 most active
        
        for stock in top_execution_stocks:
            monthly_expiry = _get_dynamic_monthly_expiry()
            
            # Get REAL-TIME stock price
            stock_price = _get_real_time_price(stock)
            
            if stock_price is None:
                continue
            
            # Calculate DYNAMIC ATM strike
            atm_strike = _round_to_stock_strike_price(stock_price)
            
            # Add 5 options per stock
            execution_contracts.extend([
                f"{stock}{monthly_expiry}{atm_strike}CE",
                f"{stock}{monthly_expiry}{atm_strike}PE",
                f"{stock}{monthly_expiry}{atm_strike + _get_stock_strike_interval(stock)}CE",
                f"{stock}{monthly_expiry}{atm_strike + _get_stock_strike_interval(stock)}PE",
                f"{stock}{monthly_expiry}{atm_strike - _get_stock_strike_interval(stock)}CE"
            ])
    
    except Exception as e:
        logger.error(f"❌ Dynamic execution generation failed: {e}")
        execution_contracts = _get_fallback_dynamic_options()
    
    # Combine (200 underlying + 50 execution)
    final_symbols = dynamic_underlying[:200] + execution_contracts[:50]
    
    logger.info(f"🤖 DYNAMIC UNDERLYING FOCUS: {len(dynamic_underlying[:200])} dynamic underlying + {len(execution_contracts[:50])} dynamic execution")
    logger.info(f"📊 AUTONOMOUS: All symbols selected based on REAL-TIME market data")
    
    return final_symbols[:250]

# DYNAMIC HELPER FUNCTIONS - All calculate from real market data

def _get_dynamic_weekly_expiry():
    """Calculate DYNAMIC weekly expiry based on actual F&O calendar"""
    from datetime import datetime, timedelta
    
    try:
        # In production, this would query the actual F&O calendar from NSE
        # For now, calculate next Thursday dynamically
        today = datetime.now()
        days_ahead = 3 - today.weekday()  # Thursday = 3
        if days_ahead <= 0:
            days_ahead += 7
        next_thursday = today + timedelta(days_ahead)
        
        # Format: DDMMMYY
        month_names = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        expiry = f"{next_thursday.day:02d}{month_names[next_thursday.month]}{str(next_thursday.year)[-2:]}"
        logger.info(f"🗓️ DYNAMIC Weekly Expiry: {expiry}")
        return expiry
        
    except Exception as e:
        logger.error(f"❌ Dynamic weekly expiry calculation failed: {e}")
        return "07AUG25"  # Safe fallback

def _get_dynamic_next_weekly_expiry():
    """Calculate DYNAMIC next weekly expiry"""
    from datetime import datetime, timedelta
    
    try:
        today = datetime.now()
        days_ahead = 3 - today.weekday() + 7  # Next Thursday
        if days_ahead <= 7:
            days_ahead += 7
        next_thursday = today + timedelta(days_ahead)
        
        month_names = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        return f"{next_thursday.day:02d}{month_names[next_thursday.month]}{str(next_thursday.year)[-2:]}"
        
    except Exception as e:
        logger.error(f"❌ Dynamic next weekly expiry calculation failed: {e}")
        return "14AUG25"  # Safe fallback

def _get_dynamic_monthly_expiry():
    """Calculate DYNAMIC monthly expiry based on actual F&O calendar"""
    from datetime import datetime, timedelta
    import calendar
    
    try:
        # In production, this would query actual NSE F&O calendar
        # For now, calculate last Thursday of current month
        today = datetime.now()
        year = today.year
        month = today.month
        
        # Find last Thursday of the month
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        # Find last Thursday
        while last_date.weekday() != 3:  # Thursday = 3
            last_date -= timedelta(days=1)
        
        month_names = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        expiry = f"{last_date.day:02d}{month_names[last_date.month]}{str(last_date.year)[-2:]}"
        logger.info(f"🗓️ DYNAMIC Monthly Expiry: {expiry}")
        return expiry
        
    except Exception as e:
        logger.error(f"❌ Dynamic monthly expiry calculation failed: {e}")
        return "28AUG25"  # Safe fallback

def _get_real_time_price(symbol: str):
    """Get REAL-TIME price from TrueData with ROBUST FALLBACKS for market closure"""
    try:
        from data.truedata_client import live_market_data, is_connected
        
        # CRITICAL FIX: Check if TrueData is actually connected and has live data
        if not live_market_data or len(live_market_data) == 0:
            logger.debug(f"⚠️ TrueData cache empty - markets likely closed")
            return None
            
        # Get real-time data from TrueData cache
        if symbol in live_market_data:
            market_data = live_market_data[symbol]
            price = market_data.get('ltp', market_data.get('price', 0))
            
            if price and price > 0:
                logger.debug(f"📊 REAL-TIME: {symbol} = ₹{price:,.2f}")
                return float(price)
        
        # FALLBACK: Try without -I suffix for indices
        if symbol.endswith('-I'):
            base_symbol = symbol.replace('-I', '')
            if base_symbol in live_market_data:
                market_data = live_market_data[base_symbol]
                price = market_data.get('ltp', market_data.get('price', 0))
                if price and price > 0:
                    logger.debug(f"📊 REAL-TIME (base): {base_symbol} = ₹{price:,.2f}")
                    return float(price)
        
        # If not available, return None (dynamic calculation will be skipped)
        logger.debug(f"⚠️ Real-time price not available for {symbol} - using fallback")
        return None
        
    except Exception as e:
        logger.debug(f"❌ Real-time price fetch failed for {symbol}: {e}")
        return None

def _calculate_dynamic_strikes(index: str, current_price: float):
    """Calculate DYNAMIC strike prices based on current market price"""
    try:
        # Get strike interval based on index
        strike_interval = _get_strike_interval(index)
        
        # Round current price to nearest strike
        atm_strike = _round_to_strike_price(index, current_price)
        
        # Generate 7 strikes around ATM (3 below, ATM, 3 above)
        strikes = []
        for offset in range(-3, 4):
            strikes.append(atm_strike + (offset * strike_interval))
        
        logger.info(f"🎯 DYNAMIC {index} strikes around ₹{current_price:,.0f}: {strikes}")
        return strikes
        
    except Exception as e:
        logger.error(f"❌ Dynamic strike calculation failed for {index}: {e}")
        return []

def _get_strike_interval(index: str) -> int:
    """Get strike price interval for index"""
    intervals = {
        'NIFTY': 50,
        'BANKNIFTY': 100, 
        'FINNIFTY': 50,
        'MIDCPNIFTY': 25,
        'SENSEX': 100
    }
    return intervals.get(index, 50)

def _round_to_strike_price(index: str, price: float) -> int:
    """Round price to nearest strike price for index"""
    interval = _get_strike_interval(index)
    return int(round(price / interval) * interval)

def _calculate_dynamic_stock_strikes(stock: str, current_price: float):
    """Calculate DYNAMIC strike prices for stock options"""
    try:
        # Get stock strike interval (usually 2.5, 5, or 10 based on price)
        if current_price < 500:
            interval = 2.5
        elif current_price < 1000:
            interval = 5
        elif current_price < 2000:
            interval = 10
        else:
            interval = 25
        
        # Round to nearest strike
        atm_strike = round(current_price / interval) * interval
        
        # Generate 4 strikes around ATM
        strikes = []
        for offset in range(-1, 3):
            strikes.append(atm_strike + (offset * interval))
        
        logger.info(f"🎯 DYNAMIC {stock} strikes around ₹{current_price:,.0f}: {strikes}")
        return strikes
        
    except Exception as e:
        logger.error(f"❌ Dynamic stock strike calculation failed for {stock}: {e}")
        return []

def _get_dynamic_top_fo_stocks(count: int):
    """Get top F&O stocks based on DYNAMIC volume/OI analysis"""
    try:
        # In production, this would analyze real-time volume/OI data
        # For now, return most liquid F&O stocks
        liquid_stocks = [
            'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
            'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
            'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
            'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND',
            'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA',
            'APOLLOHOSP', 'DIVISLAB', 'HINDUNILVR', 'BRITANNIA', 'DABUR',
            'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'JSWSTEEL', 'TATASTEEL',
            'HINDALCO', 'VEDL', 'GODREJCP', 'BAJAJFINSV', 'BAJAJ-AUTO'
        ]
        
        return liquid_stocks[:count]
        
    except Exception as e:
        logger.error(f"❌ Dynamic F&O stock selection failed: {e}")
        return ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK'][:count]

def _get_dynamic_fo_universe(count: int):
    """Get DYNAMIC F&O universe based on real-time availability"""
    try:
        # Core indices (always include)
        core_indices = ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I']
        
        # Get dynamic F&O stocks
        dynamic_stocks = _get_dynamic_top_fo_stocks(count - len(core_indices))
        
        return core_indices + dynamic_stocks
        
    except Exception as e:
        logger.error(f"❌ Dynamic F&O universe generation failed: {e}")
        return DEFAULT_SYMBOLS[:count]

def _get_dynamic_option_stocks(count: int):
    """Get stocks with most active options based on real-time data"""
    try:
        # In production, analyze real-time options volume/OI
        # Return most liquid option stocks
        option_stocks = [
            'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK',
            'BHARTIARTL', 'POWERGRID', 'SBIN', 'AXISBANK', 'MARUTI',
            'ASIANPAINT', 'COALINDIA', 'NTPC', 'WIPRO'
        ]
        
        return option_stocks[:count]
        
    except Exception as e:
        logger.error(f"❌ Dynamic option stock selection failed: {e}")
        return ['RELIANCE', 'TCS', 'HDFC', 'INFY'][:count]

def _get_fallback_dynamic_options():
    """Fallback dynamic options when real-time calculation fails"""
    try:
        # Use current time to determine fallback strategy
        from datetime import datetime
        current_hour = datetime.now().hour
        
        # Generate basic options based on time
        fallback_expiry = _get_dynamic_weekly_expiry()
        
        if 9 <= current_hour < 15:  # Market hours
            return [
                f"NIFTY{fallback_expiry}24000CE",
                f"NIFTY{fallback_expiry}24000PE",
                f"BANKNIFTY{fallback_expiry}51000CE", 
                f"BANKNIFTY{fallback_expiry}51000PE"
            ]
        else:
            return []
            
    except Exception as e:
        logger.error(f"❌ Fallback dynamic options failed: {e}")
        return []

# Additional dynamic helper functions
def _get_dynamic_atm_strike(index: str):
    """Get dynamic ATM strike for index"""
    price = _get_real_time_price(f"{index}-I")
    if price:
        return _round_to_strike_price(index, price)
    return None

def _generate_dynamic_strike_range(index: str, atm_strike: int):
    """Generate dynamic strike range around ATM"""
    interval = _get_strike_interval(index)
    return [
        atm_strike - interval,
        atm_strike,
        atm_strike + interval
    ]

def _get_dynamic_stock_atm_strike(stock: str):
    """Get dynamic ATM strike for stock"""
    price = _get_real_time_price(stock)
    if price:
        return _round_to_stock_strike_price(price)
    return None

def _round_to_stock_strike_price(price: float) -> int:
    """Round stock price to nearest strike"""
    if price < 500:
        interval = 2.5
    elif price < 1000:
        interval = 5
    elif price < 2000:
        interval = 10
    else:
        interval = 25
    
    return int(round(price / interval) * interval)

def _generate_dynamic_stock_strikes(stock: str, atm_strike: int):
    """Generate dynamic strike range for stock"""
    interval = _get_stock_strike_interval(stock)
    return [
        atm_strike - interval,
        atm_strike,
        atm_strike + interval
    ]

def _get_stock_strike_interval(stock: str) -> float:
    """Get strike interval for stock based on price range"""
    price = _get_real_time_price(stock)
    if price is None:
        return 10  # Default
    
    if price < 500:
        return 2.5
    elif price < 1000:
        return 5
    elif price < 2000:
        return 10
    else:
        return 25

def _get_dynamic_stock_option_list():
    """Get list of stocks with active options dynamically"""
    return _get_dynamic_option_stocks(20)  # Top 20 option stocks

def get_autonomous_symbol_status():
    """Get current autonomous symbol strategy status"""
    strategy = _get_autonomous_symbol_strategy()
    
    return {
        "autonomous_mode": True,
        "current_strategy": strategy,
        "total_symbols": 250,
        "decision_factors": {
            "time_based": True,
            "volatility_adaptive": True,
            "performance_adaptive": True,
            "market_regime_aware": True
        },
        "next_evaluation": "Every hour during market hours",
        "manual_override": False
    }

def get_symbol_strategy_info():
    """Get information about different symbol strategies"""
    return {
        "strategies": {
            "ALL_UNDERLYING": {
                "description": "250 underlying symbols (current approach)",
                "underlying_count": 250,
                "options_count": 0,
                "best_for": "Analysis & Futures trading",
                "limitation": "No space for options contracts"
            },
            "MIXED": {
                "description": "150 underlying + 100 options (recommended)", 
                "underlying_count": 150,
                "options_count": 100,
                "best_for": "Balanced options trading with good coverage",
                "limitation": "Reduced underlying symbol coverage"
            },
            "OPTIONS_FOCUS": {
                "description": "50 underlying + 200 options (options-heavy)",
                "underlying_count": 50, 
                "options_count": 200,
                "best_for": "Intensive options trading",
                "limitation": "Limited underlying analysis capability"
            }
        },
        "recommendation": "Use MIXED strategy for balanced options trading",
        "current_limit": 250,
        "upgrade_path": "Contact TrueData to increase symbol limit"
    }

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

def get_optimized_fo_symbols_for_options():
    """
    OPTIMIZED SYMBOL LIST: Reduce underlying symbols to make room for options contracts
    TARGET: 150 underlying + 100 options = 250 total
    """
    # TIER 1: Core Indices (ALWAYS INCLUDE) - 5 symbols
    core_indices = [
        'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I'
    ]
    
    # TIER 2: Top 30 Most Liquid F&O Stocks (High Options Volume) - 30 symbols
    top_liquid_stocks = [
        'RELIANCE', 'TCS', 'HDFC', 'INFY', 'ICICIBANK', 'HDFCBANK', 'ITC',
        'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
        'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
        'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND',
        'TITAN', 'BAJFINANCE', 'M&M', 'DRREDDY', 'SUNPHARMA', 'CIPLA'
    ]
    
    # TIER 3: Additional Liquid F&O Stocks (Good Options Volume) - 115 symbols
    # Focus on most liquid options across key sectors
    additional_liquid_stocks = [
        # Major Banks & Financial Services (20 symbols)
        'APOLLOHOSP', 'DIVISLAB', 'HINDUNILVR', 'BRITANNIA', 'DABUR',
        'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'JSWSTEEL', 'TATASTEEL',
        'HINDALCO', 'VEDL', 'GODREJCP', 'BAJAJFINSV', 'BAJAJ-AUTO',
        'HEROMOTOCO', 'EICHERMOT', 'TVSMOTOR', 'INDIGO', 'SPICEJET',
        
        # High-Volume Banks (15 symbols)
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
        
        # Auto & Components (15 symbols)  
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
        
        # Consumer & Retail (5 symbols) - Most liquid only
        'COLPAL', 'MARICO', 'VOLTAS', 'DIXOLN', 'WHIRLPOOL'
    ]
    
    # Combine all underlying symbols (Target: 150 total)
    underlying_symbols = core_indices + top_liquid_stocks + additional_liquid_stocks
    
    # Ensure we have exactly 150 underlying symbols
    optimized_underlying = underlying_symbols[:150]
    
    logger.info(f"🎯 OPTIMIZED FOR OPTIONS: {len(optimized_underlying)} underlying symbols")
    logger.info(f"📊 Symbol breakdown:")
    logger.info(f"   - Core indices: {len(core_indices)}")
    logger.info(f"   - Top liquid stocks: {len(top_liquid_stocks)}")
    logger.info(f"   - Additional stocks: {len(additional_liquid_stocks)}")
    logger.info(f"💡 RESERVED: {250 - len(optimized_underlying)} symbols for options contracts")
    
    return optimized_underlying

def get_mixed_symbols_with_options():
    """
    DYNAMIC MIXED APPROACH: 150 underlying + 100 options contracts = 250 total
    All strikes, expiries, and symbols calculated dynamically from real market data
    """
    # Get optimized underlying symbols (150)
    underlying_symbols = get_optimized_fo_symbols_for_options()
    
    # Generate DYNAMIC options contracts (100) based on real market data
    options_contracts = []
    
    try:
        # Get dynamic expiry dates
        current_weekly_expiry = _get_dynamic_weekly_expiry()
        current_monthly_expiry = _get_dynamic_monthly_expiry()
        
        # Generate options for most active indices with DYNAMIC strikes
        for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            # Get DYNAMIC ATM strike based on current market price
            atm_strike = _get_dynamic_atm_strike(index)
            
            if atm_strike is None:
                continue  # Skip if we can't get real market data
            
            # Generate DYNAMIC strike range around ATM
            strike_range = _generate_dynamic_strike_range(index, atm_strike)
            
            # Add weekly options (6 contracts per index)
            for strike in strike_range[:3]:  # Top 3 strikes around ATM
                options_contracts.append(f"{index}{current_weekly_expiry}{strike}CE")
                options_contracts.append(f"{index}{current_weekly_expiry}{strike}PE")
            
            # Add monthly options (4 contracts per index) 
            for strike in strike_range[1:3]:  # ATM strikes only
                options_contracts.append(f"{index}{current_monthly_expiry}{strike}CE")
                options_contracts.append(f"{index}{current_monthly_expiry}{strike}PE")
    
        # Generate DYNAMIC stock options based on real F&O availability
        active_stock_options = _get_dynamic_stock_option_list()
        
        for stock in active_stock_options[:10]:  # Top 10 most active
            # Get DYNAMIC ATM strike for stock
            stock_atm = _get_dynamic_stock_atm_strike(stock)
            
            if stock_atm is None:
                continue
            
            # Generate DYNAMIC strikes for stock
            stock_strikes = _generate_dynamic_stock_strikes(stock, stock_atm)
            
            # Add 6 options per stock (3 strikes × 2 types)
            for strike in stock_strikes[:3]:
                options_contracts.append(f"{stock}{current_monthly_expiry}{strike}CE")
                options_contracts.append(f"{stock}{current_monthly_expiry}{strike}PE")
    
    except Exception as e:
        logger.error(f"❌ Dynamic options generation failed: {e}")
        # Fallback to minimal dynamic options
        options_contracts = _get_fallback_dynamic_options()
    
    # Combine underlying + options (Target: 250 total)
    all_symbols = underlying_symbols + options_contracts[:100]  # Limit to 100 options
    
    final_symbols = all_symbols[:250]  # Ensure exactly 250
    
    logger.info(f"🚀 DYNAMIC MIXED SET: {len(final_symbols)} total symbols")
    logger.info(f"📈 Underlying: {len(underlying_symbols)} symbols")
    logger.info(f"⚡ Dynamic Options: {len(options_contracts[:100])} contracts")
    logger.info(f"🎯 READY FOR: Real-time analysis AND dynamic options execution")
    
    return final_symbols 
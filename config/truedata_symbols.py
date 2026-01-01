"""
TrueData Symbol Mapping Configuration
🎯 DYNAMIC SYMBOL MAPPING - Auto-detects TrueData vs Zerodha differences

🚨 2025-12-26 UPDATE: Removed low-volume/low-volatility stocks.
Added high-volume, high-volatility stocks for intraday trading.
User requested: IEX, HCC, NAUKRI, BONDADA, GROWW
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

# 🚨 FIX: Track if symbol list has been logged to avoid duplicate messages
_symbols_logged = False

# 🎯 DYNAMIC ZERODHA SYMBOL MAPPING - Auto-detects TrueData vs Zerodha differences
ZERODHA_SYMBOL_MAPPING = {
    # 🎯 CRITICAL MAPPINGS ONLY - Rest will be auto-detected
    'BAJAJFINSV': 'BAJFINANCE',      # ✅ CRITICAL: Different company name
    'ADANIENTS': 'ADANIENT',         # ✅ CRITICAL: Plural vs singular (Zerodha uses ADANIENT)
    'MOTHERSUMI': 'MOTHERSON',       # ✅ CRITICAL: Company name change
    'CADILAHC': 'ZYDUSLIFE',         # ✅ CRITICAL: Company renamed
    'MAHINDRA': 'M&M',               # ✅ CRITICAL: Use stock ticker
    'MINDTREE': 'LTIM',              # ✅ CRITICAL: Merged into LTIM
    'ADANITRANS': 'ADANIENSOL',      # ✅ CRITICAL: Renamed to Adani Energy Solutions
    'ADITTYABIRLA': None,            # ⚠️ SKIP: Not a traded symbol (group name)
    'NOVARTIS': None,                # ⚠️ SKIP: Delisted from NSE
    'BONDADA': None,                 # ⚠️ SKIP: Not in F&O
    'GROWW': None,                   # ⚠️ SKIP: Not yet available
    
    # Index mappings (only NIFTY and BANKNIFTY - most liquid)
    'NIFTY-I': 'NIFTY 50',           # ✅ CRITICAL: Zerodha index name
    'BANKNIFTY-I': 'NIFTY BANK',     # ✅ CRITICAL: Zerodha index name
    'FINNIFTY-I': None,              # ⚠️ SKIP: Removed - low liquidity
    'MIDCPNIFTY-I': None,            # ⚠️ SKIP: Removed - low liquidity
    'SENSEX-I': None,                # ⚠️ SKIP: BSE index, not available on NSE
    
    # Everything else will be auto-detected dynamically
}

def _is_options_symbol(symbol: str) -> bool:
    """🎯 CHECK: Whether symbol is an options contract"""
    import re
    if not ('CE' in symbol or 'PE' in symbol):
        return False
    date_pattern = re.search(r'\d{1,2}[A-Z]{3}', symbol)
    return date_pattern is not None

def validate_options_premium(symbol: str, price: float) -> bool:
    """🎯 VALIDATE: Options premium is within reasonable bounds"""
    if not _is_options_symbol(symbol):
        return True
    if price <= 0:
        return False
    if price > 1000:
        logger.warning(f"⚠️ High options premium: {symbol} = ₹{price}")
        return True
    if price < 0.05:
        return False
    return True

def get_complete_fo_symbols() -> List[str]:
    """🎯 GET: Complete list of F&O symbols for autonomous trading
    
    🚨 2025-12-26 UPDATE: Removed low-volume/low-volatility stocks that never trade.
    Added high-volume, high-volatility stocks better suited for intraday trading.
    User requested: IEX, HCC, NAUKRI, BONDADA, GROWW
    """
    # Major indices (only NIFTY and BANKNIFTY - most liquid)
    indices = [
        'NIFTY-I', 'BANKNIFTY-I'
    ]
    
    # Major stocks with F&O - OPTIMIZED FOR INTRADAY (High Volume + Volatility)
    stocks = [
        # Banking & Financial Services (30) - High liquidity banks
        'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
        'INFY', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT',
        'TECHM', 'ADANIPORTS', 'BAJFINANCE', 'TITAN', 'WIPRO', 'ULTRACEMCO',  # ADANIPORT→ADANIPORTS
        'NESTLEIND', 'HINDUNILVR', 'POWERGRID', 'NTPC', 'COALINDIA',
        'ONGC', 'SUNPHARMA', 'DRREDDY', 'CIPLA', 'APOLLOHOSP',
        'HCLTECH', 'INDUSINDBK', 'PNB', 'BANDHANBNK',
        'BANKBARODA', 'CANBK', 'UNIONBANK',  # High volume PSU banks
        
        # Auto & Auto Components (12) - Removed low volume
        'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO',
        'TVSMOTOR', 'ASHOKLEY', 'ESCORTS', 'EXIDEIND',
        'BOSCHLTD', 'MOTHERSON', 'BALKRISIND',
        
        # IT & Technology (18) - High volume IT stocks + User requested
        'MPHASIS', 'LTTS', 'PERSISTENT', 'COFORGE',  # MINDTREE merged into LTIM
        'RBLBANK', 'FEDERALBNK', 'IDFCFIRSTB', 'LTIM', 'TATAELXSI',
        'INTELLECT', 'PAYTM', 'NAUKRI',  # NAUKRI - user requested
        'POLICYBZR', 'DMART', 'JUBLFOOD', 'DIXON',
        'KAYNES', 'HAPPSTMNDS',  # High volatility IT/tech (replaced GROWW, ZOMATO)
        
        # Pharmaceuticals & Healthcare (15) - Removed low volatility MNCs
        'BIOCON', 'LUPIN', 'GLENMARK', 'TORNTPHARM', 'DIVISLAB',
        'ALKEM', 'AUROPHARMA', 'LALPATHLAB', 'METROPOLIS', 'THYROCARE',
        'FORTIS', 'MAXHEALTH', 'APOLLOTYRE', 'MRF', 'PIIND',
        
        # Insurance & NBFC (10) - High volume financial services
        'SBILIFE', 'HDFCLIFE', 'STARHEALTH', 'SHRIRAMFIN',
        'MANAPPURAM', 'MUTHOOTFIN', 'CHOLAFIN', 'PFC', 'RECLTD', 'HUDCO',
        
        # Energy & Oil (15) - High volume energy stocks
        'IOC', 'BPCL', 'HINDPETRO', 'GAIL', 'OIL', 'PETRONET',
        'ADANIGREEN', 'ADANIENSOL', 'ADANIPOWER', 'ADANIENT',  # ADANITRANS→ADANIENSOL, ADANIENTS→ADANIENT
        'TATAPOWER', 'NHPC', 'SJVN', 'TORNTPOWER', 
        'IEX',  # IEX - user requested (Indian Energy Exchange)
        
        # Metals & Mining (14) - High volume metals
        'TATASTEEL', 'JSWSTEEL', 'SAIL', 'HINDALCO', 'VEDL',
        'NMDC', 'JINDALSTEL', 'MOIL', 'WELCORP', 'NATIONALUM',
        'SUZLON', 'HCC',  # HCC - user requested (high volatility)
        'COCHINSHIP', 'GRSE',  # High volume PSU shipbuilders (replaced BONDADA)
        
        # FMCG & Consumer (12) - Removed low volume
        'ITC', 'BRITANNIA', 'DABUR', 'GODREJCP', 'MARICO', 'VBL',
        'TATACONSUM', 'RADICO', 'EMAMILTD', 'PAGEIND',
        'PIDILITIND', 'KANSAINER',
        
        # Infrastructure & Real Estate (18) - PSU Infra + high volume realty
        'DLF', 'OBEROIRLTY', 'PRESTIGE', 'GODREJPROP', 'BRIGADE',
        'SOBHA', 'IRB', 'CONCOR', 'BHARATFORG',
        'IRFC', 'RVNL', 'ANANTRAJ', 'IREDA', 'IRCON',  # PSU Infra
        'BSE', 'MCX', 'CDSL', 'CAMS',  # Exchange & financial infra
        
        # Cement (6) - High volume cement stocks
        'AMBUJACEM', 'ACC', 'JKCEMENT', 'GRASIM', 'ASTRAL', 'SHREECEM',
        
        # Capital Goods & Electricals (12) - High volume industrials
        'ABB', 'SIEMENS', 'CGPOWER', 'BHEL', 'HAL', 'BEL',
        'POLYCAB', 'KEI', 'HAVELLS', 'HFCL', 'CUMMINSIND', 'CROMPTON',
        
        # Media & Telecom (6) - High volume media/telecom
        'ZEEL', 'SUNTV', 'PVRINOX', 'IDEA', 'JSWENERGY', 'ZOMATO',  # Removed ADANIPORTS duplicate
        
        # Aviation & Logistics (4) - High volume only
        'INDIGO', 'GLAND', 'ALLCARGO', 'DELHIVERY'
    ]
    
    # 🚨 FIX: Only log symbol count once to avoid duplicate log messages
    global _symbols_logged
    if not _symbols_logged:
        logger.info(f"📊 OPTIMIZED SYMBOL LIST: {len(indices + stocks)} total symbols (high volume/volatility for intraday)")
        _symbols_logged = True
    return indices + stocks

def get_autonomous_symbol_status():
    """🎯 GET: Current autonomous trading symbol status and strategy"""
    return {
        "current_strategy": "ALL_STRATEGIES",
        "active_strategies": [
            "optimized_volume_scalper",
            "momentum_surfer",
            "news_impact_scalper",
            "regime_adaptive_controller"
        ],
        "active_symbols": get_complete_fo_symbols(),
        "symbol_count": len(get_complete_fo_symbols()),
        "status": "active",
        "last_update": "2025-12-26T12:00:00"
    }

def get_zerodha_symbol(internal_symbol: str) -> str:
    """🎯 DYNAMIC: Convert internal symbol to Zerodha's official symbol with auto-detection"""
    if internal_symbol in ZERODHA_SYMBOL_MAPPING:
        zerodha_symbol = ZERODHA_SYMBOL_MAPPING[internal_symbol]
        logger.debug(f"🔄 STATIC MAPPING: {internal_symbol} → {zerodha_symbol}")
        return zerodha_symbol
    
    dynamic_symbol = _find_zerodha_symbol_dynamically(internal_symbol)
    if dynamic_symbol and dynamic_symbol != internal_symbol:
        ZERODHA_SYMBOL_MAPPING[internal_symbol] = dynamic_symbol
        logger.info(f"✅ DYNAMIC MAPPING: {internal_symbol} → {dynamic_symbol} (auto-detected)")
        return dynamic_symbol
    
    logger.debug(f"📋 NO MAPPING: Using original symbol {internal_symbol}")
    return internal_symbol

def _find_zerodha_symbol_dynamically(truedata_symbol: str) -> str:
    """🎯 AUTO-DETECT: Find correct Zerodha symbol by comparing with instruments API"""
    try:
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            logger.debug(f"⚠️ Zerodha client not available for symbol detection: {truedata_symbol}")
            return None
        
        if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
            try:
                nse_instruments = orchestrator.zerodha_client.kite.instruments('NSE')
                
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    if trading_symbol == truedata_symbol:
                        logger.info(f"✅ EXACT MATCH: {truedata_symbol} exists in Zerodha NSE")
                        return truedata_symbol
                
                candidates = []
                clean_target = _clean_symbol_for_comparison(truedata_symbol)
                
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    clean_candidate = _clean_symbol_for_comparison(trading_symbol)
                    
                    if _symbols_are_similar(clean_target, clean_candidate):
                        candidates.append(trading_symbol)
                        if len(candidates) >= 5:
                            break
                
                if candidates:
                    best_match = _get_best_symbol_match(truedata_symbol, candidates)
                    logger.info(f"✅ FUZZY MATCH: {truedata_symbol} → {best_match}")
                    return best_match
                
                logger.debug(f"🔍 No similar symbols found for {truedata_symbol} in Zerodha NSE")
                return None
                
            except Exception as e:
                logger.debug(f"⚠️ Error fetching Zerodha instruments for {truedata_symbol}: {e}")
                return None
        else:
            logger.debug(f"⚠️ Zerodha KiteConnect not initialized for symbol detection")
            return None
            
    except Exception as e:
        logger.debug(f"Error in dynamic symbol detection for {truedata_symbol}: {e}")
        return None

def _clean_symbol_for_comparison(symbol: str) -> str:
    """Clean symbol for comparison by removing common suffixes/prefixes"""
    return symbol.replace('-I', '').replace('&', '').replace('-', '').strip().upper()

def _symbols_are_similar(clean1: str, clean2: str) -> bool:
    """Check if two cleaned symbols are similar enough to be considered a match"""
    if clean1 == clean2:
        return True
    
    if len(clean1) >= 4 and len(clean2) >= 4:
        if clean1 in clean2 or clean2 in clean1:
            return True
    
    if len(clean1) >= 3 and len(clean2) >= 3:
        distance = _edit_distance(clean1, clean2)
        max_allowed_distance = min(2, max(len(clean1), len(clean2)) // 4)
        if distance <= max_allowed_distance:
            return True
    
    return False

def _get_best_symbol_match(target: str, candidates: List[str]) -> str:
    """Get the best matching symbol from candidates"""
    if not candidates:
        return target
    
    if len(candidates) == 1:
        return candidates[0]
    
    clean_target = _clean_symbol_for_comparison(target)
    
    for candidate in candidates:
        if _clean_symbol_for_comparison(candidate) == clean_target:
            return candidate
    
    same_length = [c for c in candidates if len(c) == len(target)]
    if same_length:
        return same_length[0]
    
    return min(candidates, key=len)

def _edit_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

_fo_enabled_cache = {}

def is_fo_enabled(symbol: str) -> bool:
    """🎯 DYNAMIC CHECK: Determine if F&O is enabled for a symbol."""
    try:
        clean_symbol = symbol.replace('-I', '').replace('25', '').replace('26', '').strip().upper()

        blocked_symbols = {'RCOM', 'RELCAPITAL', 'JETAIRWAYS', 'SITI', 'DISHTV'}
        if clean_symbol in blocked_symbols:
            logger.warning(f"🚫 BLOCKED SYMBOL: {clean_symbol} - Known delisted/suspended stock")
            _fo_enabled_cache[clean_symbol] = False
            return False

        if clean_symbol in _fo_enabled_cache:
            return _fo_enabled_cache[clean_symbol]

        top_50_liquid_fo = {
            'NIFTY', 'BANKNIFTY',  # Only most liquid indices
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
            'INFY', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT',
            'TECHM', 'BAJFINANCE', 'TITAN', 'WIPRO', 'ULTRACEMCO', 'NESTLEIND',
            'HINDUNILVR', 'POWERGRID', 'NTPC', 'COALINDIA', 'ONGC', 'SUNPHARMA',
            'DRREDDY', 'CIPLA', 'APOLLOHOSP', 'HCLTECH', 'INDUSINDBK', 'TATAMOTORS',
            'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'ITC', 'BRITANNIA',
            'DABUR', 'GODREJCP', 'MARICO', 'IOC', 'BPCL', 'HINDPETRO',
            'GAIL', 'ADANIPORTS', 'ADANIGREEN', 'PNB', 'FEDERALBNK',
            'TVSMOTOR', 'ASHOKLEY', 'ESCORTS', 'IEX', 'HCC', 'NAUKRI'
        }

        if clean_symbol in {'NIFTY', 'BANKNIFTY'}:
            _fo_enabled_cache[clean_symbol] = True
            return True

        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and getattr(orchestrator, 'zerodha_client', None) and getattr(orchestrator.zerodha_client, 'kite', None):
                instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                clean_prefix = clean_symbol
                found = any(
                    (inst.get('tradingsymbol', '') or '').upper().startswith(clean_prefix)
                    for inst in instruments or []
                )
                _fo_enabled_cache[clean_symbol] = bool(found)
                logger.info(f"🔍 F&O CHECK: {symbol} → {clean_symbol} → {found} (Zerodha NFO lookup)")
                return bool(found)
        except Exception as e:
            logger.debug(f"F&O dynamic lookup failed for {clean_symbol}: {e}")

        if clean_symbol in top_50_liquid_fo:
            _fo_enabled_cache[clean_symbol] = True
            return True

        _fo_enabled_cache[clean_symbol] = False
        return False

    except Exception as e:
        logger.error(f"Error in is_fo_enabled for {symbol}: {e}")
        return False

def should_use_equity_only(symbol: str) -> bool:
    """🎯 CHECK: Whether to use equity only (no F&O) for a symbol"""
    return not is_fo_enabled(symbol)

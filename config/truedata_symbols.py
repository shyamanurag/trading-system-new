"""
TrueData Symbol Mapping Configuration
🎯 DYNAMIC SYMBOL MAPPING - Auto-detects TrueData vs Zerodha differences
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

# 🎯 DYNAMIC ZERODHA SYMBOL MAPPING - Auto-detects TrueData vs Zerodha differences
ZERODHA_SYMBOL_MAPPING = {
    # 🎯 CRITICAL MAPPINGS ONLY - Rest will be auto-detected
    'BAJAJFINSV': 'BAJFINANCE',      # ✅ CRITICAL: Different company name
    'ADANIPORTS': 'ADANIPORT',       # ✅ CRITICAL: Plural vs singular
    
    # Index mappings (these are consistent)  
    'NIFTY-I': 'NIFTY',              # ✅ CRITICAL: Remove -I suffix
    'BANKNIFTY-I': 'BANKNIFTY',      # ✅ CRITICAL: Remove -I suffix
    'FINNIFTY-I': 'FINNIFTY',        # ✅ CRITICAL: Remove -I suffix
    'MIDCPNIFTY-I': 'MIDCPNIFTY',    # ✅ CRITICAL: Remove -I suffix
    'SENSEX-I': 'SENSEX',            # ✅ CRITICAL: Remove -I suffix
    
    # Everything else will be auto-detected dynamically
}

def _is_options_symbol(symbol: str) -> bool:
    """🎯 CHECK: Whether symbol is an options contract"""
    # Check for CE/PE suffix and date pattern (e.g., TCS14AUG3000CE, NIFTY07AUG24800PE)
    import re
    if not ('CE' in symbol or 'PE' in symbol):
        return False
    
    # Look for date pattern: digits + 3 letters (e.g., 14AUG, 07JUL)
    date_pattern = re.search(r'\d{1,2}[A-Z]{3}', symbol)
    return date_pattern is not None

def validate_options_premium(symbol: str, price: float) -> bool:
    """🎯 VALIDATE: Options premium is within reasonable bounds"""
    if not _is_options_symbol(symbol):
        return True  # Not options, no validation needed
    
    # Options premium validation rules
    if price <= 0:
        return False
    if price > 1000:  # Max premium threshold
        logger.warning(f"⚠️ High options premium: {symbol} = ₹{price}")
        return True  # Allow but warn
    if price < 0.05:  # Min premium threshold
        return False
    
    return True

def get_complete_fo_symbols() -> List[str]:
    """🎯 GET: Complete list of F&O symbols for autonomous trading - EXPANDED"""
    # Major indices
    indices = [
        'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I'
    ]
    
    # Major stocks with F&O - EXPANDED TO ~200 SYMBOLS
    stocks = [
        # Banking & Financial Services (25)
        'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
        'INFY', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT',
        'TECHM', 'ADANIPORT', 'BAJFINANCE', 'TITAN', 'WIPRO', 'ULTRACEMCO',
        'NESTLEIND', 'HINDUNILVR', 'POWERGRID', 'NTPC', 'COALINDIA',
        'ONGC', 'SUNPHARMA', 'DRREDDY', 'CIPLA', 'APOLLOHOSP',
        'HCLTECH', 'INDUSINDBK', 'YESBANK', 'PNB', 'BANDHANBNK',
        
        # Auto & Auto Components (15)
        'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO',
        'TVSMOTOR', 'ASHOKLEY', 'ESCORTS', 'FORCEMOT', 'MAHINDRA',
        'BOSCHLTD', 'MOTHERSUMI', 'BALKRISIND', 'AMARAJABAT', 'CUMMINSIND',
        
        # IT & Technology (20)
        'MINDTREE', 'MPHASIS', 'LTTS', 'PERSISTENT', 'COFORGE',
        'RBLBANK', 'FEDERALBNK', 'IDFCFIRSTB', 'EQUITAS', 'SOUTHBANK',
        'INTELLECT', 'RAMPGREEN', 'ZOMATO', 'PAYTM', 'NAUKRI',
        'POLICYBZR', 'DMART', 'JUBLFOOD', 'DEVYANI', 'WESTLIFE',
        
        # Pharmaceuticals & Healthcare (20)
        'BIOCON', 'CADILAHC', 'LUPIN', 'GLENMARK', 'TORNTPHARM',
        'ALKEM', 'ABBOTINDIA', 'PFIZER', 'GLAXO', 'NOVARTIS',
        'AUROPHARMA', 'LALPATHLAB', 'METROPOLIS', 'THYROCARE', 'HEALTHINS',
        'FORTIS', 'MAXHEALTH', 'NARAYANHRL', 'APOLLOTYRE', 'MRF',
        
        # Energy & Oil (15)
        'IOC', 'BPCL', 'HINDPETRO', 'GAIL', 'OIL', 'PETRONET',
        'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'ADANIENTS',
        'TATAPOWER', 'NHPC', 'SJVN', 'TORNTPOWER', 'CESC',
        
        # Metals & Mining (15)
        'TATASTEEL', 'JSWSTEEL', 'SAILSTEEL', 'HINDALCO', 'VEDL',
        'NMDC', 'COAL', 'JINDALSTEL', 'MOIL', 'WELCORP',
        'RATNAMANI', 'MANAPPURAM', 'MUTHOOTFIN', 'CHOLAFIN', 'PFC',
        
        # FMCG & Consumer (20)
        'ITC', 'BRITANNIA', 'DABUR', 'GODREJCP', 'MARICO',
        'COLPAL', 'PGHH', 'VBL', 'CCL', 'RADICO',
        'TATACONSUM', 'EMAMILTD', 'JYOTHYLAB', 'BAJAJCON', 'PAGEIND',
        'PIDILITIND', 'BERGER', 'KANSAINER', 'ASTRAL', 'RELAXO',
        
        # Infrastructure & Real Estate (15)
        'DLF', 'OBEROIRLTY', 'PRESTIGE', 'GODREJPROP', 'BRIGADE',
        'PHOENIXLTD', 'SOBHA', 'MINDSPACE', 'BROOKFIELD', 'EMBASSY',
        'IGARASHI', 'IRB', 'GMRINFRA', 'CONCOR', 'BHARATFORG',
        
        # Telecom & Media (10)
        'IDEA', 'RCOM', 'GTPL', 'SITI', 'HATHWAY',
        'DISHTV', 'TV18BRDCST', 'NETWORK18', 'ADANIPORTS', 'JSWENERGY',
        
        # Textiles & Apparel (10)
        'RTNPOWER', 'VARDHMAN', 'WELSPUNIND', 'RAYMOND', 'ARVIND',
        'GRASIM', 'ADITTYABIRLA', 'CENTURYTEX', 'KPR', 'SIYARAM',
        
        # Aviation & Logistics (10)
        'INDIGO', 'SPICEJET', 'BLUEDART', 'GLAND', 'ALLCARGO',
        'VTL', 'TCI', 'MAHLOG', 'GATI', 'SNOWMAN'
    ]
    
    logger.info(f"📊 EXPANDED SYMBOL LIST: {len(indices + stocks)} total symbols")
    return indices + stocks

def get_autonomous_symbol_status():
    """🎯 GET: Current autonomous trading symbol status and strategy"""
    return {
        "current_strategy": "news_impact_scalper",
        "active_symbols": get_complete_fo_symbols(),
        "symbol_count": len(get_complete_fo_symbols()),
        "status": "active",
        "last_update": "2025-07-31T04:10:45"
    }

def get_zerodha_symbol(internal_symbol: str) -> str:
    """🎯 DYNAMIC: Convert internal symbol to Zerodha's official symbol with auto-detection"""
    # First check static mappings
    if internal_symbol in ZERODHA_SYMBOL_MAPPING:
        zerodha_symbol = ZERODHA_SYMBOL_MAPPING[internal_symbol]
        logger.debug(f"🔄 STATIC MAPPING: {internal_symbol} → {zerodha_symbol}")
        return zerodha_symbol
    
    # Try dynamic detection if not in static mapping
    dynamic_symbol = _find_zerodha_symbol_dynamically(internal_symbol)
    if dynamic_symbol and dynamic_symbol != internal_symbol:
        # Cache the result for future use
        ZERODHA_SYMBOL_MAPPING[internal_symbol] = dynamic_symbol
        logger.info(f"✅ DYNAMIC MAPPING: {internal_symbol} → {dynamic_symbol} (auto-detected)")
        return dynamic_symbol
    
    # Fallback to original symbol
    logger.debug(f"📋 NO MAPPING: Using original symbol {internal_symbol}")
    return internal_symbol

def _find_zerodha_symbol_dynamically(truedata_symbol: str) -> str:
    """🎯 AUTO-DETECT: Find correct Zerodha symbol by comparing with instruments API"""
    try:
        # Get orchestrator instance to access Zerodha client
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            logger.debug(f"⚠️ Zerodha client not available for symbol detection: {truedata_symbol}")
            return None
        
        # Try to get instruments data
        if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
            try:
                # Get all NSE instruments
                nse_instruments = orchestrator.zerodha_client.kite.instruments('NSE')
                
                # Look for exact match first
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    if trading_symbol == truedata_symbol:
                        logger.info(f"✅ EXACT MATCH: {truedata_symbol} exists in Zerodha NSE")
                        return truedata_symbol
                
                # Look for similar symbols (fuzzy matching)
                candidates = []
                clean_target = _clean_symbol_for_comparison(truedata_symbol)
                
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    clean_candidate = _clean_symbol_for_comparison(trading_symbol)
                    
                    # Check for matches
                    if _symbols_are_similar(clean_target, clean_candidate):
                        candidates.append(trading_symbol)
                        if len(candidates) >= 5:  # Limit candidates
                            break
                
                # If we found candidates, return the best match
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
    # Exact match after cleaning
    if clean1 == clean2:
        return True
    
    # Check if one is contained in the other (for partial matches)
    if len(clean1) >= 4 and len(clean2) >= 4:
        if clean1 in clean2 or clean2 in clean1:
            return True
    
    # Check edit distance for close matches
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
    
    # Prefer exact matches after cleaning
    for candidate in candidates:
        if _clean_symbol_for_comparison(candidate) == clean_target:
            return candidate
    
    # Prefer symbols with same length
    same_length = [c for c in candidates if len(c) == len(target)]
    if same_length:
        return same_length[0]
    
    # Return shortest candidate (usually the base symbol)
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
    """🎯 DYNAMIC CHECK: Determine if F&O is enabled for a symbol.

    Long-term fix: use expanded F&O universe plus live Zerodha NFO instruments lookup,
    with a small in-memory cache to avoid repeated heavy calls.
    """
    try:
        # Normalize for comparison
        clean_symbol = symbol.replace('-I', '').replace('25', '').replace('26', '').strip().upper()

        # Block delisted/suspended symbols
        blocked_symbols = {'RCOM', 'RELCAPITAL', 'YESBANK', 'JETAIRWAYS'}
        if clean_symbol in blocked_symbols:
            logger.warning(f"🚫 BLOCKED SYMBOL: {clean_symbol} - Known delisted/suspended stock")
            _fo_enabled_cache[clean_symbol] = False
            return False

        # Cache hit
        if clean_symbol in _fo_enabled_cache:
            result = _fo_enabled_cache[clean_symbol]
            logger.info(f"🔍 F&O CHECK (cache): {symbol} → {clean_symbol} → {result}")
            return result

        # Baseline liquid universe (kept for conservative allow-list)
        top_50_liquid_fo = {
            'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX',
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
            'INFY', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT',
            'TECHM', 'BAJFINANCE', 'TITAN', 'WIPRO', 'ULTRACEMCO', 'NESTLEIND',
            'HINDUNILVR', 'POWERGRID', 'NTPC', 'COALINDIA', 'ONGC', 'SUNPHARMA',
            'DRREDDY', 'CIPLA', 'APOLLOHOSP', 'HCLTECH', 'INDUSINDBK', 'TATAMOTORS',
            'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'VEDL', 'ITC', 'BRITANNIA',
            'DABUR', 'GODREJCP', 'MARICO', 'IOC', 'BPCL', 'HINDPETRO',
            'GAIL', 'ADANIPORT', 'ADANIGREEN', 'PNB', 'FEDERALBNK',
            # Additional F&O enabled stocks from expanded universe
            'TVSMOTOR', 'ASHOKLEY', 'ESCORTS', 'MAHINDRA'
        }

        # Indices: always F&O enabled
        if clean_symbol in {'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX'}:
            _fo_enabled_cache[clean_symbol] = True
            logger.info(f"🔍 F&O CHECK: {symbol} → {clean_symbol} → True (index)")
            return True

        # Dynamic verification via Zerodha NFO instruments (authoritative)
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and getattr(orchestrator, 'zerodha_client', None) and getattr(orchestrator.zerodha_client, 'kite', None):
                instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                # Any NFO tradingsymbol beginning with the underlying indicates options availability
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

        # If broker lookup unavailable, conservatively allow only top_50 list; otherwise False
        if clean_symbol in top_50_liquid_fo:
            _fo_enabled_cache[clean_symbol] = True
            logger.info(f"🔍 F&O CHECK: {symbol} → {clean_symbol} → True (top-50 fallback)")
            return True

        _fo_enabled_cache[clean_symbol] = False
        logger.info(f"🔍 F&O CHECK: {symbol} → {clean_symbol} → False (not in NFO, not in top-50)")
        return False

    except Exception as e:
        logger.error(f"Error in is_fo_enabled for {symbol}: {e}")
        return False

def should_use_equity_only(symbol: str) -> bool:
    """🎯 CHECK: Whether to use equity only (no F&O) for a symbol"""
    # For symbols without F&O or during market hours restrictions
    return not is_fo_enabled(symbol)

def _is_options_symbol(symbol: str) -> bool:
    """🎯 CHECK: Whether symbol is an options contract"""
    # Check for CE/PE suffix and date pattern (e.g., TCS14AUG3000CE, NIFTY07AUG24800PE)
    import re
    if not ('CE' in symbol or 'PE' in symbol):
        return False
    
    # Look for date pattern: digits + 3 letters (e.g., 14AUG, 07JUL)
    date_pattern = re.search(r'\d{1,2}[A-Z]{3}', symbol)
    return date_pattern is not None

def validate_options_premium(symbol: str, price: float) -> bool:
    """🎯 VALIDATE: Options premium is within reasonable bounds"""
    if not _is_options_symbol(symbol):
        return True  # Not options, no validation needed
    
    # Options premium validation rules
    if price <= 0:
        return False
    if price > 1000:  # Max premium threshold
        logger.warning(f"⚠️ High options premium: {symbol} = ₹{price}")
        return True  # Allow but warn
    if price < 0.05:  # Min premium threshold
        return False
    
    return True

def get_complete_fo_symbols() -> List[str]:
    """🎯 GET: Complete list of F&O symbols for autonomous trading - EXPANDED"""
    # Major indices
    indices = [
        'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I', 'MIDCPNIFTY-I', 'SENSEX-I'
    ]
    
    # Major stocks with F&O - EXPANDED TO ~200 SYMBOLS
    stocks = [
        # Banking & Financial Services (25)
        'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
        'INFY', 'KOTAKBANK', 'LT', 'AXISBANK', 'MARUTI', 'ASIANPAINT',
        'TECHM', 'ADANIPORT', 'BAJFINANCE', 'TITAN', 'WIPRO', 'ULTRACEMCO',
        'NESTLEIND', 'HINDUNILVR', 'POWERGRID', 'NTPC', 'COALINDIA',
        'ONGC', 'SUNPHARMA', 'DRREDDY', 'CIPLA', 'APOLLOHOSP',
        'HCLTECH', 'INDUSINDBK', 'YESBANK', 'PNB', 'BANDHANBNK',
        
        # Auto & Auto Components (15)
        'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO',
        'TVSMOTOR', 'ASHOKLEY', 'ESCORTS', 'FORCEMOT', 'MAHINDRA',
        'BOSCHLTD', 'MOTHERSUMI', 'BALKRISIND', 'AMARAJABAT', 'CUMMINSIND',
        
        # IT & Technology (20)
        'MINDTREE', 'MPHASIS', 'LTTS', 'PERSISTENT', 'COFORGE',
        'RBLBANK', 'FEDERALBNK', 'IDFCFIRSTB', 'EQUITAS', 'SOUTHBANK',
        'INTELLECT', 'RAMPGREEN', 'ZOMATO', 'PAYTM', 'NAUKRI',
        'POLICYBZR', 'DMART', 'JUBLFOOD', 'DEVYANI', 'WESTLIFE',
        
        # Pharmaceuticals & Healthcare (20)
        'BIOCON', 'CADILAHC', 'LUPIN', 'GLENMARK', 'TORNTPHARM',
        'ALKEM', 'ABBOTINDIA', 'PFIZER', 'GLAXO', 'NOVARTIS',
        'AUROPHARMA', 'LALPATHLAB', 'METROPOLIS', 'THYROCARE', 'HEALTHINS',
        'FORTIS', 'MAXHEALTH', 'NARAYANHRL', 'APOLLOTYRE', 'MRF',
        
        # Energy & Oil (15)
        'IOC', 'BPCL', 'HINDPETRO', 'GAIL', 'OIL', 'PETRONET',
        'ADANIGREEN', 'ADANITRANS', 'ADANIPOWER', 'ADANIENTS',
        'TATAPOWER', 'NHPC', 'SJVN', 'TORNTPOWER', 'CESC',
        
        # Metals & Mining (15)
        'TATASTEEL', 'JSWSTEEL', 'SAILSTEEL', 'HINDALCO', 'VEDL',
        'NMDC', 'COAL', 'JINDALSTEL', 'MOIL', 'WELCORP',
        'RATNAMANI', 'MANAPPURAM', 'MUTHOOTFIN', 'CHOLAFIN', 'PFC',
        
        # FMCG & Consumer (20)
        'ITC', 'BRITANNIA', 'DABUR', 'GODREJCP', 'MARICO',
        'COLPAL', 'PGHH', 'VBL', 'CCL', 'RADICO',
        'TATACONSUM', 'EMAMILTD', 'JYOTHYLAB', 'BAJAJCON', 'PAGEIND',
        'PIDILITIND', 'BERGER', 'KANSAINER', 'ASTRAL', 'RELAXO',
        
        # Infrastructure & Real Estate (15)
        'DLF', 'OBEROIRLTY', 'PRESTIGE', 'GODREJPROP', 'BRIGADE',
        'PHOENIXLTD', 'SOBHA', 'MINDSPACE', 'BROOKFIELD', 'EMBASSY',
        'IGARASHI', 'IRB', 'GMRINFRA', 'CONCOR', 'BHARATFORG',
        
        # Telecom & Media (10)
        'IDEA', 'RCOM', 'GTPL', 'SITI', 'HATHWAY',
        'DISHTV', 'TV18BRDCST', 'NETWORK18', 'ADANIPORTS', 'JSWENERGY',
        
        # Textiles & Apparel (10)
        'RTNPOWER', 'VARDHMAN', 'WELSPUNIND', 'RAYMOND', 'ARVIND',
        'GRASIM', 'ADITTYABIRLA', 'CENTURYTEX', 'KPR', 'SIYARAM',
        
        # Aviation & Logistics (10)
        'INDIGO', 'SPICEJET', 'BLUEDART', 'GLAND', 'ALLCARGO',
        'VTL', 'TCI', 'MAHLOG', 'GATI', 'SNOWMAN'
    ]
    
    logger.info(f"📊 EXPANDED SYMBOL LIST: {len(indices + stocks)} total symbols")
    return indices + stocks

def get_autonomous_symbol_status():
    """🎯 GET: Current autonomous trading symbol status and strategy"""
    return {
        "current_strategy": "news_impact_scalper",
        "active_symbols": get_complete_fo_symbols(),
        "symbol_count": len(get_complete_fo_symbols()),
        "status": "active",
        "last_update": "2025-07-31T04:10:45"
    }

def get_zerodha_symbol(internal_symbol: str) -> str:
    """🎯 DYNAMIC: Convert internal symbol to Zerodha's official symbol with auto-detection"""
    # First check static mappings
    if internal_symbol in ZERODHA_SYMBOL_MAPPING:
        zerodha_symbol = ZERODHA_SYMBOL_MAPPING[internal_symbol]
        logger.debug(f"🔄 STATIC MAPPING: {internal_symbol} → {zerodha_symbol}")
        return zerodha_symbol
    
    # Try dynamic detection if not in static mapping
    dynamic_symbol = _find_zerodha_symbol_dynamically(internal_symbol)
    if dynamic_symbol and dynamic_symbol != internal_symbol:
        # Cache the result for future use
        ZERODHA_SYMBOL_MAPPING[internal_symbol] = dynamic_symbol
        logger.info(f"✅ DYNAMIC MAPPING: {internal_symbol} → {dynamic_symbol} (auto-detected)")
        return dynamic_symbol
    
    # Fallback to original symbol
    logger.debug(f"📋 NO MAPPING: Using original symbol {internal_symbol}")
    return internal_symbol

def _find_zerodha_symbol_dynamically(truedata_symbol: str) -> str:
    """🎯 AUTO-DETECT: Find correct Zerodha symbol by comparing with instruments API"""
    try:
        # Get orchestrator instance to access Zerodha client
        from src.core.orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        
        if not orchestrator or not orchestrator.zerodha_client:
            logger.debug(f"⚠️ Zerodha client not available for symbol detection: {truedata_symbol}")
            return None
        
        # Try to get instruments data
        if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
            try:
                # Get all NSE instruments
                nse_instruments = orchestrator.zerodha_client.kite.instruments('NSE')
                
                # Look for exact match first
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    if trading_symbol == truedata_symbol:
                        logger.info(f"✅ EXACT MATCH: {truedata_symbol} exists in Zerodha NSE")
                        return truedata_symbol
                
                # Look for similar symbols (fuzzy matching)
                candidates = []
                clean_target = _clean_symbol_for_comparison(truedata_symbol)
                
                for instrument in nse_instruments:
                    trading_symbol = instrument.get('tradingsymbol', '')
                    clean_candidate = _clean_symbol_for_comparison(trading_symbol)
                    
                    # Check for matches
                    if _symbols_are_similar(clean_target, clean_candidate):
                        candidates.append(trading_symbol)
                        if len(candidates) >= 5:  # Limit candidates
                            break
                
                # If we found candidates, return the best match
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
    # Exact match after cleaning
    if clean1 == clean2:
        return True
    
    # Check if one is contained in the other (for partial matches)
    if len(clean1) >= 4 and len(clean2) >= 4:
        if clean1 in clean2 or clean2 in clean1:
            return True
    
    # Check edit distance for close matches
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
    
    # Prefer exact matches after cleaning
    for candidate in candidates:
        if _clean_symbol_for_comparison(candidate) == clean_target:
            return candidate
    
    # Prefer symbols with same length
    same_length = [c for c in candidates if len(c) == len(target)]
    if same_length:
        return same_length[0]
    
    # Return shortest candidate (usually the base symbol)
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
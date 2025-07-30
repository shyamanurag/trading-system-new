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
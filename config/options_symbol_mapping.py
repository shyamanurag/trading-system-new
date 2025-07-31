"""
Options Symbol Mapping Functions
🎯 Handle TrueData ↔ Zerodha options symbol conversions
"""

import re
import logging

logger = logging.getLogger(__name__)

def get_options_symbol_mapping(truedata_symbol: str) -> str:
    """Convert TrueData options symbol to Zerodha format (and vice versa)"""
    # For now, assume they use the same format - but this can be updated when we discover differences
    # TrueData format: TCS14AUG3000CE
    # Zerodha format:  TCS14AUG3000CE (same)
    
    # If we discover format differences, we'll add conversion logic here
    return truedata_symbol

def get_truedata_options_format(underlying: str, expiry: str, strike: int, option_type: str) -> str:
    """Generate TrueData options symbol format for subscription"""
    # Generate symbol for TrueData subscription
    # Format: UNDERLYING + EXPIRY + STRIKE + TYPE
    # Example: TCS14AUG3000CE
    
    # Clean underlying symbol for TrueData
    clean_underlying = underlying.replace('-I', '')  # Remove index suffix
    
    return f"{clean_underlying}{expiry}{strike}{option_type}"

def convert_zerodha_to_truedata_options(zerodha_symbol: str) -> str:
    """Convert Zerodha options symbol to TrueData format"""
    # Currently they appear to be the same format
    # But if we discover differences during testing, we'll add conversion here
    return zerodha_symbol

def convert_truedata_to_zerodha_options(truedata_symbol: str) -> str:
    """Convert TrueData options symbol to Zerodha format"""
    # Currently they appear to be the same format
    # But if we discover differences during testing, we'll add conversion here
    return truedata_symbol

def is_valid_options_symbol(symbol: str) -> bool:
    """Check if symbol is a valid options contract"""
    if not ('CE' in symbol or 'PE' in symbol):
        return False
    
    # Look for date pattern: digits + 3 letters (e.g., 14AUG, 07JUL)
    date_pattern = re.search(r'\d{1,2}[A-Z]{3}', symbol)
    return date_pattern is not None

def extract_options_components(options_symbol: str) -> dict:
    """Extract underlying, expiry, strike, and type from options symbol"""
    try:
        # Pattern: UNDERLYING + DDMMM + STRIKE + TYPE
        # Example: TCS14AUG3000CE
        
        match = re.search(r'^([A-Z]+)(\d{1,2}[A-Z]{3})(\d+)(CE|PE)$', options_symbol)
        
        if match:
            return {
                'underlying': match.group(1),
                'expiry': match.group(2),
                'strike': int(match.group(3)),
                'option_type': match.group(4),
                'is_valid': True
            }
        else:
            logger.warning(f"Could not parse options symbol: {options_symbol}")
            return {'is_valid': False}
            
    except Exception as e:
        logger.error(f"Error extracting options components from {options_symbol}: {e}")
        return {'is_valid': False}
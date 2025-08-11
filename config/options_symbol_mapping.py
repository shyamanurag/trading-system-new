"""
Options Symbol Mapping Functions
🎯 Handle TrueData ↔ Zerodha options symbol conversions
"""

import re
import logging

logger = logging.getLogger(__name__)

def get_options_symbol_mapping(truedata_symbol: str) -> str:
    """Convert TrueData options symbol to Zerodha format (and vice versa)"""
    # CRITICAL: Different formats discovered!
    # TrueData format:  BANKNIFTY221006237000CE (SYMBOL + YYMMDD + STRIKE + TYPE)  
    # Zerodha format:   BANKNIFTY06OCT237000CE  (SYMBOL + DDMMM + STRIKE + TYPE)
    
    try:
        # Parse TrueData format and convert to Zerodha
        components = extract_options_components(truedata_symbol)
        if components.get('is_valid'):
            return convert_truedata_to_zerodha_options(truedata_symbol)
        else:
            # If parsing fails, assume it's already in correct format
            return truedata_symbol
    except:
        return truedata_symbol

def get_truedata_options_format(underlying: str, expiry: str, strike: int, option_type: str) -> str:
    """Generate TrueData options symbol format for subscription"""
    # Generate symbol for TrueData subscription
    # TrueData Format: UNDERLYING + YYMMDD + STRIKE + TYPE
    # Example: TCS220814003000CE (for 14-AUG-2022)
    
    # Clean underlying symbol for TrueData
    clean_underlying = underlying.replace('-I', '')  # Remove index suffix
    
    # Convert expiry from Zerodha format (14AUG) to TrueData format (YYMMDD)
    truedata_expiry = convert_expiry_to_truedata_format(expiry)
    
    return f"{clean_underlying}{truedata_expiry}{strike:05d}{option_type}"

def convert_expiry_to_truedata_format(expiry: str) -> str:
    """Convert expiry from Zerodha format (14AUG) to TrueData format (220814)"""
    try:
        import re
        from datetime import datetime
        
        # Parse Zerodha expiry: 14AUG or 14AUG25
        match = re.search(r'^(\d{1,2})([A-Z]{3})(?:\d{2})?$', expiry)
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            
            # Convert month name to number
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            month = month_map.get(month_str, 8)  # Default to August
            
            # Determine year (assume current or next year based on month)
            current_year = datetime.now().year
            year = current_year if month >= datetime.now().month else current_year + 1
            
            # Format as TrueData: YYMMDD
            return f"{year % 100:02d}{month:02d}{day:02d}"
        else:
            logger.warning(f"Could not parse expiry format: {expiry}")
            return "220814"  # Fallback
            
    except Exception as e:
        logger.error(f"Error converting expiry to TrueData format: {e}")
        return "220814"  # Fallback

def convert_zerodha_to_truedata_options(zerodha_symbol: str) -> str:
    """Convert Zerodha options symbol to TrueData format"""
    # Convert: NTPC14AUG25350CE -> NTPC250814350CE
    # From: SYMBOL + DDMMMYY + STRIKE + TYPE
    # To:   SYMBOL + YYMMDD + STRIKE + TYPE
    
    try:
        import re
        from datetime import datetime
        
        # Parse Zerodha format: NTPC14AUG25350CE (with year)
        # First try with year included
        match = re.search(r'^([A-Z&]+)(\d{1,2})([A-Z]{3})(\d{2})(\d+)(CE|PE)$', zerodha_symbol)
        
        if match:
            underlying = match.group(1)
            day = int(match.group(2))
            month_str = match.group(3)
            year = int(match.group(4)) + 2000  # Convert YY to YYYY
            strike = match.group(5)
            option_type = match.group(6)
            
            # Convert month name to number
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            month = month_map.get(month_str, 1)
            
            # Format as TrueData: YYMMDD
            truedata_date = f"{year % 100:02d}{month:02d}{day:02d}"
            
            logger.debug(f"📊 Zerodha→TrueData: {zerodha_symbol} → {underlying}{truedata_date}{strike}{option_type}")
            return f"{underlying}{truedata_date}{strike}{option_type}"
        
        # Fallback: Try without year (old format)
        match = re.search(r'^([A-Z&]+)(\d{1,2})([A-Z]{3})(\d+)(CE|PE)$', zerodha_symbol)
        
        if match:
            underlying = match.group(1)
            day = int(match.group(2))
            month_str = match.group(3)
            strike = match.group(4)
            option_type = match.group(5)
            
            # Convert month name to number
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            month = month_map.get(month_str, 1)
            
            # Determine year (assume current or next year based on month)
            current_year = datetime.now().year
            year = current_year if month >= datetime.now().month else current_year + 1
            
            # Format as TrueData: YYMMDD
            truedata_date = f"{year % 100:02d}{month:02d}{day:02d}"
            
            return f"{underlying}{truedata_date}{strike}{option_type}"
        else:
            logger.warning(f"Could not parse Zerodha symbol: {zerodha_symbol}")
            return zerodha_symbol
            
    except Exception as e:
        logger.error(f"Error converting Zerodha to TrueData format: {e}")
        return zerodha_symbol

def convert_truedata_to_zerodha_options(truedata_symbol: str) -> str:
    """Convert TrueData options symbol to Zerodha format"""
    # Convert: BANKNIFTY221006237000CE -> BANKNIFTY06OCT237000CE
    # From: SYMBOL + YYMMDD + STRIKE + TYPE  
    # To:   SYMBOL + DDMMM + STRIKE + TYPE
    
    try:
        import re
        from datetime import datetime
        
        # Parse TrueData format: BANKNIFTY221006237000CE
        match = re.search(r'^([A-Z&]+)(\d{6})(\d+)(CE|PE)$', truedata_symbol)
        
        if match:
            underlying = match.group(1)
            date_str = match.group(2)  # YYMMDD
            strike = match.group(3)
            option_type = match.group(4)
            
            # Parse date
            year = 2000 + int(date_str[:2])
            month = int(date_str[2:4]) 
            day = int(date_str[4:6])
            
            # Convert to month name
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            month_str = month_names[month - 1]
            
            # Format as Zerodha: YYMMM (year first, not day first)
            year_short = str(year)[-2:]  # Last 2 digits of year (e.g., 2025 -> 25)
            zerodha_date = f"{year_short}{month_str}"
            
            # Remove leading zeros from strike for Zerodha format
            strike_clean = str(int(strike))
            
            return f"{underlying}{zerodha_date}{strike_clean}{option_type}"
        else:
            logger.warning(f"Could not parse TrueData symbol: {truedata_symbol}")
            return truedata_symbol
            
    except Exception as e:
        logger.error(f"Error converting TrueData to Zerodha format: {e}")
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
"""
TrueData Configuration for Trading System
"""
import os
from typing import Dict, Any

# TrueData Configuration
TRUEDATA_CONFIG = {
    'username': os.getenv('TRUEDATA_USERNAME', 'your_username'),
    'password': os.getenv('TRUEDATA_PASSWORD', 'your_password'),
    'live_port': int(os.getenv('TRUEDATA_LIVE_PORT', 8084)),
    'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
    'log_level': os.getenv('TRUEDATA_LOG_LEVEL', 'INFO'),
    'is_sandbox': os.getenv('TRUEDATA_IS_SANDBOX', 'false').lower() == 'true',
    'data_timeout': int(os.getenv('TRUEDATA_DATA_TIMEOUT', 60)),
    'retry_attempts': int(os.getenv('TRUEDATA_RETRY_ATTEMPTS', 3)),
    'retry_delay': int(os.getenv('TRUEDATA_RETRY_DELAY', 5)),
    'redis_host': os.getenv('REDIS_HOST', 'localhost'),
    'redis_port': int(os.getenv('REDIS_PORT', 6379)),
    'redis_db': int(os.getenv('REDIS_DB', 0)),
    'max_connection_attempts': int(os.getenv('TRUEDATA_MAX_CONNECTION_ATTEMPTS', 3))
}

# Sandbox Configuration (for testing)
TRUEDATA_SANDBOX_CONFIG = {
    'username': os.getenv('TRUEDATA_SANDBOX_USERNAME', 'sandbox_username'),
    'password': os.getenv('TRUEDATA_SANDBOX_PASSWORD', 'sandbox_password'),
    'live_port': int(os.getenv('TRUEDATA_SANDBOX_LIVE_PORT', 8086)),
    'url': os.getenv('TRUEDATA_SANDBOX_URL', 'sandbox.truedata.in'),
    'log_level': 'DEBUG',
    'is_sandbox': True,
    'data_timeout': 30,
    'retry_attempts': 2,
    'retry_delay': 3,
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 1,  # Use different DB for sandbox
    'max_connection_attempts': 2
}

# Default symbols for testing
DEFAULT_SYMBOLS = [
    'NIFTY-I',
    'BANKNIFTY-I',
    'RELIANCE',
    'TCS',
    'INFY',
    'HDFC',
    'ICICIBANK',
    'HINDUNILVR',
    'ITC',
    'SBIN'
]

# Options symbols
OPTIONS_SYMBOLS = [
    'NIFTY',
    'BANKNIFTY',
    'FINNIFTY'
]

# Bar sizes for historical data
BAR_SIZES = [
    '1 min',
    '5 min',
    '15 min',
    '30 min',
    '1 hour',
    '1 day'
]

def get_config(is_sandbox: bool = False) -> Dict[str, Any]:
    """
    Get TrueData configuration based on environment
    
    Args:
        is_sandbox: Whether to use sandbox configuration
        
    Returns:
        Configuration dictionary
    """
    if is_sandbox:
        return TRUEDATA_SANDBOX_CONFIG.copy()
    return TRUEDATA_CONFIG.copy()

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate TrueData configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['username', 'password', 'live_port', 'url']
    
    for field in required_fields:
        if field not in config or not config[field]:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Validate port number
    if not (1024 <= config['live_port'] <= 65535):
        print(f"❌ Invalid port number: {config['live_port']}")
        return False
    
    print("✅ TrueData configuration is valid")
    return True

def print_config(config: Dict[str, Any], hide_password: bool = True):
    """
    Print configuration (with option to hide password)
    
    Args:
        config: Configuration dictionary
        hide_password: Whether to hide password in output
    """
    print("TrueData Configuration:")
    print("-" * 30)
    
    for key, value in config.items():
        if key == 'password' and hide_password:
            print(f"{key}: {'*' * len(str(value))}")
        else:
            print(f"{key}: {value}")
    
    print("-" * 30)

if __name__ == "__main__":
    # Test configuration
    print("Testing TrueData Configuration...")
    
    # Test production config
    prod_config = get_config(is_sandbox=False)
    print("\nProduction Configuration:")
    print_config(prod_config)
    validate_config(prod_config)
    
    # Test sandbox config
    sandbox_config = get_config(is_sandbox=True)
    print("\nSandbox Configuration:")
    print_config(sandbox_config)
    validate_config(sandbox_config)
    
    print(f"\nDefault Symbols: {DEFAULT_SYMBOLS}")
    print(f"Options Symbols: {OPTIONS_SYMBOLS}")
    print(f"Bar Sizes: {BAR_SIZES}") 
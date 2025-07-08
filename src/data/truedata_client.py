#!/usr/bin/env python3
"""
TrueData Client Bridge - CRITICAL FIX for import path conflicts
Bridges API endpoints to the working TrueData client in data/truedata_client.py
"""

# Import from the working TrueData client
from data.truedata_client import (
    truedata_client,
    live_market_data,
    initialize_truedata,
    get_truedata_status,
    is_connected,
    get_live_data_for_symbol,
    get_all_live_data,
    subscribe_to_symbols,
    force_disconnect_truedata
)

def get_truedata_client():
    """Get the working TrueData client instance"""
    return truedata_client

def init_truedata_client():
    """Initialize the TrueData client"""
    return initialize_truedata()

# Export all necessary functions and data
__all__ = [
    'truedata_client',
    'live_market_data', 
    'initialize_truedata',
    'get_truedata_status',
    'is_connected',
    'get_live_data_for_symbol',
    'get_all_live_data',
    'subscribe_to_symbols',
    'force_disconnect_truedata',
    'get_truedata_client',
    'init_truedata_client'
] 
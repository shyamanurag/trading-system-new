"""
Shared TrueData Connection Manager
==================================
Solves the "User Already Connected" error by allowing autonomous system
to use existing TrueData connection instead of creating duplicate connections.
"""

import logging
import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SharedTrueDataManager:
    """
    Manages shared access to TrueData connection
    Prevents duplicate connections and "User Already Connected" errors
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self.primary_connection = None
        self.live_market_data = {}
        self.connection_status = {
            'connected': False,
            'last_update': None,
            'symbols_count': 0,
            'data_source': 'none'
        }
        self.subscribers = []
        self._data_lock = threading.Lock()
        
        logger.info("🔄 SharedTrueDataManager initialized")
    
    def register_existing_connection(self, connection_data: Dict[str, Any]) -> bool:
        """
        Register an existing TrueData connection for sharing
        
        Args:
            connection_data: Dictionary containing live market data and connection info
            
        Returns:
            bool: True if successfully registered
        """
        try:
            with self._data_lock:
                # Store the live market data reference
                self.live_market_data = connection_data.get('live_data', {})
                
                # Update connection status
                self.connection_status = {
                    'connected': True,
                    'last_update': datetime.now().isoformat(),
                    'symbols_count': len(self.live_market_data),
                    'data_source': connection_data.get('source', 'external_truedata')
                }
                
                logger.info(f"✅ Registered existing TrueData connection with {len(self.live_market_data)} symbols")
                logger.info(f"   Data source: {self.connection_status['data_source']}")
                
                # Notify subscribers
                self._notify_subscribers('connection_established', self.connection_status)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to register existing connection: {e}")
            return False
    
    def connect_to_existing_truedata(self) -> bool:
        """
        Connect to existing TrueData by looking for active connections
        """
        try:
            logger.info("🔍 Searching for existing TrueData connections...")
            
            # Method 1: Try to import and access existing truedata_client
            try:
                from data.truedata_client import live_market_data, get_truedata_status
                
                status = get_truedata_status()
                if status.get('connected', False):
                    logger.info("🎉 Found existing TrueData connection!")
                    
                    # Register the existing connection
                    connection_data = {
                        'live_data': live_market_data,
                        'source': 'existing_truedata_client'
                    }
                    
                    return self.register_existing_connection(connection_data)
                    
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")
            
            # Method 2: Try to find TrueData through environment or global state
            try:
                # Check if there's a global TrueData instance
                import sys
                for module_name, module in sys.modules.items():
                    if hasattr(module, 'live_market_data') and hasattr(module, 'connected'):
                        if getattr(module, 'connected', False):
                            logger.info(f"🎉 Found TrueData connection in module: {module_name}")
                            
                            connection_data = {
                                'live_data': getattr(module, 'live_market_data', {}),
                                'source': f'global_module_{module_name}'
                            }
                            
                            return self.register_existing_connection(connection_data)
                            
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")
            
            # Method 3: Use external API to get data (if available)
            try:
                # This will be implemented if needed
                pass
                
            except Exception as e:
                logger.warning(f"Method 3 failed: {e}")
            
            logger.warning("❌ No existing TrueData connection found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error connecting to existing TrueData: {e}")
            return False
    
    def get_market_data(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market data from shared connection
        
        Args:
            symbol: Specific symbol to get data for, or None for all data
            
        Returns:
            Dict containing market data
        """
        try:
            with self._data_lock:
                if not self.connection_status['connected']:
                    logger.warning("⚠️ No TrueData connection available")
                    return {}
                
                if symbol:
                    # Get specific symbol data
                    symbol_data = self.live_market_data.get(symbol, {})
                    if symbol_data:
                        logger.debug(f"📊 Retrieved data for {symbol}: LTP={symbol_data.get('ltp', 'N/A')}")
                    return symbol_data
                else:
                    # Get all market data
                    logger.debug(f"📊 Retrieved all market data: {len(self.live_market_data)} symbols")
                    return self.live_market_data.copy()
                    
        except Exception as e:
            logger.error(f"❌ Error getting market data: {e}")
            return {}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        with self._data_lock:
            return self.connection_status.copy()
    
    def subscribe_to_updates(self, callback):
        """Subscribe to connection updates"""
        self.subscribers.append(callback)
        logger.info(f"📢 New subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def _notify_subscribers(self, event_type: str, data: Any):
        """Notify all subscribers of updates"""
        for callback in self.subscribers:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"❌ Error notifying subscriber: {e}")
    
    def start_periodic_status_check(self, interval: int = 30):
        """Start periodic status checking"""
        def status_checker():
            while True:
                try:
                    time.sleep(interval)
                    
                    # Update connection status
                    if self.connection_status['connected']:
                        with self._data_lock:
                            self.connection_status['last_update'] = datetime.now().isoformat()
                            self.connection_status['symbols_count'] = len(self.live_market_data)
                        
                        logger.debug(f"📊 Status check: {self.connection_status['symbols_count']} symbols active")
                    
                except Exception as e:
                    logger.error(f"❌ Status checker error: {e}")
        
        # Start status checker in background thread
        status_thread = threading.Thread(target=status_checker, daemon=True)
        status_thread.start()
        logger.info(f"📊 Started periodic status check (interval: {interval}s)")

# Global instance
shared_truedata_manager = SharedTrueDataManager()

def get_shared_truedata_manager() -> SharedTrueDataManager:
    """Get the shared TrueData manager instance"""
    return shared_truedata_manager

def initialize_shared_truedata():
    """Initialize shared TrueData connection"""
    manager = get_shared_truedata_manager()
    
    # Try to connect to existing TrueData
    success = manager.connect_to_existing_truedata()
    
    if success:
        # Start periodic status monitoring
        manager.start_periodic_status_check()
        logger.info("🎉 Shared TrueData manager initialized successfully")
    else:
        logger.warning("⚠️ Shared TrueData manager initialized but no connection found")
    
    return success 
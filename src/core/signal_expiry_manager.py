"""
Signal Expiry Manager
=====================
Manages signal expiry and execution throttling to prevent stale signals from executing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SignalExpiryManager:
    """
    Manages signal expiry and execution throttling.
    
    Features:
    - Signal expiry after 5 minutes (configurable)
    - Execution throttling: 30 seconds between same-symbol executions
    - Prevents stale signals from executing
    """
    
    def __init__(self):
        self.signal_creation_times: Dict[str, datetime] = {}  # signal_id -> creation_time
        self.last_execution_times: Dict[str, datetime] = {}  # symbol -> last_execution_time
        
        # Configuration
        self.signal_expiry_seconds = 300  # 5 minutes
        self.execution_throttle_seconds = 30  # 30 seconds between same-symbol executions
        
        logger.info("✅ Signal Expiry Manager initialized")
    
    def is_signal_expired(self, signal: Dict) -> bool:
        """Check if a signal has expired"""
        try:
            signal_id = signal.get('signal_id', '')
            
            # Check if we have a creation time for this signal
            if signal_id in self.signal_creation_times:
                creation_time = self.signal_creation_times[signal_id]
                age_seconds = (datetime.now() - creation_time).total_seconds()
                
                if age_seconds > self.signal_expiry_seconds:
                    logger.warning(f"⏰ EXPIRED SIGNAL: {signal_id} is {age_seconds:.0f}s old (max {self.signal_expiry_seconds}s)")
                    return True
            
            # Also check timestamp in metadata
            metadata = signal.get('metadata', {})
            timestamp_str = metadata.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_seconds = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds()
                    
                    if age_seconds > self.signal_expiry_seconds:
                        logger.warning(f"⏰ EXPIRED SIGNAL: {signal.get('symbol')} is {age_seconds:.0f}s old")
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signal expiry: {e}")
            return False
    
    def can_execute(self, symbol: str) -> bool:
        """Check if we can execute a trade for this symbol (throttling check)"""
        try:
            if symbol not in self.last_execution_times:
                return True
            
            last_execution = self.last_execution_times[symbol]
            seconds_since_last = (datetime.now() - last_execution).total_seconds()
            
            if seconds_since_last < self.execution_throttle_seconds:
                logger.info(f"⏳ THROTTLED: {symbol} - {seconds_since_last:.0f}s since last execution (min {self.execution_throttle_seconds}s)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking execution throttle: {e}")
            return True  # Allow execution on error
    
    def record_signal_creation(self, signal_id: str):
        """Record when a signal was created"""
        self.signal_creation_times[signal_id] = datetime.now()
    
    def record_execution(self, symbol: str):
        """Record when a trade was executed for a symbol"""
        self.last_execution_times[symbol] = datetime.now()
    
    def cleanup_old_records(self):
        """Remove old records to prevent memory buildup"""
        try:
            now = datetime.now()
            cutoff = now - timedelta(hours=1)
            
            # Cleanup signal creation times
            expired_signals = [
                sig_id for sig_id, time in self.signal_creation_times.items()
                if time < cutoff
            ]
            for sig_id in expired_signals:
                del self.signal_creation_times[sig_id]
            
            # Cleanup execution times
            old_executions = [
                symbol for symbol, time in self.last_execution_times.items()
                if time < cutoff
            ]
            for symbol in old_executions:
                del self.last_execution_times[symbol]
            
            if expired_signals or old_executions:
                logger.debug(f"🧹 Cleaned up {len(expired_signals)} expired signals, {len(old_executions)} old executions")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global instance
signal_expiry_manager = SignalExpiryManager()


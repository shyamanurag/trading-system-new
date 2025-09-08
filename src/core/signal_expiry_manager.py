#!/usr/bin/env python3
"""
Signal Expiry and Execution Throttling Manager
==============================================
Ensures signals are valid only for 5 minutes and execution attempts are throttled to 30 seconds
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class SignalExpiryManager:
    """Manages signal expiry and execution throttling"""
    
    def __init__(self):
        # Signal expiry configuration
        self.signal_ttl_seconds = 300  # 5 minutes
        
        # Execution throttling configuration  
        self.execution_throttle_seconds = 30  # 30 seconds between execution attempts
        
        # In-memory tracking
        self.signal_memory = {}  # signal_id -> {created_at, last_execution_attempt, attempts}
        self.symbol_execution_history = {}  # symbol -> {last_attempt_time, attempts}
        
        logger.info("✅ Signal Expiry Manager initialized")
        logger.info(f"   📅 Signal TTL: {self.signal_ttl_seconds} seconds (5 minutes)")
        logger.info(f"   ⏱️ Execution throttle: {self.execution_throttle_seconds} seconds")
    
    def add_signal(self, signal: Dict) -> bool:
        """Add a new signal to tracking"""
        try:
            signal_id = signal.get('signal_id')
            if not signal_id:
                # Generate signal ID if not present
                symbol = signal.get('symbol', 'UNKNOWN')
                action = signal.get('action', 'BUY')
                timestamp = int(time.time())
                signal_id = f"{symbol}_{action}_{timestamp}"
                signal['signal_id'] = signal_id
            
            current_time = datetime.now()
            
            # Add to memory
            self.signal_memory[signal_id] = {
                'signal': signal.copy(),
                'created_at': current_time,
                'last_execution_attempt': None,
                'attempts': 0,
                'expired': False
            }
            
            logger.info(f"📝 Signal added to tracking: {signal_id} (expires in {self.signal_ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding signal to tracking: {e}")
            return False
    
    def is_signal_expired(self, signal: Dict) -> bool:
        """Check if a signal has expired (older than 5 minutes)"""
        try:
            signal_id = signal.get('signal_id')
            if not signal_id:
                return True  # No ID = treat as expired
            
            if signal_id not in self.signal_memory:
                # Check generated_at timestamp from signal
                generated_at = signal.get('generated_at')
                if generated_at:
                    try:
                        if isinstance(generated_at, str):
                            gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                        else:
                            gen_time = generated_at
                        
                        age_seconds = (datetime.now() - gen_time).total_seconds()
                        is_expired = age_seconds > self.signal_ttl_seconds
                        
                        if is_expired:
                            logger.info(f"⏰ Signal expired: {signal.get('symbol')} (age: {age_seconds:.1f}s)")
                        
                        return is_expired
                        
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Could not parse generated_at time: {parse_error}")
                        return True  # Treat unparseable as expired
                
                return True  # No tracking info = treat as expired
            
            # Check tracked signal
            signal_info = self.signal_memory[signal_id]
            age_seconds = (datetime.now() - signal_info['created_at']).total_seconds()
            is_expired = age_seconds > self.signal_ttl_seconds
            
            if is_expired and not signal_info['expired']:
                signal_info['expired'] = True
                logger.info(f"⏰ Signal expired: {signal.get('symbol')} (age: {age_seconds:.1f}s)")
            
            return is_expired
            
        except Exception as e:
            logger.error(f"❌ Error checking signal expiry: {e}")
            return True  # On error, treat as expired for safety
    
    def can_execute_signal(self, signal: Dict) -> bool:
        """Check if signal can be executed (not throttled)"""
        try:
            symbol = signal.get('symbol')
            if not symbol:
                return False
            
            current_time = datetime.now()
            
            # Check symbol-level throttling
            if symbol in self.symbol_execution_history:
                last_attempt = self.symbol_execution_history[symbol]['last_attempt_time']
                time_since_last = (current_time - last_attempt).total_seconds()
                
                if time_since_last < self.execution_throttle_seconds:
                    remaining_time = self.execution_throttle_seconds - time_since_last
                    logger.info(f"⏳ Execution throttled for {symbol}: {remaining_time:.1f}s remaining")
                    return False
            
            # Check signal-level throttling
            signal_id = signal.get('signal_id')
            if signal_id and signal_id in self.signal_memory:
                signal_info = self.signal_memory[signal_id]
                if signal_info['last_execution_attempt']:
                    time_since_last = (current_time - signal_info['last_execution_attempt']).total_seconds()
                    
                    if time_since_last < self.execution_throttle_seconds:
                        remaining_time = self.execution_throttle_seconds - time_since_last
                        logger.info(f"⏳ Signal execution throttled: {signal_id} ({remaining_time:.1f}s remaining)")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking execution throttle: {e}")
            return False  # On error, don't allow execution for safety
    
    def record_execution_attempt(self, signal: Dict) -> None:
        """Record an execution attempt for throttling purposes"""
        try:
            symbol = signal.get('symbol')
            signal_id = signal.get('signal_id')
            current_time = datetime.now()
            
            # Record symbol-level attempt
            if symbol:
                if symbol not in self.symbol_execution_history:
                    self.symbol_execution_history[symbol] = {
                        'last_attempt_time': current_time,
                        'attempts': 1
                    }
                else:
                    self.symbol_execution_history[symbol]['last_attempt_time'] = current_time
                    self.symbol_execution_history[symbol]['attempts'] += 1
            
            # Record signal-level attempt
            if signal_id and signal_id in self.signal_memory:
                self.signal_memory[signal_id]['last_execution_attempt'] = current_time
                self.signal_memory[signal_id]['attempts'] += 1
            
            logger.info(f"📊 Execution attempt recorded: {symbol} (signal: {signal_id})")
            
        except Exception as e:
            logger.error(f"❌ Error recording execution attempt: {e}")
    
    def filter_valid_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals to only include valid (non-expired, non-throttled) ones"""
        if not signals:
            return []
        
        valid_signals = []
        expired_count = 0
        throttled_count = 0
        
        for signal in signals:
            # Check expiry first
            if self.is_signal_expired(signal):
                expired_count += 1
                continue
            
            # Check throttling
            if not self.can_execute_signal(signal):
                throttled_count += 1
                continue
            
            # Signal is valid
            valid_signals.append(signal)
        
        # Log filtering results
        if expired_count > 0:
            logger.info(f"🗑️ Filtered out {expired_count} expired signals (>5 minutes old)")
        
        if throttled_count > 0:
            logger.info(f"⏳ Filtered out {throttled_count} throttled signals (<30s since last attempt)")
        
        if valid_signals:
            logger.info(f"✅ {len(valid_signals)} valid signals ready for execution")
        
        return valid_signals
    
    def cleanup_expired_signals(self) -> None:
        """Clean up expired signals from memory"""
        try:
            current_time = datetime.now()
            expired_signal_ids = []
            expired_symbols = []
            
            # Clean up signal memory
            for signal_id, signal_info in list(self.signal_memory.items()):
                age_seconds = (current_time - signal_info['created_at']).total_seconds()
                if age_seconds > self.signal_ttl_seconds * 2:  # Clean up after 10 minutes
                    expired_signal_ids.append(signal_id)
            
            for signal_id in expired_signal_ids:
                del self.signal_memory[signal_id]
            
            # Clean up symbol execution history (older than 1 hour)
            for symbol, history in list(self.symbol_execution_history.items()):
                age_seconds = (current_time - history['last_attempt_time']).total_seconds()
                if age_seconds > 3600:  # 1 hour
                    expired_symbols.append(symbol)
            
            for symbol in expired_symbols:
                del self.symbol_execution_history[symbol]
            
            if expired_signal_ids or expired_symbols:
                logger.info(f"🧹 Cleaned up {len(expired_signal_ids)} expired signals and {len(expired_symbols)} old symbol histories")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def get_signal_stats(self) -> Dict:
        """Get statistics about signal tracking"""
        try:
            current_time = datetime.now()
            
            active_signals = 0
            expired_signals = 0
            
            for signal_info in self.signal_memory.values():
                age_seconds = (current_time - signal_info['created_at']).total_seconds()
                if age_seconds <= self.signal_ttl_seconds:
                    active_signals += 1
                else:
                    expired_signals += 1
            
            return {
                'active_signals': active_signals,
                'expired_signals': expired_signals,
                'total_tracked': len(self.signal_memory),
                'symbols_with_history': len(self.symbol_execution_history),
                'signal_ttl_seconds': self.signal_ttl_seconds,
                'execution_throttle_seconds': self.execution_throttle_seconds
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting signal stats: {e}")
            return {}

# Global instance
signal_expiry_manager = SignalExpiryManager()

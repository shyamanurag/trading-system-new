"""
Signal Deduplication and Quality Filtering System
=================================================
Prevents multiple signals for the same symbol at the same timestamp
Implements signal quality scoring and filtering
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class SignalDeduplicator:
    """Handles signal deduplication and quality filtering"""
    
    def __init__(self):
        self.recent_signals = defaultdict(list)  # symbol -> list of recent signals
        self.signal_history = {}  # signal_id -> signal data
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.now()
        
        # Quality thresholds - BALANCED FOR PRODUCTION TRADING
        self.min_confidence_threshold = 0.65  # Slightly lowered to capture 0.65 confidence signals
        self.max_signals_per_symbol = 2  # Allow 2 signals per symbol per period 
        self.deduplication_window = 30  # Reduced to 30 seconds window
        
    def process_signals(self, signals: List[Dict]) -> List[Dict]:
        """Process and deduplicate signals, return only high-quality unique signals"""
        if not signals:
            return []
        
        # Clean up old signals periodically
        self._cleanup_old_signals()
        
        # Filter by quality first
        quality_signals = self._filter_by_quality(signals)
        
        # Deduplicate by symbol
        deduplicated_signals = self._deduplicate_by_symbol(quality_signals)
        
        # Check for timestamp collisions and resolve
        final_signals = self._resolve_timestamp_collisions(deduplicated_signals)
        
        # Update signal history
        self._update_signal_history(final_signals)
        
        logger.info(f"📊 Signal Processing: {len(signals)} → {len(quality_signals)} → {len(final_signals)}")
        
        return final_signals
    
    def _filter_by_quality(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals by quality thresholds"""
        quality_signals = []
        rejection_stats = {
            'low_confidence': 0,
            'missing_fields': 0,
            'invalid_prices': 0,
            'poor_risk_reward': 0
        }
        
        for signal in signals:
            confidence = signal.get('confidence', 0)
            
            # Check minimum confidence
            if confidence < self.min_confidence_threshold:
                rejection_stats['low_confidence'] += 1
                logger.debug(f"❌ Signal rejected - low confidence: {signal['symbol']} ({confidence:.2f} < {self.min_confidence_threshold})")
                continue
            
            # Check for required fields
            required_fields = ['symbol', 'action', 'entry_price', 'stop_loss', 'target']
            if not all(field in signal for field in required_fields):
                rejection_stats['missing_fields'] += 1
                logger.debug(f"❌ Signal rejected - missing fields: {signal.get('symbol', 'UNKNOWN')}")
                continue
            
            # Check for reasonable price levels
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            target = signal.get('target', 0)
            
            if not all([entry_price > 0, stop_loss > 0, target > 0]):
                rejection_stats['invalid_prices'] += 1
                logger.debug(f"❌ Signal rejected - invalid prices: {signal['symbol']}")
                continue
            
            # Check risk-reward ratio
            if signal['action'] == 'BUY':
                risk = entry_price - stop_loss
                reward = target - entry_price
            else:  # SELL
                risk = stop_loss - entry_price
                reward = entry_price - target
            
            if risk <= 0 or reward <= 0:
                rejection_stats['invalid_prices'] += 1
                logger.debug(f"❌ Signal rejected - invalid risk/reward: {signal['symbol']}")
                continue
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 1.5:  # ADJUSTED: Minimum 1.5:1 profit-to-loss ratio for current market
                rejection_stats['poor_risk_reward'] += 1
                logger.debug(f"❌ Signal rejected - poor risk/reward: {signal['symbol']} ({risk_reward_ratio:.2f} < 1.5)")
                continue
            
            quality_signals.append(signal)
        
        # Log summary of rejections
        if any(rejection_stats.values()):
            logger.info(f"📊 Quality Filter Results: {len(quality_signals)} passed, {sum(rejection_stats.values())} rejected")
            for reason, count in rejection_stats.items():
                if count > 0:
                    logger.info(f"   - {reason}: {count} signals")
        
        return quality_signals
    
    def _deduplicate_by_symbol(self, signals: List[Dict]) -> List[Dict]:
        """Remove duplicate signals for the same symbol, keep highest confidence"""
        symbol_signals = defaultdict(list)
        
        # Group signals by symbol
        for signal in signals:
            symbol = signal['symbol']
            symbol_signals[symbol].append(signal)
        
        deduplicated = []
        
        for symbol, symbol_signal_list in symbol_signals.items():
            # Check if we already have recent signals for this symbol
            recent_count = len([s for s in self.recent_signals[symbol] 
                              if (datetime.now() - s['timestamp']).total_seconds() < self.deduplication_window])
            
            if recent_count >= self.max_signals_per_symbol:
                logger.debug(f"❌ Signal rejected - too many recent signals: {symbol}")
                continue
            
            # If multiple signals for same symbol, keep the highest confidence
            if len(symbol_signal_list) > 1:
                best_signal = max(symbol_signal_list, key=lambda s: s.get('confidence', 0))
                logger.info(f"🔄 Deduplication: {symbol} - kept best of {len(symbol_signal_list)} signals")
                deduplicated.append(best_signal)
            else:
                deduplicated.append(symbol_signal_list[0])
        
        return deduplicated
    
    def _resolve_timestamp_collisions(self, signals: List[Dict]) -> List[Dict]:
        """Resolve timestamp collisions by adding microsecond precision and random suffix"""
        resolved_signals = []
        
        for i, signal in enumerate(signals):
            # Generate unique signal ID with microsecond precision
            timestamp = datetime.now()
            unique_id = f"{signal['symbol']}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}_{i:03d}"
            
            # Add unique identifiers
            signal['signal_id'] = unique_id
            signal['generated_at'] = timestamp
            signal['deduplication_rank'] = i + 1
            
            resolved_signals.append(signal)
        
        return resolved_signals
    
    def _update_signal_history(self, signals: List[Dict]):
        """Update signal history and recent signals tracking"""
        for signal in signals:
            symbol = signal['symbol']
            signal_id = signal['signal_id']
            
            # Add to signal history
            self.signal_history[signal_id] = signal
            
            # Add to recent signals for this symbol
            self.recent_signals[symbol].append({
                'signal_id': signal_id,
                'timestamp': signal['generated_at'],
                'confidence': signal['confidence']
            })
    
    def _cleanup_old_signals(self):
        """Clean up old signals from memory"""
        if (datetime.now() - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.cleanup_interval)
        
        # Clean up recent signals
        for symbol in list(self.recent_signals.keys()):
            self.recent_signals[symbol] = [
                s for s in self.recent_signals[symbol] 
                if s['timestamp'] > cutoff_time
            ]
            
            # Remove empty entries
            if not self.recent_signals[symbol]:
                del self.recent_signals[symbol]
        
        # Clean up signal history
        old_signal_ids = [
            signal_id for signal_id, signal in self.signal_history.items()
            if signal['generated_at'] < cutoff_time
        ]
        
        for signal_id in old_signal_ids:
            del self.signal_history[signal_id]
        
        self.last_cleanup = datetime.now()
        logger.debug(f"🧹 Cleaned up {len(old_signal_ids)} old signals")
    
    def get_signal_stats(self) -> Dict:
        """Get statistics about signal processing"""
        total_recent = sum(len(signals) for signals in self.recent_signals.values())
        
        return {
            'total_recent_signals': total_recent,
            'symbols_with_signals': len(self.recent_signals),
            'signal_history_size': len(self.signal_history),
            'last_cleanup': self.last_cleanup.isoformat(),
            'min_confidence_threshold': self.min_confidence_threshold,
            'deduplication_window': self.deduplication_window
        }

# Global instance
signal_deduplicator = SignalDeduplicator()

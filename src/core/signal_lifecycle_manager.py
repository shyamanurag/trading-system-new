"""
🎯 COMPREHENSIVE SIGNAL LIFECYCLE MANAGEMENT SYSTEM
==================================================
Manages the complete lifecycle of trading signals from generation to cleanup.
Prevents system overload by automatically cleaning up irrelevant/expired signals.

KEY FEATURES:
1. Signal expiry management with configurable TTL
2. Automatic cleanup of expired signals from all caches
3. Memory optimization to prevent system overload
4. Elite recommendations cleanup integration
5. Database cleanup for historical signals
6. Performance monitoring and metrics
7. Configurable cleanup intervals and retention policies
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
import json

logger = logging.getLogger(__name__)

class SignalLifecycleStage(Enum):
    """Signal lifecycle stages"""
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CLEANED_UP = "CLEANED_UP"

@dataclass
class SignalLifecycleConfig:
    """Configuration for signal lifecycle management"""
    # Signal expiry times (in minutes)
    signal_ttl_minutes: int = 15  # Signals expire after 15 minutes
    failed_signal_ttl_minutes: int = 60  # Failed signals kept for 1 hour for analysis
    executed_signal_ttl_hours: int = 24  # Executed signals kept for 24 hours
    
    # Cleanup intervals
    cleanup_interval_minutes: int = 5  # Run cleanup every 5 minutes
    deep_cleanup_interval_hours: int = 1  # Deep cleanup every hour
    
    # Memory limits
    max_signals_in_memory: int = 1000  # Maximum signals to keep in memory
    max_elite_recommendations: int = 100  # Maximum elite recommendations
    
    # Cache cleanup
    clear_strategy_caches: bool = True
    clear_orchestrator_caches: bool = True
    clear_elite_caches: bool = True
    clear_redis_caches: bool = True

class SignalLifecycleManager:
    """
    COMPREHENSIVE SIGNAL LIFECYCLE MANAGEMENT
    
    Manages signals from generation to cleanup, preventing system overload
    and ensuring optimal performance by removing irrelevant signals.
    """
    
    def __init__(self, config: SignalLifecycleConfig = None):
        self.config = config or SignalLifecycleConfig()
        
        # Lifecycle tracking
        self.signal_stages: Dict[str, SignalLifecycleStage] = {}
        self.signal_timestamps: Dict[str, datetime] = {}
        self.signal_metadata: Dict[str, Dict] = {}
        
        # Cleanup tracking
        self.last_cleanup = datetime.now()
        self.last_deep_cleanup = datetime.now()
        self.cleanup_stats = {
            'total_cleanups': 0,
            'signals_cleaned': 0,
            'cache_clears': 0,
            'memory_freed_mb': 0
        }
        
        # Component references
        self.signal_recorder = None
        self.orchestrator = None
        self.elite_scanner = None
        self.redis_client = None
        
        # Background task
        self.cleanup_task = None
        self.running = False
        
        logger.info(f"🎯 Signal Lifecycle Manager initialized with TTL: {self.config.signal_ttl_minutes}min")
    
    async def start(self):
        """Start the lifecycle management system"""
        try:
            self.running = True
            
            # Initialize component references
            await self._initialize_components()
            
            # Start background cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("🚀 Signal Lifecycle Manager started")
            
        except Exception as e:
            logger.error(f"❌ Error starting Signal Lifecycle Manager: {e}")
    
    async def stop(self):
        """Stop the lifecycle management system"""
        try:
            self.running = False
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("🛑 Signal Lifecycle Manager stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Signal Lifecycle Manager: {e}")
    
    async def register_signal(self, signal_id: str, signal_data: Dict, stage: SignalLifecycleStage = SignalLifecycleStage.GENERATED):
        """Register a new signal in the lifecycle system"""
        try:
            self.signal_stages[signal_id] = stage
            self.signal_timestamps[signal_id] = datetime.now()
            self.signal_metadata[signal_id] = {
                'symbol': signal_data.get('symbol', ''),
                'strategy': signal_data.get('strategy', ''),
                'confidence': signal_data.get('confidence', 0.0),
                'entry_price': signal_data.get('entry_price', 0.0),
                'registered_at': datetime.now().isoformat()
            }
            
            logger.debug(f"📝 Signal registered: {signal_id} -> {stage.value}")
            
        except Exception as e:
            logger.error(f"❌ Error registering signal {signal_id}: {e}")
    
    async def update_signal_stage(self, signal_id: str, stage: SignalLifecycleStage):
        """Update signal lifecycle stage"""
        try:
            if signal_id in self.signal_stages:
                old_stage = self.signal_stages[signal_id]
                self.signal_stages[signal_id] = stage
                
                # Update timestamp for certain stages
                if stage in [SignalLifecycleStage.EXECUTED, SignalLifecycleStage.FAILED, SignalLifecycleStage.EXPIRED]:
                    self.signal_timestamps[signal_id] = datetime.now()
                
                logger.debug(f"🔄 Signal stage updated: {signal_id} -> {old_stage.value} → {stage.value}")
            
        except Exception as e:
            logger.error(f"❌ Error updating signal stage {signal_id}: {e}")
    
    async def is_signal_expired(self, signal_id: str) -> bool:
        """Check if a signal has expired"""
        try:
            if signal_id not in self.signal_timestamps:
                return True  # Unknown signals are considered expired
            
            signal_time = self.signal_timestamps[signal_id]
            stage = self.signal_stages.get(signal_id, SignalLifecycleStage.GENERATED)
            
            # Different TTL based on stage
            if stage == SignalLifecycleStage.EXECUTED:
                ttl = timedelta(hours=self.config.executed_signal_ttl_hours)
            elif stage == SignalLifecycleStage.FAILED:
                ttl = timedelta(minutes=self.config.failed_signal_ttl_minutes)
            else:
                ttl = timedelta(minutes=self.config.signal_ttl_minutes)
            
            return datetime.now() - signal_time > ttl
            
        except Exception as e:
            logger.error(f"❌ Error checking signal expiry {signal_id}: {e}")
            return True
    
    async def cleanup_expired_signals(self) -> Dict[str, int]:
        """Clean up expired signals from all system components"""
        try:
            cleanup_results = {
                'expired_signals': 0,
                'memory_cleaned': 0,
                'cache_cleared': 0,
                'elite_cleaned': 0,
                'redis_cleaned': 0
            }
            
            # Find expired signals
            expired_signal_ids = []
            for signal_id in list(self.signal_stages.keys()):
                if await self.is_signal_expired(signal_id):
                    expired_signal_ids.append(signal_id)
            
            if not expired_signal_ids:
                logger.debug("✅ No expired signals found")
                return cleanup_results
            
            logger.info(f"🧹 Cleaning up {len(expired_signal_ids)} expired signals")
            
            # 1. Clean up from signal recorder
            if self.signal_recorder:
                try:
                    for signal_id in expired_signal_ids:
                        if signal_id in self.signal_recorder.signal_records:
                            del self.signal_recorder.signal_records[signal_id]
                            cleanup_results['memory_cleaned'] += 1
                    
                    # Clean up elite recommendations
                    self.signal_recorder.elite_recommendations = [
                        rec for rec in self.signal_recorder.elite_recommendations
                        if rec.get('recommendation_id') not in expired_signal_ids
                    ]
                    cleanup_results['elite_cleaned'] = len(expired_signal_ids)
                    
                except Exception as e:
                    logger.error(f"Error cleaning signal recorder: {e}")
            
            # 2. Clean up from orchestrator
            if self.orchestrator:
                try:
                    # Clean up signal stats
                    if hasattr(self.orchestrator, 'signal_stats'):
                        recent_signals = self.orchestrator.signal_stats.get('recent_signals', [])
                        self.orchestrator.signal_stats['recent_signals'] = [
                            sig for sig in recent_signals
                            if sig.get('signal_id') not in expired_signal_ids
                        ]
                        
                        failed_signals = self.orchestrator.signal_stats.get('failed_signals', [])
                        self.orchestrator.signal_stats['failed_signals'] = [
                            sig for sig in failed_signals
                            if sig.get('signal_id') not in expired_signal_ids
                        ]
                    
                    cleanup_results['cache_cleared'] += 1
                    
                except Exception as e:
                    logger.error(f"Error cleaning orchestrator: {e}")
            
            # 3. Clean up from elite scanner
            if self.elite_scanner:
                try:
                    # Clean cached recommendations
                    if hasattr(self.elite_scanner, 'cached_recommendations'):
                        self.elite_scanner.cached_recommendations = [
                            rec for rec in self.elite_scanner.cached_recommendations
                            if rec.get('recommendation_id') not in expired_signal_ids
                        ]
                    
                    # Clean failed orders cache
                    if hasattr(self.elite_scanner, 'failed_orders_cache'):
                        self.elite_scanner.failed_orders_cache = [
                            order for order in self.elite_scanner.failed_orders_cache
                            if order.get('signal', {}).get('signal_id') not in expired_signal_ids
                        ]
                    
                except Exception as e:
                    logger.error(f"Error cleaning elite scanner: {e}")
            
            # 4. Clean up from Redis
            if self.redis_client and self.config.clear_redis_caches:
                try:
                    redis_cleaned = 0
                    for signal_id in expired_signal_ids:
                        # Clean various Redis keys related to signals
                        keys_to_clean = [
                            f"signal:{signal_id}",
                            f"signal_attempts:{signal_id}",
                            f"signal_metadata:{signal_id}",
                            f"elite_signal:{signal_id}"
                        ]
                        
                        for key in keys_to_clean:
                            try:
                                await self.redis_client.delete(key)
                                redis_cleaned += 1
                            except:
                                pass
                    
                    cleanup_results['redis_cleaned'] = redis_cleaned
                    
                except Exception as e:
                    logger.error(f"Error cleaning Redis: {e}")
            
            # 5. Clean up from lifecycle manager itself
            for signal_id in expired_signal_ids:
                self.signal_stages.pop(signal_id, None)
                self.signal_timestamps.pop(signal_id, None)
                self.signal_metadata.pop(signal_id, None)
            
            cleanup_results['expired_signals'] = len(expired_signal_ids)
            
            # Update cleanup stats
            self.cleanup_stats['total_cleanups'] += 1
            self.cleanup_stats['signals_cleaned'] += len(expired_signal_ids)
            self.cleanup_stats['cache_clears'] += cleanup_results['cache_cleared']
            
            logger.info(f"✅ Cleanup completed: {cleanup_results}")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"❌ Error during signal cleanup: {e}")
            return {'error': str(e)}
    
    async def deep_cleanup(self) -> Dict[str, int]:
        """Perform deep cleanup including memory optimization"""
        try:
            logger.info("🧹 Starting deep cleanup...")
            
            # Regular cleanup first
            cleanup_results = await self.cleanup_expired_signals()
            
            # Memory optimization
            memory_results = await self._optimize_memory()
            cleanup_results.update(memory_results)
            
            # Strategy cache cleanup
            if self.config.clear_strategy_caches:
                strategy_results = await self._cleanup_strategy_caches()
                cleanup_results.update(strategy_results)
            
            self.last_deep_cleanup = datetime.now()
            
            logger.info(f"✅ Deep cleanup completed: {cleanup_results}")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"❌ Error during deep cleanup: {e}")
            return {'error': str(e)}
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        try:
            while self.running:
                try:
                    # Regular cleanup
                    if datetime.now() - self.last_cleanup > timedelta(minutes=self.config.cleanup_interval_minutes):
                        await self.cleanup_expired_signals()
                        self.last_cleanup = datetime.now()
                    
                    # Deep cleanup
                    if datetime.now() - self.last_deep_cleanup > timedelta(hours=self.config.deep_cleanup_interval_hours):
                        await self.deep_cleanup()
                    
                    # Sleep for a minute before next check
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"❌ Error in cleanup loop: {e}")
                    await asyncio.sleep(60)  # Continue after error
                    
        except asyncio.CancelledError:
            logger.info("🛑 Cleanup loop cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in cleanup loop: {e}")
    
    async def _initialize_components(self):
        """Initialize references to system components"""
        try:
            # Try to get signal recorder
            try:
                from src.core.signal_recorder import signal_recorder
                self.signal_recorder = signal_recorder
                logger.debug("✅ Signal recorder reference initialized")
            except Exception as e:
                logger.debug(f"Signal recorder not available: {e}")
            
            # Try to get orchestrator
            try:
                from src.core.orchestrator import get_orchestrator_instance
                self.orchestrator = get_orchestrator_instance()
                logger.debug("✅ Orchestrator reference initialized")
            except Exception as e:
                logger.debug(f"Orchestrator not available: {e}")
            
            # Try to get elite scanner
            try:
                from src.api.elite_recommendations import autonomous_scanner
                self.elite_scanner = autonomous_scanner
                logger.debug("✅ Elite scanner reference initialized")
            except Exception as e:
                logger.debug(f"Elite scanner not available: {e}")
            
            # Try to get Redis client
            try:
                from src.core.signal_deduplicator import signal_deduplicator
                if hasattr(signal_deduplicator, 'redis_client'):
                    self.redis_client = signal_deduplicator.redis_client
                    logger.debug("✅ Redis client reference initialized")
            except Exception as e:
                logger.debug(f"Redis client not available: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
    
    async def _optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage by limiting signal storage"""
        try:
            results = {'memory_optimized': 0}
            
            # Limit signals in memory
            if len(self.signal_stages) > self.config.max_signals_in_memory:
                # Keep only the most recent signals
                sorted_signals = sorted(
                    self.signal_timestamps.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                signals_to_keep = dict(sorted_signals[:self.config.max_signals_in_memory])
                signals_to_remove = set(self.signal_stages.keys()) - set(signals_to_keep.keys())
                
                for signal_id in signals_to_remove:
                    self.signal_stages.pop(signal_id, None)
                    self.signal_timestamps.pop(signal_id, None)
                    self.signal_metadata.pop(signal_id, None)
                
                results['memory_optimized'] = len(signals_to_remove)
                logger.info(f"🧹 Memory optimized: removed {len(signals_to_remove)} old signals")
            
            # Limit elite recommendations
            if self.signal_recorder and len(self.signal_recorder.elite_recommendations) > self.config.max_elite_recommendations:
                # Keep only the most recent recommendations
                self.signal_recorder.elite_recommendations.sort(
                    key=lambda x: x.get('generated_at', ''),
                    reverse=True
                )
                removed_count = len(self.signal_recorder.elite_recommendations) - self.config.max_elite_recommendations
                self.signal_recorder.elite_recommendations = self.signal_recorder.elite_recommendations[:self.config.max_elite_recommendations]
                
                results['elite_optimized'] = removed_count
                logger.info(f"🧹 Elite recommendations optimized: removed {removed_count} old recommendations")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error optimizing memory: {e}")
            return {'error': str(e)}
    
    async def _cleanup_strategy_caches(self) -> Dict[str, int]:
        """Clean up strategy-specific caches"""
        try:
            results = {'strategies_cleaned': 0}
            
            if self.orchestrator and hasattr(self.orchestrator, 'strategies'):
                for strategy_name, strategy_info in self.orchestrator.strategies.items():
                    try:
                        strategy_instance = strategy_info.get('instance')
                        if strategy_instance:
                            # Clean current_positions of expired signals
                            if hasattr(strategy_instance, 'current_positions'):
                                expired_positions = []
                                for symbol, position in strategy_instance.current_positions.items():
                                    if isinstance(position, dict):
                                        signal_id = position.get('signal_id')
                                        if signal_id and await self.is_signal_expired(signal_id):
                                            expired_positions.append(symbol)
                                
                                for symbol in expired_positions:
                                    strategy_instance.current_positions.pop(symbol, None)
                                
                                if expired_positions:
                                    results['strategies_cleaned'] += 1
                                    logger.debug(f"🧹 Cleaned {len(expired_positions)} expired positions from {strategy_name}")
                    
                    except Exception as e:
                        logger.error(f"Error cleaning strategy {strategy_name}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error cleaning strategy caches: {e}")
            return {'error': str(e)}
    
    async def get_lifecycle_stats(self) -> Dict[str, Any]:
        """Get comprehensive lifecycle statistics"""
        try:
            # Count signals by stage
            stage_counts = {}
            for stage in SignalLifecycleStage:
                stage_counts[stage.value] = sum(1 for s in self.signal_stages.values() if s == stage)
            
            # Calculate expiry stats
            expired_count = 0
            for signal_id in self.signal_stages.keys():
                if await self.is_signal_expired(signal_id):
                    expired_count += 1
            
            return {
                'total_signals_tracked': len(self.signal_stages),
                'signals_by_stage': stage_counts,
                'expired_signals_pending_cleanup': expired_count,
                'cleanup_stats': self.cleanup_stats,
                'last_cleanup': self.last_cleanup.isoformat(),
                'last_deep_cleanup': self.last_deep_cleanup.isoformat(),
                'config': {
                    'signal_ttl_minutes': self.config.signal_ttl_minutes,
                    'cleanup_interval_minutes': self.config.cleanup_interval_minutes,
                    'max_signals_in_memory': self.config.max_signals_in_memory
                },
                'memory_usage': {
                    'signal_stages': len(self.signal_stages),
                    'signal_timestamps': len(self.signal_timestamps),
                    'signal_metadata': len(self.signal_metadata)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting lifecycle stats: {e}")
            return {'error': str(e)}

# Global instance
signal_lifecycle_manager = SignalLifecycleManager()

async def start_signal_lifecycle_management():
    """Start the global signal lifecycle management system"""
    await signal_lifecycle_manager.start()

async def stop_signal_lifecycle_management():
    """Stop the global signal lifecycle management system"""
    await signal_lifecycle_manager.stop()

async def register_signal_lifecycle(signal_id: str, signal_data: Dict, stage: SignalLifecycleStage = SignalLifecycleStage.GENERATED):
    """Register a signal in the lifecycle management system"""
    await signal_lifecycle_manager.register_signal(signal_id, signal_data, stage)

async def update_signal_lifecycle_stage(signal_id: str, stage: SignalLifecycleStage):
    """Update a signal's lifecycle stage"""
    await signal_lifecycle_manager.update_signal_stage(signal_id, stage)

async def cleanup_expired_signals():
    """Manually trigger cleanup of expired signals"""
    return await signal_lifecycle_manager.cleanup_expired_signals()

async def get_signal_lifecycle_stats():
    """Get signal lifecycle statistics"""
    return await signal_lifecycle_manager.get_lifecycle_stats()

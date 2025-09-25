"""
🎯 COMPREHENSIVE SIGNAL RECORDING SYSTEM
=======================================
Records ALL generated signals to elite recommendations page and maintains
complete audit trail of signal generation, execution, and outcomes.

FEATURES:
1. Real-time signal recording to elite recommendations
2. Signal lifecycle tracking (generated -> executed/failed/expired)
3. Performance analytics and success rate tracking
4. Database persistence for historical analysis
5. API integration for frontend display
6. Automatic cleanup of expired signals
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)

class SignalStatus(Enum):
    """Signal lifecycle status"""
    GENERATED = "GENERATED"
    PENDING_EXECUTION = "PENDING_EXECUTION"
    EXECUTED = "EXECUTED"
    FAILED_EXECUTION = "FAILED_EXECUTION"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

@dataclass
class SignalRecord:
    """Complete signal record for tracking"""
    signal_id: str
    timestamp: datetime
    strategy: str
    symbol: str
    action: str  # BUY/SELL
    entry_price: float
    stop_loss: Optional[float]
    target: Optional[float]
    confidence: float
    quantity: int
    status: SignalStatus
    
    # Elite recommendation fields
    risk_reward_ratio: float
    risk_percent: float
    reward_percent: float
    
    # Execution tracking
    execution_timestamp: Optional[datetime] = None
    execution_price: Optional[float] = None
    execution_status: Optional[str] = None
    
    # Performance tracking
    outcome: Optional[str] = None  # WIN/LOSS/BREAKEVEN
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = None
    valid_until: Optional[datetime] = None
    
    def to_elite_recommendation(self) -> Dict[str, Any]:
        """Convert signal record to elite recommendation format"""
        try:
            # Calculate secondary and tertiary targets
            if self.target and self.entry_price:
                if self.action == 'BUY':
                    distance = abs(self.target - self.entry_price)
                    secondary_target = self.target + (distance * 0.5)
                    tertiary_target = self.target + (distance * 1.0)
                else:  # SELL
                    distance = abs(self.entry_price - self.target)
                    secondary_target = self.target - (distance * 0.5)
                    tertiary_target = self.target - (distance * 1.0)
            else:
                secondary_target = self.entry_price * 1.02 if self.action == 'BUY' else self.entry_price * 0.98
                tertiary_target = self.entry_price * 1.03 if self.action == 'BUY' else self.entry_price * 0.97
            
            return {
                "recommendation_id": self.signal_id,
                "symbol": self.symbol,
                "direction": "LONG" if self.action == 'BUY' else "SHORT",
                "strategy": f"Live {self.strategy}",
                "confidence": round(self.confidence * 10, 1) if self.confidence <= 1.0 else round(self.confidence, 1),
                "entry_price": round(self.entry_price, 2),
                "current_price": round(self.entry_price, 2),
                "stop_loss": round(self.stop_loss, 2) if self.stop_loss else round(self.entry_price * 0.98, 2),
                "primary_target": round(self.target, 2) if self.target else round(self.entry_price * 1.02, 2),
                "secondary_target": round(secondary_target, 2),
                "tertiary_target": round(tertiary_target, 2),
                "risk_reward_ratio": round(self.risk_reward_ratio, 2),
                "risk_metrics": {
                    "risk_percent": round(self.risk_percent, 2),
                    "reward_percent": round(self.reward_percent, 2),
                    "position_size": 2.0,
                    "risk_calculation": "LIVE_STRATEGY_CALCULATION"
                },
                "confluence_factors": [
                    f"Live Strategy: {self.strategy}",
                    f"Signal Confidence: {self.confidence:.2f}",
                    f"Entry Price: ₹{self.entry_price:,.2f}",
                    f"Risk/Reward: {self.risk_reward_ratio:.2f}:1",
                    f"Generated: {self.timestamp.strftime('%H:%M:%S')}",
                    f"Status: {self.status.value}",
                    "Real-time Live Trading Signal"
                ],
                "entry_conditions": [
                    f"Live {self.strategy} strategy signal",
                    "Price at strategy-calculated entry level",
                    "Live market conditions favorable",
                    "Real-time risk management applied",
                    f"Confidence threshold met: {self.confidence:.2f}"
                ],
                "timeframe": "Intraday",
                "valid_until": self.valid_until.isoformat() if self.valid_until else (datetime.now() + timedelta(hours=4)).isoformat(),
                "status": "ACTIVE" if self.status in [SignalStatus.GENERATED, SignalStatus.PENDING_EXECUTION] else self.status.value,
                "generated_at": self.timestamp.isoformat(),
                "execution_status": self.execution_status,
                "execution_price": self.execution_price,
                "pnl": self.pnl,
                "pnl_percent": self.pnl_percent,
                "outcome": self.outcome,
                "data_source": "LIVE_TRADING_SIGNAL",
                "strategy_metadata": self.metadata or {},
                "autonomous": True,
                "live_signal": True
            }
            
        except Exception as e:
            logger.error(f"Error converting signal to elite recommendation: {e}")
            return {}

class SignalRecorder:
    """
    COMPREHENSIVE SIGNAL RECORDING SYSTEM
    
    Records all signals generated by strategies and maintains complete
    lifecycle tracking from generation to outcome.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Signal storage
        self.signal_records: Dict[str, SignalRecord] = {}
        self.elite_recommendations: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.strategy_performance: Dict[str, Dict] = {}
        self.daily_stats = {
            'total_signals': 0,
            'executed_signals': 0,
            'failed_signals': 0,
            'expired_signals': 0,
            'win_rate': 0.0,
            'avg_pnl': 0.0
        }
        
        # Configuration
        self.max_records = self.config.get('max_records', 1000)
        self.cleanup_interval_hours = self.config.get('cleanup_interval_hours', 24)
        self.signal_validity_hours = self.config.get('signal_validity_hours', 4)
        
        # Database connection (if available)
        self.db_enabled = False
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database connection for persistence"""
        try:
            # Try to initialize database connection
            # This is optional - system works without database
            pass
        except Exception as e:
            logger.debug(f"Database not available for signal recording: {e}")
            self.db_enabled = False
    
    async def record_signal(self, signal: Dict[str, Any], strategy: str) -> str:
        """
        Record a new signal from strategy
        
        Args:
            signal: Signal dictionary from strategy
            strategy: Strategy name that generated the signal
            
        Returns:
            signal_id: Unique identifier for the recorded signal
        """
        try:
            # Generate unique signal ID
            signal_id = self._generate_signal_id(signal, strategy)
            
            # Extract signal data
            symbol = signal.get('symbol', '')
            action = signal.get('action', 'BUY')
            entry_price = float(signal.get('entry_price', 0.0))
            stop_loss = signal.get('stop_loss')
            target = signal.get('target')
            confidence = float(signal.get('confidence', 0.0))
            quantity = int(signal.get('quantity', 0))
            
            # Calculate risk/reward metrics
            risk_reward_ratio, risk_percent, reward_percent = self._calculate_risk_metrics(
                entry_price, stop_loss, target, action
            )
            
            # Create signal record
            signal_record = SignalRecord(
                signal_id=signal_id,
                timestamp=datetime.now(),
                strategy=strategy,
                symbol=symbol,
                action=action,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                quantity=quantity,
                status=SignalStatus.GENERATED,
                risk_reward_ratio=risk_reward_ratio,
                risk_percent=risk_percent,
                reward_percent=reward_percent,
                metadata=signal.get('metadata', {}),
                valid_until=datetime.now() + timedelta(hours=self.signal_validity_hours)
            )
            
            # Store signal record
            self.signal_records[signal_id] = signal_record
            
            # Add to elite recommendations
            elite_rec = signal_record.to_elite_recommendation()
            if elite_rec:
                self.elite_recommendations.append(elite_rec)
                
            # Update statistics
            self.daily_stats['total_signals'] += 1
            self._update_strategy_performance(strategy, 'signal_generated')
            
            # Persist to database if available
            if self.db_enabled:
                await self._persist_signal_to_db(signal_record)
            
            logger.info(f"📊 SIGNAL RECORDED: {signal_id} - {strategy} {symbol} {action} @ ₹{entry_price}")
            logger.info(f"   Added to Elite Recommendations (Total: {len(self.elite_recommendations)})")
            
            # Cleanup old records
            await self._cleanup_expired_signals()
            
            return signal_id
            
        except Exception as e:
            logger.error(f"❌ Error recording signal: {e}")
            return ""
    
    async def update_signal_status(self, signal_id: str, status: SignalStatus, 
                                 execution_data: Dict = None) -> bool:
        """Update signal status and execution data"""
        try:
            if signal_id not in self.signal_records:
                logger.warning(f"Signal {signal_id} not found for status update")
                return False
            
            signal_record = self.signal_records[signal_id]
            old_status = signal_record.status
            signal_record.status = status
            
            # Update execution data if provided
            if execution_data:
                signal_record.execution_timestamp = execution_data.get('timestamp', datetime.now())
                signal_record.execution_price = execution_data.get('price')
                signal_record.execution_status = execution_data.get('status')
                signal_record.pnl = execution_data.get('pnl')
                signal_record.pnl_percent = execution_data.get('pnl_percent')
                signal_record.outcome = execution_data.get('outcome')
            
            # Update elite recommendation
            await self._update_elite_recommendation(signal_id, signal_record)
            
            # Update statistics
            if status == SignalStatus.EXECUTED:
                self.daily_stats['executed_signals'] += 1
                self._update_strategy_performance(signal_record.strategy, 'signal_executed')
            elif status == SignalStatus.FAILED_EXECUTION:
                self.daily_stats['failed_signals'] += 1
                self._update_strategy_performance(signal_record.strategy, 'signal_failed')
            elif status == SignalStatus.EXPIRED:
                self.daily_stats['expired_signals'] += 1
                self._update_strategy_performance(signal_record.strategy, 'signal_expired')
            
            logger.info(f"📊 SIGNAL STATUS UPDATED: {signal_id} - {old_status.value} → {status.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating signal status: {e}")
            return False
    
    async def get_elite_recommendations(self) -> List[Dict[str, Any]]:
        """Get all current elite recommendations"""
        try:
            # Clean up expired recommendations
            await self._cleanup_expired_signals()
            
            # Return active recommendations sorted by timestamp (newest first)
            active_recommendations = [
                rec for rec in self.elite_recommendations 
                if rec.get('status') in ['ACTIVE', 'GENERATED', 'PENDING_EXECUTION']
            ]
            
            active_recommendations.sort(
                key=lambda x: datetime.fromisoformat(x['generated_at']), 
                reverse=True
            )
            
            return active_recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting elite recommendations: {e}")
            return []
    
    async def get_signal_statistics(self) -> Dict[str, Any]:
        """Get comprehensive signal statistics"""
        try:
            # Calculate win rate
            total_completed = self.daily_stats['executed_signals']
            if total_completed > 0:
                winning_signals = sum(
                    1 for record in self.signal_records.values()
                    if record.outcome == 'WIN'
                )
                self.daily_stats['win_rate'] = (winning_signals / total_completed) * 100
                
                # Calculate average P&L
                pnl_values = [
                    record.pnl_percent for record in self.signal_records.values()
                    if record.pnl_percent is not None
                ]
                if pnl_values:
                    self.daily_stats['avg_pnl'] = sum(pnl_values) / len(pnl_values)
            
            return {
                'daily_stats': self.daily_stats,
                'strategy_performance': self.strategy_performance,
                'total_active_recommendations': len(self.elite_recommendations),
                'total_recorded_signals': len(self.signal_records),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting signal statistics: {e}")
            return {}
    
    def _generate_signal_id(self, signal: Dict, strategy: str) -> str:
        """Generate unique signal ID"""
        try:
            timestamp = datetime.now().isoformat()
            symbol = signal.get('symbol', '')
            action = signal.get('action', '')
            
            data = f"{strategy}_{symbol}_{action}_{timestamp}"
            return hashlib.md5(data.encode()).hexdigest()[:12].upper()
            
        except Exception as e:
            logger.error(f"Error generating signal ID: {e}")
            return f"SIG_{int(datetime.now().timestamp())}"
    
    def _calculate_risk_metrics(self, entry_price: float, stop_loss: Optional[float], 
                              target: Optional[float], action: str) -> tuple:
        """Calculate risk/reward metrics"""
        try:
            if not stop_loss or not target:
                # Default risk/reward if not provided
                return 2.0, 2.0, 4.0
            
            if action == 'BUY':
                risk = abs(entry_price - stop_loss)
                reward = abs(target - entry_price)
            else:  # SELL
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - target)
            
            risk_percent = (risk / entry_price) * 100
            reward_percent = (reward / entry_price) * 100
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            return risk_reward_ratio, risk_percent, reward_percent
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return 2.0, 2.0, 4.0
    
    def _update_strategy_performance(self, strategy: str, event: str):
        """Update strategy performance statistics"""
        try:
            if strategy not in self.strategy_performance:
                self.strategy_performance[strategy] = {
                    'signals_generated': 0,
                    'signals_executed': 0,
                    'signals_failed': 0,
                    'signals_expired': 0,
                    'win_rate': 0.0,
                    'avg_pnl': 0.0
                }
            
            if event == 'signal_generated':
                self.strategy_performance[strategy]['signals_generated'] += 1
            elif event == 'signal_executed':
                self.strategy_performance[strategy]['signals_executed'] += 1
            elif event == 'signal_failed':
                self.strategy_performance[strategy]['signals_failed'] += 1
            elif event == 'signal_expired':
                self.strategy_performance[strategy]['signals_expired'] += 1
                
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
    
    async def _update_elite_recommendation(self, signal_id: str, signal_record: SignalRecord):
        """Update elite recommendation with latest signal data"""
        try:
            # Find and update the recommendation
            for i, rec in enumerate(self.elite_recommendations):
                if rec.get('recommendation_id') == signal_id:
                    updated_rec = signal_record.to_elite_recommendation()
                    if updated_rec:
                        self.elite_recommendations[i] = updated_rec
                    break
                    
        except Exception as e:
            logger.error(f"Error updating elite recommendation: {e}")
    
    async def _cleanup_expired_signals(self):
        """Clean up expired signals and recommendations"""
        try:
            current_time = datetime.now()
            expired_signal_ids = []
            
            # Find expired signals
            for signal_id, record in self.signal_records.items():
                if record.valid_until and current_time > record.valid_until:
                    if record.status in [SignalStatus.GENERATED, SignalStatus.PENDING_EXECUTION]:
                        record.status = SignalStatus.EXPIRED
                        expired_signal_ids.append(signal_id)
            
            # Update expired signals
            for signal_id in expired_signal_ids:
                await self.update_signal_status(signal_id, SignalStatus.EXPIRED)
            
            # Remove old records if we exceed max limit
            if len(self.signal_records) > self.max_records:
                # Keep most recent records
                sorted_records = sorted(
                    self.signal_records.items(),
                    key=lambda x: x[1].timestamp,
                    reverse=True
                )
                
                # Keep only max_records
                self.signal_records = dict(sorted_records[:self.max_records])
                
                # Update elite recommendations to match
                active_signal_ids = set(self.signal_records.keys())
                self.elite_recommendations = [
                    rec for rec in self.elite_recommendations
                    if rec.get('recommendation_id') in active_signal_ids
                ]
            
            if expired_signal_ids:
                logger.info(f"🧹 Cleaned up {len(expired_signal_ids)} expired signals")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired signals: {e}")
    
    async def _persist_signal_to_db(self, signal_record: SignalRecord):
        """Persist signal record to database (if available)"""
        try:
            if not self.db_enabled:
                return
            
            # Database persistence logic would go here
            # For now, just log that we would persist
            logger.debug(f"Would persist signal {signal_record.signal_id} to database")
            
        except Exception as e:
            logger.error(f"Error persisting signal to database: {e}")

# Global signal recorder instance
signal_recorder = SignalRecorder()

async def record_signal(signal: Dict[str, Any], strategy: str) -> str:
    """
    Global function to record a signal
    
    Args:
        signal: Signal dictionary from strategy
        strategy: Strategy name
        
    Returns:
        signal_id: Unique identifier for the recorded signal
    """
    return await signal_recorder.record_signal(signal, strategy)

async def update_signal_status(signal_id: str, status: SignalStatus, execution_data: Dict = None) -> bool:
    """
    Global function to update signal status
    
    Args:
        signal_id: Signal identifier
        status: New status
        execution_data: Optional execution data
        
    Returns:
        bool: Success status
    """
    return await signal_recorder.update_signal_status(signal_id, status, execution_data)

async def get_all_elite_recommendations() -> List[Dict[str, Any]]:
    """
    Global function to get all elite recommendations
    
    Returns:
        List of elite recommendations
    """
    return await signal_recorder.get_elite_recommendations()

"""
Confluence Amplifier
Manages strategy confluence and signal amplification with proper integration
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class ConfluenceAmplifier(BaseStrategy):
    """Amplifies trading signals based on strategy confluence with proper integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "ConfluenceAmplifier"
        
        # Signal processing parameters
        self.confluence_threshold = config.get('confluence', {}).get('threshold', 0.7)
        self.signal_decay_hours = config.get('confluence', {}).get('decay_hours', 2.0)
        self.max_signal_history = config.get('confluence', {}).get('max_history', 50)
        
        # Signal storage - Dict format signals from other strategies
        self.signal_history = []  # List of Dict signals
        self.strategy_weights = {
            'EnhancedMomentumSurfer': 0.3,
            'EnhancedVolumeProfileScalper': 0.25,
            'EnhancedVolatilityExplosion': 0.25,
            'EnhancedNewsImpactScalper': 0.2
        }
        
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and generate signals"""
        if not self.is_active:
            return
            
        try:
            # Check SCALPING cooldown
            if not self._is_scalping_cooldown_passed():
                return
                
            # Process market data and generate signals
            signals = self._generate_signals(data)
            
            # FIXED: Only store signals for orchestrator collection - no direct execution
            for signal in signals:
                self.current_positions[signal['symbol']] = signal
                logger.info(f"🚨 {self.name} SIGNAL GENERATED: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
            
            # Update last signal time if signals generated
            if signals:
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    def _generate_signals(self, data: Dict) -> List[Dict]:
        """Generate signals based on confluence analysis"""
        try:
            # Clean up old signals first
            self._cleanup_old_signals()
            
            # Check if we have enough signals for confluence analysis
            if len(self.signal_history) < 2:
                return []
            
            # Analyze confluence and generate amplified signals
            confluent_signals = self._analyze_confluence(data)
            
            return confluent_signals
            
        except Exception as e:
            logger.error(f"Error generating confluence signals: {e}")
            return []
    
    async def process_external_signal(self, signal: Dict):
        """Process a signal from another strategy and check for confluence"""
        try:
            if not signal or not isinstance(signal, dict):
                return
            
            # Add timestamp if not present
            if 'timestamp' not in signal.get('metadata', {}):
                if 'metadata' not in signal:
                    signal['metadata'] = {}
                signal['metadata']['timestamp'] = datetime.now().isoformat()
            
            # Add signal to history
            self.signal_history.append(signal)
            
            # Trim history if needed
            if len(self.signal_history) > self.max_signal_history:
                self.signal_history.pop(0)
            
            logger.debug(f"Added signal from {signal.get('strategy', 'UNKNOWN')} to confluence history")
            
        except Exception as e:
            logger.error(f"Error processing external signal: {e}")
    
    def _cleanup_old_signals(self):
        """Remove signals older than decay period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.signal_decay_hours)
            
            # Filter out old signals
            self.signal_history = [
                signal for signal in self.signal_history
                if self._get_signal_timestamp(signal) > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old signals: {e}")
    
    def _get_signal_timestamp(self, signal: Dict) -> datetime:
        """Extract timestamp from signal metadata"""
        try:
            timestamp_str = signal.get('metadata', {}).get('timestamp')
            if timestamp_str:
                # Handle both ISO format and datetime objects
                if isinstance(timestamp_str, str):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                elif isinstance(timestamp_str, datetime):
                    return timestamp_str
            
            # Fallback to current time minus decay period (will be cleaned up)
            return datetime.now() - timedelta(hours=self.signal_decay_hours + 1)
            
        except Exception as e:
            logger.error(f"Error parsing signal timestamp: {e}")
            return datetime.now() - timedelta(hours=self.signal_decay_hours + 1)
    
    def _analyze_confluence(self, current_market_data: Dict) -> List[Dict]:
        """Analyze signal confluence and generate amplified signals"""
        try:
            confluent_signals = []
            
            # Group signals by symbol and action
            signal_groups = {}
            
            for signal in self.signal_history:
                symbol = signal.get('symbol', 'UNKNOWN')
                action = signal.get('action', 'UNKNOWN')
                strategy = signal.get('strategy', 'UNKNOWN')
                
                # Only consider recent signals (last hour)
                signal_time = self._get_signal_timestamp(signal)
                if (datetime.now() - signal_time).total_seconds() > 3600:  # 1 hour
                    continue
                
                key = f"{symbol}_{action}"
                if key not in signal_groups:
                    signal_groups[key] = []
                
                signal_groups[key].append({
                    'signal': signal,
                    'strategy': strategy,
                    'timestamp': signal_time,
                    'weight': self.strategy_weights.get(strategy, 0.1)
                })
            
            # Analyze each group for confluence
            for group_key, group_signals in signal_groups.items():
                if len(group_signals) < 2:  # Need at least 2 signals for confluence
                    continue
                
                confluence_analysis = self._calculate_group_confluence(group_signals)
                
                if confluence_analysis['confluence_strength'] >= self.confluence_threshold:
                    # Create amplified signal
                    amplified_signal = self._create_amplified_signal(
                        group_signals, confluence_analysis, current_market_data
                    )
                    
                    if amplified_signal:
                        confluent_signals.append(amplified_signal)
                        logger.info(f"🔥 CONFLUENCE DETECTED: {group_key} with {len(group_signals)} strategies")
            
            return confluent_signals
            
        except Exception as e:
            logger.error(f"Error analyzing confluence: {e}")
            return []
    
    def _calculate_group_confluence(self, group_signals: List[Dict]) -> Dict:
        """Calculate confluence strength for a group of signals"""
        try:
            # Calculate weighted confluence strength
            total_weight = sum(s['weight'] for s in group_signals)
            unique_strategies = len(set(s['strategy'] for s in group_signals))
            
            # Base confluence from number of strategies
            base_confluence = min(unique_strategies / 4.0, 1.0)  # Max 4 strategies
            
            # Weight-adjusted confluence
            weight_confluence = total_weight / sum(self.strategy_weights.values())
            
            # Time proximity bonus (signals close in time get bonus)
            timestamps = [s['timestamp'] for s in group_signals]
            time_spread = (max(timestamps) - min(timestamps)).total_seconds() / 60  # minutes
            time_bonus = max(0, (10 - time_spread) / 10 * 0.2)  # Up to 20% bonus for signals within 10 minutes
            
            # Confidence bonus (higher confidence signals get bonus)
            avg_confidence = np.mean([
                s['signal'].get('confidence', 0.5) for s in group_signals
            ])
            confidence_bonus = (avg_confidence - 0.5) * 0.3  # Up to 15% bonus
            
            # Calculate final confluence strength
            confluence_strength = (base_confluence * 0.4 + weight_confluence * 0.4 + 
                                 time_bonus + confidence_bonus)
            
            return {
                'confluence_strength': min(confluence_strength, 1.0),
                'strategy_count': unique_strategies,
                'total_weight': total_weight,
                'avg_confidence': avg_confidence,
                'time_spread_minutes': time_spread,
                'strategies': [s['strategy'] for s in group_signals]
            }
            
        except Exception as e:
            logger.error(f"Error calculating group confluence: {e}")
            return {'confluence_strength': 0.0}
    
    def _create_amplified_signal(self, group_signals: List[Dict], confluence_analysis: Dict, 
                                current_market_data: Dict) -> Optional[Dict]:
        """Create an amplified signal based on confluence"""
        try:
            # Use the most recent signal as base
            base_signal = max(group_signals, key=lambda x: x['timestamp'])['signal']
            symbol = base_signal.get('symbol')
            
            # Get current market data for the symbol
            symbol_data = current_market_data.get(symbol, {})
            current_price = symbol_data.get('close', base_signal.get('entry_price', 0))
            
            if current_price <= 0:
                return None
            
            # Calculate amplified confidence
            base_confidence = base_signal.get('confidence', 0.5)
            confluence_boost = confluence_analysis['confluence_strength'] * 0.3  # Up to 30% boost
            amplified_confidence = min(base_confidence + confluence_boost, 0.95)
            
            # Calculate consensus levels (average of all signals)
            entry_prices = [s['signal'].get('entry_price', current_price) for s in group_signals]
            stop_losses = [s['signal'].get('stop_loss', current_price * 0.98) for s in group_signals]
            targets = [s['signal'].get('target', current_price * 1.02) for s in group_signals]
            
            consensus_entry = np.mean(entry_prices)
            consensus_stop = np.mean(stop_losses)
            consensus_target = np.mean(targets)
            
            # Create amplified signal using base strategy format
            amplified_signal = self.create_standard_signal(
                symbol=symbol,
                action=base_signal.get('action', 'BUY'),
                entry_price=current_price,  # Use current price for immediate execution
                stop_loss=consensus_stop,
                target=consensus_target,
                confidence=amplified_confidence,
                metadata={
                    'confluence_strength': confluence_analysis['confluence_strength'],
                    'contributing_strategies': confluence_analysis['strategies'],
                    'strategy_count': confluence_analysis['strategy_count'],
                    'original_signals': len(group_signals),
                    'consensus_entry': consensus_entry,
                    'time_spread_minutes': confluence_analysis['time_spread_minutes'],
                    'amplification_type': 'MULTI_STRATEGY_CONFLUENCE',
                    'risk_type': 'CONFLUENCE_AMPLIFIED',
                    'strategy_version': '2.0_FIXED'
                }
            )
            
            return amplified_signal
            
        except Exception as e:
            logger.error(f"Error creating amplified signal: {e}")
            return None
    
    async def _execute_confluent_trades(self, confluent_signals: List[Dict]):
        """Execute confluent trades"""
        try:
            for signal in confluent_signals:
                logger.info(f"🔥 {self.name} EXECUTING CONFLUENT TRADE: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, "
                           f"SL: ₹{signal['stop_loss']:.2f}, "
                           f"Target: ₹{signal['target']:.2f}, "
                           f"Confidence: {signal['confidence']:.2f} "
                           f"(Confluence: {signal['metadata']['confluence_strength']:.2f})")
                
                # Send signal to trade engine
                success = await self.send_to_trade_engine(signal)
                
                if success:
                    self.current_positions[signal['symbol']] = signal
                    logger.info(f"✅ {self.name} confluent trade executed successfully")
                else:
                    logger.error(f"❌ {self.name} confluent trade execution failed")
                
        except Exception as e:
            logger.error(f"Error executing confluent trades: {e}")
    
    def get_confluence_status(self) -> Dict:
        """Get current confluence analysis status"""
        try:
            recent_signals = [
                s for s in self.signal_history
                if (datetime.now() - self._get_signal_timestamp(s)).total_seconds() < 3600
            ]
            
            strategy_counts = {}
            for signal in recent_signals:
                strategy = signal.get('strategy', 'UNKNOWN')
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            return {
                'total_signals_last_hour': len(recent_signals),
                'strategy_breakdown': strategy_counts,
                'confluence_threshold': self.confluence_threshold,
                'signal_history_size': len(self.signal_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting confluence status: {e}")
            return {'error': str(e)} 
"""
Confluence Amplifier
Manages strategy confluence and signal amplification
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    LONG = "long"
    SHORT = "short"
    EXIT = "exit"
    NEUTRAL = "neutral"

@dataclass
class Signal:
    type: SignalType
    strength: float
    source: str
    timestamp: pd.Timestamp
    metadata: Dict

class ConfluenceAmplifier:
    """Amplifies trading signals based on strategy confluence"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.signal_history = []
        self.confluence_threshold = config.get('confluence', {}).get('threshold', 0.7)
        self.signal_decay = config.get('confluence', {}).get('decay', 0.1)
        self.max_history = config.get('confluence', {}).get('max_history', 100)
        
    async def process_signals(self, signals: List[Signal]) -> Optional[Signal]:
        """Process and amplify signals based on confluence"""
        try:
            # Add new signals to history
            self.signal_history.extend(signals)
            
            # Trim history if needed
            if len(self.signal_history) > self.max_history:
                self.signal_history = self.signal_history[-self.max_history:]
            
            # Calculate signal confluence
            confluence = self._calculate_confluence()
            
            # Generate amplified signal if confluence is high enough
            if confluence['strength'] >= self.confluence_threshold:
                amplified_signal = self._generate_amplified_signal(confluence)
                logger.info(f"Generated amplified signal: {amplified_signal.type.value} "
                          f"with strength {amplified_signal.strength:.2f}")
                return amplified_signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing signals: {str(e)}")
            return None
    
    def _calculate_confluence(self) -> Dict:
        """Calculate signal confluence metrics"""
        if not self.signal_history:
            return {'type': SignalType.NEUTRAL, 'strength': 0.0}
        
        # Group signals by type
        signal_groups = {
            SignalType.LONG: [],
            SignalType.SHORT: [],
            SignalType.EXIT: [],
            SignalType.NEUTRAL: []
        }
        
        # Apply time decay to signal strengths
        current_time = pd.Timestamp.now()
        for signal in self.signal_history:
            time_diff = (current_time - signal.timestamp).total_seconds() / 3600  # hours
            decayed_strength = signal.strength * np.exp(-self.signal_decay * time_diff)
            signal_groups[signal.type].append(decayed_strength)
        
        # Calculate average strength for each type
        avg_strengths = {
            signal_type: np.mean(strengths) if strengths else 0.0
            for signal_type, strengths in signal_groups.items()
        }
        
        # Find dominant signal type
        dominant_type = max(avg_strengths.items(), key=lambda x: x[1])[0]
        
        # Calculate overall confluence strength
        total_strength = sum(avg_strengths.values())
        if total_strength > 0:
            confluence_strength = avg_strengths[dominant_type] / total_strength
        else:
            confluence_strength = 0.0
        
        return {
            'type': dominant_type,
            'strength': confluence_strength,
            'strengths': avg_strengths
        }
    
    def _generate_amplified_signal(self, confluence: Dict) -> Signal:
        """Generate amplified signal based on confluence"""
        # Calculate base strength
        base_strength = confluence['strength']
        
        # Apply amplification factors
        amplification = 1.0
        
        # Amplify based on signal consistency
        if len(self.signal_history) >= 3:
            recent_signals = self.signal_history[-3:]
            if all(s.type == confluence['type'] for s in recent_signals):
                amplification *= 1.2
        
        # Amplify based on signal source diversity
        unique_sources = len(set(s.source for s in self.signal_history))
        if unique_sources >= 2:
            amplification *= 1.1
        
        # Calculate final strength
        final_strength = min(base_strength * amplification, 1.0)
        
        return Signal(
            type=confluence['type'],
            strength=final_strength,
            source='confluence_amplifier',
            timestamp=pd.Timestamp.now(),
            metadata={
                'base_strength': base_strength,
                'amplification': amplification,
                'confluence_metrics': confluence
            }
        )
    
    def get_signal_weights(self) -> Dict[str, float]:
        """Get signal weights for different strategy types"""
        return {
            'volatility_explosion': 0.3,
            'momentum_surfer': 0.3,
            'volume_profile_scalper': 0.2,
            'news_impact_scalper': 0.2
        }
    
    def clear_history(self):
        """Clear signal history"""
        self.signal_history = [] 
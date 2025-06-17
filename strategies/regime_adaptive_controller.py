"""
Regime Adaptive Controller
Manages market regime detection and strategy adaptation
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio

from src.core.base import BaseStrategy
from src.core.models import Signal

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    ULTRA_HIGH_VOL = "ultra_high_vol"

@dataclass
class RegimeMetrics:
    volatility: float
    trend_strength: float
    momentum: float
    volume_profile: float
    regime: MarketRegime

class RegimeAdaptiveController(BaseStrategy):
    """Controls strategy adaptation based on market regime detection"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.current_regime = MarketRegime.RANGING
        self.regime_metrics = RegimeMetrics(
            volatility=0.0,
            trend_strength=0.0,
            momentum=0.0,
            volume_profile=0.0,
            regime=MarketRegime.RANGING
        )
        self.regime_history = []
        self.min_samples = config.get('regime_detection', {}).get('min_samples', 100)
        self.regime_threshold = config.get('regime_detection', {}).get('threshold', 0.7)
        
        # Regime thresholds
        self.regime_thresholds = {
            'ULTRA_HIGH_VOL': {'vix': 25, 'atr_ratio': 1.5},
            'TRENDING': {'adx': 30, 'directional_movement': 0.7},
            'RANGE_BOUND': {'adx': 20, 'atr_ratio': 0.5}
        }
        
        # Allocation adjustments
        self.allocation_adjustments = {
            'ULTRA_HIGH_VOL': {
                'volatility_explosion': 1.4,
                'momentum_surfer': 0.6,
                'volume_profile_scalper': 1.0,
                'news_impact_scalper': 1.0
            },
            'TRENDING': {
                'momentum_surfer': 1.4,
                'volume_profile_scalper': 1.2,
                'volatility_explosion': 0.7,
                'news_impact_scalper': 0.7
            },
            'RANGE_BOUND': {
                'volume_profile_scalper': 1.5,
                'volatility_explosion': 1.2,
                'momentum_surfer': 0.6,
                'news_impact_scalper': 0.7
            }
        }
        
        self._regime_lock = asyncio.Lock()
        
    def _initialize_strategy(self):
        """Initialize strategy-specific components"""
        pass
        
    async def update_regime(self, market_data: pd.DataFrame) -> MarketRegime:
        """Update market regime based on latest market data"""
        try:
            async with self._regime_lock:
                # Calculate regime metrics
                self.regime_metrics.volatility = self._calculate_volatility(market_data)
                self.regime_metrics.trend_strength = self._calculate_trend_strength(market_data)
                self.regime_metrics.momentum = self._calculate_momentum(market_data)
                self.regime_metrics.volume_profile = self._calculate_volume_profile(market_data)
                
                # Detect regime
                new_regime = self._detect_regime()
                
                # Update regime history
                self.regime_history.append(new_regime)
                if len(self.regime_history) > self.min_samples:
                    self.regime_history.pop(0)
                
                # Update current regime if stable
                if self._is_regime_stable():
                    self.current_regime = new_regime
                    logger.info(f"Market regime updated to: {self.current_regime.value}")
                
                return self.current_regime
                
        except Exception as e:
            logger.error(f"Error updating market regime: {str(e)}")
            return self.current_regime
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate market volatility"""
        returns = data['close'].pct_change()
        return returns.std() * np.sqrt(252)  # Annualized volatility
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength using ADX"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Calculate smoothed averages
        period = 14
        tr_smoothed = tr.rolling(period).mean()
        plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / tr_smoothed
        minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / tr_smoothed
        
        # Calculate ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1]
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate market momentum"""
        period = 14
        return (data['close'].iloc[-1] / data['close'].iloc[-period] - 1) * 100
    
    def _calculate_volume_profile(self, data: pd.DataFrame) -> float:
        """Calculate volume profile strength"""
        volume_ma = data['volume'].rolling(20).mean()
        return (data['volume'].iloc[-1] / volume_ma.iloc[-1] - 1) * 100
    
    def _detect_regime(self) -> MarketRegime:
        """Detect market regime based on metrics"""
        metrics = self.regime_metrics
        
        if metrics.volatility > 0.3:  # High volatility
            return MarketRegime.VOLATILE
        elif metrics.trend_strength > 25:  # Strong trend
            return MarketRegime.TRENDING
        elif metrics.momentum > 5:  # Strong momentum
            return MarketRegime.BREAKOUT
        elif metrics.momentum < -5:  # Negative momentum
            return MarketRegime.REVERSAL
        else:
            return MarketRegime.RANGING
    
    def _is_regime_stable(self) -> bool:
        """Check if regime is stable enough to update"""
        if len(self.regime_history) < self.min_samples:
            return False
        
        recent_regimes = self.regime_history[-self.min_samples:]
        regime_counts = pd.Series(recent_regimes).value_counts()
        most_common = regime_counts.max() / len(recent_regimes)
        
        return most_common >= self.regime_threshold
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get strategy weights based on current regime"""
        weights = {
            'volatility_explosion': 0.0,
            'momentum_surfer': 0.0,
            'volume_profile_scalper': 0.0,
            'news_impact_scalper': 0.0
        }
        
        if self.current_regime == MarketRegime.VOLATILE:
            weights['volatility_explosion'] = 0.4
            weights['volume_profile_scalper'] = 0.3
            weights['momentum_surfer'] = 0.2
            weights['news_impact_scalper'] = 0.1
            
        elif self.current_regime == MarketRegime.TRENDING:
            weights['momentum_surfer'] = 0.4
            weights['volatility_explosion'] = 0.3
            weights['volume_profile_scalper'] = 0.2
            weights['news_impact_scalper'] = 0.1
            
        elif self.current_regime == MarketRegime.BREAKOUT:
            weights['momentum_surfer'] = 0.5
            weights['volatility_explosion'] = 0.3
            weights['volume_profile_scalper'] = 0.1
            weights['news_impact_scalper'] = 0.1
            
        elif self.current_regime == MarketRegime.REVERSAL:
            weights['news_impact_scalper'] = 0.4
            weights['volume_profile_scalper'] = 0.3
            weights['volatility_explosion'] = 0.2
            weights['momentum_surfer'] = 0.1
            
        else:  # RANGING
            weights['volume_profile_scalper'] = 0.4
            weights['news_impact_scalper'] = 0.3
            weights['volatility_explosion'] = 0.2
            weights['momentum_surfer'] = 0.1
        
        return weights
    
    def get_allocation_multiplier(self, strategy_name: str) -> float:
        """Get allocation multiplier for a strategy based on current regime"""
        regime_name = self.current_regime.value.upper()
        return self.allocation_adjustments.get(regime_name, {}).get(strategy_name, 1.0)
    
    async def generate_signals(self, market_data: Dict) -> List[Signal]:
        """Generate trading signals - meta-strategy doesn't generate direct signals"""
        # Update regime based on market data
        if isinstance(market_data, pd.DataFrame):
            await self.update_regime(market_data)
        return [] 
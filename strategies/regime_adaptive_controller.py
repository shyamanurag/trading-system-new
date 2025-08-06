"""
Regime Adaptive Controller
A meta-strategy that adapts to market regimes and controls other strategies
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

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

class RegimeAdaptiveController:
    """Meta-strategy that adapts to market regimes"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "RegimeAdaptiveController"
        self.is_active = False
        self.current_regime = MarketRegime.RANGING
        self.regime_metrics = RegimeMetrics(0.0, 0.0, 0.0, 0.0, MarketRegime.RANGING)
        self.regime_history = []
        self.min_samples = 3
        self.regime_threshold = 0.6
        
        # CRITICAL FIX: Historical data accumulation for proper time series analysis
        self.historical_data = []
        self.max_history = 100  # Keep last 100 data points
        
        # Allocation adjustments by regime
        self.allocation_adjustments = {
            'VOLATILE': {
                'professional_options_engine': 1.5,
                'nifty_intelligence_engine': 0.8,
                'smart_intraday_options': 1.2,
                'market_microstructure_edge': 1.0
            },
            'TRENDING': {
                'nifty_intelligence_engine': 1.5,
                'professional_options_engine': 1.2,
                'smart_intraday_options': 0.8,
                'market_microstructure_edge': 0.9
            },
            'RANGING': {
                'smart_intraday_options': 1.3,
                'professional_options_engine': 0.9,
                'nifty_intelligence_engine': 0.7,
                'market_microstructure_edge': 1.1
            },
            'BREAKOUT': {
                'nifty_intelligence_engine': 1.8,
                'professional_options_engine': 1.4,
                'smart_intraday_options': 1.0,
                'market_microstructure_edge': 0.8
            },
            'REVERSAL': {
                'market_microstructure_edge': 1.5,
                'smart_intraday_options': 1.3,
                'professional_options_engine': 1.1,
                'nifty_intelligence_engine': 0.6
            }
        }
        
        self._regime_lock = asyncio.Lock()
        
    def _initialize_strategy(self):
        """Initialize strategy-specific components"""
        pass
    
    async def initialize(self):
        """Initialize the strategy"""
        logger.info(f"Initializing {self.__class__.__name__} strategy")
        self._initialize_strategy()
        # CRITICAL FIX: Set strategy to active
        self.is_active = True
        logger.info(f"✅ {self.name} strategy activated successfully")
        return True
    
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and update regime analysis"""
        if not self.is_active:
            return
            
        try:
            # Add data to historical buffer for regime analysis
            await self._process_market_data_for_regime(data)
            
            # Update market regime based on accumulated data
            await self.update_regime()
            
            # Note: This strategy doesn't generate trading signals directly
            # It acts as a meta-controller that adjusts other strategies
            
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    async def _process_market_data_for_regime(self, data: Dict):
        """Process market data for regime analysis"""
        try:
            # Extract market metrics for regime detection
            timestamp = datetime.now()
            
            # Calculate aggregate market metrics from all symbols
            total_volume = 0
            total_price_change = 0
            total_ltp = 0
            symbol_count = 0
            
            for symbol, symbol_data in data.items():
                if isinstance(symbol_data, dict):
                    volume = symbol_data.get('volume', 0)
                    price_change = symbol_data.get('price_change', 0)
                    # 🚨 CRITICAL FIX: Get LTP for close price calculation
                    ltp = symbol_data.get('ltp', 0) or symbol_data.get('close', 0)
                    
                    total_volume += volume
                    total_price_change += abs(price_change)
                    total_ltp += ltp
                    symbol_count += 1
            
            if symbol_count > 0:
                avg_volatility = total_price_change / symbol_count
                avg_volume = total_volume / symbol_count
                # 🚨 CRITICAL FIX: Calculate average close price for regime analysis
                avg_close = total_ltp / symbol_count
                
                # Store for regime analysis with close price included
                regime_data = {
                    'timestamp': timestamp,
                    'volatility': avg_volatility,
                    'volume': avg_volume,
                    'close': avg_close,  # 🚨 FIX: Add close field for technical analysis
                    'symbol_count': symbol_count
                }
                
                self.historical_data.append(regime_data)
                
                # Keep only recent data
                if len(self.historical_data) > self.max_history:
                    self.historical_data.pop(0)
                    
        except Exception as e:
            logger.error(f"Error processing market data for regime: {e}")
    
    async def update_regime(self) -> MarketRegime:
        """Update market regime based on accumulated historical data - FIXED"""
        try:
            async with self._regime_lock:
                if len(self.historical_data) < 2:
                    return self.current_regime
                
                # Calculate regime metrics using historical data
                self.regime_metrics.volatility = self._calculate_volatility_fixed()
                self.regime_metrics.trend_strength = self._calculate_trend_strength_fixed()
                self.regime_metrics.momentum = self._calculate_momentum_fixed()
                self.regime_metrics.volume_profile = self._calculate_volume_profile_fixed()
                
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
    
    def _calculate_volatility_fixed(self) -> float:
        """Calculate market volatility - FIXED for accumulated data"""
        try:
            if len(self.historical_data) < 2:
                return 0.02  # Default 2% volatility
            
            # Calculate returns from historical data
            closes = [d['close'] for d in self.historical_data]
            returns = []
            for i in range(1, len(closes)):
                if closes[i-1] > 0:
                    returns.append((closes[i] - closes[i-1]) / closes[i-1])
            
            if len(returns) < 2:
                return 0.02
            
            # Calculate volatility
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            return min(max(volatility, 0.01), 2.0)  # Cap between 1% and 200%
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.02
    
    def _calculate_trend_strength_fixed(self) -> float:
        """Calculate trend strength - FIXED for accumulated data"""
        try:
            if len(self.historical_data) < 10:
                return 20.0  # Default neutral trend strength
            
            # Simple trend strength based on price direction consistency
            closes = [d['close'] for d in self.historical_data[-10:]]  # Last 10 points
            ups = 0
            downs = 0
            
            for i in range(1, len(closes)):
                if closes[i] > closes[i-1]:
                    ups += 1
                elif closes[i] < closes[i-1]:
                    downs += 1
            
            # Calculate trend strength as directional consistency
            total_moves = ups + downs
            if total_moves == 0:
                return 20.0
            
            trend_strength = abs(ups - downs) / total_moves * 100
            return min(max(trend_strength, 0.0), 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 20.0
    
    def _calculate_momentum_fixed(self) -> float:
        """Calculate market momentum - FIXED for accumulated data"""
        try:
            if len(self.historical_data) < 5:
                return 0.0  # Default neutral momentum
            
            # Calculate momentum as recent price change
            current_close = self.historical_data[-1]['close']
            past_close = self.historical_data[-5]['close']  # 5 periods ago
            
            if past_close <= 0:
                return 0.0
            
            momentum = ((current_close - past_close) / past_close) * 100
            return min(max(momentum, -50.0), 50.0)  # Cap between -50% and +50%
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _calculate_volume_profile_fixed(self) -> float:
        """Calculate volume profile strength - FIXED for accumulated data"""
        try:
            if len(self.historical_data) < 10:
                return 0.0  # Default neutral volume profile
            
            # Calculate recent volume vs average volume
            recent_volumes = [d['volume'] for d in self.historical_data[-5:]]  # Last 5 periods
            avg_volumes = [d['volume'] for d in self.historical_data[-10:]]  # Last 10 periods
            
            if not recent_volumes or not avg_volumes:
                return 0.0
            
            recent_avg = np.mean(recent_volumes)
            overall_avg = np.mean(avg_volumes)
            
            if overall_avg <= 0:
                return 0.0
            
            volume_profile = ((recent_avg - overall_avg) / overall_avg) * 100
            return min(max(volume_profile, -100.0), 100.0)  # Cap between -100% and +100%
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return 0.0
    
    def _detect_regime(self) -> MarketRegime:
        """Detect market regime based on metrics - FIXED thresholds"""
        metrics = self.regime_metrics
        
        # Use more realistic thresholds
        if metrics.volatility > 0.15:  # 15% volatility - high volatility
            return MarketRegime.VOLATILE
        elif metrics.trend_strength > 70:  # 70% trend strength - strong trend
            return MarketRegime.TRENDING
        elif metrics.momentum > 3:  # 3% momentum - strong upward momentum
            return MarketRegime.BREAKOUT
        elif metrics.momentum < -3:  # -3% momentum - strong downward momentum
            return MarketRegime.REVERSAL
        else:
            return MarketRegime.RANGING
    
    def _is_regime_stable(self) -> bool:
        """Check if regime is stable enough to update"""
        if len(self.regime_history) < self.min_samples:
            return False
        
        recent_regimes = self.regime_history[-self.min_samples:]
        regime_counts = {}
        for regime in recent_regimes:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        most_common_count = max(regime_counts.values()) if regime_counts else 0
        most_common_ratio = most_common_count / len(recent_regimes)
        
        return most_common_ratio >= self.regime_threshold
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get strategy weights based on current regime"""
        weights = {
            'professional_options_engine': 0.0,
            'nifty_intelligence_engine': 0.0,
            'smart_intraday_options': 0.0,
            'market_microstructure_edge': 0.0
        }
        
        if self.current_regime == MarketRegime.VOLATILE:
            weights['professional_options_engine'] = 0.4
            weights['smart_intraday_options'] = 0.3
            weights['nifty_intelligence_engine'] = 0.2
            weights['market_microstructure_edge'] = 0.1
            
        elif self.current_regime == MarketRegime.TRENDING:
            weights['nifty_intelligence_engine'] = 0.4
            weights['professional_options_engine'] = 0.3
            weights['smart_intraday_options'] = 0.2
            weights['market_microstructure_edge'] = 0.1
            
        elif self.current_regime == MarketRegime.BREAKOUT:
            weights['nifty_intelligence_engine'] = 0.5
            weights['professional_options_engine'] = 0.3
            weights['smart_intraday_options'] = 0.1
            weights['market_microstructure_edge'] = 0.1
            
        elif self.current_regime == MarketRegime.REVERSAL:
            weights['market_microstructure_edge'] = 0.4
            weights['smart_intraday_options'] = 0.3
            weights['professional_options_engine'] = 0.2
            weights['nifty_intelligence_engine'] = 0.1
            
        else:  # RANGING
            weights['smart_intraday_options'] = 0.4
            weights['market_microstructure_edge'] = 0.3
            weights['professional_options_engine'] = 0.2
            weights['nifty_intelligence_engine'] = 0.1
        
        return weights
    
    def get_allocation_multiplier(self, strategy_name: str) -> float:
        """Get allocation multiplier for a strategy based on current regime"""
        regime_name = self.current_regime.value.upper()
        return self.allocation_adjustments.get(regime_name, {}).get(strategy_name, 1.0)
    
    async def generate_signals(self, market_data: Dict) -> List[Dict]:
        """Generate trading signals - meta-strategy doesn't generate direct signals"""
        # Update regime based on market data
        await self.on_market_data(market_data)
        return []
    
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 
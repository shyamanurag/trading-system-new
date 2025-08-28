"""
Nifty Intelligence Engine - NIFTY INDEX SPECIALIST
Advanced Nifty futures and options strategy with GARCH volatility modeling,
regime detection, and sophisticated position management.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedVolatilityExplosion(BaseStrategy):
    """
    NIFTY INDEX SPECIALIST ENGINE
    - GARCH volatility modeling
    - Regime detection (trending/sideways/volatile)
    - Nifty futures with point-based targets
    - Index options strategies
    - Intelligent trailing stops
    """
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.strategy_name = "nifty_intelligence_engine"
        self.description = "Nifty Intelligence Engine with advanced pattern recognition"
        
        # Nifty-specific parameters
        self.nifty_symbols = ['NIFTY-I', 'NIFTY-FUT', 'BANKNIFTY-I', 'FINNIFTY-I']
        
        # Point-based targets for Nifty futures (normal market conditions)
        self.nifty_target_points = 75  # 50-100 points target
        self.nifty_stop_points = 12    # 10-15 points stop
        
        # GARCH volatility parameters
        self.volatility_window = 20
        self.volatility_history = []
        
        # Regime detection
        self.regime_states = ['trending_up', 'trending_down', 'sideways', 'volatile']
        self.current_regime = 'sideways'
        
        # Position management
        self.max_positions_per_symbol = 2
        self.trailing_stop_activation = 0.6  # Activate trailing at 60% of target
        
        logger.info("✅ NiftyIntelligenceEngine strategy initialized")

    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info("✅ Nifty Intelligence Engine loaded successfully")

    async def on_market_data(self, data: Dict):
        """Process market data and generate Nifty signals"""
        if not self.is_active:
            return
            
        try:
            # Generate signals using the existing method
            signals = await self.generate_signals(data)
            
            # Store signals in current_positions for orchestrator to find
            for signal in signals:
                symbol = signal.get('symbol')
                if symbol:
                    self.current_positions[symbol] = signal
                    logger.info(f"🎯 NIFTY INTELLIGENCE: {signal['symbol']} {signal['action']} "
                               f"Confidence: {signal.get('confidence', 0):.1f}/10 "
                               f"Regime: {self.current_regime}")
                
        except Exception as e:
            logger.error(f"Error in Nifty Intelligence Engine: {e}")

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent Nifty signals with regime awareness"""
        try:
            signals = []
            
            if not market_data:
                return signals
            
            # Update volatility model
            self._update_volatility_model(market_data)
            
            # Detect current market regime
            self._detect_market_regime(market_data)
            
            # Generate signals based on regime
            for symbol in self.nifty_symbols:
                if symbol in market_data:
                    signal = await self._analyze_nifty_opportunity(symbol, market_data)
                    if signal:
                        signals.append(signal)
            
            logger.info(f"📊 Nifty Intelligence Engine generated {len(signals)} signals (Regime: {self.current_regime})")
            return signals
            
        except Exception as e:
            logger.error(f"Error in Nifty Intelligence Engine: {e}")
            return []

    def _update_volatility_model(self, market_data: Dict[str, Any]):
        """Update GARCH-inspired volatility model"""
        try:
            nifty_data = market_data.get('NIFTY-I', {})
            if not nifty_data:
                return
            
            change_percent = nifty_data.get('change_percent', 0)
            self.volatility_history.append(abs(change_percent))
            
            # Keep rolling window
            if len(self.volatility_history) > self.volatility_window:
                self.volatility_history.pop(0)
            
            # Calculate current volatility
            if len(self.volatility_history) >= 5:
                self.current_volatility = np.std(self.volatility_history[-10:]) if len(self.volatility_history) >= 10 else np.std(self.volatility_history)
            else:
                self.current_volatility = 1.0
                
        except Exception as e:
            logger.debug(f"Error updating volatility model: {e}")

    def _detect_market_regime(self, market_data: Dict[str, Any]):
        """Detect current market regime using price action"""
        try:
            nifty_data = market_data.get('NIFTY-I', {})
            if not nifty_data:
                return
            
            change_percent = nifty_data.get('change_percent', 0)
            ltp = nifty_data.get('ltp', 0)
            
            # Simple regime detection logic
            if abs(change_percent) > 1.5:
                if change_percent > 0:
                    self.current_regime = 'trending_up'
                else:
                    self.current_regime = 'trending_down'
            elif hasattr(self, 'current_volatility') and self.current_volatility > 2.0:
                self.current_regime = 'volatile'
            else:
                self.current_regime = 'sideways'
                
        except Exception as e:
            logger.debug(f"Error detecting market regime: {e}")

    async def _analyze_nifty_opportunity(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze Nifty opportunity based on regime and volatility"""
        try:
            data = market_data.get(symbol, {})
            if not data:
                return None
            
            ltp = data.get('ltp', 0)
            change_percent = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            
            if ltp <= 0:
                return None
            
            # Regime-based signal generation
            signal_type = None
            confidence = 5.0
            reasoning = f"Nifty analysis in {self.current_regime} regime"
            
            if self.current_regime == 'trending_up' and change_percent > 0.5:
                signal_type = 'buy'
                confidence += 2.0
                reasoning += f" - Uptrend continuation, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'trending_down' and change_percent < -0.5:
                signal_type = 'sell'
                confidence += 2.0
                reasoning += f" - Downtrend continuation, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'volatile' and abs(change_percent) > 1.0:
                # In volatile regime, trade momentum
                signal_type = 'buy' if change_percent > 0 else 'sell'
                confidence += 1.5
                reasoning += f" - Volatile regime momentum, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'sideways' and abs(change_percent) > 0.3:
                # In sideways, look for mean reversion
                signal_type = 'sell' if change_percent > 0 else 'buy'
                confidence += 1.0
                reasoning += f" - Sideways mean reversion, change: {change_percent:.1f}%"
            
            if not signal_type:
                return None

            # Volume/volatility confirmation
            if volume > 1000000:
                confidence += 1.0
            elif volume > 500000:
                confidence += 0.5

            if hasattr(self, 'current_volatility') and self.current_volatility > 2.0:
                confidence += 0.5

            if confidence < 9.0:
                return None

            # Use standardized signal creation to ensure correct fields
            stop_loss = ltp * (0.99 if signal_type == 'buy' else 1.01)
            target = ltp * (1.02 if signal_type == 'buy' else 0.98)
            action = 'BUY' if signal_type == 'buy' else 'SELL'
            return await self.create_standard_signal(
                symbol=symbol,
                action=action,
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': reasoning + " | Index regime"
                },
                market_bias=self.market_bias
            )
            
        except Exception as e:
            logger.debug(f"Error analyzing Nifty opportunity for {symbol}: {e}")
            return None

    async def _create_futures_signal(self, symbol: str, signal_type: str, confidence: float, 
                                   reasoning: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Nifty futures signal with point-based targets"""
        try:
            data = market_data.get(symbol, {})
            ltp = data.get('ltp', 0)
            
            # Point-based targets for futures
            if signal_type == 'buy':
                target_price = ltp + self.nifty_target_points
                stop_loss_price = ltp - self.nifty_stop_points
            else:
                target_price = ltp - self.nifty_target_points
                stop_loss_price = ltp + self.nifty_stop_points
            
            # Position sizing for futures (larger lots)
            position_size = 75  # Standard Nifty lot size
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': ltp,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'quantity': position_size,
                'confidence': confidence,
                'strategy': self.strategy_name,
                'reasoning': reasoning + f" | Futures target: {self.nifty_target_points}pts, stop: {self.nifty_stop_points}pts",
                'timestamp': datetime.now().isoformat(),
                'instrument_type': 'futures',
                'trailing_stop_enabled': True,
                'trailing_stop_activation': self.trailing_stop_activation
            }
            
        except Exception as e:
            logger.error(f"Error creating futures signal: {e}")
            return None

    async def _create_index_options_signal(self, symbol: str, signal_type: str, confidence: float,
                                         reasoning: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create index options signal"""
        try:
            # For index options, use the base strategy's options signal creation
            return await self._create_options_signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                market_data=market_data,
                reasoning=reasoning + " | Index options strategy",
                position_size=150  # Standard options lot size
            )
            
        except Exception as e:
            logger.error(f"Error creating index options signal: {e}")
            return None

logger.info("✅ Nifty Intelligence Engine loaded successfully")
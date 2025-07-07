"""
Enhanced Volatility Explosion Strategy
A sophisticated volatility-based trading strategy with advanced risk management
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedVolatilityExplosion:
    """Enhanced volatility-based trading strategy with advanced risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "EnhancedVolatilityExplosion"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)  # 1 second - aggressive scalping precision
        
    async def initialize(self):
        """Initialize the strategy"""
        logger.info(f"Initializing {self.name} strategy")
        self.is_active = True
        
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and generate signals"""
        if not self.is_active:
            return
            
        try:
            # Check cooldown
            if not self._is_cooldown_passed():
                return
                
            # Process market data and generate signals
            signals = self._generate_signals(data)
            
            # Execute trades based on signals
            if signals:
                await self._execute_trades(signals)
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    def _is_cooldown_passed(self) -> bool:
        """Check if cooldown period has passed"""
        if not self.last_signal_time:
            return True
        return (datetime.now() - self.last_signal_time).total_seconds() >= self.signal_cooldown
            
    def _generate_signals(self, data: Dict) -> List[Dict]:
        """Generate trading signals based on market data"""
        signals = []
        
        try:
            # Extract symbols from market data
            symbols = list(data.keys()) if isinstance(data, dict) else []
            
            for symbol in symbols:
                symbol_data = data.get(symbol, {})
                if not symbol_data:
                    continue
                    
                # Generate signal for this symbol
                signal = self._analyze_volatility(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _analyze_volatility(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze volatility patterns and generate signal if conditions are met"""
        try:
            # Extract price data
            current_price = data.get('close', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            volume = data.get('volume', 0)
            
            if not all([current_price, high, low, volume]):
                return None
                
            # Calculate DYNAMIC risk metrics (NO FIXED PERCENTAGES)
            atr_estimate = high - low  # Single day ATR estimate
            volatility = (atr_estimate / current_price) if current_price > 0 else 0
            
            # Calculate volatility indicators
            price_range = high - low
            avg_price = (high + low) / 2
            volatility_ratio = price_range / avg_price if avg_price > 0 else 0
            
            # Get historical volatility context
            historical_vol = data.get('historical_volatility', 0.02)  # Default 2%
            
            # Volatility explosion detection - ADJUSTED FOR REALISTIC MARKET CONDITIONS
            volatility_score = 0
            
            # Check if current volatility is significantly higher than historical - LOWERED THRESHOLDS
            if volatility_ratio > historical_vol * 1.5:  # 1.5x historical volatility (was 2x)
                volatility_score += 3
            elif volatility_ratio > historical_vol * 1.2:  # 1.2x historical volatility (was 1.5x)
                volatility_score += 2
            elif volatility_ratio > historical_vol * 1.1:  # 1.1x historical volatility (was 1.2x)
                volatility_score += 1
                
            # Check for volume confirmation - LOWERED THRESHOLDS
            volume_change = data.get('volume_change', 0)
            if volume_change > 25:  # 25% volume increase (was 50%)
                volatility_score += 2
            elif volume_change > 15:  # 15% volume increase (was 25%)
                volatility_score += 1
                
            # Check for price gap - LOWERED THRESHOLDS
            price_change = data.get('price_change', 0)
            if abs(price_change) > 0.25:  # 0.25% price change (was 1.0%)
                volatility_score += 1
                
            # Generate signal if volatility explosion is detected
            if volatility_score >= 3:  # Strong volatility explosion
                # Dynamic stop loss based on ATR and volatility strength
                vol_multiplier = min(volatility_score / 5.0, 2.5)
                stop_loss_distance = atr_estimate * vol_multiplier
                
                # Determine direction based on price action
                if price_change > 0:
                    action = 'BUY'
                    stop_loss = current_price - stop_loss_distance
                    target = current_price + (stop_loss_distance * 1.5)  # 1.5:1 R/R for volatility
                else:
                    action = 'SELL'
                    stop_loss = current_price + stop_loss_distance
                    target = current_price - (stop_loss_distance * 1.5)  # 1.5:1 R/R for volatility
                    
                return {
                    'symbol': symbol,
                    'action': action,
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'strategy': self.name,
                    'confidence': min(volatility_score / 5.0, 0.9),
                    'metadata': {
                        'volatility_score': volatility_score,
                        'volatility_ratio': volatility_ratio,
                        'historical_vol': historical_vol,
                        'volume_change': volume_change,
                        'price_change': price_change,
                        'atr_estimate': atr_estimate,
                        'volatility': volatility,
                        'stop_loss_distance': stop_loss_distance,
                        'risk_type': 'VOLATILITY_EXPLOSION_BASED',
                        'vol_multiplier': vol_multiplier,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing volatility for {symbol}: {e}")
            
        return None
        
    async def _execute_trades(self, signals: List[Dict]):
        """Execute trades based on generated signals - PRODUCTION MODE"""
        try:
            for signal in signals:
                logger.info(f"🚀 {self.name} EXECUTING TRADE: {signal['symbol']} {signal['action']} "
                           f"Confidence: {signal['confidence']:.2f}")
                
                # PRODUCTION: Send signal to trade engine for actual execution
                await self._send_to_trade_engine(signal)
                self.current_positions[signal['symbol']] = signal
                
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
    
    async def _send_to_trade_engine(self, signal: Dict):
        """Send signal to trade engine for actual execution"""
        try:
            # Get orchestrator instance and send signal to trade engine
            from src.core.orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                await orchestrator.trade_engine.process_signals([signal])
                logger.info(f"✅ Signal sent to trade engine: {signal['symbol']}")
            else:
                logger.error(f"❌ Trade engine not available for signal: {signal['symbol']}")
                
        except Exception as e:
            logger.error(f"Error sending signal to trade engine: {e}")
        
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 
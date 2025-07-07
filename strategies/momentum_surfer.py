"""
Enhanced Momentum Surfer Strategy
A sophisticated momentum-based trading strategy with advanced risk management
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedMomentumSurfer:
    """Enhanced momentum-based trading strategy with advanced risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "EnhancedMomentumSurfer"
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
                signal = self._analyze_symbol(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _analyze_symbol(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze a single symbol and generate signal if conditions are met"""
        try:
            # Extract price data
            current_price = data.get('close', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            volume = data.get('volume', 0)
            open_price = data.get('open', current_price)
            
            if not all([current_price, high, low, volume]):
                return None
                
            # Calculate DYNAMIC risk metrics (NO FIXED PERCENTAGES)
            atr_estimate = high - low  # Single day ATR estimate
            volatility = (atr_estimate / current_price) if current_price > 0 else 0
            
            # Dynamic risk calculation based on market conditions
            base_risk = max(volatility * 2.0, 0.005)  # At least 0.5% but volatility-driven
            max_risk = min(base_risk, 0.035)  # Cap at 3.5% for extreme volatility
            
            # Calculate momentum indicators
            price_change = data.get('price_change', 0)
            volume_change = data.get('volume_change', 0)
            
            # Simple momentum conditions - ADJUSTED FOR REALISTIC MARKET CONDITIONS
            momentum_score = 0
            
            # Price momentum - LOWERED THRESHOLDS FOR NORMAL TRADING
            if price_change > 0.1:  # 0.1% price increase (was 0.5%)
                momentum_score += 2
            elif price_change > 0.05:  # 0.05% price increase (was 0.2%)
                momentum_score += 1
            elif price_change < -0.1:  # -0.1% price decrease (was -0.5%)
                momentum_score -= 2
            elif price_change < -0.05:  # -0.05% price decrease (was -0.2%)
                momentum_score -= 1
                
            # Volume momentum - LOWERED THRESHOLDS FOR REALISTIC VOLUME
            if volume_change > 10:  # 10% volume increase (was 20%)
                momentum_score += 1
            elif volume_change < -10:  # -10% volume decrease (was -20%)
                momentum_score -= 1
                
            # Generate signal if momentum is strong enough
            if momentum_score >= 2:  # Strong positive momentum
                # Dynamic stop loss based on ATR and momentum strength
                momentum_multiplier = min(momentum_score / 3.0, 2.0)
                stop_loss_distance = atr_estimate * momentum_multiplier
                
                stop_loss = current_price - stop_loss_distance
                target = current_price + (stop_loss_distance * 2.0)  # 2:1 R/R
                
                return {
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'strategy': self.name,
                    'confidence': min(momentum_score / 3.0, 0.9),
                    'metadata': {
                        'momentum_score': momentum_score,
                        'price_change': price_change,
                        'volume_change': volume_change,
                        'atr_estimate': atr_estimate,
                        'volatility': volatility,
                        'stop_loss_distance': stop_loss_distance,
                        'risk_type': 'ATR_MOMENTUM_BASED',
                        'momentum_multiplier': momentum_multiplier,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            elif momentum_score <= -2:  # Strong negative momentum
                # Dynamic stop loss based on ATR and momentum strength
                momentum_multiplier = min(abs(momentum_score) / 3.0, 2.0)
                stop_loss_distance = atr_estimate * momentum_multiplier
                
                stop_loss = current_price + stop_loss_distance
                target = current_price - (stop_loss_distance * 2.0)  # 2:1 R/R
                
                return {
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'strategy': self.name,
                    'confidence': min(abs(momentum_score) / 3.0, 0.9),
                    'metadata': {
                        'momentum_score': momentum_score,
                        'price_change': price_change,
                        'volume_change': volume_change,
                        'atr_estimate': atr_estimate,
                        'volatility': volatility,
                        'stop_loss_distance': stop_loss_distance,
                        'risk_type': 'ATR_MOMENTUM_BASED',
                        'momentum_multiplier': momentum_multiplier,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol}: {e}")
            
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
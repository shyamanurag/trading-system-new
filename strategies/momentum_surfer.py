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
        self.signal_cooldown = config.get('signal_cooldown_seconds', 5)  # 5 seconds - balanced for performance
        
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
            
            if not all([current_price, high, low, volume]):
                return None
                
            # Calculate momentum indicators
            price_change = data.get('price_change', 0)
            volume_change = data.get('volume_change', 0)
            
            # Simple momentum conditions
            momentum_score = 0
            
            # Price momentum
            if price_change > 0.5:  # 0.5% price increase
                momentum_score += 2
            elif price_change > 0.2:
                momentum_score += 1
            elif price_change < -0.5:
                momentum_score -= 2
            elif price_change < -0.2:
                momentum_score -= 1
                
            # Volume momentum
            if volume_change > 20:  # 20% volume increase
                momentum_score += 1
            elif volume_change < -20:
                momentum_score -= 1
                
            # Generate signal if momentum is strong enough
            if momentum_score >= 2:  # Strong positive momentum
                return {
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.98,  # 2% stop loss
                    'target': current_price * 1.03,  # 3% target
                    'strategy': self.name,
                    'confidence': min(momentum_score / 3.0, 0.9),
                    'metadata': {
                        'momentum_score': momentum_score,
                        'price_change': price_change,
                        'volume_change': volume_change,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            elif momentum_score <= -2:  # Strong negative momentum
                return {
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': current_price * 1.02,  # 2% stop loss
                    'target': current_price * 0.97,  # 3% target
                    'strategy': self.name,
                    'confidence': min(abs(momentum_score) / 3.0, 0.9),
                    'metadata': {
                        'momentum_score': momentum_score,
                        'price_change': price_change,
                        'volume_change': volume_change,
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
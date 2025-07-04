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
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)  # 1 second for scalping
        
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
                
            # Calculate volatility indicators
            price_range = high - low
            avg_price = (high + low) / 2
            volatility_ratio = price_range / avg_price if avg_price > 0 else 0
            
            # Get historical volatility context
            historical_vol = data.get('historical_volatility', 0.02)  # Default 2%
            
            # Volatility explosion detection
            volatility_score = 0
            
            # Check if current volatility is significantly higher than historical
            if volatility_ratio > historical_vol * 2:  # 2x historical volatility
                volatility_score += 3
            elif volatility_ratio > historical_vol * 1.5:  # 1.5x historical volatility
                volatility_score += 2
            elif volatility_ratio > historical_vol * 1.2:  # 1.2x historical volatility
                volatility_score += 1
                
            # Check for volume confirmation
            volume_change = data.get('volume_change', 0)
            if volume_change > 50:  # 50% volume increase
                volatility_score += 2
            elif volume_change > 25:
                volatility_score += 1
                
            # Check for price gap
            price_change = data.get('price_change', 0)
            if abs(price_change) > 1.0:  # 1% price change
                volatility_score += 1
                
            # Generate signal if volatility explosion is detected
            if volatility_score >= 3:  # Strong volatility explosion
                # Determine direction based on price action
                if price_change > 0:
                    action = 'BUY'
                    target_multiplier = 1.02
                    stop_multiplier = 0.98
                else:
                    action = 'SELL'
                    target_multiplier = 0.98
                    stop_multiplier = 1.02
                    
                return {
                    'symbol': symbol,
                    'action': action,
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': current_price * stop_multiplier,
                    'target': current_price * target_multiplier,
                    'strategy': self.name,
                    'confidence': min(volatility_score / 5.0, 0.9),
                    'metadata': {
                        'volatility_score': volatility_score,
                        'volatility_ratio': volatility_ratio,
                        'historical_vol': historical_vol,
                        'volume_change': volume_change,
                        'price_change': price_change,
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
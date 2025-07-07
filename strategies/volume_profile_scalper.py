"""
Enhanced Volume Profile Scalper Strategy
A sophisticated volume-based trading strategy with advanced risk management
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedVolumeProfileScalper:
    """Enhanced volume-based trading strategy with advanced risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "EnhancedVolumeProfileScalper"
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
                signal = self._analyze_volume_profile(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _analyze_volume_profile(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze volume profile and generate signal if conditions are met"""
        try:
            # Extract price data
            current_price = data.get('close', 0)
            volume = data.get('volume', 0)
            high = data.get('high', current_price)
            low = data.get('low', current_price)
            
            if not all([current_price, volume]):
                return None
                
            # Calculate DYNAMIC risk metrics (NO FIXED PERCENTAGES)
            atr_estimate = high - low  # Single day ATR estimate
            volatility = (atr_estimate / current_price) if current_price > 0 else 0
            
            # Dynamic risk calculation based on market conditions
            base_risk = max(volatility * 1.5, 0.005)  # At least 0.5% but volatility-driven
            max_risk = min(base_risk, 0.025)  # Cap at 2.5% for scalping
            
            # Calculate volume profile indicators
            volume_change = data.get('volume_change', 0)
            price_change = data.get('price_change', 0)
            
            # Volume profile scoring - ADJUSTED FOR REALISTIC MARKET CONDITIONS
            volume_score = 0
            
            # High volume with price movement - LOWERED THRESHOLDS
            if volume_change > 25 and abs(price_change) > 0.1:  # 25% volume, 0.1% price (was 100%, 0.5%)
                volume_score += 3
            elif volume_change > 15 and abs(price_change) > 0.05:  # 15% volume, 0.05% price (was 50%, 0.3%)
                volume_score += 2
            elif volume_change > 10 and abs(price_change) > 0.03:  # 10% volume, 0.03% price (was 25%, 0.2%)
                volume_score += 1
                
            # Generate signal if volume profile is strong
            if volume_score >= 2:
                action = 'BUY' if price_change > 0 else 'SELL'
                
                # Dynamic stop loss based on ATR and volume strength
                volume_multiplier = min(volume_score / 3.0, 2.0)
                stop_loss_distance = atr_estimate * volume_multiplier
                
                if action == 'BUY':
                    stop_loss = current_price - stop_loss_distance
                    target = current_price + (stop_loss_distance * 1.2)  # 1.2:1 R/R for scalping
                else:
                    stop_loss = current_price + stop_loss_distance
                    target = current_price - (stop_loss_distance * 1.2)  # 1.2:1 R/R for scalping
                
                return {
                    'symbol': symbol,
                    'action': action,
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'strategy': self.name,
                    'confidence': min(volume_score / 3.0, 0.9),
                    'metadata': {
                        'volume_score': volume_score,
                        'volume_change': volume_change,
                        'price_change': price_change,
                        'atr_estimate': atr_estimate,
                        'volatility': volatility,
                        'stop_loss_distance': stop_loss_distance,
                        'risk_type': 'VOLUME_PROFILE_BASED',
                        'volume_multiplier': volume_multiplier,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing volume profile for {symbol}: {e}")
            
        return None
        
    async def _execute_trades(self, signals: List[Dict]):
        """Execute trades based on generated signals"""
        try:
            for signal in signals:
                logger.info(f"{self.name} generated signal: {signal['symbol']} {signal['action']} "
                           f"Confidence: {signal['confidence']:.2f}")
                
                # In a real implementation, this would send to trade engine
                # For now, just log the signal
                self.current_positions[signal['symbol']] = signal
                
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
        
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 
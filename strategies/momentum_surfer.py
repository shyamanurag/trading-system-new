"""
Enhanced Momentum Surfer Strategy
A sophisticated momentum-based trading strategy with proper ATR-based risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedMomentumSurfer(BaseStrategy):
    """Enhanced momentum-based trading strategy with proper ATR risk management"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedMomentumSurfer"
        
        # Strategy-specific parameters
        self.momentum_thresholds = {
            'strong_positive': 0.15,  # 0.15% price increase
            'moderate_positive': 0.08,  # 0.08% price increase
            'strong_negative': -0.15,  # 0.15% price decrease
            'moderate_negative': -0.08,  # 0.08% price decrease
            'volume_threshold': 15  # 15% volume increase
        }
        
        # ATR multipliers for different momentum strengths
        self.atr_multipliers = {
            'strong_momentum': 2.5,  # 2.5x ATR for strong momentum
            'moderate_momentum': 1.8,  # 1.8x ATR for moderate momentum
            'weak_momentum': 1.2   # 1.2x ATR for weak momentum
        }
        
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
                signal = self._analyze_momentum(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _analyze_momentum(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze momentum and generate signal if conditions are met"""
        try:
            # Extract price data
            current_price = data.get('close', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            volume = data.get('volume', 0)
            
            if not all([current_price, high, low, volume]):
                return None
                
            # Calculate proper ATR using base class method
            atr = self.calculate_atr(symbol, high, low, current_price)
            
            # Calculate momentum indicators
            price_change = data.get('price_change', 0)
            volume_change = data.get('volume_change', 0)
            
            # Analyze momentum strength and direction
            momentum_analysis = self._analyze_momentum_strength(price_change, volume_change)
            
            if momentum_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action and ATR multiplier
            action = momentum_analysis['action']
            atr_multiplier = self.atr_multipliers[momentum_analysis['signal_strength']]
            
            # Calculate dynamic stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.5, max_percent=4.0
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=2.0
            )
            
            # Calculate confidence based on momentum strength
            confidence = self._calculate_confidence(momentum_analysis, price_change, volume_change)
            
            # Create standardized signal
            signal = self.create_standard_signal(
                symbol=symbol,
                action=action,
                entry_price=current_price,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'momentum_score': momentum_analysis['score'],
                    'momentum_strength': momentum_analysis['signal_strength'],
                    'price_change': price_change,
                    'volume_change': volume_change,
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'ATR_MOMENTUM_BASED',
                    'strategy_version': '2.0_FIXED'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing momentum for {symbol}: {e}")
            
        return None
    
    def _analyze_momentum_strength(self, price_change: float, volume_change: float) -> Dict:
        """Analyze momentum strength and determine signal type"""
        thresholds = self.momentum_thresholds
        
        # Calculate momentum score
        momentum_score = 0
        
        # Price momentum scoring
        if price_change >= thresholds['strong_positive']:
            momentum_score += 3
        elif price_change >= thresholds['moderate_positive']:
            momentum_score += 2
        elif price_change <= thresholds['strong_negative']:
            momentum_score -= 3
        elif price_change <= thresholds['moderate_negative']:
            momentum_score -= 2
        
        # Volume confirmation
        if volume_change > thresholds['volume_threshold']:
            momentum_score += 1 if momentum_score > 0 else -1
        
        # Determine signal strength and action
        if momentum_score >= 3:
            return {
                'signal_strength': 'strong_momentum',
                'action': 'BUY',
                'score': momentum_score
            }
        elif momentum_score >= 2:
            return {
                'signal_strength': 'moderate_momentum',
                'action': 'BUY',
                'score': momentum_score
            }
        elif momentum_score <= -3:
            return {
                'signal_strength': 'strong_momentum',
                'action': 'SELL',
                'score': momentum_score
            }
        elif momentum_score <= -2:
            return {
                'signal_strength': 'moderate_momentum',
                'action': 'SELL',
                'score': momentum_score
            }
        else:
            return {
                'signal_strength': 'none',
                'action': 'HOLD',
                'score': momentum_score
            }
    
    def _calculate_confidence(self, momentum_analysis: Dict, price_change: float, 
                             volume_change: float) -> float:
        """Calculate signal confidence based on momentum analysis"""
        base_confidence = 0.5
        
        # Boost confidence for strong momentum
        if momentum_analysis['signal_strength'] == 'strong_momentum':
            base_confidence = 0.8
        elif momentum_analysis['signal_strength'] == 'moderate_momentum':
            base_confidence = 0.6
        
        # Boost confidence for strong price change
        price_boost = min(abs(price_change) / 0.5, 0.2)  # Up to 20% boost
        
        # Boost confidence for volume confirmation
        volume_boost = min(volume_change / 50, 0.1)  # Up to 10% boost
        
        final_confidence = base_confidence + price_boost + volume_boost
        
        return min(final_confidence, 0.9)  # Cap at 90%
    
    async def _execute_trades(self, signals: List[Dict]):
        """Execute trades based on generated signals"""
        try:
            for signal in signals:
                logger.info(f"🚀 {self.name} EXECUTING TRADE: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, "
                           f"SL: ₹{signal['stop_loss']:.2f}, "
                           f"Target: ₹{signal['target']:.2f}, "
                           f"Confidence: {signal['confidence']:.2f}")
                
                # Send signal to trade engine
                success = await self.send_to_trade_engine(signal)
                
                if success:
                    self.current_positions[signal['symbol']] = signal
                    logger.info(f"✅ {self.name} trade executed successfully")
                else:
                    logger.error(f"❌ {self.name} trade execution failed")
                
        except Exception as e:
            logger.error(f"Error executing trades: {e}") 
"""
Enhanced Volume Profile Scalper Strategy
A sophisticated volume-based trading strategy with proper ATR-based risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedVolumeProfileScalper(BaseStrategy):
    """Enhanced volume-based trading strategy with proper ATR risk management"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedVolumeProfileScalper"
        
        # Strategy-specific parameters
        self.volume_thresholds = {
            'high_volume': 30,      # 30% volume increase
            'moderate_volume': 20,   # 20% volume increase
            'low_volume': 12,       # 12% volume increase
            'price_confirmation': {
                'strong': 0.12,     # 0.12% price movement
                'moderate': 0.08,   # 0.08% price movement
                'weak': 0.05        # 0.05% price movement
            }
        }
        
        # ATR multipliers for different volume strengths
        self.atr_multipliers = {
            'high_volume': 2.0,     # 2.0x ATR for high volume
            'moderate_volume': 1.5,  # 1.5x ATR for moderate volume
            'low_volume': 1.2       # 1.2x ATR for low volume
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
            high = data.get('high', current_price)
            low = data.get('low', current_price)
            volume = data.get('volume', 0)
            
            if not all([current_price, volume]):
                return None
                
            # Calculate proper ATR using base class method
            atr = self.calculate_atr(symbol, high, low, current_price)
            
            # Calculate volume profile indicators
            volume_change = data.get('volume_change', 0)
            price_change = data.get('price_change', 0)
            
            # Analyze volume profile strength
            volume_analysis = self._analyze_volume_strength(volume_change, price_change)
            
            if volume_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action based on price direction
            action = 'BUY' if price_change > 0 else 'SELL'
            atr_multiplier = self.atr_multipliers[volume_analysis['signal_strength']]
            
            # Calculate dynamic stop loss and target (tighter for scalping)
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.3, max_percent=2.5  # Tighter bounds for scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.5  # 1.5:1 for scalping
            )
            
            # Calculate confidence based on volume analysis
            confidence = self._calculate_confidence(volume_analysis, volume_change, price_change)
            
            # Create standardized signal
            signal = self.create_standard_signal(
                symbol=symbol,
                action=action,
                entry_price=current_price,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'volume_score': volume_analysis['score'],
                    'volume_strength': volume_analysis['signal_strength'],
                    'volume_change': volume_change,
                    'price_change': price_change,
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'VOLUME_PROFILE_BASED',
                    'strategy_version': '2.0_FIXED'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing volume profile for {symbol}: {e}")
            
        return None
    
    def _analyze_volume_strength(self, volume_change: float, price_change: float) -> Dict:
        """Analyze volume strength and determine signal type"""
        thresholds = self.volume_thresholds
        price_thresholds = thresholds['price_confirmation']
        
        # Calculate volume score based on volume change and price confirmation
        volume_score = 0
        
        # Volume strength scoring
        if volume_change >= thresholds['high_volume']:
            if abs(price_change) >= price_thresholds['strong']:
                volume_score = 3
                signal_strength = 'high_volume'
            elif abs(price_change) >= price_thresholds['moderate']:
                volume_score = 2
                signal_strength = 'moderate_volume'
            else:
                volume_score = 1
                signal_strength = 'low_volume'
        elif volume_change >= thresholds['moderate_volume']:
            if abs(price_change) >= price_thresholds['moderate']:
                volume_score = 2
                signal_strength = 'moderate_volume'
            elif abs(price_change) >= price_thresholds['weak']:
                volume_score = 1
                signal_strength = 'low_volume'
            else:
                volume_score = 0
                signal_strength = 'none'
        elif volume_change >= thresholds['low_volume']:
            if abs(price_change) >= price_thresholds['weak']:
                volume_score = 1
                signal_strength = 'low_volume'
            else:
                volume_score = 0
                signal_strength = 'none'
        else:
            volume_score = 0
            signal_strength = 'none'
        
        # Require minimum volume score for signal generation
        if volume_score < 1:
            signal_strength = 'none'
        
        return {
            'signal_strength': signal_strength,
            'score': volume_score
        }
    
    def _calculate_confidence(self, volume_analysis: Dict, volume_change: float, 
                             price_change: float) -> float:
        """Calculate signal confidence based on volume analysis"""
        base_confidence = 0.4
        
        # Boost confidence for strong volume
        if volume_analysis['signal_strength'] == 'high_volume':
            base_confidence = 0.7
        elif volume_analysis['signal_strength'] == 'moderate_volume':
            base_confidence = 0.6
        elif volume_analysis['signal_strength'] == 'low_volume':
            base_confidence = 0.5
        
        # Boost confidence for strong volume change
        volume_boost = min(volume_change / 100, 0.15)  # Up to 15% boost
        
        # Boost confidence for price confirmation
        price_boost = min(abs(price_change) / 0.3, 0.15)  # Up to 15% boost
        
        final_confidence = base_confidence + volume_boost + price_boost
        
        return min(final_confidence, 0.9)  # Cap at 90%
    
    async def _execute_trades(self, signals: List[Dict]):
        """Execute trades based on generated signals - FIXED TO ACTUALLY EXECUTE"""
        try:
            for signal in signals:
                logger.info(f"🚀 {self.name} EXECUTING TRADE: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, "
                           f"SL: ₹{signal['stop_loss']:.2f}, "
                           f"Target: ₹{signal['target']:.2f}, "
                           f"Confidence: {signal['confidence']:.2f}")
                
                # FIXED: Actually send signal to trade engine instead of just logging
                success = await self.send_to_trade_engine(signal)
                
                if success:
                    self.current_positions[signal['symbol']] = signal
                    logger.info(f"✅ {self.name} trade executed successfully")
                else:
                    logger.error(f"❌ {self.name} trade execution failed")
                
        except Exception as e:
            logger.error(f"Error executing trades: {e}") 
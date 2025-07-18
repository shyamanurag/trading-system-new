"""
Enhanced News Impact Scalper Strategy - SCALPING OPTIMIZED
A sophisticated momentum-based trading strategy that identifies rapid price movements
with SCALPING-OPTIMIZED parameters and timing
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedNewsImpactScalper(BaseStrategy):
    """Enhanced momentum-based strategy with SCALPING-OPTIMIZED parameters"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedNewsImpactScalper"
        
        # REALISTIC momentum thresholds (prevent false signals on market noise)
        self.momentum_thresholds = {
            'extreme_momentum': {
                'price_change': 0.35,    # 0.35% rapid price change (realistic)
                'volume_spike': 60       # 60% volume spike (realistic)
            },
            'strong_momentum': {
                'price_change': 0.25,    # 0.25% rapid price change (realistic)
                'volume_spike': 45       # 45% volume spike (realistic)
            },
            'moderate_momentum': {
                'price_change': 0.18,    # 0.18% rapid price change (realistic)
                'volume_spike': 30       # 30% volume spike (realistic)
            }
        }
        
        # SCALPING-OPTIMIZED ATR multipliers (tighter stops)
        self.atr_multipliers = {
            'extreme_momentum': 1.8,    # 1.8x ATR for extreme momentum (tighter)
            'strong_momentum': 1.5,     # 1.5x ATR for strong momentum (tighter)
            'moderate_momentum': 1.2    # 1.2x ATR for moderate momentum (tighter)
        }
        
        # Enhanced cooldown control (prevent signal spam)
        self.scalping_cooldown = 25  # 25 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        self.symbol_cooldown_duration = 40  # 40 seconds per symbol
        
        # Signal quality filters
        self.min_confidence = 0.7  # Minimum 70% confidence required
        
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and generate signals"""
        if not self.is_active:
            return
            
        try:
            # Check SCALPING cooldown
            if not self._is_scalping_cooldown_passed():
                return
                
            # Process market data and generate signals
            signals = self._generate_signals(data)
            
            # CRITICAL FIX: Store signals in current_positions IMMEDIATELY for orchestrator
            for signal in signals:
                self.current_positions[signal['symbol']] = signal
                logger.info(f"🚨 {self.name} SIGNAL GENERATED: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
            
            # Execute trades based on signals (backup method)
            if signals:
                await self._execute_trades(signals)
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
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
                
                # Check symbol-specific cooldown for scalping
                if not self._is_symbol_scalping_cooldown_passed(symbol):
                    continue
                    
                # Generate signal for this symbol
                signal = self._analyze_rapid_momentum(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    # Update symbol cooldown
                    self.symbol_cooldowns[symbol] = datetime.now()
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _is_symbol_scalping_cooldown_passed(self, symbol: str) -> bool:
        """Check if symbol-specific scalping cooldown has passed"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= 20  # 20 seconds per symbol (fastest for news)
    
    def _analyze_rapid_momentum(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze rapid momentum movements with SCALPING optimization"""
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
            
            # Calculate momentum indicators
            price_change = data.get('price_change', 0)
            volume_change = data.get('volume_change', 0)
            
            # Analyze rapid momentum with SCALPING thresholds
            momentum_analysis = self._analyze_momentum_strength(price_change, volume_change)
            
            if momentum_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action based on price direction
            action = 'BUY' if price_change > 0 else 'SELL'
            atr_multiplier = self.atr_multipliers[momentum_analysis['signal_strength']]
            
            # Calculate SCALPING-OPTIMIZED stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.3, max_percent=0.8  # TIGHT bounds for news scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.8  # 1.8:1 for news scalping
            )
            
            # Calculate confidence based on momentum analysis
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
                    'scalping_optimized': True,
                    'momentum_score': momentum_analysis['score'],
                    'momentum_strength': momentum_analysis['signal_strength'],
                    'price_change': price_change,
                    'volume_change': volume_change,
                    'rapid_momentum_detected': True,
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'SCALPING_NEWS_MOMENTUM',
                    'strategy_type': 'news_scalper',
                    'strategy_version': '2.0_SCALPING_OPTIMIZED'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing rapid momentum for {symbol}: {e}")
            
        return None
    
    def _analyze_momentum_strength(self, price_change: float, volume_change: float) -> Dict:
        """Analyze momentum strength to detect rapid movements (news-like behavior)"""
        thresholds = self.momentum_thresholds
        
        momentum_score = 0
        signal_strength = 'none'
        
        # Check for extreme momentum (strongest signal)
        extreme = thresholds['extreme_momentum']
        if abs(price_change) >= extreme['price_change'] and volume_change >= extreme['volume_spike']:
            momentum_score = 4
            signal_strength = 'extreme_momentum'
        
        # Check for strong momentum
        elif abs(price_change) >= thresholds['strong_momentum']['price_change']:
            strong = thresholds['strong_momentum']
            if volume_change >= strong['volume_spike']:
                momentum_score = 3
                signal_strength = 'strong_momentum'
            elif volume_change >= strong['volume_spike'] * 0.7:  # 70% of threshold
                momentum_score = 2.5
                signal_strength = 'strong_momentum'
        
        # Check for moderate momentum
        elif abs(price_change) >= thresholds['moderate_momentum']['price_change']:
            moderate = thresholds['moderate_momentum']
            if volume_change >= moderate['volume_spike']:
                momentum_score = 2
                signal_strength = 'moderate_momentum'
            elif volume_change >= moderate['volume_spike'] * 0.8:  # 80% of threshold
                momentum_score = 1.5
                signal_strength = 'moderate_momentum'
        
        # Additional scoring for very high volume without extreme price movement
        if volume_change >= 40 and abs(price_change) >= 0.08:  # High volume with decent price move
            if signal_strength == 'none':
                momentum_score = 1.5
                signal_strength = 'moderate_momentum'
            else:
                momentum_score += 0.5  # Boost existing signal
        
        # Require minimum score for signal generation
        if momentum_score < 1.5:
            signal_strength = 'none'
        
        return {
            'signal_strength': signal_strength,
            'score': momentum_score
        }
    
    def _calculate_confidence(self, momentum_analysis: Dict, price_change: float, 
                             volume_change: float) -> float:
        """Calculate signal confidence based on momentum analysis"""
        base_confidence = 0.4
        
        # Boost confidence for strong momentum
        if momentum_analysis['signal_strength'] == 'extreme_momentum':
            base_confidence = 0.85
        elif momentum_analysis['signal_strength'] == 'strong_momentum':
            base_confidence = 0.75
        elif momentum_analysis['signal_strength'] == 'moderate_momentum':
            base_confidence = 0.6
        
        # Boost confidence for strong price movement
        price_boost = min(abs(price_change) / 0.5, 0.1)  # Up to 10% boost
        
        # Boost confidence for volume confirmation
        volume_boost = min(volume_change / 100, 0.1)  # Up to 10% boost
        
        # Penalize if volume is too low relative to price movement
        if volume_change < 15 and abs(price_change) > 0.15:
            base_confidence *= 0.8  # 20% penalty for weak volume confirmation
        
        final_confidence = base_confidence + price_boost + volume_boost
        
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
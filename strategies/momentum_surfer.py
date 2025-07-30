"""
Enhanced Momentum Surfer Strategy - SCALPING OPTIMIZED
A sophisticated momentum-based trading strategy with SCALPING-OPTIMIZED risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedMomentumSurfer(BaseStrategy):
    """Enhanced momentum-based trading strategy with SCALPING-OPTIMIZED parameters"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedMomentumSurfer"
        
        # BALANCED momentum thresholds (generate signals for P&L testing)
        self.momentum_thresholds = {
            'strong_positive': 0.15,    # 0.15% price increase (increased from 0.08% for selectivity)
            'moderate_positive': 0.10,  # 0.10% price increase (increased from 0.05% for selectivity)
            'strong_negative': -0.15,   # 0.15% price decrease (increased from -0.08% for selectivity)
            'moderate_negative': -0.10, # 0.10% price decrease (increased from -0.05% for selectivity)
            'volume_threshold': 25      # 25% volume increase (increased from 10% for selectivity)
        }
        
        # REALISTIC ATR multipliers (balanced risk management)
        self.atr_multipliers = {
            'strong_momentum': 2.0,     # 2.0x ATR for strong momentum
            'moderate_momentum': 1.8,   # 1.8x ATR for moderate momentum
            'weak_momentum': 1.5        # 1.5x ATR for weak momentum
        }
        
        # Enhanced cooldown control
        self.scalping_cooldown = 60  # 60 seconds between signals (increased from 30s for selectivity)
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        
        # Signal quality filters
        self.min_confidence_threshold = 0.85  # Minimum 85% confidence (increased from 70%)
        self.trend_confirmation_periods = 3   # Require 3 periods of trend confirmation
    
    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info(f"✅ {self.name} strategy initialized successfully")
        
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and generate signals"""
        if not self.is_active:
            return
            
        try:
            # Check SCALPING cooldown
            if not self._is_scalping_cooldown_passed():
                return
                
            # Check signal rate limits
            if not self._check_signal_rate_limits():
                return
                
            # Process market data and generate signals
            signals = self._generate_signals(data)
            
            # 🎯 QUALITY OVER QUANTITY: Be more selective with signals  
            original_signal_count = len(signals)
            
            # Apply STRICTER quality filters to reduce signal volume
            quality_signals = []
            for signal in signals:
                # Only keep highest confidence signals (0.85+)
                confidence = signal.get('confidence', 0)
                if confidence >= 0.85:
                    quality_signals.append(signal)
                    self.current_positions[signal['symbol']] = signal
                    self._increment_signal_counters()  # Track signal generation
                    logger.info(f"🚨 {self.name} HIGH-QUALITY SIGNAL: {signal['symbol']} {signal['action']} "
                               f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
                else:
                    logger.debug(f"📉 {self.name} SIGNAL REJECTED: {signal['symbol']} low confidence ({confidence:.2f} < 0.85)")
            
            # Log filtering results
            if len(quality_signals) < original_signal_count:
                filtered_count = original_signal_count - len(quality_signals)
                logger.warning(f"🎯 {self.name} QUALITY FILTER: {filtered_count}/{original_signal_count} signals rejected (low confidence)")
            
            # Update last signal time if signals generated
            if quality_signals:
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
                signal = self._analyze_momentum(symbol, symbol_data)
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
        return time_since >= 60  # 60 seconds per symbol for momentum
    
    def _analyze_momentum(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze momentum with SCALPING optimization"""
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
            
            # Analyze momentum strength with enhanced filters to prevent false signals
            momentum_analysis = self._analyze_momentum_strength(price_change, volume_change, data or {})
            
            if momentum_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action and ATR multiplier
            action = momentum_analysis['action']
            atr_multiplier = self.atr_multipliers[momentum_analysis['signal_strength']]
            
            # Calculate SCALPING-OPTIMIZED stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.3, max_percent=0.7  # TIGHT bounds for momentum scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.4  # 1.4:1 for momentum scalping
            )
            
            # Calculate confidence based on momentum analysis
            confidence = self._calculate_confidence(momentum_analysis, price_change, volume_change, data or {})
            
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
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'SCALPING_MOMENTUM',
                    'strategy_version': '2.0_SCALPING_OPTIMIZED'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing momentum for {symbol}: {e}")
            
        return None
    
    def _analyze_momentum_strength(self, price_change: float, volume_change: float, trend_data: Optional[Dict] = None) -> Dict:
        """Analyze momentum strength with enhanced filters to prevent false signals"""
        thresholds = self.momentum_thresholds
        
        # Calculate momentum score based on price and volume changes
        momentum_score = 0
        
        # Price momentum scoring (with realistic thresholds)
        if price_change >= thresholds['strong_positive']:
            momentum_score += 3
        elif price_change >= thresholds['moderate_positive']:
            momentum_score += 2
        elif price_change <= thresholds['strong_negative']:
            momentum_score -= 3
        elif price_change <= thresholds['moderate_negative']:
            momentum_score -= 2
        
        # Volume confirmation (FIXED: Make volume additive, not penalty-based)
        if volume_change > thresholds['volume_threshold']:
            momentum_score += 1 if momentum_score > 0 else -1
        # REMOVED: Penalty for low volume - let price momentum drive signals
        
        # REMOVED: Trend confirmation penalty - too restrictive for scalping
        # REMOVED: Market volatility penalty - we WANT volatility for scalping
        
        # Determine signal strength and action (stricter criteria)
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
                             volume_change: float, trend_data: Optional[Dict] = None) -> float:
        """Calculate signal confidence with enhanced quality scoring"""
        base_confidence = 0.4  # Lower base confidence
        
        # Boost confidence for strong momentum
        if momentum_analysis['signal_strength'] == 'strong_momentum':
            base_confidence = 0.7
        elif momentum_analysis['signal_strength'] == 'moderate_momentum':
            base_confidence = 0.5
        
        # FIXED: Boost confidence for meaningful price change (realistic thresholds)
        if abs(price_change) >= 0.08:  # 0.08% move (aligned with strategy thresholds)
            price_boost = min(abs(price_change) / 0.5, 0.25)  # Up to 25% boost for 0.5% move
        else:
            price_boost = 0  # No boost for very small moves
        
        # Boost confidence for significant volume
        if volume_change >= 20:
            volume_boost = min(volume_change / 100, 0.2)  # Up to 20% boost
        elif volume_change >= 10:
            volume_boost = min(volume_change / 200, 0.1)  # Up to 10% boost
        else:
            volume_boost = 0
        
        # REMOVED: Trend confirmation boost - too complex for scalping
        
        # REMOVED: Time-based penalty - scalping should be fast
        
        # Calculate final confidence
        final_confidence = base_confidence + price_boost + volume_boost
        
        # Cap confidence at 95%
        return min(final_confidence, 0.95)
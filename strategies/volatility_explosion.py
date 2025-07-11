"""
Enhanced Volatility Explosion Strategy - SCALPING OPTIMIZED
A sophisticated volatility-based trading strategy with SCALPING-OPTIMIZED risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedVolatilityExplosion(BaseStrategy):
    """Enhanced volatility-based trading strategy with SCALPING-OPTIMIZED parameters"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedVolatilityExplosion"
        
        # SCALPING-OPTIMIZED volatility thresholds
        self.volatility_thresholds = {
            'extreme_volatility': 1.8,   # 1.8x historical volatility (more sensitive)
            'high_volatility': 1.4,      # 1.4x historical volatility (more sensitive)
            'moderate_volatility': 1.2,  # 1.2x historical volatility (more sensitive)
            'volume_confirmation': {
                'strong': 25,            # 25% volume increase (more sensitive)
                'moderate': 18,          # 18% volume increase (more sensitive)
                'weak': 12              # 12% volume increase (more sensitive)
            },
            'price_gap_threshold': 0.2   # 0.2% price gap (tighter)
        }
        
        # SCALPING-OPTIMIZED ATR multipliers (tighter stops)
        self.atr_multipliers = {
            'extreme_volatility': 2.0,   # 2.0x ATR for extreme volatility (tighter)
            'high_volatility': 1.6,      # 1.6x ATR for high volatility (tighter)
            'moderate_volatility': 1.3   # 1.3x ATR for moderate volatility (tighter)
        }
        
        # SCALPING cooldown control
        self.scalping_cooldown = 20  # 20 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        
        # Historical volatility tracking per symbol
        self.volatility_history = {}
    
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
                
            # Process market data and generate signals
            signals = self._generate_signals(data)
            
            # FIXED: Only store signals for orchestrator collection - no direct execution
            for signal in signals:
                self.current_positions[signal['symbol']] = signal
                logger.info(f"🚨 {self.name} SIGNAL GENERATED: {signal['symbol']} {signal['action']} "
                           f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
            
            # Update last signal time if signals generated
            if signals:
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
                signal = self._analyze_volatility(symbol, symbol_data)
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
        return time_since >= 45  # 45 seconds per symbol for volatility
    
    def _analyze_volatility(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze volatility patterns with SCALPING optimization"""
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
            
            # Calculate current volatility ratio (simplified but consistent)
            current_volatility_ratio = atr / current_price if current_price > 0 else 0
            
            # Get or calculate historical volatility for this symbol
            historical_volatility = self._get_historical_volatility(symbol, current_volatility_ratio)
            
            # Analyze volatility explosion with SCALPING thresholds
            volatility_analysis = self._analyze_volatility_explosion(
                current_volatility_ratio, historical_volatility, data
            )
            
            if volatility_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action based on price direction
            price_change = data.get('price_change', 0)
            action = 'BUY' if price_change > 0 else 'SELL'
            atr_multiplier = self.atr_multipliers[volatility_analysis['signal_strength']]
            
            # Calculate SCALPING-OPTIMIZED stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.4, max_percent=1.0  # TIGHT bounds for volatility scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.6  # 1.6:1 for volatility scalping
            )
            
            # Calculate confidence based on volatility analysis
            confidence = self._calculate_confidence(volatility_analysis, current_volatility_ratio, historical_volatility)
            
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
                    'volatility_score': volatility_analysis['score'],
                    'volatility_strength': volatility_analysis['signal_strength'],
                    'current_volatility': current_volatility_ratio,
                    'historical_volatility': historical_volatility,
                    'volatility_ratio': current_volatility_ratio / historical_volatility if historical_volatility > 0 else 1.0,
                    'volume_change': data.get('volume_change', 0),
                    'price_change': price_change,
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'SCALPING_VOLATILITY_EXPLOSION',
                    'strategy_version': '2.0_SCALPING_OPTIMIZED'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing volatility for {symbol}: {e}")
            
        return None
    
    def _get_historical_volatility(self, symbol: str, current_volatility: float) -> float:
        """Get or calculate historical volatility for the symbol"""
        try:
            if symbol not in self.volatility_history:
                self.volatility_history[symbol] = []
            
            # Add current volatility to history
            self.volatility_history[symbol].append(current_volatility)
            
            # Keep only last 20 observations
            if len(self.volatility_history[symbol]) > 20:
                self.volatility_history[symbol].pop(0)
            
            # Calculate historical average
            if len(self.volatility_history[symbol]) < 5:
                return 0.02  # Default 2% historical volatility
            
            # Use average of last 10-15 observations (excluding most recent)
            historical_data = self.volatility_history[symbol][:-1]  # Exclude current
            if len(historical_data) >= 3:
                return sum(historical_data[-10:]) / len(historical_data[-10:])
            else:
                return 0.02
                
        except Exception as e:
            logger.error(f"Error calculating historical volatility for {symbol}: {e}")
            return 0.02
    
    def _analyze_volatility_explosion(self, current_vol: float, historical_vol: float, data: Dict) -> Dict:
        """Analyze volatility explosion strength"""
        thresholds = self.volatility_thresholds
        volume_change = data.get('volume_change', 0)
        price_change = data.get('price_change', 0)
        
        # Calculate volatility ratio
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        volatility_score = 0
        
        # Volatility explosion scoring
        if vol_ratio >= thresholds['extreme_volatility']:
            volatility_score += 4
            signal_strength = 'extreme_volatility'
        elif vol_ratio >= thresholds['high_volatility']:
            volatility_score += 3
            signal_strength = 'high_volatility'
        elif vol_ratio >= thresholds['moderate_volatility']:
            volatility_score += 2
            signal_strength = 'moderate_volatility'
        else:
            volatility_score = 0
            signal_strength = 'none'
        
        # Volume confirmation
        vol_confirmations = thresholds['volume_confirmation']
        if volume_change >= vol_confirmations['strong']:
            volatility_score += 2
        elif volume_change >= vol_confirmations['moderate']:
            volatility_score += 1
        elif volume_change >= vol_confirmations['weak']:
            volatility_score += 0.5
        
        # Price gap confirmation
        if abs(price_change) >= thresholds['price_gap_threshold']:
            volatility_score += 1
        
        # Require minimum score for signal generation
        if volatility_score < 3:
            signal_strength = 'none'
        
        return {
            'signal_strength': signal_strength,
            'score': volatility_score,
            'vol_ratio': vol_ratio
        }
    
    def _calculate_confidence(self, volatility_analysis: Dict, current_vol: float, historical_vol: float) -> float:
        """Calculate signal confidence based on volatility analysis"""
        base_confidence = 0.5
        
        # Boost confidence for strong volatility explosion
        if volatility_analysis['signal_strength'] == 'extreme_volatility':
            base_confidence = 0.8
        elif volatility_analysis['signal_strength'] == 'high_volatility':
            base_confidence = 0.7
        elif volatility_analysis['signal_strength'] == 'moderate_volatility':
            base_confidence = 0.6
        
        # Boost confidence for high volatility ratio
        vol_ratio_boost = min((volatility_analysis['vol_ratio'] - 1.0) / 2.0, 0.15)  # Up to 15% boost
        
        # Boost confidence for high volatility score
        score_boost = min(volatility_analysis['score'] / 10.0, 0.1)  # Up to 10% boost
        
        final_confidence = base_confidence + vol_ratio_boost + score_boost
        
        return min(final_confidence, 0.9)  # Cap at 90% 
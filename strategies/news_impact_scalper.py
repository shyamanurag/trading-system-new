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
        
        # 🚨 ULTRA-STRICT momentum thresholds - NEWS EVENTS ONLY!
        self.momentum_thresholds = {
            'extreme_momentum': {
                'price_change': 1.0,     # 1.0% rapid price change (REAL NEWS ONLY)
                'volume_spike': 200      # 200% volume spike (MAJOR NEWS EVENTS)
            },
            'strong_momentum': {
                'price_change': 0.75,    # 0.75% rapid price change (SIGNIFICANT NEWS)
                'volume_spike': 150      # 150% volume spike (STRONG NEWS IMPACT)
            },
            'moderate_momentum': {
                'price_change': 0.50,    # 0.50% rapid price change (MINOR NEWS)
                'volume_spike': 100      # 100% volume spike (ELEVATED ACTIVITY)
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
        
        # Signal quality filters (configurable from config)
        self.min_confidence_threshold = config.get('min_confidence_threshold', 0.85)  # Dynamic threshold
        
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
            
            # 🎯 QUALITY OVER QUANTITY: Reduce signal generation volume
            # Instead of generating 35+ signals, be more selective
            original_signal_count = len(signals)
            
            # Apply STRICTER signal quality filters to reduce volume
            quality_signals = []
            for signal in signals:
                # Only keep highest confidence signals (using dynamic threshold)
                confidence = signal.get('confidence', 0)
                min_confidence = self.min_confidence_threshold
                if confidence >= min_confidence:
                    quality_signals.append(signal)
                    self.current_positions[signal['symbol']] = signal
                    logger.info(f"🚨 {self.name} HIGH-QUALITY SIGNAL: {signal['symbol']} {signal['action']} "
                               f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
                else:
                    logger.debug(f"📉 {self.name} SIGNAL REJECTED: {signal['symbol']} low confidence ({confidence:.2f} < {min_confidence})")
            
            # Update signals to only include high-quality ones
            signals = quality_signals
            
            # Log filtering results
            if len(quality_signals) < original_signal_count:
                filtered_count = original_signal_count - len(quality_signals)
                logger.warning(f"🎯 {self.name} QUALITY FILTER: {filtered_count}/{original_signal_count} signals rejected (low confidence)")
            
            # Execute trades based on signals (backup method)
            if quality_signals:
                await self._execute_trades(quality_signals)
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
        """Generate trading signals based on market data - OPTIMIZED FOR QUALITY OVER QUANTITY"""
        signals = []
        
        try:
            # 🚨 CRITICAL FIX: LIMIT TO HIGH-VALUE SYMBOLS ONLY (not all market data)
            # Filter to only process liquid, high-value stocks
            symbols = self._get_priority_symbols(data)
            logger.debug(f"📊 {self.name}: Processing {len(symbols)} priority symbols (filtered from {len(data)} total)")
            
            # 🎯 FURTHER LIMIT: Maximum 5 signals per cycle to prevent bombardment
            max_signals_per_cycle = 5
            processed_count = 0
            
            for symbol in symbols:
                # Hard limit to prevent signal bombardment
                if len(signals) >= max_signals_per_cycle:
                    logger.info(f"🚫 {self.name}: Reached max signals limit ({max_signals_per_cycle}) - stopping to prevent bombardment")
                    break
                    
                symbol_data = data.get(symbol, {})
                if not symbol_data:
                    continue
                
                # Check symbol-specific cooldown for scalping
                if not self._is_symbol_scalping_cooldown_passed(symbol):
                    continue
                    
                processed_count += 1
                
                # Generate signal for this symbol
                signal = self._analyze_rapid_momentum(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    # Update symbol cooldown
                    self.symbol_cooldowns[symbol] = datetime.now()
                    logger.debug(f"✅ {self.name}: Generated signal {len(signals)}/{max_signals_per_cycle} for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _get_priority_symbols(self, data: Dict) -> List[str]:
        """Get priority symbols for trading - focus on liquid, high-value stocks only"""
        try:
            # 🎯 PRECISION OVER SPEED: Only trade high-quality, liquid symbols
            priority_symbols = [
                # NIFTY 50 high-liquidity stocks
                'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR',
                'INFY', 'KOTAKBANK', 'LT', 'SBIN', 'BHARTIARTL',
                'ASIANPAINT', 'MARUTI', 'AXISBANK', 'TITAN', 'NESTLEIND',
                'BAJFINANCE', 'HCLTECH', 'WIPRO', 'M&M', 'ADANIPORT',
                # Index symbols
                'NIFTY', 'BANKNIFTY', 'FINNIFTY'
            ]
            
            # Filter to only symbols present in current market data
            available_symbols = []
            for symbol in priority_symbols:
                if symbol in data and data[symbol]:
                    # Additional filter: Only symbols with sufficient volume
                    symbol_data = data[symbol]
                    volume = symbol_data.get('volume', 0)
                    if volume > 100000:  # Minimum 1 lakh volume for liquidity
                        available_symbols.append(symbol)
            
            logger.debug(f"🎯 {self.name}: Selected {len(available_symbols)} high-liquidity symbols from {len(priority_symbols)} priority list")
            return available_symbols[:15]  # Limit to top 15 even from priority list
            
        except Exception as e:
            logger.error(f"Error filtering priority symbols: {e}")
            # Fallback: Use first 10 symbols from data
            all_symbols = list(data.keys())
            return all_symbols[:10]  # Emergency fallback with hard limit
    
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
        
        # Check for strong momentum - STRICT REQUIREMENTS (NO FALLBACKS)
        elif abs(price_change) >= thresholds['strong_momentum']['price_change']:
            strong = thresholds['strong_momentum']
            if volume_change >= strong['volume_spike']:
                momentum_score = 3
                signal_strength = 'strong_momentum'
            # REMOVED: No fallback logic - either meets threshold or doesn't
        
        # Check for moderate momentum - STRICT REQUIREMENTS (NO FALLBACKS)
        elif abs(price_change) >= thresholds['moderate_momentum']['price_change']:
            moderate = thresholds['moderate_momentum']
            if volume_change >= moderate['volume_spike']:
                momentum_score = 2
                signal_strength = 'moderate_momentum'
            # REMOVED: No 80% fallback logic - either meets threshold or doesn't
        
        # REMOVED: Additional scoring for high volume - too weak and causing bombardment
        # Old logic: volume_change >= 40 and price_change >= 0.08 was generating signals on normal noise
        
        # Require HIGHER minimum score for signal generation (anti-bombardment)
        if momentum_score < 2.0:  # Increased from 1.5 to 2.0 - only strong signals
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
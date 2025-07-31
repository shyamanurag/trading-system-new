"""
Enhanced Volume Profile Scalper Strategy - SCALPING OPTIMIZED
A sophisticated volume-based trading strategy with proper ATR-based risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedVolumeProfileScalper(BaseStrategy):
    """Enhanced volume-based trading strategy with SCALPING-OPTIMIZED parameters"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "EnhancedVolumeProfileScalper"
        
        # STRICT CASH SEGMENT THRESHOLDS (prevent opening second false signals)
        self.volume_thresholds = {
            'high_volume': 75,      # 75% volume increase (much stricter - increased from 50%)
            'moderate_volume': 55,   # 55% volume increase (much stricter - increased from 35%)
            'low_volume': 40,        # 40% volume increase (much stricter - increased from 25%)
            'price_confirmation': {
                'strong': 0.25,     # 0.25% price movement (stricter - increased from 0.15%)
                'moderate': 0.18,   # 0.18% price movement (stricter - increased from 0.10%)
                'weak': 0.12        # 0.12% price movement (stricter - increased from 0.08%)
            }
        }
        
        # STRICTER ATR multipliers for cash segment reliability
        self.atr_multipliers = {
            'high_volume': 2.2,     # 2.2x ATR for high volume (more conservative)
            'moderate_volume': 1.8,  # 1.8x ATR for moderate volume (more conservative)
            'low_volume': 1.5       # 1.5x ATR for low volume (more conservative)
        }
        
        # Enhanced cooldown control with market opening protection
        self.scalping_cooldown = 60  # 60 seconds between signals (longer cooldown)
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        self.market_opening_protection = 900  # 15 minutes protection after market opening
        
        # Stricter signal quality filters (configurable from config)
        self.min_confidence_threshold = config.get('min_confidence_threshold', 0.80)  # Dynamic threshold
        self.volume_confirmation_required = True  # Require volume confirmation
        self.min_market_minutes = 15  # Don't trade until 15 minutes after market open
    
    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info(f"✅ {self.name} strategy initialized successfully")
        
    async def on_market_data(self, data: Dict):
        """Handle incoming market data and generate signals"""
        if not self.is_active:
            return
            
        try:
            # ========================================
            # CRITICAL: MANAGE EXISTING POSITIONS FIRST
            # ========================================
            await self.manage_existing_positions(data)
            
            # MARKET OPENING PROTECTION: Don't trade in first 15 minutes
            if not self._is_market_ready_for_trading():
                return
                
            # Check SCALPING cooldown
            if not self._is_scalping_cooldown_passed():
                return
                
            # Check signal rate limits
            if not self._check_signal_rate_limits():
                return
                
            # Process market data and generate NEW signals (only if no existing positions)
            signals = await self._generate_signals(data)
            
            # 🎯 QUALITY OVER QUANTITY: Be more selective with signals
            original_signal_count = len(signals)
            
            # Apply STRICTER quality filters to reduce signal volume
            quality_signals = []
            for signal in signals:
                # Only keep highest confidence signals (using dynamic threshold)
                confidence = signal.get('confidence', 0)
                min_confidence = self.min_confidence_threshold
                if confidence >= min_confidence:
                    quality_signals.append(signal)
                    self.current_positions[signal['symbol']] = signal
                    self._increment_signal_counters()  # Track signal generation
                    logger.info(f"🚨 {self.name} HIGH-QUALITY SIGNAL: {signal['symbol']} {signal['action']} "
                               f"Entry: ₹{signal['entry_price']:.2f}, Confidence: {signal['confidence']:.2f}")
                else:
                    logger.debug(f"📉 {self.name} SIGNAL REJECTED: {signal['symbol']} low confidence ({confidence:.2f} < {min_confidence})")
            
            # Log filtering results
            if len(quality_signals) < original_signal_count:
                filtered_count = original_signal_count - len(quality_signals)
                logger.warning(f"🎯 {self.name} QUALITY FILTER: {filtered_count}/{original_signal_count} signals rejected (low confidence)")
            
            # Update last signal time if signals generated
            if quality_signals:
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in {self.name} strategy: {str(e)}")
    
    def _is_market_ready_for_trading(self) -> bool:
        """Check if market has been open long enough for reliable volume data"""
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
        
        # If before market open, don't trade
        if now < market_open_time:
            return False
            
        # If within first 15 minutes of market opening, don't trade
        minutes_since_open = (now - market_open_time).total_seconds() / 60
        if minutes_since_open < self.min_market_minutes:
            return False
            
        return True
    
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
    async def _generate_signals(self, data: Dict) -> List[Dict]:
        """Generate trading signals based on market data - ANTI-BOMBARDMENT VERSION"""
        signals = []
        
        try:
            # 🚨 CRITICAL FIX: LIMIT TO HIGH-VALUE SYMBOLS ONLY (not all market data)
            symbols = self._get_priority_symbols(data)
            logger.debug(f"📊 {self.name}: Processing {len(symbols)} priority symbols (filtered from {len(data)} total)")
            
            # 🎯 HARD LIMIT: Maximum 3 signals per cycle (volume strategy should be selective)
            max_signals_per_cycle = 3
            
            for symbol in symbols:
                # Hard limit to prevent signal bombardment
                if len(signals) >= max_signals_per_cycle:
                    logger.info(f"🚫 {self.name}: Reached max signals limit ({max_signals_per_cycle}) - stopping bombardment")
                    break
                    
                symbol_data = data.get(symbol, {})
                if not symbol_data:
                    continue
                
                # Check symbol-specific cooldown for scalping
                if not self._is_symbol_scalping_cooldown_passed(symbol):
                    continue
                    
                # Generate signal for this symbol
                signal = await self._analyze_volume_profile(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    # Update symbol cooldown
                    self.symbol_cooldowns[symbol] = datetime.now()
                    logger.debug(f"✅ {self.name}: Generated signal {len(signals)}/{max_signals_per_cycle} for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _get_priority_symbols(self, data: Dict) -> List[str]:
        """Get priority symbols for volume trading - focus on high-volume, liquid stocks"""
        try:
            # VOLUME STRATEGY: Focus on stocks with consistently high volume
            priority_symbols = [
                # High-volume NIFTY 50 stocks
                'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN',
                'INFY', 'BHARTIARTL', 'LT', 'MARUTI', 'AXISBANK',
                'BAJFINANCE', 'KOTAKBANK', 'TITAN', 'ASIANPAINT', 'HCLTECH',
                # Index symbols (always high volume)
                'NIFTY', 'BANKNIFTY', 'FINNIFTY'
            ]
            
            # Filter based on current volume (volume strategy needs active trading)
            available_symbols = []
            for symbol in priority_symbols:
                if symbol in data and data[symbol]:
                    symbol_data = data[symbol]
                    volume = symbol_data.get('volume', 0)
                    if volume > 500000:  # Minimum 5 lakh volume for volume strategy
                        available_symbols.append(symbol)
            
            logger.debug(f"🎯 {self.name}: Selected {len(available_symbols)} high-volume symbols")
            return available_symbols[:10]  # Limit to top 10 for volume strategy
            
        except Exception as e:
            logger.error(f"Error filtering volume symbols: {e}")
            # Fallback: Use first 5 symbols
            return list(data.keys())[:5]
    
    def _is_symbol_scalping_cooldown_passed(self, symbol: str) -> bool:
        """Check if symbol-specific scalping cooldown has passed"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= 30  # 30 seconds per symbol
    
    async def _analyze_volume_profile(self, symbol: str, data: Dict) -> Optional[Dict]:
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
            
            # Calculate SCALPING-OPTIMIZED stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.2, max_percent=0.6  # ULTRA-TIGHT bounds for scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.5  # 1.5:1 optimal for scalping
            )
            
            # Calculate confidence based on volume analysis
            confidence = self._calculate_confidence(volume_analysis, volume_change, price_change)
            
            # Create standardized signal
            signal = await self.create_standard_signal(
                symbol=symbol,
                action=action,
                entry_price=current_price,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'scalping_optimized': True,
                    'volume_score': volume_analysis['score'],
                    'volume_strength': volume_analysis['signal_strength'],
                    'volume_change': volume_change,
                    'price_change': price_change,
                    'atr': atr,
                    'atr_multiplier': atr_multiplier,
                    'risk_type': 'SCALPING_VOLUME_PROFILE',
                    'strategy_version': '2.0_SCALPING_OPTIMIZED'
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
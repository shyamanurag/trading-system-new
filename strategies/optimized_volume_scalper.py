"""
Optimized Volume Profile Scalper - TRUE SCALPING VERSION
Ultra-fast scalping with proper timing controls and risk management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class OptimizedVolumeScalper(BaseStrategy):
    """TRUE SCALPING: Ultra-fast volume-based scalping with proper timing"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "OptimizedVolumeScalper"
        
        # Enhanced cooldown parameters (prevent signal spam)
        self.signal_cooldown = 25  # 25 seconds between signals
        self.symbol_cooldown = 40  # 40 seconds per symbol
        
        # Signal quality filters
        self.min_confidence = 0.7  # Minimum 70% confidence required
        
        # Position timing controls (CRITICAL for scalping)
        self.position_hold_max_minutes = 2  # Auto-exit after 2 minutes
        self.rapid_exit_minutes = 1         # Consider rapid exit after 1 minute
        
        # REALISTIC volume thresholds (prevent false signals on market noise)
        self.volume_thresholds = {
            'high_volume': 22,       # 22% volume increase (reduced from 45% for current market)
            'moderate_volume': 15,   # 15% volume increase (reduced from 30% for current market)
            'low_volume': 10,        # 10% volume increase (reduced from 20% for current market)
            'price_confirmation': {
                'strong': 0.08,      # 0.08% price movement (reduced from 0.15% for current market)
                'moderate': 0.05,    # 0.05% price movement (reduced from 0.10% for current market)
                'weak': 0.03         # 0.03% price movement (reduced from 0.08% for current market)
            }
        }
        
        # SCALPING-OPTIMIZED ATR multipliers (tighter)
        self.atr_multipliers = {
            'high_volume': 1.5,      # 1.5x ATR (vs 2.0x)
            'moderate_volume': 1.2,  # 1.2x ATR (vs 1.5x)
            'low_volume': 1.0        # 1.0x ATR (vs 1.2x)
        }
        
        # Position tracking for time-based exits
        self.position_timestamps = {}
        
    async def on_market_data(self, data: Dict):
        """Handle market data with scalping-optimized timing"""
        if not self.is_active:
            return
            
        try:
            # Check time-based exits FIRST (critical for scalping)
            await self._check_time_based_exits()
            
            # Check cooldown with scalping parameters
            if not self._is_scalping_cooldown_passed():
                return
                
            # Process market data for scalping signals
            signals = self._generate_scalping_signals(data)
            
            # Execute trades with position tracking
            if signals:
                await self._execute_scalping_trades(signals)
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
    
    def _is_scalping_cooldown_passed(self) -> bool:
        """Scalping-specific cooldown check"""
        if not self.last_signal_time:
            return True
            
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.signal_cooldown
    
    async def _check_time_based_exits(self):
        """Check and execute time-based exits for scalping positions"""
        current_time = datetime.now()
        positions_to_exit = []
        
        for symbol, entry_time in self.position_timestamps.items():
            position_age = (current_time - entry_time).total_seconds() / 60  # minutes
            
            # Rapid exit after 1 minute if not profitable
            if position_age >= self.rapid_exit_minutes:
                # Check if position is profitable
                if symbol in self.current_positions:
                    position_data = self.current_positions[symbol]
                    if position_data and self._should_rapid_exit(position_data):
                        positions_to_exit.append(symbol)
                        logger.info(f"⚡ RAPID EXIT: {symbol} after {position_age:.1f} minutes")
            
            # Force exit after max hold time
            elif position_age >= self.position_hold_max_minutes:
                positions_to_exit.append(symbol)
                logger.info(f"⏰ TIME EXIT: {symbol} after {position_age:.1f} minutes")
        
        # Execute time-based exits
        for symbol in positions_to_exit:
            await self._execute_time_based_exit(symbol)
    
    def _should_rapid_exit(self, position_data: Dict) -> bool:
        """Determine if position should be rapidly exited"""
        # If position is not showing profit potential, exit quickly
        current_price = position_data.get('current_price', 0)
        entry_price = position_data.get('entry_price', 0)
        action = position_data.get('action', '')
        
        if not all([current_price, entry_price, action]):
            return True  # Exit if data is incomplete
        
        # Calculate current profit/loss percentage
        if action == 'BUY':
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            pnl_percent = ((entry_price - current_price) / entry_price) * 100
        
        # Exit if losing more than 0.3% or not gaining at least 0.1%
        return pnl_percent < -0.3 or pnl_percent < 0.1
    
    async def _execute_time_based_exit(self, symbol: str):
        """Execute time-based exit for scalping position"""
        try:
            # Create exit signal
            exit_signal = {
                'symbol': symbol,
                'action': 'EXIT',
                'exit_reason': 'TIME_BASED_SCALPING_EXIT',
                'timestamp': datetime.now().isoformat(),
                'strategy': self.name
            }
            
            # Send to trade engine
            await self.send_to_trade_engine(exit_signal)
            
            # Clean up position tracking
            if symbol in self.position_timestamps:
                del self.position_timestamps[symbol]
            if symbol in self.current_positions:
                del self.current_positions[symbol]
                
        except Exception as e:
            logger.error(f"Error executing time-based exit for {symbol}: {e}")
    
    def _generate_scalping_signals(self, data: Dict) -> List[Dict]:
        """Generate scalping signals with optimized parameters"""
        signals = []
        
        try:
            symbols = list(data.keys()) if isinstance(data, dict) else []
            
            for symbol in symbols:
                symbol_data = data.get(symbol, {})
                if not symbol_data:
                    continue
                
                # Check symbol-specific cooldown
                if not self._is_symbol_cooldown_passed(symbol):
                    continue
                    
                # Generate scalping signal
                signal = self._analyze_scalping_volume(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating scalping signals: {e}")
            
        return signals
    
    def _is_symbol_cooldown_passed(self, symbol: str) -> bool:
        """Check symbol-specific cooldown for scalping"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= self.symbol_cooldown
    
    def _analyze_scalping_volume(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze volume for scalping with optimized parameters"""
        try:
            # Extract price data
            current_price = data.get('close', 0)
            high = data.get('high', current_price)
            low = data.get('low', current_price)
            volume = data.get('volume', 0)
            
            if not all([current_price, volume]):
                return None
                
            # Calculate ATR
            atr = self.calculate_atr(symbol, high, low, current_price)
            
            # Calculate volume indicators
            volume_change = data.get('volume_change', 0)
            price_change = data.get('price_change', 0)
            
            # Analyze volume with scalping thresholds
            volume_analysis = self._analyze_scalping_volume_strength(volume_change, price_change)
            
            if volume_analysis['signal_strength'] == 'none':
                return None
            
            # Determine action
            action = 'BUY' if price_change > 0 else 'SELL'
            atr_multiplier = self.atr_multipliers[volume_analysis['signal_strength']]
            
            # SCALPING-OPTIMIZED stop loss and target
            stop_loss = self.calculate_dynamic_stop_loss(
                current_price, atr, action, atr_multiplier, 
                min_percent=0.2, max_percent=0.8  # ULTRA-TIGHT for scalping
            )
            
            target = self.calculate_dynamic_target(
                current_price, stop_loss, risk_reward_ratio=1.5  # 1.5:1 for scalping
            )
            
            # Calculate confidence
            confidence = self._calculate_scalping_confidence(volume_analysis, volume_change, price_change)
            
            # Create scalping signal
            signal = self.create_standard_signal(
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
                    'max_hold_minutes': self.position_hold_max_minutes,
                    'rapid_exit_minutes': self.rapid_exit_minutes,
                    'strategy_version': 'SCALPING_OPTIMIZED_1.0'
                }
            )
            
            return signal
                
        except Exception as e:
            logger.error(f"Error analyzing scalping volume for {symbol}: {e}")
            
        return None
    
    def _analyze_scalping_volume_strength(self, volume_change: float, price_change: float) -> Dict:
        """Analyze volume strength with scalping-optimized thresholds"""
        thresholds = self.volume_thresholds
        price_thresholds = thresholds['price_confirmation']
        
        volume_score = 0
        
        # SCALPING-OPTIMIZED volume strength scoring
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
        
        return {
            'signal_strength': signal_strength,
            'score': volume_score
        }
    
    def _calculate_scalping_confidence(self, volume_analysis: Dict, volume_change: float, price_change: float) -> float:
        """Calculate confidence for scalping signals"""
        base_confidence = 0.5
        
        # Volume analysis contribution
        volume_score = volume_analysis.get('score', 0)
        volume_confidence = min(volume_score * 0.15, 0.4)  # Max 40% from volume
        
        # Price movement contribution
        price_confidence = min(abs(price_change) * 0.02, 0.3)  # Max 30% from price
        
        # Volume-price synchronization bonus
        if volume_change > 15 and abs(price_change) > 0.05:
            sync_bonus = 0.2  # 20% bonus for good synchronization
        else:
            sync_bonus = 0.0
        
        total_confidence = base_confidence + volume_confidence + price_confidence + sync_bonus
        return min(total_confidence, 1.0)
    
    async def _execute_scalping_trades(self, signals: List[Dict]):
        """Execute scalping trades with position tracking"""
        for signal in signals:
            try:
                # Execute trade
                await self.send_to_trade_engine(signal)
                
                # Track position timestamp for time-based exits
                symbol = signal['symbol']
                self.position_timestamps[symbol] = datetime.now()
                
                # Update symbol cooldown
                if symbol not in self.symbol_cooldowns:
                    self.symbol_cooldowns = {}
                self.symbol_cooldowns[symbol] = datetime.now()
                
                logger.info(f"🎯 SCALPING SIGNAL: {signal['symbol']} {signal['action']} @ {signal['entry_price']} "
                           f"(SL: {signal['stop_loss']}, Target: {signal['target']})")
                
            except Exception as e:
                logger.error(f"Error executing scalping trade: {e}") 
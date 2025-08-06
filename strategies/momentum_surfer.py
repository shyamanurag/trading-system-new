"""
Smart Intraday Options - EQUITY STOCKS SPECIALIST
Comprehensive intraday options strategy covering all market conditions:
trending, sideways, breakouts, reversals, high/low volatility, short selling, range trading.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedMomentumSurfer(BaseStrategy):
    """
    EQUITY STOCKS SPECIALIST ENGINE
    - Market regime aware (trending/sideways/breakout/reversal)
    - Real-time position tracking
    - Short selling for falling markets
    - Range trading for sideways markets
    - Alternative data integration ready
    """
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.strategy_name = "smart_intraday_options"
        self.description = "Smart Intraday Options with dynamic strike selection"
        
        # Market regime parameters
        self.trending_threshold = 1.0  # 1% move indicates trend
        self.sideways_range = 0.5     # 0.5% range for sideways detection
        self.breakout_threshold = 1.5  # 1.5% for breakout detection
        
        # Stock selection criteria
        self.focus_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'ITC',
            'BHARTIARTL', 'KOTAKBANK', 'LT', 'SBIN', 'WIPRO', 'AXISBANK',
            'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC'
        ]
        
        # Position management
        self.max_intraday_positions = 5
        self.profit_booking_threshold = 0.3  # 30% profit booking
        self.stop_loss_threshold = 0.15      # 15% stop loss
        
        # Market condition strategies
        self.strategies_by_condition = {
            'trending_up': self._trending_up_strategy,
            'trending_down': self._trending_down_strategy,
            'sideways': self._sideways_strategy,
            'breakout_up': self._breakout_up_strategy,
            'breakout_down': self._breakout_down_strategy,
            'reversal_up': self._reversal_up_strategy,
            'reversal_down': self._reversal_down_strategy,
            'high_volatility': self._high_volatility_strategy,
            'low_volatility': self._low_volatility_strategy
        }
        
        logger.info("✅ SmartIntradayOptions strategy initialized")

    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info("✅ Smart Intraday Options loaded successfully")

    async def on_market_data(self, data: Dict):
        """Process market data and generate intraday signals"""
        if not self.is_active:
            return
            
        try:
            # Generate signals using the existing method
            signals = await self.generate_signals(data)
            
            # Store signals in current_positions for orchestrator to find
            for signal in signals:
                symbol = signal.get('symbol')
                if symbol:
                    self.current_positions[symbol] = signal
                    logger.info(f"🎯 SMART INTRADAY: {signal['symbol']} {signal['action']} "
                               f"Confidence: {signal.get('confidence', 0):.1f}/10")
                
        except Exception as e:
            logger.error(f"Error in Smart Intraday Options: {e}")

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals based on comprehensive market condition analysis"""
        try:
            signals = []
            
            if not market_data:
                return signals
            
            # Analyze each focus stock
            for stock in self.focus_stocks:
                if stock in market_data:
                    # Detect market condition for this stock
                    market_condition = self._detect_market_condition(stock, market_data)
                    
                    # Generate signal based on condition
                    signal = await self._generate_condition_based_signal(stock, market_condition, market_data)
                    if signal:
                        signals.append(signal)
            
            logger.info(f"📊 Smart Intraday Options generated {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error in Smart Intraday Options: {e}")
            return []

    def _detect_market_condition(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Detect current market condition for the stock"""
        try:
            data = market_data.get(symbol, {})
            if not data:
                return 'sideways'
            
            change_percent = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            ltp = data.get('ltp', 0)
            
            # Get average volume (simulated)
            avg_volume = volume * 0.8  # Assume current is 20% above average
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            
            # Condition detection logic
            if abs(change_percent) >= self.breakout_threshold and volume_ratio > 1.5:
                return 'breakout_up' if change_percent > 0 else 'breakout_down'
            
            elif change_percent >= self.trending_threshold:
                return 'trending_up'
            
            elif change_percent <= -self.trending_threshold:
                return 'trending_down'
            
            elif abs(change_percent) <= self.sideways_range:
                return 'sideways'
            
            elif volume_ratio > 2.0:
                return 'high_volatility'
            
            elif volume_ratio < 0.5:
                return 'low_volatility'
            
            # Check for reversal patterns (simplified)
            elif change_percent > 0.5 and change_percent < self.trending_threshold:
                return 'reversal_up'
            
            elif change_percent < -0.5 and change_percent > -self.trending_threshold:
                return 'reversal_down'
            
            return 'sideways'
            
        except Exception as e:
            logger.debug(f"Error detecting market condition for {symbol}: {e}")
            return 'sideways'

    async def _generate_condition_based_signal(self, symbol: str, condition: str, 
                                             market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal based on detected market condition"""
        try:
            strategy_func = self.strategies_by_condition.get(condition)
            if not strategy_func:
                return None
            
            return await strategy_func(symbol, market_data)
            
        except Exception as e:
            logger.debug(f"Error generating condition-based signal for {symbol}: {e}")
            return None

    async def _trending_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for uptrending stocks"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if change_percent > 1.0:  # Strong uptrend
            confidence = 9.2 + min(change_percent * 0.2, 0.8)
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='buy',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Uptrending stock strategy - Change: {change_percent:.1f}%",
                position_size=100
            )
        return None

    async def _trending_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downtrending stocks - SHORT SELLING"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if change_percent < -1.0:  # Strong downtrend
            confidence = 9.2 + min(abs(change_percent) * 0.2, 0.8)
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='sell',  # SHORT SELLING
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Downtrending stock SHORT strategy - Change: {change_percent:.1f}%",
                position_size=100
            )
        return None

    async def _sideways_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """RANGE TRADING strategy for sideways markets"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        ltp = data.get('ltp', 0)
        
        # Range trading: buy at support, sell at resistance
        if change_percent < -0.3:  # Near support
            confidence = 9.1
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='buy',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Range trading: Buy at support - Change: {change_percent:.1f}%",
                position_size=150
            )
        elif change_percent > 0.3:  # Near resistance
            confidence = 9.1
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='sell',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Range trading: Sell at resistance - Change: {change_percent:.1f}%",
                position_size=150
            )
        return None

    async def _breakout_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward breakouts"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if change_percent > 1.5 and volume > 100000:
            confidence = 9.5 + min(change_percent * 0.1, 0.5)
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='buy',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Upward breakout with volume - Change: {change_percent:.1f}%, Volume: {volume:,}",
                position_size=200
            )
        return None

    async def _breakout_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward breakouts"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if change_percent < -1.5 and volume > 100000:
            confidence = 9.5 + min(abs(change_percent) * 0.1, 0.5)
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='sell',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Downward breakout with volume - Change: {change_percent:.1f}%, Volume: {volume:,}",
                position_size=200
            )
        return None

    async def _reversal_up_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for upward reversals"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if 0.5 <= change_percent <= 1.0:  # Modest upward move after decline
            confidence = 9.0
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='buy',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Upward reversal pattern - Change: {change_percent:.1f}%",
                position_size=100
            )
        return None

    async def _reversal_down_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for downward reversals"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        if -1.0 <= change_percent <= -0.5:  # Modest downward move after rise
            confidence = 9.0
            return await self._create_options_signal(
                symbol=symbol,
                signal_type='sell',
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Downward reversal pattern - Change: {change_percent:.1f}%",
                position_size=100
            )
        return None

    async def _high_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for high volatility periods"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        
        if volume > 200000 and abs(change_percent) > 0.5:
            signal_type = 'buy' if change_percent > 0 else 'sell'
            confidence = 9.3
            return await self._create_options_signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                market_data=market_data,
                reasoning=f"High volatility momentum - Change: {change_percent:.1f}%, Volume: {volume:,}",
                position_size=125
            )
        return None

    async def _low_volatility_strategy(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Strategy for low volatility periods"""
        data = market_data.get(symbol, {})
        change_percent = data.get('change_percent', 0)
        
        # In low volatility, look for any movement
        if abs(change_percent) > 0.2:
            signal_type = 'buy' if change_percent > 0 else 'sell'
            confidence = 9.0
            return await self._create_options_signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                market_data=market_data,
                reasoning=f"Low volatility opportunity - Change: {change_percent:.1f}%",
                position_size=75
            )
        return None

logger.info("✅ Smart Intraday Options loaded successfully")
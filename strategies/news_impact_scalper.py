"""
Enhanced News Impact Scalper Strategy
A sophisticated news-based trading strategy with advanced risk management
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedNewsImpactScalper:
    """Enhanced news-based trading strategy with advanced risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "EnhancedNewsImpactScalper"
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
                signal = self._analyze_news_impact(symbol, symbol_data)
                if signal:
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            
        return signals
    
    def _analyze_news_impact(self, symbol: str, data: Dict) -> Optional[Dict]:
        """Analyze news impact and generate signal if conditions are met"""
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
            
            # Calculate news impact indicators
            price_change = data.get('price_change', 0)
            volume_change = data.get('volume_change', 0)
            
            # NEWS IMPACT ANALYSIS: Use price/volume patterns to detect news impact
            # When real news data unavailable, use market behavior patterns
            news_sentiment = data.get('news_sentiment', 0)  # -1 to 1 scale 
            news_volume = data.get('news_volume', 0)  # Number of news items
            
            # If no real news data, simulate based on price/volume action
            if news_sentiment == 0 and news_volume == 0:
                # Strong price movement with high volume suggests news impact
                if abs(price_change) > 0.15 and volume_change > 30:
                    news_sentiment = 0.6 if price_change > 0 else -0.6
                    news_volume = 5
                elif abs(price_change) > 0.1 and volume_change > 20:
                    news_sentiment = 0.4 if price_change > 0 else -0.4
                    news_volume = 3
            
            # News impact scoring - ADJUSTED FOR REALISTIC MARKET CONDITIONS
            news_score = 0
            
            # Strong news sentiment with price movement - LOWERED THRESHOLDS
            if abs(news_sentiment) > 0.5 and abs(price_change) > 0.15:  # 0.15% price (was 0.8%)
                news_score += 3
            elif abs(news_sentiment) > 0.3 and abs(price_change) > 0.1:  # 0.1% price (was 0.5%)
                news_score += 2
            elif abs(news_sentiment) > 0.2 and abs(price_change) > 0.05:  # 0.05% price (was 0.3%)
                news_score += 1
                
            # High news volume confirmation
            if news_volume > 5:  # 5 news items (was 10)
                news_score += 1
            elif news_volume > 3:  # 3 news items (was 5)
                news_score += 0.5
                
            # Volume spike confirmation - LOWERED THRESHOLDS
            if volume_change > 30:  # 30% volume (was 75%)
                news_score += 1
            elif volume_change > 20:  # 20% volume (was 50%)
                news_score += 0.5
                
            # Generate signal if news impact is strong
            if news_score >= 2.0:  # Lowered from 2.5
                action = 'BUY' if news_sentiment > 0 else 'SELL'
                
                # Dynamic stop loss based on ATR and news impact strength
                news_multiplier = min(news_score / 3.0, 2.0)
                stop_loss_distance = atr_estimate * news_multiplier
                
                if action == 'BUY':
                    stop_loss = current_price - stop_loss_distance
                    target = current_price + (stop_loss_distance * 1.8)  # 1.8:1 R/R for news
                else:
                    stop_loss = current_price + stop_loss_distance
                    target = current_price - (stop_loss_distance * 1.8)  # 1.8:1 R/R for news
                
                return {
                    'symbol': symbol,
                    'action': action,
                    'quantity': 50,  # 1 lot for NIFTY
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'strategy': self.name,
                    'confidence': min(news_score / 4.0, 0.9),
                    'metadata': {
                        'news_score': news_score,
                        'news_sentiment': news_sentiment,
                        'news_volume': news_volume,
                        'volume_change': volume_change,
                        'price_change': price_change,
                        'atr_estimate': atr_estimate,
                        'volatility': volatility,
                        'stop_loss_distance': stop_loss_distance,
                        'risk_type': 'NEWS_IMPACT_BASED',
                        'news_multiplier': news_multiplier,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing news impact for {symbol}: {e}")
            
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
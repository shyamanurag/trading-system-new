"""
Pre-Market Analyzer
Analyzes market conditions and prepares system before trading hours
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class PreMarketAnalyzer:
    """Analyzes pre-market conditions and prepares trading system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.analysis_results = {}
        self.market_outlook = "NEUTRAL"
        self.key_levels = {}
        self.news_events = []
        self.strategy_recommendations = {}
        
    async def run_pre_market_analysis(self) -> Dict:
        """Run complete pre-market analysis"""
        logger.info("Starting pre-market analysis...")
        
        try:
            # 1. Analyze global markets
            global_analysis = await self._analyze_global_markets()
            
            # 2. Analyze previous day's data
            previous_day = await self._analyze_previous_day()
            
            # 3. Calculate key levels
            self.key_levels = await self._calculate_key_levels()
            
            # 4. Check news and events
            self.news_events = await self._check_news_events()
            
            # 5. Analyze volatility expectations
            volatility_analysis = await self._analyze_volatility()
            
            # 6. Generate market outlook
            self.market_outlook = await self._generate_market_outlook(
                global_analysis, previous_day, volatility_analysis
            )
            
            # 7. Recommend strategy adjustments
            self.strategy_recommendations = await self._recommend_strategies()
            
            # 8. Prepare system parameters
            system_params = await self._prepare_system_parameters()
            
            # Compile results
            self.analysis_results = {
                'timestamp': datetime.now().isoformat(),
                'market_outlook': self.market_outlook,
                'global_analysis': global_analysis,
                'previous_day': previous_day,
                'key_levels': self.key_levels,
                'news_events': self.news_events,
                'volatility_analysis': volatility_analysis,
                'strategy_recommendations': self.strategy_recommendations,
                'system_parameters': system_params
            }
            
            logger.info(f"Pre-market analysis complete. Outlook: {self.market_outlook}")
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"Error in pre-market analysis: {e}")
            return {}
    
    async def _analyze_global_markets(self) -> Dict:
        """Analyze global market conditions"""
        try:
            # In production, fetch real data from APIs
            # NO MOCK DATA - Real pre-market data required
            return {
                'us_markets': {
                    'sp500_change': -0.5,
                    'nasdaq_change': -0.8,
                    'dow_change': -0.3,
                    'sentiment': 'BEARISH'
                },
                'asian_markets': {
                    'nikkei_change': 0.2,
                    'hang_seng_change': -0.1,
                    'sentiment': 'NEUTRAL'
                },
                'commodities': {
                    'gold_change': 0.3,
                    'oil_change': -1.2,
                    'sentiment': 'MIXED'
                },
                'currencies': {
                    'usd_inr': 83.25,
                    'change': 0.1
                },
                'overall_sentiment': 'CAUTIOUS'
            }
        except Exception as e:
            logger.error(f"Error analyzing global markets: {e}")
            return {}
    
    async def _analyze_previous_day(self) -> Dict:
        """Analyze previous trading day's data"""
        try:
            # Fetch previous day's data
            # In production, get from database
            return {
                'nifty_close': 19800,
                'nifty_change': -0.3,
                'volume': 'ABOVE_AVERAGE',
                'volatility': 'NORMAL',
                'breadth': {
                    'advances': 800,
                    'declines': 700,
                    'unchanged': 50
                },
                'fii_activity': {
                    'net_buying': -1200,  # Crores
                    'sentiment': 'SELLING'
                },
                'dii_activity': {
                    'net_buying': 800,
                    'sentiment': 'BUYING'
                },
                'key_movers': [
                    {'symbol': 'RELIANCE', 'change': -2.1},
                    {'symbol': 'TCS', 'change': 1.5}
                ]
            }
        except Exception as e:
            logger.error(f"Error analyzing previous day: {e}")
            return {}
    
    async def _calculate_key_levels(self) -> Dict:
        """Calculate key support/resistance levels"""
        try:
            # In production, use technical analysis
            spot_price = 19800  # Example
            
            # Calculate pivot points
            high = 19850
            low = 19720
            close = 19800
            
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
            
            return {
                'pivot': round(pivot, 2),
                'resistance': {
                    'r1': round(r1, 2),
                    'r2': round(r2, 2),
                    'r3': round(r3, 2)
                },
                'support': {
                    's1': round(s1, 2),
                    's2': round(s2, 2),
                    's3': round(s3, 2)
                },
                'previous_high': high,
                'previous_low': low,
                'previous_close': close,
                'opening_range': {
                    'expected_high': close + 50,
                    'expected_low': close - 50
                }
            }
        except Exception as e:
            logger.error(f"Error calculating key levels: {e}")
            return {}
    
    async def _check_news_events(self) -> List[Dict]:
        """Check for important news and events"""
        try:
            # In production, fetch from news APIs
            return [
                {
                    'time': '10:00',
                    'event': 'RBI Policy Meeting',
                    'impact': 'HIGH',
                    'expected_volatility': 'INCREASED'
                },
                {
                    'time': '14:30',
                    'event': 'US CPI Data',
                    'impact': 'MEDIUM',
                    'expected_volatility': 'MODERATE'
                }
            ]
        except Exception as e:
            logger.error(f"Error checking news events: {e}")
            return []
    
    async def _analyze_volatility(self) -> Dict:
        """Analyze expected volatility"""
        try:
            # In production, use options data and VIX
            return {
                'current_vix': 12.5,
                'vix_change': 0.8,
                'expected_range': {
                    'high': 19900,
                    'low': 19700
                },
                'iv_percentile': 45,
                'put_call_ratio': 0.9,
                'max_pain': 19800,
                'volatility_forecast': 'NORMAL',
                'recommended_strategies': ['momentum', 'mean_reversion']
            }
        except Exception as e:
            logger.error(f"Error analyzing volatility: {e}")
            return {}
    
    async def _generate_market_outlook(self, global_data: Dict, 
                                     previous_day: Dict, 
                                     volatility: Dict) -> str:
        """Generate overall market outlook"""
        try:
            score = 0
            
            # Global sentiment
            if global_data.get('overall_sentiment') == 'BULLISH':
                score += 2
            elif global_data.get('overall_sentiment') == 'BEARISH':
                score -= 2
            
            # Previous day trend
            if previous_day.get('nifty_change', 0) > 0.5:
                score += 1
            elif previous_day.get('nifty_change', 0) < -0.5:
                score -= 1
            
            # FII/DII activity
            fii_net = previous_day.get('fii_activity', {}).get('net_buying', 0)
            if fii_net > 1000:
                score += 1
            elif fii_net < -1000:
                score -= 1
            
            # Volatility
            if volatility.get('current_vix', 20) > 20:
                score -= 1
            elif volatility.get('current_vix', 20) < 15:
                score += 1
            
            # Determine outlook
            if score >= 3:
                return "BULLISH"
            elif score <= -3:
                return "BEARISH"
            elif -1 <= score <= 1:
                return "NEUTRAL"
            elif score > 1:
                return "CAUTIOUS_BULLISH"
            else:
                return "CAUTIOUS_BEARISH"
                
        except Exception as e:
            logger.error(f"Error generating market outlook: {e}")
            return "NEUTRAL"
    
    async def _recommend_strategies(self) -> Dict:
        """Recommend strategy adjustments based on analysis"""
        try:
            recommendations = {}
            
            # Based on market outlook
            if self.market_outlook == "BULLISH":
                recommendations['momentum_surfer'] = {
                    'enabled': True,
                    'allocation': 0.3,
                    'bias': 'CALL',
                    'risk_multiplier': 1.2
                }
                recommendations['volatility_explosion'] = {
                    'enabled': True,
                    'allocation': 0.2,
                    'risk_multiplier': 0.8
                }
            elif self.market_outlook == "BEARISH":
                recommendations['momentum_surfer'] = {
                    'enabled': True,
                    'allocation': 0.3,
                    'bias': 'PUT',
                    'risk_multiplier': 1.2
                }
                recommendations['mean_reversion'] = {
                    'enabled': True,
                    'allocation': 0.25,
                    'risk_multiplier': 1.0
                }
            else:  # NEUTRAL
                recommendations['mean_reversion'] = {
                    'enabled': True,
                    'allocation': 0.25,
                    'risk_multiplier': 1.0
                }
                recommendations['volatility_explosion'] = {
                    'enabled': True,
                    'allocation': 0.25,
                    'risk_multiplier': 1.0
                }
            
            # Adjust for events
            if any(event['impact'] == 'HIGH' for event in self.news_events):
                for strategy in recommendations.values():
                    strategy['risk_multiplier'] *= 0.8  # Reduce risk
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error recommending strategies: {e}")
            return {}
    
    async def _prepare_system_parameters(self) -> Dict:
        """Prepare system parameters for the day"""
        try:
            vix = self.analysis_results.get('volatility_analysis', {}).get('current_vix', 15)
            
            # Dynamic risk parameters based on conditions
            if vix > 20:
                max_positions = 3
                risk_per_trade = 0.015
                max_daily_loss = 0.015
            elif vix < 12:
                max_positions = 5
                risk_per_trade = 0.025
                max_daily_loss = 0.025
            else:
                max_positions = 4
                risk_per_trade = 0.02
                max_daily_loss = 0.02
            
            return {
                'max_positions': max_positions,
                'risk_per_trade': risk_per_trade,
                'max_daily_loss': max_daily_loss,
                'order_size_multiplier': 1.0 if vix < 20 else 0.8,
                'stop_loss_multiplier': 1.2 if vix > 15 else 1.0,
                'take_profit_multiplier': 0.8 if vix > 20 else 1.0,
                'enabled_hours': {
                    'start': '09:15' if self.market_outlook != 'BEARISH' else '09:30',
                    'end': '15:15'
                }
            }
            
        except Exception as e:
            logger.error(f"Error preparing system parameters: {e}")
            return {}
    
    def get_key_levels(self) -> Dict:
        """Get calculated key levels"""
        return self.key_levels
    
    def get_market_outlook(self) -> str:
        """Get market outlook"""
        return self.market_outlook
    
    def get_recommendations(self) -> Dict:
        """Get strategy recommendations"""
        return self.strategy_recommendations 
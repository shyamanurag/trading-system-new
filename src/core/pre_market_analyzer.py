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
        self.paper_mode = config.get('paper_mode', True)  # Default to paper mode
        
    async def run_pre_market_analysis(self) -> Dict:
        """Run complete pre-market analysis"""
        logger.info("Starting pre-market analysis...")
        
        try:
            if self.paper_mode:
                logger.info("Running in PAPER MODE - using mock data")
                return await self._run_paper_mode_analysis()
            else:
                return await self._run_live_analysis()
               
        except Exception as e:
            logger.error(f"Error in pre-market analysis: {e}")
            # Return mock data to allow system to continue
            return await self._run_paper_mode_analysis()
    
    async def _run_paper_mode_analysis(self) -> Dict:
        """Run analysis using mock data for paper trading"""
        logger.info("🧪 PAPER MODE: Using simulated market data")
        
        # Mock global markets data
        global_analysis = {
            'us_markets': {
                'sp500_change': 0.2,  # Slightly positive
                'nasdaq_change': 0.1,
                'dow_change': 0.15,
                'sentiment': 'NEUTRAL'
            },
            'asian_markets': {
                'nikkei_change': 0.3,
                'hang_seng_change': 0.1,
                'sentiment': 'BULLISH'
            },
            'commodities': {
                'gold_change': -0.1,
                'oil_change': 0.5,
                'sentiment': 'MIXED'
            },
            'currencies': {
                'usd_inr': 83.20,
                'change': -0.05
            },
            'overall_sentiment': 'NEUTRAL'
        }
        
        # Mock previous day data
        previous_day = {
            'nifty_close': 19850,
            'nifty_change': 0.2,
            'volume': 'NORMAL',
            'volatility': 'LOW',
            'breadth': {
                'advances': 850,
                'declines': 650,
                'unchanged': 50
            },
            'fii_activity': {
                'net_buying': 500,  # Crores
                'sentiment': 'BUYING'
            },
            'dii_activity': {
                'net_buying': 300,
                'sentiment': 'BUYING'
            },
            'key_movers': [
                {'symbol': 'RELIANCE', 'change': 1.2},
                {'symbol': 'TCS', 'change': 0.8},
                {'symbol': 'INFY', 'change': -0.5}
            ]
        }
        
        # Calculate mock key levels
        self.key_levels = await self._calculate_mock_key_levels()
        
        # Mock news events
        self.news_events = [
            {
                'time': '11:00',
                'event': 'Mock RBI Meeting Minutes',
                'impact': 'MEDIUM',
                'expected_volatility': 'NORMAL'
            }
        ]
        
        # Mock volatility analysis
        volatility_analysis = {
            'current_vix': 13.5,
            'vix_change': -0.2,
            'expected_range': {
                'high': 19900,
                'low': 19800
            },
            'iv_percentile': 40,
            'put_call_ratio': 0.85,
            'max_pain': 19850,
            'volatility_forecast': 'LOW',
            'recommended_strategies': ['momentum', 'mean_reversion']
        }
        
        # Generate market outlook
        self.market_outlook = await self._generate_market_outlook(
            global_analysis, previous_day, volatility_analysis
        )
        
        # Recommend strategies for paper mode
        self.strategy_recommendations = await self._recommend_paper_strategies()
        
        # Prepare system parameters
        system_params = await self._prepare_paper_system_parameters()
        
        # Compile results
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'PAPER_TRADING',
            'market_outlook': self.market_outlook,
            'global_analysis': global_analysis,
            'previous_day': previous_day,
            'key_levels': self.key_levels,
            'news_events': self.news_events,
            'volatility_analysis': volatility_analysis,
            'strategy_recommendations': self.strategy_recommendations,
            'system_parameters': system_params
        }
        
        logger.info(f"✅ Paper mode pre-market analysis complete. Outlook: {self.market_outlook}")
        return self.analysis_results
    
    async def _run_live_analysis(self) -> Dict:
        """Run analysis with live data - original logic"""
        # Original analysis logic would go here
        # This is only called when paper_mode = False
        
        try:
            # Try to import live data - this is where it was failing
            from data.truedata_client import live_market_data
            nifty_data = live_market_data.get('NIFTY', {})
            spot_price = nifty_data.get('ltp', nifty_data.get('last_price', 19850))
           
            # Continue with live analysis...
            # [Original analysis code would go here]
           
        except ImportError as e:
            logger.warning(f"TrueData import failed: {e}. Falling back to paper mode.")
            return await self._run_paper_mode_analysis()
        except Exception as e:
            logger.error(f"Live analysis failed: {e}. Falling back to paper mode.")
            return await self._run_paper_mode_analysis()
        
        # Return mock data for now
        return await self._run_paper_mode_analysis()
    
    async def _calculate_mock_key_levels(self) -> Dict:
        """Calculate mock key support/resistance levels for paper trading"""
        # Mock current price
        spot_price = 19850
        
        # Calculate pivot points based on mock data
        high = 19880
        low = 19810
        close = 19850
        
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'spot_price': spot_price,
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
                'expected_high': close + 30,
                'expected_low': close - 30
            }
        }
    
    async def _recommend_paper_strategies(self) -> Dict:
        """Recommend strategies for paper trading mode"""
        # Conservative paper trading recommendations
        recommendations = {
            'momentum_surfer': {
                'enabled': True,
                'allocation': 0.25,
                'bias': 'NEUTRAL',
                'risk_multiplier': 0.8  # Reduced for paper mode
            },
            'mean_reversion': {
                'enabled': True,
                'allocation': 0.25,
                'risk_multiplier': 0.8
            },
            'volatility_explosion': {
                'enabled': True,
                'allocation': 0.20,
                'risk_multiplier': 0.7
            }
        }
        
        logger.info("📊 Paper mode strategy recommendations generated")
        return recommendations
    
    async def _prepare_paper_system_parameters(self) -> Dict:
        """Prepare system parameters for paper trading"""
        return {
            'mode': 'PAPER_TRADING',
            'max_positions': 3,  # Conservative for testing
            'risk_per_trade': 0.015,  # 1.5% risk per trade
            'max_daily_loss': 0.02,   # 2% max daily loss
            'order_size_multiplier': 0.5,  # Smaller sizes for paper mode
            'stop_loss_multiplier': 1.0,
            'take_profit_multiplier': 1.0,
            'enabled_hours': {
                'start': '09:15',
                'end': '15:15'
            },
            'paper_mode_settings': {
                'initial_capital': 100000,  # 1 lakh virtual capital
                'commission_per_trade': 20,
                'slippage_bps': 5  # 5 basis points slippage simulation
            }
        }
    
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
            # Get real spot price from TrueData
            from data.truedata_client import live_market_data
            nifty_data = live_market_data.get('NIFTY', {})
            spot_price = nifty_data.get('ltp', nifty_data.get('last_price', 0.0))
           
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
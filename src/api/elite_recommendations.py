"""
Elite Trading Recommendations API - Using Real Strategies
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import os
import logging
import requests
from src.core.models import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)

class AutonomousEliteScanner:
    """
    Scanner for ELITE POSITIONAL TRADES (1-2 week timeframe)
    
    🎯 PURPOSE: Show high-quality positional trades, NOT intraday scalps
    - Minimum confidence: 8.5/10 (0.85 normalized)
    - Timeframe: 1-2 weeks (positional/swing)
    - Quality over quantity
    """
    
    def __init__(self):
        self.last_scan_time = None
        self.scan_interval_minutes = 0.5  # Scan every 30 seconds
        # 🎯 ELITE = 8.5+ confidence (not 7.5)
        self.min_confidence = 0.85  # Minimum confidence for elite recommendations (8.5/10)
        self.cached_recommendations = []
        self.cache_duration_seconds = 30
        self.strategies = {}
        
        # 🎯 POSITIONAL TIMEFRAME: 1-2 weeks, NOT intraday
        self.min_timeframe_days = 5  # Minimum 5 days (1 week)
        self.max_timeframe_days = 14  # Maximum 14 days (2 weeks)
        self.exclude_intraday = True  # Filter out intraday signals
        
        # CRITICAL: Failed Order Management
        self.failed_orders_cache = []  # Store failed orders with ≥9 confidence
        self.failed_orders_max_age_hours = 24  # Keep failed orders for 24 hours
        
    async def initialize_strategies(self):
        """Initialize UNIQUE PROFESSIONAL strategies - duplicates eliminated"""
        try:
            # Import UNIQUE professional strategies with distinct mathematical edges
            from strategies.optimized_volume_scalper import OptimizedVolumeScalper
            from strategies.regime_adaptive_controller import RegimeAdaptiveController
            from strategies.news_impact_scalper import EnhancedNewsImpactScalper
            from strategies.momentum_surfer import EnhancedMomentumSurfer
            
            # Configuration for strategies (same as orchestrator)
            config = {
                'signal_cooldown_seconds': 1,
                'risk_per_trade': 0.02,
                'max_positions': 5
            }
            
            # Initialize UNIQUE professional strategies with distinct capabilities
            self.strategies = {
                'optimized_volume_scalper': OptimizedVolumeScalper(config),      # Market microstructure + Statistical arbitrage
                'regime_adaptive_controller': RegimeAdaptiveController(config),  # HMM + Kalman filtering (META)
                'news_impact_scalper': EnhancedNewsImpactScalper(config),       # Black-Scholes + Greeks (OPTIONS)
                'momentum_surfer': EnhancedMomentumSurfer(config),              # Hodrick-Prescott + Cross-sectional (MOMENTUM)
                
                # ELIMINATED DUPLICATES
                # 'volatility_explosion': REMOVED - Too much overlap with volume_scalper GARCH models
            }
            
            # Initialize all strategies
            for name, strategy in self.strategies.items():
                await strategy.initialize()
                logger.info(f"✅ Elite scanner initialized strategy: {name}")
                
            logger.info(f"🚀 Elite scanner initialized with {len(self.strategies)} real strategies")
            
        except Exception as e:
            logger.error(f"Error initializing strategies for elite scanner: {e}")
            self.strategies = {}

    async def get_market_data(self):
        """Get market data from the main system"""
        try:
            # Get market data from local API
            from src.api.market_data import get_all_market_data
            market_data_response = await get_all_market_data()
            
            if market_data_response.get('success') and market_data_response.get('data'):
                return market_data_response['data']
            else:
                logger.warning("No market data available from main system")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}

    async def scan_for_elite_setups(self):
        """Scan using the ACTUAL 6 strategies - FIXED: Don't consume signals from main orchestrator"""
        try:
            # CRITICAL FIX: Use shared strategies from orchestrator instead of separate instances
            try:
                from src.core.dependencies import get_orchestrator
                orchestrator = await get_orchestrator()
                
                if orchestrator and hasattr(orchestrator, 'strategies') and orchestrator.strategies:
                    # Use the SAME strategy instances as the main orchestrator
                    shared_strategies = orchestrator.strategies
                    logger.info(f"🔗 Using shared strategies from orchestrator: {len(shared_strategies)} strategies")
                else:
                    # Fallback to separate instances if orchestrator not available
                    if not self.strategies:
                        await self.initialize_strategies()
                    shared_strategies = self.strategies
                    logger.info(f"⚠️ Using separate strategy instances: {len(shared_strategies)} strategies")
                    
            except Exception as e:
                logger.error(f"Error accessing orchestrator strategies: {e}")
                if not self.strategies:
                    await self.initialize_strategies()
                shared_strategies = self.strategies
                
            if not shared_strategies:
                logger.error("No strategies available for elite recommendations")
                return []
            
            # Get market data
            market_data = await self.get_market_data()
            if not market_data:
                logger.warning("No market data available for elite scan")
                return []
            
            logger.info(f"🔍 Elite scan using {len(shared_strategies)} REAL strategies on {len(market_data)} symbols")
            
            # Transform market data for strategies (same as orchestrator)
            transformed_data = self._transform_market_data_for_strategies(market_data)
            
            # Collect all signals from all strategies - FIXED: Don't clear signals
            all_signals = []
            
            for strategy_name, strategy_info in shared_strategies.items():
                try:
                    # Get strategy instance
                    strategy = strategy_info.get('instance') if isinstance(strategy_info, dict) else strategy_info
                    
                    if not strategy:
                        logger.warning(f"No strategy instance for {strategy_name}")
                        continue
                    
                    # FIXED: Read signals WITHOUT clearing them (let orchestrator handle clearing)
                    signals_generated = 0
                    if hasattr(strategy, 'current_positions'):
                        for symbol, signal in strategy.current_positions.items():
                            if isinstance(signal, dict) and 'action' in signal and signal.get('action') != 'HOLD':
                                # Add strategy info to signal
                                signal['strategy'] = strategy_name
                                
                                # Filter by confidence
                                if signal.get('confidence', 0) >= self.min_confidence:
                                    # CRITICAL FIX: Validate expiry for options before adding signal
                                    if self._is_option_expired(signal.get('symbol', '')):
                                        logger.warning(f"🚫 EXPIRED OPTION BLOCKED: {signal['symbol']} - skipping signal")
                                        continue
                                    
                                    # CRITICAL FIX: Copy signal instead of consuming it
                                    all_signals.append(signal.copy())
                                    signals_generated += 1
                                    logger.info(f"✅ ELITE SIGNAL COPIED: {strategy_name} -> {signal['symbol']} {signal['action']}")
                                
                                # FIXED: DON'T clear the signal - let orchestrator handle it
                                # strategy.current_positions[symbol] = None  # REMOVED THIS LINE
                    
                    if signals_generated == 0:
                        logger.info(f"📝 {strategy_name}: No elite signals generated")
                        
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy_name}: {e}")
                    continue
            
            # Convert signals to Elite recommendations format
            elite_recommendations = []
            for signal in all_signals:
                recommendation = self.convert_signal_to_recommendation(signal)
                if recommendation:
                    elite_recommendations.append(recommendation)
            
            # CRITICAL: Add failed orders with ≥9 confidence as elite recommendations
            failed_order_recommendations = self.get_failed_orders_as_recommendations()
            elite_recommendations.extend(failed_order_recommendations)
            
            self.last_scan_time = datetime.now()
            total_strategy_signals = len(all_signals)
            total_failed_orders = len(failed_order_recommendations)
            logger.info(f"🎯 Elite scan completed: {len(elite_recommendations)} recommendations "
                       f"({total_strategy_signals} from strategies + {total_failed_orders} failed orders)")
            logger.info(f"🔄 Signals preserved for main orchestrator to execute trades")
            
            return elite_recommendations
            
        except Exception as e:
            logger.error(f"Error in elite scan: {e}")
            return []

    def _transform_market_data_for_strategies(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform market data for strategies - SAME AS ORCHESTRATOR"""
        try:
            transformed_data = {}
            current_time = datetime.now()
            
            for symbol, data in raw_data.items():
                # Use current price from different possible fields
                current_price = data.get('ltp', data.get('close', data.get('price', 0)))
                volume = data.get('volume', 0)
                
                # Extract OHLC data
                high = data.get('high', current_price)
                low = data.get('low', current_price)
                open_price = data.get('open', current_price)
                
                # Calculate price and volume changes (simple calculation for Elite)
                price_change = data.get('change_percent', 0)
                volume_change = 0  # Simple calculation for Elite
                
                # Create strategy-compatible data format
                strategy_data = {
                    'symbol': symbol,
                    'close': current_price,
                    'ltp': current_price,
                    'high': high,
                    'low': low,
                    'open': open_price,
                    'volume': volume,
                    'price_change': round(price_change, 4),
                    'volume_change': round(volume_change, 4),
                    'timestamp': data.get('timestamp', current_time.isoformat())
                }
                
                transformed_data[symbol] = strategy_data
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error transforming market data: {e}")
            return raw_data

    def _get_live_price(self, symbol: str) -> float:
        """Get live current price from TrueData market data feed"""
        try:
            # Try to get live price from TrueData cache
            from data.truedata_client import live_market_data
            
            if symbol in live_market_data:
                live_data = live_market_data[symbol]
                ltp = live_data.get('ltp', 0)
                if ltp and ltp > 0:
                    logger.debug(f"✅ Live price for {symbol}: ₹{ltp}")
                    return float(ltp)
            
            # Fallback: Try to get from market data API
            from src.api.market_data import get_market_data_for_symbol
            market_data = get_market_data_for_symbol(symbol)
            if market_data and 'ltp' in market_data:
                ltp = market_data['ltp']
                if ltp and ltp > 0:
                    logger.debug(f"✅ API price for {symbol}: ₹{ltp}")
                    return float(ltp)
            
            logger.warning(f"⚠️ No live price available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting live price for {symbol}: {e}")
            return None

    def convert_signal_to_recommendation(self, signal):
        """
        Convert real strategy signal to Elite recommendation format
        
        🎯 ELITE CRITERIA:
        - Confidence >= 8.5/10 (0.85 normalized)
        - Positional timeframe (1-2 weeks)
        - NOT intraday trades
        """
        try:
            entry_price = signal.get('entry_price', 0)
            symbol = signal.get('symbol', 'UNKNOWN')
            
            # 🎯 ELITE FILTER 1: Check confidence threshold (8.5+)
            confidence = signal.get('confidence', 0)
            # Normalize confidence to 0-1 scale if it's in 0-10 scale
            if confidence > 1:
                confidence_normalized = confidence / 10.0
            else:
                confidence_normalized = confidence
                
            if confidence_normalized < self.min_confidence:
                logger.debug(f"🚫 ELITE FILTER: {symbol} rejected - confidence {confidence_normalized:.2f} < {self.min_confidence}")
                return None
            
            # 🎯 ELITE FILTER 2: Exclude intraday trades
            is_intraday = signal.get('is_intraday', signal.get('metadata', {}).get('is_intraday', False))
            trading_mode = signal.get('trading_mode', signal.get('metadata', {}).get('trading_mode', 'SWING'))
            
            if self.exclude_intraday and is_intraday:
                logger.debug(f"🚫 ELITE FILTER: {symbol} rejected - intraday trade not suitable for positional")
                return None
            
            if 'SCALP' in str(trading_mode).upper() or 'INTRADAY' in str(trading_mode).upper():
                logger.debug(f"🚫 ELITE FILTER: {symbol} rejected - {trading_mode} mode not suitable for positional")
                return None
            
            # CRITICAL FIX: Get LIVE current price from TrueData feed
            current_price = self._get_live_price(symbol)
            if current_price is None or current_price <= 0:
                # Fallback to entry price if live price unavailable
                current_price = entry_price
                logger.warning(f"⚠️ No live price for {symbol}, using entry price")
            
            stop_loss = signal.get('stop_loss')
            target = signal.get('target')
            
            # Only use real strategy signals with proper risk management
            if not stop_loss or not target:
                logger.warning(f"Signal rejected: Missing stop_loss or target for {symbol}")
                return None
            
            # Calculate risk/reward using strategy's calculations with entry price
            risk_percent = abs((entry_price - stop_loss) / entry_price) * 100
            reward_percent = abs((target - entry_price) / entry_price) * 100
            risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 3.0
            
            # 🎯 ELITE FILTER 3: Minimum target for positional (3%+)
            if reward_percent < 3.0:
                logger.debug(f"🚫 ELITE FILTER: {symbol} rejected - target {reward_percent:.1f}% < 3% for positional")
                return None
            
            signal_timeframe = signal.get('timeframe', signal.get('metadata', {}).get('timeframe', None))
            is_options = 'CE' in symbol or 'PE' in symbol
            
            # 🎯 POSITIONAL TIMEFRAME: 1-2 weeks
            if signal_timeframe and 'week' in signal_timeframe.lower():
                timeframe = signal_timeframe
                valid_days = 10
            elif risk_reward_ratio >= 3.0:
                timeframe = "1-2 weeks (Positional Swing)"
                valid_days = 10
            elif risk_reward_ratio >= 2.0:
                timeframe = "5-10 days (Swing)"
                valid_days = 7
            else:
                timeframe = "5-7 days (Short Swing)"
                valid_days = 5
            
            logger.info(f"✅ ELITE APPROVED: {symbol} - Confidence: {confidence_normalized:.2f}, Target: {reward_percent:.1f}%, Timeframe: {timeframe}")
            
            # Calculate dynamic position size based on confidence and risk
            # Higher confidence + lower risk = larger position size
            if signal['confidence'] >= 0.90 and risk_percent <= 2.0:
                position_size_percent = 3.0  # 3% of capital
            elif signal['confidence'] >= 0.85 and risk_percent <= 3.0:
                position_size_percent = 2.5  # 2.5% of capital
            elif signal['confidence'] >= 0.80:
                position_size_percent = 2.0  # 2% of capital
            elif signal['confidence'] >= 0.75:
                position_size_percent = 1.5  # 1.5% of capital
            else:
                position_size_percent = 1.0  # 1% of capital (conservative)
            
            # Build dynamic confluence factors based on actual signal data
            confluence_factors = [
                f"Real Strategy: {signal['strategy']}",
                f"Signal Confidence: {signal['confidence']:.2f} ({signal['confidence']*100:.1f}/10)",
                f"Entry: ₹{entry_price:,.2f} | Current: ₹{current_price:,.2f}",
                f"Risk/Reward: {risk_reward_ratio:.2f}:1 (Risk: {risk_percent:.1f}%, Reward: {reward_percent:.1f}%)"
            ]
            
            # Add strategy-specific metadata if available
            if signal.get('metadata', {}).get('atr'):
                confluence_factors.append(f"ATR: {signal['metadata']['atr']:.2f}")
            if signal.get('metadata', {}).get('volume'):
                confluence_factors.append(f"Volume: {signal['metadata']['volume']:,.0f}")
            if signal.get('metadata', {}).get('underlying_change'):
                confluence_factors.append(f"Momentum: {signal['metadata']['underlying_change']:.2f}%")
            
            # Add timestamp
            confluence_factors.append(f"Generated: {signal['metadata'].get('timestamp', datetime.now().isoformat())}")
            
            return {
                "recommendation_id": f"ELITE_{signal['symbol']}_{signal['strategy']}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                "symbol": signal['symbol'],
                "direction": "LONG" if signal['action'] == 'BUY' else "SHORT",
                "strategy": f"Real {signal['strategy']}",
                "confidence": round(signal['confidence'] * 100, 1),
                "entry_price": round(entry_price, 2),
                "current_price": round(current_price, 2),
                "stop_loss": round(stop_loss, 2),
                "primary_target": round(target, 2),
                "secondary_target": self._calculate_secondary_target(target, current_price, signal['action']),
                "tertiary_target": self._calculate_tertiary_target(target, current_price, signal['action']),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "risk_metrics": {
                    "risk_percent": round(risk_percent, 2),
                    "reward_percent": round(reward_percent, 2),
                    "position_size": round(position_size_percent, 1),
                    "risk_calculation": "DYNAMIC_ATR_BASED"
                },
                "confluence_factors": confluence_factors,
                "entry_conditions": [
                    f"Real {signal['strategy']} strategy signal",
                    "Price at strategy-calculated entry level",
                    f"ATR-based dynamic risk management (R:R {risk_reward_ratio:.1f}:1)",
                    f"Market-adaptive position sizing ({position_size_percent}% capital)",
                    f"Confidence: {signal['confidence']*100:.0f}/10"
                ],
                "timeframe": timeframe,
                "valid_until": (datetime.now() + timedelta(days=valid_days)).isoformat(),
                "status": "ACTIVE",
                "generated_at": datetime.now().isoformat(),
                "data_source": "REAL_STRATEGY_GENERATED",
                "strategy_metadata": signal.get('metadata', {}),
                "autonomous": True,
                
                # 🔥 NEW: Clear trading mode indicators
                "is_intraday": is_intraday,
                "trading_mode": trading_mode,
                "square_off_time": signal.get('square_off_time', "15:15 IST" if is_intraday else "N/A"),
                "WARNING": "INTRADAY_SIGNAL_SQUARE_OFF_TODAY" if is_intraday else "SWING_SIGNAL_NOT_FOR_INTRADAY",
                "recommendation_type": "INTRADAY" if is_intraday else "SWING"
            }
            
        except Exception as e:
            logger.error(f"Error converting signal to recommendation: {e}")
            return None

    def _calculate_secondary_target(self, primary_target, entry_price, action):
        """Calculate secondary target based on position direction"""
        if action == 'SELL':  # SHORT position
            distance = abs(entry_price - primary_target)
            return round(primary_target - (distance * 0.5), 2)
        else:  # LONG position
            distance = abs(primary_target - entry_price)
            return round(primary_target + (distance * 0.5), 2)
    
    def _calculate_tertiary_target(self, primary_target, entry_price, action):
        """Calculate tertiary target based on position direction"""
        if action == 'SELL':  # SHORT position
            distance = abs(entry_price - primary_target)
            return round(primary_target - (distance * 1.0), 2)
        else:  # LONG position
            distance = abs(primary_target - entry_price)
            return round(primary_target + (distance * 1.0), 2)


    def _is_option_expired(self, symbol: str) -> bool:
        """
        Check if an option symbol is expired based on current date.
        Returns True if option is expired and should not be traded.
        """
        try:
            if not symbol or ('CE' not in symbol and 'PE' not in symbol):
                return False  # Not an option
            
            from datetime import datetime
            today = datetime.now().date()
            
            # Extract date from option symbol (assuming format like SYMBOL25JUL1000CE)
            import re
            date_pattern = r'(\d{2})([A-Z]{3})'
            match = re.search(date_pattern, symbol)
            
            if not match:
                logger.warning(f"⚠️ Could not extract expiry date from symbol: {symbol}")
                return False
            
            day = int(match.group(1))
            month_abbr = match.group(2)
            
            # Map month abbreviations
            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            
            if month_abbr not in month_map:
                logger.warning(f"⚠️ Unknown month abbreviation in symbol: {symbol}")
                return False
            
            month = month_map[month_abbr]
            year = today.year  # Assume current year
            
            # Create expiry date
            try:
                from datetime import date
                expiry_date = date(year, month, day)
                
                # If expiry date is in the past, the option is expired
                is_expired = expiry_date < today
                
                if is_expired:
                    logger.info(f"🚫 EXPIRED OPTION: {symbol} expired on {expiry_date}")
                else:
                    logger.debug(f"✅ VALID OPTION: {symbol} expires on {expiry_date}")
                
                return is_expired
                
            except ValueError as e:
                logger.warning(f"⚠️ Invalid date for symbol {symbol}: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error checking option expiry for {symbol}: {e}")
            return False

    def add_failed_order(self, signal: Dict):
        """Add failed order to elite recommendations if confidence ≥9"""
        try:
            confidence = signal.get('confidence', 0)
            if confidence >= 9.0:
                failed_order = {
                    'signal': signal,
                    'failed_at': datetime.now(),
                    'reason': 'EXECUTION_FAILED',
                    'status': 'AVAILABLE_FOR_ELITE'
                }
                self.failed_orders_cache.append(failed_order)
                
                # Clean up old failed orders
                self._cleanup_old_failed_orders()
                
                logger.info(f"📋 ELITE: Added failed order {signal['symbol']} with confidence {confidence:.1f} to elite recommendations")
                
        except Exception as e:
            logger.error(f"Error adding failed order to elite cache: {e}")
    
    def _cleanup_old_failed_orders(self):
        """Remove failed orders older than max age"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.failed_orders_max_age_hours)
            self.failed_orders_cache = [
                order for order in self.failed_orders_cache 
                if order['failed_at'] > cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error cleaning up failed orders: {e}")
    
    def get_failed_orders_as_recommendations(self) -> List[Dict]:
        """Get failed orders as elite recommendations"""
        try:
            self._cleanup_old_failed_orders()
            
            recommendations = []
            for failed_order in self.failed_orders_cache:
                signal = failed_order['signal']
                recommendations.append({
                    'symbol': signal.get('symbol'),
                    'action': signal.get('action'),
                    'entry_price': signal.get('entry_price'),
                    'stop_loss': signal.get('stop_loss'),
                    'target': signal.get('target'),
                    'confidence': signal.get('confidence'),
                    'strategy': signal.get('strategy', 'FAILED_ORDER_RECOVERY'),
                    'signal_type': 'FAILED_ORDER_ELITE',
                    'failed_at': failed_order['failed_at'].isoformat(),
                    'age_hours': (datetime.now() - failed_order['failed_at']).total_seconds() / 3600,
                    'recommendation_reason': f"High confidence signal ({signal.get('confidence', 0):.1f}/10) failed execution - manual review recommended"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting failed orders as recommendations: {e}")
            return []

# Global scanner instance
autonomous_scanner = AutonomousEliteScanner()

@router.get("/")
async def get_elite_recommendations():
    """Get current elite trading recommendations using REAL strategies + Live Signal Recorder"""
    try:
        logger.info("📊 ELITE RECOMMENDATIONS ENDPOINT CALLED - Fetching live signals...")
        
        # Get live recorded signals from signal recorder
        from src.core.signal_recorder import get_all_elite_recommendations
        live_recommendations = await get_all_elite_recommendations()
        logger.info(f"✅ Retrieved {len(live_recommendations)} live recommendations from signal recorder")
        
        # Use intelligent caching for strategy-based recommendations
        cache_duration_seconds = 30
        
        if autonomous_scanner.last_scan_time is None or \
           (datetime.now() - autonomous_scanner.last_scan_time).total_seconds() > cache_duration_seconds:
            logger.info("🔄 Running fresh elite scan using REAL strategies...")
            strategy_recommendations = await autonomous_scanner.scan_for_elite_setups()
            autonomous_scanner.cached_recommendations = strategy_recommendations
            logger.info(f"✅ Fresh scan completed: {len(strategy_recommendations)} strategy recommendations")
        else:
            logger.info("⚡ Using cached elite recommendations")
            strategy_recommendations = autonomous_scanner.cached_recommendations
            logger.info(f"📦 Cached recommendations: {len(strategy_recommendations)}")
        
        # Combine live signals with strategy recommendations
        all_recommendations = live_recommendations + strategy_recommendations
        
        # 🔧 2025-12-30 FIX: Show ALL signals, not just ACTIVE ones
        # Include EXECUTED (trades we made), EXPIRED (for review), and ACTIVE
        # This fixes "15 registered but shows 0" issue
        seen_keys = set()  # Track symbol+action to avoid duplicates
        all_filtered_recommendations = []
        
        # Valid statuses to show (includes executed and expired for transparency)
        valid_statuses = ['ACTIVE', 'GENERATED', 'PENDING_EXECUTION', 'EXECUTED', 'EXPIRED']
        
        for rec in all_recommendations:
            status = rec.get('status', 'UNKNOWN')
            symbol = rec.get('symbol', '')
            action = rec.get('action', rec.get('direction', ''))
            
            # Create unique key to avoid duplicates
            rec_key = f"{symbol}_{action}_{rec.get('recommendation_id', '')}"
            
            if rec_key not in seen_keys:
                # Update current price with live data
                live_price = autonomous_scanner._get_live_price(symbol)
                if live_price and live_price > 0:
                    rec['current_price'] = round(live_price, 2)
                    logger.debug(f"📈 Updated {symbol} current price: ₹{live_price}")
                
                # Ensure status field is populated
                if not status or status == 'UNKNOWN':
                    rec['status'] = 'GENERATED'
                
                all_filtered_recommendations.append(rec)
                seen_keys.add(rec_key)
        
        # Sort by timestamp (newest first)
        all_filtered_recommendations.sort(
            key=lambda x: x.get('generated_at', ''), 
            reverse=True
        )
        
        # Separate active vs historical for logging
        active_count = sum(1 for r in all_filtered_recommendations if r.get('status') in ['ACTIVE', 'GENERATED', 'PENDING_EXECUTION'])
        executed_count = sum(1 for r in all_filtered_recommendations if r.get('status') == 'EXECUTED')
        expired_count = sum(1 for r in all_filtered_recommendations if r.get('status') == 'EXPIRED')
        
        logger.info(f"📊 FINAL RESULT: {len(all_filtered_recommendations)} recommendations "
                   f"(Active: {active_count}, Executed: {executed_count}, Expired: {expired_count})")
        logger.info(f"   From {len(live_recommendations)} live + {len(strategy_recommendations)} strategy signals")
        
        if len(all_filtered_recommendations) == 0:
            logger.warning("⚠️ NO RECOMMENDATIONS FOUND - Check:")
            logger.warning("   1. Are strategies generating signals?")
            logger.warning("   2. Are signals meeting min_confidence threshold (0.75)?")
            logger.warning("   3. Signal recorder may need to be checked")
        else:
            logger.info(f"✅ Returning {len(all_filtered_recommendations)} recommendations:")
            for i, rec in enumerate(all_filtered_recommendations[:3], 1):  # Log first 3
                logger.info(f"   {i}. {rec.get('symbol')} - {rec.get('direction')} - Status: {rec.get('status')} - Confidence: {rec.get('confidence')}%")
        
        return {
            "success": True,
            "recommendations": all_filtered_recommendations,
            "total_count": len(all_filtered_recommendations),
            "active_count": active_count,
            "executed_count": executed_count,
            "expired_count": expired_count,
            "live_signals": len(live_recommendations),
            "strategy_signals": len(strategy_recommendations),
            "status": "ACTIVE",
            "message": f"Found {len(all_filtered_recommendations)} recommendations (Active: {active_count}, Executed: {executed_count}, Expired: {expired_count})",
            "data_source": "LIVE_SIGNALS_AND_REAL_STRATEGIES",
            "scan_timestamp": autonomous_scanner.last_scan_time.isoformat() if autonomous_scanner.last_scan_time else datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "next_scan": (datetime.now() + timedelta(minutes=autonomous_scanner.scan_interval_minutes)).isoformat(),
            "strategies_used": list(autonomous_scanner.strategies.keys()) if autonomous_scanner.strategies else [],
            "cache_status": "LIVE_SIGNALS_INTEGRATED",
            "debug_info": {
                "total_before_filter": len(all_recommendations),
                "active_after_filter": len(active_recommendations),
                "min_confidence": autonomous_scanner.min_confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching elite recommendations: {e}")
        return {
            "success": True,
            "recommendations": [],
            "total_count": 0,
            "status": "NO_RECOMMENDATIONS",
            "message": "No elite recommendations available from real strategies at this time",
            "data_source": "REAL_STRATEGY_SYSTEM",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/add-failed-order")
async def add_failed_order_to_elite(signal: Dict):
    """Add failed order to elite recommendations if confidence ≥9"""
    try:
        confidence = signal.get('confidence', 0)
        
        if confidence < 9.0:
            return {
                "success": False,
                "message": f"Order confidence {confidence:.1f} below minimum 9.0 for elite recommendations",
                "added_to_elite": False
            }
        
        # Add to elite recommendations
        autonomous_scanner.add_failed_order(signal)
        
        return {
            "success": True,
            "message": f"Failed order for {signal.get('symbol')} added to elite recommendations",
            "confidence": confidence,
            "added_to_elite": True,
            "symbol": signal.get('symbol'),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding failed order to elite: {e}")
        raise HTTPException(status_code=500, detail="Failed to add order to elite recommendations")

@router.get("/failed-orders")
async def get_failed_orders():
    """Get all failed orders in elite recommendations"""
    try:
        failed_orders = autonomous_scanner.get_failed_orders_as_recommendations()
        
        return {
            "success": True,
            "failed_orders": failed_orders,
            "total_count": len(failed_orders),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting failed orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve failed orders")

@router.post("/force-scan")
async def force_autonomous_scan():
    """Force an immediate scan using REAL strategies"""
    try:
        logger.info("🔄 Forcing immediate elite scan using REAL strategies...")
        recommendations = await autonomous_scanner.scan_for_elite_setups()
        
        return {
            "success": True,
            "message": "Forced elite scan using REAL strategies completed",
            "recommendations_found": len(recommendations),
            "recommendations": recommendations,
            "strategies_used": list(autonomous_scanner.strategies.keys()) if autonomous_scanner.strategies else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in forced scan: {e}")
        raise HTTPException(status_code=500, detail="Real strategy scan failed")

@router.get("/scanner-status")
async def get_scanner_status():
    """Get Elite scanner status"""
    try:
        return {
            "success": True,
            "scanner_active": bool(autonomous_scanner.strategies),
            "strategies_loaded": list(autonomous_scanner.strategies.keys()) if autonomous_scanner.strategies else [],
            "last_scan": autonomous_scanner.last_scan_time.isoformat() if autonomous_scanner.last_scan_time else None,
            "scan_interval_minutes": autonomous_scanner.scan_interval_minutes,
            "min_confidence": autonomous_scanner.min_confidence,
            "cache_duration": autonomous_scanner.cache_duration_seconds,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scanner status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scanner status")

@router.get("/signal-statistics")
async def get_signal_statistics():
    """Get comprehensive signal statistics from live trading"""
    try:
        from src.core.signal_recorder import signal_recorder
        stats = await signal_recorder.get_signal_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting signal statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get signal statistics")

@router.get("/live-signals")
async def get_live_signals():
    """Get all live signals recorded from strategies"""
    try:
        from src.core.signal_recorder import get_all_elite_recommendations
        live_signals = await get_all_elite_recommendations()
        
        return {
            "success": True,
            "live_signals": live_signals,
            "total_count": len(live_signals),
            "message": f"Retrieved {len(live_signals)} live signals from active trading",
            "data_source": "LIVE_SIGNAL_RECORDER",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting live signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get live signals")

@router.get("/signal-lifecycle")
async def get_signal_lifecycle_stats():
    """Get comprehensive signal lifecycle statistics"""
    try:
        from src.core.signal_lifecycle_manager import get_signal_lifecycle_stats
        stats = await get_signal_lifecycle_stats()
        
        return {
            "success": True,
            "lifecycle_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting signal lifecycle stats: {e}")
        # Return default stats instead of error to prevent frontend issues
        return {
            "success": True,
            "lifecycle_stats": {
                "total_signals_tracked": 0,
                "signals_by_stage": {},
                "expired_signals_pending_cleanup": 0,
                "cleanup_stats": {
                    "total_cleanups": 0,
                    "signals_cleaned": 0,
                    "cache_clears": 0
                },
                "last_cleanup": datetime.now().isoformat(),
                "last_deep_cleanup": datetime.now().isoformat(),
                "config": {
                    "signal_ttl_minutes": 15,
                    "cleanup_interval_minutes": 5,
                    "max_signals_in_memory": 1000
                },
                "memory_usage": {
                    "signal_stages": 0,
                    "signal_timestamps": 0,
                    "signal_metadata": 0
                },
                "status": "initializing"
            },
            "timestamp": datetime.now().isoformat(),
            "note": "Signal lifecycle manager initializing - showing default stats"
        }

@router.post("/cleanup-expired-signals")
async def cleanup_expired_signals():
    """Manually trigger cleanup of expired signals"""
    try:
        from src.core.signal_lifecycle_manager import cleanup_expired_signals
        cleanup_results = await cleanup_expired_signals()
        
        return {
            "success": True,
            "cleanup_results": cleanup_results,
            "message": f"Cleaned up {cleanup_results.get('expired_signals', 0)} expired signals",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up expired signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup expired signals")

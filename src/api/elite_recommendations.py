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

router = APIRouter()
logger = logging.getLogger(__name__)

class AutonomousEliteScanner:
    """Scanner that uses the ACTUAL 6 trading strategies - NO CUSTOM CODE"""
    
    def __init__(self):
        self.last_scan_time = None
        self.scan_interval_minutes = 0.5  # Scan every 30 seconds
        self.min_confidence = 0.75  # Minimum confidence for elite recommendations
        self.cached_recommendations = []
        self.cache_duration_seconds = 30
        self.strategies = {}
        
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
                from src.core.orchestrator import get_orchestrator
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

    def convert_signal_to_recommendation(self, signal):
        """Convert real strategy signal to Elite recommendation format"""
        try:
            current_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss')
            target = signal.get('target')
            
            # Only use real strategy signals with proper risk management
            if not stop_loss or not target:
                logger.warning(f"Signal rejected: Missing stop_loss or target for {signal.get('symbol', 'UNKNOWN')}")
                return None
            
            # Calculate risk/reward using strategy's calculations
            risk_percent = abs((current_price - stop_loss) / current_price) * 100
            reward_percent = abs((target - current_price) / current_price) * 100
            risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 3.0
            
            return {
                "recommendation_id": f"ELITE_{signal['symbol']}_{signal['strategy']}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                "symbol": signal['symbol'],
                "direction": "LONG" if signal['action'] == 'BUY' else "SHORT",
                "strategy": f"Real {signal['strategy']}",
                "confidence": round(signal['confidence'] * 100, 1),
                "entry_price": round(current_price, 2),
                "current_price": round(current_price, 2),
                "stop_loss": round(stop_loss, 2),
                "primary_target": round(target, 2),
                "secondary_target": self._calculate_secondary_target(target, current_price, signal['action']),
                "tertiary_target": self._calculate_tertiary_target(target, current_price, signal['action']),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "risk_metrics": {
                    "risk_percent": round(risk_percent, 2),
                    "reward_percent": round(reward_percent, 2),
                    "position_size": 2.0,
                    "risk_calculation": "REAL_STRATEGY_CALCULATION"
                },
                "confluence_factors": [
                    f"Real Strategy: {signal['strategy']}",
                    f"Signal Confidence: {signal['confidence']:.2f}",
                    f"Entry Price: ₹{current_price:,.2f}",
                    f"Risk/Reward: {risk_reward_ratio:.2f}:1",
                    f"Strategy Generated: {signal['metadata'].get('timestamp', 'N/A')}",
                    "Generated by Real Production Trading Strategies"
                ],
                "entry_conditions": [
                    f"Real {signal['strategy']} strategy signal",
                    "Price at strategy-calculated entry level",
                    "Strategy-based risk management parameters",
                    "Market conditions favorable per strategy",
                    "Real strategy risk calculation applied"
                ],
                "timeframe": "5-10 days",
                "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
                "status": "ACTIVE",
                "generated_at": datetime.now().isoformat(),
                "data_source": "REAL_STRATEGY_GENERATED",
                "strategy_metadata": signal.get('metadata', {}),
                "autonomous": True,
                "WARNING": "REAL_STRATEGY_NON_INTRADAY_SIGNAL"
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
        # Get live recorded signals from signal recorder
        from src.core.signal_recorder import get_all_elite_recommendations
        live_recommendations = await get_all_elite_recommendations()
        
        # Use intelligent caching for strategy-based recommendations
        cache_duration_seconds = 30
        
        if autonomous_scanner.last_scan_time is None or \
           (datetime.now() - autonomous_scanner.last_scan_time).total_seconds() > cache_duration_seconds:
            logger.info("🔄 Running fresh elite scan using REAL strategies...")
            strategy_recommendations = await autonomous_scanner.scan_for_elite_setups()
            autonomous_scanner.cached_recommendations = strategy_recommendations
        else:
            logger.info("⚡ Using cached elite recommendations")
            strategy_recommendations = autonomous_scanner.cached_recommendations
        
        # Combine live signals with strategy recommendations
        all_recommendations = live_recommendations + strategy_recommendations
        
        # Filter only ACTIVE recommendations and remove duplicates
        seen_symbols = set()
        active_recommendations = []
        
        for rec in all_recommendations:
            if rec.get('status') in ['ACTIVE', 'GENERATED', 'PENDING_EXECUTION']:
                symbol = rec.get('symbol')
                if symbol not in seen_symbols:
                    active_recommendations.append(rec)
                    seen_symbols.add(symbol)
        
        # Sort by timestamp (newest first)
        active_recommendations.sort(
            key=lambda x: x.get('generated_at', ''), 
            reverse=True
        )
        
        return {
            "success": True,
            "recommendations": active_recommendations,
            "total_count": len(active_recommendations),
            "live_signals": len(live_recommendations),
            "strategy_signals": len(strategy_recommendations),
            "status": "ACTIVE",
            "message": f"Found {len(active_recommendations)} elite recommendations ({len(live_recommendations)} live + {len(strategy_recommendations)} strategy)",
            "data_source": "LIVE_SIGNALS_AND_REAL_STRATEGIES",
            "scan_timestamp": autonomous_scanner.last_scan_time.isoformat() if autonomous_scanner.last_scan_time else datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "next_scan": (datetime.now() + timedelta(minutes=autonomous_scanner.scan_interval_minutes)).isoformat(),
            "strategies_used": list(autonomous_scanner.strategies.keys()) if autonomous_scanner.strategies else [],
            "cache_status": "LIVE_SIGNALS_INTEGRATED"
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
        raise HTTPException(status_code=500, detail="Failed to get signal lifecycle statistics")

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

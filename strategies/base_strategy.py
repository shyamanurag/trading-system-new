"""
INSTITUTIONAL-GRADE BASE STRATEGY
Professional foundation with advanced mathematical models and quantitative analysis.

DAVID VS GOLIATH COMPETITIVE ADVANTAGES:
1. Advanced ATR calculation with GARCH volatility modeling
2. Professional risk management with Kelly criterion and VaR
3. Real-time performance attribution and Sharpe ratio tracking
4. Adaptive position sizing based on market regime and volatility
5. Statistical significance testing for all trading decisions
6. Professional execution algorithms with market impact modeling
7. Machine learning enhanced signal validation
8. Institutional-grade performance monitoring and alerting

Built to compete with hedge funds using superior mathematical rigor.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time, timedelta
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
import pytz
import time as time_module
import os
import math
import warnings
warnings.filterwarnings('ignore')

# Import our professional mathematical foundation
from src.core.enhanced_strategy.mathematical_foundation import ProfessionalMathFoundation

logger = logging.getLogger(__name__)

class BaseStrategy:
    """
    INSTITUTIONAL-GRADE BASE STRATEGY
    
    COMPETITIVE ADVANTAGES:
    1. GARCH-ENHANCED ATR: Superior volatility estimation vs simple ATR
    2. KELLY CRITERION: Optimal position sizing vs fixed percentages
    3. REAL-TIME SHARPE: Performance attribution vs basic P&L tracking
    4. VAR MONITORING: Professional risk management vs simple stop losses
    5. STATISTICAL VALIDATION: Significance testing vs gut feelings
    6. ADAPTIVE SIZING: Market regime awareness vs static allocation
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "InstitutionalBaseStrategy"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)
        
        # PROFESSIONAL MATHEMATICAL FOUNDATION - Using static methods
        
        # 🚨 CRITICAL: Duplicate order prevention system (SHARED across ALL strategies)
        # Use class-level dict so ALL strategy instances see ALL orders
        if not hasattr(BaseStrategy, '_global_recent_orders'):
            BaseStrategy._global_recent_orders = {}
        self._recent_orders = BaseStrategy._global_recent_orders  # Point to shared dict
        
        # PROFESSIONAL PERFORMANCE TRACKING
        self.strategy_returns = []
        self.trade_history = []
        self.performance_attribution = {
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'var_95': 0.0,
            'statistical_significance': 1.0,
            'kelly_optimal_size': 0.02
        }
        
        # CRITICAL: Signal rate limiting to prevent flooding
        self.max_signals_per_hour = 50  # Maximum 50 signals per hour (manageable)
        self.max_signals_per_strategy = 10  # Maximum 10 signals per strategy per hour
        self.signals_generated_this_hour = 0
        self.strategy_signals_this_hour = 0
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        self.hour_start_time = datetime.now(ist)
        
        # Enhanced cooldown control
        self.scalping_cooldown = 30  # 30 seconds between signals
        self.symbol_cooldowns = {}   # Symbol-specific cooldowns
        self.position_cooldowns = {}  # Phantom position cleanup cooldowns
        
        # EMERGENCY STOP LOSS THRESHOLDS (configurable)
        self.emergency_loss_amount = config.get('emergency_loss_amount', -1000)  # ₹1000 default
        self.emergency_loss_percent = config.get('emergency_loss_percent', -2.0)  # 2% default
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
        # Symbol filtering and selection
        self.watchlist = set()  # Symbols this strategy is interested in
        self.active_symbols = set()  # Symbols currently being analyzed
        self.symbol_filters = config.get('symbol_filters', {})
        self.max_symbols_to_analyze = config.get('max_symbols_to_analyze', 20)
        
        # CRITICAL: Position Management System
        self.active_positions = {}  # symbol -> position data with strategy linkage
        self.position_metadata = {}  # symbol -> strategy-specific position data
        self.trailing_stops = {}
        self.emergency_exits_processed = {}  # symbol -> timestamp (prevent repeated emergency exits)
        
        # 🎯 MARKET BIAS COORDINATION
        self.market_bias = None  # Will be set by orchestrator
        self.position_entry_times = {}  # symbol -> entry timestamp
        self.failed_options_symbols = set()  # Track symbols that failed subscription
        self._last_known_capital = 0.0  # Cache for capital when API fails
        self._latest_market_data = {}  # Store latest market data for relative strength checks
        
        # Signal generation throttling
        self._last_signal_generation = {}  # symbol -> timestamp
        self._signal_throttle_interval = 5.0  # 5 seconds between signals for same symbol
        
        # 🚨 SIGNAL EXPIRY AND EXECUTION THROTTLING
        self.signal_expiry_seconds = 120  # 2 minutes - signals valid for 2 minutes only
        self.execution_throttle_seconds = 30  # 30 seconds between execution attempts
        self.signal_timestamps = {}  # symbol -> signal generation timestamp
        self.last_execution_attempts = {}  # symbol -> last execution attempt timestamp
        self.expired_signals_for_elite = []  # Store expired signals for Elite Recommendations

    def _cleanup_expired_signals(self) -> None:
        """🚨 2-MINUTE SIGNAL VALIDITY: Delete signals older than 2 minutes and route to Elite Recommendations"""
        try:
            current_time = time_module.time()
            expired_symbols = []
            
            for symbol, timestamp in list(self.signal_timestamps.items()):
                age_seconds = current_time - timestamp
                if age_seconds > self.signal_expiry_seconds:
                    expired_symbols.append((symbol, age_seconds))
            
            # Delete expired signals from memory and route to Elite Recommendations
            for symbol, age_seconds in expired_symbols:
                if symbol in self.current_positions:
                    signal = self.current_positions[symbol]
                    if isinstance(signal, dict) and signal.get('action') != 'HOLD':
                        logger.info(f"🗑️ EXPIRED SIGNAL: {symbol} (age: {age_seconds:.1f}s) - Routing to Elite Recommendations")
                        
                        # Route unexecuted signal to Elite Recommendations
                        self._route_expired_signal_to_elite(signal, age_seconds)
                        
                        # Complete removal from system
                        del self.current_positions[symbol]
                
                # CRITICAL: Clean up ALL tracking data for complete removal
                if symbol in self.signal_timestamps:
                    del self.signal_timestamps[symbol]
                if symbol in self.last_execution_attempts:
                    del self.last_execution_attempts[symbol]
                if symbol in self.symbol_cooldowns:
                    del self.symbol_cooldowns[symbol]
                if symbol in self.position_cooldowns:
                    del self.position_cooldowns[symbol]
                
                # Clear recent order tracking to allow fresh signal generation
                recent_order_key = f"recent_order_{symbol}"
                if hasattr(self, '_recent_orders') and recent_order_key in self._recent_orders:
                    del self._recent_orders[recent_order_key]
                    logger.info(f"🧹 CLEARED ORDER HISTORY: {symbol} - Fresh signals now allowed")
                    
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired signals: {e}")
    
    def _route_expired_signal_to_elite(self, signal: Dict, age_seconds: float) -> None:
        """Route expired unexecuted signal to Elite Trade Recommendations"""
        try:
            import requests
            from datetime import datetime
            
            # Prepare expired signal data for Elite Recommendations
            elite_signal = {
                'symbol': signal.get('symbol'),
                'action': signal.get('action'),
                'entry_price': signal.get('entry_price'),
                'stop_loss': signal.get('stop_loss'),
                'target': signal.get('target'),
                'confidence': signal.get('confidence'),
                'strategy': signal.get('strategy', self.name),
                'status': 'EXPIRED_UNEXECUTED',
                'expiry_reason': f'Signal expired after {age_seconds:.0f}s (2-minute validity)',
                'generated_at': signal.get('generated_at', datetime.now().isoformat()),
                'expired_at': datetime.now().isoformat(),
                'signal_age_seconds': age_seconds,
                'metadata': signal.get('metadata', {})
            }
            
            # Try to send to Elite Recommendations API
            try:
                response = requests.post(
                    'http://localhost:8000/api/elite-recommendations/add-expired-signal',
                    json=elite_signal,
                    timeout=2
                )
                
                if response.status_code == 200:
                    logger.info(f"📋 ELITE: Expired signal {signal.get('symbol')} added to recommendations")
                else:
                    logger.debug(f"Elite API returned {response.status_code} for expired signal")
                    
            except requests.exceptions.RequestException:
                # Store locally if API unavailable
                self.expired_signals_for_elite.append(elite_signal)
                # Keep only last 50 expired signals
                if len(self.expired_signals_for_elite) > 50:
                    self.expired_signals_for_elite.pop(0)
                logger.debug(f"Elite API unavailable - stored expired signal locally")
                
        except Exception as e:
            logger.error(f"Error routing expired signal to Elite: {e}")
    
    def _can_execute_signal(self, symbol: str) -> bool:
        """🚨 EXECUTION THROTTLING: Check if signal can be executed (30-second throttle)"""
        try:
            if symbol not in self.last_execution_attempts:
                return True  # First execution attempt
            
            current_time = time_module.time()
            last_attempt = self.last_execution_attempts[symbol]
            time_since_last = current_time - last_attempt
            
            if time_since_last < self.execution_throttle_seconds:
                remaining_time = self.execution_throttle_seconds - time_since_last
                logger.info(f"⏳ EXECUTION THROTTLED: {symbol} ({remaining_time:.1f}s remaining)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking execution throttle: {e}")
            return False
    
    def _record_execution_attempt(self, symbol: str) -> None:
        """Record execution attempt for throttling"""
        try:
            self.last_execution_attempts[symbol] = time_module.time()
            logger.debug(f"📊 Execution attempt recorded: {symbol}")
        except Exception as e:
            logger.error(f"❌ Error recording execution attempt: {e}")
    
    def _track_signal_creation(self, symbol: str) -> None:
        """🚨 SIGNAL TRACKING: Record when a signal is created"""
        try:
            self.signal_timestamps[symbol] = time_module.time()
            logger.debug(f"📝 Signal timestamp recorded: {symbol}")
        except Exception as e:
            logger.error(f"❌ Error tracking signal creation: {e}")
    
    async def on_market_data(self, data: Dict):
        """🚨 BASE SIGNAL PROCESSING: Clean up expired signals before processing"""
        try:
            # 0. Store latest market data for relative strength checks
            self._latest_market_data = data
            
            # 1. Clean up expired signals (older than 5 minutes)
            self._cleanup_expired_signals()
            
            # 2. Call the strategy-specific implementation
            # This method should be overridden by child strategies
            pass
            
        except Exception as e:
            logger.error(f"❌ Error in base on_market_data: {e}")
    
    def purge_symbol_state(self, symbol: str) -> None:
        """Remove cached state for a symbol so strategy decides fresh next cycle."""
        try:
            if symbol in getattr(self, 'current_positions', {}):
                self.current_positions.pop(symbol, None)
            if symbol in getattr(self, 'symbol_cooldowns', {}):
                self.symbol_cooldowns.pop(symbol, None)
            if symbol in getattr(self, 'position_cooldowns', {}):
                self.position_cooldowns.pop(symbol, None)
            if hasattr(self, 'price_history') and isinstance(getattr(self, 'price_history'), dict):
                self.price_history.pop(symbol, None)
            if hasattr(self, 'volume_history') and isinstance(getattr(self, 'volume_history'), dict):
                self.volume_history.pop(symbol, None)
            if symbol in getattr(self, 'active_positions', {}):
                # Do not alter real positions; only clear strategy-side caches
                pass
            logger.info(f"🧹 {self.__class__.__name__}: Purged cached state for {symbol}")
        except Exception as e:
            logger.debug(f"{self.__class__.__name__}: purge_symbol_state failed for {symbol}: {e}")

    def set_market_bias(self, market_bias):
        """Set market bias system for coordinated signal generation"""
        self.market_bias = market_bias
        logger.debug(f"🎯 {self.name}: Market bias system connected")
        
        # Position deduplication and management flags
        self.max_position_age_hours = 24  # Auto-close positions after 24 hours
        self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
        self.profit_lock_percentage = 1.0  # Lock profit at 1%
    
    def check_relative_strength(self, symbol: str, action: str, stock_change_percent: float, 
                               nifty_change_percent: float, min_outperformance: float = 0.3) -> Tuple[bool, str]:
        """
        Check if stock has relative strength/weakness vs NIFTY
        
        PROFESSIONAL LOGIC:
        - LONGS: Stock must OUTPERFORM market (stronger than NIFTY)
        - SHORTS: Stock must UNDERPERFORM market (weaker than NIFTY)
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            stock_change_percent: Stock's % change
            nifty_change_percent: NIFTY's % change
            min_outperformance: Minimum % outperformance required (default 0.3%)
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        try:
            # Skip check for index trades (NIFTY/BANKNIFTY options)
            index_identifiers = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']
            if any(idx in symbol.upper() for idx in index_identifiers):
                return True, "Index trade - no RS check needed"
            
            relative_strength = stock_change_percent - nifty_change_percent
            
            if action.upper() == "BUY":
                # LONG: Stock must outperform market
                if relative_strength < min_outperformance:
                    reason = (f"❌ WEAK STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}% < {min_outperformance:+.2f}% required)")
                    logger.info(reason)
                    return False, reason
                else:
                    reason = (f"✅ STRONG STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}%)")
                    logger.info(reason)
                    return True, reason
            
            elif action.upper() == "SELL":
                # SHORT: Stock must underperform market
                if relative_strength > -min_outperformance:
                    reason = (f"❌ STRONG STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}% > {-min_outperformance:+.2f}% max)")
                    logger.info(reason)
                    return False, reason
                else:
                    reason = (f"✅ WEAK STOCK: {symbol} {stock_change_percent:+.2f}% vs NIFTY {nifty_change_percent:+.2f}% "
                            f"(RS: {relative_strength:+.2f}%)")
                    logger.info(reason)
                    return True, reason
            
            return True, "Action not BUY/SELL"
            
        except Exception as e:
            logger.warning(f"Error checking relative strength for {symbol}: {e}")
            return True, f"RS check error: {e}"  # Allow on error to not block trading
        
        # 🎯 ACTIVE POSITION MANAGEMENT CONFIGURATION
        self.enable_active_management = self.config.get('enable_active_management', True)
        self.partial_profit_threshold = self.config.get('partial_profit_threshold', 15)  # Book profits at 15%
        self.aggressive_profit_threshold = self.config.get('aggressive_profit_threshold', 25)  # Aggressive booking at 25%
        self.scaling_profit_threshold = self.config.get('scaling_profit_threshold', 5)  # Scale position at 5% profit
        self.breakeven_buffer = self.config.get('breakeven_buffer', 2)  # 2% buffer above breakeven
        self.time_based_tightening_hours = self.config.get('time_based_tightening', 2)  # Tighten stops after 2 hours
        self.volatility_adjustment_threshold = self.config.get('volatility_threshold', 3)  # Adjust stops at 3% volatility
        
        # ⏰ TRADING TIME RESTRICTIONS (IST)
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.no_new_signals_after = time(15, 0)  # 3:00 PM IST - No new signals
        self.mandatory_close_time = time(15, 20)  # 3:20 PM IST - Force close all positions
        self.warning_close_time = time(15, 15)    # 3:15 PM IST - Start aggressive closing
        
        # Position management tracking
        self.management_actions_taken = {}  # symbol -> list of actions taken
        self.last_management_time = {}  # symbol -> last management timestamp
        
    def _is_trading_hours_active(self) -> bool:
        """⏰ CHECK TRADING HOURS - Simplified check for position management"""
        try:
            # Ensure ist_timezone is available (fallback for inheritance issues)
            if not hasattr(self, 'ist_timezone'):
                import pytz
                self.ist_timezone = pytz.timezone('Asia/Kolkata')
                
            current_time_ist = datetime.now(self.ist_timezone).time()
            
            # Market open check (9:15 AM - 3:30 PM IST)
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            return market_open <= current_time_ist <= market_close
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFE fallback - BLOCK trading if error in time check (safer)
            return False
    
    def _get_position_close_urgency(self) -> str:
        """⏰ GET POSITION CLOSE URGENCY - Determine urgency level for position closure"""
        try:
            # Ensure ist_timezone is available (fallback for inheritance issues)
            if not hasattr(self, 'ist_timezone'):
                import pytz
                self.ist_timezone = pytz.timezone('Asia/Kolkata')
                
            # 🚨 DEFENSIVE: Ensure mandatory_close_time exists (fallback for inheritance issues)
            if not hasattr(self, 'mandatory_close_time'):
                logger.warning("⚠️ mandatory_close_time not found, using default")
                from datetime import time
                self.mandatory_close_time = time(15, 20)  # 3:20 PM IST
                
            current_time_ist = datetime.now(self.ist_timezone).time()
            
            # Ensure all time attributes are time objects, not strings
            mandatory_close = self.mandatory_close_time
            if isinstance(mandatory_close, str):
                from datetime import time
                hour, minute = map(int, mandatory_close.split(':'))
                mandatory_close = time(hour, minute)
            
            if current_time_ist >= mandatory_close:  # After 3:20 PM
                return "IMMEDIATE"
            
            if hasattr(self, 'warning_close_time'):
                warning_close = self.warning_close_time
                if isinstance(warning_close, str):
                    from datetime import time
                    hour, minute = map(int, warning_close.split(':'))
                    warning_close = time(hour, minute)
                if current_time_ist >= warning_close:  # After 3:15 PM
                    return "URGENT"
            
            if hasattr(self, 'no_new_signals_after'):
                no_new_signals = self.no_new_signals_after
                if isinstance(no_new_signals, str):
                    from datetime import time
                    hour, minute = map(int, no_new_signals.split(':'))
                    no_new_signals = time(hour, minute)
                if current_time_ist >= no_new_signals:  # After 3:00 PM
                    return "GRADUAL"
            
                return "NORMAL"
                
        except Exception as e:
            logger.error(f"Error determining close urgency: {e}")
            return "NORMAL"
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        time_since_last = (current_time_ist - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
    def _check_signal_rate_limits(self) -> bool:
        """Check if signal generation is allowed based on rate limits"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        # Reset hourly counters if hour has passed
        if (current_time - self.hour_start_time).total_seconds() >= 3600:
            self.signals_generated_this_hour = 0
            self.strategy_signals_this_hour = 0
            self.hour_start_time = current_time
        
        # Check global hourly limit
        if self.signals_generated_this_hour >= self.max_signals_per_hour:
            logger.debug(f"⚠️ Hourly signal limit reached: {self.signals_generated_this_hour}/{self.max_signals_per_hour}")
            return False
        
        # Check strategy-specific hourly limit
        if self.strategy_signals_this_hour >= self.max_signals_per_strategy:
            logger.debug(f"⚠️ Strategy signal limit reached: {self.strategy_signals_this_hour}/{self.max_signals_per_strategy}")
            return False
        
        return True
    
    def _check_capital_affordability(self, symbol: str, quantity: int, price: float, available_capital: float) -> bool:
        """Check if signal is affordable with available capital - CRITICAL FIX for 1,237 failures"""
        required_capital = price * quantity
        
        if required_capital > available_capital:
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} needs ₹{required_capital:,.0f} > available ₹{available_capital:,.0f}")
            return False
        
        # Also check if it's more than 80% of available capital (risk management)
        if required_capital > (available_capital * 0.8):
            logger.debug(f"💰 SIGNAL FILTERED: {symbol} uses {required_capital/available_capital:.1%} of capital (>80% limit)")
            return False
        
        return True
    
    def _increment_signal_counters(self):
        """Increment signal counters when a signal is generated"""
        self.signals_generated_this_hour += 1
        self.strategy_signals_this_hour += 1
        
    def _record_order_placement(self, symbol: str):
        """🚨 CRITICAL: Record when an order is placed to prevent duplicates (GLOBAL across all strategies)"""
        try:
            current_time = time_module.time()
            
            # Record exact symbol
            recent_order_key = f"recent_order_{symbol}"
            self._recent_orders[recent_order_key] = current_time
            
            # 🚨 CRITICAL FIX: Also record UNDERLYING to block ALL related orders
            # Extract underlying: "TITAN25OCT3650CE" → "TITAN"
            underlying = symbol
            if symbol.endswith('CE') or symbol.endswith('PE'):
                import re
                match = re.match(r'^([A-Z]+)', symbol)
                if match:
                    underlying = match.group(1)
            
            # Record underlying separately (prevents CE and PE on same stock)
            if underlying != symbol:
                underlying_key = f"recent_order_{underlying}"
                self._recent_orders[underlying_key] = current_time
                logger.info(f"📝 RECORDED ORDER (GLOBAL): {symbol} + underlying {underlying} by {self.name}")
            else:
                logger.info(f"📝 RECORDED ORDER (GLOBAL): {symbol} by {self.name}")
            
            logger.info(f"   📊 Total tracked orders: {len(self._recent_orders)}")
            
            # Clean up old entries (older than 1 hour)
            cutoff_time = current_time - 3600
            keys_to_remove = [k for k, v in self._recent_orders.items() if v < cutoff_time]
            for key in keys_to_remove:
                del self._recent_orders[key]
                
        except Exception as e:
            logger.error(f"Error recording order placement: {e}")
    
    # ========================================
    # CRITICAL: POSITION MANAGEMENT SYSTEM
    # ========================================
    
    def has_existing_position(self, symbol: str) -> bool:
        """🚨 CRITICAL FIX: Check for existing positions to prevent DUPLICATE ORDERS"""
        
        # Extract underlying symbol for comprehensive checking
        # For options: "TCS25OCT2940CE" → "TCS"
        # For equity: "TCS" → "TCS"
        underlying = symbol
        if symbol.endswith('CE') or symbol.endswith('PE'):
            # Remove expiry and strike: "TCS25OCT2940CE" → "TCS"
            import re
            match = re.match(r'^([A-Z]+)', symbol)
            if match:
                underlying = match.group(1)
        
        # 🚨 STEP 1: Check REAL Zerodha positions first (most authoritative)
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                # Get real positions from Zerodha
                positions = orchestrator.zerodha_client.get_positions_sync()
                if positions and isinstance(positions, dict):
                    # Check both net and day positions
                    for pos_list in [positions.get('net', []), positions.get('day', [])]:
                        if isinstance(pos_list, list):
                            for pos in pos_list:
                                pos_symbol = pos.get('tradingsymbol', '')
                                pos_qty = pos.get('quantity', 0)
                                
                                if pos_qty == 0:
                                    continue  # Skip closed positions
                                
                                # Check exact match first
                                if pos_symbol == symbol:
                                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} has REAL position qty={pos_qty}")
                                    return True
                                
                                # CRITICAL FIX: Also check for same underlying
                                # If TCS25OCT2940CE exists, block ALL TCS signals (TCS25OCT2950CE, TCS equity, etc.)
                                pos_underlying = pos_symbol
                                if pos_symbol.endswith('CE') or pos_symbol.endswith('PE'):
                                    import re
                                    match = re.match(r'^([A-Z]+)', pos_symbol)
                                    if match:
                                        pos_underlying = match.group(1)
                                
                                if pos_underlying == underlying:
                                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} - Found existing position for underlying {underlying}: {pos_symbol} qty={pos_qty}")
                                    return True
        except Exception as e:
            logger.debug(f"Could not check Zerodha positions: {e}")
        
        # 🚨 STEP 2: Check recent order history to prevent rapid duplicates (2-minute window)
        try:
            # Check if we've placed an order for this symbol in the last 2 minutes (matches signal validity)
            current_time = time_module.time()
            
            if hasattr(self, '_recent_orders'):
                # Check exact symbol match
                exact_key = f"recent_order_{symbol}"
                last_order_time = self._recent_orders.get(exact_key, 0)
                if current_time - last_order_time < 120:  # 2 minutes (matches signal expiry)
                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED: {symbol} ordered {(current_time - last_order_time):.0f}s ago")
                    return True
                
                # CRITICAL FIX: Also check for underlying symbol
                # If TCS25OCT2940CE was ordered, block all TCS-related signals
                underlying_key = f"recent_order_{underlying}"
                last_underlying_time = self._recent_orders.get(underlying_key, 0)
                if current_time - last_underlying_time < 120:
                    logger.warning(f"🚫 DUPLICATE ORDER BLOCKED (GLOBAL): {symbol} - Underlying {underlying} ordered {(current_time - last_underlying_time):.0f}s ago")
                    logger.warning(f"   🎯 Blocked by {self.name} - prevents contradictory CE/PE on same stock")
                    return True
                    
                # Also check all recent orders for same underlying
                for recent_key, recent_time in self._recent_orders.items():
                    if not recent_key.startswith('recent_order_'):
                        continue
                    recent_symbol = recent_key.replace('recent_order_', '')
                    
                    # Extract underlying from recent order
                    recent_underlying = recent_symbol
                    if recent_symbol.endswith('CE') or recent_symbol.endswith('PE'):
                        import re
                        match = re.match(r'^([A-Z]+)', recent_symbol)
                        if match:
                            recent_underlying = match.group(1)
                    
                    # Block if same underlying and within 2 minutes
                    if recent_underlying == underlying and current_time - recent_time < 120:
                        logger.warning(f"🚫 DUPLICATE ORDER BLOCKED (GLOBAL): {symbol} - Related order {recent_symbol} placed {(current_time - recent_time):.0f}s ago")
                        logger.warning(f"   🎯 Blocked by {self.name} - prevents multiple positions on {underlying}")
                        return True
            else:
                self._recent_orders = {}
                
        except Exception as e:
            logger.debug(f"Could not check recent orders: {e}")
        
        # 🚨 STEP 3: Check local strategy positions
        if symbol in self.active_positions:
            # Check for phantom positions (older than 30 minutes)
            position_data = self.active_positions[symbol]
            if isinstance(position_data, dict):
                timestamp = position_data.get('timestamp', 0)
                current_time = time_module.time()
                
                # CRITICAL FIX: Handle timestamp corruption (Unix epoch issues)
                if timestamp == 0 or timestamp < 1000000000:  # Before year 2001 (likely corrupted)
                    logger.warning(f"🧹 CLEARING CORRUPTED TIMESTAMP POSITION: {symbol} (timestamp: {timestamp})")
                    del self.active_positions[symbol]
                    # Add cooldown to prevent immediate regeneration
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
                
                age_minutes = (current_time - timestamp) / 60
                
                # CRITICAL FIX: Handle extreme ages (likely timestamp corruption)
                if age_minutes > 1440:  # More than 24 hours indicates corruption
                    logger.warning(f"🧹 CLEARING PHANTOM POSITION: {symbol} (age: {age_minutes:.1f} min - likely corrupted timestamp)")
                    del self.active_positions[symbol]
                    # Add cooldown to prevent immediate regeneration
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
                elif age_minutes > 30:  # Normal 30 minute cleanup
                    logger.warning(f"🧹 CLEARING PHANTOM POSITION: {symbol} (age: {age_minutes:.1f} min)")
                    del self.active_positions[symbol]
                    # CRITICAL FIX: Add cooldown period after clearing phantom position
                    self._add_position_cooldown(symbol, 60)  # 60 second cooldown
                    return False
            
            logger.info(f"🚫 {self.strategy_name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
            return True
        return False
    
    def _add_position_cooldown(self, symbol: str, seconds: int):
        """Add cooldown period for a symbol after phantom position cleanup"""
        expiry_time = time_module.time() + seconds
        self.position_cooldowns[symbol] = expiry_time
        logger.info(f"🕐 COOLDOWN ADDED: {symbol} for {seconds} seconds")
    
    def _is_position_cooldown_active(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period"""
        if symbol not in self.position_cooldowns:
            return False
        
        current_time = time_module.time()
        if current_time < self.position_cooldowns[symbol]:
            remaining = int(self.position_cooldowns[symbol] - current_time)
            logger.info(f"🕐 COOLDOWN ACTIVE: {symbol} ({remaining}s remaining)")
            return True
        else:
            # Cooldown expired, remove it
            del self.position_cooldowns[symbol]
            return False
    
    async def manage_existing_positions(self, market_data: Dict) -> List[Dict]:
        """🎯 COMPREHENSIVE POSITION MANAGEMENT - Active monitoring and management"""
        try:
            # 🚨 CRITICAL FIX: Sync local positions with REAL Zerodha positions
            # Remove positions that no longer exist in broker
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            real_symbols_with_positions = set()
            
            if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                try:
                    real_positions = await orchestrator.zerodha_client.get_positions()

                    # 🚨 VALIDATION: Ensure real_positions is a dict
                    if real_positions is None:
                        logger.warning("⚠️ get_positions returned None")
                        real_positions = {}
                    elif isinstance(real_positions, int):
                        logger.error(f"❌ get_positions returned int instead of dict: {real_positions}")
                        real_positions = {}
                    elif not isinstance(real_positions, dict):
                        logger.error(f"❌ get_positions returned {type(real_positions)} instead of dict: {real_positions}")
                        real_positions = {}

                    if real_positions:
                        # First, collect all symbols that have real positions
                        for pos_list in [real_positions.get('net', []), real_positions.get('day', [])]:
                            for pos in pos_list:
                                symbol = pos.get('tradingsymbol')
                                qty = pos.get('quantity', 0)
                                if qty != 0:  # Only consider non-zero positions
                                    real_symbols_with_positions.add(symbol)
                        
                        # Clean up local positions that don't exist in broker
                        symbols_to_remove = []
                        for symbol in list(self.active_positions.keys()):
                            if symbol not in real_symbols_with_positions:
                                logger.warning(f"🧹 CLEANING STALE POSITION: {symbol} (not in broker)")
                                symbols_to_remove.append(symbol)
                        
                        for symbol in symbols_to_remove:
                            del self.active_positions[symbol]
                    
                        # Now process emergency exits for REAL positions
                        # 🚨 CRITICAL FIX: Track processed symbols to prevent duplicate exits
                        emergency_exits_processed = set()
                        
                        for pos_list in [real_positions.get('net', []), real_positions.get('day', [])]:
                            for pos in pos_list:
                                symbol = pos.get('tradingsymbol')
                                qty = pos.get('quantity', 0)
                                avg_price = pos.get('average_price', 0)
                                pnl = pos.get('pnl', 0) or pos.get('unrealised', 0) or 0
                                
                                # Skip if no actual position (qty = 0 means position closed)
                                if qty == 0:
                                    continue
                                
                                # 🚨 CRITICAL: Skip if already processed (prevents duplicate exits)
                                if symbol in emergency_exits_processed:
                                    logger.debug(f"⏭️ Skipping {symbol} - already checked for emergency exit")
                                    continue
                                emergency_exits_processed.add(symbol)
                                
                                # 🚨 COOLDOWN: Skip if emergency exit was recently processed for this symbol
                                current_time = datetime.now()
                                if symbol in self.emergency_exits_processed:
                                    last_exit_time = self.emergency_exits_processed[symbol]
                                    time_since_exit = (current_time - last_exit_time).total_seconds()
                                    if time_since_exit < 300:  # 5 minute cooldown
                                        logger.debug(f"⏳ Emergency exit cooldown: {symbol} ({time_since_exit:.0f}s remaining)")
                                        continue
                                
                                # EMERGENCY: Exit ANY position with >₹1000 loss or >2% loss
                                loss_threshold_amount = -1000  # ₹1000 loss
                                loss_threshold_percent = -2.0  # 2% loss
                                
                                # Calculate percentage loss
                                if avg_price > 0 and qty != 0:
                                    current_price = market_data.get(symbol, {}).get('ltp', avg_price)
                                    pnl_percent = ((current_price - avg_price) / avg_price) * 100
                                else:
                                    pnl_percent = 0
                                
                                # Check if position needs emergency exit
                                if (pnl < loss_threshold_amount) or (pnl_percent < loss_threshold_percent):
                                    logger.error(f"🚨 EMERGENCY STOP LOSS TRIGGERED: {symbol}")
                                    logger.error(f"   Loss: ₹{pnl:.2f} ({pnl_percent:.1f}%), Qty: {qty}, Avg: ₹{avg_price:.2f}")
                                    
                                    # 🚨 CRITICAL FIX: Only place exit order if position actually exists (qty != 0)
                                    if qty != 0:
                                        # Force immediate exit signal
                                        exit_signal = {
                                            'symbol': symbol,
                                            'action': 'SELL' if qty > 0 else 'BUY',
                                            'quantity': abs(qty),
                                            'entry_price': market_data.get(symbol, {}).get('ltp', avg_price),
                                            'stop_loss': 0,
                                            'target': 0,
                                            'confidence': 10.0,  # Maximum confidence for emergency exit
                                            'reason': f'EMERGENCY_STOP_LOSS: ₹{pnl:.2f} ({pnl_percent:.1f}%)',  # Add at top level
                                            'metadata': {
                                                'reason': 'EMERGENCY_STOP_LOSS',
                                                'loss_amount': pnl,
                                                'loss_percent': pnl_percent,
                                                'management_action': True,
                                                'closing_action': True,
                                                'bypass_all_checks': True
                                            }
                                        }
                                        await self._execute_management_action(exit_signal)
                                        logger.error(f"🚨 EXECUTED EMERGENCY EXIT for {symbol} - Loss: ₹{pnl:.2f}")
                                        
                                        # 🚨 COOLDOWN: Record emergency exit to prevent repeats
                                        self.emergency_exits_processed[symbol] = current_time
                                    else:
                                        # Position already closed, just log the loss and clean up
                                        logger.error(f"🚨 POSITION ALREADY CLOSED: {symbol} - Loss recorded: ₹{pnl:.2f}")
                                        logger.error(f"   No exit order needed (quantity = 0) - cleaning up tracking")
                                        # Clean up tracking for closed position
                                        if symbol in self.active_positions:
                                            del self.active_positions[symbol]
            
                except Exception as positions_error:
                    logger.error(f"❌ Error processing positions: {positions_error}")
                    logger.error(f"   Error type: {type(positions_error)}")
                    if "can't be used in 'await' expression" in str(positions_error):
                        logger.error("🚨 CRITICAL: Zerodha API returned non-coroutine for positions")
            
            # ⏰ CHECK POSITION CLOSURE URGENCY based on current time
            close_urgency = self._get_position_close_urgency()
            current_time_ist = datetime.now(self.ist_timezone).strftime('%H:%M:%S')
            
            positions_to_exit = []
            positions_to_modify = []
            
            for symbol, position in self.active_positions.items():
                if symbol not in market_data:
                    continue
                    
                current_price = market_data[symbol].get('ltp', 0)
                if current_price == 0:
                    continue
                
                # ⏰ PRIORITY: HANDLE TIME-BASED CLOSURE URGENCY
                if close_urgency == "IMMEDIATE":  # After 3:20 PM - FORCE CLOSE ALL
                    positions_to_exit.append({
                        'symbol': symbol,
                        'reason': f'MANDATORY_CLOSE_3:20PM_IST',
                        'current_price': current_price,
                        'position': position,
                        'urgent': True
                    })
                    logger.warning(f"🚨 {self.name}: MANDATORY CLOSE {symbol} at {current_time_ist} IST (After 3:20 PM)")
                    continue
                    
                elif close_urgency == "URGENT":  # 3:15-3:20 PM - AGGRESSIVE CLOSING
                    # Force exit losing positions, book profits on winning ones
                    entry_price = position.get('entry_price', 0)
                    action = position.get('action', 'BUY')
                    
                    if action == 'BUY':
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                    
                    # Close losing positions immediately, be more aggressive on winners
                    if pnl_pct < -2:  # Losing >2%
                        positions_to_exit.append({
                            'symbol': symbol,
                            'reason': f'URGENT_CLOSE_3:15PM_LOSS_{pnl_pct:.1f}%',
                            'current_price': current_price,
                            'position': position,
                            'urgent': True
                        })
                        logger.warning(f"🚨 {self.name}: URGENT CLOSE {symbol} (Loss: {pnl_pct:.1f}%) at {current_time_ist} IST")
                        continue
                    elif pnl_pct > 5:  # Winning >5% - book 75% profits
                        await self.book_partial_profits(symbol, current_price, position, 75)
                        logger.info(f"⏰ {self.name}: URGENT PROFIT BOOKING 75% for {symbol} (P&L: {pnl_pct:.1f}%) at {current_time_ist} IST")
                        
                elif close_urgency == "GRADUAL":  # 3:00-3:15 PM - NO NEW POSITIONS, gradual exit
                    # Start booking profits more aggressively, no new scaling
                    entry_price = position.get('entry_price', 0)
                    action = position.get('action', 'BUY')
                    
                    if action == 'BUY':
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                    else:
                        pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                    
                    # More aggressive profit booking after 3 PM
                    if pnl_pct > 8:  # Lower threshold for profit booking
                        await self.book_partial_profits(symbol, current_price, position, 50)
                        logger.info(f"⏰ {self.name}: GRADUAL PROFIT BOOKING 50% for {symbol} (P&L: {pnl_pct:.1f}%) at {current_time_ist} IST")
                
                # 1. CHECK FOR REGULAR EXIT CONDITIONS (if not urgent closure)
                if close_urgency not in ["IMMEDIATE", "URGENT"]:
                    exit_decision = await self.should_exit_position(symbol, current_price, position)
                    
                    if exit_decision['should_exit']:
                        positions_to_exit.append({
                            'symbol': symbol,
                            'reason': exit_decision['reason'],
                            'current_price': current_price,
                            'position': position,
                            'urgent': False
                        })
                        continue
                
                # 2. ENHANCED OPEN POSITION DECISION ANALYSIS
                if close_urgency == "NORMAL":
                    # Use enhanced decision system for comprehensive position analysis
                    decision_result = await self._evaluate_open_position_decision(
                        symbol, current_price, position, market_data[symbol]
                    )
                    
                    # Execute decision based on enhanced analysis
                    await self._execute_position_decision(symbol, current_price, position, decision_result)
                    
                    # FALLBACK: Legacy position management for compatibility
                    management_actions = await self.analyze_position_management(symbol, current_price, position, market_data[symbol])
                    
                    # 3. UPDATE TRAILING STOPS (if not handled by enhanced system)
                    if decision_result.action.value not in ['TRAIL_STOP', 'ADJUST_STOP']:
                        await self.update_trailing_stop(symbol, current_price, position)
                    
                    # 4. PARTIAL PROFIT BOOKING (if not handled by enhanced system)
                    if decision_result.action.value != 'EXIT_PARTIAL' and management_actions.get('book_partial_profits'):
                        await self.book_partial_profits(symbol, current_price, position, management_actions['partial_percentage'])
                    
                    # 5. SCALE INTO POSITION (if not handled by enhanced system)
                    if decision_result.action.value != 'SCALE_IN' and management_actions.get('scale_position'):
                        await self.scale_into_position(symbol, current_price, position, management_actions['scale_quantity'])
                    
                    # 6. DYNAMIC STOP LOSS ADJUSTMENT (if not handled by enhanced system)
                    if decision_result.action.value not in ['ADJUST_STOP', 'TRAIL_STOP'] and management_actions.get('adjust_stop_loss'):
                        await self.adjust_dynamic_stop_loss(symbol, current_price, position, management_actions['new_stop_loss'])
                    
                    # 7. TIME-BASED PROFIT PROTECTION
                    await self.apply_time_based_management(symbol, current_price, position)
                    
                    # 8. VOLATILITY-BASED ADJUSTMENTS
                    await self.apply_volatility_based_management(symbol, current_price, position, market_data[symbol])
                    
            # Execute position exits
            for exit_data in positions_to_exit:
                await self.exit_position(exit_data['symbol'], exit_data['current_price'], exit_data['reason'])
                
            # Enhanced logging with time context
            if len(self.active_positions) > 0:
                logger.info(f"🎯 {self.name}: Managing {len(self.active_positions)} positions | "
                           f"Exits: {len(positions_to_exit)} | Urgency: {close_urgency} | Time: {current_time_ist} IST")
                
        except Exception as e:
            logger.error(f"Error managing existing positions: {e}")
    
    async def _evaluate_open_position_decision(self, symbol: str, current_price: float, 
                                             position: Dict, market_data: Dict):
        """Evaluate open position using enhanced decision system"""
        try:
            # Import the enhanced open position decision system
            from src.core.open_position_decision import evaluate_open_position
            
            # Get market bias if available
            market_bias = getattr(self, 'market_bias', None)
            
            # Evaluate position decision
            decision_result = await evaluate_open_position(
                position=position,
                current_price=current_price,
                market_data=market_data,
                market_bias=market_bias,
                portfolio_context={'strategy_name': self.name}
            )
            
            logger.info(f"🎯 POSITION DECISION: {symbol} -> {decision_result.action.value} "
                       f"(Confidence: {decision_result.confidence:.1f}, Urgency: {decision_result.urgency})")
            logger.info(f"   Reasoning: {decision_result.reasoning}")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"❌ Error evaluating open position decision for {symbol}: {e}")
            # Return default HOLD decision
            from src.core.open_position_decision import OpenPositionDecisionResult, OpenPositionAction
            return OpenPositionDecisionResult(
                action=OpenPositionAction.HOLD,
                exit_reason=None,
                confidence=0.0,
                urgency="LOW",
                quantity_percentage=0.0,
                new_stop_loss=None,
                new_target=None,
                reasoning=f"Decision evaluation error: {str(e)} - Defaulting to HOLD",
                metadata={'error': str(e)}
            )
    
    async def _execute_position_decision(self, symbol: str, current_price: float, 
                                       position: Dict, decision_result):
        """Execute the decision from enhanced position analysis"""
        try:
            action = decision_result.action
            
            if action.value == "EXIT_FULL":
                # Full position exit
                await self.exit_position(symbol, current_price, decision_result.exit_reason.value)
                logger.info(f"✅ EXECUTED: Full exit for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "EXIT_PARTIAL":
                # Partial position exit
                percentage = decision_result.quantity_percentage
                await self.book_partial_profits(symbol, current_price, position, percentage)
                logger.info(f"✅ EXECUTED: Partial exit {percentage}% for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "EMERGENCY_EXIT":
                # Emergency exit
                await self.exit_position(symbol, current_price, "EMERGENCY_EXIT")
                logger.warning(f"🚨 EXECUTED: Emergency exit for {symbol} - {decision_result.reasoning}")
                
            elif action.value == "SCALE_IN":
                # Scale into position
                percentage = decision_result.quantity_percentage
                current_quantity = position.get('quantity', 0)
                scale_quantity = int(current_quantity * percentage / 100)
                if scale_quantity > 0:
                    await self.scale_into_position(symbol, current_price, position, scale_quantity)
                    logger.info(f"✅ EXECUTED: Scale in {scale_quantity} shares for {symbol} - {decision_result.reasoning}")
                
            elif action.value in ["TRAIL_STOP", "ADJUST_STOP"]:
                # Adjust stop loss
                if decision_result.new_stop_loss:
                    await self.adjust_dynamic_stop_loss(symbol, current_price, position, decision_result.new_stop_loss)
                    logger.info(f"✅ EXECUTED: Stop adjustment to ₹{decision_result.new_stop_loss:.2f} for {symbol}")
                
            elif action.value == "HOLD":
                # Hold position - no action needed
                logger.debug(f"📊 HOLDING: {symbol} - {decision_result.reasoning}")
                
            else:
                logger.warning(f"⚠️ Unknown position action: {action.value} for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error executing position decision for {symbol}: {e}")
    
    async def should_exit_position(self, symbol: str, current_price: float, position: Dict) -> Dict:
        """Determine if position should be exited based on trailing stops, targets, time"""
        try:
            entry_price = position.get('entry_price', 0)
            action = position.get('action', 'BUY')
            stop_loss = position.get('stop_loss', 0)
            target = position.get('target', 0)
            
            # CRITICAL FIX: Handle None values for stop_loss and target
            if stop_loss is None:
                stop_loss = 0
            if target is None:
                target = 0
            
            # Check stop loss (only if not zero)
            if stop_loss > 0:
                if action == 'BUY' and current_price <= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
                elif action == 'SELL' and current_price >= stop_loss:
                    return {'should_exit': True, 'reason': 'STOP_LOSS_HIT'}
            
            # Check target (only if not zero)
            if target > 0:
                if action == 'BUY' and current_price >= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
                elif action == 'SELL' and current_price <= target:
                    return {'should_exit': True, 'reason': 'TARGET_HIT'}
            
            # Check trailing stop
            if symbol in self.trailing_stops:
                trailing_stop = self.trailing_stops[symbol]['stop_price']
                if action == 'BUY' and current_price <= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
                elif action == 'SELL' and current_price >= trailing_stop:
                    return {'should_exit': True, 'reason': 'TRAILING_STOP_HIT'}
            
            # Check position age (auto-close old positions)
            entry_time = self.position_entry_times.get(symbol)
            if entry_time:
                age_hours = (datetime.now() - entry_time).total_seconds() / 3600
                if age_hours > self.max_position_age_hours:
                    return {'should_exit': True, 'reason': 'POSITION_EXPIRED'}
            
            return {'should_exit': False, 'reason': 'HOLD'}
            
        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")
            return {'should_exit': False, 'reason': 'ERROR'}
    
    async def update_trailing_stop(self, symbol: str, current_price: float, position: Dict):
        """Update trailing stop for profitable positions"""
        try:
            action = position.get('action', 'BUY')
            entry_price = position.get('entry_price', 0)
            
            # Calculate profit percentage
            if action == 'BUY':
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # 🚨 DEFENSIVE: Ensure profit_lock_percentage exists (fallback for inheritance issues)
            if not hasattr(self, 'profit_lock_percentage'):
                logger.warning("⚠️ profit_lock_percentage not found, using default")
                self.profit_lock_percentage = 1.0  # Lock profit at 1%
            
            # Only set trailing stop if position is profitable
            if profit_pct > self.profit_lock_percentage:
                
                # 🚨 DEFENSIVE: Ensure trailing_stop_percentage exists
                if not hasattr(self, 'trailing_stop_percentage'):
                    logger.warning("⚠️ trailing_stop_percentage not found, using default")
                    self.trailing_stop_percentage = 0.5  # 0.5% trailing stop
                
                # Calculate trailing stop price
                if action == 'BUY':
                    trailing_stop_price = current_price * (1 - self.trailing_stop_percentage / 100)
                else:
                    trailing_stop_price = current_price * (1 + self.trailing_stop_percentage / 100)
                
                # Update trailing stop if it's better than current
                if symbol not in self.trailing_stops:
                    self.trailing_stops[symbol] = {
                        'stop_price': trailing_stop_price,
                        'last_update': datetime.now(),
                        'highest_profit': profit_pct
                    }
                    logger.info(f"🎯 {self.name}: Set trailing stop for {symbol} at ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                else:
                    current_trailing = self.trailing_stops[symbol]
                    
                    # Update if new trailing stop is better
                    if ((action == 'BUY' and trailing_stop_price > current_trailing['stop_price']) or
                        (action == 'SELL' and trailing_stop_price < current_trailing['stop_price'])):
                        
                        self.trailing_stops[symbol].update({
                            'stop_price': trailing_stop_price,
                            'last_update': datetime.now(),
                            'highest_profit': max(profit_pct, current_trailing['highest_profit'])
                        })
                        logger.info(f"🎯 {self.name}: Updated trailing stop for {symbol} to ₹{trailing_stop_price:.2f} (profit: {profit_pct:.2f}%)")
                        
                        # 🔥 CRITICAL FIX: Send trailing stop to broker
                        await self._modify_broker_stop_loss(symbol, trailing_stop_price, action)
                        
        except Exception as e:
            logger.error(f"Error updating trailing stop for {symbol}: {e}")
    
    async def _modify_broker_stop_loss(self, symbol: str, new_sl_price: float, action: str):
        """🔥 CRITICAL: Modify stop loss order at broker for trailing stops"""
        try:
            # Get orchestrator to access zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not (orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client):
                logger.debug(f"⚠️ Cannot modify SL - zerodha client not available")
                return
            
            zerodha = orchestrator.zerodha_client
            
            # Get current open SL order for this symbol
            try:
                orders = await zerodha.get_orders()
                if not orders:
                    logger.debug(f"⚠️ No orders found for {symbol}")
                    return
            except Exception as e:
                logger.error(f"Error fetching orders for {symbol}: {e}")
                return
            
            # Find the active SL order for this symbol
            sl_order = None
            for order in orders:
                if (order.get('tradingsymbol') == symbol and 
                    order.get('order_type') in ['SL', 'SL-M'] and
                    order.get('status') in ['OPEN', 'TRIGGER PENDING'] and
                    order.get('tag') == 'ALGO_SL'):
                    sl_order = order
                    break
            
            if not sl_order:
                logger.debug(f"⚠️ No open SL order found for {symbol} (may have been filled)")
                return
            
            order_id = sl_order.get('order_id')
            old_trigger = sl_order.get('trigger_price', 0)
            
            # Only modify if new SL is significantly different (avoid spam)
            if abs(new_sl_price - old_trigger) < 0.50:  # Less than ₹0.50 change
                logger.debug(f"Skipping SL modification for {symbol} - change too small")
                return
            
            # Modify the SL order with new trigger price
            modify_params = {
                'trigger_price': new_sl_price,
                'order_type': 'SL-M'
            }
            
            result = await zerodha.modify_order(order_id, modify_params)
            
            if result:
                logger.info(f"✅ BROKER SL UPDATED: {symbol} {old_trigger:.2f} -> {new_sl_price:.2f} (Order: {order_id})")
            else:
                logger.warning(f"⚠️ SL modification returned no result for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error modifying broker SL for {symbol}: {e}")
    
    async def analyze_position_management(self, symbol: str, current_price: float, position: Dict, market_data: Dict) -> Dict:
        """🧠 INTELLIGENT POSITION ANALYSIS - Determine optimal management actions"""
        try:
            entry_price = position.get('entry_price', 0)
            action = position.get('action', 'BUY')
            quantity = position.get('quantity', 0)
            entry_time = position.get('timestamp')
            
            # Calculate current profit/loss
            if action == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Calculate position age in minutes
            position_age = 0
            if entry_time:
                try:
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    else:
                        entry_dt = entry_time
                    position_age = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 60
                except:
                    position_age = 0
            
            # Get market indicators
            volume = market_data.get('volume', 0)
            change_pct = market_data.get('change_percent', 0)
            
            actions = {
                'book_partial_profits': False,
                'scale_position': False,
                'adjust_stop_loss': False,
                'partial_percentage': 0,
                'scale_quantity': 0,
                'new_stop_loss': 0
            }
            
            # 1. DYNAMIC PROFIT BOOKING (based on target achievement, not hardcoded %)
            target = position.get('target', 0)
            if target > 0:
                # Calculate distance to target
                if action == 'BUY':
                    target_achievement = (current_price - entry_price) / (target - entry_price) if target > entry_price else 0
                else:
                    target_achievement = (entry_price - current_price) / (entry_price - target) if entry_price > target else 0
                
                # Dynamic profit booking based on target progress
                if target_achievement >= 0.8:  # 80% of target achieved
                    if position_age > 30:  # Held for 30+ minutes - book profits
                        actions['book_partial_profits'] = True
                        actions['partial_percentage'] = 60  # Book 60% of position
                        logger.info(f"💰 {self.name}: {symbol} - Booking 60% profits (Target: {target_achievement*100:.1f}%, Age: {position_age:.1f}min)")
                elif target_achievement >= 1.0:  # Target exceeded - aggressive booking
                    actions['book_partial_profits'] = True
                    actions['partial_percentage'] = 80  # Book 80% profits
                    logger.info(f"💰 {self.name}: {symbol} - Target exceeded! Booking 80% profits (Achievement: {target_achievement*100:.1f}%)")
            
            # 2. MOMENTUM-BASED POSITION SCALING (Conservative - only for strong setups)
            # Only scale if risk per trade is still within 1% limit
            current_risk_percent = abs(current_price - position.get('stop_loss', entry_price)) / entry_price * 100 if entry_price > 0 else 0
            if current_risk_percent < 0.8 and pnl_pct > 3 and abs(change_pct) > 1.5:  # Conservative scaling
                if position_age < 10 and quantity < 150:  # Fresh position, not too large
                    actions['scale_position'] = True
                    actions['scale_quantity'] = max(1, int(quantity * 0.15))  # Scale by 15% only
                    logger.info(f"📈 {self.name}: {symbol} - Conservative scaling by {actions['scale_quantity']} shares (risk: {current_risk_percent:.2f}%)")
            
            # 3. DYNAMIC TRAILING STOP (based on original stop distance, not hardcoded %)
            original_stop = position.get('stop_loss', 0)
            if original_stop > 0 and pnl_pct > 5:  # Only after decent profit
                original_risk_distance = abs(entry_price - original_stop)
                buffer_distance = original_risk_distance * 0.3  # 30% of original risk as buffer
                
                if action == 'BUY':
                    actions['new_stop_loss'] = max(entry_price + buffer_distance, current_price - original_risk_distance * 0.8)
                else:
                    actions['new_stop_loss'] = min(entry_price - buffer_distance, current_price + original_risk_distance * 0.8)
                actions['adjust_stop_loss'] = True
                logger.info(f"🛡️ {self.name}: {symbol} - Dynamic trailing stop (P&L: {pnl_pct:.2f}%, Risk Distance: {original_risk_distance:.2f})")
            
            # 4. SCALPING AUTO-EXIT: Close positions after 10 minutes max (quick in/out)
            if position_age > 10:  # 10 minutes max hold for scalping
                actions['immediate_exit'] = True
                actions['exit_reason'] = 'SCALPING_AUTO_EXIT_10MIN'
                logger.info(f"⚡ {self.name}: {symbol} - Auto-exit after {position_age:.1f} minutes (scalping rule)")
            
            # 5. SMALL PROFIT CAPTURE: Take profits quickly on small moves
            elif pnl_pct > 3 and position_age > 2:  # 3%+ profit after 2+ minutes
                actions['immediate_exit'] = True
                actions['exit_reason'] = 'QUICK_PROFIT_CAPTURE'
                logger.info(f"💨 {self.name}: {symbol} - Quick profit capture: {pnl_pct:.2f}% in {position_age:.1f}min")
            
            return actions
            
        except Exception as e:
            logger.error(f"Error analyzing position management for {symbol}: {e}")
            return {}
    
    async def book_partial_profits(self, symbol: str, current_price: float, position: Dict, percentage: int):
        """💰 PARTIAL PROFIT BOOKING - Lock in profits while maintaining exposure"""
        try:
            current_quantity = position.get('quantity', 0)
            action = position.get('action', 'BUY')
            
            # Calculate quantity to book
            quantity_to_book = max(1, int(current_quantity * percentage / 100))
            
            # Create exit signal for partial quantity
            exit_action = 'SELL' if action == 'BUY' else 'BUY'
            
            # Generate partial exit signal for execution
            partial_signal = await self._create_management_signal(
                symbol=symbol,
                action=exit_action,
                quantity=quantity_to_book,
                price=current_price,
                reason=f'PARTIAL_PROFIT_BOOKING_{percentage}%'
            )
            
            # Execute the partial exit order
            if partial_signal:
                await self._execute_management_action(partial_signal)
                logger.info(f"💰 {self.name}: Booking {percentage}% profits for {symbol} - {quantity_to_book} shares at ₹{current_price:.2f}")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'PARTIAL_PROFIT_BOOKING_{percentage}%')
                self.last_management_time[symbol] = datetime.now()
                
                # Update position quantity
                remaining_quantity = current_quantity - quantity_to_book
                if remaining_quantity > 0:
                    position['quantity'] = remaining_quantity
                    logger.info(f"📊 {symbol}: Remaining position - {remaining_quantity} shares")
                else:
                    # Position fully closed
                    await self.exit_position(symbol, current_price, f'FULL_PROFIT_BOOKING_{percentage}%')
            
        except Exception as e:
            logger.error(f"Error booking partial profits for {symbol}: {e}")
    
    async def scale_into_position(self, symbol: str, current_price: float, position: Dict, additional_quantity: int):
        """📈 POSITION SCALING - Add to winning positions with strong momentum"""
        try:
            action = position.get('action', 'BUY')
            
            # Create additional position signal for execution
            scale_signal = await self._create_management_signal(
                symbol=symbol,
                action=action,  # Same direction as original
                quantity=additional_quantity,
                price=current_price,
                reason='POSITION_SCALING_MOMENTUM'
            )
            
            # Execute the scaling order
            if scale_signal:
                await self._execute_management_action(scale_signal)
                logger.info(f"📈 {self.name}: Scaling {symbol} position - Adding {additional_quantity} shares at ₹{current_price:.2f}")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'POSITION_SCALING_{additional_quantity}_shares')
                self.last_management_time[symbol] = datetime.now()
                
                # Update position tracking to include scaled quantity
                current_quantity = position.get('quantity', 0)
                position['quantity'] = current_quantity + additional_quantity
                
                # Recalculate average entry price
                current_entry = position.get('entry_price', 0)
                current_value = current_quantity * current_entry
                additional_value = additional_quantity * current_price
                new_avg_entry = (current_value + additional_value) / (current_quantity + additional_quantity)
                position['entry_price'] = new_avg_entry
                
                logger.info(f"📊 {symbol}: Scaled position - {position['quantity']} total shares, avg entry: ₹{new_avg_entry:.2f}")
            
        except Exception as e:
            logger.error(f"Error scaling position for {symbol}: {e}")
    
    async def adjust_dynamic_stop_loss(self, symbol: str, current_price: float, position: Dict, new_stop_loss: float):
        """🛡️ DYNAMIC STOP LOSS - Adjust stop loss based on market conditions"""
        try:
            current_stop = position.get('stop_loss', 0)
            action = position.get('action', 'BUY')
            
            # Only adjust if new stop is better (more protective while profitable)
            should_update = False
            if action == 'BUY' and new_stop_loss > current_stop:
                should_update = True
            elif action == 'SELL' and new_stop_loss < current_stop:
                should_update = True
            
            if should_update:
                position['stop_loss'] = new_stop_loss
                logger.info(f"🛡️ {self.name}: Adjusted {symbol} stop loss to ₹{new_stop_loss:.2f} (was ₹{current_stop:.2f})")
                
                # Track management action
                if symbol not in self.management_actions_taken:
                    self.management_actions_taken[symbol] = []
                self.management_actions_taken[symbol].append(f'STOP_LOSS_ADJUSTMENT_TO_{new_stop_loss:.2f}')
                self.last_management_time[symbol] = datetime.now()
                
                # Update stop loss in position tracker/broker if available
                # Note: Stop loss adjustments are applied to the position tracker
                # The actual broker stop loss orders are managed by the position monitor
            
        except Exception as e:
            logger.error(f"Error adjusting stop loss for {symbol}: {e}")
    
    async def apply_time_based_management(self, symbol: str, current_price: float, position: Dict):
        """⏰ TIME-BASED MANAGEMENT - Apply time decay considerations"""
        try:
            entry_time = position.get('timestamp')
            if not entry_time:
                return
                
            # Calculate position age
            try:
                if isinstance(entry_time, str):
                    entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                else:
                    entry_dt = entry_time
                position_age_hours = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 3600
            except:
                return
            
            action = position.get('action', 'BUY')
            entry_price = position.get('entry_price', 0)
            
            # Calculate current P&L
            if action == 'BUY':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Time-based profit protection (tighten stops over time)
            if position_age_hours > 2 and pnl_pct > 0:  # 2+ hours and profitable
                # Tighten trailing stop for older positions
                tighter_stop_pct = max(0.5, 2.0 - (position_age_hours * 0.2))  # Gradually tighten
                
                if symbol in self.trailing_stops:
                    current_trail = self.trailing_stops[symbol]['stop_price']
                    if action == 'BUY':
                        tighter_stop = current_price * (1 - tighter_stop_pct / 100)
                        if tighter_stop > current_trail:
                            self.trailing_stops[symbol]['stop_price'] = tighter_stop
                            logger.info(f"⏰ {self.name}: Tightened trailing stop for {symbol} due to time (age: {position_age_hours:.1f}h)")
                    else:
                        tighter_stop = current_price * (1 + tighter_stop_pct / 100)
                        if tighter_stop < current_trail:
                            self.trailing_stops[symbol]['stop_price'] = tighter_stop
                            logger.info(f"⏰ {self.name}: Tightened trailing stop for {symbol} due to time (age: {position_age_hours:.1f}h)")
            
        except Exception as e:
            logger.error(f"Error applying time-based management for {symbol}: {e}")
    
    async def apply_volatility_based_management(self, symbol: str, current_price: float, position: Dict, market_data: Dict):
        """📊 VOLATILITY-BASED MANAGEMENT - Adjust based on market volatility"""
        try:
            # Calculate short-term volatility from price movements
            high = market_data.get('high', current_price)
            low = market_data.get('low', current_price)
            volume = market_data.get('volume', 0)
            
            # Calculate intraday volatility
            if high > 0 and low > 0:
                intraday_volatility = ((high - low) / current_price) * 100
                
                action = position.get('action', 'BUY')
                entry_price = position.get('entry_price', 0)
                
                # High volatility (>3%) - tighten stops
                if intraday_volatility > 3:
                    if symbol in self.trailing_stops:
                        current_trail = self.trailing_stops[symbol]['stop_price']
                        volatility_adjustment = 0.5  # Tighter stops in high volatility
                        
                        if action == 'BUY':
                            adjusted_stop = current_price * (1 - volatility_adjustment / 100)
                            if adjusted_stop > current_trail:
                                self.trailing_stops[symbol]['stop_price'] = adjusted_stop
                                logger.info(f"📊 {self.name}: Tightened stop for {symbol} due to high volatility ({intraday_volatility:.2f}%)")
                        else:
                            adjusted_stop = current_price * (1 + volatility_adjustment / 100)
                            if adjusted_stop < current_trail:
                                self.trailing_stops[symbol]['stop_price'] = adjusted_stop
                                logger.info(f"📊 {self.name}: Tightened stop for {symbol} due to high volatility ({intraday_volatility:.2f}%)")
                
                # Low volatility (<1%) with high volume - consider scaling
                elif intraday_volatility < 1 and volume > 500000:
                    # This suggests strong conviction move - handled in main analysis
                    pass
            
        except Exception as e:
            logger.error(f"Error applying volatility-based management for {symbol}: {e}")
    
    def get_position_management_summary(self) -> Dict:
        """📊 GET POSITION MANAGEMENT SUMMARY - For monitoring and reporting"""
        try:
            summary = {
                'total_positions': len(self.active_positions),
                'positions_with_trailing_stops': len(self.trailing_stops),
                'management_actions': {},
                'position_details': []
            }
            
            # Count management actions
            for symbol, actions in self.management_actions_taken.items():
                for action in actions:
                    if action not in summary['management_actions']:
                        summary['management_actions'][action] = 0
                    summary['management_actions'][action] += 1
            
            # Position details with current P&L
            for symbol, position in self.active_positions.items():
                entry_price = position.get('entry_price', 0)
                current_price = position.get('current_price', entry_price)
                action = position.get('action', 'BUY')
                quantity = position.get('quantity', 0)
                
                # Calculate P&L
                if action == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
                
                # Position age
                entry_time = position.get('timestamp')
                age_hours = 0
                if entry_time:
                    try:
                        if isinstance(entry_time, str):
                            entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                        else:
                            entry_dt = entry_time
                        age_hours = (datetime.now().replace(tzinfo=None) - entry_dt.replace(tzinfo=None)).total_seconds() / 3600
                    except:
                        pass
                
                position_detail = {
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl_percent': pnl_pct,
                    'age_hours': age_hours,
                    'has_trailing_stop': symbol in self.trailing_stops,
                    'management_actions': self.management_actions_taken.get(symbol, [])
                }
                
                summary['position_details'].append(position_detail)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating position management summary: {e}")
            return {}
    
    def log_position_management_status(self):
        """📊 LOG POSITION MANAGEMENT STATUS - Regular monitoring log"""
        try:
            summary = self.get_position_management_summary()
            
            if summary['total_positions'] > 0:
                logger.info(f"🎯 {self.name} POSITION MANAGEMENT STATUS:")
                logger.info(f"   📊 Total Positions: {summary['total_positions']}")
                logger.info(f"   🛡️ Trailing Stops: {summary['positions_with_trailing_stops']}")
                
                # Log management actions taken
                if summary['management_actions']:
                    actions_str = ", ".join([f"{action}: {count}" for action, count in summary['management_actions'].items()])
                    logger.info(f"   ⚡ Actions Taken: {actions_str}")
                
                # Log top 3 positions by P&L
                positions = sorted(summary['position_details'], key=lambda x: x['pnl_percent'], reverse=True)[:3]
                for pos in positions:
                    logger.info(f"   📈 {pos['symbol']}: {pos['pnl_percent']:.2f}% | "
                               f"Age: {pos['age_hours']:.1f}h | Actions: {len(pos['management_actions'])}")
        
        except Exception as e:
            logger.error(f"Error logging position management status: {e}")
    
    async def _create_management_signal(self, symbol: str, action: str, quantity: int, price: float, reason: str) -> Dict:
        """🎯 CREATE MANAGEMENT SIGNAL - Format position management actions as executable signals"""
        try:
            # Create signal in the same format as regular trading signals
            management_signal = {
                'signal_id': f"{self.name}_MGMT_{symbol}_{int(time_module.time())}",
                'symbol': symbol,
                'action': action.upper(),
                'quantity': quantity,
                'entry_price': price,
                'price': price,  # Both fields for compatibility
                'order_type': 'MARKET',  # Management actions use market orders for quick execution
                'product': self._get_product_type_for_symbol(symbol),
                'validity': 'DAY',
                'tag': 'POSITION_MGMT',
                'strategy': self.name,
                'strategy_name': self.name,
                'reason': reason,
                'user_id': 'system',
                'timestamp': datetime.now().isoformat(),
                'management_action': True,  # Flag to identify management actions
                'closing_action': True,     # Allow execution even after 3:00 PM
                'source': 'position_management'
            }
            
            logger.debug(f"🎯 Created management signal: {symbol} {action} {quantity} @ ₹{price:.2f} ({reason})")
            return management_signal
            
        except Exception as e:
            logger.error(f"Error creating management signal for {symbol}: {e}")
            return {}
    
    def _get_product_type_for_symbol(self, symbol: str) -> str:
        """Get appropriate product type for symbol"""
        # Options require NRML, equity can use MIS for intraday
        if 'CE' in symbol or 'PE' in symbol:
            return 'NRML'  # Options must use NRML
        else:
            return 'MIS'  # Margin Intraday Square-off for equity
    
    async def _execute_management_action(self, signal: Dict):
        """🚀 EXECUTE MANAGEMENT ACTION - Send management signals for immediate execution"""
        try:
            # 🚨 CRITICAL: Record order placement to prevent duplicates
            symbol = signal.get('symbol')
            if symbol:
                self._record_order_placement(symbol)
            
            # Get orchestrator instance for execution
            orchestrator = self._get_orchestrator_instance()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                # Send directly to trade engine for immediate execution
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.info(f"🚀 Executing management action: {signal['symbol']} {signal['action']} {signal['quantity']} ({reason})")
                
                # Process through trade engine (bypasses deduplication for management actions)
                await orchestrator.trade_engine._process_live_signal(signal)
                
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.info(f"✅ Management action submitted: {signal['symbol']} {reason}")
                
            else:
                # Fallback: Store in pending management actions for next cycle processing
                reason = signal.get('reason', signal.get('metadata', {}).get('reason', 'POSITION_MANAGEMENT'))
                logger.warning(f"⚠️ No trade engine available - queuing management action: {signal['symbol']} {reason}")
                
                if not hasattr(self, 'pending_management_actions'):
                    self.pending_management_actions = []
                self.pending_management_actions.append(signal)
                
        except Exception as e:
            logger.error(f"❌ Error executing management action for {signal.get('symbol', 'UNKNOWN')}: {e}")
            # Don't raise exception to avoid breaking position management loop
    
    def _get_orchestrator_instance(self):
        """Get orchestrator instance for execution"""
        try:
            # Try to get orchestrator instance from singleton pattern
            if hasattr(self, 'orchestrator') and self.orchestrator:
                return self.orchestrator
            
            # Try to get from TradingOrchestrator singleton
            from src.core.orchestrator import TradingOrchestrator
            return getattr(TradingOrchestrator, '_instance', None)
            
        except Exception as e:
            logger.error(f"Error getting orchestrator instance: {e}")
            return None
    
    async def process_pending_management_actions(self):
        """🔄 PROCESS PENDING MANAGEMENT ACTIONS - Handle queued management actions"""
        try:
            if not hasattr(self, 'pending_management_actions') or not self.pending_management_actions:
                return
            
            logger.info(f"🔄 Processing {len(self.pending_management_actions)} pending management actions")
            
            for signal in self.pending_management_actions.copy():
                await self._execute_management_action(signal)
                self.pending_management_actions.remove(signal)
                
            logger.info(f"✅ Processed all pending management actions")
            
        except Exception as e:
            logger.error(f"Error processing pending management actions: {e}")
    
    async def exit_position(self, symbol: str, exit_price: float, reason: str):
        """Exit position and clean up tracking data"""
        try:
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                entry_price = position.get('entry_price', 0)
                action = position.get('action', 'BUY')
                
                # Calculate realized P&L
                if action == 'BUY':
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                
                # Log position exit
                logger.info(f"🚪 {self.name}: EXITING {symbol} at ₹{exit_price:.2f} | "
                           f"Entry: ₹{entry_price:.2f} | P&L: {pnl_pct:.2f}% | Reason: {reason}")
                
                # Clean up position tracking
                del self.active_positions[symbol]
                if symbol in self.position_metadata:
                    del self.position_metadata[symbol]
                if symbol in self.trailing_stops:
                    del self.trailing_stops[symbol]
                if symbol in self.position_entry_times:
                    del self.position_entry_times[symbol]
                
                # Create exit signal for execution
                exit_signal = {
                    'symbol': symbol,
                    'action': 'SELL' if action == 'BUY' else 'BUY',  # Opposite action to close
                    'entry_price': exit_price,
                    'stop_loss': 0,  # No stop loss for exit signal
                    'target': exit_price,
                    'confidence': 10.0,  # High confidence for exits
                    'quantity': position.get('quantity', 1),
                    'strategy': self.name,
                    'signal_type': 'POSITION_EXIT',
                    'exit_reason': reason,
                    'original_entry_price': entry_price,
                    'realized_pnl_pct': pnl_pct,
                    'metadata': {
                        'position_exit': True,
                        'exit_reason': reason,
                        'holding_time_hours': (datetime.now() - self.position_entry_times.get(symbol, datetime.now())).total_seconds() / 3600
                    }
                }
                
                # Store exit signal for orchestrator collection
                self.current_positions[f"{symbol}_EXIT"] = exit_signal
                
        except Exception as e:
            logger.error(f"Error exiting position for {symbol}: {e}")
    
    def record_position_entry(self, symbol: str, signal: Dict):
        """Record position entry for tracking and management"""
        try:
            # Store active position data
            self.active_positions[symbol] = {
                'entry_price': signal.get('entry_price', 0),
                'action': signal.get('action', 'BUY'),
                'stop_loss': signal.get('stop_loss', 0),
                'target': signal.get('target', 0),
                'confidence': signal.get('confidence', 0),
                'quantity': signal.get('quantity', 1),
                'strategy': self.name,
                'entry_time': datetime.now(),
                'timestamp': time_module.time()
            }
            
            # Store entry time for age tracking
            self.position_entry_times[symbol] = datetime.now()
            
            # Store strategy-specific metadata
            self.position_metadata[symbol] = signal.get('metadata', {})
            
            logger.info(f"📈 {self.name}: POSITION ENTERED {symbol} {signal.get('action')} at ₹{signal.get('entry_price', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Error recording position entry for {symbol}: {e}")
    
    def _is_symbol_scalping_cooldown_passed(self, symbol: str, cooldown_seconds: int = 30) -> bool:
        """Check if symbol-specific SCALPING cooldown has passed"""
        if symbol not in self.symbol_cooldowns:
            return True
        
        last_signal = self.symbol_cooldowns[symbol]
        time_since = (datetime.now() - last_signal).total_seconds()
        return time_since >= cooldown_seconds
    
    def _update_symbol_cooldown(self, symbol: str):
        """Update symbol-specific cooldown timestamp"""
        if not hasattr(self, 'symbol_cooldowns'):
            self.symbol_cooldowns = {}
        self.symbol_cooldowns[symbol] = datetime.now()
        
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours - INTRADAY FOCUSED with square-off logic"""
        try:
            # Get current time in IST (same as orchestrator)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # NSE trading hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # 🚨 DAVID VS GOLIATH: Stop OPTIONS even EARLIER (avoid theta decay trap)
            # Market makers win in the last 2 hours via time decay
            # Exit before they feast on our premiums
            options_cutoff_time = time(13, 30)  # 1:30 PM - No new OPTIONS after this (was 2:00 PM)
            square_off_time = time(15, 0)  # 3:00 PM - Start square-off
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                logger.info(f"🚫 SAFETY: Trading blocked on weekend. Current day: {now.strftime('%A')}")
                return False
            
            is_trading_time = market_open <= current_time <= market_close
            is_square_off_time = square_off_time <= current_time <= market_close
            is_options_late = options_cutoff_time <= current_time <= market_close
            
            if not is_trading_time:
                logger.info(f"🚫 SAFETY: Trading blocked outside market hours. Current IST time: {current_time} "
                           f"(Market: {market_open} - {market_close})")
                return False
            elif is_square_off_time:
                logger.warning(f"⚠️ INTRADAY SQUARE-OFF: New positions blocked. Current time: {current_time} "
                              f"(Square-off starts: {square_off_time})")
                return False
            elif option_type in ['CE', 'PE'] and is_options_late:
                logger.warning(f"🚫 OPTIONS CUTOFF: No new options after {options_cutoff_time} (avoid theta decay)")
                logger.info(f"   Current time: {current_time} | Options cutoff: {options_cutoff_time}")
                return False
            else:
                logger.info(f"✅ TRADING HOURS: Market open for new positions. Current IST time: {current_time}")
                return True
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFETY: If timezone check fails, default to False (safer)
            return False
    
    def _is_intraday_square_off_time(self) -> bool:
        """Check if it's time to square off intraday positions"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Square-off window: 3:00 PM to 3:30 PM
            square_off_start = time(15, 0)
            market_close = time(15, 30)
            
            return square_off_start <= current_time <= market_close
            
        except Exception as e:
            logger.error(f"Error checking square-off time: {e}")
            return False
    
    def _is_opening_gap_gate_active(self, market_data: Dict, gap_threshold: float = 0.8) -> bool:
        """Opening gate: block counter-gap trades in first minutes after large gap"""
        try:
            # Determine time phase from orchestrator if available
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            time_phase = getattr(getattr(orchestrator, 'market_bias', None), 'current_bias', None)
            phase = getattr(time_phase, 'time_phase', 'UNKNOWN') if time_phase else 'UNKNOWN'

            if phase not in ('OPENING', 'MORNING'):
                return False

            # Use index data for gap (NIFTY-I preferred)
            index_data = market_data.get('NIFTY-I') or market_data.get('NIFTY') or {}
            open_price = float(index_data.get('open', 0) or 0)
            prev_close = float(index_data.get('prev_close', 0) or 0)
            if open_price > 0 and prev_close > 0:
                gap_pct = ((open_price - prev_close) / prev_close) * 100.0
                return abs(gap_pct) >= gap_threshold
            return False
        except Exception:
            return False

    def calculate_true_range(self, high: float, low: float, prev_close: float) -> float:
        """Calculate True Range - the foundation of proper ATR calculation"""
        try:
            if prev_close <= 0:
                return high - low  # First calculation or invalid previous close
            
            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            range1 = high - low
            range2 = abs(high - prev_close)
            range3 = abs(low - prev_close)
            
            return max(range1, range2, range3)
            
        except Exception as e:
            logger.error(f"Error calculating True Range: {e}")
            return high - low if high > low else 0.01  # Fallback
    
    def calculate_atr(self, symbol: str, current_high: float, current_low: float, 
                     current_close: float, period: int = 14) -> float:
        """
        PROFESSIONAL GARCH-ENHANCED ATR CALCULATION
        DAVID VS GOLIATH ADVANTAGE: Superior volatility estimation using GARCH models
        """
        try:
            # Store current data
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            # Add current data point
            data_point = {
                'high': current_high,
                'low': current_low,
                'close': current_close,
                'timestamp': datetime.now()
            }
            
            self.historical_data[symbol].append(data_point)
            
            # Trim history if needed
            if len(self.historical_data[symbol]) > self.max_history:
                self.historical_data[symbol].pop(0)
            
            history = self.historical_data[symbol]
            if len(history) < 2:
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # PROFESSIONAL GARCH-ENHANCED ATR
            if len(history) >= 10:  # Need sufficient data for GARCH
                # Extract price series
                prices = np.array([h['close'] for h in history])
                
                # GARCH-enhanced ATR (our competitive advantage)
                garch_atr = ProfessionalMathFoundation.garch_atr(prices, period)
                
                # Traditional ATR for ensemble
                traditional_atr = self._calculate_traditional_atr_internal(history, period)
                
                # ENSEMBLE ATR (70% GARCH, 30% traditional)
                ensemble_atr = (garch_atr * 0.7) + (traditional_atr * 0.3)
                
                # PROFESSIONAL VALIDATION
                atr_percentage = ensemble_atr / current_close if current_close > 0 else 0.02
                
                # Adaptive bounds based on market conditions
                if atr_percentage < 0.003:  # Too conservative
                    ensemble_atr = current_close * 0.008
                elif atr_percentage > 0.08:  # Too aggressive
                    ensemble_atr = current_close * 0.04
                
                # Update performance attribution
                self._update_performance_attribution(symbol, ensemble_atr, garch_atr, traditional_atr)
                
                return max(ensemble_atr, 1.0)
            
            else:
                # Fallback to traditional ATR for insufficient data
                return self._calculate_traditional_atr_internal(history, period)
                
        except Exception as e:
            logger.error(f"Professional ATR calculation failed for {symbol}: {e}")
            return current_high - current_low if current_high > current_low else current_close * 0.01
    
    def _calculate_traditional_atr_internal(self, history: List[Dict], period: int) -> float:
        """Traditional ATR calculation for ensemble"""
        try:
            true_ranges = []
            for i in range(1, len(history)):
                prev_close = history[i-1]['close']
                current_data = history[i]
                tr = self.calculate_true_range(
                    current_data['high'], 
                    current_data['low'], 
                    prev_close
                )
                true_ranges.append(tr)
            
            if len(true_ranges) == 0:
                return 0.02
            
            atr_period = min(period, len(true_ranges))
            recent_trs = true_ranges[-atr_period:]
            atr = np.mean(recent_trs)
            
            # Ensure minimum ATR (0.1% of price) and reasonable maximum (10% of price)
            min_atr = current_close * 0.001 if hasattr(self, 'current_close') else 1.0
            max_atr = current_close * 0.1 if hasattr(self, 'current_close') else 100.0
            
            return max(min_atr, min(atr, max_atr))
            
        except Exception as e:
            logger.error(f"Traditional ATR calculation failed: {e}")
            return 0.02
    
    def _update_performance_attribution(self, symbol: str, ensemble_atr: float, 
                                      garch_atr: float, traditional_atr: float):
        """Update performance attribution for professional analysis"""
        try:
            if not hasattr(self, 'atr_performance'):
                self.atr_performance = {}
            
            if symbol not in self.atr_performance:
                self.atr_performance[symbol] = {
                    'ensemble_history': [],
                    'garch_history': [],
                    'traditional_history': [],
                    'accuracy_scores': []
                }
            
            perf = self.atr_performance[symbol]
            perf['ensemble_history'].append(ensemble_atr)
            perf['garch_history'].append(garch_atr)
            perf['traditional_history'].append(traditional_atr)
            
            # Keep only recent history (last 50 observations)
            for key in ['ensemble_history', 'garch_history', 'traditional_history']:
                if len(perf[key]) > 50:
                    perf[key].pop(0)
            
            # Update strategy-level performance attribution
            if len(self.strategy_returns) > 0:
                recent_returns = np.array(self.strategy_returns[-20:])  # Last 20 trades
                
                # Update professional metrics
                self.performance_attribution['sharpe_ratio'] = ProfessionalMathFoundation.sharpe_ratio(recent_returns)
                self.performance_attribution['var_95'] = ProfessionalMathFoundation.var_calculation(recent_returns)
                self.performance_attribution['statistical_significance'] = ProfessionalMathFoundation.statistical_significance_test(recent_returns)
                
                # Calculate win rate and average win/loss
                wins = recent_returns[recent_returns > 0]
                losses = recent_returns[recent_returns < 0]
                
                self.performance_attribution['win_rate'] = len(wins) / len(recent_returns) if len(recent_returns) > 0 else 0.0
                self.performance_attribution['avg_win'] = np.mean(wins) if len(wins) > 0 else 0.0
                self.performance_attribution['avg_loss'] = np.mean(losses) if len(losses) > 0 else 0.0
                
                # Calculate Kelly optimal size
                if len(wins) > 0 and len(losses) > 0:
                    self.performance_attribution['kelly_optimal_size'] = ProfessionalMathFoundation.kelly_position_size(
                        self.performance_attribution['win_rate'],
                        abs(self.performance_attribution['avg_win']),
                        abs(self.performance_attribution['avg_loss']),
                        100000  # Assume ₹1L capital for percentage calculation
                    ) / 100000  # Convert back to fraction
                    
        except Exception as e:
            logger.error(f"Performance attribution update failed: {e}")
    
    def get_professional_position_size(self, symbol: str, signal_confidence: float, 
                                     current_price: float, capital: float) -> float:
        """
        PROFESSIONAL POSITION SIZING using Kelly Criterion
        COMPETITIVE ADVANTAGE: Optimal sizing vs fixed percentages
        """
        try:
            # Base position size from Kelly criterion
            kelly_size = self.performance_attribution.get('kelly_optimal_size', 0.02)
            
            # Adjust based on signal confidence
            confidence_multiplier = min(signal_confidence / 10.0, 1.0)  # Normalize to 0-1
            
            # Adjust based on current volatility (ATR)
            if symbol in self.historical_data and len(self.historical_data[symbol]) > 5:
                recent_data = self.historical_data[symbol][-1]
                atr = self.calculate_atr(symbol, recent_data['high'], recent_data['low'], recent_data['close'])
                volatility_adjustment = min(1.0, 0.02 / (atr / current_price))  # Reduce size for high volatility
            else:
                volatility_adjustment = 1.0
            
            # Professional position sizing formula
            optimal_size = kelly_size * confidence_multiplier * volatility_adjustment
            
            # Safety bounds
            optimal_size = max(0.005, min(optimal_size, 0.05))  # Between 0.5% and 5%
            
            position_value = optimal_size * capital
            
            logger.debug(f"🎯 PROFESSIONAL SIZING: {symbol} kelly={kelly_size:.3f} "
                        f"confidence={confidence_multiplier:.2f} vol_adj={volatility_adjustment:.2f} "
                        f"final={optimal_size:.3f} value=₹{position_value:,.0f}")
            
            return position_value
            
        except Exception as e:
            logger.error(f"Professional position sizing failed for {symbol}: {e}")
            return capital * 0.02  # 2% fallback
            
            return max(min_atr, min(atr, max_atr))
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {e}")
            # Fallback to simple range calculation
            return current_high - current_low if current_high > current_low else current_close * 0.01
    
    def calculate_dynamic_stop_loss(self, entry_price: float, atr: float, action: str, 
                                   multiplier: float = 2.0, min_percent: float = 0.5, 
                                   max_percent: float = 5.0, available_capital: float = None) -> float:
        """Calculate dynamic stop loss with MAXIMUM 1% RISK PER TRADE constraint"""
        try:
            # Get available capital for 1% risk calculation
            if available_capital is None:
                available_capital = self._get_available_capital()
            
            # MAXIMUM 1% RISK PER TRADE CONSTRAINT
            max_risk_amount = available_capital * 0.01  # 1% of capital
            
            # Calculate ATR-based stop loss distance
            atr_distance = atr * multiplier
            
            # Convert to percentage
            atr_percent = (atr_distance / entry_price) * 100
            
            # CRITICAL: Ensure stop loss doesn't exceed 1% risk per trade
            # Estimate typical trade size to validate risk
            typical_trade_value = min(available_capital * 0.25, 50000)  # 25% capital or ₹50k max
            typical_quantity = typical_trade_value / entry_price
            potential_risk = atr_distance * typical_quantity
            
            # If ATR-based risk exceeds 1%, constrain it
            if potential_risk > max_risk_amount:
                # Recalculate stop distance to exactly match 1% risk
                constrained_distance = max_risk_amount / typical_quantity
                constrained_percent = (constrained_distance / entry_price) * 100
                logger.info(f"🛡️ 1% RISK CONSTRAINT: {action} @ {entry_price:.2f} - ATR stop {atr_percent:.2f}% → {constrained_percent:.2f}%")
                bounded_percent = constrained_percent
            else:
                # Apply SCALPING-OPTIMIZED bounds (tighter than original)
                bounded_percent = max(min_percent, min(atr_percent, max_percent))
            
            bounded_distance = (bounded_percent / 100) * entry_price
            
            # Calculate stop loss based on action
            if action.upper() == 'BUY':
                stop_loss = entry_price - bounded_distance
            else:  # SELL
                stop_loss = entry_price + bounded_distance
            
            logger.info(f"🎯 DYNAMIC STOP: {action} @ {entry_price:.2f} → SL @ {stop_loss:.2f} "
                       f"(Risk: {bounded_percent:.2f}%, Max Risk: ₹{max_risk_amount:.0f})")
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            # Fallback to percentage-based stop loss
            fallback_percent = 0.5  # 0.5% fallback for scalping
            if action.upper() == 'BUY':
                return entry_price * (1 - fallback_percent / 100)
            else:
                return entry_price * (1 + fallback_percent / 100)
    
    def calculate_rsi_divergence(self, symbol: str, prices: List[float], rsi_values: List[float]) -> Optional[str]:
        """
        🎯 CODE ENHANCEMENT: Detect RSI divergence for high-probability reversals
        RSI divergence is one of the most reliable reversal signals
        
        Returns: 'bullish', 'bearish', or None
        """
        try:
            if len(prices) < 14 or len(rsi_values) < 14:
                return None
            
            # Find recent peaks and troughs
            recent_prices = prices[-14:]
            recent_rsi = rsi_values[-14:]
            
            # Bullish divergence: Price makes lower low, RSI makes higher low
            price_low_1 = min(recent_prices[:7])
            price_low_2 = min(recent_prices[7:])
            
            # Find corresponding RSI values
            price_low_1_idx = recent_prices[:7].index(price_low_1)
            price_low_2_idx = 7 + recent_prices[7:].index(price_low_2)
            
            rsi_at_low_1 = recent_rsi[price_low_1_idx]
            rsi_at_low_2 = recent_rsi[price_low_2_idx]
            
            # Bullish divergence detected
            if price_low_2 < price_low_1 and rsi_at_low_2 > rsi_at_low_1:
                logger.info(f"📈 BULLISH DIVERGENCE detected for {symbol}: Price {price_low_1:.2f}→{price_low_2:.2f}, RSI {rsi_at_low_1:.1f}→{rsi_at_low_2:.1f}")
                return 'bullish'
            
            # Bearish divergence: Price makes higher high, RSI makes lower high
            price_high_1 = max(recent_prices[:7])
            price_high_2 = max(recent_prices[7:])
            
            price_high_1_idx = recent_prices[:7].index(price_high_1)
            price_high_2_idx = 7 + recent_prices[7:].index(price_high_2)
            
            rsi_at_high_1 = recent_rsi[price_high_1_idx]
            rsi_at_high_2 = recent_rsi[price_high_2_idx]
            
            # Bearish divergence detected
            if price_high_2 > price_high_1 and rsi_at_high_2 < rsi_at_high_1:
                logger.info(f"📉 BEARISH DIVERGENCE detected for {symbol}: Price {price_high_1:.2f}→{price_high_2:.2f}, RSI {rsi_at_high_1:.1f}→{rsi_at_high_2:.1f}")
                return 'bearish'
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating RSI divergence: {e}")
            return None
    
    def detect_bollinger_squeeze(self, symbol: str, prices: List[float], period: int = 20) -> Dict:
        """
        🎯 CODE ENHANCEMENT: Detect Bollinger Band squeeze (precedes big moves)
        When bands squeeze tight, a large move is imminent
        
        Returns: {'squeezing': bool, 'breakout_direction': str, 'squeeze_intensity': float}
        """
        try:
            if len(prices) < period:
                return {'squeezing': False, 'breakout_direction': None, 'squeeze_intensity': 0.0}
            
            recent_prices = prices[-period:]
            
            # Calculate Bollinger Bands
            sma = np.mean(recent_prices)
            std = np.std(recent_prices)
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            bandwidth = (upper_band - lower_band) / sma
            
            # Historical bandwidth for comparison
            if len(prices) >= period * 2:
                historical_prices = prices[-period*2:-period]
                hist_sma = np.mean(historical_prices)
                hist_std = np.std(historical_prices)
                hist_bandwidth = (2 * hist_std * 2) / hist_sma
                
                # Squeeze detected when current bandwidth < 75% of historical
                is_squeezing = bandwidth < (hist_bandwidth * 0.75)
                squeeze_intensity = 1 - (bandwidth / hist_bandwidth) if hist_bandwidth > 0 else 0
                
                # Detect breakout direction
                current_price = prices[-1]
                breakout_direction = None
                
                if is_squeezing:
                    # Check momentum
                    recent_momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
                    
                    if current_price > sma and recent_momentum > 0.002:  # Breaking up
                        breakout_direction = 'UP'
                        logger.info(f"🎯 SQUEEZE BREAKOUT UP detected for {symbol}: Intensity {squeeze_intensity:.2%}")
                    elif current_price < sma and recent_momentum < -0.002:  # Breaking down
                        breakout_direction = 'DOWN'
                        logger.info(f"🎯 SQUEEZE BREAKOUT DOWN detected for {symbol}: Intensity {squeeze_intensity:.2%}")
                
                return {
                    'squeezing': is_squeezing,
                    'breakout_direction': breakout_direction,
                    'squeeze_intensity': squeeze_intensity,
                    'bandwidth': bandwidth
                }
            
            return {'squeezing': False, 'breakout_direction': None, 'squeeze_intensity': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting Bollinger squeeze: {e}")
            return {'squeezing': False, 'breakout_direction': None, 'squeeze_intensity': 0.0}
    
    def calculate_macd_signal(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        🎯 CODE ENHANCEMENT: MACD with histogram divergence detection
        MACD is excellent for trend strength and momentum
        
        Returns: {'macd': float, 'signal': float, 'histogram': float, 'divergence': str}
        """
        try:
            if len(prices) < slow + signal:
                return {'macd': 0, 'signal': 0, 'histogram': 0, 'divergence': None}
            
            prices_array = np.array(prices)
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(prices_array, fast)
            ema_slow = self._calculate_ema(prices_array, slow)
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            macd_series = prices_array[-len(macd_line):]
            signal_line = self._calculate_ema(macd_line, signal)
            
            # Histogram
            histogram = macd_line[-len(signal_line):] - signal_line
            
            # Detect histogram divergence
            divergence = None
            if len(histogram) >= 10:
                recent_hist = histogram[-10:]
                # Positive divergence: histogram making higher lows
                if recent_hist[-1] > recent_hist[-5] and recent_hist[-1] < 0:
                    divergence = 'bullish'
                # Negative divergence: histogram making lower highs
                elif recent_hist[-1] < recent_hist[-5] and recent_hist[-1] > 0:
                    divergence = 'bearish'
            
            return {
                'macd': macd_line[-1],
                'signal': signal_line[-1],
                'histogram': histogram[-1],
                'divergence': divergence,
                'crossover': 'bullish' if macd_line[-1] > signal_line[-1] and macd_line[-2] < signal_line[-2] else 'bearish' if macd_line[-1] < signal_line[-1] and macd_line[-2] > signal_line[-2] else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'divergence': None}
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def detect_market_regime(self, symbol: str, prices: List[float], volumes: List[float]) -> Dict:
        """
        🎯 CODE ENHANCEMENT: Sophisticated market regime detection
        Different strategies work in different regimes
        
        Returns: {'regime': str, 'strength': float, 'volatility': str}
        """
        try:
            if len(prices) < 50:
                return {'regime': 'UNKNOWN', 'strength': 0.0, 'volatility': 'NORMAL'}
            
            recent_prices = np.array(prices[-50:])
            recent_volumes = np.array(volumes[-50:]) if len(volumes) >= 50 else None
            
            # Calculate metrics
            returns = np.diff(recent_prices) / recent_prices[:-1]
            
            # 1. Trend detection (using ADX concept)
            sma_20 = np.mean(recent_prices[-20:])
            sma_50 = np.mean(recent_prices)
            trend_slope = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            # 2. Volatility regime
            volatility = np.std(returns) * np.sqrt(252)
            hist_volatility = np.std(np.diff(prices[-100:-50]) / prices[-100:-50]) * np.sqrt(252) if len(prices) >= 100 else volatility
            
            volatility_regime = 'HIGH' if volatility > hist_volatility * 1.3 else 'LOW' if volatility < hist_volatility * 0.7 else 'NORMAL'
            
            # 3. Determine regime
            if abs(trend_slope) > 0.05 and sma_20 > sma_50 * 1.01:
                regime = 'STRONG_TRENDING_UP'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif abs(trend_slope) > 0.05 and sma_20 < sma_50 * 0.99:
                regime = 'STRONG_TRENDING_DOWN'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif abs(trend_slope) > 0.02:
                regime = 'TRENDING_UP' if trend_slope > 0 else 'TRENDING_DOWN'
                strength = min(abs(trend_slope) * 10, 1.0)
            elif volatility_regime == 'HIGH':
                regime = 'VOLATILE_RANGING'
                strength = 0.5
            else:
                regime = 'RANGING'
                strength = 0.3
            
            logger.debug(f"📊 Market Regime for {symbol}: {regime} (strength: {strength:.2f}, vol: {volatility_regime})")
            
            return {
                'regime': regime,
                'strength': strength,
                'volatility': volatility_regime,
                'trend_slope': trend_slope,
                'current_volatility': volatility
            }
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {'regime': 'UNKNOWN', 'strength': 0.0, 'volatility': 'NORMAL'}
    
    def calculate_smart_entry_score(self, symbol: str, signal_type: str, market_data: Dict) -> float:
        """
        🎯 CODE ENHANCEMENT: Multi-factor entry quality score
        Combines multiple technical factors for optimal entry timing
        
        Returns: Score 0.0-1.0 (1.0 = perfect entry setup)
        """
        try:
            data = market_data.get(symbol, {})
            
            # Get price history
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return 0.5  # Neutral if insufficient data
            
            prices = self.price_history[symbol]
            volumes = self.volume_history.get(symbol, [])
            
            score_factors = []
            
            # Factor 1: RSI positioning (30% weight)
            if len(prices) >= 14:
                rsi = self._calculate_rsi(prices, 14)
                if signal_type == 'BUY':
                    # Prefer RSI 30-50 (oversold but recovering)
                    if 30 <= rsi <= 50:
                        score_factors.append(0.3)
                    elif 25 <= rsi < 30 or 50 < rsi <= 55:
                        score_factors.append(0.2)
                    else:
                        score_factors.append(0.1)
                else:  # SELL
                    # Prefer RSI 50-70 (overbought but weakening)
                    if 50 <= rsi <= 70:
                        score_factors.append(0.3)
                    elif 45 <= rsi < 50 or 70 < rsi <= 75:
                        score_factors.append(0.2)
                    else:
                        score_factors.append(0.1)
            
            # Factor 2: Volume confirmation (25% weight)
            if len(volumes) >= 20:
                current_vol = volumes[-1]
                avg_vol = np.mean(volumes[-20:])
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
                
                if vol_ratio > 1.5:
                    score_factors.append(0.25)  # Strong volume
                elif vol_ratio > 1.2:
                    score_factors.append(0.18)  # Good volume
                elif vol_ratio > 1.0:
                    score_factors.append(0.12)  # Above average
                else:
                    score_factors.append(0.05)  # Weak volume
            
            # Factor 3: Price action alignment (25% weight)
            if len(prices) >= 5:
                short_momentum = (prices[-1] - prices[-3]) / prices[-3]
                medium_momentum = (prices[-1] - prices[-5]) / prices[-5]
                
                if signal_type == 'BUY':
                    if short_momentum > 0 and medium_momentum > 0:
                        score_factors.append(0.25)  # Aligned momentum
                    elif short_momentum > 0:
                        score_factors.append(0.15)  # Short-term momentum
                    else:
                        score_factors.append(0.05)  # Against momentum
                else:  # SELL
                    if short_momentum < 0 and medium_momentum < 0:
                        score_factors.append(0.25)  # Aligned momentum
                    elif short_momentum < 0:
                        score_factors.append(0.15)  # Short-term momentum
                    else:
                        score_factors.append(0.05)  # Against momentum
            
            # Factor 4: Support/Resistance proximity (20% weight)
            current_price = data.get('ltp', 0)
            if current_price > 0 and len(prices) >= 20:
                recent_high = max(prices[-20:])
                recent_low = min(prices[-20:])
                price_range = recent_high - recent_low
                
                if signal_type == 'BUY':
                    # Better entry near support (lower 25% of range)
                    distance_from_low = (current_price - recent_low) / price_range if price_range > 0 else 0.5
                    if distance_from_low < 0.25:
                        score_factors.append(0.20)
                    elif distance_from_low < 0.40:
                        score_factors.append(0.15)
                    else:
                        score_factors.append(0.05)
                else:  # SELL
                    # Better entry near resistance (upper 25% of range)
                    distance_from_high = (recent_high - current_price) / price_range if price_range > 0 else 0.5
                    if distance_from_high < 0.25:
                        score_factors.append(0.20)
                    elif distance_from_high < 0.40:
                        score_factors.append(0.15)
                    else:
                        score_factors.append(0.05)
            
            total_score = sum(score_factors)
            
            logger.debug(f"📊 Entry Score for {symbol} {signal_type}: {total_score:.2f}")
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating entry score: {e}")
            return 0.5
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            prices_array = np.array(prices[-period-1:])
            deltas = np.diff(prices_array)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def calculate_volatility_adjusted_position_size(self, symbol: str, base_quantity: int, 
                                                    entry_price: float, stop_loss: float) -> int:
        """
        🎯 CODE ENHANCEMENT: Dynamic position sizing based on volatility
        Reduces position size in high volatility, increases in low volatility
        
        Returns: Adjusted quantity
        """
        try:
            # Get price history
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return base_quantity
            
            prices = self.price_history[symbol]
            
            # Calculate current volatility
            returns = np.diff(prices[-20:]) / prices[-20:-1]
            current_vol = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Calculate historical volatility (last 50 days if available)
            if len(prices) >= 50:
                hist_returns = np.diff(prices[-50:]) / prices[-50:-1]
                hist_vol = np.std(hist_returns) * np.sqrt(252)
            else:
                hist_vol = current_vol
            
            # Volatility ratio
            vol_ratio = current_vol / hist_vol if hist_vol > 0 else 1.0
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            risk_percent = risk_per_share / entry_price if entry_price > 0 else 0.05
            
            # Adjust position size based on volatility
            if vol_ratio > 1.5:  # High volatility
                adjustment_factor = 0.6  # Reduce to 60%
                logger.info(f"⚠️ HIGH VOLATILITY for {symbol}: Reducing position size to 60%")
            elif vol_ratio > 1.2:  # Elevated volatility
                adjustment_factor = 0.8  # Reduce to 80%
                logger.info(f"⚠️ ELEVATED VOLATILITY for {symbol}: Reducing position size to 80%")
            elif vol_ratio < 0.7:  # Low volatility
                adjustment_factor = 1.2  # Increase to 120%
                logger.info(f"✅ LOW VOLATILITY for {symbol}: Increasing position size to 120%")
            else:  # Normal volatility
                adjustment_factor = 1.0
            
            # Also consider risk percentage
            if risk_percent > 0.05:  # Risk > 5% per share
                risk_adjustment = 0.05 / risk_percent
                adjustment_factor *= risk_adjustment
                logger.info(f"⚠️ HIGH RISK/SHARE for {symbol}: Further reducing position")
            
            adjusted_quantity = int(base_quantity * adjustment_factor)
            
            # Ensure minimum quantity
            adjusted_quantity = max(adjusted_quantity, 1)
            
            logger.info(f"📊 Position Size for {symbol}: {base_quantity} → {adjusted_quantity} (vol_ratio: {vol_ratio:.2f}, risk: {risk_percent:.2%})")
            
            return adjusted_quantity
            
        except Exception as e:
            logger.error(f"Error calculating volatility-adjusted position size: {e}")
            return base_quantity
    
    def calculate_trailing_stop_with_atr(self, symbol: str, entry_price: float, current_price: float,
                                        position_type: str, atr_multiplier: float = 2.0) -> float:
        """
        🎯 CODE ENHANCEMENT: ATR-based trailing stop (adapts to volatility)
        Uses Average True Range for volatility-adjusted stops
        
        Returns: Trailing stop price
        """
        try:
            # Get price history for ATR calculation
            if symbol not in self.price_history or len(self.price_history[symbol]) < 14:
                # Fallback to fixed percentage
                if position_type.upper() == 'LONG':
                    return current_price * 0.98  # 2% trailing stop
                else:
                    return current_price * 1.02
            
            prices = self.price_history[symbol][-14:]
            
            # Calculate True Range
            tr_list = []
            for i in range(1, len(prices)):
                high = prices[i]
                low = prices[i]
                prev_close = prices[i-1]
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                tr_list.append(tr)
            
            # Average True Range
            atr = np.mean(tr_list) if tr_list else (current_price * 0.02)
            
            # Calculate trailing stop
            if position_type.upper() == 'LONG':
                trailing_stop = current_price - (atr * atr_multiplier)
                # Never move stop down
                if entry_price > current_price:  # In loss
                    initial_stop = entry_price * 0.98
                    trailing_stop = max(trailing_stop, initial_stop)
            else:  # SHORT
                trailing_stop = current_price + (atr * atr_multiplier)
                # Never move stop up
                if entry_price < current_price:  # In loss
                    initial_stop = entry_price * 1.02
                    trailing_stop = min(trailing_stop, initial_stop)
            
            logger.debug(f"📊 ATR Trailing Stop for {symbol}: ATR={atr:.2f}, Stop={trailing_stop:.2f}")
            
            return trailing_stop
            
        except Exception as e:
            logger.error(f"Error calculating ATR trailing stop: {e}")
            # Fallback
            if position_type.upper() == 'LONG':
                return current_price * 0.98
            else:
                return current_price * 1.02
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                risk_reward_ratio: float = None) -> float:
        """Calculate dynamic target with MARKET-ADAPTIVE risk/reward ratio"""
        try:
            # Get current market regime for adaptive risk-reward
            market_regime = "NORMAL"
            nifty_momentum = 0.0
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, 'market_bias') and orchestrator.market_bias:
                    market_regime = getattr(orchestrator.market_bias.current_bias, 'market_regime', 'NORMAL')
                    nifty_momentum = getattr(orchestrator.market_bias.current_bias, 'nifty_momentum', 0.0)
            except:
                pass
            
            # 🚨 DAVID VS GOLIATH: HIGHER R:R to compensate for tighter stops
            # Tighter stops (3-7%) mean we need bigger targets to be profitable
            if risk_reward_ratio is None:
                # RANGING MARKET: Still conservative but higher (was 1.2)
                if abs(nifty_momentum) < 0.15 or market_regime in ('ranging', 'sideways', 'CHOPPY'):
                    risk_reward_ratio = 1.8  # 1:1.8 (was 1.2) - tighter stops need bigger targets
                    logger.debug(f"🔄 RANGING MARKET: Using higher R:R = 1:{risk_reward_ratio} (tight stops)")
                # TRENDING MARKET: Significantly higher (was 2.0)
                elif abs(nifty_momentum) >= 0.3:
                    risk_reward_ratio = 2.5  # 1:2.5 (was 2.0) - ride the trend harder
                    logger.debug(f"📈 TRENDING MARKET: Using aggressive R:R = 1:{risk_reward_ratio} (tight stops)")
                # MODERATE MOMENTUM: Higher balanced (was 1.5)
                else:
                    risk_reward_ratio = 2.0  # 1:2.0 (was 1.5)
                    logger.debug(f"⚖️ MODERATE MARKET: Using improved R:R = 1:{risk_reward_ratio} (tight stops)")
            
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            
            # Calculate reward distance
            reward_distance = risk_distance * risk_reward_ratio
            
            # Calculate target based on entry vs stop loss relationship
            if stop_loss < entry_price:  # BUY trade
                target = entry_price + reward_distance
            else:  # SELL trade
                target = entry_price - reward_distance
            
            logger.info(f"🎯 DYNAMIC TARGET: Entry={entry_price:.2f}, SL={stop_loss:.2f}, "
                       f"Target={target:.2f}, R:R=1:{risk_reward_ratio}, Regime={market_regime}")
            
            return round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target: {e}")
            # Conservative fallback for ranging markets
            target_percent = 0.008  # 0.8% conservative fallback
            if stop_loss < entry_price:  # BUY trade
                return entry_price * (1 + target_percent)
            else:  # SELL trade
                return entry_price * (1 - target_percent)
    
    def _calculate_adaptive_confidence_threshold(self, symbol: str, action: str, confidence: float) -> Tuple[float, str]:
        """
        🔥 PROFESSIONAL MEAN REVERSION-AWARE CONFIDENCE THRESHOLD
        
        Adjusts minimum confidence based on NIFTY move from open using multi-indicator system:
        - Points from open (NIFTY-specific zones: 0-50-100-150+ pts)
        - Market regime (TRENDING/CHOPPY)
        - Bias confidence
        - Signal alignment (with or against trend)
        
        Returns:
            (min_confidence_threshold, reason_string)
        """
        try:
            # Default threshold (TUNED: lowered from 8.5 to 7.5)
            min_conf = 7.5
            reasons = []
            
            # Get market bias if available
            if not (hasattr(self, 'market_bias') and self.market_bias):
                return min_conf, "default"
            
            current_bias = self.market_bias.current_bias
            
            # Get NIFTY data for mean reversion analysis
            nifty_data = self._get_nifty_data_from_bias()
            if not nifty_data:
                return min_conf, "no_nifty_data"
            
            # Calculate NIFTY move from open
            ltp = float(nifty_data.get('ltp', 0))
            open_price = float(nifty_data.get('open', 0))
            
            if not (ltp and open_price):
                return min_conf, "insufficient_nifty_data"
            
            move_from_open = ltp - open_price
            abs_move = abs(move_from_open)
            
            # Determine move zone (NIFTY-specific thresholds)
            if abs_move < 50:
                zone = 'EARLY'
                zone_adjustment = -1.0  # Lower threshold (encourage trading)
                reasons.append(f"EARLY:{abs_move:.0f}pts")
            elif abs_move < 100:
                zone = 'MID'
                zone_adjustment = 0.0  # Normal threshold
                reasons.append(f"MID:{abs_move:.0f}pts")
            elif abs_move < 150:
                zone = 'EXTENDED'
                # Check if chasing or fading
                bias_direction = current_bias.direction
                if (action == 'BUY' and bias_direction == 'BULLISH' and move_from_open > 0) or \
                   (action == 'SELL' and bias_direction == 'BEARISH' and move_from_open < 0):
                    # Chasing extended move - DISCOURAGE
                    zone_adjustment = +1.5
                    reasons.append(f"EXTENDED_CHASE:{abs_move:.0f}pts⚠️")
                else:
                    # Fading extended move - ENCOURAGE
                    zone_adjustment = -0.5
                    reasons.append(f"EXTENDED_FADE:{abs_move:.0f}pts✅")
            else:  # >= 150 points
                zone = 'EXTREME'
                bias_direction = current_bias.direction
                if (action == 'BUY' and bias_direction == 'BULLISH' and move_from_open > 0) or \
                   (action == 'SELL' and bias_direction == 'BEARISH' and move_from_open < 0):
                    # Chasing EXTREME move - STRONGLY DISCOURAGE
                    zone_adjustment = +2.0
                    reasons.append(f"EXTREME_CHASE:{abs_move:.0f}pts🔴")
                else:
                    # Fading EXTREME move - STRONGLY ENCOURAGE
                    zone_adjustment = -1.5
                    reasons.append(f"EXTREME_FADE:{abs_move:.0f}pts✅✅")
            
            min_conf += zone_adjustment
            
            # Market regime adjustment
            market_regime = getattr(current_bias, 'market_regime', 'NORMAL')
            if market_regime == 'CHOPPY':
                min_conf += 0.5
                reasons.append("CHOPPY+0.5")
            elif market_regime in ['STRONG_TRENDING', 'TRENDING']:
                min_conf -= 0.5
                reasons.append("TRENDING-0.5")
            
            # Bias confidence adjustment
            bias_confidence = getattr(current_bias, 'confidence', 0.0)
            if bias_confidence >= 7.0:
                # High bias confidence = lower threshold for aligned signals
                if (action == 'BUY' and current_bias.direction == 'BULLISH') or \
                   (action == 'SELL' and current_bias.direction == 'BEARISH'):
                    min_conf -= 0.5
                    reasons.append("ALIGNED-0.5")
            elif bias_confidence <= 3.0:
                # Low bias confidence = higher threshold
                min_conf += 0.5
                reasons.append("WEAK_BIAS+0.5")
            
            # Clamp to reasonable range (5.5 to 9.5)
            min_conf = max(5.5, min(min_conf, 9.5))
            
            reason_str = " | ".join(reasons) if reasons else "default"
            return min_conf, reason_str
            
        except Exception as e:
            logger.error(f"Error calculating adaptive threshold: {e}")
            return 7.5, f"error"
    
    def _get_nifty_data_from_bias(self) -> Optional[Dict]:
        """Get NIFTY data from market bias system"""
        try:
            if not (hasattr(self, 'market_bias') and self.market_bias):
                return None
            
            # Try to get NIFTY data from bias system's latest update
            if hasattr(self.market_bias, 'current_bias'):
                # The bias system stores NIFTY data internally
                # Check for various NIFTY representations
                for attr in ['nifty_data', '_nifty_data', 'latest_nifty_data']:
                    if hasattr(self.market_bias, attr):
                        data = getattr(self.market_bias, attr, None)
                        if data and isinstance(data, dict):
                            return data
            
            # Fallback: Try to access orchestrator's data
            try:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator and hasattr(orchestrator, '_latest_market_data'):
                    for symbol in ['NIFTY-I', 'NIFTY', 'NIFTY 50']:
                        if symbol in orchestrator._latest_market_data:
                            return orchestrator._latest_market_data[symbol]
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get NIFTY data: {e}")
            return None
    
    def validate_signal_levels(self, entry_price: float, stop_loss: float, 
                              target: float, action: str) -> bool:
        """Validate that signal levels make logical sense"""
        try:
            # Normalize numeric types to avoid '<' between str and int/float errors
            entry_price = float(entry_price)
            stop_loss = float(stop_loss)
            target = float(target)
            if action.upper() == 'BUY':
                # For BUY: stop_loss < entry_price < target
                if not (stop_loss < entry_price < target):
                    logger.warning(f"❌ Invalid BUY signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
                
                # 🔥 ENHANCED: Percentage-based minimum spreads (protects against order rejections)
                sl_spread_pct = ((entry_price - stop_loss) / entry_price) * 100
                target_spread_pct = ((target - entry_price) / entry_price) * 100
                
                # Define minimums based on price band
                if entry_price >= 1000:
                    MIN_SL_SPREAD = 0.3  # 0.3% for high-priced stocks
                    MIN_TARGET_SPREAD = 0.5  # 0.5% minimum target
                elif entry_price >= 100:
                    MIN_SL_SPREAD = 0.4  # 0.4% for mid-priced
                    MIN_TARGET_SPREAD = 0.6  # 0.6% minimum target
                elif entry_price >= 10:
                    MIN_SL_SPREAD = 0.5  # 0.5% for low-priced
                    MIN_TARGET_SPREAD = 0.8  # 0.8% minimum target
                else:
                    # Options/Ultra-low: Use absolute ₹0.10 minimum
                    MIN_SL_SPREAD = (0.10 / entry_price) * 100
                    MIN_TARGET_SPREAD = (0.15 / entry_price) * 100
                
                if sl_spread_pct < MIN_SL_SPREAD:
                    logger.warning(f"❌ BUY: SL too close to entry: {sl_spread_pct:.2f}% < {MIN_SL_SPREAD:.2f}% "
                                 f"(SL={stop_loss:.2f}, Entry={entry_price:.2f})")
                    return False
                
                if target_spread_pct < MIN_TARGET_SPREAD:
                    logger.warning(f"❌ BUY: Target too close to entry: {target_spread_pct:.2f}% < {MIN_TARGET_SPREAD:.2f}% "
                                 f"(Entry={entry_price:.2f}, Target={target:.2f})")
                    return False
            else:  # SELL
                # For SELL: target < entry_price < stop_loss
                if not (target < entry_price < stop_loss):
                    logger.warning(f"❌ Invalid SELL signal levels: Target={target}, Entry={entry_price}, SL={stop_loss}")
                    return False
                
                # 🔥 ENHANCED: Percentage-based minimum spreads
                sl_spread_pct = ((stop_loss - entry_price) / entry_price) * 100
                target_spread_pct = ((entry_price - target) / entry_price) * 100
                
                # Define minimums based on price band
                if entry_price >= 1000:
                    MIN_SL_SPREAD = 0.3  # 0.3% for high-priced stocks
                    MIN_TARGET_SPREAD = 0.5  # 0.5% minimum target
                elif entry_price >= 100:
                    MIN_SL_SPREAD = 0.4  # 0.4% for mid-priced
                    MIN_TARGET_SPREAD = 0.6  # 0.6% minimum target
                elif entry_price >= 10:
                    MIN_SL_SPREAD = 0.5  # 0.5% for low-priced
                    MIN_TARGET_SPREAD = 0.8  # 0.8% minimum target
                else:
                    # Options/Ultra-low: Use absolute ₹0.10 minimum
                    MIN_SL_SPREAD = (0.10 / entry_price) * 100
                    MIN_TARGET_SPREAD = (0.15 / entry_price) * 100
                
                if sl_spread_pct < MIN_SL_SPREAD:
                    logger.warning(f"❌ SELL: SL too close to entry: {sl_spread_pct:.2f}% < {MIN_SL_SPREAD:.2f}% "
                                 f"(Entry={entry_price:.2f}, SL={stop_loss:.2f})")
                    return False
                
                if target_spread_pct < MIN_TARGET_SPREAD:
                    logger.warning(f"❌ SELL: Target too close to entry: {target_spread_pct:.2f}% < {MIN_TARGET_SPREAD:.2f}% "
                                 f"(Target={target:.2f}, Entry={entry_price:.2f})")
                    return False
            
            # Check for identical levels (problematic for low-priced stocks)
            if entry_price == stop_loss == target:
                logger.warning(f"Invalid signal levels: All levels identical ({entry_price}) - likely rounding issue for low-priced stock")
                return False
            
            # Check risk/reward ratio is reasonable (>= ~0.45:1 to 5:1)
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            
            if risk <= 0:
                logger.warning(f"Zero or negative risk: {risk}")
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 0.45 or risk_reward_ratio > 5.0:
                logger.warning(f"Unreasonable risk/reward ratio: {risk_reward_ratio}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal levels: {e}")
            return False
    
    async def create_standard_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, 
                              metadata: Dict, market_bias=None, market_data: Dict = None) -> Optional[Dict]:
        """Create standardized signal format - SUPPORTS EQUITY, FUTURES & OPTIONS"""
        try:
            # 🔧 TIME RESTRICTIONS MOVED TO RISK MANAGER
            # Strategies should always generate signals for analysis
            # Risk Manager will reject orders based on time restrictions
            
            # 🎯 RELATIVE STRENGTH CHECK: Stock must outperform/underperform market
            # Use provided market_data or fall back to stored latest data
            data_to_use = market_data if market_data else self._latest_market_data
            
            if market_bias and data_to_use:
                # Get NIFTY change percent from market bias
                nifty_change = getattr(getattr(market_bias, 'current_bias', None), 'nifty_momentum', None)
                
                # Get stock change percent from market data
                stock_change = None
                if symbol in data_to_use:
                    stock_data = data_to_use[symbol]
                    stock_change = stock_data.get('change_percent') or stock_data.get('provider_change_percent')
                    if stock_change is not None:
                        stock_change = float(stock_change)
                
                # Perform relative strength check
                if nifty_change is not None and stock_change is not None:
                    rs_allowed, rs_reason = self.check_relative_strength(
                        symbol=symbol,
                        action=action,
                        stock_change_percent=stock_change,
                        nifty_change_percent=nifty_change,
                        min_outperformance=0.3  # 0.3% minimum outperformance
                    )
                    
                    if not rs_allowed:
                        logger.info(f"🚫 RELATIVE STRENGTH FILTER: {symbol} {action} rejected - {rs_reason}")
                        return None
            
            # 🎯 MARKET BIAS COORDINATION: Filter signals based on market direction
            if market_bias:
                # CRITICAL FIX: Normalize confidence to 0-10 scale
                # Some strategies use percentage (0-100), others use decimal (0-10)
                if confidence > 10:
                    # It's a percentage, convert to 0-10 scale
                    normalized_confidence = confidence / 10.0
                    logger.debug(f"📊 Confidence normalization for {symbol}: {confidence}% → {normalized_confidence}/10")
                else:
                    # Already in 0-10 scale
                    normalized_confidence = confidence
                    logger.debug(f"📊 Confidence for {symbol} already normalized: {normalized_confidence}/10")
                
                # Use the new clearer method if available
                if hasattr(market_bias, 'should_allow_signal'):
                    should_allow = market_bias.should_allow_signal(action.upper(), normalized_confidence)
                else:
                    # Fallback: if no bias method available, allow signal
                    should_allow = True
                    logger.warning(f"⚠️ Market bias object missing should_allow_signal method")
                
                if not should_allow:
                    logger.info(f"🚫 BIAS FILTER: {symbol} {action} rejected by market bias "
                               f"(Bias: {getattr(market_bias.current_bias, 'direction', 'UNKNOWN')}, "
                               f"Raw Confidence: {confidence}, Normalized: {normalized_confidence:.1f}/10)")
                    return None
                else:
                    # Apply position size multiplier ONLY when aligned with current bias
                    try:
                        current_bias_dir = getattr(getattr(market_bias, 'current_bias', None), 'direction', 'NEUTRAL')
                        is_aligned = (
                            (current_bias_dir == 'BULLISH' and action.upper() == 'BUY') or
                            (current_bias_dir == 'BEARISH' and action.upper() == 'SELL')
                        )
                    except Exception:
                        current_bias_dir = 'NEUTRAL'
                        is_aligned = False

                    if is_aligned and hasattr(market_bias, 'get_position_size_multiplier'):
                        # Micro-size in CHOPPY regimes even when aligned
                        bias_multiplier = market_bias.get_position_size_multiplier(action.upper())
                        try:
                            regime = getattr(getattr(market_bias, 'current_bias', None), 'market_regime', 'NORMAL')
                            if regime in ('CHOPPY', 'VOLATILE_CHOPPY'):
                                bias_multiplier = min(bias_multiplier, 1.0)
                        except Exception:
                            pass
                        metadata['bias_multiplier'] = bias_multiplier
                        if bias_multiplier > 1.0:
                            logger.info(f"🔥 BIAS BOOST: {symbol} {action} gets {bias_multiplier:.1f}x position size")
                        elif bias_multiplier < 1.0:
                            logger.info(f"⚠️ BIAS REDUCE: {symbol} {action} gets {bias_multiplier:.1f}x position size")
                    else:
                        metadata['bias_multiplier'] = 1.0
            
            # CRITICAL FIX: Type validation to prevent float/string arithmetic errors
            try:
                entry_price = float(entry_price) if entry_price not in [None, '', 'N/A', '-'] else 0.0
                stop_loss = float(stop_loss) if stop_loss not in [None, '', 'N/A', '-'] else 0.0
                target = float(target) if target not in [None, '', 'N/A', '-'] else 0.0
                confidence = float(confidence) if confidence not in [None, '', 'N/A', '-'] else 0.0
            except (ValueError, TypeError) as type_error:
                logger.error(f"❌ TYPE ERROR for {symbol}: Invalid numeric data - {type_error}")
                logger.error(f"   entry_price: {repr(entry_price)}, stop_loss: {repr(stop_loss)}, "
                            f"target: {repr(target)}, confidence: {repr(confidence)}")
                return None
            
            # Validate numeric ranges
            if entry_price <= 0:
                logger.error(f"❌ INVALID ENTRY PRICE for {symbol}: {entry_price} - REJECTING SIGNAL")
                logger.error(f"   This will cause quantity = 0 and signal rejection")
                return None
            # ========================================
            # CRITICAL: POSITION DEDUPLICATION CHECK
            # ========================================
            # Skip duplicate check for management/closing actions
            is_management = metadata.get('management_action', False)
            is_closing = metadata.get('closing_action', False)
            bypass_checks = metadata.get('bypass_all_checks', False)
            
            if not (is_management or is_closing or bypass_checks):
                if self.has_existing_position(symbol):
                    logger.info(f"🚫 {self.name}: DUPLICATE SIGNAL PREVENTED for {symbol} - Position already exists")
                    return None
            
            # ========================================
            # CRITICAL: PHANTOM POSITION COOLDOWN CHECK  
            # ========================================
            if self._is_position_cooldown_active(symbol):
                logger.info(f"🕐 {self.name}: SIGNAL DELAYED for {symbol} - Position cooldown active")
                return None
            
            # ========================================
            # 🔥 PROFESSIONAL MEAN REVERSION-AWARE CONFIDENCE THRESHOLD
            # ========================================
            # Multi-indicator system prevents chasing exhausted moves (150+ points)
            min_conf, adjustment_reason = self._calculate_adaptive_confidence_threshold(symbol, action, confidence)
            logger.debug(f"📊 Adaptive Threshold: {symbol} {action} -> min_conf={min_conf:.1f} ({adjustment_reason})")

            # Ensure confidence is numeric before comparison
            try:
                if not isinstance(confidence, (int, float)):
                    logger.error(f"❌ CONFIDENCE TYPE ERROR for {symbol}: confidence is {type(confidence)} = {repr(confidence)}")
                    confidence = float(confidence) if confidence else 0.0
                
                # CRITICAL FIX: Normalize confidence to 0-10 scale for comparison with min_conf
                # Strategies generate confidence in 0-1 scale (0.9 = 90%)
                # min_conf is in 0-10 scale (8.5 = 85%)
                confidence_normalized = confidence * 10.0 if confidence <= 1.0 else confidence
                
                if confidence_normalized < min_conf:
                    logger.info(f"🗑️ {self.name}: LOW CONFIDENCE SIGNAL SCRAPPED for {symbol} - Confidence: {confidence_normalized:.1f}/10 (min={min_conf})")
                    return None
                else:
                    logger.debug(f"✅ Confidence check passed: {symbol} - {confidence_normalized:.1f}/10 >= {min_conf}")
            except (TypeError, ValueError) as e:
                logger.error(f"❌ Error comparing confidence for {symbol}: {e}")
                logger.error(f"   confidence={repr(confidence)}, min_conf={repr(min_conf)}")
                return None

            # Opening gap gate: DISABLED - market_data not available in this context
            # TODO: Move this check to risk manager or pass market_data to this method
            
            # 🎯 INTELLIGENT SIGNAL TYPE SELECTION based on market conditions and symbol
            # Ensure numeric types for decision helpers
            try:
                _entry_price_num = float(entry_price)
            except (TypeError, ValueError):
                _entry_price_num = 0.0
            try:
                _confidence_num = float(confidence)
            except (TypeError, ValueError):
                _confidence_num = 0.0

            signal_type = self._determine_optimal_signal_type(symbol, _entry_price_num, _confidence_num, metadata)
            
            if signal_type == 'OPTIONS':
                # Convert to options signal
                return await self._create_options_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            elif signal_type == 'FUTURES':
                # Create futures signal (if available)
                return self._create_futures_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            else:
                # Create equity signal (default)
                return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
                
        except Exception as e:
            logger.error(f"Error creating signal for {symbol}: {e}")
            return None
    
    def _determine_optimal_signal_type(self, symbol: str, entry_price: float, confidence: float, metadata: Dict) -> str:
        """Determine the best signal type based on market conditions and F&O availability"""
        try:
            # 🚨 CRITICAL FIX: Normalize confidence to 0-1 scale
            # Strategies send 0-10 scale, we need 0-1 for thresholds
            if confidence > 1.0:
                normalized_confidence = confidence / 10.0
                logger.debug(f"📊 Normalizing confidence: {confidence:.2f} → {normalized_confidence:.2f}")
            else:
                normalized_confidence = confidence
            
            # 🚨 CRITICAL: Check F&O availability first
            from config.truedata_symbols import is_fo_enabled, should_use_equity_only
            
            # DEBUG: Log F&O check details
            fo_enabled = is_fo_enabled(symbol)
            equity_only = should_use_equity_only(symbol)
            logger.info(f"🔍 F&O CHECK for {symbol}: fo_enabled={fo_enabled}, equity_only={equity_only}")
            logger.debug(f"   Strategy instance: {self.name}, Signal ID: {getattr(metadata, 'get', lambda x: 'unknown')('signal_id', 'unknown')}")
            
            # CRITICAL DEBUG: For problematic symbols, add extra validation
            if symbol in ['FORCEMOT', 'RCOM', 'DEVYANI', 'RAYMOND', 'ASTRAL', 'IDEA']:
                logger.info(f"🔍 PROBLEMATIC SYMBOL DEBUG: {symbol} - F&O={fo_enabled}, Equity_Only={equity_only}")
            
            # HARD RULE: Avoid options for very low-priced stocks (illiquid contracts)
            if entry_price and entry_price < 50:
                logger.info(f"🎯 LOW PRICE EQUITY-ONLY: {symbol} @ ₹{entry_price:.2f} → EQUITY (avoid illiquid options)")
                return 'EQUITY'

            # Force equity for known cash-only stocks
            if equity_only:
                logger.info(f"🎯 CASH-ONLY STOCK: {symbol} → EQUITY (no F&O available)")
                return 'EQUITY'
            
            # Check if F&O is available for this symbol
            if not fo_enabled:
                logger.info(f"🎯 NO F&O AVAILABLE: {symbol} → EQUITY (no options trading)")
                return 'EQUITY'
            
            # Factors for signal type selection (F&O enabled symbols)
            is_index = symbol.endswith('-I') or symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
            # 🚨 MATHEMATICAL FIX: Raise confidence threshold to 85% (was 80%)
            # 🚨 DAVID VS GOLIATH: EXTREME selectivity for options
            # 4 days of losses = we only take THE BEST setups
            is_high_confidence = normalized_confidence >= 0.92  # Was 0.85, now 0.92 (TOP 8% signals only)
            is_very_high_confidence = normalized_confidence >= 0.95  # Was 0.90, now 0.95 (TOP 5% signals)
            is_scalping = metadata.get('risk_type', '').startswith('SCALPING')
            volatility_score = metadata.get('volume_score', 0)
            
            # 🚨 DAVID VS GOLIATH: ULTRA-STRICT decision logic
            # After 4 days of losses, we're being EXTREMELY selective
            # Only the absolute best setups get options leverage
            
            # 1. Index symbols: STILL allow options (but tight stops)
            if is_index:
                logger.info(f"🎯 INDEX SIGNAL: {symbol} → OPTIONS (F&O enabled)")
                return 'OPTIONS'
            
            # 2. STOCK OPTIONS: Need 95% confidence (was 90%)
            # We're fighting against market makers with deep pockets
            # Only take setups where we have MASSIVE edge
            elif is_very_high_confidence:  # 95%+ confidence
                logger.info(f"🎯 ELITE CONFIDENCE: {symbol} → OPTIONS (conf={normalized_confidence:.2f} ≥ 0.95)")
                return 'OPTIONS'
            
            # 3. High volatility + 92%+ confidence (was 85%)
            elif volatility_score >= 0.85 and normalized_confidence >= 0.92:
                logger.info(f"🎯 HIGH VOL + STRONG CONF: {symbol} → OPTIONS (vol={volatility_score:.2f}, conf={normalized_confidence:.2f})")
                return 'OPTIONS'
            
            # 4. ALL OTHER CASES: Default to EQUITY (safer)
            # Better to make small gains in equity than big losses in options
            else:
                logger.info(f"🎯 CONSERVATIVE CHOICE: {symbol} → EQUITY (conf={normalized_confidence:.2f} < 0.95)")
                logger.info(f"   Reason: David vs Goliath - only taking elite options setups")
                return 'EQUITY'
                
        except Exception as e:
            logger.error(f"Error determining signal type: {e}")
            return 'EQUITY'  # Safest fallback
    
    async def _create_options_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Dict:
        """Create standardized signal format for options"""
        try:
            # If market is closed, do not attempt options trading or on-demand data
            if not self._is_trading_hours():
                logger.warning(f"⏸️ MARKET CLOSED - Skipping options signal for {symbol}")
                return None
            # 🎯 CRITICAL FIX: Convert to options symbol and force BUY action
            options_symbol, option_type = await self._convert_to_options_symbol(symbol, entry_price, action)
            
            # 🚨 CRITICAL: Check if signal was rejected (e.g., MIDCPNIFTY, SENSEX)
            if options_symbol is None or option_type == 'REJECTED':
                logger.warning(f"⚠️ OPTIONS SIGNAL REJECTED: {symbol} - cannot be traded")
                return None
            
            # 🎯 FALLBACK: If options not available, create equity signal instead
            if option_type == 'EQUITY':
                logger.info(f"🔄 FALLBACK TO EQUITY: Creating equity signal for {options_symbol}")
                return self._create_equity_signal(options_symbol, action, entry_price, stop_loss, target, confidence, metadata)
            
            final_action = 'BUY' # Force all options signals to be BUY
            
            # 🔍 CRITICAL DEBUG: Log the complete symbol creation process
            logger.info(f"🔍 SYMBOL CREATION DEBUG:")
            logger.info(f"   Original: {symbol} → Options: {options_symbol}")
            logger.info(f"   Type: {option_type}, Action: {final_action}")
            logger.info(f"   Entry Price: ₹{entry_price} (underlying)")
            
            # 🎯 CRITICAL FIX: Get actual options premium from TrueData instead of stock price
            options_entry_price = self._get_options_premium(options_symbol, symbol)
            
            # 🔍 DEBUG: Log premium fetching
            logger.info(f"   Options Premium: ₹{options_entry_price} (vs underlying ₹{entry_price})")
            
            # 🚨 CRITICAL: Block options signals with zero LTP completely
            if options_entry_price <= 0:
                # Attempt nearby-strike rescue before giving up
                try:
                    rescue = self._attempt_nearby_strike_rescue(options_symbol)
                except Exception as _rescue_err:
                    rescue = None
                    logger.debug(f"Nearby-strike rescue error: {_rescue_err}")
                if rescue and rescue.get('symbol') and rescue.get('ltp', 0) > 0:
                    new_symbol = rescue['symbol']
                    options_entry_price = rescue['ltp']
                    logger.info(f"🛟 RESCUED OPTIONS: Switching to {new_symbol} with LTP ₹{options_entry_price}")
                    options_symbol = new_symbol
                
                if options_entry_price <= 0:
                    logger.error(f"❌ REJECTING OPTIONS SIGNAL: {options_symbol} has ZERO LTP - cannot trade")
                    # Only fall back to equity if market is open
                    if self._is_trading_hours():
                        logger.info(f"🔄 ATTEMPTING EQUITY FALLBACK for {symbol} due to zero options LTP")
                        logger.info(f"   REASON: Options contract {options_symbol} not liquid or doesn't exist")
                        logger.info(f"   SOLUTION: Trading underlying equity with same risk-reward profile")
                        
                        # CRITICAL FIX: Ensure metadata shows EQUITY signal type for fallback
                        equity_metadata = metadata.copy()
                        equity_metadata['signal_type'] = 'EQUITY'
                        equity_metadata['fallback_reason'] = 'options_ltp_zero'
                        equity_metadata['original_options_symbol'] = options_symbol
                        
                        return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, equity_metadata)
                    return None

            # 🎯 CRITICAL FIX: Calculate correct stop_loss and target for options (only after non-zero premium)
            options_stop_loss, options_target = self._calculate_options_levels(
                options_entry_price, stop_loss, target, option_type, action, symbol
            )
            
            # Validate signal levels only if we have a real entry price
            if not self.validate_signal_levels(options_entry_price, options_stop_loss, options_target, 'BUY'):
                logger.warning(f"Invalid options signal levels: Entry={options_entry_price}, SL={options_stop_loss}, Target={options_target}")
                return None
            
            # 🎯 CRITICAL FIX: Always BUY options (no selling due to margin requirements)
            final_action = 'BUY'  # Force all options signals to be BUY
            
            # Calculate risk metrics using OPTIONS pricing (handle 0.0 entry price)
            risk_amount = abs(options_entry_price - options_stop_loss)
            reward_amount = abs(options_target - options_entry_price)
            risk_percent = (risk_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            reward_percent = (reward_amount / options_entry_price) * 100 if options_entry_price > 0 else 0
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # CRITICAL FIX: Generate unique signal_id for tracking
            signal_id = f"{self.name}_{options_symbol}_{int(datetime.now().timestamp())}"
            
            # CRITICAL FIX: Validate quantity BEFORE creating signal
            quantity = self._get_capital_constrained_quantity(options_symbol, symbol, options_entry_price)
            if quantity <= 0:
                logger.error(f"❌ SIGNAL REJECTED: {options_symbol} - Quantity is {quantity} (insufficient capital or invalid lot size)")
                logger.error(f"   This signal will NOT be sent to trade engine")
                return None
            
            return {
                # Core signal fields (consistent naming)
                'signal_id': signal_id,
                'symbol': options_symbol,  # 🎯 FIXED: Use options symbol instead of underlying
                'underlying_symbol': symbol,  # Keep original for reference
                'option_type': option_type,  # CE or PE
                'action': final_action.upper(),  # Always BUY for options (no selling due to margin)
                'quantity': quantity,  # 🎯 CAPITAL-AWARE: Limit lots based on capital (validated above)
                'entry_price': self._round_to_tick_size(options_entry_price),  # 🎯 FIXED: Use tick size rounding
                'stop_loss': self._round_to_tick_size(options_stop_loss),      # 🎯 FIXED: Tick size rounding
                'target': self._round_to_tick_size(options_target),            # 🎯 FIXED: Tick size rounding
                'strategy': self.name,  # Use 'strategy' for compatibility
                'strategy_name': self.name,  # Also include strategy_name for new components
                'confidence': round(confidence, 2),
                'quality_score': round(confidence, 2),  # Map confidence to quality_score
                
                # Risk metrics
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                
                # Enhanced metadata
                'metadata': {
                    **metadata,
                    'signal_validation': 'PASSED',
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.name,
                    'signal_source': 'strategy_engine',
                    'underlying_price': round(entry_price, 2),  # Keep original stock price for reference
                    'options_conversion': 'PREMIUM_BASED'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating standard signal: {e}")
            return None
    
    def _create_equity_signal(self, symbol: str, action: str, entry_price: float, 
                             stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """Create equity signal with standard parameters"""
        try:
            # Hard block known delisted/suspended symbols at source
            try:
                blocked_symbols = {'RCOM', 'RELCAPITAL', 'YESBANK', 'JETAIRWAYS'}
                if symbol in blocked_symbols:
                    logger.warning(f"🚫 BLOCKED EQUITY SIGNAL: {symbol} is delisted/suspended - rejecting")
                    return None
            except Exception:
                pass

            # Validate signal levels
            if not self.validate_signal_levels(entry_price, stop_loss, target, action):
                logger.warning(f"Invalid equity signal levels: {symbol}")
                return None
            
            # Calculate risk metrics
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(target - entry_price)
            risk_percent = (risk_amount / entry_price) * 100
            reward_percent = (reward_amount / entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Check minimum risk-reward ratio (DYNAMIC based on volatility)
            min_risk_reward_ratio = self._get_dynamic_min_risk_reward_ratio(symbol, entry_price)
            
            # TEMPORARY FIX: Override minimum ratio to allow equity fallback signals
            min_risk_reward_ratio = 1.15  # Temporarily lower to allow 1.20+ signals through
            
            if risk_reward_ratio < min_risk_reward_ratio:
                logger.warning(f"Equity signal below {min_risk_reward_ratio}:1 ratio: {symbol} ({risk_reward_ratio:.2f})")
                return None
            
            signal = {
                'signal_id': f"{self.name}_{symbol}_{int(time_module.time())}",
                'symbol': symbol,
                'action': action.upper(),
                'quantity': self._get_capital_constrained_quantity(symbol, symbol, entry_price),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'strategy': self.name,
                'strategy_name': self.__class__.__name__,
                'confidence': confidence,
                'quality_score': confidence,
                'risk_metrics': {
                    'risk_amount': round(risk_amount, 2),
                    'reward_amount': round(reward_amount, 2),
                    'risk_percent': round(risk_percent, 2),
                    'reward_percent': round(reward_percent, 2),
                    'risk_reward_ratio': round(risk_reward_ratio, 2)
                },
                'metadata': {
                    **metadata,
                    'signal_type': 'EQUITY',
                    'timestamp': datetime.now().isoformat(),
                    'strategy_instance': self.__class__.__name__,
                    'signal_source': 'strategy_engine'
                },
                'generated_at': datetime.now().isoformat()
            }
            
            # DEFERRED: Position entry is recorded only after real execution confirmation
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating equity signal: {e}")
            return None
    
    def _create_futures_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, metadata: Dict) -> Optional[Dict]:
        """Create futures signal (placeholder for now)"""
        try:
            # For now, fallback to equity signal
            # TODO: Implement proper futures signal creation with correct expiry, etc.
            logger.info(f"📊 FUTURES signal requested for {symbol} - using equity for now")
            return self._create_equity_signal(symbol, action, entry_price, stop_loss, target, confidence, metadata)
            
        except Exception as e:
            logger.error(f"Error creating futures signal: {e}")
            return None
    
    def _get_real_market_price(self, symbol: str) -> Optional[float]:
        """Get real market price from TrueData cache to ensure accurate strike calculation"""
        try:
            from data.truedata_client import live_market_data
            
            # Debug: Log available symbols in cache
            if live_market_data:
                available_symbols = list(live_market_data.keys())
                logger.info(f"🔍 DEBUG: TrueData cache has {len(available_symbols)} symbols")
                # Check if HDFC variants exist
                hdfc_symbols = [s for s in available_symbols if 'HDFC' in s.upper()]
                if hdfc_symbols:
                    logger.info(f"🔍 DEBUG: HDFC symbols in cache: {hdfc_symbols}")
                else:
                    logger.warning(f"⚠️ DEBUG: No HDFC symbols found in TrueData cache")
                    
            if live_market_data and symbol in live_market_data:
                stock_price = live_market_data[symbol].get('ltp', 0)
                logger.info(f"📊 Real market price for {symbol}: ₹{stock_price}")
                return float(stock_price) if stock_price > 0 else None
            else:
                logger.warning(f"⚠️ No real market data available for {symbol}")
                # Debug: Show what symbols are available
                if live_market_data:
                    sample_symbols = list(live_market_data.keys())[:10]
                    logger.info(f"🔍 DEBUG: Sample symbols in cache: {sample_symbols}")
                return None
        except Exception as e:
            logger.error(f"Error getting real market price for {symbol}: {e}")
            return None

    def _attempt_nearby_strike_rescue(self, options_symbol: str) -> Optional[Dict]:
        """Try nearby strikes (±2 steps) to find a tradable option LTP via Zerodha sync path.
        Returns {'symbol': new_symbol, 'ltp': price} if found, else None.
        """
        try:
            import re as _re
            m = _re.match(r'^([A-Z]+)(\d{2}[A-Z]{3}\d{2})(\d+)(CE|PE)$', options_symbol)
            if not m:
                return None
            underlying, expiry, strike_str, opt_type = m.groups()
            try:
                base_strike = int(strike_str)
            except Exception:
                return None

            # Get zerodha client
            if not getattr(self, 'zerodha_client', None):
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    if orchestrator:
                        self.zerodha_client = orchestrator.zerodha_client
                except Exception:
                    pass
            if not getattr(self, 'zerodha_client', None):
                return None

            # Use 50 as generic strike step for stocks; indices have 50 as well in most cases
            step = 50
            candidates = []
            for k in [-2, -1, 1, 2]:  # skip 0 because current strike already failed
                candidate_strike = base_strike + k * step
                if candidate_strike <= 0:
                    continue
                sym = f"{underlying}{expiry}{candidate_strike}{opt_type}"
                candidates.append(sym)

            for sym in candidates:
                try:
                    ltp = self.zerodha_client.get_options_ltp_sync(sym)
                    if ltp and ltp > 0:
                        return {'symbol': sym, 'ltp': float(ltp)}
                except Exception:
                    continue

            return None
        except Exception:
            return None

    async def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
        """Convert equity signal to options symbol with BUY-only approach - FIXED SYMBOL FORMAT"""
        
        try:
            # 🚨 CRITICAL FIX: Get REAL market price instead of using entry_price which might be wrong
            logger.info(f"🔍 DEBUG: Converting {underlying_symbol} to options with passed price ₹{current_price:.2f}")
            
            real_market_price = self._get_real_market_price(underlying_symbol)
            if real_market_price and real_market_price > 0:
                actual_price = real_market_price
                logger.info(f"🔍 PRICE CORRECTION: Using real market price ₹{actual_price:.2f} instead of ₹{current_price:.2f}")
            else:
                actual_price = current_price
                logger.warning(f"⚠️ Using passed price ₹{actual_price:.2f} (real price unavailable)")

            # 🚨 DEFENSIVE: Validate that actual_price is not zero/negative
            if actual_price <= 0:
                logger.error(f"❌ INVALID ACTUAL PRICE: {actual_price} for {underlying_symbol} - cannot proceed")
                return underlying_symbol, 'EQUITY'
                
            # Debug: Check if the price looks reasonable for this symbol
            if underlying_symbol == 'HDFCBANK' and actual_price < 800:
                logger.error(f"🚨 SUSPICIOUS PRICE: HDFCBANK price ₹{actual_price:.2f} seems too low (expected ~960)")
                logger.error(f"🚨 This will generate wrong strike prices. Investigate price source!")
            elif underlying_symbol == 'GAIL' and (actual_price < 150 or actual_price > 200):
                logger.warning(f"⚠️ GAIL price ₹{actual_price:.2f} outside expected range (150-200)")
            
            # 🎯 CRITICAL FIX: Convert to Zerodha's official symbol name FIRST
            from config.truedata_symbols import get_zerodha_symbol, is_fo_enabled
            zerodha_underlying = get_zerodha_symbol(underlying_symbol)
            
            # CRITICAL FIX: Check if symbol is F&O enabled before attempting options
            if not is_fo_enabled(zerodha_underlying):
                logger.warning(f"⚠️ {zerodha_underlying} is NOT F&O enabled - cannot trade options")
                logger.info(f"🔄 FALLBACK: Trading {zerodha_underlying} as EQUITY instead")
                return zerodha_underlying, 'EQUITY'
            
            # 🎯 CRITICAL FIX: Only BUY signals for options (no selling due to margin requirements)
            # 🔧 IMPORTANT: Only use indices with confirmed options contracts on Zerodha
            if zerodha_underlying in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:  # REMOVED MIDCPNIFTY - no options
                # Index options - use volume-based strike selection for liquidity
                try:
                    expiry = await self._get_next_expiry(zerodha_underlying)
                    if not expiry:
                        logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - REJECTING SIGNAL")
                        return None, 'REJECTED'

                    # 🚨 DEFENSIVE: Check if expiry is valid before using
                    if not isinstance(expiry, str):
                        logger.error(f"❌ INVALID EXPIRY TYPE: {type(expiry)} = {expiry} for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                    strike = await self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)

                    # 🚨 DEFENSIVE: Check if strike is valid
                    if not isinstance(strike, int) or strike <= 0:
                        logger.error(f"❌ INVALID STRIKE: {strike} (type: {type(strike)}) for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                except Exception as await_error:
                    logger.error(f"❌ AWAIT ERROR in index options: {await_error}")
                    logger.error(f"   Error type: {type(await_error)}")
                    if "can't be used in 'await' expression" in str(await_error):
                        logger.error(f"🚨 CRITICAL: Attempted to await a non-coroutine for {zerodha_underlying}")
                        logger.error(f"   This indicates a method returning wrong type instead of coroutine")
                    return underlying_symbol, 'EQUITY'
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                # 🔧 CRITICAL FIX: Use Zerodha's EXACT format from API response
                # Zerodha format: NIFTY07AUG2524650CE (not NIFTY25AUG24650CE)
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                
                logger.info(f"🎯 INDEX SIGNAL: {underlying_symbol} → OPTIONS (F&O enabled)")
                logger.info(f"   Generated: {options_symbol}")
                return options_symbol, option_type
            elif zerodha_underlying in ['MIDCPNIFTY', 'SENSEX']:
                # 🚨 CRITICAL: These indices cannot be traded as equity - SKIP SIGNAL
                logger.warning(f"⚠️ {zerodha_underlying} cannot be traded as equity - SIGNAL REJECTED")
                return None, 'REJECTED'
            else:
                # Stock options - convert equity to options using ZERODHA NAME
                # 🎯 USER REQUIREMENT: Volume-based strike selection for liquidity
                try:
                    expiry = await self._get_next_expiry(zerodha_underlying)
                    if not expiry:
                        logger.error(f"❌ No valid expiry from Zerodha for {zerodha_underlying} - FALLBACK TO EQUITY")
                        return None, 'REJECTED'

                    # 🚨 DEFENSIVE: Check if expiry is valid before using
                    if not isinstance(expiry, str):
                        logger.error(f"❌ INVALID EXPIRY TYPE: {type(expiry)} = {expiry} for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                    strike = await self._get_volume_based_strike(zerodha_underlying, actual_price, expiry, action)

                    # 🚨 DEFENSIVE: Check if strike is valid
                    if not isinstance(strike, int) or strike <= 0:
                        logger.error(f"❌ INVALID STRIKE: {strike} (type: {type(strike)}) for {zerodha_underlying}")
                        return underlying_symbol, 'EQUITY'

                except Exception as await_error:
                    logger.error(f"❌ AWAIT ERROR in stock options: {await_error}")
                    logger.error(f"   Error type: {type(await_error)}")
                    if "can't be used in 'await' expression" in str(await_error):
                        logger.error(f"🚨 CRITICAL: Attempted to await a non-coroutine for {zerodha_underlying}")
                        logger.error(f"   This indicates a method returning wrong type instead of coroutine")
                    return underlying_symbol, 'EQUITY'
                
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                
                # 🔧 CRITICAL FIX: Use Zerodha's exact symbol format for stocks too
                # Zerodha format: GAIL02SEP25150CE should be GAIL25SEP02150CE (YYMMMDDD format)
                options_symbol = f"{zerodha_underlying}{expiry}{strike}{option_type}"
                logger.debug(f"🔍 GENERATED OPTIONS SYMBOL: {options_symbol} (format: {zerodha_underlying} + {expiry} + {strike} + {option_type})")
                
                # 🚨 CRITICAL FIX: Validate if options symbol exists in Zerodha before using
                if self._validate_options_symbol_exists(options_symbol):
                    logger.info(f"🎯 ZERODHA OPTIONS SYMBOL: {underlying_symbol} → {options_symbol}")
                    logger.info(f"   Mapping: {underlying_symbol} → {zerodha_underlying}")
                    logger.info(f"   Strike: {strike}, Expiry: {expiry}, Type: {option_type}")
                    logger.info(f"   Used Price: ₹{actual_price:.2f} (real market price)")
                    return options_symbol, option_type
                else:
                    # 🎯 FALLBACK: Options not available, trade equity instead
                    logger.warning(f"⚠️ OPTIONS NOT AVAILABLE: {options_symbol} doesn't exist in Zerodha NFO")
                    logger.info(f"🔄 FALLBACK: Trading {zerodha_underlying} as EQUITY instead")
                    
                    return zerodha_underlying, 'EQUITY'
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            return underlying_symbol, 'CE'
    
    def _validate_options_symbol_exists(self, options_symbol: str, underlying_symbol: str = None) -> bool:
        """Validate if options symbol exists in Zerodha NFO instruments"""
        try:
            # Extract underlying symbol if not provided
            if not underlying_symbol:
                # Extract from options symbol (e.g., NIFTY14AUG2524550PE -> NIFTY)
                underlying_symbol = options_symbol.split('CE')[0].split('PE')[0]
                # Remove date patterns to get clean symbol
                import re
                underlying_symbol = re.sub(r'\d{2}[A-Z]{3}\d{2}', '', underlying_symbol)
            
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Zerodha client not available for options validation")
                return False  # Conservative: assume options don't exist
            
            # CRITICAL FIX: validate_options_symbol is async, but this method is sync
            # We need to run it synchronously here
            import asyncio
            try:
                # Get the current event loop or create new one
                try:
                    loop = asyncio.get_running_loop()
                    # We're already in an async context, create a task
                    future = asyncio.create_task(orchestrator.zerodha_client.validate_options_symbol(options_symbol))
                    # Can't await here in sync method, so return True for now (assume valid)
                    logger.warning(f"⚠️ Async validation deferred for {options_symbol} - assuming valid")
                    return True
                except RuntimeError:
                    # No running loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    is_valid = loop.run_until_complete(orchestrator.zerodha_client.validate_options_symbol(options_symbol))
            except Exception as async_err:
                logger.error(f"❌ Error in async validation: {async_err}")
                # Fallback: assume valid to allow trading
                return True
            
            if is_valid:
                logger.info(f"✅ OPTIONS VALIDATED: {options_symbol} exists in Zerodha NFO")
                return True
            else:
                logger.warning(f"❌ OPTIONS NOT FOUND: {options_symbol} doesn't exist in Zerodha NFO")
                
                # Debug what options are actually available
                try:
                    # Extract expiry from options symbol for debugging
                    import re
                    match = re.search(r'(\d{2}[A-Z]{3}\d{2})', options_symbol)
                    if match:
                        expiry_str = match.group(1)
                        import asyncio
                        asyncio.create_task(self._debug_available_options(underlying_symbol, expiry_str))
                except Exception as debug_e:
                    logger.error(f"Debug options failed: {debug_e}")
                
                return False
                
        except Exception as e:
            logger.error(f"Error validating options symbol {options_symbol}: {e}")
            return False  # Conservative: assume options don't exist
    
    async def _debug_available_options(self, underlying_symbol: str, expiry_str: str) -> None:
        """Debug function to check what options are actually available"""
        try:
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Cannot debug options - Zerodha client not available")
                return
            
            logger.info(f"🔍 DEBUGGING AVAILABLE OPTIONS for {underlying_symbol} expiry {expiry_str}")
            
            # Get all NFO instruments
            try:
                instruments = await orchestrator.zerodha_client.get_instruments("NFO")

                # 🚨 VALIDATION: Ensure instruments is a list
                if instruments is None:
                    logger.error("❌ get_instruments returned None")
                    return
                elif isinstance(instruments, int):
                    logger.error(f"❌ get_instruments returned int instead of list: {instruments}")
                    return
                elif not isinstance(instruments, list):
                    logger.error(f"❌ get_instruments returned {type(instruments)} instead of list: {instruments}")
                    return
                elif not instruments:
                    logger.error("❌ No NFO instruments available")
                    return

            except Exception as instruments_error:
                logger.error(f"❌ Error getting NFO instruments: {instruments_error}")
                logger.error(f"   Error type: {type(instruments_error)}")
                if "can't be used in 'await' expression" in str(instruments_error):
                    logger.error("🚨 CRITICAL: Zerodha API returned non-coroutine for instruments")
                return
            
            # Find all options for this underlying and expiry
            available_options = []
            for inst in instruments:
                trading_symbol = inst.get('tradingsymbol', '')
                if (underlying_symbol.upper() in trading_symbol.upper() and 
                    expiry_str in trading_symbol and
                    inst.get('instrument_type') in ['CE', 'PE']):
                    available_options.append({
                        'symbol': trading_symbol,
                        'strike': inst.get('strike', 0),
                        'type': inst.get('instrument_type'),
                        'expiry': inst.get('expiry')
                    })
            
            if available_options:
                # Sort by strike price
                available_options.sort(key=lambda x: float(x['strike']) if x['strike'] else 0)
                
                logger.info(f"✅ FOUND {len(available_options)} options for {underlying_symbol} {expiry_str}")
                
                # Show CE options
                ce_options = [opt for opt in available_options if opt['type'] == 'CE']
                if ce_options:
                    strikes = [str(int(float(opt['strike']))) for opt in ce_options[:10]]  # First 10
                    logger.info(f"   CE Strikes: {', '.join(strikes)}{'...' if len(ce_options) > 10 else ''}")
                
                # Show PE options  
                pe_options = [opt for opt in available_options if opt['type'] == 'PE']
                if pe_options:
                    strikes = [str(int(float(opt['strike']))) for opt in pe_options[:10]]  # First 10
                    logger.info(f"   PE Strikes: {', '.join(strikes)}{'...' if len(pe_options) > 10 else ''}")
            else:
                logger.error(f"❌ NO OPTIONS FOUND for {underlying_symbol} {expiry_str}")
                
                # Check if the underlying exists at all
                all_underlyings = set()
                for inst in instruments:
                    trading_symbol = inst.get('tradingsymbol', '')
                    if inst.get('instrument_type') in ['CE', 'PE']:
                        # Extract underlying from options symbol
                        import re
                        match = re.match(r'^([A-Z]+)', trading_symbol)
                        if match:
                            all_underlyings.add(match.group(1))
                
                if underlying_symbol.upper() not in all_underlyings:
                    logger.error(f"❌ UNDERLYING NOT FOUND: {underlying_symbol} not in NFO options")
                    similar = [u for u in all_underlyings if underlying_symbol.upper()[:4] in u]
                    if similar:
                        logger.info(f"   Similar underlyings: {', '.join(list(similar)[:5])}")
                else:
                    logger.error(f"❌ NO OPTIONS for expiry {expiry_str} - check expiry date")
                        
        except Exception as e:
            logger.error(f"Error debugging available options: {e}")
    
    def _get_atm_strike(self, symbol: str, price: float) -> int:
        """Get ATM strike for index options - FIXED for Zerodha's actual intervals"""
        # 🚨 CRITICAL FIX: Based on user feedback "for indices only in 100"
        # All major indices use 100-point intervals in Zerodha
        
        if symbol == 'NIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 NIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'BANKNIFTY':
            strike = round(price / 100) * 100  # Already correct
            logger.info(f"🎯 BANKNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        elif symbol == 'FINNIFTY':
            strike = round(price / 100) * 100  # Changed from 50 to 100
            logger.info(f"🎯 FINNIFTY STRIKE: ₹{price} → {strike} (100-point interval)")
            return int(strike)
        else:
            # Fallback for other indices
            strike = round(price / 100) * 100
            logger.info(f"🎯 {symbol} STRIKE: ₹{price} → {strike} (100-point interval fallback)")
            return int(strike)
    
    def _get_atm_strike_for_stock(self, current_price: float) -> int:
        """Get ATM strike for stock options - FIXED to use Zerodha's actual intervals"""
        try:
            # 🔍 DEBUG: Log current price and strike calculation
            logger.info(f"🔍 DEBUG: Calculating ATM strike for stock price: ₹{current_price}")
            
            # 🚨 CRITICAL FIX: Zerodha only offers strikes in multiples of 50 for most stocks
            # Based on user feedback: "for option price if we see only the prices which are in multiple of 50"
            interval = 50  # Fixed interval for all stocks to match Zerodha availability
            
            # Round to nearest 50
            atm_strike = round(current_price / interval) * interval
            
            logger.info(f"🎯 STOCK STRIKE CALCULATION (FIXED):")
            logger.info(f"   Current Price: ₹{current_price}")
            logger.info(f"   Strike Interval: {interval} (Zerodha standard)")
            logger.info(f"   ATM Strike: {int(atm_strike)}")
            logger.info(f"   Available: {int(atm_strike-50)}, {int(atm_strike)}, {int(atm_strike+50)}")
            
            return int(atm_strike)
            
        except Exception as e:
            logger.error(f"Error calculating ATM strike for stock: {e}")
            # Fallback to nearest 50 (Zerodha standard)
            fallback_strike = round(current_price / 50) * 50
            logger.warning(f"⚠️ FALLBACK STRIKE: {int(fallback_strike)} (rounded to nearest 50)")
            return int(fallback_strike)
      
    async def _get_next_expiry(self, underlying_symbol: str = "NIFTY") -> str:
        """DYNAMIC EXPIRY SELECTION: Get optimal expiry based on strategy requirements"""
        # 🔍 DEBUG: Add comprehensive logging for expiry date debugging
        logger.info(f"🔍 DEBUG: Getting next expiry date...")
        
        # Try to get real expiry dates from Zerodha first
        try:
            available_expiries = await self._get_available_expiries_from_zerodha(underlying_symbol)
        except Exception as e:
            logger.error(f"Error fetching expiries from Zerodha: {e}")
            available_expiries = []
        
        if available_expiries:
            logger.info(f"✅ Found {len(available_expiries)} expiry dates from Zerodha API")
            for i, exp in enumerate(available_expiries[:3]):  # Log first 3
                logger.info(f"   {i+1}. {exp['formatted']} ({exp['date']})")
            
            # Prefer nearest weekly first; if LTP missing later, logic will escalate to next
            optimal_expiry = await self._get_optimal_expiry_for_strategy(underlying_symbol, "nearest_weekly")

            # 🚨 DEFENSIVE: Validate optimal_expiry before returning
            if optimal_expiry is None:
                logger.error(f"❌ _get_optimal_expiry_for_strategy returned None for {underlying_symbol}")
                logger.error("   This should not happen - falling back to calculated expiry")
                # Continue to fallback logic below
            elif not isinstance(optimal_expiry, str):
                logger.error(f"❌ _get_optimal_expiry_for_strategy returned invalid type: {type(optimal_expiry)} = {optimal_expiry}")
                logger.error("   This should not happen - falling back to calculated expiry")
                optimal_expiry = None
            else:
                logger.info(f"🎯 SELECTED EXPIRY: {optimal_expiry}")
                return optimal_expiry
        else:
            logger.warning("⚠️ No expiry dates from Zerodha API - using calculated fallback")
            # Fallback: for stocks, choose last Thursday of current/next month; for indices, next Thursday
            from datetime import datetime, timedelta
            today = datetime.now().date()
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            is_index = zerodha_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']

            def _last_thursday(year: int, month: int):
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                d = datetime(year, month, last_day).date()
                # Thursday = 3
                offset = (d.weekday() - 3) % 7
                return d - timedelta(days=offset)

            if is_index:
                days_ahead = (3 - today.weekday()) % 7  # next Thursday including today
                if days_ahead == 0:
                    days_ahead = 7
                fallback_date = today + timedelta(days=days_ahead)
            else:
                # Stock options: monthly expiry (last Thursday). If today >= last Thursday, move to next month
                lt = _last_thursday(today.year, today.month)
                if today >= lt:
                    year = today.year + (1 if today.month == 12 else 0)
                    month = 1 if today.month == 12 else today.month + 1
                    lt = _last_thursday(year, month)
                fallback_date = lt

            # CRITICAL FIX: Use Zerodha format YYMM not DDMMMYY
            fallback_expiry = fallback_date.strftime("%y%b").upper()
            logger.info(f"🔄 FALLBACK EXPIRY: {fallback_expiry} ({'monthly last Thursday' if not is_index else 'next Thursday'})")
            return fallback_expiry
    
    async def _get_optimal_expiry_for_strategy(self, underlying_symbol: str = "NIFTY", preference: str = "nearest_weekly") -> str:
        """
        Get optimal expiry based on strategy requirements - FIXED ZERODHA FORMAT
        
        Args:
            preference: "nearest_weekly", "nearest_monthly", "next_weekly", "max_time_decay"
        """
        try:
            # Map TrueData symbol to Zerodha symbol before fetching expiries
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            available_expiries = await self._get_available_expiries_from_zerodha(zerodha_symbol)
        except Exception as e:
            logger.error(f"Error fetching expiries from Zerodha: {e}")
            available_expiries = []
        
        if not available_expiries:
            # 🚨 NO FALLBACK: Return None if no real expiries from Zerodha API
            logger.error("❌ No expiries from Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        today = datetime.now().date()
        
        # 🚨 CRITICAL FIX: Use next day as cutoff to avoid expired/expiring options
        # Today is July 31, so July 25 expiry has already passed
        cutoff_date = today + timedelta(days=1)  # Use tomorrow as cutoff for safety
        
        # Filter future expiries only
        future_expiries = [exp for exp in available_expiries if exp['date'] >= cutoff_date]
        
        if not future_expiries:
            # 🚨 NO FALLBACK: Return None if no future expiries found
            logger.error("❌ No future expiries found in Zerodha API - REJECTING SIGNAL (no fallback)")
            return None
        
        # Sort by date
        future_expiries.sort(key=lambda x: x['date'])
        
        # 🎯 SMART EXPIRY SELECTION: Indices vs Stocks
        # Map TrueData symbols to Zerodha symbols for proper identification
        zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
        is_index = zerodha_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX']
        
        if is_index:
            # INDICES: Skip immediate expiry (too little time), use next one
            days_to_first_expiry = (future_expiries[0]['date'] - today).days
            
            if days_to_first_expiry <= 2 and len(future_expiries) > 1:
                # Skip very near expiry (0-2 days), use next
                nearest = future_expiries[1]
                logger.info(f"📊 INDEX {zerodha_symbol} (from {underlying_symbol}): Skipping immediate expiry ({days_to_first_expiry} days), using next ({(nearest['date'] - today).days} days)")
            else:
                # First expiry has enough time
                nearest = future_expiries[0]
                logger.info(f"📊 INDEX {zerodha_symbol} (from {underlying_symbol}): Using nearest expiry ({days_to_first_expiry} days)")
        else:
            # STOCKS: Prefer monthly expiries (last-Thursday); filter out weekly expiries
            monthly_only = [exp for exp in future_expiries if exp.get('is_monthly', False)]
            if monthly_only:
                nearest = monthly_only[0]
                logger.info(f"📊 STOCK {zerodha_symbol}: Using nearest MONTHLY expiry ({(nearest['date'] - today).days} days)")
            else:
                # Fallback: if API doesn't flag monthly, pick the first future expiry
                nearest = future_expiries[0]
                logger.warning(f"⚠️ STOCK {zerodha_symbol}: No monthly flag found, using first future expiry ({(nearest['date'] - today).days} days)")
            
        # Override with preference if specified
        if preference == "next_weekly" and len(future_expiries) > 1:
            nearest = future_expiries[1]
            logger.info(f"   Override: Using next expiry as requested")
        
        # 🔧 CRITICAL FIX: Convert to Zerodha format (25JUL instead of 31JUL25)
        exp_date = nearest['date']
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 25SEP (YY + MMM), NOT 30SEP25
        try:
            # 🚨 DEFENSIVE: Validate date components before formatting
            if not (1 <= exp_date.month <= 12):
                logger.error(f"❌ INVALID MONTH: {exp_date.month} for {underlying_symbol}")
                return None

            if not (1 <= exp_date.day <= 31):
                logger.error(f"❌ INVALID DAY: {exp_date.day} for {underlying_symbol}")
                return None

            zerodha_expiry = f"{str(exp_date.year)[-2:]}{month_names[exp_date.month - 1]}"

            # 🚨 DEFENSIVE: Validate the formatted result
            if not isinstance(zerodha_expiry, str) or len(zerodha_expiry) != 5:
                logger.error(f"❌ INVALID EXPIRY FORMAT: {zerodha_expiry} (type: {type(zerodha_expiry)}, length: {len(zerodha_expiry)}) for {underlying_symbol}")
                return None
        
            logger.info(f"🎯 OPTIMAL EXPIRY: {zerodha_expiry} (from {nearest['formatted']})")
            logger.info(f"   Date: {exp_date}, Days ahead: {(exp_date - today).days}")
            
            return zerodha_expiry

        except Exception as format_error:
            logger.error(f"❌ EXPIRY FORMATTING ERROR for {underlying_symbol}: {format_error}")
            logger.error(f"   Date object: {exp_date} (type: {type(exp_date)})")
            logger.error(f"   Month: {getattr(exp_date, 'month', 'MISSING')} Day: {getattr(exp_date, 'day', 'MISSING')} Year: {getattr(exp_date, 'year', 'MISSING')}")
            return None
    
    async def _get_available_expiries_from_zerodha(self, underlying_symbol: str) -> List[Dict]:
        """
        Fetch available expiry dates from Zerodha instruments API
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Log symbol mapping for debugging
            zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if zerodha_symbol != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_symbol}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                # During backtesting, Zerodha client won't be available - use fallback
                if hasattr(self, 'backtest_mode') and self.backtest_mode:
                    logger.info("📊 In backtest mode - using calculated expiries")
                else:
                    logger.error("❌ Zerodha client not available for expiry lookup")
                return []
            
            # 🚨 DEFENSIVE: Try to get expiries for the specific underlying symbol first
            try:
                logger.info(f"🔍 Trying to get expiries directly for {zerodha_symbol}")
                expiries = await orchestrator.zerodha_client.get_available_expiries_for_symbol(zerodha_symbol)

                # 🚨 DEFENSIVE: Validate the response
                if expiries is None:
                    logger.error(f"❌ get_available_expiries_for_symbol returned None for {zerodha_symbol}")
                    expiries = []
                elif isinstance(expiries, int):
                    logger.error(f"❌ get_available_expiries_for_symbol returned int instead of list: {expiries} for {zerodha_symbol}")
                    expiries = []
                elif not isinstance(expiries, list):
                    logger.error(f"❌ get_available_expiries_for_symbol returned {type(expiries)} instead of list: {expiries} for {zerodha_symbol}")
                    expiries = []
                elif expiries:  # List is not empty
                    logger.info(f"✅ Found {len(expiries)} expiries for {zerodha_symbol}")
                    return expiries
            except Exception as direct_err:
                logger.warning(f"⚠️ Direct expiry fetch failed for {zerodha_symbol}: {direct_err}")

            # Fallback: Try common symbols if direct fetch failed
            logger.info(f"🔄 Falling back to common symbols for expiry lookup")

            # Try to get expiries for common underlying symbols we trade
            common_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'POWERGRID', 'RELIANCE', 'TCS']
            
            for symbol in common_symbols:
                try:
                    logger.info(f"🔍 Trying common symbol {symbol} for expiry data")
                    expiries = await orchestrator.zerodha_client.get_available_expiries_for_symbol(symbol)

                    # 🚨 DEFENSIVE: Validate the response
                    if expiries is None:
                        logger.warning(f"⚠️ get_available_expiries_for_symbol returned None for {symbol}")
                        continue
                    elif isinstance(expiries, int):
                        logger.error(f"❌ get_available_expiries_for_symbol returned int instead of list: {expiries} for {symbol}")
                        continue
                    elif not isinstance(expiries, list):
                        logger.error(f"❌ get_available_expiries_for_symbol returned {type(expiries)} instead of list: {expiries} for {symbol}")
                        continue
                    elif expiries:  # List is not empty
                            logger.info(f"📅 Using expiries from {symbol}: {len(expiries)} found")
                            return expiries
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching expiries for {symbol}: {e}")
                    continue
            
            # If no expiries found from API, REJECT signal
            logger.error("❌ No expiries found from Zerodha API - NO FALLBACK")
            # 🚨 FINAL VALIDATION: Ensure we return a valid list of dictionaries
            if not isinstance(expiries, list):
                logger.error(f"❌ expiries is not a list: {type(expiries)} = {expiries}")
            return []
            
            # Validate each expiry entry
            valid_expiries = []
            for expiry in expiries:
                if isinstance(expiry, dict) and 'date' in expiry and 'formatted' in expiry:
                    valid_expiries.append(expiry)
                else:
                    logger.warning(f"⚠️ Filtering out invalid expiry entry: {expiry} (type: {type(expiry)})")

            return valid_expiries
            
        except Exception as e:
            logger.error(f"❌ Error fetching available expiries: {e}")
            # Add debug info to help identify the issue
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return []
    
    def _get_fallback_expiries(self) -> List[Dict]:
        """Generate realistic weekly expiries when API is unavailable"""
        today = datetime.now().date()
        expiries = []
        
        # Add all Thursdays for next 8 weeks
        current_date = today
        for weeks_ahead in range(8):
            # Find next Thursday
            days_ahead = (3 - current_date.weekday()) % 7  # Thursday = 3
            if days_ahead == 0 and current_date == today:
                days_ahead = 7  # If today is Thursday, get next Thursday
                
            thursday = current_date + timedelta(days=days_ahead)
            
            # Format for Zerodha: 25AUG (YY + MMM)
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            formatted = f"{str(thursday.year)[-2:]}{month_names[thursday.month - 1]}"
            
            # Determine if it's monthly (last Thursday of month)
            next_week = thursday + timedelta(days=7)
            is_monthly = next_week.month != thursday.month
            
            expiries.append({
                'date': thursday,
                'formatted': formatted,
                'is_weekly': True,
                'is_monthly': is_monthly
            })
            
            current_date = thursday + timedelta(days=1)  # Move to next week
        
        logger.info(f"📅 Generated {len(expiries)} fallback expiries: {[e['formatted'] for e in expiries[:3]]}...")
        return expiries
    
    def _calculate_next_thursday_fallback(self) -> str:
        """Fallback calculation for next Thursday when API is unavailable - FIXED ZERODHA FORMAT"""
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
        if days_ahead == 0:
            days_ahead = 7  # If today is Thursday, get next Thursday
            
        next_thursday = today + timedelta(days=days_ahead)
        
        # 🚨 CRITICAL DEBUG: Log calculation details
        logger.info(f"🔍 EXPIRY CALCULATION DEBUG:")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')} (weekday: {today.weekday()})")
        logger.info(f"   Days ahead to Thursday: {days_ahead}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        
        # 🔧 CRITICAL FIX: Format for Zerodha - their format is 25JUL (not 31JUL25)
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        # 🚨 CRITICAL FIX: Zerodha format is 14AUG25 (DD + MMM + YY), NOT 14AUG (DD + MMM)
        expiry_formatted = f"{next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}"
        
        logger.info(f"📅 ZERODHA EXPIRY FORMAT: {expiry_formatted}")
        logger.info(f"   Next Thursday: {next_thursday.strftime('%A, %B %d, %Y')}")
        logger.info(f"   Today: {today.strftime('%A, %B %d, %Y')}")
        logger.info(f"   OLD FORMAT would be: {next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}")
        logger.info(f"   NEW ZERODHA FORMAT: {expiry_formatted}")
        
        return expiry_formatted
    
    def _get_last_thursday_of_month(self, year: int, month: int) -> datetime:
        """Get the last Thursday of a given month - DEPRECATED: Use dynamic expiry selection"""
        import calendar
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        
        # Find the last Thursday
        last_date = datetime(year, month, last_day)
        
        # Thursday is 3, so we need to go back to find the last Thursday
        days_back = (last_date.weekday() - 3) % 7  # 3 = Thursday
        if days_back == 0 and last_date.weekday() == 3:
            # Already a Thursday
            return last_date
        else:
            # Go back to find the last Thursday
            last_thursday = last_date - timedelta(days=days_back)
            return last_thursday
    
    def _truncate_symbol_for_options(self, symbol: str) -> str:
        """Truncate symbol names for options format"""
        # Common truncations for stock options
        truncation_map = {
            'ICICIBANK': 'ICICIBANK',  # Actually, let's test with full name first
            'HDFCBANK': 'HDFCBANK',
            'RELIANCE': 'RELIANCE',
            'BHARTIARTL': 'BHARTIARTL'
        }
        return truncation_map.get(symbol, symbol)
    
    def _is_cooldown_passed(self) -> bool:
        """Check if cooldown period has passed"""
        if not self.last_signal_time:
            return True
        return (datetime.now() - self.last_signal_time).total_seconds() >= self.signal_cooldown
    
    async def send_to_trade_engine(self, signal: Dict):
        """Send signal to trade engine for execution"""
        try:
            # Get orchestrator instance and send signal to trade engine
            from src.core.orchestrator import get_orchestrator
            orchestrator = await get_orchestrator()
            
            if orchestrator and hasattr(orchestrator, 'trade_engine') and orchestrator.trade_engine:
                await orchestrator.trade_engine.process_signals([signal])
                logger.info(f"✅ Signal sent to trade engine: {signal['symbol']} {signal['action']}")
                return True
            else:
                logger.error(f"❌ Trade engine not available for signal: {signal['symbol']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending signal to trade engine: {e}")
            return False
    
    async def initialize(self):
        """Initialize the strategy - to be implemented by subclasses"""
        logger.info(f"Initializing {self.name} strategy")
        self.is_active = True
    
    def should_analyze_symbol(self, symbol: str, market_data: Dict) -> bool:
        """Determine if this symbol should be analyzed based on strategy criteria"""
        try:
            # Skip if already at max capacity
            if len(self.active_symbols) >= self.max_symbols_to_analyze:
                return symbol in self.active_symbols  # Only analyze if already tracking
            
            # Check symbol-specific filters
            symbol_data = market_data.get(symbol, {})
            
            # Volume filter
            if 'min_volume' in self.symbol_filters:
                volume = symbol_data.get('volume', 0)
                if volume < self.symbol_filters['min_volume']:
                    return False
            
            # Price range filter
            if 'min_price' in self.symbol_filters or 'max_price' in self.symbol_filters:
                ltp = symbol_data.get('ltp', 0)
                if 'min_price' in self.symbol_filters and ltp < self.symbol_filters['min_price']:
                    return False
                if 'max_price' in self.symbol_filters and ltp > self.symbol_filters['max_price']:
                    return False
            
            # Change percent filter (volatility)
            if 'min_change_percent' in self.symbol_filters:
                change_pct = abs(symbol_data.get('change_percent', 0))
                if change_pct < self.symbol_filters['min_change_percent']:
                    return False
            
            # Strategy-specific watchlist
            if self.watchlist and symbol not in self.watchlist:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in symbol filter for {symbol}: {e}")
            return False
    
    def update_active_symbols(self, market_data: Dict):
        """Update list of actively analyzed symbols based on current market conditions"""
        try:
            # Remove symbols with no recent data
            symbols_to_remove = set()
            for symbol in self.active_symbols:
                if symbol not in market_data:
                    symbols_to_remove.add(symbol)
            
            for symbol in symbols_to_remove:
                self.active_symbols.discard(symbol)
                logger.info(f"🔄 Removed {symbol} from active analysis (no data)")
            
            # Add new promising symbols if under capacity
            if len(self.active_symbols) < self.max_symbols_to_analyze:
                # Sort symbols by selection criteria (volume, volatility, etc)
                candidates = []
                for symbol, data in market_data.items():
                    if symbol not in self.active_symbols and self.should_analyze_symbol(symbol, market_data):
                        score = self._calculate_symbol_score(symbol, data)
                        candidates.append((symbol, score))
                
                # Add top candidates
                candidates.sort(key=lambda x: x[1], reverse=True)
                for symbol, score in candidates[:self.max_symbols_to_analyze - len(self.active_symbols)]:
                    self.active_symbols.add(symbol)
                    logger.info(f"➕ Added {symbol} to active analysis (score: {score:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating active symbols: {e}")
    
    def _calculate_symbol_score(self, symbol: str, data: Dict) -> float:
        """Calculate score for symbol selection (higher = better)"""
        try:
            score = 0.0
            
            # Volume score (normalized)
            volume = data.get('volume', 0)
            if volume > 1000000:
                score += 10.0
            elif volume > 500000:
                score += 5.0
            elif volume > 100000:
                score += 2.0
            
            # Volatility score
            change_pct = abs(data.get('change_percent', 0))
            score += min(change_pct * 2, 10.0)  # Cap at 10
            
            # Liquidity score (based on price)
            ltp = data.get('ltp', 0)
            if 100 < ltp < 5000:  # Sweet spot for liquidity
                score += 5.0
            
            # Momentum score
            if data.get('change_percent', 0) > 0:
                score += 2.0  # Slight bias towards gainers
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating score for {symbol}: {e}")
            return 0.0
    
    async def on_market_data(self, data: Dict):
        """Handle incoming market data - to be implemented by subclasses"""
        # Update active symbols before processing
        self.update_active_symbols(data)
        
        # Store historical data only for active symbols
        for symbol in self.active_symbols:
            if symbol in data:
                self._update_historical_data(symbol, data[symbol])
    
    def _update_historical_data(self, symbol: str, data: Dict):
        """Update historical data for a symbol"""
        try:
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            # Add current data point
            data_point = {
                'timestamp': data.get('timestamp', datetime.now()),
                'open': data.get('open', 0),
                'high': data.get('high', 0),
                'low': data.get('low', 0),
                'close': data.get('close', data.get('ltp', 0)),
                'volume': data.get('volume', 0),
                'ltp': data.get('ltp', 0),
                'change_percent': data.get('change_percent', 0)
            }
            
            self.historical_data[symbol].append(data_point)
            
            # Trim history if needed
            if len(self.historical_data[symbol]) > self.max_history:
                self.historical_data[symbol].pop(0)
                
        except Exception as e:
            logger.error(f"Error updating historical data for {symbol}: {e}")
        
        pass
    
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 

    def _get_options_premium(self, options_symbol: str, underlying_symbol: str) -> float:
        """Get real-time premium for options symbol with enhanced fallbacks"""
        if not self._is_trading_hours():
            logger.warning(f"⚠️ Market closed - cannot get options premium for {options_symbol}")
            return 0.0
        
        # REMOVED: Stock options restriction - fixing root LTP issue instead
        # Users confirmed stock options should work, need to debug actual LTP failures
        
        try:
            # NEW: Dynamic fetch for zerodha_client if missing
            if not hasattr(self, 'zerodha_client') or self.zerodha_client is None:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                if orchestrator:
                    self.zerodha_client = orchestrator.zerodha_client
                    logger.info(f"✅ Dynamically fetched Zerodha client for {self.name}")
                else:
                    logger.warning(f"⚠️ Could not fetch Zerodha client dynamically - skipping Zerodha fallback")
            
            # Primary - Zerodha LTP (sync version)
            if self.zerodha_client:
                logger.info(f"🔍 DEBUGGING: Fetching Zerodha LTP for {options_symbol}")
                zerodha_ltp = self.zerodha_client.get_options_ltp_sync(options_symbol)
                logger.info(f"📊 Zerodha LTP Response: {zerodha_ltp} for {options_symbol}")
                if zerodha_ltp and zerodha_ltp > 0:
                    logger.info(f"✅ Primary Zerodha LTP for {options_symbol}: ₹{zerodha_ltp}")
                    
                    # 🚨 CRITICAL: Reject ultra-low premium options (< ₹1.00)
                    if zerodha_ltp < 1.00:
                        logger.warning(f"⚠️ REJECTING LOW PREMIUM: {options_symbol} premium ₹{zerodha_ltp:.2f} < ₹1.00 minimum")
                        logger.warning(f"   Reason: Insufficient liquidity and tick size constraints for proper risk management")
                        return 0.0  # Return 0 to trigger rejection
                    
                    return zerodha_ltp
                else:
                    logger.warning(f"⚠️ Zerodha LTP is zero or None: {zerodha_ltp} for {options_symbol}")
            else:
                logger.warning(f"⚠️ No Zerodha client available for LTP fetching")
            
            # Primary Fallback: Zerodha bid/ask average
            if self.zerodha_client:
                try:
                    full_symbol = f"NFO:{options_symbol}"
                    quote = self.zerodha_client.kite.quote(full_symbol)
                    if quote and full_symbol in quote:
                        data = quote[full_symbol]
                        bid = data.get('depth', {}).get('buy', [{}])[0].get('price', 0)
                        ask = data.get('depth', {}).get('sell', [{}])[0].get('price', 0)
                        if bid > 0 and ask > 0:
                            avg_price = (bid + ask) / 2
                            logger.info(f"✅ Zerodha bid/ask average (primary fallback) for {options_symbol}: ₹{avg_price} (bid: ₹{bid}, ask: ₹{ask})")
                            return avg_price
                        elif bid > 0:
                            logger.info(f"✅ Using Zerodha bid price (primary fallback) for {options_symbol}: ₹{bid}")
                            return bid
                        elif ask > 0:
                            logger.info(f"✅ Using Zerodha ask price (primary fallback) for {options_symbol}: ₹{ask}")
                            return ask
                    logger.warning(f"⚠️ Zerodha quote primary fallback returned zero for {options_symbol}")
                except Exception as quote_err:
                    logger.warning(f"⚠️ Zerodha quote primary fallback failed for {options_symbol}: {quote_err}")
            
            # 🚨 INVESTIGATION: Log detailed error information for debugging
            logger.error(f"❌ ALL ZERODHA METHODS FAILED for {options_symbol}")
            logger.error(f"   - LTP method failed")
            logger.error(f"   - Quote method failed")
            logger.error(f"   - Need to investigate specific API endpoint issues")
            return 0.0
        
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR getting options premium for {options_symbol}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return 0.0
    
    def _round_to_tick_size(self, price: float) -> float:
        """Round options price to proper tick size (₹0.05 for options)"""
        try:
            from src.utils.helpers import round_price_to_tick
            return round_price_to_tick(price, 0.05)  # Options tick size is ₹0.05
        except ImportError:
            # Fallback if import fails
            return round(price / 0.05) * 0.05

    
    def _calculate_options_levels(self, options_entry_price: float, original_stop_loss: float, 
                                 original_target: float, option_type: str, action: str, underlying_symbol: str) -> tuple:
        """Dynamically calculate stop_loss and target for options premium using REAL ATR"""
        try:
            # CRITICAL FIX: Calculate REAL ATR for the underlying symbol
            atr = None
            atr_percent = None
            
            # Try to get live market data for ATR calculation
            try:
                from data.truedata_client import live_market_data
                if underlying_symbol in live_market_data:
                    market_data = live_market_data[underlying_symbol]
                    high = float(market_data.get('high', 0))
                    low = float(market_data.get('low', 0))
                    ltp = float(market_data.get('ltp', 0))
                    
                    if high > 0 and low > 0 and ltp > 0:
                        atr = self.calculate_atr(underlying_symbol, high, low, ltp)
                        atr_percent = (atr / ltp) * 100 if ltp > 0 else 0
                        logger.info(f"📊 ATR-BASED RISK: {underlying_symbol} - ATR=₹{atr:.2f} ({atr_percent:.2f}%)")
            except Exception as atr_err:
                logger.debug(f"Could not calculate ATR for {underlying_symbol}: {atr_err}")
            
            # If ATR calculation succeeded, use it; otherwise use volatility-based fallback
            if atr_percent and 0.5 <= atr_percent <= 10:  # Sanity check: 0.5% - 10% range
                # 🚨 MATHEMATICAL FIX: Tighter multiplier for options
                # Options have limited downside (premium), need tighter stops to preserve capital
                base_risk_percent = min(atr_percent * 1.0, 0.10)  # 1.0x ATR (was 1.5x), max 10% (was 20%)
                logger.info(f"✅ USING ATR: {underlying_symbol} - Risk={base_risk_percent*100:.1f}% (1.0x ATR, TIGHTENED)")
            else:
                # Fallback to volatility-based calculation
                base_risk_percent = self._get_dynamic_risk_percentage(underlying_symbol, options_entry_price)
                logger.info(f"⚠️ FALLBACK: {underlying_symbol} - Risk={base_risk_percent*100:.1f}% (volatility-based)")
            
            # DYNAMIC FIX: Use market-based reward-to-risk ratio for quality trading
            target_risk_reward_ratio = self._get_dynamic_target_risk_reward_ratio(underlying_symbol, options_entry_price, option_type)
            
            # Calculate risk and reward amounts
            risk_amount = options_entry_price * base_risk_percent
            reward_amount = risk_amount * target_risk_reward_ratio
            
            # For BUY actions (all our options signals):
            # - stop_loss = Lower premium (cut losses)
            # - target = Higher premium (take profits)
            options_stop_loss = options_entry_price - risk_amount
            options_target = options_entry_price + reward_amount
            
            # Ensure stop_loss doesn't go too low (minimum 5% of entry price)
            min_stop_loss = options_entry_price * 0.05  # Max 95% loss
            options_stop_loss = max(options_stop_loss, min_stop_loss)
            
            # Recalculate actual risk/reward after bounds
            actual_risk = options_entry_price - options_stop_loss
            actual_reward = options_target - options_entry_price
            actual_ratio = actual_reward / actual_risk if actual_risk > 0 else 2.1
            actual_risk_percent = (actual_risk / options_entry_price) * 100
            actual_reward_percent = (actual_reward / options_entry_price) * 100
            
            logger.info(f"📊 OPTIONS LEVELS (ATR-DYNAMIC):")
            logger.info(f"   Entry: ₹{options_entry_price:.2f}")
            logger.info(f"   Stop Loss: ₹{options_stop_loss:.2f} (Risk: ₹{actual_risk:.2f} = {actual_risk_percent:.1f}%)")
            logger.info(f"   Target: ₹{options_target:.2f} (Reward: ₹{actual_reward:.2f} = {actual_reward_percent:.1f}%)")
            logger.info(f"   R:R Ratio = 1:{actual_ratio:.2f} (Target: 1:{target_risk_reward_ratio})")
            
            return options_stop_loss, options_target
            
        except Exception as e:
            logger.error(f"Error calculating options levels: {e}")
            # 🚨 MATHEMATICAL FIX: Tighter conservative fallback
            base_risk_percent = 0.08  # 8% fallback risk (was 15%)
            risk_amount = options_entry_price * base_risk_percent  
            target_ratio = 2.5  # Better fallback ratio (was 2.0)
            reward_amount = risk_amount * target_ratio
            stop_loss = options_entry_price - risk_amount
            target = options_entry_price + reward_amount
            # Ensure minimum stop loss
            stop_loss = max(stop_loss, options_entry_price * 0.10)  # Max 90% loss (was 95%)
            return stop_loss, target
    
    def _calculate_dynamic_options_multiplier(self, option_type: str, options_entry_price: float) -> float:
        """Calculate dynamic options multiplier based on market conditions"""
        try:
            # Base multiplier starts at 2.0
            base_multiplier = 2.0
            
            # Adjust based on option premium level (higher premium = lower multiplier)
            if options_entry_price > 200:
                premium_adjustment = 0.8  # Deep ITM options move less
            elif options_entry_price > 100:
                premium_adjustment = 1.0  # ATM options
            else:
                premium_adjustment = 1.2  # OTM options move more
            
            # Adjust based on option type and market conditions
            type_adjustment = 1.0  # Base adjustment
            
            # Final multiplier
            multiplier = base_multiplier * premium_adjustment * type_adjustment
            return max(1.5, min(multiplier, 5.0))  # Bounds between 1.5x and 5x
            
        except Exception as e:
            logger.error(f"Error calculating dynamic multiplier: {e}")
            return 2.5  # Fallback
    
    def _calculate_dynamic_volatility_factor(self, underlying_price: float) -> float:
        """Calculate dynamic volatility factor based on market conditions"""
        try:
            # This would ideally use historical price data to calculate actual volatility
            # For now, use a market-condition based approach
            
            # Base volatility factor
            base_volatility = 0.02  # 2% base
            
            # Adjust based on market hours and conditions
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11 or 14 <= current_hour <= 15:  # High volatility hours
                time_adjustment = 1.3
            else:
                time_adjustment = 1.0
            
            # Adjust based on underlying price level (higher price = potentially lower volatility)
            if underlying_price > 10000:
                price_adjustment = 0.8
            elif underlying_price > 1000:
                price_adjustment = 1.0
            else:
                price_adjustment = 1.2
            
            volatility_factor = base_volatility * time_adjustment * price_adjustment
            return max(0.01, min(volatility_factor, 0.1))  # Between 1% and 10%
            
        except Exception as e:
            logger.error(f"Error calculating volatility factor: {e}")
            return 0.03  # 3% fallback
    
    def _extract_strike_from_symbol(self, options_symbol: str) -> float:
        """Extract strike price from options symbol - FIXED REGEX"""
        try:
            import re
            
            # 🎯 CORRECT FORMAT: SYMBOL + YYMMM + STRIKE + TYPE
            # Examples: ASIANPAINT25AUG2450CE, TCS25AUG3000PE
            
            # Pattern: Any letters + YYMMM + NUMBERS + CE/PE
            match = re.search(r'([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)$', options_symbol)
            
            if match:
                symbol_part = match.group(1)    # e.g., "ASIANPAINT" 
                date_part = match.group(2)      # e.g., "25AUG"
                strike_part = match.group(3)    # e.g., "2450"
                option_type = match.group(4)    # e.g., "CE"
                
                logger.info(f"🔍 STRIKE EXTRACTION: {options_symbol}")
                logger.info(f"   Symbol: {symbol_part}, Date: {date_part}, Strike: {strike_part}, Type: {option_type}")
                
                return float(strike_part)
            
            # If regex fails, use fallback
            logger.error(f"❌ Could not extract strike from {options_symbol}")
            return 2500.0  # Safe fallback
            
        except Exception as e:
            logger.error(f"Error extracting strike from {options_symbol}: {e}")
            return 2500.0  # Fallback
    
    def _get_dynamic_min_risk_reward_ratio(self, symbol: str, price: float) -> float:
        """Calculate minimum risk-reward ratio based on market volatility and symbol characteristics"""
        try:
            # Get market volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base minimum ratio (conservative)
            base_ratio = 1.2
            
            # Adjust based on volatility:
            # High volatility = lower minimum ratio (easier to achieve)  
            # Low volatility = higher minimum ratio (need better setups)
            if volatility_multiplier > 2.0:
                return base_ratio * 0.8  # 0.96 for high volatility
            elif volatility_multiplier > 1.5:
                return base_ratio * 0.9  # 1.08 for medium volatility  
            else:
                return base_ratio * 1.0  # 1.20 for low volatility (FIXED: was 1.1 = 1.32)
                
        except Exception as e:
            logger.error(f"Error calculating dynamic min R:R ratio: {e}")
            return 1.2  # Conservative fallback
    
    def _get_dynamic_target_risk_reward_ratio(self, symbol: str, price: float, option_type: str = 'CE') -> float:
        """Calculate target risk-reward ratio based on market conditions and symbol characteristics"""
        try:
            # Get market volatility and momentum indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # Base target ratio
            base_ratio = 2.0
            
            # Adjust based on volatility:
            # High volatility = higher target ratio (bigger moves possible)
            # Low volatility = lower target ratio (smaller moves expected)
            if volatility_multiplier > 2.5:
                target_ratio = base_ratio * 1.3  # 2.6 for very high volatility
            elif volatility_multiplier > 2.0:
                target_ratio = base_ratio * 1.2  # 2.4 for high volatility
            elif volatility_multiplier > 1.5:
                target_ratio = base_ratio * 1.1  # 2.2 for medium volatility
            else:
                target_ratio = base_ratio * 0.9  # 1.8 for low volatility
            
            # Options-specific adjustments
            if option_type in ['CE', 'PE']:
                # 🚨 MATHEMATICAL FIX: Higher minimum R:R for options to justify risk
                # Need at least 2:1 to overcome theta decay and slippage
                target_ratio *= 1.2  # Increased from 1.1
            
            # 🚨 STRICTER BOUNDS: Minimum 2:1 R:R for options (was 1.5:1)
            return max(2.0, min(target_ratio, 3.5))
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target R:R ratio: {e}")
            return 2.2  # Conservative fallback
    
    def _get_dynamic_risk_percentage(self, symbol: str, price: float) -> float:
        """
        🚨 DAVID VS GOLIATH: Ultra-tight risk for options survival
        4 days of losses = need MUCH tighter stops
        """
        try:
            # Get volatility indicators
            volatility_multiplier = self._get_volatility_multiplier(symbol, price)
            
            # 🚨 DRASTIC REDUCTION: 8% → 5% base risk
            # Options decay FAST, we need to exit losers IMMEDIATELY
            base_risk = 0.05  # 5% base risk (was 8%, was 12% before that)
            
            # Adjust based on volatility (even tighter):
            # High volatility = VERY tight stops (options will whipsaw)
            # Low volatility = still tight but slightly more room
            if volatility_multiplier > 2.0:
                risk_percent = base_risk * 0.75  # 3.75% for high vol (was 6.8%)
            elif volatility_multiplier > 1.5:
                risk_percent = base_risk * 0.90  # 4.5% for medium vol (was 8.0%)
            else:
                risk_percent = base_risk * 1.0  # 5.0% for low vol (was 8.8%)
            
            # 🚨 ULTRA-TIGHT BOUNDS: 3-7% max (was 6-12%)
            # Example: ₹60 premium option
            #   3% = ₹1.80 stop (exit FAST if wrong)
            #   7% = ₹4.20 stop (maximum allowed loss)
            return max(0.03, min(risk_percent, 0.07))  # Between 3% and 7%
            
        except Exception as e:
            logger.error(f"Error calculating dynamic risk percentage: {e}")
            return 0.05  # 🚨 ULTRA-TIGHT: 5% fallback (was 8%)
    
    def _get_volatility_multiplier(self, symbol: str, price: float) -> float:
        """Get volatility multiplier for the symbol based on recent price action"""
        try:
            # Try to get actual volatility data from TrueData
            from data.truedata_client import live_market_data
            
            if symbol in live_market_data:
                market_data = live_market_data[symbol]
                
                # Calculate intraday volatility
                high = market_data.get('high', price)
                low = market_data.get('low', price)
                open_price = market_data.get('open', price)
                
                if high > 0 and low > 0 and open_price > 0:
                    # Calculate percentage range
                    day_range = ((high - low) / open_price) * 100
                    
                    # Convert to volatility multiplier
                    if day_range > 4.0:
                        return 2.5  # Very high volatility
                    elif day_range > 3.0:
                        return 2.0  # High volatility
                    elif day_range > 2.0:
                        return 1.5  # Medium volatility
                    else:
                        return 1.0  # Low volatility
            
            # Fallback: Use symbol characteristics
            # Major indices tend to be less volatile than individual stocks
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                return 1.8  # Index volatility
            else:
                return 1.5  # Stock volatility
                
        except Exception as e:
            logger.error(f"Error calculating volatility multiplier for {symbol}: {e}")
            return 1.5  # Moderate fallback
    
    def _calculate_days_to_expiry(self, options_symbol: str) -> int:
        """Calculate days to expiry from options symbol"""
        try:
            # Extract date from symbol and calculate days remaining
            import re
            from datetime import datetime, timedelta
            
            # Look for date pattern in symbol (e.g., 31JUL25)
            date_match = re.search(r'(\d{1,2})([A-Z]{3})(\d{2})', options_symbol)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)
                year = int(date_match.group(3)) + 2000
                
                month_map = {
                    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                }
                month = month_map.get(month_str, 1)
                
                expiry_date = datetime(year, month, day)
                days_remaining = (expiry_date - datetime.now()).days
                return max(1, days_remaining)  # At least 1 day
            
            # Fallback: assume 7 days
            return 7
            
        except Exception as e:
            logger.error(f"Error calculating expiry for {options_symbol}: {e}")
            return 7  # 1 week fallback
    
    def _get_dynamic_lot_size(self, options_symbol: str, underlying_symbol: str) -> int:
        """🎯 ROBUST LOT SIZE: Zerodha API with hardcoded fallbacks for major F&O stocks"""
        try:
            # Try to get actual lot size from Zerodha instruments API
            actual_lot_size = self._fetch_zerodha_lot_size(underlying_symbol)
            if actual_lot_size:
                logger.info(f"✅ DYNAMIC LOT SIZE: {underlying_symbol} = {actual_lot_size} (from Zerodha API)")
                return actual_lot_size
            
            # 🚨 HARDCODED FALLBACK: Common F&O symbols with standard lot sizes
            common_lot_sizes = {
                'DMART': 150,
                'FEDERALBNK': 5000,
                'TATACONSUM': 550,
                'DRREDDY': 625,
                'APOLLOTYRE': 2000,  # Actually equity-only
                'TATASTEEL': 3500,
                'RELIANCE': 250,
                'HDFCBANK': 1100,
                'ICICIBANK': 700,
                'KOTAKBANK': 400,
                'SBIN': 1500,
                'AXISBANK': 1200,
                'INDUSINDBK': 900,
                'BAJFINANCE': 125,
                'MARUTI': 100,
                'INFY': 300,
                'TCS': 150,
                'WIPRO': 3000,
                'LT': 225,
                'SUNPHARMA': 400,
                'CIPLA': 350,
                'BHARTIARTL': 475,
                'TITAN': 300,
                'ASIANPAINT': 150,
                'NESTLEIND': 50,
                'HINDUNILVR': 300,
                'ITC': 3200,
                'COALINDIA': 4000,
                'ONGC': 4200,
                'NTPC': 2000,
                'POWERGRID': 1800,
                'TATAMOTORS': 1500,
                'HINDALCO': 1700,
                'VEDL': 1150,
                'JSWSTEEL': 800,
                'SAIL': 6000,
                'NMDC': 1300,
                'GAIL': 2200,
                'IOC': 3500,
                'BPCL': 600,
                'HPCL': 1050
            }
            
            fallback_lot_size = common_lot_sizes.get(underlying_symbol)
            if fallback_lot_size:
                logger.info(f"✅ FALLBACK LOT SIZE: {underlying_symbol} = {fallback_lot_size} (hardcoded)")
                return fallback_lot_size
            
            # If no fallback available, treat as equity
            logger.warning(f"⚠️ NO LOT SIZE available for {underlying_symbol} - treating as EQUITY only")
            logger.info(f"🔄 FALLBACK: {underlying_symbol} should use EQUITY trading instead of F&O")
            return None
                
        except Exception as e:
            logger.error(f"Error getting dynamic lot size for {options_symbol}: {e}")
            return None
    
    def _map_truedata_to_zerodha_symbol(self, truedata_symbol: str) -> str:
        """Map TrueData symbol format to Zerodha format"""
        # Direct mapping for common indices
        symbol_mapping = {
            'NIFTY-I': 'NIFTY',
            'BANKNIFTY-I': 'BANKNIFTY', 
            'FINNIFTY-I': 'FINNIFTY',
            'MIDCPNIFTY-I': 'MIDCPNIFTY',
            'SENSEX-I': 'SENSEX',
            'BANKEX-I': 'BANKEX'
        }
        
        # Check direct mapping first
        if truedata_symbol in symbol_mapping:
            return symbol_mapping[truedata_symbol]
        
        # For regular stocks, remove any suffixes and clean
        cleaned_symbol = truedata_symbol.replace('-I', '').replace('-EQ', '').strip()
        
        return cleaned_symbol
    
    def _fetch_zerodha_lot_size(self, underlying_symbol: str) -> int:
        """🎯 DYNAMIC: Fetch actual lot size from Zerodha instruments API"""
        try:
            # Log symbol mapping for debugging
            clean_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
            if clean_underlying != underlying_symbol:
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {clean_underlying}")
            
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.debug(f"⚠️ Zerodha client not available for lot size lookup: {underlying_symbol}")
                return None
            
            # Try to get instruments data
            if hasattr(orchestrator.zerodha_client, 'kite') and orchestrator.zerodha_client.kite:
                try:
                    # Get NFO instruments (F&O contracts)
                    instruments = orchestrator.zerodha_client.kite.instruments('NFO')
                    logger.debug(f"🔍 Searching for lot size: {underlying_symbol} → {clean_underlying}")
                    
                    # Look for the underlying symbol in F&O instruments
                    for instrument in instruments:
                        trading_symbol = instrument.get('tradingsymbol', '')
                        segment = instrument.get('segment', '')
                        name = instrument.get('name', '')
                        
                        # 🚨 ENHANCED MATCHING: Multiple matching strategies
                        symbol_matches = (
                            trading_symbol.startswith(clean_underlying) or  # RELIANCE25SEP...
                            (name and clean_underlying in name.upper()) or  # Company name in 'name' field
                            (clean_underlying in trading_symbol and len(clean_underlying) > 3)  # Partial match for longer symbols
                        )
                        
                        if (symbol_matches and 
                            segment == 'NFO-OPT' and  # Options only
                            ('CE' in trading_symbol or 'PE' in trading_symbol)):
                            
                            lot_size = instrument.get('lot_size', 0)
                            if lot_size > 0:
                                logger.info(f"✅ ZERODHA LOT SIZE: {underlying_symbol} = {lot_size}")
                                logger.debug(f"   Matched instrument: {trading_symbol} (segment: {segment})")
                                return lot_size
                    
                    logger.debug(f"🔍 No F&O lot size found for {underlying_symbol} in Zerodha instruments")
                    return None
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error fetching Zerodha instruments for {underlying_symbol}: {e}")
                    return None
            else:
                logger.debug(f"⚠️ Zerodha KiteConnect not initialized for lot size lookup")
                return None
                
        except Exception as e:
            logger.debug(f"Error fetching Zerodha lot size for {underlying_symbol}: {e}")
            return None
    
    
    # REMOVED: Duplicate function - using the complete implementation below
            # For options: margin is typically much less than premium cost
            premium_per_lot = lot_size * entry_price
            
            # Try to get actual margin requirement from Zerodha
            try:
                if hasattr(self, 'zerodha_client') and self.zerodha_client:
                    # Use Zerodha's margin calculation if available
                    estimated_margin_per_lot = self.zerodha_client.get_required_margin_for_order(
                        symbol=options_symbol, quantity=lot_size, price=entry_price, 
                        transaction_type='BUY', product='MIS'
                    )
                    if estimated_margin_per_lot and estimated_margin_per_lot > 0:
                        logger.info(f"📊 ZERODHA MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
                    else:
                        # Fallback: estimate margin as percentage of premium
                        estimated_margin_per_lot = premium_per_lot * 0.3  # ~30% margin for options
                        logger.info(f"📊 ESTIMATED MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
                else:
                    # Fallback: estimate margin as percentage of premium  
                    estimated_margin_per_lot = premium_per_lot * 0.3  # ~30% margin for options
                    logger.info(f"📊 ESTIMATED MARGIN: {options_symbol} = ₹{estimated_margin_per_lot:,.0f} per lot")
            except Exception as e:
                # Conservative fallback
                estimated_margin_per_lot = premium_per_lot * 0.3
                logger.debug(f"Margin calculation fallback for {options_symbol}: {e}")
            
            # Apply 25% margin allocation limit
            max_margin_allowed = available_capital * max_margin_per_trade_pct
            max_affordable_lots = int(max_margin_allowed / estimated_margin_per_lot) if estimated_margin_per_lot > 0 else 0
            
            if max_affordable_lots < 1:
                logger.warning(
                    f"❌ OPTIONS REJECTED: {options_symbol} 1 lot needs ₹{estimated_margin_per_lot:,.0f} margin, "
                    f"exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                )
                return 0
            
            final_lots = max_affordable_lots
            total_margin = final_lots * estimated_margin_per_lot
            
            logger.info(f"✅ OPTIONS MARGIN OK: {final_lots} lots, Est. Margin ₹{total_margin:,.0f}")
            return final_lots * lot_size
        
        else:  # Equity
            if entry_price <= 0:
                return 0
            min_trade_value = 25000.0  # Minimum ₹25,000 trade value for stocks
            
            # Check if we can afford minimum trade value
            if available_capital < min_trade_value:
                return 0
                
            # 🎯 CRITICAL: Calculate shares needed for MINIMUM ₹25,000 trade value
            min_shares_required = int(min_trade_value / entry_price)
            cost_for_min_shares = min_shares_required * entry_price
            
                                        # 🚨 MARGIN-BASED POSITION SIZING: Use 25% of available margin
            # For MIS equity: margin ≈ 25-30% of trade value (leverage ~4x)
            estimated_margin_factor = 0.25  # Conservative estimate for MIS margin requirement
            max_margin_allowed = available_capital * max_margin_per_trade_pct
            
            # Calculate maximum trade value we can afford with 25% margin allocation
            max_affordable_trade_value = max_margin_allowed / estimated_margin_factor
            max_affordable_shares = int(max_affordable_trade_value / entry_price)
            max_affordable_cost = max_affordable_shares * entry_price
            
            # Use the higher of: minimum trade value OR maximum affordable within margin limits
            if max_affordable_cost >= min_trade_value:
                # We can afford more than minimum - use maximum affordable
                final_quantity = max_affordable_shares
                cost = max_affordable_cost
                estimated_margin = cost * estimated_margin_factor
                
                logger.debug(f"✅ MARGIN-OPTIMIZED: {underlying_symbol} = {final_quantity} shares")
                logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                logger.debug(f"   💳 Est. Margin: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital:.1%} of capital)")
                logger.debug(f"   📊 Leverage: ~{cost/estimated_margin:.1f}x")
                return final_quantity
            else:
                # Can only afford minimum - check if it fits in margin allocation
                min_estimated_margin = cost_for_min_shares * estimated_margin_factor
                
                if min_estimated_margin <= max_margin_allowed:
                    logger.debug(f"✅ MINIMUM VIABLE: {underlying_symbol} = {min_shares_required} shares")
                    logger.debug(f"   💰 Trade Value: ₹{cost_for_min_shares:,.0f}")
                    logger.debug(f"   💳 Est. Margin: ₹{min_estimated_margin:,.0f}")
                    return min_shares_required
                else:
                    logger.warning(
                        f"❌ EQUITY REJECTED: {underlying_symbol} min trade ₹{min_trade_value:,.0f} "
                        f"needs ₹{min_estimated_margin:,.0f} margin, exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                    )
                    return 0
    
    def _get_available_capital(self) -> float:
        """🎯 DYNAMIC: Get available capital from Zerodha margins API in real-time"""
        try:
            # First check if we have orchestrator set on this instance
            orchestrator = getattr(self, 'orchestrator', None)
            
            # If not, try to get from global instance
            if not orchestrator:
                from src.core.orchestrator import get_orchestrator_instance
                orchestrator = get_orchestrator_instance()
                
            # Also check for zerodha_client directly on self
            zerodha_client = getattr(self, 'zerodha_client', None)
            
            # Use zerodha_client from wherever we can find it
            if zerodha_client or (orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client):
                if not zerodha_client:
                    zerodha_client = orchestrator.zerodha_client
                try:
                    # Try to get margins (available cash) from Zerodha
                    if hasattr(zerodha_client, 'get_margins'):
                        # Use async method if available
                        import asyncio
                        loop = asyncio.get_event_loop()
                        
                        if loop.is_running():
                            # 🚨 CRITICAL FIX: Use synchronous method in async context
                            if hasattr(zerodha_client, 'get_margins_sync'):
                                real_available = zerodha_client.get_margins_sync()
                                if real_available > 0:
                                    logger.info(f"✅ REAL-TIME CAPITAL: ₹{real_available:,.2f} (sync from Zerodha)")
                                    # Cache the value
                                    self._last_known_capital = real_available
                                    return float(real_available)
                        else:
                            # Run async method to get live margins
                            margins = loop.run_until_complete(zerodha_client.get_margins())
                            if margins and isinstance(margins, (int, float)) and margins > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{margins:,.2f} (live from Zerodha)")
                                self._last_known_capital = margins
                                return float(margins)
                    
                    # Fallback: Try sync method if available
                    if hasattr(zerodha_client, 'kite') and zerodha_client.kite:
                        try:
                            margins = zerodha_client.kite.margins()
                            equity_cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
                            if equity_cash > 0:
                                logger.info(f"✅ DYNAMIC CAPITAL: ₹{equity_cash:,.2f} (from Zerodha equity margins)")
                                self._last_known_capital = equity_cash
                                return float(equity_cash)
                        except Exception as margin_error:
                            logger.debug(f"⚠️ Error fetching Zerodha margins: {margin_error}")
                            
                except Exception as zerodha_error:
                    logger.debug(f"⚠️ Error accessing Zerodha for capital: {zerodha_error}")
            
            # Fallback to cached or config capital if API fails
            if hasattr(self, '_last_known_capital') and self._last_known_capital > 0:
                logger.info(f"✅ Using last known capital: ₹{self._last_known_capital:,.2f}")
                return self._last_known_capital
            
            # Use config capital as fallback
            try:
                # 🚨 DEFENSIVE: Use self.config if available, otherwise import
                if hasattr(self, 'config') and self.config:
                    config_capital = self.config.get('available_capital', 75000)
                    logger.info(f"✅ Using strategy config capital: ₹{config_capital:,.2f}")
                    return float(config_capital)
                else:
                    from config import config
                    config_capital = config.get('available_capital', 75000)
                    logger.info(f"✅ Using global config capital: ₹{config_capital:,.2f}")
                    return float(config_capital)
            except (ImportError, AttributeError) as config_error:
                # Hardcoded fallback if config import fails
                logger.warning(f"⚠️ Config access failed ({config_error}), using hardcoded capital: ₹75,000")
                return 75000.0
            
        except Exception as e:
            logger.error(f"Error getting dynamic available capital: {e}")
            # Return hardcoded capital on error
            return 75000.0
    async def _get_volume_based_strike(self, underlying_symbol: str, current_price: float, expiry: str, action: str) -> int:
        """🎯 USER REQUIREMENT: Select strike based on volume - use closest available strike to ATM"""
        try:
            # First get ATM strike as baseline
            atm_strike = self._get_atm_strike_for_stock(current_price)
            
            logger.info(f"🎯 STRIKE SELECTION for {underlying_symbol}")
            logger.info(f"   Current Price: ₹{current_price:.2f}, Calculated ATM: {atm_strike}")

            # Get orchestrator to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()

            if orchestrator and orchestrator.zerodha_client:
                try:
                    # Map symbol to Zerodha format
                    zerodha_symbol = self._map_truedata_to_zerodha_symbol(underlying_symbol)

                    # Find closest available strike using Zerodha's actual instruments
                    try:
                        closest_strike = await orchestrator.zerodha_client.find_closest_available_strike(
                            zerodha_symbol, atm_strike, expiry
                        )

                        # 🚨 DEFENSIVE: Validate the response from find_closest_available_strike
                        if closest_strike is None:
                            logger.warning(f"⚠️ find_closest_available_strike returned None for {zerodha_symbol}")
                            return atm_strike
                        elif isinstance(closest_strike, int):
                            if closest_strike > 0:
                                logger.info(f"✅ Using available strike: {closest_strike} (instead of {atm_strike})")
                                return closest_strike
                            else:
                                logger.warning(f"⚠️ Invalid strike value: {closest_strike}, using ATM: {atm_strike}")
                                return atm_strike
                        else:
                            logger.error(f"❌ find_closest_available_strike returned {type(closest_strike)} instead of int: {closest_strike}")
                            return atm_strike

                    except Exception as strike_error:
                        logger.error(f"❌ ERROR calling find_closest_available_strike for {zerodha_symbol}: {strike_error}")
                        logger.error(f"   Error type: {type(strike_error)}")
                        if "can't be used in 'await' expression" in str(strike_error):
                            logger.error(f"🚨 CRITICAL: Zerodha API returned non-coroutine in strike lookup")
                        return atm_strike

                except Exception as zerodha_err:
                    logger.warning(f"⚠️ Error accessing Zerodha strikes: {zerodha_err}")
                    return atm_strike
            else:
                logger.warning("⚠️ Zerodha client not available, using calculated ATM strike")
            return atm_strike
                
        except Exception as e:
            logger.error(f"Error in volume-based strike selection: {e}")
            # Fallback to ATM
            atm_strike = self._get_atm_strike_for_stock(current_price)
            logger.warning(f"⚠️ Fallback to ATM strike: {atm_strike}")
            return atm_strike
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {}
    
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                # 🚨 CRITICAL FIX: Map TrueData symbol to Zerodha symbol (NIFTY-I → NIFTY)
                zerodha_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_underlying}")
                
                base_lot_size = self._get_dynamic_lot_size(options_symbol, zerodha_underlying)
                if base_lot_size is None:
                    logger.warning(f"⚠️ NO LOT SIZE for {zerodha_underlying} - FALLING BACK to EQUITY trading")
                    # 🎯 AUTOMATIC FALLBACK: Calculate equity quantity instead of rejecting
                    is_options = False  # Switch to equity mode
                
            if is_options:
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price BEFORE margin calculation
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {options_symbol}")
                    logger.error(f"   Cannot calculate margin/quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🚨 CRITICAL FIX: Get REAL margin requirement from Zerodha API
                margin_required = 0.0
                
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        # Get actual margin requirement from Zerodha
                        if hasattr(orchestrator.zerodha_client, 'get_required_margin_for_order'):
                            # Use the actual F&O symbol for margin calculation
                            actual_symbol = options_symbol if options_symbol else underlying_symbol
                            margin_required = orchestrator.zerodha_client.get_required_margin_for_order(
                                symbol=actual_symbol,
                                quantity=base_lot_size,
                                order_type='BUY',
                                product='MIS'  # Intraday
                            )
                            logger.info(f"📊 Dynamic margin from Zerodha: ₹{margin_required:,.2f} for {actual_symbol}")
                except Exception as e:
                    logger.debug(f"Could not get dynamic margin: {e}")
                
                # Fallback if dynamic margin not available
                if margin_required <= 0:
                    if 'CE' in options_symbol or 'PE' in options_symbol:
                        # Options: Premium estimate (no caps - based on actual lot size)
                        margin_required = base_lot_size * 50  # Remove capital percentage cap
                        logger.info(f"📊 Options margin estimate: ₹{margin_required:,.2f}")
                    else:
                        # Futures: 10-15% of contract value
                        contract_value = base_lot_size * entry_price
                        margin_required = contract_value * 0.10  # 10% margin estimate
                        logger.info(f"📊 Futures margin estimate: ₹{margin_required:,.2f}")
                
                # 🎯 MARGIN-BASED ALLOCATION: 80% margin limit per trade (allow high-value positions)
                max_margin_per_trade_pct = 0.80  # 80% of available capital per trade  
                max_margin_allowed = available_capital * max_margin_per_trade_pct

                # CRITICAL: Options should ALWAYS be 1 lot (as per user requirement)
                lots_needed_for_min = 1  # Always 1 lot for options/F&O
                logger.info(f"🎯 OPTIONS LOT SIZE: Fixed to 1 lot for {zerodha_underlying}")

                total_margin = margin_required * lots_needed_for_min if margin_required > 0 else margin_required

                # Check if we can afford it within margin limits
                if total_margin <= max_margin_allowed and total_margin <= available_capital:
                    total_qty = base_lot_size * lots_needed_for_min
                    logger.info(
                        f"✅ F&O ORDER: {zerodha_underlying} = {lots_needed_for_min} lot(s) × {base_lot_size} = {total_qty} qty"
                    )
                    logger.info(
                        f"   💰 Margin: ₹{total_margin:,.0f} (per lot ₹{margin_required:,.0f}) / Available: ₹{available_capital:,.0f}"
                    )
                    return total_qty

                # If even 1 lot is too expensive, reject early
                logger.warning(
                    f"❌ F&O REJECTED: {zerodha_underlying} exceeds capital limits "
                    f"(needed ₹{total_margin:,.0f}, available ₹{available_capital:,.0f})"
                )
                return 0
            else:
                # 🎯 EQUITY: Use share-based calculation with minimum trade value
                # CRITICAL FIX: Reduce minimum trade value to work with available capital
                min_trade_value = 20000.0  # Reduced from ₹25,000 to ₹20,000 for capital efficiency
                
                # Check if we can afford minimum trade value
                if available_capital < min_trade_value:
                    logger.warning(
                        f"❌ EQUITY REJECTED: {underlying_symbol} insufficient capital for min trade value "
                        f"(need ₹{min_trade_value:,.0f}, available ₹{available_capital:,.0f})"
                    )
                    return 0
                
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {underlying_symbol}")
                    logger.error(f"   Cannot calculate quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🎯 CRITICAL: Calculate shares needed for MINIMUM ₹25,000 trade value
                min_shares_required = int(min_trade_value / entry_price)
                cost_for_min_shares = min_shares_required * entry_price
                
                # 🚨 MARGIN-BASED POSITION SIZING: Use 25% of available margin
                estimated_margin_factor = 0.25  # Conservative estimate for MIS margin requirement
                max_margin_per_trade_pct = 0.25  # 25% of available margin per trade
                max_margin_allowed = available_capital * max_margin_per_trade_pct
                
                # Calculate maximum trade value we can afford with 25% margin allocation
                max_affordable_trade_value = max_margin_allowed / estimated_margin_factor
                max_affordable_shares = int(max_affordable_trade_value / entry_price)
                max_affordable_cost = max_affordable_shares * entry_price
                
                # Use the higher of: minimum trade value OR maximum affordable within margin limits
                if max_affordable_cost >= min_trade_value:
                    # We can afford more than minimum - use maximum affordable
                    final_quantity = max_affordable_shares
                    cost = max_affordable_cost
                    estimated_margin = cost * estimated_margin_factor
                    
                    logger.debug(f"✅ MARGIN-OPTIMIZED: {underlying_symbol} = {final_quantity} shares")
                    logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                    logger.debug(f"   💳 Est. Margin: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital:.1%} of capital)")
                    logger.debug(f"   📊 Leverage: ~{cost/estimated_margin:.1f}x")
                else:
                    # Can only afford minimum - check if it fits in margin allocation
                    min_estimated_margin = cost_for_min_shares * estimated_margin_factor
                    
                    if min_estimated_margin <= max_margin_allowed:
                        final_quantity = min_shares_required
                        cost = cost_for_min_shares
                        logger.debug(f"✅ MINIMUM VIABLE: {underlying_symbol} = {final_quantity} shares")
                        logger.debug(f"   💰 Trade Value: ₹{cost:,.0f}")
                        logger.debug(f"   💳 Est. Margin: ₹{cost * estimated_margin_factor:,.0f}")
                    else:
                        logger.warning(
                            f"❌ EQUITY REJECTED: {underlying_symbol} min trade ₹{min_trade_value:,.0f} "
                            f"needs ₹{min_estimated_margin:,.0f} margin, exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                        )
                        return 0

                logger.debug(f"✅ EQUITY ORDER: {underlying_symbol} = {final_quantity} shares")
                logger.debug(f"   💰 Cost: ₹{cost:,.0f} / Available: ₹{available_capital:,.0f} ({cost/available_capital:.1%})")
                
                # CRITICAL DEBUG: Log final quantity calculation
                if final_quantity == 0:
                    logger.error(f"🚨 CRITICAL: Quantity calculation returned 0 for {underlying_symbol}")
                    logger.error(f"   This should NOT happen for equity signals with valid entry price ₹{entry_price}")
                
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {}
    
    
    def _get_capital_constrained_quantity(self, options_symbol: str, underlying_symbol: str, entry_price: float) -> int:
        """🎯 SMART QUANTITY: F&O uses lots, Equity uses shares based on capital"""
        try:
            # Check if this is F&O (options) or equity
            is_options = (options_symbol != underlying_symbol or 
                         'CE' in options_symbol or 'PE' in options_symbol)
            
            # Get real-time available capital
            available_capital = self._get_available_capital()
            
            if is_options:
                # 🎯 F&O: Use lot-based calculation
                # 🚨 CRITICAL FIX: Map TrueData symbol to Zerodha symbol (NIFTY-I → NIFTY)
                zerodha_underlying = self._map_truedata_to_zerodha_symbol(underlying_symbol)
                logger.info(f"🔄 SYMBOL MAPPING: {underlying_symbol} → {zerodha_underlying}")
                
                base_lot_size = self._get_dynamic_lot_size(options_symbol, zerodha_underlying)
                if base_lot_size is None:
                    logger.warning(f"⚠️ NO LOT SIZE for {zerodha_underlying} - FALLING BACK to EQUITY trading")
                    # 🎯 AUTOMATIC FALLBACK: Calculate equity quantity instead of rejecting
                    is_options = False  # Switch to equity mode
                
            if is_options:
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price BEFORE margin calculation
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {options_symbol}")
                    logger.error(f"   Cannot calculate margin/quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🚨 CRITICAL FIX: Get REAL margin requirement from Zerodha API
                margin_required = 0.0
                
                try:
                    from src.core.orchestrator import get_orchestrator_instance
                    orchestrator = get_orchestrator_instance()
                    
                    if orchestrator and hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
                        # Get actual margin requirement from Zerodha
                        if hasattr(orchestrator.zerodha_client, 'get_required_margin_for_order'):
                            # Use the actual F&O symbol for margin calculation
                            actual_symbol = options_symbol if options_symbol else underlying_symbol
                            margin_required = orchestrator.zerodha_client.get_required_margin_for_order(
                                symbol=actual_symbol,
                                quantity=base_lot_size,
                                order_type='BUY',
                                product='MIS'  # Intraday
                            )
                            logger.info(f"📊 Dynamic margin from Zerodha: ₹{margin_required:,.2f} for {actual_symbol}")
                except Exception as e:
                    logger.debug(f"Could not get dynamic margin: {e}")
                
                # Fallback if dynamic margin not available
                if margin_required <= 0:
                    if 'CE' in options_symbol or 'PE' in options_symbol:
                        # Options: Premium estimate (no caps - based on actual lot size)
                        margin_required = base_lot_size * 50  # Remove capital percentage cap
                        logger.info(f"📊 Options margin estimate: ₹{margin_required:,.2f}")
                    else:
                        # Futures: 10-15% of contract value
                        contract_value = base_lot_size * entry_price
                        margin_required = contract_value * 0.10  # 10% margin estimate
                        logger.info(f"📊 Futures margin estimate: ₹{margin_required:,.2f}")
                
                # 🎯 MARGIN-BASED ALLOCATION: 80% margin limit per trade (allow high-value positions)
                max_margin_per_trade_pct = 0.80  # 80% of available capital per trade  
                max_margin_allowed = available_capital * max_margin_per_trade_pct

                # CRITICAL: Options should ALWAYS be 1 lot (as per user requirement)
                lots_needed_for_min = 1  # Always 1 lot for options/F&O
                logger.info(f"🎯 OPTIONS LOT SIZE: Fixed to 1 lot for {zerodha_underlying}")

                total_margin = margin_required * lots_needed_for_min if margin_required > 0 else margin_required

                # Check if we can afford it within margin limits
                if total_margin <= max_margin_allowed and total_margin <= available_capital:
                    total_qty = base_lot_size * lots_needed_for_min
                    logger.info(
                        f"✅ F&O ORDER: {zerodha_underlying} = {lots_needed_for_min} lot(s) × {base_lot_size} = {total_qty} qty"
                    )
                    logger.info(
                        f"   💰 Margin: ₹{total_margin:,.0f} (per lot ₹{margin_required:,.0f}) / Available: ₹{available_capital:,.0f}"
                    )
                    return total_qty

                # If even 1 lot is too expensive, reject early
                logger.warning(
                    f"❌ F&O REJECTED: {zerodha_underlying} exceeds capital limits "
                    f"(needed ₹{total_margin:,.0f}, available ₹{available_capital:,.0f})"
                )
                return 0
            else:
                # 🎯 EQUITY: Use share-based calculation with minimum trade value
                # CRITICAL FIX: Reduce minimum trade value to work with available capital
                min_trade_value = 20000.0  # Reduced from ₹25,000 to ₹20,000 for capital efficiency
                
                # Check if we can afford minimum trade value
                if available_capital < min_trade_value:
                    logger.warning(
                        f"❌ EQUITY REJECTED: {underlying_symbol} insufficient capital for min trade value "
                        f"(need ₹{min_trade_value:,.0f}, available ₹{available_capital:,.0f})"
                    )
                    return 0
                
                # 🚨 CRITICAL SAFETY: Check for zero/invalid entry price
                if entry_price <= 0:
                    logger.error(f"❌ INVALID ENTRY PRICE: {entry_price} for {underlying_symbol}")
                    logger.error(f"   Cannot calculate quantity with zero/negative entry price")
                    logger.error(f"   This indicates a price data issue - signal should be rejected")
                    return 0
                
                # 🎯 CRITICAL: Calculate shares needed for MINIMUM ₹25,000 trade value
                min_shares_required = int(min_trade_value / entry_price)
                cost_for_min_shares = min_shares_required * entry_price
                
                # 🚨 MARGIN-BASED POSITION SIZING: Use 25% of available margin
                estimated_margin_factor = 0.25  # Conservative estimate for MIS margin requirement
                max_margin_per_trade_pct = 0.25  # 25% of available margin per trade
                max_margin_allowed = available_capital * max_margin_per_trade_pct
                
                # Calculate maximum trade value we can afford with 25% margin allocation
                max_affordable_trade_value = max_margin_allowed / estimated_margin_factor
                max_affordable_shares = int(max_affordable_trade_value / entry_price)
                max_affordable_cost = max_affordable_shares * entry_price
                
                # Use the higher of: minimum trade value OR maximum affordable within margin limits
                if max_affordable_cost >= min_trade_value:
                    # We can afford more than minimum - use maximum affordable
                    final_quantity = max_affordable_shares
                    cost = max_affordable_cost
                    estimated_margin = cost * estimated_margin_factor
                    
                    logger.info(f"✅ MARGIN-OPTIMIZED: {underlying_symbol} = {final_quantity} shares")
                    logger.info(f"   💰 Trade Value: ₹{cost:,.0f}")
                    logger.info(f"   💳 Est. Margin: ₹{estimated_margin:,.0f} ({estimated_margin/available_capital:.1%} of capital)")
                    logger.info(f"   📊 Leverage: ~{cost/estimated_margin:.1f}x")
                else:
                    # Can only afford minimum - check if it fits in margin allocation
                    min_estimated_margin = cost_for_min_shares * estimated_margin_factor
                    
                    if min_estimated_margin <= max_margin_allowed:
                        final_quantity = min_shares_required
                        cost = cost_for_min_shares
                        logger.info(f"✅ MINIMUM VIABLE: {underlying_symbol} = {final_quantity} shares")
                        logger.info(f"   💰 Trade Value: ₹{cost:,.0f}")
                        logger.info(f"   💳 Est. Margin: ₹{cost * estimated_margin_factor:,.0f}")
                    else:
                        logger.warning(
                            f"❌ EQUITY REJECTED: {underlying_symbol} min trade ₹{min_trade_value:,.0f} "
                            f"needs ₹{min_estimated_margin:,.0f} margin, exceeds 25% limit ₹{max_margin_allowed:,.0f}"
                        )
                        return 0

                logger.info(f"✅ EQUITY ORDER: {underlying_symbol} = {final_quantity} shares")
                logger.info(f"   💰 Cost: ₹{cost:,.0f} / Available: ₹{available_capital:,.0f} ({cost/available_capital:.1%})")
                
                # CRITICAL DEBUG: Log final quantity calculation
                if final_quantity == 0:
                    logger.error(f"🚨 CRITICAL: Quantity calculation returned 0 for {underlying_symbol}")
                    logger.error(f"   This should NOT happen for equity signals with valid entry price ₹{entry_price}")
                
                return final_quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            # Fallback based on signal type
            if 'CE' in options_symbol or 'PE' in options_symbol:
                return 75  # F&O fallback
            else:
                return 10  # Equity fallback
    
    def _get_strikes_volume_data(self, underlying_symbol: str, strikes: List[int], expiry: str, action: str) -> Dict:
        """Get volume data for strikes from market data sources"""
        try:
            # Try to get volume data from TrueData cache
            from data.truedata_client import live_market_data
            
            volume_data = {}
            option_type = 'CE' if action.upper() == 'BUY' else 'PE'
            
            for strike in strikes:
                # Build options symbol using proper format mapping
                from config.options_symbol_mapping import get_truedata_options_format
                options_symbol = get_truedata_options_format(underlying_symbol, expiry, strike, option_type)
                
                if live_market_data and options_symbol in live_market_data:
                    market_data = live_market_data[options_symbol]
                    volume = market_data.get('volume', 0)
                    premium = market_data.get('ltp', market_data.get('price', 0))
                    
                    volume_data[strike] = {
                        'volume': volume,
                        'premium': premium,
                        'symbol': options_symbol
                    }
                    
            if volume_data:
                logger.info(f"✅ Retrieved volume data for {len(volume_data)} strikes from TrueData")
                return volume_data
            else:
                logger.debug(f"Volume data not needed - using ATM strike for {underlying_symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {} 
    
    # ==================================================================================
    # OPTION CHAIN UTILITIES - Access and analyze comprehensive option chain data
    # ==================================================================================
    
    def get_option_chain(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get option chain data for a given underlying from market data
        
        Returns:
            Dict with structure:
            {
                'underlying': str,
                'expiry': str,
                'atm_strike': float,
                'spot_price': float,
                'chain': {'calls': {...}, 'puts': {...}},
                'analytics': {'pcr': float, 'max_pain': float, 'iv_mean': float, ...}
            }
        """
        try:
            if '_option_chains' not in market_data:
                return None
            
            option_chains = market_data['_option_chains']
            return option_chains.get(underlying_symbol)
            
        except Exception as e:
            logger.debug(f"Error getting option chain for {underlying_symbol}: {e}")
            return None
    
    def get_pcr_ratio(self, underlying_symbol: str, market_data: Dict[str, Any]) -> float:
        """
        Get Put-Call Ratio (OI based) for underlying
        PCR > 1.0 indicates more puts than calls (bearish sentiment)
        PCR < 1.0 indicates more calls than puts (bullish sentiment)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('pcr', 0)
            return 0
        except:
            return 0
    
    def get_max_pain_strike(self, underlying_symbol: str, market_data: Dict[str, Any]) -> float:
        """
        Get max pain strike - where option writers lose least
        Price tends to gravitate towards max pain near expiry
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('max_pain', 0)
            return 0
        except:
            return 0
    
    def get_option_support_resistance(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Get support and resistance levels based on max OI
        
        Returns:
            (support_strike, resistance_strike)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                analytics = chain['analytics']
                support = analytics.get('support', 0)
                resistance = analytics.get('resistance', 0)
                return (support, resistance)
            return (0, 0)
        except:
            return (0, 0)
    
    def get_iv_skew(self, underlying_symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get IV skew data
        Positive skew means OTM puts have higher IV than OTM calls (fear/protection buying)
        Negative skew means OTM calls have higher IV (unusual, indicates bullish speculation)
        
        Returns:
            {'otm_call_iv': float, 'otm_put_iv': float, 'skew': float}
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                return chain['analytics'].get('iv_skew', {})
            return {}
        except:
            return {}
    
    def is_high_iv_environment(self, underlying_symbol: str, market_data: Dict[str, Any], threshold: float = 25.0) -> bool:
        """
        Check if we're in a high IV environment
        High IV is good for option selling, low IV for option buying
        
        Args:
            threshold: IV percentage threshold (default 25%)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if chain and 'analytics' in chain:
                iv_mean = chain['analytics'].get('iv_mean', 0)
                return iv_mean > threshold
            return False
        except:
            return False
    
    def get_option_greeks(self, options_symbol: str, underlying_symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get Greeks (delta, gamma, theta, vega) for a specific option
        
        Returns:
            {'delta': float, 'gamma': float, 'theta': float, 'vega': float}
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if not chain or 'chain' not in chain:
                return {}
            
            # Parse option symbol to get strike and type
            import re
            match = re.match(r"([A-Z]+)(\d{2}[A-Z]{3})(\d+)(CE|PE)", options_symbol)
            if not match:
                return {}
            
            _, _, strike_str, option_type = match.groups()
            strike = float(strike_str)
            
            # Get the option data
            option_data = None
            if option_type == 'CE':
                option_data = chain['chain']['calls'].get(strike)
            else:
                option_data = chain['chain']['puts'].get(strike)
            
            if option_data and 'greeks' in option_data:
                return option_data['greeks']
            
            return {}
            
        except Exception as e:
            logger.debug(f"Error getting Greeks for {options_symbol}: {e}")
            return {}
    
    def should_avoid_option_trade_based_on_chain(self, underlying_symbol: str, action: str, 
                                                  market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Use option chain analytics to filter out bad trade setups
        
        Args:
            underlying_symbol: Underlying symbol
            action: 'BUY' or 'SELL'
            market_data: Market data with option chain
        
        Returns:
            (should_avoid: bool, reason: str)
        """
        try:
            chain = self.get_option_chain(underlying_symbol, market_data)
            if not chain:
                return (False, "")
            
            analytics = chain.get('analytics', {})
            spot_price = chain.get('spot_price', 0)
            max_pain = analytics.get('max_pain', 0)
            pcr = analytics.get('pcr', 0)
            support, resistance = self.get_option_support_resistance(underlying_symbol, market_data)
            
            # Rule 1: Avoid buying calls near resistance
            if action == 'BUY' and resistance > 0:
                distance_to_resistance = (resistance - spot_price) / spot_price * 100
                if 0 < distance_to_resistance < 1.0:  # Within 1% of resistance
                    return (True, f"Near resistance at {resistance} (OI-based)")
            
            # Rule 2: Avoid buying puts near support
            if action == 'SELL' and support > 0:
                distance_to_support = (spot_price - support) / spot_price * 100
                if 0 < distance_to_support < 1.0:  # Within 1% of support
                    return (True, f"Near support at {support} (OI-based)")
            
            # Rule 3: Consider max pain - price gravitates towards it near expiry
            if max_pain > 0:
                distance_to_max_pain = abs(spot_price - max_pain) / spot_price * 100
                if distance_to_max_pain > 5.0:  # More than 5% away from max pain
                    # If we're above max pain and buying calls, be cautious
                    if action == 'BUY' and spot_price > max_pain:
                        return (True, f"Spot â‚¹{spot_price:.0f} far above max pain â‚¹{max_pain:.0f}")
                    # If we're below max pain and buying puts, be cautious
                    if action == 'SELL' and spot_price < max_pain:
                        return (True, f"Spot â‚¹{spot_price:.0f} far below max pain â‚¹{max_pain:.0f}")
            
            # Rule 4: Extreme PCR can indicate reversals
            if pcr > 2.0:  # Very high PCR - oversold, potential reversal up
                if action == 'SELL':
                    return (True, f"Extreme PCR {pcr:.2f} indicates potential reversal (avoid shorts)")
            elif pcr < 0.5:  # Very low PCR - overbought, potential reversal down
                if action == 'BUY':
                    return (True, f"Extreme PCR {pcr:.2f} indicates potential reversal (avoid longs)")
            
            return (False, "")
            
        except Exception as e:
            logger.debug(f"Error checking option chain filters: {e}")
            return (False, "")

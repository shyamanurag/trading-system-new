"""
Base Strategy Class - SCALPING OPTIMIZED
Common functionality for all trading strategies with proper ATR calculation and SCALPING risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
import numpy as np
import pytz  # Add timezone support

logger = logging.getLogger(__name__)

class BaseStrategy:
    """Base class for all trading strategies with SCALPING-OPTIMIZED timing and risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = "BaseStrategy"
        self.is_active = False
        self.current_positions = {}
        self.performance_metrics = {}
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown_seconds', 1)
        
        # SCALPING-OPTIMIZED cooldown controls
        self.scalping_cooldown = config.get('scalping_cooldown_seconds', 15)  # Default 15 seconds
        self.symbol_cooldowns = {}  # Symbol-specific cooldowns
        
        # Historical data for proper ATR calculation
        self.historical_data = {}  # symbol -> list of price data
        self.max_history = 50  # Keep last 50 data points per symbol
        
    def _is_scalping_cooldown_passed(self) -> bool:
        """Check if SCALPING cooldown period has passed"""
        if not self.last_signal_time:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.scalping_cooldown
    
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
        """Check if within trading hours - FIXED: Now uses IST timezone"""
        try:
            # Get current time in IST (same as orchestrator)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # NSE trading hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                logger.info(f"🚫 SAFETY: Trading blocked on weekend. Current day: {now.strftime('%A')}")
                return False
            
            is_trading_time = market_open <= current_time <= market_close
            
            if not is_trading_time:
                logger.info(f"🚫 SAFETY: Trading blocked outside market hours. Current IST time: {current_time} "
                           f"(Market: {market_open} - {market_close})")
            else:
                logger.info(f"✅ TRADING HOURS: Market open. Current IST time: {current_time}")
            
            return is_trading_time
            
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            # SAFETY: If timezone check fails, default to False (safer)
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
        """Calculate Average True Range - PROPER IMPLEMENTATION"""
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
            
            # Calculate ATR
            history = self.historical_data[symbol]
            if len(history) < 2:
                # Not enough data for ATR - use simple range
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # Calculate True Range for recent periods
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
            
            # Calculate ATR as average of True Ranges
            if len(true_ranges) == 0:
                return current_high - current_low if current_high > current_low else current_close * 0.01
            
            # Use available data or period, whichever is smaller
            atr_period = min(period, len(true_ranges))
            recent_trs = true_ranges[-atr_period:]
            
            atr = np.mean(recent_trs)
            
            # Ensure minimum ATR (0.1% of price) and reasonable maximum (10% of price)
            min_atr = current_close * 0.001
            max_atr = current_close * 0.1
            
            return max(min_atr, min(atr, max_atr))
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {e}")
            # Fallback to simple range calculation
            return current_high - current_low if current_high > current_low else current_close * 0.01
    
    def calculate_dynamic_stop_loss(self, entry_price: float, atr: float, action: str, 
                                   multiplier: float = 2.0, min_percent: float = 0.5, 
                                   max_percent: float = 5.0) -> float:
        """Calculate dynamic stop loss based on ATR with SCALPING-OPTIMIZED bounds"""
        try:
            # Calculate ATR-based stop loss distance
            atr_distance = atr * multiplier
            
            # Convert to percentage
            atr_percent = (atr_distance / entry_price) * 100
            
            # Apply SCALPING-OPTIMIZED bounds (tighter than original)
            bounded_percent = max(min_percent, min(atr_percent, max_percent))
            bounded_distance = (bounded_percent / 100) * entry_price
            
            # Calculate stop loss based on action
            if action.upper() == 'BUY':
                stop_loss = entry_price - bounded_distance
            else:  # SELL
                stop_loss = entry_price + bounded_distance
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            # Fallback to percentage-based stop loss
            fallback_percent = 0.5  # 0.5% fallback for scalping
            if action.upper() == 'BUY':
                return entry_price * (1 - fallback_percent / 100)
            else:
                return entry_price * (1 + fallback_percent / 100)
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                risk_reward_ratio: float = 1.5) -> float:
        """Calculate dynamic target with SCALPING-OPTIMIZED risk/reward ratio"""
        try:
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            
            # Calculate reward distance
            reward_distance = risk_distance * risk_reward_ratio
            
            # Calculate target based on entry vs stop loss relationship
            if stop_loss < entry_price:  # BUY trade
                target = entry_price + reward_distance
            else:  # SELL trade
                target = entry_price - reward_distance
            
            return round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating dynamic target: {e}")
            # Fallback to simple percentage target
            if stop_loss < entry_price:  # BUY trade
                return entry_price * 1.015  # 1.5% target for scalping
            else:  # SELL trade
                return entry_price * 0.985  # 1.5% target for scalping
    
    def validate_signal_levels(self, entry_price: float, stop_loss: float, 
                              target: float, action: str) -> bool:
        """Validate that signal levels make logical sense"""
        try:
            if action.upper() == 'BUY':
                # For BUY: stop_loss < entry_price < target
                if not (stop_loss < entry_price < target):
                    logger.warning(f"Invalid BUY signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
            else:  # SELL
                # For SELL: target < entry_price < stop_loss
                if not (target < entry_price < stop_loss):
                    logger.warning(f"Invalid SELL signal levels: SL={stop_loss}, Entry={entry_price}, Target={target}")
                    return False
            
            # Check risk/reward ratio is reasonable (0.5:1 to 5:1)
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            
            if risk <= 0:
                logger.warning(f"Zero or negative risk: {risk}")
                return False
            
            risk_reward_ratio = reward / risk
            if risk_reward_ratio < 0.5 or risk_reward_ratio > 5.0:
                logger.warning(f"Unreasonable risk/reward ratio: {risk_reward_ratio}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal levels: {e}")
            return False
    
    def create_standard_signal(self, symbol: str, action: str, entry_price: float, 
                              stop_loss: float, target: float, confidence: float, 
                              metadata: Dict) -> Optional[Dict]:
        """Create standardized signal format for all strategies"""
        try:
            # 🎯 CRITICAL FIX: Convert to options symbol for scalping strategies
            options_symbol, option_type = self._convert_to_options_symbol(symbol, entry_price, action)
            
            # 🎯 CRITICAL FIX: Get actual options premium from TrueData instead of stock price
            options_entry_price = self._get_options_premium(options_symbol, entry_price, option_type)
            
            # 🎯 CRITICAL FIX: Calculate correct stop_loss and target for options
            options_stop_loss, options_target = self._calculate_options_levels(
                options_entry_price, stop_loss, target, option_type, action
            )
            
            # Validate signal levels with OPTIONS pricing
            if not self.validate_signal_levels(options_entry_price, options_stop_loss, options_target, 'BUY'):
                logger.warning(f"Invalid options signal levels: Entry={options_entry_price}, SL={options_stop_loss}, Target={options_target}")
                return None
            
            # 🎯 CRITICAL FIX: Always BUY options (no selling due to margin requirements)
            final_action = 'BUY'  # Force all options signals to be BUY
            
            # Calculate risk metrics using OPTIONS pricing
            risk_amount = abs(options_entry_price - options_stop_loss)
            reward_amount = abs(options_target - options_entry_price)
            risk_percent = (risk_amount / options_entry_price) * 100
            reward_percent = (reward_amount / options_entry_price) * 100
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # CRITICAL FIX: Generate unique signal_id for tracking
            signal_id = f"{self.name}_{options_symbol}_{int(datetime.now().timestamp())}"
            
            return {
                # Core signal fields (consistent naming)
                'signal_id': signal_id,
                'symbol': options_symbol,  # 🎯 FIXED: Use options symbol instead of underlying
                'underlying_symbol': symbol,  # Keep original for reference
                'option_type': option_type,  # CE or PE
                'action': final_action.upper(),  # Always BUY for options (no selling due to margin)
                'quantity': self._get_dynamic_lot_size(options_symbol, symbol),  # 🎯 DYNAMIC: Get actual lot size
                'entry_price': round(options_entry_price, 2),  # 🎯 FIXED: Use options premium
                'stop_loss': round(options_stop_loss, 2),      # 🎯 FIXED: Correct options stop_loss
                'target': round(options_target, 2),            # 🎯 FIXED: Correct options target
                'strategy': self.name,  # Use 'strategy' for compatibility
                'strategy_name': self.name,  # Also include strategy_name for new components
                'confidence': round(min(confidence, 0.9), 2),
                'quality_score': round(min(confidence, 0.9), 2),  # Map confidence to quality_score
                
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
    
    def _convert_to_options_symbol(self, underlying_symbol: str, current_price: float, action: str) -> tuple:
        """Convert underlying symbol to appropriate options symbol for scalping"""
        try:
            # 🎯 CRITICAL FIX: Only BUY signals for options (no selling due to margin requirements)
            # Convert equity signals to options BUY signals only
            if underlying_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index options - use current levels
                strike = self._get_atm_strike(underlying_symbol, current_price)
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                expiry = self._get_next_expiry()
                options_symbol = f"{underlying_symbol}{expiry}{strike}{option_type}"
                return options_symbol, option_type
            else:
                # Stock options - convert equity to options
                # CRITICAL FIX: Truncate long symbol names for options
                truncated_symbol = self._truncate_symbol_for_options(underlying_symbol)
                strike = self._get_atm_strike_for_stock(current_price)
                # CRITICAL CHANGE: Always BUY options, choose CE/PE based on market direction
                if action.upper() == 'BUY':
                    option_type = 'CE'  # BUY Call when bullish
                else:  # SELL signal becomes BUY Put
                    option_type = 'PE'  # BUY Put when bearish
                    
                expiry = self._get_next_expiry()
                options_symbol = f"{truncated_symbol}{expiry}{strike}{option_type}"
                return options_symbol, option_type
                
        except Exception as e:
            logger.error(f"Error converting to options symbol: {e}")
            # Fallback to underlying symbol
            return underlying_symbol, 'EQUITY'
    
    def _get_atm_strike(self, symbol: str, price: float) -> int:
        """Get ATM strike for index options"""
        if symbol == 'NIFTY':
            return round(price / 50) * 50  # Round to nearest 50
        elif symbol == 'BANKNIFTY':
            return round(price / 100) * 100  # Round to nearest 100
        elif symbol == 'FINNIFTY':
            return round(price / 50) * 50  # Round to nearest 50
        else:
            return int(price)
    
    def _get_atm_strike_for_stock(self, price: float) -> int:
        """Get ATM strike for stock options - FIXED with realistic strikes"""
        # CRITICAL FIX: Use more realistic strike intervals for stocks
        if price < 50:
            return int(round(price / 2.5) * 2.5)  # Round to nearest 2.5 for low-priced stocks
        elif price < 100:
            return int(round(price / 5) * 5)  # Round to nearest 5
        elif price < 200:
            return int(round(price / 10) * 10)  # Round to nearest 10
        elif price < 500:
            return int(round(price / 20) * 20)  # Round to nearest 20
        elif price < 1000:
            return int(round(price / 50) * 50)  # Round to nearest 50
        else:
            return int(round(price / 100) * 100)  # Round to nearest 100 for high-priced stocks
      
    def _get_next_expiry(self) -> str:
        """DYNAMIC EXPIRY SELECTION: Get optimal expiry based on strategy requirements"""
        # This method will be called with specific requirements
        return self._get_optimal_expiry_for_strategy()
    
    def _get_optimal_expiry_for_strategy(self, preference: str = "nearest_weekly") -> str:
        """
        Get optimal expiry based on strategy requirements
        
        Args:
            preference: "nearest_weekly", "nearest_monthly", "next_weekly", "max_time_decay"
        """
        available_expiries = self._get_available_expiries_from_zerodha()
        
        if not available_expiries:
            # Fallback to calculated next Thursday if API unavailable
            return self._calculate_next_thursday_fallback()
        
        today = datetime.now().date()
        
        # Filter future expiries only
        future_expiries = [exp for exp in available_expiries if exp['date'] > today]
        
        if not future_expiries:
            return self._calculate_next_thursday_fallback()
        
        # Sort by date
        future_expiries.sort(key=lambda x: x['date'])
        
        # Strategy-based selection
        if preference == "nearest_weekly":
            # Prefer weekly expiries (usually nearest)
            weekly_expiries = [exp for exp in future_expiries if exp.get('is_weekly', True)]
            return weekly_expiries[0]['formatted'] if weekly_expiries else future_expiries[0]['formatted']
            
        elif preference == "nearest_monthly":
            # Prefer monthly expiries (last Thursday of month)
            monthly_expiries = [exp for exp in future_expiries if exp.get('is_monthly', False)]
            return monthly_expiries[0]['formatted'] if monthly_expiries else future_expiries[0]['formatted']
            
        elif preference == "next_weekly":
            # Skip current week, get next week
            if len(future_expiries) > 1:
                return future_expiries[1]['formatted']
            else:
                return future_expiries[0]['formatted']
                
        elif preference == "max_time_decay":
            # For theta strategies - longer expiry
            if len(future_expiries) >= 3:
                return future_expiries[2]['formatted']  # 3rd nearest expiry
            else:
                return future_expiries[-1]['formatted']  # Longest available
        
        # Default: nearest expiry
        return future_expiries[0]['formatted']
    
    def _get_available_expiries_from_zerodha(self) -> List[Dict]:
        """
        Fetch available expiry dates from Zerodha instruments API
        Returns list of {date: datetime.date, formatted: str, is_weekly: bool, is_monthly: bool}
        """
        try:
            # Get orchestrator instance to access Zerodha client
            from src.core.orchestrator import get_orchestrator_instance
            orchestrator = get_orchestrator_instance()
            
            if not orchestrator or not orchestrator.zerodha_client:
                logger.warning("⚠️ Zerodha client not available for expiry lookup")
                return self._get_fallback_expiries()
            
            # Use the new async method - we'll need to handle this synchronously
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Try to get expiries for common underlying symbols we trade
            all_expiries = set()
            
            # Get expiries for indices and stocks we commonly trade
            common_symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'POWERGRID', 'RELIANCE', 'TCS']
            
            for symbol in common_symbols:
                try:
                    if loop.is_running():
                        # If we're already in an async context, use the fallback
                        expiries = self._get_fallback_expiries()
                        return expiries
                    else:
                        # Run the async method
                        expiries = loop.run_until_complete(
                            orchestrator.zerodha_client.get_available_expiries_for_symbol(symbol)
                        )
                        
                        if expiries:
                            # Use expiries from the first successful symbol lookup
                            logger.info(f"📅 Using expiries from {symbol}: {len(expiries)} found")
                            return expiries
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get expiries for {symbol}: {e}")
                    continue
            
            # If no expiries found from API, use fallback
            logger.warning("⚠️ No expiries found from Zerodha API, using fallback")
            return self._get_fallback_expiries()
            
        except Exception as e:
            logger.error(f"❌ Error fetching available expiries: {e}")
            return self._get_fallback_expiries()
    
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
            
            # Format for Zerodha: 31JUL25
            month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            formatted = f"{thursday.day:02d}{month_names[thursday.month - 1]}{str(thursday.year)[-2:]}"
            
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
        """Fallback calculation for next Thursday when API is unavailable"""
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
        if days_ahead == 0:
            days_ahead = 7  # If today is Thursday, get next Thursday
            
        next_thursday = today + timedelta(days=days_ahead)
        
        # Format for Zerodha
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        return f"{next_thursday.day:02d}{month_names[next_thursday.month - 1]}{str(next_thursday.year)[-2:]}"
    
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
    
    async def on_market_data(self, data: Dict):
        """Handle incoming market data - to be implemented by subclasses"""
        pass
    
    async def shutdown(self):
        """Shutdown the strategy"""
        logger.info(f"Shutting down {self.name} strategy")
        self.is_active = False 

    def _get_options_premium(self, options_symbol: str, fallback_price: float, option_type: str) -> float:
        """Get actual options premium from TrueData cache"""
        try:
            # Try to get options premium from TrueData global cache
            try:
                from data.truedata_client import live_market_data
                if live_market_data and options_symbol in live_market_data:
                    options_data = live_market_data[options_symbol]
                    # Extract LTP (Last Traded Price) for options premium
                    premium = options_data.get('ltp', options_data.get('price', options_data.get('last_price')))
                    if premium and premium > 0:
                        logger.info(f"✅ Got options premium from TrueData: {options_symbol} = ₹{premium}")
                        return float(premium)
            except Exception as e:
                logger.debug(f"Could not access TrueData for {options_symbol}: {e}")
            
            # Fallback: Estimate options premium dynamically based on market conditions
            estimated_premium = self._estimate_options_premium_dynamic(fallback_price, option_type, options_symbol)
            logger.warning(f"⚠️ Using dynamic estimation for {options_symbol}: ₹{estimated_premium}")
            return estimated_premium
            
        except Exception as e:
            logger.error(f"Error getting options premium for {options_symbol}: {e}")
            # Final fallback
            return self._estimate_options_premium_dynamic(fallback_price, option_type, options_symbol)
    
    def _estimate_options_premium_dynamic(self, underlying_price: float, option_type: str, options_symbol: str) -> float:
        """Dynamically estimate options premium based on market conditions"""
        try:
            # Extract strike and expiry from options symbol for dynamic calculation
            strike_price = self._extract_strike_from_symbol(options_symbol)
            days_to_expiry = self._calculate_days_to_expiry(options_symbol)
            
            # Calculate moneyness (how far the option is from ATM)
            moneyness = abs(underlying_price - strike_price) / underlying_price
            
            # Calculate time value factor (more time = higher premium)
            time_value_factor = max(0.1, min(1.0, days_to_expiry / 30))  # 30 days max
            
            # Calculate volatility factor based on recent price movements
            volatility_factor = self._calculate_dynamic_volatility_factor(underlying_price)
            
            # Base premium calculation using Black-Scholes approximation
            intrinsic_value = max(0, underlying_price - strike_price) if option_type == 'CE' else max(0, strike_price - underlying_price)
            time_value = underlying_price * volatility_factor * time_value_factor * (1 - moneyness)
            
            estimated_premium = intrinsic_value + time_value
            
            # Dynamic bounds based on underlying price
            min_premium = underlying_price * 0.001  # 0.1% minimum
            max_premium = underlying_price * 0.2    # 20% maximum
            estimated_premium = max(min_premium, min(estimated_premium, max_premium))
            
            logger.info(f"📊 Dynamic estimation: {option_type} premium = ₹{estimated_premium:.2f}")
            logger.info(f"   Underlying: ₹{underlying_price}, Strike: ₹{strike_price}")
            logger.info(f"   Days to expiry: {days_to_expiry}, Volatility factor: {volatility_factor:.3f}")
            
            return estimated_premium
            
        except Exception as e:
            logger.error(f"Error in dynamic estimation: {e}")
            # Simple fallback based on underlying price percentage
            return underlying_price * 0.02  # 2% of underlying as fallback
    
    def _calculate_options_levels(self, options_entry_price: float, original_stop_loss: float, 
                                 original_target: float, option_type: str, action: str) -> tuple:
        """Dynamically calculate stop_loss and target for options premium"""
        try:
            # Calculate the original risk-reward ratio from underlying signal
            underlying_risk = abs(original_stop_loss - original_target)
            original_entry = (original_stop_loss + original_target) / 2  # Approximate original entry
            underlying_risk_percent = (underlying_risk / original_entry) * 100
            
            # Calculate original reward-to-risk ratio dynamically
            original_reward = abs(original_target - original_entry)
            original_risk_amount = abs(original_stop_loss - original_entry)
            original_rr_ratio = original_reward / original_risk_amount if original_risk_amount > 0 else 2.0
            
            # Calculate dynamic options multiplier based on volatility and time
            options_multiplier = self._calculate_dynamic_options_multiplier(option_type, options_entry_price)
            
            # Calculate options premium movements dynamically
            risk_amount = options_entry_price * (underlying_risk_percent / 100) * options_multiplier
            reward_amount = risk_amount * original_rr_ratio  # Use original risk-reward ratio
            
            # For BUY actions (all our options signals):
            # - stop_loss = Lower premium (cut losses)
            # - target = Higher premium (take profits)
            options_stop_loss = options_entry_price - risk_amount
            options_target = options_entry_price + reward_amount
            
            # Dynamic bounds based on entry price
            min_stop_loss = options_entry_price * 0.05  # Max 95% loss
            options_stop_loss = max(options_stop_loss, min_stop_loss)
            
            logger.info(f"📊 Dynamic options levels:")
            logger.info(f"   Entry: ₹{options_entry_price:.2f}")
            logger.info(f"   Stop Loss: ₹{options_stop_loss:.2f} (Risk: ₹{risk_amount:.2f})")
            logger.info(f"   Target: ₹{options_target:.2f} (Reward: ₹{reward_amount:.2f})")
            logger.info(f"   Original R:R = {original_rr_ratio:.2f}, Options Multiplier = {options_multiplier:.2f}")
            
            return options_stop_loss, options_target
            
        except Exception as e:
            logger.error(f"Error calculating dynamic options levels: {e}")
            # Dynamic fallback based on entry price
            risk_percent = 0.2  # 20% risk
            reward_percent = risk_percent * 2.5  # Dynamic reward based on risk
            stop_loss = options_entry_price * (1 - risk_percent)
            target = options_entry_price * (1 + reward_percent)
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
        """Extract strike price from options symbol"""
        try:
            # Extract numeric part before CE/PE
            import re
            match = re.search(r'(\d+)(CE|PE)$', options_symbol)
            if match:
                return float(match.group(1))
            # Fallback: try to extract any number
            numbers = re.findall(r'\d+', options_symbol)
            return float(numbers[-1]) if numbers else 1000.0
        except Exception as e:
            logger.error(f"Error extracting strike from {options_symbol}: {e}")
            return 1000.0  # Fallback
    
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
        """Get dynamic lot size based on options contract specifications"""
        try:
            # Try to get lot size from TrueData or predefined mappings
            if underlying_symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                # Index options have standard lot sizes
                lot_sizes = {'NIFTY': 50, 'BANKNIFTY': 15, 'FINNIFTY': 40}
                return lot_sizes.get(underlying_symbol, 50)
            else:
                # Stock options typically have lot size based on price
                # Higher priced stocks have smaller lot sizes
                try:
                    from data.truedata_client import live_market_data
                    if live_market_data and underlying_symbol in live_market_data:
                        stock_price = live_market_data[underlying_symbol].get('ltp', 1000)
                        if stock_price > 5000:
                            return 50  # Small lot for expensive stocks
                        elif stock_price > 1000:
                            return 100  # Medium lot
                        else:
                            return 200  # Large lot for cheaper stocks
                except:
                    pass
                
                # Fallback: standard lot size
                return 100
                
        except Exception as e:
            logger.error(f"Error getting lot size for {options_symbol}: {e}")
            return 50  # Safe fallback 
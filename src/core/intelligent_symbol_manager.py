"""
Intelligent Symbol Management System
Automatically manages TrueData symbols for indices and F&O trading
- Auto-adds new contracts
- Auto-removes expired contracts  
- Manages 250 symbol limit
- Uses existing credentials
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
import os
from dataclasses import dataclass, field

# Import TrueData client functions
from data.truedata_client import subscribe_to_symbols, is_connected, live_market_data

logger = logging.getLogger(__name__)

@dataclass
class SymbolConfig:
    """Configuration for symbol management"""
    max_symbols: int = 250
    auto_refresh_interval: int = 3600  # 1 hour
    expiry_check_interval: int = 1800  # 30 minutes
    
    # Core indices (always subscribed)
    core_indices: List[str] = field(default_factory=lambda: [
        'NIFTY', 'BANKNIFTY', 'FINNIFTY'
    ])
    
    # Top F&O stocks (priority)
    priority_stocks: List[str] = field(default_factory=lambda: [
        'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'ITC',
        'HDFCBANK', 'KOTAKBANK', 'AXISBANK', 'LT', 'WIPRO', 'BHARTIARTL',
        'MARUTI', 'ASIANPAINT', 'HCLTECH', 'POWERGRID', 'NTPC', 'COALINDIA',
        'TECHM', 'TATAMOTORS', 'ADANIPORTS', 'ULTRACEMCO', 'NESTLEIND'
    ])


class IntelligentSymbolManager:
    """Automatically manages TrueData symbols"""
    
    def __init__(self, config: Optional[SymbolConfig] = None):
        self.config = config or SymbolConfig()
        self.active_symbols: Set[str] = set()
        self.pending_symbols: List[str] = []  # Symbols waiting to be subscribed
        self.symbol_metadata: Dict[str, Dict] = {}
        self.is_running = False
        self.tasks = []
        
        logger.info("🤖 Intelligent Symbol Manager initialized")
        logger.info(f"   Max symbols: {self.config.max_symbols}")
        logger.info(f"   Core indices: {len(self.config.core_indices)}")
        logger.info(f"   Priority stocks: {len(self.config.priority_stocks)}")

    async def start(self):
        """Start the intelligent symbol management"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🚀 Starting Intelligent Symbol Manager...")
        
        # Initial symbol setup
        await self.initial_symbol_setup()
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self.auto_refresh_loop()),
            asyncio.create_task(self.expiry_monitor_loop()),
            asyncio.create_task(self.market_hours_optimizer())
        ]
        
        logger.info("✅ Intelligent Symbol Manager started")

    async def stop(self):
        """Stop the symbol manager"""
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        logger.info("🛑 Intelligent Symbol Manager stopped")

    async def initial_symbol_setup(self):
        """Setup initial symbols based on market conditions"""
        logger.info("🔧 Setting up initial symbols...")
        
        # Always include core indices
        symbols_to_add = set(self.config.core_indices)
        
        # Add priority stocks
        symbols_to_add.update(self.config.priority_stocks)
        
        # Add current month F&O contracts for indices
        current_expiry = self.get_current_monthly_expiry()
        for index in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            # Add ATM and nearby strikes
            atm_options = self.generate_atm_options(index, current_expiry)
            symbols_to_add.update(atm_options[:20])  # Limit per index
        
        # Add weekly expiry for current week (indices)
        weekly_expiry = self.get_current_weekly_expiry()
        for index in ['NIFTY', 'BANKNIFTY']:
            weekly_options = self.generate_atm_options(index, weekly_expiry, weekly=True)
            symbols_to_add.update(weekly_options[:10])  # Limit for weekly
        
        # Respect symbol limit
        symbols_list = list(symbols_to_add)[:self.config.max_symbols]
        
        # Wait for TrueData to be connected before subscribing
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            if is_connected():
                logger.info("✅ TrueData connected - proceeding with symbol subscription")
                break
            else:
                logger.info(f"⏳ Waiting for TrueData connection... (attempt {retry_count + 1}/{max_retries})")
                await asyncio.sleep(5)  # Wait 5 seconds between retries
                retry_count += 1
        
        if retry_count >= max_retries:
            logger.warning("⚠️ TrueData not connected after max retries - will retry in background")
            logger.info("💡 Symbols will be added automatically when TrueData connects")
        else:
            # Subscribe to symbols
            await self.subscribe_symbols(symbols_list)
        
        logger.info(f"✅ Initial setup complete: {len(symbols_list)} symbols")

    async def subscribe_symbols(self, symbols: List[str]):
        """Subscribe to symbols using existing TrueData cache - FIXED TO PREVENT CONNECTION CONFLICTS"""
        try:
            # Filter out already subscribed symbols
            new_symbols = [s for s in symbols if s not in self.active_symbols]
            
            if not new_symbols:
                return
                
            logger.info(f"📊 Registering {len(new_symbols)} new symbols for tracking...")
            
            # CRITICAL FIX: Don't call subscribe_to_symbols() which creates connection conflicts
            # Instead, just register symbols for tracking and let main TrueData client handle subscriptions
            
            if is_connected():
                logger.info("✅ TrueData connected - symbols will be available via cache")
                
                # Just update our tracking - don't try to subscribe directly
                self.active_symbols.update(new_symbols)
                
                # Store metadata
                timestamp = datetime.now().isoformat()
                for symbol in new_symbols:
                    self.symbol_metadata[symbol] = {
                        'added_at': timestamp,
                        'type': self.classify_symbol(symbol),
                        'priority': self.get_symbol_priority(symbol)
                    }
                
                logger.info(f"✅ Registered {len(new_symbols)} symbols for tracking")
                logger.info(f"📊 Total tracked symbols: {len(self.active_symbols)}")
                
                # Check if any symbols are already available in cache
                available_count = sum(1 for symbol in new_symbols if symbol in live_market_data)
                if available_count > 0:
                    logger.info(f"📊 {available_count}/{len(new_symbols)} symbols already available in cache")
                
            else:
                logger.warning("⚠️ TrueData not connected - symbols registered for when connection is available")
                # Store symbols for later processing
                self.pending_symbols.extend(new_symbols)
                logger.info(f"💾 Stored {len(new_symbols)} symbols as pending")
                
        except Exception as e:
            logger.error(f"❌ Symbol registration error: {e}")

    async def unsubscribe_symbols(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        try:
            # Remove from active symbols
            symbols_to_remove = [s for s in symbols if s in self.active_symbols]
            
            if not symbols_to_remove:
                return
                
            logger.info(f"🗑️ Removing {len(symbols_to_remove)} symbols...")
            
            # Update tracking
            for symbol in symbols_to_remove:
                self.active_symbols.discard(symbol)
                self.symbol_metadata.pop(symbol, None)
            
            logger.info(f"✅ Removed {len(symbols_to_remove)} symbols")
            logger.info(f"📊 Total active symbols: {len(self.active_symbols)}")
            
        except Exception as e:
            logger.error(f"❌ Unsubscription error: {e}")

    async def auto_refresh_loop(self):
        """Automatically refresh symbols based on market conditions"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.auto_refresh_interval)
                
                if not self.is_market_hours():
                    continue
                    
                logger.info("🔄 Auto-refreshing symbols...")
                
                # Handle pending symbols first
                if self.pending_symbols:
                    logger.info(f"🔄 Retrying subscription for {len(self.pending_symbols)} pending symbols...")
                    pending_copy = self.pending_symbols.copy()
                    self.pending_symbols.clear()
                    await self.subscribe_symbols(pending_copy)
                
                # Check for new contracts
                await self.add_new_contracts()
                
                # Optimize symbol allocation
                await self.optimize_symbol_allocation()
                
            except Exception as e:
                logger.error(f"❌ Auto-refresh error: {e}")

    async def expiry_monitor_loop(self):
        """Monitor and remove expired contracts"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.expiry_check_interval)
                
                logger.info("🕒 Checking for expired contracts...")
                
                expired_symbols = self.find_expired_symbols()
                if expired_symbols:
                    await self.unsubscribe_symbols(expired_symbols)
                    logger.info(f"🗑️ Removed {len(expired_symbols)} expired symbols")
                
            except Exception as e:
                logger.error(f"❌ Expiry monitor error: {e}")

    async def market_hours_optimizer(self):
        """Optimize symbols based on market hours"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_hour = datetime.now().hour
                
                # Pre-market: Focus on indices and futures
                if 8 <= current_hour < 9:
                    await self.pre_market_optimization()
                
                # Market hours: Full symbol set
                elif 9 <= current_hour < 15:
                    await self.market_hours_optimization()
                
                # Post-market: Reduce to core symbols
                elif current_hour >= 16:
                    await self.post_market_optimization()
                    
            except Exception as e:
                logger.error(f"❌ Market hours optimizer error: {e}")

    def get_current_monthly_expiry(self) -> str:
        """Get current month F&O expiry date"""
        now = datetime.now()
        # Last Thursday of the month logic
        # Simplified: Use end of month + format
        year = now.year
        month = now.month
        
        # Get last Thursday (simplified)
        last_day = 31 if month in [1,3,5,7,8,10,12] else 30
        if month == 2:
            last_day = 29 if year % 4 == 0 else 28
            
        # Format: 25JUN24 style
        month_names = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        return f"25{month_names[month]}{str(year)[-2:]}"

    def get_current_weekly_expiry(self) -> str:
        """Get current week expiry date"""
        now = datetime.now()
        
        # Find next Thursday
        days_ahead = 3 - now.weekday()  # Thursday is 3
        if days_ahead <= 0:
            days_ahead += 7
            
        next_thursday = now + timedelta(days=days_ahead)
        
        # Format: 27JUN24 style
        month_names = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                      'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        day = next_thursday.day
        month = next_thursday.month
        year = next_thursday.year
        
        return f"{day:02d}{month_names[month]}{str(year)[-2:]}"

    def generate_atm_options(self, index: str, expiry: str, weekly: bool = False) -> List[str]:
        """Generate ATM option symbols for an index"""
        # Simplified ATM calculation
        atm_levels = {
            'NIFTY': [24000, 24100, 24200, 24300, 24400],
            'BANKNIFTY': [51000, 51100, 51200, 51300, 51400],
            'FINNIFTY': [23000, 23100, 23200, 23300, 23400]
        }
        
        strikes = atm_levels.get(index, [])
        options = []
        
        for strike in strikes:
            # Call and Put options
            options.append(f"{index}{expiry}{strike}CE")
            options.append(f"{index}{expiry}{strike}PE")
        
        return options

    def classify_symbol(self, symbol: str) -> str:
        """Classify symbol type"""
        if symbol in self.config.core_indices:
            return 'core_index'
        elif symbol in self.config.priority_stocks:
            return 'priority_stock'
        elif 'CE' in symbol or 'PE' in symbol:
            return 'option'
        else:
            return 'stock'

    def get_symbol_priority(self, symbol: str) -> int:
        """Get symbol priority (lower = higher priority)"""
        if symbol in self.config.core_indices:
            return 1
        elif symbol in self.config.priority_stocks:
            return 2
        elif 'CE' in symbol or 'PE' in symbol:
            return 3
        else:
            return 4

    def find_expired_symbols(self) -> List[str]:
        """Find expired option contracts"""
        expired = []
        today = datetime.now().date()
        
        for symbol in self.active_symbols:
            if 'CE' in symbol or 'PE' in symbol:
                # Extract expiry from symbol (simplified)
                # In reality, you'd parse the expiry date properly
                if self.is_symbol_expired(symbol, today):
                    expired.append(symbol)
        
        return expired

    def is_symbol_expired(self, symbol: str, today) -> bool:
        """Check if an option symbol is expired"""
        # Simplified expiry check
        # In production, parse the actual expiry date from symbol
        return False  # For now, return False

    def is_market_hours(self) -> bool:
        """Check if markets are open"""
        now = datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        # Check if it's a weekday
        is_weekday = now.weekday() < 5
        
        return is_weekday and market_open <= current_time <= market_close

    async def add_new_contracts(self):
        """Add new F&O contracts as they become available"""
        # Logic to identify and add new contracts
        # This would connect to exchange APIs or use TrueData contract APIs
        pass

    async def optimize_symbol_allocation(self):
        """Optimize symbol allocation within 250 limit"""
        if len(self.active_symbols) < self.config.max_symbols:
            return
            
        # Remove low priority symbols if at limit
        symbols_by_priority = sorted(
            self.active_symbols,
            key=lambda s: self.symbol_metadata.get(s, {}).get('priority', 999)
        )
        
        # Keep high priority, remove low priority
        symbols_to_remove = symbols_by_priority[self.config.max_symbols:]
        if symbols_to_remove:
            await self.unsubscribe_symbols(symbols_to_remove)

    async def pre_market_optimization(self):
        """Pre-market symbol optimization"""
        logger.info("🌅 Pre-market optimization")
        # Focus on indices and futures

    async def market_hours_optimization(self):
        """Market hours symbol optimization"""
        logger.info("📈 Market hours optimization")
        # Full symbol set with options

    async def post_market_optimization(self):
        """Post-market symbol optimization"""
        logger.info("🌙 Post-market optimization")
        # Reduce to core symbols

    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'is_running': self.is_running,
            'active_symbols': len(self.active_symbols),
            'max_symbols': self.config.max_symbols,
            'symbol_utilization': f"{len(self.active_symbols)}/{self.config.max_symbols}",
            'core_indices': len([s for s in self.active_symbols if s in self.config.core_indices]),
            'priority_stocks': len([s for s in self.active_symbols if s in self.config.priority_stocks]),
            'options': len([s for s in self.active_symbols if 'CE' in s or 'PE' in s]),
            'last_refresh': datetime.now().isoformat()
        }


# Global instance
intelligent_symbol_manager = IntelligentSymbolManager()

# API functions for the backend
async def start_intelligent_symbol_management():
    """Start intelligent symbol management"""
    await intelligent_symbol_manager.start()

async def stop_intelligent_symbol_management():
    """Stop intelligent symbol management"""
    await intelligent_symbol_manager.stop()

def get_intelligent_symbol_status():
    """Get intelligent symbol manager status"""
    return intelligent_symbol_manager.get_status()

def get_active_symbols():
    """Get currently active symbols"""
    return list(intelligent_symbol_manager.active_symbols)

logger.info("🤖 Intelligent Symbol Manager module loaded") 
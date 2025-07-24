"""
Daily Capital Synchronization
Fetches real available funds from broker accounts and updates system capital
"""

import logging
import asyncio
from datetime import datetime, time
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class DailyCapitalSync:
    """Fetches real capital from broker accounts and updates system accordingly"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.account_capitals = {}  # user_id -> actual_capital
        self.last_sync_time = None
        self.is_syncing = False
        
    async def sync_all_accounts(self) -> Dict[str, float]:
        """Sync capital for all accounts at system startup"""
        try:
            if self.is_syncing:
                logger.info("🔄 Capital sync already in progress")
                return self.account_capitals
                
            self.is_syncing = True
            logger.info("🔄 Starting daily capital synchronization...")
            
            # Get orchestrator and broker clients
            if not self.orchestrator:
                logger.error("❌ No orchestrator available for capital sync")
                return {}
                
            # Sync Zerodha accounts
            zerodha_capitals = await self._sync_zerodha_accounts()
            
            # Update system capitals
            await self._update_system_capitals(zerodha_capitals)
            
            self.last_sync_time = datetime.now()
            self.account_capitals = zerodha_capitals
            
            logger.info(f"✅ Capital sync completed for {len(zerodha_capitals)} accounts")
            logger.info(f"💰 Total system capital: ₹{sum(zerodha_capitals.values()):,.2f}")
            
            return zerodha_capitals
            
        except Exception as e:
            logger.error(f"❌ Error during capital sync: {e}")
            return {}
        finally:
            self.is_syncing = False
    
    async def _sync_zerodha_accounts(self) -> Dict[str, float]:
        """Fetch real available funds from Zerodha accounts"""
        try:
            zerodha_capitals = {}
            
            # Get Zerodha client from orchestrator
            if (not self.orchestrator or 
                not hasattr(self.orchestrator, 'zerodha_client') or 
                not self.orchestrator.zerodha_client):
                logger.error("❌ No Zerodha client available")
                return {}
                
            zerodha_client = self.orchestrator.zerodha_client
            
            # Get real margins from Zerodha API
            logger.info("🔍 Fetching real margins from Zerodha API...")
            margins_data = await zerodha_client.get_margins()
            
            if margins_data and 'equity' in margins_data:
                available_cash = margins_data['equity'].get('available', {}).get('cash', 0)
                
                # Get user ID
                user_id = zerodha_client.user_id or 'ZERODHA_USER'
                zerodha_capitals[user_id] = float(available_cash)
                
                logger.info(f"✅ Zerodha account {user_id}: ₹{available_cash:,.2f} available")
                
                # Check if this is significantly different from hardcoded value
                hardcoded_capital = 1000000.0
                if abs(available_cash - hardcoded_capital) > 10000:  # More than 10K difference
                    logger.warning(f"⚠️ SIGNIFICANT DIFFERENCE:")
                    logger.warning(f"   Hardcoded: ₹{hardcoded_capital:,.2f}")
                    logger.warning(f"   Real Available: ₹{available_cash:,.2f}")
                    logger.warning(f"   Using REAL amount for position sizing!")
                
            else:
                logger.error("❌ Could not fetch margins from Zerodha")
                
                # Fallback to hardcoded for testing
                fallback_capital = 1000000.0
                user_id = zerodha_client.user_id or 'ZERODHA_USER'
                zerodha_capitals[user_id] = fallback_capital
                logger.warning(f"⚠️ Using fallback capital: ₹{fallback_capital:,.2f}")
            
            return zerodha_capitals
            
        except Exception as e:
            logger.error(f"❌ Error fetching Zerodha margins: {e}")
            return {}
    
    async def _update_system_capitals(self, account_capitals: Dict[str, float]):
        """Update system components with real capital amounts"""
        try:
            total_capital = sum(account_capitals.values())
            
            if not self.orchestrator:
                logger.error("❌ No orchestrator available for capital updates")
                return
            
            # Update Position Tracker
            if hasattr(self.orchestrator, 'position_tracker') and self.orchestrator.position_tracker:
                await self.orchestrator.position_tracker.set_capital(total_capital)
                logger.info(f"✅ Updated Position Tracker capital: ₹{total_capital:,.2f}")
            
            # Update Trade Engine
            if hasattr(self.orchestrator, 'trade_engine') and self.orchestrator.trade_engine:
                # Update trade engine's capital tracking
                if hasattr(self.orchestrator.trade_engine, 'set_capital'):
                    await self.orchestrator.trade_engine.set_capital(total_capital)
                logger.info(f"✅ Updated Trade Engine capital: ₹{total_capital:,.2f}")
            
            # Update Risk Manager
            if hasattr(self.orchestrator, 'risk_manager') and self.orchestrator.risk_manager:
                # Update risk manager's capital base
                if hasattr(self.orchestrator.risk_manager, 'set_capital'):
                    await self.orchestrator.risk_manager.set_capital(total_capital)
                logger.info(f"✅ Updated Risk Manager capital: ₹{total_capital:,.2f}")
            
            # Update individual account capitals
            for user_id, capital in account_capitals.items():
                await self._update_user_capital(user_id, capital)
                
        except Exception as e:
            logger.error(f"❌ Error updating system capitals: {e}")
    
    async def _update_user_capital(self, user_id: str, capital: float):
        """Update individual user capital in trading control"""
        try:
            # Import trading control to update user capital
            from src.api.trading_control import broker_users
            
            if user_id in broker_users:
                broker_users[user_id]['current_capital'] = capital
                broker_users[user_id]['initial_capital'] = capital  # Update both
                logger.info(f"✅ Updated user {user_id} capital: ₹{capital:,.2f}")
            else:
                logger.warning(f"⚠️ User {user_id} not found in broker_users")
                
        except Exception as e:
            logger.error(f"❌ Error updating user capital: {e}")
    
    async def get_account_capital(self, user_id: str) -> float:
        """Get current capital for specific account"""
        return self.account_capitals.get(user_id, 1000000.0)  # Fallback to 10L
    
    async def get_total_capital(self) -> float:
        """Get total capital across all accounts"""
        return sum(self.account_capitals.values())
    
    async def calculate_position_size(self, user_id: str, signal: Dict, risk_percent: float = 0.02) -> int:
        """Calculate position size based on actual available capital"""
        try:
            # Get real capital for this user
            user_capital = await self.get_account_capital(user_id)
            
            # Calculate risk amount
            risk_amount = user_capital * risk_percent
            
            # Get entry price from signal
            entry_price = signal.get('entry_price', signal.get('price', 100))
            stop_loss = signal.get('stop_loss', entry_price * 0.98)  # 2% default stop
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            if risk_per_share > 0:
                # Calculate quantity based on risk
                quantity = int(risk_amount / risk_per_share)
                
                # Apply minimum/maximum limits
                quantity = max(1, quantity)  # Minimum 1 share
                max_quantity = int(user_capital * 0.1 / entry_price)  # Max 10% of capital
                quantity = min(quantity, max_quantity)
                
                logger.info(f"📊 Position Size Calculation:")
                logger.info(f"   User Capital: ₹{user_capital:,.2f}")
                logger.info(f"   Risk Amount: ₹{risk_amount:,.2f} ({risk_percent*100}%)")
                logger.info(f"   Entry Price: ₹{entry_price}")
                logger.info(f"   Stop Loss: ₹{stop_loss}")
                logger.info(f"   Risk Per Share: ₹{risk_per_share}")
                logger.info(f"   Calculated Quantity: {quantity}")
                
                return quantity
            else:
                logger.warning(f"⚠️ Invalid risk calculation for {signal.get('symbol')}")
                return 1
                
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return 1
    
    def should_sync_today(self) -> bool:
        """Check if capital sync is needed today"""
        if not self.last_sync_time:
            return True
            
        # Sync if last sync was not today
        today = datetime.now().date()
        last_sync_date = self.last_sync_time.date()
        
        return today != last_sync_date
    
    async def schedule_daily_sync(self):
        """Schedule capital sync for market opening time"""
        try:
            while True:
                # Check if it's market opening time (9:00 AM IST)
                now = datetime.now()
                market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
                
                if (now.time() >= time(9, 0) and now.time() <= time(9, 30) and 
                    self.should_sync_today()):
                    
                    logger.info("🌅 Market opening - starting capital sync")
                    await self.sync_all_accounts()
                
                # Sleep for 30 minutes before checking again
                await asyncio.sleep(1800)  # 30 minutes
                
        except Exception as e:
            logger.error(f"❌ Error in daily sync scheduler: {e}") 
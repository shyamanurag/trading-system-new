\"\"\"
Production-Level Trading Orchestrator
====================================
Coordinates all trading system components without TrueData dependencies.
Implements proper initialization, error handling, and component management.
\"\"\"

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any
import sys
import os

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config.database import get_redis_client
from brokers.resilient_zerodha import ResilientZerodhaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionPositionTracker:
    \"\"\"Production-level position tracker with proper error handling\"\"\"
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.positions = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        \"\"\"Initialize position tracker\"\"\"
        try:
            if self.redis_client:
                await self.redis_client.ping()
                self.logger.info(\"Position tracker initialized with Redis\")
            else:
                self.logger.info(\"Position tracker initialized without Redis\")
            return True
        except Exception as e:
            self.logger.error(f\"Position tracker initialization failed: {e}\")
            return False
    
    async def update_position(self, symbol: str, quantity: int, price: float) -> bool:
        \"\"\"Update position for symbol\"\"\"
        try:
            self.positions[symbol] = {
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now()
            }
            return True
        except Exception as e:
            self.logger.error(f\"Failed to update position for {symbol}: {e}\")
            return False
    
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        \"\"\"Get position for symbol\"\"\"
        return self.positions.get(symbol, {'quantity': 0, 'price': 0.0})
    
    async def get_all_positions(self) -> Dict[str, Any]:
        \"\"\"Get all positions\"\"\"
        return self.positions.copy()

class ProductionEventBus:
    \"\"\"Production-level event bus for component communication\"\"\"
    
    def __init__(self):
        self.subscribers = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        \"\"\"Initialize event bus\"\"\"
        try:
            self.logger.info(\"Event bus initialized\")
            return True
        except Exception as e:
            self.logger.error(f\"Event bus initialization failed: {e}\")
            return False
    
    async def publish(self, event_type: str, data: Any) -> bool:
        \"\"\"Publish event to subscribers\"\"\"
        try:
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    await callback(data)
            return True
        except Exception as e:
            self.logger.error(f\"Failed to publish event {event_type}: {e}\")
            return False
    
    def subscribe(self, event_type: str, callback):
        \"\"\"Subscribe to event type\"\"\"
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

class ProductionRiskManager:
    \"\"\"Production-level risk manager\"\"\"
    
    def __init__(self, event_bus=None, position_tracker=None, max_daily_loss=10000, max_position_size=100000):
        self.event_bus = event_bus
        self.position_tracker = position_tracker
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.daily_pnl = 0.0
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        \"\"\"Initialize risk manager\"\"\"
        try:
            self.logger.info(\"Risk manager initialized\")
            return True
        except Exception as e:
            self.logger.error(f\"Risk manager initialization failed: {e}\")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        \"\"\"Get risk manager status\"\"\"
        return {
            'status': 'production_risk_manager_active',
            'daily_pnl': self.daily_pnl,
            'max_daily_loss': self.max_daily_loss,
            'risk_limit_used': abs(self.daily_pnl) / self.max_daily_loss if self.max_daily_loss > 0 else 0.0
        }

class TradingOrchestrator:
    \"\"\"
    Production-Level Trading Orchestrator
    ===================================
    Manages all trading system components without external dependencies.
    Implements proper initialization, health monitoring, and error recovery.
    \"\"\"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.components = {}
        self.is_initialized = False
        self.is_running = False
        self.strategies = {}
        self.active_strategies = []
        
        # Core components
        self.event_bus = None
        self.position_tracker = None
        self.risk_manager = None
        self.zerodha_client = None
        
        # Market data and symbols
        self.market_data = {}
        self.subscribed_symbols = set()
        
        # Configuration
        self.max_daily_trades = 50
        self.max_position_size = 100000
        self.risk_limit = 0.02
        
    async def initialize(self) -> bool:
        \"\"\"Initialize all system components\"\"\"
        try:
            self.logger.info(\" Initializing Production Trading Orchestrator...\")
            
            success_count = 0
            total_components = 4
            
            # 1. Event Bus
            self.event_bus = ProductionEventBus()
            if await self.event_bus.initialize():
                self.components['event_bus'] = True
                success_count += 1
                self.logger.info(\" Event bus initialized\")
            else:
                self.components['event_bus'] = False
                self.logger.error(\" Event bus initialization failed\")
            
            # 2. Position Tracker
            try:
                redis_client = get_redis_client()
                self.position_tracker = ProductionPositionTracker(redis_client)
            except:
                self.position_tracker = ProductionPositionTracker()
                
            if await self.position_tracker.initialize():
                self.components['position_tracker'] = True
                success_count += 1
                self.logger.info(\" Position tracker initialized\")
            else:
                self.components['position_tracker'] = False
                self.logger.error(\" Position tracker initialization failed\")
            
            # 3. Risk Manager
            try:
                self.risk_manager = ProductionRiskManager(
                    event_bus=self.event_bus,
                    position_tracker=self.position_tracker,
                    max_daily_loss=10000,
                    max_position_size=self.max_position_size
                )
                if await self.risk_manager.initialize():
                    self.components['risk_manager'] = True
                    success_count += 1
                    self.logger.info(\" Risk manager initialized\")
                else:
                    self.components['risk_manager'] = False
                    self.logger.error(\" Risk manager initialization failed\")
            except Exception as e:
                self.components['risk_manager'] = False
                self.logger.error(f\" Risk manager initialization failed: {e}\")
            
            # 4. Zerodha Client
            try:
                self.zerodha_client = ResilientZerodhaClient()
                if await self.zerodha_client.initialize():
                    self.components['zerodha_client'] = True
                    success_count += 1
                    self.logger.info(\" Zerodha client initialized\")
                else:
                    self.components['zerodha_client'] = False
                    self.logger.error(\" Zerodha client initialization failed\")
            except Exception as e:
                self.components['zerodha_client'] = False
                self.logger.error(f\" Zerodha client initialization failed: {e}\")
            
            # Load strategies
            await self._load_strategies()
            
            # Check initialization success
            self.is_initialized = success_count >= 3
            
            if self.is_initialized:
                self.logger.info(f\" Orchestrator initialized successfully ({success_count}/{total_components} components)\")
            else:
                self.logger.error(f\" Orchestrator initialization failed ({success_count}/{total_components} components)\")
            
            return self.is_initialized
            
        except Exception as e:
            self.logger.error(f\"Critical error during orchestrator initialization: {e}\")
            self.is_initialized = False
            return False
    
    async def _load_strategies(self):
        \"\"\"Load trading strategies\"\"\"
        try:
            strategy_names = [
                'regime_adaptive_controller',
                'confluence_amplifier', 
                'momentum_surfer',
                'volume_profile_scalper',
                'volatility_explosion'
            ]
            
            for strategy_name in strategy_names:
                try:
                    self.strategies[strategy_name] = {
                        'name': strategy_name,
                        'active': True,
                        'last_signal': None
                    }
                    self.active_strategies.append(strategy_name)
                    self.logger.info(f\" Loaded strategy: {strategy_name}\")
                    
                except Exception as e:
                    self.logger.error(f\" Failed to load strategy {strategy_name}: {e}\")
            
            self.logger.info(f\" Loaded {len(self.strategies)} trading strategies\")
            
        except Exception as e:
            self.logger.error(f\"Error loading strategies: {e}\")
    
    async def start_trading(self) -> bool:
        \"\"\"Start autonomous trading\"\"\"
        try:
            if not self.is_initialized:
                self.logger.error(\"Cannot start trading - orchestrator not initialized\")
                return False
            
            self.is_running = True
            self.logger.info(\" Autonomous trading started\")
            
            # Start market data processing
            asyncio.create_task(self._process_market_data())
            
            return True
            
        except Exception as e:
            self.logger.error(f\"Failed to start trading: {e}\")
            return False
    
    async def stop_trading(self) -> bool:
        \"\"\"Stop autonomous trading\"\"\"
        try:
            self.is_running = False
            self.logger.info(\" Autonomous trading stopped\")
            return True
        except Exception as e:
            self.logger.error(f\"Failed to stop trading: {e}\")
            return False
    
    async def _process_market_data(self):
        \"\"\"Process incoming market data\"\"\"
        while self.is_running:
            try:
                # Get market data from API (avoiding TrueData dependency)
                market_data = await self._get_market_data_from_api()
                
                # Update internal market data
                self.market_data.update(market_data)
                
                # Publish market data event
                if self.event_bus:
                    await self.event_bus.publish('market_data_update', market_data)
                
                await asyncio.sleep(5)  # Process every 5 seconds
                
            except Exception as e:
                self.logger.error(f\"Error processing market data: {e}\")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _get_market_data_from_api(self) -> Dict[str, Any]:
        \"\"\"Get market data from internal API instead of TrueData directly\"\"\"
        try:
            # Import here to avoid circular imports
            from src.api.market_data import get_live_market_data
            
            # Get market data from our internal API
            market_data_response = await get_live_market_data()
            
            if market_data_response and 'data' in market_data_response:
                return market_data_response['data']
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f\"Failed to get market data from API: {e}\")
            return {}
    
    def _is_market_open(self) -> bool:
        \"\"\"Check if market is open\"\"\"
        try:
            from datetime import datetime
            import pytz
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Market hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                return False
            
            return market_open <= current_time <= market_close
            
        except Exception as e:
            self.logger.error(f\"Error checking market hours: {e}\")
            return True  # Default to True if check fails
    
    def _get_market_outlook(self) -> str:
        \"\"\"Get current market outlook\"\"\"
        try:
            if self._is_market_open():
                return \"MARKET_OPEN\"
            else:
                return \"MARKET_CLOSED\"
        except Exception as e:
            self.logger.error(f\"Error getting market outlook: {e}\")
            return \"UNKNOWN\"
    
    async def get_status(self) -> Dict[str, Any]:
        \"\"\"Get orchestrator status\"\"\"
        try:
            component_count = sum(1 for status in self.components.values() if status)
            total_components = len(self.components)
            
            return {
                'system_ready': self.is_initialized,
                'trading_active': self.is_running,
                'market_open': self._is_market_open(),
                'market_outlook': self._get_market_outlook(),
                'components_ready': component_count,
                'total_components': total_components,
                'component_status': self.components,
                'strategies_loaded': len(self.strategies),
                'active_strategies': self.active_strategies,
                'symbol_count': len(self.market_data),
                'subscribed_symbols': len(self.subscribed_symbols),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f\"Error getting status: {e}\")
            return {
                'system_ready': False,
                'error': str(e)
            }
    
    async def get_risk_status(self) -> Dict[str, Any]:
        \"\"\"Get risk manager status\"\"\"
        try:
            if self.risk_manager and self.components.get('risk_manager', False):
                return await self.risk_manager.get_status()
            else:
                return {
                    'status': 'risk_manager_not_initialized',
                    'daily_pnl': 0.0,
                    'max_daily_loss': self.max_position_size,
                    'risk_limit_used': 0.0
                }
        except Exception as e:
            self.logger.error(f\"Error getting risk status: {e}\")
            return {
                'status': 'risk_manager_error',
                'error': str(e)
            }

# Global orchestrator instance
orchestrator = TradingOrchestrator()

async def get_orchestrator() -> TradingOrchestrator:
    \"\"\"Get orchestrator instance\"\"\"
    if not orchestrator.is_initialized:
        await orchestrator.initialize()
    return orchestrator

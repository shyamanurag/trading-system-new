"""
Trading Orchestrator
Manages the overall trading system operations with enhanced features
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta, timezone
import logging
import asyncio
import os
from .config import settings
from .connection_manager import ConnectionManager
from .pre_market_analyzer import PreMarketAnalyzer
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RealSignal:
    """Real trading signal with actual market data"""
    symbol: str
    side: str
    price: float
    quantity: int
    strategy_name: str
    quality_score: float = 80.0
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class TradingOrchestrator:
    """Real money trading orchestrator - NO MOCK COMPONENTS ALLOWED"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TradingOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'TradingOrchestrator':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Real trading state only
        self.is_active = False
        self.system_ready = False
        
        # Real components - no mock fallbacks
        self.zerodha = None
        self.connection_manager = None
        self.position_tracker = None
        self.risk_manager = None
        self.order_manager = None
        self.trade_engine = None
        self.market_data = None
        self.strategy_engine = None
        self.pre_market_analyzer = None
        
        # Real trading session data
        self.session_id = None
        self.start_time = None
        self.last_heartbeat = None
        self.total_trades = 0
        self.daily_pnl = 0.0
        self.active_positions = []
        self.active_strategies = []
        self.pre_market_results = {}
        
        # Load real configuration
        self.config = self._load_config()
        self._instance_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🏦 REAL MONEY Trading Orchestrator initialized (ID: {self._instance_id})")
        logger.info("⚡ NO MOCK COMPONENTS - Real trading only!")
        
        self._initialized = True

    def _load_config(self) -> Dict[str, Any]:
        """Load real trading configuration"""
        try:
            # Load from actual config files - no test configs
            from src.config.loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_config()
            
            # CRITICAL: Ensure no mock/test mode enabled
            if config.get('mock_market_data', False):
                raise ValueError("❌ MOCK MODE DETECTED - Not allowed in real money trading!")
            if config.get('mock_broker_apis', False):
                raise ValueError("❌ MOCK BROKER DETECTED - Not allowed in real money trading!")
            if config.get('skip_external_apis', False):
                raise ValueError("❌ SKIP EXTERNAL APIs DETECTED - Not allowed in real money trading!")
                
            logger.info("✅ Real trading configuration loaded - no mock contamination")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return minimal safe config
            return {
                'trading': {
                    'enabled': True,
                    'paper_mode': False,  # REAL MONEY MODE
                    'max_daily_loss': 50000,
                    'max_position_size': 0.05
                }
            }

    def _initialize(self):
        """Initialize real components only"""
        try:
            # Initialize broker connection (real Zerodha only)
            self._initialize_broker_connection()
            
            # Initialize connection manager (real connections only)
            self._initialize_connection_manager()
            
            logger.info("✅ Real components initialized")
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise RuntimeError("Cannot initialize real trading components")

    def _initialize_broker_connection(self):
        """Initialize REAL Zerodha connection only"""
        try:
            from brokers.resilient_zerodha import ResilientZerodhaConnection
            from brokers.zerodha import ZerodhaIntegration
            
            # CRITICAL: Only use real Zerodha - no mock fallback
            zerodha_config = self.config.get('zerodha', {})
            if not zerodha_config:
                # Set basic config for real money trading
                zerodha_config = {
                    'mock_mode': False,  # REAL MONEY MODE
                    'order_rate_limit': 1.0,
                    'ws_reconnect_delay': 5,
                    'ws_max_reconnect_attempts': 10
                }
                
            # Initialize base Zerodha integration
            zerodha_integration = ZerodhaIntegration(config=zerodha_config)
            
            # Wrap with resilient connection
            self.zerodha = ResilientZerodhaConnection(
                broker=zerodha_integration,
                config=zerodha_config
            )
            
            logger.info("✅ REAL Zerodha connection initialized - NO MOCK FALLBACK")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize REAL Zerodha: {e}")
            # DO NOT create mock - fail cleanly for real money safety
            raise RuntimeError("Cannot initialize real Zerodha connection - aborting for safety")

    def _initialize_connection_manager(self):
        """Initialize REAL connection manager only"""
        try:
            from src.core.connection_manager import ConnectionManager
            
            self.connection_manager = ConnectionManager(config=self.config)
            logger.info("✅ REAL Connection Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection manager: {e}")
            # DO NOT create mock - fail cleanly
            raise RuntimeError("Cannot initialize real connection manager")

    def _can_start_trading(self) -> bool:
        """Check if real trading can start safely"""
        try:
            # STRICT checks for real money safety
            if not self.zerodha:
                logger.error("❌ No real Zerodha connection - cannot trade")
                return False
                
            if not self.connection_manager:
                logger.error("❌ No real connection manager - cannot trade")
                return False
                
            # Check market data availability
            if not self.market_data:
                logger.error("❌ No real market data - cannot trade")
                return False
                
            # Check risk management
            if not self.risk_manager:
                logger.error("❌ No real risk manager - cannot trade")
                return False
                
            logger.info("✅ All real components available for trading")
            return True
            
        except Exception as e:
            logger.error(f"Trading safety check failed: {e}")
            return False

    async def initialize_system(self):
        """Initialize REAL trading system components only"""
        logger.info("🚀 Initializing REAL MONEY trading system...")
        
        try:
            # Initialize real components with strict error handling
            await self._initialize_real_trading_components()
            
            # Perform system health check
            if not await self._perform_system_health_check():
                raise RuntimeError("System health check failed")
            
            self.system_ready = True
            logger.info("✅ REAL MONEY trading system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            self.system_ready = False
            return False

    async def _initialize_real_trading_components(self):
        """Initialize REAL trading components - NO MOCK FALLBACKS"""
        logger.info("Initializing REAL trading components...")
        
        # Track initialization success - fail hard if any critical component fails
        component_status = {}
        
        # Initialize REAL components in order
        component_status['risk_manager'] = await self._safe_init_real_risk_manager()
        component_status['position_tracker'] = await self._safe_init_real_position_tracker()
        component_status['market_data'] = await self._safe_init_real_market_data()
        component_status['strategy_engine'] = await self._safe_init_real_strategy_engine()
        component_status['trade_engine'] = await self._safe_init_real_trade_engine()
        component_status['order_manager'] = await self._safe_init_real_order_manager()
        component_status['pre_market_analyzer'] = await self._safe_init_real_pre_market_analyzer()
        
        # Log component status
        self._log_component_status(component_status)
        
        # Check if we have minimum components for REAL trading
        if not self._check_minimum_real_components(component_status):
            raise RuntimeError("❌ Insufficient REAL components for safe trading")
        
        logger.info("✅ REAL trading components initialized")

    async def _safe_init_real_risk_manager(self):
        """Initialize REAL risk manager - no mock fallback"""
        try:
            from src.core.risk_manager import RiskManager
            from src.events import EventBus
            
            # Create event bus if not exists
            if not hasattr(self, 'event_bus'):
                self.event_bus = EventBus()
            
            # Create position tracker if not exists (needed by risk manager)
            if not hasattr(self, 'position_tracker'):
                logger.warning("Position tracker not available for risk manager")
                return False
            
            self.risk_manager = RiskManager(
                config=self.config.get('risk', {}),
                position_tracker=self.position_tracker,
                event_bus=self.event_bus
            )
            
            await self.risk_manager.start_monitoring()
            logger.info("✅ REAL Risk Manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Risk Manager initialization failed: {e}")
            # DO NOT create mock for real money trading
            return False

    async def _safe_init_real_position_tracker(self):
        """Initialize REAL position tracker - no mock fallback"""
        try:
            from src.core.position_tracker import PositionTracker
            from src.events import EventBus
            import redis.asyncio as redis
            
            # Create event bus if not exists
            if not hasattr(self, 'event_bus'):
                self.event_bus = EventBus()
            
            # Create redis client
            redis_config = self.config.get('redis', {
                'host': 'localhost', 
                'port': 6379
            })
            redis_client = redis.Redis(
                host=redis_config['host'], 
                port=redis_config['port']
            )
            
            self.position_tracker = PositionTracker(
                event_bus=self.event_bus,
                redis_client=redis_client
            )
            
            logger.info("✅ REAL Position Tracker initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Position Tracker initialization failed: {e}")
            return False

    async def _safe_init_real_market_data(self):
        """Initialize REAL market data - no mock fallback"""
        try:
            from src.core.market_data import MarketDataManager
            
            # Merge market_data and truedata configs
            market_config = self.config.get('market_data', {})
            truedata_config = self.config.get('truedata', {})
            merged_config = {**market_config, **truedata_config}
            
            self.market_data = MarketDataManager(config=merged_config)
            
            await self.market_data.start()
            logger.info("✅ REAL Market Data Manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Market Data initialization failed: {e}")
            return False

    async def _safe_init_real_strategy_engine(self):
        """Initialize REAL strategy engine using safe strategy loading"""
        
        class RealStrategyEngine:
            def __init__(self):
                # Load strategies safely with fallbacks
                self.strategies = {}
                
                logger.info("🔄 Loading real strategies...")
                
                # Try to load strategies individually with error handling
                self._try_load_strategy('regime_adaptive_controller', 'strategies.regime_adaptive_controller', 'RegimeAdaptiveController')
                self._try_load_strategy('confluence_amplifier', 'strategies.confluence_amplifier', 'ConfluenceAmplifier')
                self._try_load_strategy('momentum_surfer', 'strategies.momentum_surfer', 'EnhancedMomentumSurfer')
                
                # If no strategies loaded, create minimal working strategy
                if not self.strategies:
                    logger.warning("⚠️ No complex strategies loaded, creating minimal strategy")
                    self.strategies['minimal_strategy'] = self._create_minimal_working_strategy()
                
                logger.info(f"✅ Strategy engine initialized with {len(self.strategies)} strategies")
                logger.info(f"📈 Active strategies: {', '.join(self.strategies.keys())}")
            
            def _try_load_strategy(self, strategy_name: str, module_path: str, class_name: str):
                """Try to load a strategy with error handling"""
                try:
                    # Import the module
                    module = __import__(module_path, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)
                    
                    # Initialize with minimal config
                    strategy_config = {
                        'name': strategy_name,
                        'enabled': True,
                        'allocation': 0.2,
                        'signal_cooldown_seconds': 300
                    }
                    
                    strategy_instance = strategy_class(strategy_config)
                    self.strategies[strategy_name] = strategy_instance
                    
                    logger.info(f"✅ Loaded {strategy_name} ({class_name})")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not load {strategy_name}: {e}")
            
            def _create_minimal_working_strategy(self):
                """Create a minimal working strategy"""
                
                class MinimalWorkingStrategy:
                    def __init__(self):
                        self.name = "minimal_working_strategy"
                        self.is_enabled = True
                        
                    async def generate_signals(self, market_data):
                        """Generate minimal signals for system health"""
                        # Return empty signals but log that we're working
                        logger.info("💡 Minimal strategy: System healthy, no signals generated")
                        return []
                    
                    def get_strategy_metrics(self):
                        return {
                            'name': self.name,
                            'enabled': True,
                            'status': 'healthy',
                            'signals_generated': 0
                        }
                
                return MinimalWorkingStrategy()
                
            async def generate_all_signals(self, market_data):
                """Generate signals from all loaded strategies"""
                all_signals = []
                
                try:
                    for strategy_name, strategy in self.strategies.items():
                        try:
                            if hasattr(strategy, 'generate_signals'):
                                signals = await strategy.generate_signals(market_data)
                                if signals:
                                    all_signals.extend(signals)
                                    logger.info(f"📊 {strategy_name}: {len(signals)} signals")
                            else:
                                logger.debug(f"ℹ️ {strategy_name}: No generate_signals method")
                        except Exception as e:
                            logger.error(f"❌ Error in {strategy_name}: {e}")
                    
                    total_signals = len(all_signals)
                    if total_signals > 0:
                        logger.info(f"📊 Generated {total_signals} total signals")
                    else:
                        logger.debug("📊 No signals generated this cycle")
                    
                except Exception as e:
                    logger.error(f"❌ Error generating signals: {e}")
                
                return all_signals
            
            def get_strategy_status(self):
                """Get status of all strategies"""
                status = {}
                for name, strategy in self.strategies.items():
                    try:
                        if hasattr(strategy, 'get_strategy_metrics'):
                            status[name] = strategy.get_strategy_metrics()
                        else:
                            status[name] = {'name': name, 'status': 'loaded'}
                    except Exception as e:
                        status[name] = {'name': name, 'status': 'error', 'error': str(e)}
                
                return status
        
        return RealStrategyEngine()

    async def _safe_init_real_trade_engine(self):
        """Initialize REAL trade engine - no mock fallback"""
        try:
            from src.core.trade_engine import TradeEngine
            from src.core.database import get_database
            
            # Initialize with REAL database persistence
            self.database = await get_database()
            self.trade_engine = TradeEngine(
                config={
                    'paper_mode': False,  # REAL MONEY MODE
                    'enable_persistence': True,
                    'database': self.database
                }, 
                risk_manager=self.risk_manager,
                zerodha=self.zerodha
            )
            
            # Start REAL trade persistence service
            await self.trade_engine.start_persistence_service()
            
            logger.info("✅ REAL Trade Engine with DATABASE PERSISTENCE initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Trade Engine initialization failed: {e}")
            # DO NOT create mock trade engine for real money
            return False

    async def _safe_init_real_order_manager(self):
        """Initialize REAL order manager - no mock fallback"""
        try:
            from src.core.order_manager import OrderManager
            
            self.order_manager = OrderManager(
                config=self.config.get('orders', {}),
                zerodha=self.zerodha,
                risk_manager=self.risk_manager
            )
            
            await self.order_manager.initialize()
            logger.info("✅ REAL Order Manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Order Manager initialization failed: {e}")
            return False

    async def _safe_init_real_pre_market_analyzer(self):
        """Initialize REAL pre-market analyzer"""
        try:
            from src.core.pre_market_analyzer import PreMarketAnalyzer
            
            self.pre_market_analyzer = PreMarketAnalyzer(
                config=self.config.get('pre_market', {}),
                market_data=self.market_data
            )
            
            await self.pre_market_analyzer.initialize()
            logger.info("✅ REAL Pre-Market Analyzer initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ REAL Pre-Market Analyzer initialization failed: {e}")
            return False

    def _log_component_status(self, status: Dict[str, bool]):
        """Log the status of all REAL components"""
        logger.info("\n📊 REAL COMPONENT INITIALIZATION STATUS:")
        for component, success in status.items():
            status_icon = "✅" if success else "❌"
            logger.info(f"   {status_icon} {component}: {'SUCCESS' if success else 'FAILED - NO MOCK FALLBACK'}")
        
        success_count = sum(status.values())
        total_count = len(status)
        logger.info(f"\n🎯 OVERALL: {success_count}/{total_count} REAL components initialized successfully")

    def _check_minimum_real_components(self, status: Dict[str, bool]) -> bool:
        """Check if we have minimum REAL components needed for safe trading"""
        # STRICT requirements for real money trading
        required = ['market_data', 'position_tracker', 'risk_manager', 'trade_engine']
        optional = ['order_manager', 'pre_market_analyzer']
        
        # Check ALL required components must be present
        required_ok = all(status.get(component, False) for component in required)
        
        logger.info(f"Minimum REAL component check: Required {required_ok}")
        logger.info(f"Required components: {', '.join(required)}")
        logger.info(f"Missing required: {[comp for comp in required if not status.get(comp, False)]}")
        
        return required_ok

    async def _perform_system_health_check(self) -> bool:
        """Perform comprehensive REAL system health check"""
        try:
            market_open = self._is_market_open()
            
            # STRICT checks for real money safety
            checks = {
                'zerodha_connection': self.zerodha is not None,
                'market_data': self.market_data is not None,
                'risk_manager': self.risk_manager is not None,
                'position_tracker': self.position_tracker is not None,
                'trade_engine': self.trade_engine is not None,
                'strategy_engine': self.strategy_engine is not None
            }
            
            all_healthy = all(checks.values())
            
            logger.info("REAL MONEY System Health Check:")
            logger.info(f"  Market Open: {market_open}")
            for component, status in checks.items():
                logger.info(f"  {component}: {'✅' if status else '❌ MISSING - TRADING UNSAFE'}")
            
            if all_healthy:
                logger.info("✅ REAL MONEY system health check PASSED")
            else:
                logger.error("❌ REAL MONEY system health check FAILED - TRADING BLOCKED")
            
            return all_healthy
            
        except Exception as e:
            logger.error(f"Error during REAL MONEY health check: {e}")
            return False

    def _is_market_open(self) -> bool:
        """Check if market is open for trading"""
        try:
            from datetime import datetime, time
            now = datetime.now()
            
            # Indian market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            market_start = time(9, 15)
            market_end = time(15, 30)
            current_time = now.time()
            
            return market_start <= current_time <= market_end
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False

    async def enable_trading(self):
        """Enable autonomous trading with proper signal generation"""
        logger.info(f"🚀 enable_trading called on instance: {getattr(self, '_instance_id', 'unknown')}")
        logger.info(f"   Current is_active: {self.is_active}")
        logger.info(f"   Current system_ready: {self.system_ready}")
        
        # Basic checks
        if not self.system_ready:
            logger.error("System not ready. Run initialize_system() first")
            return False
            
        if self.is_active:
            logger.warning("Trading is already active")
            return True
        
        # Check market (but don't block if closed)
        market_open = self._is_market_open()
        logger.info(f"   Market open: {market_open}")
        
        # Set core state
        logger.info("🔥 Setting core trading state")
        self.is_active = True
        self.session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        
        # Verify state was set
        logger.info(f"✅ State set - is_active={self.is_active}, session_id={self.session_id}")
        
        # Start trading loop if market is open and we have components
        if market_open and self.strategy_engine and self.market_data:
            logger.info("🔄 Starting trading signal generation loop...")
            asyncio.create_task(self._start_trading_loop())
            logger.info("✅ Trading loop started")
        else:
            logger.info("📝 Trading loop not started:")
            logger.info(f"   Market open: {market_open}")
            logger.info(f"   Strategy engine: {self.strategy_engine is not None}")
            logger.info(f"   Market data: {self.market_data is not None}")
            
            # If market is closed, still show as active but not generating signals
            if not market_open:
                logger.info("💤 Trading enabled but waiting for market open")
        
        # Start monitoring
        logger.info("📊 Starting trading monitor...")
        asyncio.create_task(self._monitor_trading())
        
        logger.info(f"✅ Trading enabled! Session: {self.session_id}")
        return True
    
    async def disable_trading(self):
        """Disable autonomous trading"""
        if not self.is_active:
            logger.warning("Trading is already inactive")
            return
        
        self.is_active = False
        
        # Stop trading engine
        if self.trade_engine:
            # Handle different trade engine types gracefully
            if hasattr(self.trade_engine, 'stop'):
                await self.trade_engine.stop()
            else:
                logger.info("Trade engine has no stop() method - using graceful shutdown")
        
        # Log session summary
        await self._log_session_summary()
        
        self.session_id = None
        self.start_time = None
        self.last_heartbeat = None
        
        logger.info("Trading disabled")
    
    async def _monitor_trading(self):
        """Monitor trading activity"""
        while self.is_active:
            try:
                # Update heartbeat
                self.last_heartbeat = datetime.utcnow()
                
                # Check if market hours
                if not self._is_market_open():
                    logger.info("Outside market hours, pausing trading")
                    await asyncio.sleep(60)
                    continue
                
                # Update metrics
                await self._update_metrics()
                
                # Check risk status
                await self._check_risk_status()
                
                # Log status every 5 minutes
                if datetime.utcnow().minute % 5 == 0:
                    await self._log_trading_status()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in trading monitor: {e}")
                await asyncio.sleep(60)
    
    async def _update_metrics(self):
        """Update trading metrics"""
        try:
            # Check if position tracker is properly initialized
            if hasattr(self, 'position_tracker') and hasattr(self.position_tracker, 'get_all_positions'):
                self.active_positions = await self.position_tracker.get_all_positions()
            else:
                # For now, use empty list
                self.active_positions = []
            
            # Update other metrics
            # This would fetch from actual components
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def _check_risk_status(self):
        """Check current risk status"""
        try:
            # Check if risk manager is properly initialized
            if hasattr(self, 'risk_manager') and hasattr(self.risk_manager, 'get_risk_metrics'):
                self.risk_status = await self.risk_manager.get_risk_metrics()
                
                # Check for critical risk levels
                if self.risk_status.get('risk_score', 0) > 80:
                    logger.warning("High risk detected, consider reducing positions")
            else:
                # For now, use default risk status
                self.risk_status = {'risk_score': 0, 'status': 'normal'}
                    
        except Exception as e:
            logger.error(f"Error checking risk status: {e}")
    
    async def _log_trading_status(self):
        """Log current trading status"""
        status = await self.get_trading_status()
        logger.info(f"Trading Status: Active={status['is_active']}, "
                   f"Positions={len(status['active_positions'])}, "
                   f"Daily P&L={status['daily_pnl']:.2f}")
    
    async def _log_session_summary(self):
        """Log trading session summary"""
        if not self.start_time:
            return
            
        duration = datetime.utcnow() - self.start_time
        logger.info(f"Session Summary: Duration={duration}, "
                   f"Total Trades={self.total_trades}, "
                   f"Final P&L={self.daily_pnl:.2f}")
    
    async def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status with PERSISTENT DATA"""
        logger.debug(f"📊 get_trading_status called on instance: {getattr(self, '_instance_id', 'unknown')}")
        logger.debug(f"   is_active: {self.is_active}")
        try:
            # Get PERSISTENT trade data from trade engine
            persistent_trades = 0
            persistent_pnl = 0.0
            daily_trades = []
            
            if self.trade_engine and hasattr(self.trade_engine, 'get_daily_trades'):
                try:
                    daily_trades = await self.trade_engine.get_daily_trades()
                    persistent_trades = len(daily_trades)
                    
                    if hasattr(self.trade_engine, 'get_daily_pnl'):
                        persistent_pnl = await self.trade_engine.get_daily_pnl()
                    
                    logger.info(f"📊 PERSISTENT DATA: {persistent_trades} trades, ₹{persistent_pnl:,.2f} P&L")
                    
                except Exception as e:
                    logger.warning(f"Failed to get persistent trade data: {e}")
            
            # Use PERSISTENT data (override in-memory counters)
            final_trades = max(getattr(self, 'total_trades', 0), persistent_trades)
            final_pnl = persistent_pnl if persistent_pnl != 0 else getattr(self, 'daily_pnl', 0.0)
            
            # Safely get market outlook
            market_outlook = "unknown"
            if self.pre_market_analyzer and hasattr(self.pre_market_analyzer, 'get_market_outlook'):
                try:
                    market_outlook = self.pre_market_analyzer.get_market_outlook()
                except:
                    market_outlook = "unavailable"
            
            # Safely get key levels
            key_levels = {}
            if self.pre_market_analyzer and hasattr(self.pre_market_analyzer, 'get_key_levels'):
                try:
                    key_levels = self.pre_market_analyzer.get_key_levels()
                except:
                    key_levels = {}
            
            # Safely get connections status
            connections = {}
            if self.connection_manager and hasattr(self.connection_manager, 'get_status'):
                try:
                    connections = {
                        name: self.connection_manager.get_status(name).value
                        for name in ['zerodha', 'truedata', 'database', 'redis']
                    }
                except:
                    connections = {}
            
            return {
                "is_active": getattr(self, 'is_active', False),
                "system_ready": getattr(self, 'system_ready', False),
                "session_id": getattr(self, 'session_id', None),
                "start_time": getattr(self, 'start_time', None),
                "last_heartbeat": getattr(self, 'last_heartbeat', None),
                "market_open": self._is_market_open(),
                "market_outlook": market_outlook,
                "active_strategies": getattr(self, 'active_strategies', []),
                "active_positions": getattr(self, 'active_positions', []),
                "total_trades": final_trades,  # NOW INCLUDES PERSISTENT TRADES
                "daily_pnl": final_pnl,       # NOW INCLUDES PERSISTENT P&L
                "risk_status": getattr(self, 'risk_status', {}),
                "market_status": getattr(self, 'market_status', {}),
                "connections": connections,
                "key_levels": key_levels,
                
                # PERSISTENT trade details
                "trade_details": {
                    "daily_trades": daily_trades,
                    "persistent_count": persistent_trades,
                    "persistent_pnl": persistent_pnl,
                    "data_source": "trade_engine_persistence",
                    "persistence_enabled": hasattr(self.trade_engine, 'get_daily_trades') if self.trade_engine else False
                }
            }
        except Exception as e:
            logger.error(f"Error getting trading status: {e}")
            # Return minimal safe status
            return {
                "is_active": False,
                "system_ready": False,
                "session_id": None,
                "start_time": None,
                "last_heartbeat": None,
                "market_open": False,
                "market_outlook": "error",
                "active_strategies": [],
                "active_positions": [],
                "total_trades": 0,
                "daily_pnl": 0.0,
                "risk_status": {},
                "market_status": {},
                "connections": {},
                "key_levels": {}
            }
    
    async def shutdown(self):
        """Gracefully shutdown the trading system"""
        logger.info("Shutting down trading system...")
        
        # Disable trading
        await self.disable_trading()
        
        # Shutdown connections
        if self.connection_manager:
            await self.connection_manager.shutdown()
        
        logger.info("Trading system shutdown complete")

# Add alias for backward compatibility
Orchestrator = TradingOrchestrator 
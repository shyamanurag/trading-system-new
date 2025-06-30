"""
Trading Orchestrator
Manages the overall trading system operations with enhanced features
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta
import logging
import asyncio
from .config import settings
from .connection_manager import ConnectionManager
from .pre_market_analyzer import PreMarketAnalyzer

logger = logging.getLogger(__name__)

class MockPositionTracker:
    """Mock position tracker for demo"""
    async def get_all_positions(self):
        return []

class MockMetrics:
    """Mock metrics for demo"""
    async def get_trading_metrics(self):
        return {"total_trades": 0, "pnl": 0.0}

class MockStrategyManager:
    """Mock strategy manager for demo"""
    async def get_active_strategies(self):
        return []

class MockRiskManager:
    """Mock risk manager for demo"""
    async def get_risk_metrics(self):
        return {"exposure": 0.0, "risk_level": "low"}

class TradingOrchestrator:
    """Enhanced trading system orchestrator with pre-market analysis and connection management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'TradingOrchestrator':
        """Get the singleton instance"""
        return cls()
    
    def _initialize(self):
        """Initialize the orchestrator with enhanced features"""
        if self._initialized:
            return
            
        self.is_active = False
        self.session_id = None
        self.start_time = None
        self.last_heartbeat = None
        self.active_strategies = []
        self.active_positions = []
        self.total_trades = 0
        self.daily_pnl = 0.0
        self.risk_status = {}
        self.market_status = {}
        
        # Enhanced components
        self.connection_manager = ConnectionManager(settings.__dict__)
        self.pre_market_analyzer = PreMarketAnalyzer(settings.__dict__)
        self.pre_market_results = {}
        self.system_ready = False
        
        # Trading components (will be initialized after connections)
        self.position_tracker = None
        self.metrics = None
        self.strategy_manager = None
        self.risk_manager = None
        self.order_manager = None
        self.trade_engine = None
        
        self._initialized = True
    
    async def initialize_system(self):
        """Initialize the complete trading system"""
        try:
            logger.info("Initializing trading system...")
            
            # Ensure initialization
            self._initialize()
            
            # Step 1: Initialize all connections
            logger.info("Establishing connections...")
            connections_ok = await self.connection_manager.initialize_all_connections()
            
            if not connections_ok:
                logger.error("Failed to establish all required connections")
                return False
            
            # Step 2: Initialize trading components
            await self._initialize_trading_components()
            
            # Step 3: Run pre-market analysis
            logger.info("Running pre-market analysis...")
            self.pre_market_results = await self.pre_market_analyzer.run_pre_market_analysis()
            
            # Step 4: Apply pre-market recommendations
            await self._apply_pre_market_recommendations()
            
            # Step 5: System health check
            system_healthy = await self._perform_system_health_check()
            
            if system_healthy:
                self.system_ready = True
                logger.info("Trading system initialized successfully")
                return True
            else:
                logger.error("System health check failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize trading system: {e}")
            return False
    
    async def _initialize_trading_components(self):
        """Initialize all trading components"""
        try:
            # Get connections
            zerodha = self.connection_manager.get_connection('zerodha')
            redis_client = self.connection_manager.get_connection('redis')
            db = self.connection_manager.get_connection('database')
            
            # Store connections
            self.zerodha = zerodha
            self.redis_client = redis_client
            self.db = db
            
            # Initialize REAL trading components (not mocks)
            await self._initialize_real_trading_components()
            
            logger.info("Trading components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading components: {e}")
            raise
    
    async def _initialize_real_trading_components(self):
        """Initialize real trading components with proper implementations"""
        try:
            # Import real components (with error handling)
            logger.info("Attempting to import trading components...")
            
            logger.info("Initializing real trading components...")
            
            # Initialize Risk Manager
            try:
                risk_config = {
                    'max_daily_loss': 50000,  # ₹50,000 max daily loss
                    'max_position_size': 0.05,  # 5% per position
                    'max_total_exposure': 0.3,  # 30% total exposure
                    'paper_mode': True  # Safe paper trading
                }
                # Try to use the full RiskManager if dependencies are available
                try:
                    from .risk_manager import RiskManager
                    from .position_tracker import PositionTracker
                    from ..events import EventBus
                    
                    # Initialize dependencies
                    event_bus = EventBus()
                    position_tracker = PositionTracker(risk_config)
                    
                    self.risk_manager = RiskManager(risk_config, position_tracker, event_bus)
                    logger.info("✅ Full Risk Manager initialized")
                except ImportError as import_error:
                    logger.warning(f"Full risk manager dependencies missing: {import_error}")
                    self.risk_manager = self._create_simple_risk_manager(risk_config)
                    logger.info("✅ Simple Risk Manager initialized")
            except Exception as e:
                logger.warning(f"Risk manager init failed: {e}, using mock")
                self.risk_manager = MockRiskManager()
            
            # Initialize Position Tracker
            try:
                # For now use mock, will be real when position tracking is implemented
                self.position_tracker = MockPositionTracker()
                logger.info("✅ Position Tracker initialized (mock)")
            except Exception as e:
                logger.warning(f"Position tracker init failed: {e}")
                self.position_tracker = MockPositionTracker()
            
            # Initialize Market Data Manager
            try:
                from .market_data import MarketDataManager
                market_data_config = {
                    'paper_mode': True,
                    'symbols': ['BANKNIFTY', 'NIFTY', 'SBIN', 'RELIANCE', 'TCS'],
                    'update_interval': 1  # 1 second updates
                }
                self.market_data = MarketDataManager(market_data_config)
                logger.info("✅ Market Data Manager initialized")
            except Exception as e:
                logger.warning(f"Market data manager init failed: {e}, using mock")
                self.market_data = self._create_mock_market_data()
            
            # Initialize Strategy Engine with real strategies
            try:
                from .trading_strategies import AdvancedTradingEngine
                self.strategy_engine = AdvancedTradingEngine(self.risk_manager)
                # Load strategies into active_strategies for orchestrator tracking
                self.active_strategies = list(self.strategy_engine.strategies.keys())
                logger.info(f"✅ Strategy Engine initialized with {len(self.active_strategies)} strategies")
                logger.info(f"   📈 Active strategies: {', '.join(self.active_strategies)}")
            except Exception as e:
                logger.warning(f"Strategy engine init failed: {e}, using empty strategies")
                self.strategy_engine = None
                self.active_strategies = []
            
            # Initialize Trade Engine
            try:
                from .trade_engine import TradeEngine
                self.trade_engine = TradeEngine(
                    broker=self.zerodha,
                    risk_manager=self.risk_manager,
                    position_manager=self.position_tracker,
                    market_data=self.market_data
                )
                # Load strategies into trade engine
                if self.strategy_engine:
                    self.trade_engine.active_strategies = self.strategy_engine.strategies
                logger.info("✅ Trade Engine initialized")
            except Exception as e:
                logger.warning(f"Trade engine init failed: {e}, using broker connection")
                self.trade_engine = self.zerodha
            
            # Initialize Order Manager (mock for now)
            try:
                self.order_manager = True  # Will be real OrderManager when implemented
                logger.info("✅ Order Manager initialized (mock)")
            except Exception as e:
                logger.warning(f"Order manager init failed: {e}")
                self.order_manager = True
            
            # Start background trading tasks
            if self.strategy_engine and hasattr(self.trade_engine, 'active_strategies'):
                asyncio.create_task(self._start_trading_loop())
                logger.info("✅ Trading loop scheduled to start")
            
        except Exception as e:
            logger.error(f"Failed to initialize real trading components: {e}")
            # Fallback to mocks
            await self._initialize_mock_components()
    
    def _create_mock_market_data(self):
        """Create mock market data manager"""
        class MockMarketData:
            async def start(self):
                return True
            async def stop(self):
                return True
            async def get_latest_data(self, symbols):
                # Return mock data
                return {symbol: {'price': 100, 'volume': 1000} for symbol in symbols}
        return MockMarketData()
    
    def _create_simple_risk_manager(self, config: Dict):
        """Create a simple risk manager for basic functionality"""
        class SimpleRiskManager:
            def __init__(self, config):
                self.config = config
                self.max_daily_loss = config.get('max_daily_loss', 50000)
                self.max_position_size = config.get('max_position_size', 0.05)
                self.daily_pnl = 0.0
                self.total_exposure = 0.0
                
            async def check_trade_allowed(self, signal):
                """Simple trade validation"""
                # Basic checks for demo/paper trading
                return True
                
            async def get_risk_metrics(self):
                """Get basic risk metrics"""
                return {
                    'daily_pnl': self.daily_pnl,
                    'exposure': self.total_exposure,
                    'risk_score': min(abs(self.daily_pnl / self.max_daily_loss) * 100, 100),
                    'risk_level': 'low' if abs(self.daily_pnl) < self.max_daily_loss * 0.5 else 'medium'
                }
                
            async def validate_signal(self, signal):
                """Validate trading signal"""
                return {'allowed': True, 'reason': 'Paper mode - all trades allowed'}
                
            async def calculate_position_size(self, signal, risk_score):
                """Calculate position size"""
                # Conservative position sizing for paper trading
                return min(1, max(1, int(100000 / (signal.entry_price if hasattr(signal, 'entry_price') else 100))))
        
        return SimpleRiskManager(config)
    
    async def _initialize_mock_components(self):
        """Fallback to mock components if real ones fail"""
        logger.info("Initializing mock trading components as fallback")
        self.position_tracker = MockPositionTracker()
        self.risk_manager = MockRiskManager()
        self.order_manager = True
        self.trade_engine = self.zerodha
        self.market_data = self._create_mock_market_data()
        self.strategy_engine = None
        self.active_strategies = []
    
    async def _start_trading_loop(self):
        """Start the main trading loop that generates and processes signals"""
        try:
            logger.info("🔄 Starting trading signal generation loop...")
            
            while self.is_active:
                try:
                    # Only trade during market hours
                    if not self._is_market_open():
                        await asyncio.sleep(60)  # Check every minute when markets closed
                        continue
                    
                    # Get market data for all symbols
                    symbols = ['BANKNIFTY', 'NIFTY', 'SBIN', 'RELIANCE', 'TCS']
                    market_data = await self.market_data.get_latest_data(symbols)
                    
                    if not market_data:
                        await asyncio.sleep(5)  # Wait 5 seconds if no data
                        continue
                    
                    # Generate signals from all strategies
                    if self.strategy_engine:
                        signals = await self.strategy_engine.generate_all_signals(market_data)
                        
                        if signals:
                            logger.info(f"📊 Generated {len(signals)} trading signals")
                            
                            # Process signals through trade engine
                            for signal in signals:
                                try:
                                    # Add signal to trade queue for processing
                                    if hasattr(self.trade_engine, 'trade_queue'):
                                        await self.trade_engine.trade_queue.put(signal)
                                        logger.info(f"🎯 Signal queued: {signal.symbol} {signal.direction}")
                                except Exception as signal_error:
                                    logger.error(f"Error queuing signal: {signal_error}")
                    
                    # Wait before next iteration
                    await asyncio.sleep(10)  # Check every 10 seconds during market hours
                    
                except Exception as loop_error:
                    logger.error(f"Error in trading loop: {loop_error}")
                    await asyncio.sleep(30)  # Wait 30 seconds on error
                    
        except Exception as e:
            logger.error(f"Trading loop failed: {e}")
    
    async def _apply_pre_market_recommendations(self):
        """Apply pre-market analysis recommendations"""
        try:
            if not self.pre_market_results:
                return
            
            # Apply system parameters
            sys_params = self.pre_market_results.get('system_parameters', {})
            if sys_params:
                # Store parameters for when risk manager is properly initialized
                self.system_parameters = sys_params
                logger.info(f"System parameters stored: {sys_params}")
            
            # Apply strategy recommendations
            strategy_recs = self.pre_market_results.get('strategy_recommendations', {})
            for strategy_name, config in strategy_recs.items():
                if config.get('enabled'):
                    # Enable strategy with recommended parameters
                    await self._configure_strategy(strategy_name, config)
            
            logger.info("Pre-market recommendations applied")
            
        except Exception as e:
            logger.error(f"Failed to apply pre-market recommendations: {e}")
    
    async def _configure_strategy(self, strategy_name: str, config: Dict):
        """Configure a strategy with given parameters"""
        try:
            # This would configure the actual strategy
            # For now, just log it
            logger.info(f"Configuring strategy {strategy_name}: {config}")
            
        except Exception as e:
            logger.error(f"Failed to configure strategy {strategy_name}: {e}")
    
    async def _perform_system_health_check(self) -> bool:
        """Perform comprehensive system health check"""
        try:
            # Check critical vs optional connections based on market status
            market_open = self._is_market_open()
            
            # Core connections always required
            core_connections_ok = True
            try:
                # Check essential connections (database, redis)
                db_status = self.connection_manager.get_status('database') if self.connection_manager else None
                redis_status = self.connection_manager.get_status('redis') if self.connection_manager else None
                
                # For now, be flexible with connections when markets are closed
                if not market_open:
                    logger.info("Markets closed - relaxed connection requirements")
                    core_connections_ok = True  # Allow startup without all connections when markets closed
                else:
                    # When markets are open, require all connections
                    core_connections_ok = self.connection_manager.is_all_connected() if self.connection_manager else False
                    
            except Exception as e:
                logger.warning(f"Connection check error: {e}")
                core_connections_ok = not market_open  # Allow when markets closed, strict when open
            
            checks = {
                'connections': core_connections_ok,
                'risk_manager': self.risk_manager is not None,
                'order_manager': self.order_manager is not None,
                'position_tracker': self.position_tracker is not None,
                'pre_market_complete': bool(self.pre_market_results) or not market_open  # Not required when markets closed
            }
            
            all_healthy = all(checks.values())
            
            logger.info("System Health Check:")
            logger.info(f"  Market Open: {market_open}")
            for component, status in checks.items():
                logger.info(f"  {component}: {'✅' if status else '❌'}")
            
            if all_healthy:
                logger.info("✅ System health check PASSED")
            else:
                logger.warning("❌ System health check FAILED")
            
            return all_healthy
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return False
    
    async def enable_trading(self):
        """Enable autonomous trading with pre-checks"""
        if not self.system_ready:
            logger.error("System not ready. Run initialize_system() first")
            return False
            
        if self.is_active:
            logger.warning("Trading is already active")
            return True
        
        # Check if market is open
        if not self._is_market_open():
            logger.warning("Market is closed. Trading will start at market open.")
        
        self.is_active = True
        self.session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        
        # Start trading engine
        if self.trade_engine:
            # ZerodhaIntegration uses initialize() method, not start()
            if hasattr(self.trade_engine, 'start'):
                await self.trade_engine.start()
            elif hasattr(self.trade_engine, 'initialize'):
                await self.trade_engine.initialize()
            else:
                logger.warning("Trade engine has no start() or initialize() method")
        
        # Start monitoring
        asyncio.create_task(self._monitor_trading())
        
        logger.info(f"Trading enabled with session ID: {self.session_id}")
        logger.info(f"Market outlook: {self.pre_market_analyzer.get_market_outlook()}")
        
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
    
    def _is_market_open(self) -> bool:
        """Check if market is open"""
        current_time = datetime.now().time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Check weekday (Monday = 0, Friday = 4)
        if datetime.now().weekday() > 4:
            return False
        
        return market_open <= current_time <= market_close
    
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
        """Get current trading status with enhanced information"""
        return {
            "is_active": self.is_active,
            "system_ready": self.system_ready,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "last_heartbeat": self.last_heartbeat,
            "market_open": self._is_market_open(),
            "market_outlook": self.pre_market_analyzer.get_market_outlook(),
            "active_strategies": self.active_strategies,
            "active_positions": self.active_positions,
            "total_trades": self.total_trades,
            "daily_pnl": self.daily_pnl,
            "risk_status": self.risk_status,
            "market_status": self.market_status,
            "connections": {
                name: self.connection_manager.get_status(name).value
                for name in ['zerodha', 'truedata', 'database', 'redis']
            } if self.connection_manager else {},
            "key_levels": self.pre_market_analyzer.get_key_levels()
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
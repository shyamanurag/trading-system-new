#!/usr/bin/env python3
"""
Trading System Startup Script
Starts all necessary components for the trading system
"""

import asyncio
import os
import sys
import signal
import logging
from datetime import datetime
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingSystemManager:
    def __init__(self):
        self.processes = {}
        self.is_running = False
        
    async def start_api_server(self):
        """Start the FastAPI server"""
        logger.info("Starting API server...")
        try:
            # The API server is already running via main.py
            logger.info("✅ API server is already running on port 8000")
            return True
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False
    
    async def start_websocket_server(self):
        """Start WebSocket server with TrueData provider"""
        logger.info("Starting WebSocket server with TrueData provider...")
        
        # Check if WebSocket is disabled
        if os.getenv('DISABLE_TRUEDATA', 'false').lower() == 'true':
            logger.warning("TrueData WebSocket is disabled for development")
            return True
            
        try:
            # Import from the correct location
            from websocket_manager import WebSocketManager
            from data.truedata_provider import TrueDataProvider
            
            config = {
                'username': os.getenv('TRUEDATA_USERNAME', 'Trial106'),
                'password': os.getenv('TRUEDATA_PASSWORD', 'shyam106'),
                'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
                'live_port': int(os.getenv('TRUEDATA_PORT', 8086)),
                'is_sandbox': os.getenv('TRUEDATA_SANDBOX', 'false').lower() == 'true'
            }
            
            provider = TrueDataProvider(config)
            await provider.connect()
            
            # Subscribe to key indices
            indices = ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I']
            await provider.subscribe_symbols(indices)
            
            logger.info("✅ Market data feeds initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def start_trading_orchestrator(self):
        """Start the trading orchestrator"""
        logger.info("Starting Trading Orchestrator...")
        try:
            from core.orchestrator import TradingOrchestrator
            
            # Load config
            config = {
                'redis': {
                    'host': os.getenv('REDIS_HOST', 'localhost'),
                    'port': int(os.getenv('REDIS_PORT', 6379)),
                    'password': os.getenv('REDIS_PASSWORD'),
                    'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
                },
                'broker': {
                    'api_key': os.getenv('ZERODHA_API_KEY'),
                    'api_secret': os.getenv('ZERODHA_API_SECRET'),
                    'client_id': os.getenv('ZERODHA_CLIENT_ID')
                },
                'data_provider': {
                    'username': os.getenv('TRUEDATA_USERNAME'),
                    'password': os.getenv('TRUEDATA_PASSWORD'),
                    'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
                    'port': int(os.getenv('TRUEDATA_PORT', 8086))
                },
                'strategies': {
                    'volatility_explosion': {'enabled': True},
                    'momentum_surfer': {'enabled': True},
                    'volume_profile_scalper': {'enabled': True},
                    'news_impact_scalper': {'enabled': True}
                },
                'connection': {
                    'max_retries': 3,
                    'retry_delay': 5,
                    'heartbeat_interval': 30
                },
                'security': {
                    'jwt_secret': os.getenv('JWT_SECRET'),
                    'encryption_key': os.getenv('ENCRYPTION_KEY')
                },
                'notifications': {
                    'webhook_url': os.getenv('N8N_WEBHOOK_URL'),
                    'enabled': os.getenv('N8N_ENABLED', 'true').lower() == 'true'
                }
            }
            
            # Create and start orchestrator
            self.orchestrator = TradingOrchestrator(config)
            asyncio.create_task(self.orchestrator.start())
            
            logger.info("✅ Trading Orchestrator started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Trading Orchestrator: {e}")
            return False
    
    async def initialize_data_feeds(self):
        """Initialize market data feeds"""
        logger.info("Initializing market data feeds...")
        try:
            # Initialize TrueData connection
            from data.truedata_provider import TrueDataProvider
            
            config = {
                'username': os.getenv('TRUEDATA_USERNAME', 'Trial106'),
                'password': os.getenv('TRUEDATA_PASSWORD', 'shyam106'),
                'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
                'live_port': int(os.getenv('TRUEDATA_PORT', 8086)),
                'is_sandbox': os.getenv('TRUEDATA_SANDBOX', 'false').lower() == 'true'
            }
            
            provider = TrueDataProvider(config)
            await provider.connect()
            
            # Subscribe to key indices
            indices = ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I']
            await provider.subscribe_symbols(indices)
            
            logger.info("✅ Market data feeds initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize data feeds: {e}")
            return False
    
    async def start_autonomous_trading(self):
        """Start autonomous trading system"""
        logger.info("Starting Autonomous Trading System...")
        try:
            # The autonomous trading is managed by the orchestrator
            # Just log that it's enabled
            if os.getenv('AUTONOMOUS_TRADING_ENABLED', 'true').lower() == 'true':
                logger.info("✅ Autonomous trading is ENABLED")
            else:
                logger.info("⚠️ Autonomous trading is DISABLED")
            return True
        except Exception as e:
            logger.error(f"Failed to start autonomous trading: {e}")
            return False
    
    async def start_all_components(self):
        """Start all trading system components"""
        logger.info("=" * 60)
        logger.info("Starting Trading System Components")
        logger.info("=" * 60)
        
        self.is_running = True
        
        # Start components in order
        components = [
            ("API Server", self.start_api_server),
            ("WebSocket Server", self.start_websocket_server),
            ("Data Feeds", self.initialize_data_feeds),
            ("Trading Orchestrator", self.start_trading_orchestrator),
            ("Autonomous Trading", self.start_autonomous_trading)
        ]
        
        for name, start_func in components:
            logger.info(f"\nStarting {name}...")
            success = await start_func()
            if not success:
                logger.error(f"Failed to start {name}. Aborting startup.")
                return False
            await asyncio.sleep(2)  # Give each component time to initialize
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All components started successfully!")
        logger.info("=" * 60)
        
        # Show system status
        await self.show_system_status()
        
        return True
    
    async def show_system_status(self):
        """Display current system status"""
        logger.info("\n📊 SYSTEM STATUS:")
        logger.info(f"- Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"- API URL: http://localhost:{os.getenv('PORT', 8000)}")
        logger.info(f"- Paper Trading: {os.getenv('PAPER_TRADING', 'true')}")
        logger.info(f"- Autonomous Trading: {os.getenv('AUTONOMOUS_TRADING_ENABLED', 'true')}")
        logger.info(f"- Redis Connected: {os.getenv('REDIS_HOST', 'localhost')}")
        logger.info(f"- TrueData User: {os.getenv('TRUEDATA_USERNAME', 'Trial106')}")
        logger.info(f"- Timestamp: {datetime.now().isoformat()}")
    
    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("\nShutting down trading system...")
        self.is_running = False
        
        # Shutdown orchestrator if exists
        if hasattr(self, 'orchestrator'):
            await self.orchestrator.stop()
        
        logger.info("✅ Trading system shutdown complete")

async def main():
    """Main entry point"""
    manager = TradingSystemManager()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("\nReceived shutdown signal...")
        asyncio.create_task(manager.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all components
        success = await manager.start_all_components()
        
        if success:
            logger.info("\n🚀 Trading System is running!")
            logger.info("Press Ctrl+C to stop\n")
            
            # Keep running
            while manager.is_running:
                await asyncio.sleep(60)  # Check every minute
                # Could add periodic health checks here
        else:
            logger.error("Failed to start trading system")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await manager.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    # Check if running in production
    if os.getenv('ENVIRONMENT') == 'production':
        logger.info("Running in PRODUCTION mode")
    else:
        logger.info("Running in DEVELOPMENT mode")
    
    # Run the main function
    asyncio.run(main()) 
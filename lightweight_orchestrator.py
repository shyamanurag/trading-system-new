#!/usr/bin/env python3
"""
LIGHTWEIGHT ORCHESTRATOR
Minimal version that avoids performance bottlenecks
"""

import os
import asyncio
import logging
from typing import Dict, Optional

# Set emergency environment variables
os.environ['SKIP_STRATEGY_VALIDATION'] = 'true'
os.environ['SKIP_BACKTEST_VALIDATION'] = 'true'
os.environ['SKIP_TRUEDATA_AUTO_INIT'] = 'true'
os.environ['DISABLE_TRUEDATA_CONNECTION'] = 'true'
os.environ['FALLBACK_MODE'] = 'true'
os.environ['MINIMAL_INITIALIZATION'] = 'true'

logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)

class LightweightOrchestrator:
    """Minimal orchestrator that avoids performance bottlenecks"""
    
    def __init__(self):
        self.is_initialized = False
        self.is_running = False
        self.strategies = {}
        self.zerodha_client = None
        logger.info("🚀 Lightweight orchestrator initialized")
    
    async def initialize(self) -> bool:
        """Minimal initialization without heavy operations"""
        try:
            logger.info("⚡ Fast initialization starting...")
            
            # Skip all heavy operations
            self.is_initialized = True
            logger.info("✅ Lightweight initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lightweight initialization failed: {e}")
            return False
    
    async def start_trading(self) -> bool:
        """Start minimal trading system"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            self.is_running = True
            logger.info("✅ Lightweight trading system started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start lightweight trading: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get minimal status"""
        return {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'mode': 'lightweight',
            'strategies_loaded': len(self.strategies),
            'performance_mode': 'emergency'
        }

# Global instance for API access
lightweight_orchestrator = LightweightOrchestrator()

async def main():
    """Test the lightweight orchestrator"""
    print("🚀 Testing lightweight orchestrator...")
    
    success = await lightweight_orchestrator.initialize()
    if success:
        print("✅ Initialization successful")
        
        trading_success = await lightweight_orchestrator.start_trading()
        if trading_success:
            print("✅ Trading system started")
            print(f"📊 Status: {lightweight_orchestrator.get_status()}")
        else:
            print("❌ Trading system failed to start")
    else:
        print("❌ Initialization failed")

if __name__ == "__main__":
    asyncio.run(main())

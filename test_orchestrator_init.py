#!/usr/bin/env python3
"""
Diagnostic script to test orchestrator initialization
This will help identify what's failing during the initialize() method
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_orchestrator_initialization():
    """Test orchestrator initialization step by step"""
    try:
        logger.info("🔧 Testing Orchestrator Initialization...")
        
        # Step 1: Import the orchestrator
        logger.info("Step 1: Importing TradingOrchestrator...")
        from src.core.orchestrator import TradingOrchestrator
        logger.info("✅ TradingOrchestrator imported successfully")
        
        # Step 2: Create instance
        logger.info("Step 2: Creating orchestrator instance...")
        orchestrator = TradingOrchestrator()
        logger.info("✅ Orchestrator instance created successfully")
        
        # Step 3: Test individual initialization steps
        logger.info("Step 3: Testing initialization...")
        
        # Check what happens during initialize
        try:
            init_result = await orchestrator.initialize()
            logger.info(f"✅ Initialize result: {init_result}")
            
            if init_result:
                logger.info("🎉 Orchestrator initialized successfully!")
                
                # Test basic functionality
                logger.info("Testing basic functionality...")
                status = await orchestrator.get_status()
                logger.info(f"Status: {status}")
                
            else:
                logger.error("❌ Orchestrator initialization returned False")
                
        except Exception as init_error:
            logger.error(f"❌ Initialization failed with error: {init_error}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
    except ImportError as import_error:
        logger.error(f"❌ Import error: {import_error}")
        
    except Exception as e:
        logger.error(f"❌ General error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("🚀 Starting Orchestrator Diagnostic Test...")
    asyncio.run(test_orchestrator_initialization())
    logger.info("🏁 Diagnostic test completed") 
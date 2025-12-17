"""
Shared FastAPI Dependencies
Centralized dependency injection to prevent singleton issues
"""
import asyncio
import logging
from .orchestrator import get_orchestrator as get_orchestrator_async, get_orchestrator_instance

logger = logging.getLogger(__name__)

async def get_orchestrator():
    """
    Get the singleton orchestrator instance - FAST PATH first to prevent 504 timeouts.
    CRITICAL: This is the ONLY function that should create/return orchestrator instances
    """
    logger.debug("🔧 get_orchestrator() called from dependencies.py")
    
    # FAST PATH: Check global instance directly (non-blocking)
    # This is set by main.py during startup
    orchestrator = get_orchestrator_instance()
    if orchestrator is not None:
        logger.debug("   Fast path: returning existing orchestrator instance")
        return orchestrator
    
    # SLOW PATH: Try async initialization with timeout to prevent 504
    try:
        orchestrator = await asyncio.wait_for(get_orchestrator_async(), timeout=5.0)
        logger.debug("   Slow path: orchestrator initialized within timeout")
        return orchestrator
    except asyncio.TimeoutError:
        logger.warning("⚠️ Orchestrator initialization timed out (5s) - returning None")
        return None
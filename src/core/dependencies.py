"""
Shared FastAPI Dependencies
Centralized dependency injection to prevent singleton issues
"""
import logging
from .orchestrator import TradingOrchestrator

logger = logging.getLogger(__name__)

def get_orchestrator() -> TradingOrchestrator:
    """
    Get the singleton orchestrator instance
    CRITICAL: This is the ONLY function that should create/return orchestrator instances
    """
    logger.debug("🔧 get_orchestrator() called from dependencies.py")
    
    orchestrator = TradingOrchestrator.get_instance()
    instance_id = getattr(orchestrator, '_instance_id', 'unknown')
    logger.debug(f"   Returning instance: {instance_id}")
    
    # Ensure initialization (idempotent)
    orchestrator._initialize()
    
    return orchestrator 
"""
Bootstrap module for development - SIMPLIFIED
This file is for development only. Production uses main.py
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path
from src.monitoring.event_monitor import EventMonitor
from src.core.database_schema_manager import DatabaseSchemaManager
from src.core.config import AppConfig, DatabaseConfig
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan manager for development"""
    logger.info("Bootstrap startup...")
    yield
    logger.info("Bootstrap shutdown...")

async def initialize_system(config: AppConfig) -> Dict[str, Any]:
    """Initialize all system components"""
    logger.info("Starting system initialization...")
    
    components = {}
    
    try:
        # Initialize database configuration first
        db_config = DatabaseConfig()
        components['db_config'] = db_config
        
        # Ensure precise database schema - this is the definitive approach
        logger.info("Ensuring precise database schema...")
        schema_manager = DatabaseSchemaManager(db_config.database_url)
        schema_result = schema_manager.ensure_precise_schema()
        
        if schema_result['status'] == 'success':
            logger.info("✅ Database schema verified - all tables have precise structure")
        else:
            logger.error(f"❌ Database schema verification failed: {schema_result['errors']}")
            # Continue anyway - system can work with partial schema
        
        # Initialize Redis connection
        logger.info("Initializing Redis connection...")

def create_app():
    """Create FastAPI app for development"""
    logger.warning("⚠️ Using bootstrap.py - This is for development only!")
    logger.warning("⚠️ Production should use main.py")
    
    # Simple app for development
    app = FastAPI(
        title="Trading System API (Development)",
        description="Development bootstrap - Use main.py for production",
        version="DEV",
        lifespan=lifespan
    )
    
    # Basic health check
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "mode": "development",
            "warning": "This is development bootstrap - use main.py for production"
        }
    
    return app

# Create app if this module is imported
app = create_app() 
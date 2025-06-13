"""
Graceful Shutdown Manager
Handles clean shutdown of system components
"""
import logging
import asyncio
import signal
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GracefulShutdown:
    def __init__(self):
        self.components: List[object] = []
        self.is_running = False
        self.shutdown_timeout = 30  # seconds
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the shutdown handler"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
        
        logger.info("Graceful shutdown handler started")
    
    async def stop(self):
        """Stop the shutdown handler"""
        self.is_running = False
        logger.info("Graceful shutdown handler stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.shutdown())
    
    async def register_component(self, component):
        """Register a component for shutdown"""
        if component not in self.components:
            self.components.append(component)
            logger.info(f"Registered component for shutdown: {component.__class__.__name__}")
    
    async def shutdown(self):
        """Initiate graceful shutdown"""
        if self._shutdown_event.is_set():
            return
            
        self._shutdown_event.set()
        logger.info("Initiating graceful shutdown...")
        
        try:
            # Start shutdown timer
            shutdown_task = asyncio.create_task(self._shutdown_timeout_handler())
            
            # Shutdown components
            await self._shutdown_components()
            
            # Cancel shutdown timer
            shutdown_task.cancel()
            
            logger.info("Shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise
    
    async def _shutdown_timeout_handler(self):
        """Handle shutdown timeout"""
        try:
            await asyncio.sleep(self.shutdown_timeout)
            logger.warning("Shutdown timeout reached, forcing shutdown")
            await self._force_shutdown_components()
        except asyncio.CancelledError:
            pass
    
    async def _shutdown_components(self):
        """Shutdown all registered components"""
        shutdown_tasks = []
        
        for component in self.components:
            if hasattr(component, 'stop'):
                shutdown_tasks.append(self._shutdown_component(component))
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
    
    async def _force_shutdown_components(self):
        """Force shutdown all components"""
        for component in self.components:
            try:
                if hasattr(component, 'stop'):
                    await component.stop()
            except Exception as e:
                logger.error(f"Error during forced shutdown of {component.__class__.__name__}: {e}")
    
    async def _shutdown_component(self, component):
        """Shutdown a single component"""
        try:
            logger.info(f"Shutting down {component.__class__.__name__}")
            await component.stop()
            logger.info(f"Successfully shut down {component.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error shutting down {component.__class__.__name__}: {e}")
            raise 
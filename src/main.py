"""
Main entry point for the trading system.
This is a thin wrapper around the bootstrap module that handles the actual application setup.
"""
import uvicorn
from .bootstrap import app

# Add the new imports at the top with other API imports
from .api.dynamic_user_management import router as dynamic_user_router
from .api.user_analytics_service import router as analytics_router
from .core.multi_user_zerodha_manager import multi_user_zerodha_manager

if __name__ == "__main__":
    uvicorn.run(
        "src.bootstrap:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Add the new routers after the existing router includes (around where other API routes are registered)
app.include_router(dynamic_user_router, prefix="/api/v1", tags=["dynamic-users"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

# Add initialization for multi-user components in the startup event or initialization section
@app.on_event("startup")
async def startup_multi_user_systems():
    """Initialize multi-user systems on startup"""
    try:
        # Initialize multi-user Zerodha manager
        await multi_user_zerodha_manager.initialize()
        logger.info("✅ Multi-user Zerodha manager initialized")

        # Initialize analytics service
        from .api.user_analytics_service import analytics_service
        await analytics_service.initialize()
        logger.info("✅ User analytics service initialized")

        # Initialize dynamic user manager
        from .api.dynamic_user_management import user_manager
        await user_manager.initialize()
        logger.info("✅ Dynamic user manager initialized")

    except Exception as e:
        logger.error(f"❌ Error initializing multi-user systems: {e}") 
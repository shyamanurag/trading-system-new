"""
API Routes
Handles HTTP endpoints for the trading system
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .utils.secure_decorators import require_webhook, rate_limit

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading System API",
    description="API endpoints for the trading system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store orchestrator instance
_orchestrator = None

def init_api(orchestrator):
    """Initialize API with orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator

@app.post("/webhook")
@require_webhook(_orchestrator.security_manager)
@rate_limit(100, 60)
async def handle_webhook(request: Request):
    """Handle incoming webhook requests"""
    try:
        # Get webhook data
        data = await request.json()
        
        # Validate webhook data
        if not data:
            raise HTTPException(status_code=400, detail="Empty webhook data")
        
        # Process webhook based on type
        webhook_type = data.get('type')
        if not webhook_type:
            raise HTTPException(status_code=400, detail="Missing webhook type")
        
        # Handle different webhook types
        if webhook_type == 'market_data':
            await _orchestrator.data_connection.process_webhook(data)
        elif webhook_type == 'order_update':
            await _orchestrator.broker_connection.process_webhook(data)
        elif webhook_type == 'system_alert':
            await _orchestrator.notifier.send_alert(data)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown webhook type: {webhook_type}")
        
        return {"status": "success", "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check system components
        health_status = {
            "status": "healthy",
            "components": {
                "orchestrator": _orchestrator.is_running if _orchestrator else False,
                "broker_connection": _orchestrator.broker_connection.is_connected if _orchestrator else False,
                "data_connection": _orchestrator.data_connection.is_connected if _orchestrator else False,
                "redis": await _orchestrator.redis_client.ping() if _orchestrator else False
            }
        }
        
        # Check if any component is unhealthy
        if not all(health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return health_status
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        if not _orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        return {
            "metrics": _orchestrator.metrics,
            "risk_metrics": await _orchestrator.risk_manager.get_risk_metrics(),
            "last_update": _orchestrator.last_update.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control")
async def control_system(action: str):
    """Control system operations"""
    try:
        if not _orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        if action == "start":
            await _orchestrator.start()
        elif action == "stop":
            await _orchestrator.stop()
        elif action == "pause":
            await _orchestrator.pause()
        elif action == "resume":
            await _orchestrator.resume()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
        return {"status": "success", "message": f"System {action}ed"}
    
    except Exception as e:
        logger.error(f"Error controlling system: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
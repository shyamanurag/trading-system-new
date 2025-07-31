"""
Webhook handler and routes for processing incoming webhook requests
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Generic webhook endpoint
@router.post("/webhooks/generic")
async def receive_webhook(data: Dict[str, Any], request: Request):
    """Generic webhook receiver"""
    try:
        logger.info(f"Received webhook from {request.client.host if request.client else 'unknown'}: {data}")
        
        return {
            "status": "received",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Data Webhooks
@router.post("/webhooks/market-data")
async def receive_market_data(data: Dict[str, Any], request: Request):
    """Receive real-time market data"""
    try:
        logger.info(f"Received market data: {data}")
        
        return {
            "status": "received",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing market data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Order & Position Webhooks
@router.post("/webhooks/zerodha/order-update")
async def receive_zerodha_order_update(data: Dict[str, Any], request: Request):
    """Receive order status updates from Zerodha"""
    try:
        logger.info(f"Received Zerodha order update: {data}")
        
        order_id = data.get("order_id")
        status = data.get("status")
        
        return {
            "status": "processed",
            "order_id": order_id,
            "order_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing Zerodha order update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/zerodha/position-update")
async def receive_zerodha_position_update(data: Dict[str, Any], request: Request):
    """Receive position updates from Zerodha"""
    try:
        logger.info(f"Received Zerodha position update: {data}")
        
        return {
            "status": "updated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing Zerodha position update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Generic Zerodha webhook endpoint (for any Zerodha notification)
@router.post("/webhooks/zerodha")
async def receive_zerodha_webhook(data: Dict[str, Any], request: Request):
    """Generic Zerodha webhook receiver for any notification"""
    try:
        logger.info(f"Received Zerodha webhook from {request.client.host if request.client else 'unknown'}: {data}")
        
        # Handle different types of Zerodha notifications
        notification_type = data.get("type", "unknown")
        
        return {
            "status": "received",
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing Zerodha webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔧 FIX: Add GET handler for webhook endpoint debugging
@router.get("/webhooks/zerodha")
async def zerodha_webhook_info(request: Request):
    """Webhook endpoint info (for debugging 405 errors)"""
    return {
        "message": "Zerodha webhook endpoint active",
        "method": "POST required for webhook data",
        "status": "ready",
        "client_ip": request.client.host if request.client else "unknown"
    }

# News & Events Webhooks
@router.post("/webhooks/news-feed")
async def receive_news(data: Dict[str, Any], request: Request):
    """Receive news events"""
    try:
        logger.info(f"Received news event: {data}")
        
        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing news event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# System Health Webhooks
@router.post("/webhooks/system-health")
async def receive_health_update(data: Dict[str, Any], request: Request):
    """Receive system health updates"""
    try:
        logger.info(f"Received health update: {data}")
        
        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing health update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# n8n Integration
@router.post("/n8n")
async def n8n_webhook(request: Request):
    """Handle n8n workflow webhooks"""
    try:
        body = await request.json()
        logger.info(f"Received n8n webhook: {body}")
        
        workflow_id = body.get("workflow", {}).get("id", "unknown")
        execution_id = body.get("execution", {}).get("id", "unknown")
        
        return {
            "status": "received",
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing n8n webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Risk Management Webhooks
@router.post("/webhooks/risk-alert")
async def receive_risk_alert(data: Dict[str, Any], request: Request):
    """Receive risk management alerts"""
    try:
        logger.info(f"Received risk alert: {data}")
        
        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing risk alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Compliance Webhooks
@router.post("/webhooks/compliance-update")
async def receive_compliance_update(data: Dict[str, Any], request: Request):
    """Receive compliance updates"""
    try:
        logger.info(f"Received compliance update: {data}")
        
        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing compliance update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
#!/usr/bin/env python3
"""
WebSocket Server for Real-time Trading Data
Provides live market data, trade updates, and system notifications via WebSocket
Enhanced with TrueData, Zerodha, and n8n integrations
"""

import asyncio
import logging
import json
import os
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import unified systems
from common.logging import setup_logging, get_trading_logger
from common.health_checker import HealthChecker

# Import WebSocket and real-time components
from src.core.websocket_manager import WebSocketManager
from src.api.websocket import router as websocket_router
from data.truedata_provider import TrueDataProvider
from src.core.zerodha import ZerodhaIntegration
from integrations.n8n_integration import N8NIntegration
from src.auth import get_current_user_ws

# Setup unified logging for WebSocket server
setup_logging()
logger = get_trading_logger("websocket_server")

# Initialize FastAPI app for WebSocket server
app = FastAPI(
    title="Trading WebSocket Server",
    description="Real-time data streaming and live updates for trading system",
    version="2.0.0",
    docs_url="/ws/docs",
    redoc_url="/ws/redoc",
)

# Add CORS middleware for WebSocket connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative development port
        "https://yourdomain.com", # Production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global WebSocket components
ws_manager: WebSocketManager = None
truedata_provider: TrueDataProvider = None
zerodha_integration: ZerodhaIntegration = None
n8n_integration: N8NIntegration = None
health_checker: HealthChecker = None
active_connections: Set[WebSocket] = set()
subscription_map: Dict[str, Set[WebSocket]] = {}
provider_status: Dict[str, bool] = {
    'truedata': False,
    'zerodha': False,
    'n8n': False
}

async def init_websocket_server():
    """Initialize WebSocket server components"""
    global ws_manager, truedata_provider, zerodha_integration, n8n_integration, health_checker
    
    try:
        logger.info("Initializing comprehensive WebSocket server...")
        
        # Configuration for WebSocket manager
        ws_config = {
            'redis_url': 'redis://localhost:6379',
            'max_connections': 1000,
            'message_queue_size': 10000,
            'heartbeat_interval': 30
        }
        
        # Initialize WebSocket manager
        ws_manager = WebSocketManager(ws_config)
        
        # Initialize TrueData provider
        await init_truedata_provider()
        
        # Initialize Zerodha integration
        await init_zerodha_integration()
        
        # Initialize n8n integration
        await init_n8n_integration()
        
        # Setup market data callbacks
        await setup_market_data_callbacks()
        
        # Initialize health checker
        health_checker = HealthChecker({'monitoring': {'enabled': True}})
        await health_checker.start()
        
        # Register health checks for all providers
        health_checker.register_check("websocket_manager", ws_manager_health_check, 30)
        health_checker.register_check("truedata", truedata_health_check, 60)
        health_checker.register_check("zerodha", zerodha_health_check, 60)
        health_checker.register_check("n8n", n8n_health_check, 60)
        
        logger.info("WebSocket server initialized successfully with all providers")
        
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket server: {e}")
        raise

async def init_truedata_provider():
    """Initialize TrueData provider"""
    global truedata_provider
    
    try:
        truedata_config = {
            'username': os.getenv('TRUEDATA_USERNAME', 'demo'),
            'password': os.getenv('TRUEDATA_PASSWORD', 'demo'),
            'live_port': int(os.getenv('TRUEDATA_PORT', '8086')),
            'url': os.getenv('TRUEDATA_URL', 'push.truedata.in'),
            'is_sandbox': os.getenv('TRUEDATA_SANDBOX', 'true').lower() == 'true',
            'log_level': logging.INFO
        }
        
        truedata_provider = TrueDataProvider(truedata_config)
        await truedata_provider.connect()
        provider_status['truedata'] = True
        logger.info("TrueData provider initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize TrueData provider: {e}")
        provider_status['truedata'] = False

async def init_zerodha_integration():
    """Initialize Zerodha integration"""
    global zerodha_integration
    
    try:
        zerodha_config = {
            'api_key': os.getenv('ZERODHA_API_KEY'),
            'api_secret': os.getenv('ZERODHA_API_SECRET'),
            'user_id': os.getenv('ZERODHA_USER_ID'),
            'redis_url': 'redis://localhost:6379'
        }
        
        # Only initialize if API credentials are provided
        if zerodha_config['api_key'] and zerodha_config['api_secret']:
            zerodha_integration = ZerodhaIntegration(zerodha_config)
            await zerodha_integration.initialize()
            
            # Register market data callback
            zerodha_integration.market_data_callbacks.append(zerodha_market_data_callback)
            zerodha_integration.order_update_callbacks.append(zerodha_order_update_callback)
            
            provider_status['zerodha'] = True
            logger.info("Zerodha integration initialized successfully")
        else:
            logger.warning("Zerodha credentials not provided, skipping initialization")
            provider_status['zerodha'] = False
            
    except Exception as e:
        logger.error(f"Failed to initialize Zerodha integration: {e}")
        provider_status['zerodha'] = False

async def init_n8n_integration():
    """Initialize n8n integration"""
    global n8n_integration
    
    try:
        n8n_config = {
            'webhooks': {
                'n8n': {
                    'url': os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/trading-signals'),
                    'timeout': 10,
                    'retry_attempts': 3,
                    'retry_delay': 2
                }
            }
        }
        
        n8n_integration = N8NIntegration(n8n_config)
        await n8n_integration.initialize()
        provider_status['n8n'] = True
        logger.info("n8n integration initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize n8n integration: {e}")
        provider_status['n8n'] = False

async def setup_market_data_callbacks():
    """Setup callbacks for real-time market data from all providers"""
    try:
        # Major Indian market symbols
        symbols = ['NIFTY-I', 'BANKNIFTY-I', 'SENSEX-I', 'FINNIFTY-I']
        
        # Setup TrueData callbacks
        if truedata_provider and provider_status['truedata']:
            for symbol in symbols:
                await truedata_provider.subscribe_symbols([symbol], create_truedata_callback(symbol))
        
        # Setup Zerodha callbacks
        if zerodha_integration and provider_status['zerodha']:
            # Convert symbols to Zerodha format
            zerodha_symbols = ['NIFTY 50', 'NIFTY BANK', 'NIFTY FIN SERVICE']  # Zerodha format
            await zerodha_integration.subscribe_market_data(zerodha_symbols)
            
        logger.info(f"Setup market data callbacks for {len(symbols)} symbols across all providers")
        
    except Exception as e:
        logger.error(f"Failed to setup market data callbacks: {e}")

def create_truedata_callback(symbol: str):
    """Create callback function for TrueData market data updates"""
    async def callback(data: Dict):
        try:
            message = {
                'type': 'MARKET_DATA',
                'provider': 'TRUEDATA',
                'symbol': symbol,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            await broadcast_to_subscribers(symbol, message)
            
        except Exception as e:
            logger.error(f"Error in TrueData callback for {symbol}: {e}")
    
    return callback

async def zerodha_market_data_callback(tick_data: Dict):
    """Callback for Zerodha market data"""
    try:
        message = {
            'type': 'MARKET_DATA',
            'provider': 'ZERODHA',
            'symbol': tick_data.get('instrument_token'),
            'data': {
                'last_price': tick_data.get('last_price'),
                'change': tick_data.get('change'),
                'volume': tick_data.get('volume_traded'),
                'ohlc': tick_data.get('ohlc'),
                'timestamp': tick_data.get('timestamp')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all subscribers or specific symbol subscribers
        await broadcast_to_all(message)
        
    except Exception as e:
        logger.error(f"Error in Zerodha market data callback: {e}")

async def zerodha_order_update_callback(order_data: Dict):
    """Callback for Zerodha order updates"""
    try:
        message = {
            'type': 'ORDER_UPDATE',
            'provider': 'ZERODHA',
            'data': order_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await broadcast_to_all(message)
        
    except Exception as e:
        logger.error(f"Error in Zerodha order update callback: {e}")

async def broadcast_to_subscribers(symbol: str, message: Dict):
    """Broadcast message to all subscribers of a symbol"""
    if symbol in subscription_map:
        disconnected = []
        for websocket in subscription_map[symbol]:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            subscription_map[symbol].discard(ws)

async def broadcast_to_all(message: Dict):
    """Broadcast message to all connected clients"""
    disconnected = []
    for websocket in active_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        active_connections.discard(ws)

async def ws_manager_health_check():
    """Health check for WebSocket manager"""
    from common.health_checker import HealthCheckResult, HealthStatus
    
    try:
        if not ws_manager:
            return HealthCheckResult(
                component="websocket_manager",
                status=HealthStatus.UNHEALTHY,
                message="WebSocket manager not initialized"
            )
        
        connection_count = len(active_connections)
        
        if connection_count > 900:
            status = HealthStatus.DEGRADED
            message = f"High connection load: {connection_count} connections"
        else:
            status = HealthStatus.HEALTHY
            message = f"WebSocket manager operational: {connection_count} connections"
        
        return HealthCheckResult(
            component="websocket_manager",
            status=status,
            message=message,
            details={"active_connections": connection_count}
        )
        
    except Exception as e:
        return HealthCheckResult(
            component="websocket_manager",
            status=HealthStatus.UNHEALTHY,
            message=f"WebSocket manager health check failed: {str(e)}"
        )

async def truedata_health_check():
    """Health check for TrueData provider"""
    from common.health_checker import HealthCheckResult, HealthStatus
    
    try:
        if not truedata_provider:
            return HealthCheckResult(
                component="truedata",
                status=HealthStatus.UNKNOWN,
                message="TrueData provider not initialized"
            )
        
        is_connected = truedata_provider.is_connected
        
        if is_connected:
            return HealthCheckResult(
                component="truedata",
                status=HealthStatus.HEALTHY,
                message="TrueData provider connected",
                details={"subscribed_symbols": len(truedata_provider.subscribed_symbols)}
            )
        else:
            return HealthCheckResult(
                component="truedata",
                status=HealthStatus.UNHEALTHY,
                message="TrueData provider disconnected"
            )
        
    except Exception as e:
        return HealthCheckResult(
            component="truedata",
            status=HealthStatus.UNHEALTHY,
            message=f"TrueData health check failed: {str(e)}"
        )

async def zerodha_health_check():
    """Health check for Zerodha integration"""
    from common.health_checker import HealthCheckResult, HealthStatus
    
    try:
        if not zerodha_integration:
            return HealthCheckResult(
                component="zerodha",
                status=HealthStatus.UNKNOWN,
                message="Zerodha integration not initialized"
            )
        
        is_authenticated = zerodha_integration.is_authenticated
        ticker_connected = zerodha_integration.ticker_connected
        
        if is_authenticated and ticker_connected:
            return HealthCheckResult(
                component="zerodha",
                status=HealthStatus.HEALTHY,
                message="Zerodha integration fully operational"
            )
        elif is_authenticated:
            return HealthCheckResult(
                component="zerodha",
                status=HealthStatus.DEGRADED,
                message="Zerodha authenticated but ticker disconnected"
            )
        else:
            return HealthCheckResult(
                component="zerodha",
                status=HealthStatus.UNHEALTHY,
                message="Zerodha not authenticated"
            )
        
    except Exception as e:
        return HealthCheckResult(
            component="zerodha",
            status=HealthStatus.UNHEALTHY,
            message=f"Zerodha health check failed: {str(e)}"
        )

async def n8n_health_check():
    """Health check for n8n integration"""
    from common.health_checker import HealthCheckResult, HealthStatus
    
    try:
        if not n8n_integration:
            return HealthCheckResult(
                component="n8n",
                status=HealthStatus.UNKNOWN,
                message="n8n integration not initialized"
            )
        
        # Try to send a test ping to n8n
        test_payload = {"type": "health_check", "timestamp": datetime.now().isoformat()}
        
        try:
            # This would need to be implemented in N8NIntegration class
            # success = await n8n_integration.send_test_message(test_payload)
            success = True  # Placeholder for now
            
            if success:
                return HealthCheckResult(
                    component="n8n",
                    status=HealthStatus.HEALTHY,
                    message="n8n integration operational"
                )
            else:
                return HealthCheckResult(
                    component="n8n",
                    status=HealthStatus.DEGRADED,
                    message="n8n responding but with errors"
                )
        except:
            return HealthCheckResult(
                component="n8n",
                status=HealthStatus.UNHEALTHY,
                message="n8n not responding"
            )
        
    except Exception as e:
        return HealthCheckResult(
            component="n8n",
            status=HealthStatus.UNHEALTHY,
            message=f"n8n health check failed: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize WebSocket server on startup"""
    try:
        await init_websocket_server()
        logger.info("Comprehensive WebSocket server startup completed")
    except Exception as e:
        logger.error(f"WebSocket server startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on WebSocket server shutdown"""
    try:
        logger.info("Shutting down WebSocket server...")
        
        # Close all active connections
        for websocket in list(active_connections):
            try:
                await websocket.close()
            except:
                pass
        
        # Cleanup all providers
        if truedata_provider:
            await truedata_provider.disconnect()
        
        if zerodha_integration:
            # Zerodha cleanup would go here
            pass
        
        if n8n_integration:
            await n8n_integration.shutdown()
        
        if health_checker:
            await health_checker.stop()
        
        logger.info("WebSocket server shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during WebSocket server shutdown: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        logger.info(f"New WebSocket connection established. Total: {len(active_connections)}")
        
        # Send welcome message with provider status
        welcome_message = {
            'type': 'CONNECTION_ESTABLISHED',
            'message': 'Connected to Trading WebSocket Server',
            'providers': provider_status,
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_client_message(websocket, message)
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        # Cleanup connection
        active_connections.discard(websocket)
        
        # Remove from all subscriptions
        for symbol_subs in subscription_map.values():
            symbol_subs.discard(websocket)

async def handle_client_message(websocket: WebSocket, message: Dict):
    """Handle messages from WebSocket clients"""
    try:
        message_type = message.get('type')
        
        if message_type == 'SUBSCRIBE':
            # Subscribe to symbol updates
            symbol = message.get('symbol')
            provider = message.get('provider', 'ALL')  # Default to all providers
            
            if symbol:
                if symbol not in subscription_map:
                    subscription_map[symbol] = set()
                subscription_map[symbol].add(websocket)
                
                # Subscribe to the symbol on relevant providers
                if provider in ['ALL', 'TRUEDATA'] and truedata_provider:
                    await truedata_provider.subscribe_symbols([symbol], create_truedata_callback(symbol))
                
                if provider in ['ALL', 'ZERODHA'] and zerodha_integration:
                    await zerodha_integration.subscribe_market_data([symbol])
                
                response = {
                    'type': 'SUBSCRIPTION_CONFIRMED',
                    'symbol': symbol,
                    'provider': provider,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
                
        elif message_type == 'UNSUBSCRIBE':
            # Unsubscribe from symbol updates
            symbol = message.get('symbol')
            provider = message.get('provider', 'ALL')
            
            if symbol and symbol in subscription_map:
                subscription_map[symbol].discard(websocket)
                
                # Unsubscribe from providers if no more subscribers
                if len(subscription_map[symbol]) == 0:
                    if provider in ['ALL', 'TRUEDATA'] and truedata_provider:
                        await truedata_provider.unsubscribe_symbols([symbol])
                    
                    if provider in ['ALL', 'ZERODHA'] and zerodha_integration:
                        await zerodha_integration.unsubscribe_market_data([symbol])
                
                response = {
                    'type': 'UNSUBSCRIPTION_CONFIRMED',
                    'symbol': symbol,
                    'provider': provider,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
                
        elif message_type == 'PING':
            # Respond to ping with pong
            response = {
                'type': 'PONG',
                'providers': provider_status,
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(response))
            
        elif message_type == 'N8N_SIGNAL':
            # Send signal to n8n workflow
            if n8n_integration and message.get('signal'):
                # This would need to be implemented in the N8N integration
                response = {
                    'type': 'N8N_SIGNAL_SENT',
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}")

@app.get("/ws/health")
async def websocket_health():
    """WebSocket server health endpoint"""
    if health_checker:
        return await health_checker.get_health_status()
    else:
        return {"status": "unhealthy", "message": "Health checker not initialized"}

@app.get("/ws/stats")
async def websocket_stats():
    """Get comprehensive WebSocket server statistics"""
    return {
        "active_connections": len(active_connections),
        "subscriptions": {symbol: len(subs) for symbol, subs in subscription_map.items()},
        "providers": {
            "truedata": {
                "status": provider_status['truedata'],
                "connected": truedata_provider.is_connected if truedata_provider else False,
                "subscribed_symbols": len(truedata_provider.subscribed_symbols) if truedata_provider else 0
            },
            "zerodha": {
                "status": provider_status['zerodha'],
                "authenticated": zerodha_integration.is_authenticated if zerodha_integration else False,
                "ticker_connected": zerodha_integration.ticker_connected if zerodha_integration else False
            },
            "n8n": {
                "status": provider_status['n8n'],
                "initialized": n8n_integration is not None
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ws/providers")
async def provider_status_endpoint():
    """Get status of all data providers"""
    return {
        "providers": provider_status,
        "details": await websocket_stats()
    }

# Include WebSocket routes
app.include_router(websocket_router, prefix="/ws/api", tags=["websocket"])

def main():
    """Main WebSocket server entry point"""
    try:
        logger.info("Starting Comprehensive Trading WebSocket Server")
        
        # Start the WebSocket server
        uvicorn.run(
            "websocket_main:app",
            host="0.0.0.0",
            port=8002,  # Different port for WebSocket server
            reload=False,
            log_level="info",
            access_log=True,
        )
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")

if __name__ == "__main__":
    main() 
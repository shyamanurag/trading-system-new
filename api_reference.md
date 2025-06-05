# F&O Scalping System v2.0 - API Reference

## Overview

The F&O Scalping System provides a RESTful API for controlling the trading system, monitoring performance, and accessing trading data. All API endpoints require authentication using JWT tokens.

## Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8080/api
```

## Authentication

All API requests (except `/api/auth/login` and `/health`) require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Login

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "1",
    "username": "your-username",
    "capital": 500000,
    "is_active": true
  }
}
```

## Endpoints

### System Health

#### Health Check
```http
GET /health
```

Check system health and component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "orchestrator": true,
    "position_tracker": true,
    "order_queue": true,
    "error_handler": true
  },
  "system_health": {
    "emergency_stop": false,
    "health_score": 95.0,
    "circuit_breakers": {
      "broker_api": "closed",
      "data_provider": "closed"
    }
  }
}
```

### Dashboard

#### Get Dashboard Metrics
```http
GET /api/dashboard/metrics
```

Retrieve real-time dashboard metrics including P&L, positions, and strategy performance.

**Response:**
```json
{
  "pnl": {
    "realized_pnl": 5000,
    "unrealized_pnl": 1500,
    "total_pnl": 6500,
    "pnl_percent": 1.3,
    "daily_pnl": 6500,
    "open_positions": 3,
    "total_trades": 25,
    "winners": 18,
    "losers": 7,
    "win_rate": 72.0
  },
  "risk": {
    "max_drawdown": 0.8,
    "current_exposure": 150000,
    "exposure_percent": 30.0,
    "potential_loss": 3000,
    "capital_at_risk": 150000
  },
  "orders": {
    "pending_orders": 2,
    "active_orders": 1,
    "current_rate": 3.5,
    "fill_rate": 95.0
  },
  "strategies": {
    "MomentumSurfer": {
      "total_trades": 8,
      "total_pnl": 2500,
      "average_pnl": 312.5,
      "pnl_percent": 0.5
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Positions

#### Get Positions
```http
GET /api/positions?status=open&strategy=MomentumSurfer
```

Retrieve positions with optional filtering.

**Query Parameters:**
- `status` (optional): `open` or `closed`
- `strategy` (optional): Filter by strategy name

**Response:**
```json
{
  "positions": [
    {
      "position_id": "pos_123",
      "symbol": "NIFTY19500CE",
      "strike": 19500,
      "option_type": "CE",
      "quantity": 100,
      "entry_price": 150.0,
      "current_price": 165.0,
      "status": "open",
      "strategy_name": "MomentumSurfer",
      "unrealized_pnl": 1500,
      "pnl_percent": 10.0
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get Specific Position
```http
GET /api/positions/{position_id}
```

**Response:**
```json
{
  "position_id": "pos_123",
  "symbol": "NIFTY19500CE",
  "strike": 19500,
  "option_type": "CE",
  "quantity": 100,
  "entry_price": 150.0,
  "entry_time": "2024-01-15T09:30:00Z",
  "current_price": 165.0,
  "status": "open",
  "strategy_name": "MomentumSurfer",
  "stop_loss": 140.0,
  "target": 180.0,
  "unrealized_pnl": 1500,
  "pnl_percent": 10.0
}
```

#### Close Position
```http
POST /api/positions/{position_id}/close
```

**Request Body:**
```json
{
  "exit_price": 165.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Position closed successfully"
}
```

### Orders

#### Get Orders
```http
GET /api/orders?type=active
```

**Query Parameters:**
- `type`: `active` or `completed`

**Response:**
```json
{
  "orders": [
    {
      "order_id": "ord_456",
      "symbol": "NIFTY19500CE",
      "quantity": 100,
      "order_type": "LIMIT",
      "side": "BUY",
      "price": 150.0,
      "status": "sent",
      "strategy_name": "MomentumSurfer",
      "created_time": "2024-01-15T10:25:00Z"
    }
  ],
  "count": 1,
  "queue_status": {
    "pending_orders": 2,
    "current_rate": 3.5,
    "max_rate": 7
  }
}
```

#### Create Manual Order
```http
POST /api/orders
```

**Request Body:**
```json
{
  "symbol": "NIFTY19500CE",
  "quantity": 100,
  "order_type": "LIMIT",
  "side": "BUY",
  "price": 150.0,
  "position_id": "pos_123"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "ord_789",
  "message": "Order queued successfully"
}
```

### Strategies

#### Get Strategy Status
```http
GET /api/strategies
```

**Response:**
```json
{
  "strategies": [
    {
      "name": "MomentumSurfer",
      "enabled": true,
      "allocation": 25.0,
      "signals_generated": 50,
      "signals_executed": 8,
      "success_rate": 75.0
    },
    {
      "name": "VolatilityExplosion",
      "enabled": true,
      "allocation": 30.0,
      "signals_generated": 30,
      "signals_executed": 10,
      "success_rate": 80.0
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Toggle Strategy
```http
POST /api/strategies/{strategy_name}/toggle
```

**Request Body:**
```json
{
  "enabled": false
}
```

**Response:**
```json
{
  "success": true,
  "strategy": "MomentumSurfer",
  "enabled": false
}
```

### System Control

#### Emergency Stop
```http
POST /api/control/emergency-stop
```

⚠️ **WARNING**: This will immediately close all positions and stop all trading activities.

**Response:**
```json
{
  "success": true,
  "message": "Emergency stop executed",
  "results": {
    "orchestrator": "stopped",
    "orders_cancelled": 5,
    "positions_closed": 3
  }
}
```

#### Pause Trading
```http
POST /api/control/pause
```

Pause new trade generation while keeping existing positions.

**Response:**
```json
{
  "success": true,
  "message": "Trading paused"
}
```

#### Resume Trading
```http
POST /api/control/resume
```

**Response:**
```json
{
  "success": true,
  "message": "Trading resumed"
}
```

### Reports

#### Get Daily Report
```http
GET /api/reports/daily?date=2024-01-15
```

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format (defaults to today)

**Response:**
```json
{
  "date": "2024-01-15",
  "pnl": {
    "realized_pnl": 5000,
    "total_trades": 25,
    "win_rate": 72.0
  },
  "trades": 25,
  "strategy_performance": {
    "MomentumSurfer": {
      "trades": 8,
      "pnl": 2500
    }
  },
  "risk_metrics": {
    "max_drawdown": 0.8,
    "avg_position_size": 75000
  }
}
```

#### Export Report
```http
POST /api/reports/export
```

**Request Body:**
```json
{
  "type": "positions",
  "format": "json"
}
```

**Response:**
```json
{
  "success": true,
  "filename": "positions_20240115_103000.json",
  "message": "Export completed"
}
```

### WebSocket

#### Get WebSocket Info
```http
GET /api/websocket/info
```

**Response:**
```json
{
  "url": "ws://localhost:8080/ws",
  "protocols": ["market_data", "order_updates", "position_updates"],
  "heartbeat_interval": 30
}
```

## WebSocket API

Connect to the WebSocket endpoint for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

// Subscribe to channels
ws.send(JSON.stringify({
  action: 'subscribe',
  channels: ['positions', 'orders', 'market_data']
}));

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'position_update':
      // Handle position update
      break;
    case 'order_update':
      // Handle order update
      break;
    case 'market_tick':
      // Handle market data
      break;
  }
};
```

## Rate Limits

- Authentication: 5 requests per minute
- Order creation: 10 requests per minute
- Emergency stop: 1 request per minute
- Export: 5 requests per hour
- All other endpoints: 1000 requests per hour, 100 per minute

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "message": "Detailed error message"
}
```

### Common Error Codes

- `400` - Bad Request: Invalid parameters
- `401` - Unauthorized: Missing or invalid token
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server error
- `503` - Service Unavailable: Component not available

## SDK Examples

### Python
```python
import requests

class TradingAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get_positions(self, status='open'):
        response = requests.get(
            f'{self.base_url}/api/positions',
            params={'status': status},
            headers=self.headers
        )
        return response.json()
    
    def close_position(self, position_id, exit_price):
        response = requests.post(
            f'{self.base_url}/api/positions/{position_id}/close',
            json={'exit_price': exit_price},
            headers=self.headers
        )
        return response.json()
```

### JavaScript
```javascript
class TradingAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }
  
  async getPositions(status = 'open') {
    const response = await fetch(
      `${this.baseUrl}/api/positions?status=${status}`,
      { headers: this.headers }
    );
    return response.json();
  }
  
  async closePosition(positionId, exitPrice) {
    const response = await fetch(
      `${this.baseUrl}/api/positions/${positionId}/close`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ exit_price: exitPrice })
      }
    );
    return response.json();
  }
}
```

## Best Practices

1. **Always handle errors** - Check response status and handle errors gracefully
2. **Respect rate limits** - Implement exponential backoff for retries
3. **Use WebSocket for real-time data** - Don't poll REST endpoints for updates
4. **Cache static data** - Strategy configurations don't change often
5. **Batch operations when possible** - Reduce API calls by batching requests

## Support

For API support or to report issues:
- GitHub Issues: https://github.com/yourusername/fo-scalping-system/issues
- Email: api-support@yourdomain.com
- Documentation: https://docs.yourdomain.com
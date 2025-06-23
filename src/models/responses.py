"""
Response Models for API endpoints
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response model"""
    success: bool
    message: str
    version: str = "4.0.1"
    components: Dict[str, Any] = {}
    uptime: str = "0s"
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    active_connections: int = 0
    last_backup: Optional[str] = None
    timestamp: Optional[str] = None

class StatusResponse(BaseModel):
    """Generic status response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: Optional[str] = None

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseResponse):
    """Paginated response with metadata"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class TradeResponse(BaseResponse):
    """Trade execution response"""
    trade_id: str
    symbol: str
    quantity: float
    price: float
    side: str
    status: str
    execution_time: datetime
    fees: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class PositionResponse(BaseResponse):
    """Position response"""
    data: Optional[List[Dict[str, Any]]] = None

class MarketDataResponse(BaseResponse):
    """Market data response"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_trade: Optional[Dict[str, Any]] = None
    indicators: Optional[Dict[str, Any]] = None

class WebhookResponse(BaseResponse):
    """Webhook processing response"""
    webhook_id: str
    source: str
    event_type: str
    processed_at: datetime
    status: str
    metadata: Optional[Dict[str, Any]] = None

class UserResponse(BaseResponse):
    """User operation response"""
    user_id: str
    username: str
    email: str
    role: str
    status: str
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

class RiskResponse(BaseResponse):
    """Risk management response"""
    risk_level: str
    exposure: float
    limits: Dict[str, float]
    warnings: List[str]
    actions_taken: List[str]
    metadata: Optional[Dict[str, Any]] = None

class TradingStatusResponse(BaseResponse):
    """Trading status response"""
    pass

class PerformanceMetricsResponse(BaseResponse):
    """Performance metrics response"""
    pass

class StrategyResponse(BaseResponse):
    """Strategy response"""
    pass

class RiskMetricsResponse(BaseResponse):
    """Risk metrics response"""
    pass 
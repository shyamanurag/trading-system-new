"""
SQLAlchemy models for trading system data storage.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, JSON, ForeignKey, Index, DECIMAL, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config.database import Base

class User(Base):
    """User accounts and authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    initial_capital = Column(DECIMAL(15,2), default=50000)
    current_balance = Column(DECIMAL(15,2), default=50000)
    risk_tolerance = Column(String(20), default='medium')
    is_active = Column(Boolean, default=True)
    zerodha_client_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    positions = relationship("Position", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    orders = relationship("Order", back_populates="user")
    metrics = relationship("UserMetric", back_populates="user")
    risk_metrics = relationship("RiskMetric", back_populates="user")

class Portfolio(Base):
    """User portfolios and holdings"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    initial_balance = Column(DECIMAL(15, 2), nullable=False)
    current_balance = Column(DECIMAL(15, 2), nullable=False)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")

class Stock(Base):
    """Stock/Symbol master data"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    company_name = Column(String(200))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    market_data = relationship("MarketData", back_populates="stock")
    positions = relationship("Position", back_populates="stock")
    trades = relationship("Trade", back_populates="stock")
    recommendations = relationship("Recommendation", back_populates="stock")

class MarketData(Base):
    """Historical and real-time market data"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(DECIMAL(10, 4))
    high_price = Column(DECIMAL(10, 4))
    low_price = Column(DECIMAL(10, 4))
    close_price = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(10, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="market_data")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_market_data_stock_timestamp', 'stock_id', 'timestamp'),
    )

class Position(Base):
    """Trading positions"""
    __tablename__ = "positions"
    
    position_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(DECIMAL(10,2), nullable=False)
    current_price = Column(DECIMAL(10,2))
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True))
    strategy = Column(String(50))
    status = Column(String(20), default='open')
    unrealized_pnl = Column(DECIMAL(12,2))
    realized_pnl = Column(DECIMAL(12,2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="positions")
    trades = relationship("Trade", back_populates="position")

class Trade(Base):
    """Trading transactions"""
    __tablename__ = "trades"
    
    trade_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.position_id"))
    symbol = Column(String(20), nullable=False)
    trade_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10,2), nullable=False)
    order_id = Column(String(50))
    strategy = Column(String(50))
    commission = Column(DECIMAL(8,2), default=0)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    position = relationship("Position", back_populates="trades")

class Order(Base):
    """Trading orders"""
    __tablename__ = "orders"
    
    order_id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    broker_order_id = Column(String(100))
    parent_order_id = Column(String(50))
    symbol = Column(String(20), nullable=False)
    order_type = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10,2))
    stop_price = Column(DECIMAL(10,2))
    filled_quantity = Column(Integer, default=0)
    average_price = Column(DECIMAL(10,2))
    status = Column(String(20), default='PENDING')
    execution_strategy = Column(String(30))
    time_in_force = Column(String(10), default='DAY')
    strategy_name = Column(String(50))
    signal_id = Column(String(50))
    fees = Column(DECIMAL(8,2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    placed_at = Column(DateTime(timezone=True))
    filled_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")

class UserMetric(Base):
    """User performance metrics"""
    __tablename__ = "user_metrics"
    
    metric_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(12,2), default=0)
    win_rate = Column(DECIMAL(5,2))
    avg_win = Column(DECIMAL(10,2))
    avg_loss = Column(DECIMAL(10,2))
    sharpe_ratio = Column(DECIMAL(5,2))
    max_drawdown = Column(DECIMAL(10,2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="metrics")

class RiskMetric(Base):
    """Risk metrics"""
    __tablename__ = "risk_metrics"
    
    metric_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    portfolio_value = Column(DECIMAL(15,2))
    var_95 = Column(DECIMAL(10,2))  # Value at Risk 95%
    exposure = Column(DECIMAL(10,2))
    leverage = Column(DECIMAL(5,2))
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    alerts = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="risk_metrics")

class Recommendation(Base):
    """AI-generated trading recommendations"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    recommendation_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence_score = Column(Float, nullable=False)
    target_price = Column(DECIMAL(10, 4))
    stop_loss = Column(DECIMAL(10, 4))
    analysis = Column(Text)
    algorithm_version = Column(String(20))
    factors = Column(JSON)  # Store analysis factors as JSON
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="recommendations")
    
    # Indexes
    __table_args__ = (
        Index('ix_recommendations_stock_active', 'stock_id', 'is_active'),
    )

class RiskMetrics(Base):
    """Portfolio risk analysis data"""
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    var_1d = Column(DECIMAL(15, 2))  # Value at Risk 1 day
    var_5d = Column(DECIMAL(15, 2))  # Value at Risk 5 days
    max_drawdown = Column(DECIMAL(5, 4))  # Maximum drawdown percentage
    sharpe_ratio = Column(DECIMAL(8, 4))
    beta = Column(DECIMAL(8, 4))
    volatility = Column(DECIMAL(8, 4))
    risk_score = Column(Integer)  # 1-10 scale
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

class TradingSession(Base):
    """Trading session tracking"""
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True))
    trades_count = Column(Integer, default=0)
    total_volume = Column(DECIMAL(15, 2), default=0)
    pnl = Column(DECIMAL(15, 2), default=0)
    status = Column(String(20), default='ACTIVE')  # ACTIVE, CLOSED 
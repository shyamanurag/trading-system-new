"""
Configuration settings for the trading system
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True)
    
    # API Settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)
    
    # Database Settings - Check for DigitalOcean DATABASE_URL first
    DATABASE_URL: Optional[str] = Field(default=None, alias='DATABASE_URL')
    DB_HOST: str = Field(default="localhost", alias='DB_HOST')
    DB_PORT: int = Field(default=5432, alias='DB_PORT')
    DB_NAME: str = Field(default="trading", alias='DB_NAME')
    DB_USER: str = Field(default="postgres", alias='DB_USER')
    DB_PASSWORD: str = Field(default="", alias='DB_PASSWORD')
    DB_SSL_MODE: str = Field(default="disable", alias='DB_SSL_MODE')
    DATABASE_SSL: str = Field(default="disable", alias='DATABASE_SSL')
    
    @property
    def database_url(self) -> str:
        """Get the database URL with proper configuration"""
        # If DigitalOcean provides DATABASE_URL, use it but ensure proper SSL handling
        if self.DATABASE_URL:
            # For SQLAlchemy, we need to remove sslmode from the URL and handle it via connect_args
            url = self.DATABASE_URL
            if '?sslmode=' in url:
                # Remove sslmode parameter from URL
                base_url = url.split('?sslmode=')[0]
                return base_url
            return url
        
        # Otherwise, construct from individual settings
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        """Get connection arguments for SQLAlchemy"""
        connect_args = {}
        
        # If using DigitalOcean DATABASE_URL or SSL is required
        if self.DATABASE_URL or self.DATABASE_SSL == 'require':
            connect_args['sslmode'] = 'require'
            
        # DigitalOcean managed databases always require SSL
        if self.DATABASE_URL and 'ondigitalocean.com' in self.DATABASE_URL:
            connect_args['sslmode'] = 'require'
            
        return connect_args
    
    # Redis Settings - Check for DigitalOcean REDIS_URL first
    REDIS_URL: Optional[str] = Field(default=None, alias='REDIS_URL')
    REDIS_HOST: str = Field(default="localhost", alias='REDIS_HOST')
    REDIS_PORT: int = Field(default=6379, alias='REDIS_PORT')
    REDIS_DB: int = Field(default=0, alias='REDIS_DB')
    REDIS_PASSWORD: Optional[str] = Field(default=None, alias='REDIS_PASSWORD')
    REDIS_SSL: bool = Field(default=False, alias='REDIS_SSL')
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL with proper SSL configuration"""
        # If DigitalOcean provides REDIS_URL, use it directly
        if self.REDIS_URL:
            return self.REDIS_URL
        
        # Otherwise, construct from individual settings
        protocol = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Trading Settings
    DEFAULT_TIMEFRAME: str = Field(default="1h")
    DEFAULT_SYMBOLS: List[str] = Field(default=["BTC/USD", "ETH/USD"])
    MAX_POSITION_SIZE: float = Field(default=1.0)
    RISK_PER_TRADE: float = Field(default=0.02)
    
    # Backtesting Settings
    BACKTEST_START_DATE: str = Field(default="2023-01-01")
    BACKTEST_END_DATE: str = Field(default="2023-12-31")
    INITIAL_CAPITAL: float = Field(default=100000.0)
    
    # Monitoring Settings
    METRICS_INTERVAL: int = Field(default=60)  # seconds
    
    # File Paths
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent)
    DATA_DIR: Path = Field(default=Path(__file__).parent.parent.parent / "data")
    LOGS_DIR: Path = Field(default=Path(__file__).parent.parent.parent / "logs")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Zerodha
    ZERODHA_API_KEY: Optional[str] = Field(None, description="Zerodha API key")
    ZERODHA_API_SECRET: Optional[str] = Field(None, description="Zerodha API secret")
    ZERODHA_USER_ID: Optional[str] = Field(None, description="Zerodha user ID")
    
    # TrueData
    TRUEDATA_USERNAME: Optional[str] = Field(None, description="TrueData username")
    TRUEDATA_PASSWORD: Optional[str] = Field(None, description="TrueData password")
    TRUEDATA_LIVE_PORT: int = Field(8084, description="TrueData live port")
    TRUEDATA_IS_SANDBOX: bool = Field(False, description="TrueData sandbox mode")
    
    # Orchestrator
    ORCHESTRATOR_CONFIG: dict = Field(
        default={
            "max_positions": 5,
            "max_risk_per_trade": 0.02,  # 2% per trade
            "max_daily_loss": 0.05,      # 5% daily loss limit
            "default_timeframe": "1m",
            "default_provider": "zerodha"
        },
        description="Trading orchestrator configuration"
    )
    
    # WebSocket
    WS_PING_INTERVAL: int = Field(30, description="WebSocket ping interval in seconds")
    WS_PING_TIMEOUT: int = Field(10, description="WebSocket ping timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create settings instance
settings = get_settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.LOGS_DIR.mkdir(exist_ok=True) 
"""
Trading System Exceptions
========================
Exception classes for the trading system
"""

class TradingSystemException(Exception):
    """Base exception for trading system"""
    pass

# Alias for compatibility
TradingSystemError = TradingSystemException

class OrderExecutionException(TradingSystemException):
    """Exception for order execution errors"""
    pass

class OrderError(TradingSystemException):
    """Exception for order errors"""
    pass

class RiskError(TradingSystemException):
    """Exception for risk management errors"""
    pass

class RiskManagementException(TradingSystemException):
    """Exception for risk management errors"""
    pass

class DataException(TradingSystemException):
    """Exception for data-related errors"""
    pass

class ConnectionException(TradingSystemException):
    """Exception for connection errors"""
    pass

class AuthenticationException(TradingSystemException):
    """Exception for authentication errors"""
    pass

class ValidationException(TradingSystemException):
    """Exception for validation errors"""
    pass

class ConfigurationException(TradingSystemException):
    """Exception for configuration errors"""
    pass

class MarketDataException(TradingSystemException):
    """Exception for market data errors"""
    pass

class BrokerException(TradingSystemException):
    """Exception for broker-related errors"""
    pass

class PositionException(TradingSystemException):
    """Exception for position management errors"""
    pass

class StrategyException(TradingSystemException):
    """Exception for strategy errors"""
    pass

class SystemException(TradingSystemException):
    """Exception for system-level errors"""
    pass 
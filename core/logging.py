"""
Logging configuration for the trading system
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data)

def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level
        max_bytes: Maximum size of each log file
        backup_count: Number of backup files to keep
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Create handlers
    handlers = []
    
    # Console handler with color
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler for all logs
    all_logs_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "trading.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    all_logs_handler.setLevel(log_level)
    all_logs_handler.setFormatter(StructuredLogFormatter())
    handlers.append(all_logs_handler)
    
    # File handler for errors
    error_logs_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "error.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_logs_handler.setLevel(logging.ERROR)
    error_logs_handler.setFormatter(StructuredLogFormatter())
    handlers.append(error_logs_handler)
    
    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
        
    # Set up specific loggers
    loggers = {
        "trading": logging.getLogger("trading"),
        "broker": logging.getLogger("broker"),
        "strategy": logging.getLogger("strategy"),
        "risk": logging.getLogger("risk"),
        "data": logging.getLogger("data"),
        "webhook": logging.getLogger("webhook")
    }
    
    for logger in loggers.values():
        logger.setLevel(log_level)
        logger.propagate = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra or {})
        
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the log message and add context"""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs

def create_logger_adapter(
    logger_name: str,
    context: Optional[Dict[str, Any]] = None
) -> LoggerAdapter:
    """
    Create a logger adapter with context
    
    Args:
        logger_name: Name of the logger
        context: Additional context to add to log messages
        
    Returns:
        LoggerAdapter: Logger adapter instance
    """
    logger = get_logger(logger_name)
    return LoggerAdapter(logger, context or {}) 
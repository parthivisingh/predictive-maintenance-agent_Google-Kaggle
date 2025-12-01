"""
Structured Logging Configuration
=================================

Provides JSON-formatted logs for all tools with:
- Request IDs for tracing
- Performance metrics
- Error context
- Business metrics
"""

import logging
import json
from pythonjsonlogger import jsonlogger
from datetime import datetime
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for request tracking
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with request ID and standardized fields."""

    def add_fields(self, log_record, record, message_dict):
        """Add standard fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_record['request_id'] = request_id

        # Add source location
        log_record['source'] = f"{record.filename}:{record.lineno}"

        # Add function name
        if record.funcName and record.funcName != '<module>':
            log_record['function'] = record.funcName


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = True
) -> logging.Logger:
    """
    Configure structured logging.

    Parameters:
    -----------
    log_level : int
        Logging level (default: INFO)
    log_file : str, optional
        Log file path (if None, logs to console only)
    json_format : bool
        Use JSON formatting (default: True)

    Returns:
    --------
    logging.Logger
        Configured root logger
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    if json_format:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Parameters:
    -----------
    name : str
        Logger name (typically __name__)

    Returns:
    --------
    logging.Logger
        Logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.

    Parameters:
    -----------
    request_id : str, optional
        Request ID to set (generates new UUID if None)

    Returns:
    --------
    str
        Request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> str:
    """
    Get current request ID from context.

    Returns:
    --------
    str
        Current request ID (empty string if not set)
    """
    return request_id_ctx.get()


def clear_request_id() -> None:
    """Clear request ID from context."""
    request_id_ctx.set('')


class LogContext:
    """
    Context manager for structured logging with request tracking.

    Usage:
    ------
    with LogContext("analyze_sensors") as ctx:
        ctx.log_info("Processing sensor data", sensor_count=10)
        # ... do work ...
        ctx.log_success("Analysis complete", anomaly_detected=True)
    """

    def __init__(
        self,
        operation: str,
        logger: Optional[logging.Logger] = None,
        request_id: Optional[str] = None,
        **context_data
    ):
        """
        Initialize log context.

        Parameters:
        -----------
        operation : str
            Operation name
        logger : logging.Logger, optional
            Logger to use (creates new if None)
        request_id : str, optional
            Request ID (generates new if None)
        **context_data
            Additional context data to include in all logs
        """
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.request_id = request_id or str(uuid.uuid4())
        self.context_data = context_data
        self.start_time = None

    def __enter__(self):
        """Enter context."""
        # Set request ID
        set_request_id(self.request_id)

        # Record start time
        self.start_time = datetime.utcnow()

        # Log operation start
        self.log_info(
            f"{self.operation} started",
            operation=self.operation,
            **self.context_data
        )

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context."""
        # Calculate duration
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        if exc_type is None:
            # Success
            self.log_info(
                f"{self.operation} completed",
                operation=self.operation,
                duration_seconds=duration,
                status="success",
                **self.context_data
            )
        else:
            # Error
            self.log_error(
                f"{self.operation} failed",
                operation=self.operation,
                duration_seconds=duration,
                status="error",
                error_type=exc_type.__name__,
                error_message=str(exc_value),
                **self.context_data
            )

        # Clear request ID
        clear_request_id()

    def log_info(self, message: str, **extra):
        """Log info message with context."""
        self.logger.info(
            message,
            extra={
                'request_id': self.request_id,
                **self.context_data,
                **extra
            }
        )

    def log_warning(self, message: str, **extra):
        """Log warning message with context."""
        self.logger.warning(
            message,
            extra={
                'request_id': self.request_id,
                **self.context_data,
                **extra
            }
        )

    def log_error(self, message: str, **extra):
        """Log error message with context."""
        self.logger.error(
            message,
            extra={
                'request_id': self.request_id,
                **self.context_data,
                **extra
            }
        )

    def log_success(self, message: str, **extra):
        """Log success message with context."""
        self.log_info(message, status="success", **extra)


# Initialize logging on module import
_initialized = False

def initialize_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = True
):
    """
    Initialize logging configuration.

    This should be called once at application startup.

    Parameters:
    -----------
    log_level : int
        Logging level
    log_file : str, optional
        Log file path
    json_format : bool
        Use JSON formatting
    """
    global _initialized
    if not _initialized:
        setup_logging(log_level, log_file, json_format)
        _initialized = True


# Auto-initialize with defaults if not already initialized
if not _initialized:
    initialize_logging()

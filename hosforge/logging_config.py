"""
HOS-Forge Unified Logging Configuration — 统一日志配置。

提供标准化的日志格式、级别和工厂函数，确保所有模块使用一致的日志系统。

Usage:
    from hosforge.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.error("This is an error message", extra={"context": "some context"})

Log Level Guidelines:
    - DEBUG: Detailed information for debugging (development only)
    - INFO: Confirmation of normal operations (e.g., "Tool started", "Scan completed")
    - WARNING: Unexpected situations that don't stop execution (e.g., "Tool not found, skipping")
    - ERROR: Operation failures that don't stop the entire system (e.g., "Scan failed for target X")
    - CRITICAL: System-level failures that stop execution (e.g., "Database connection lost")
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# 统一日志格式
# 包含：时间戳 | 模块名 | 日志级别 | 消息
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

# 日期格式
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 默认日志级别
DEFAULT_LOG_LEVEL = logging.INFO

# 已配置的 logger 缓存
_configured_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """
    获取标准化的 logger 实例。

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logging.Logger: 配置好的 logger 实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation completed")
    """
    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(DEFAULT_LOG_LEVEL)
        logger.propagate = False

    _configured_loggers[name] = logger
    return logger


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_format: str = LOG_FORMAT,
    date_format: str = DATE_FORMAT,
) -> None:
    """
    全局配置日志系统。

    Args:
        level: 日志级别 (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式字符串
        date_format: 日期格式字符串

    Example:
        >>> configure_logging(level=logging.DEBUG)  # 启用调试日志
    """
    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除现有 handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加新的 handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(handler)

    # 更新所有已配置的 logger
    for logger in _configured_loggers.values():
        logger.setLevel(level)
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.addHandler(handler)


def set_log_level(level: int, module_prefix: str = "hosforge") -> None:
    """
    设置特定模块的日志级别。

    Args:
        level: 日志级别
        module_prefix: 模块前缀（默认 "hosforge"）

    Example:
        >>> set_log_level(logging.DEBUG, "hosforge.security_tools")  # 仅调试安全工具
    """
    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith(module_prefix):
            if isinstance(logger, logging.Logger):
                logger.setLevel(level)


class StructuredLogger:
    """
    结构化日志包装器，支持额外上下文字段。

    Example:
        >>> logger = StructuredLogger(get_logger(__name__))
        >>> logger.info("Scan completed", target="example.com", duration=5.2)
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _format_message(self, message: str, **kwargs: Any) -> str:
        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {context_str}"
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(self._format_message(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.exception(self._format_message(message, **kwargs))


def get_structured_logger(name: str) -> StructuredLogger:
    """
    获取结构化 logger，支持额外上下文字段。

    Args:
        name: logger 名称

    Returns:
        StructuredLogger: 结构化 logger 实例

    Example:
        >>> logger = get_structured_logger(__name__)
        >>> logger.info("Tool executed", tool="nmap", target="example.com", duration=3.5)
    """
    return StructuredLogger(get_logger(name))

"""
Logging configuration for ZombieCursor.
"""
import sys
from pathlib import Path
from loguru import logger
from core.config import settings


def setup_logging():
    """Set up logging configuration."""
    # Remove default logger
    logger.remove()
    
    # Console logger
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File logger
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # Error logger
    error_log_path = Path(settings.log_file).parent / "errors.log"
    logger.add(
        error_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("Logging system initialized")
    return logger


# Initialize logging
log = setup_logging()
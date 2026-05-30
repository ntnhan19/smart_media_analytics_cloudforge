"""
Logger configuration and utilities
Cấu hình logging cho toàn bộ project
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

# ── Setup logging directory ────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "ai_pipeline" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# ── Configure logger ───────────────────────────────────────────────────────────
logger = logging.getLogger("smart_media_analytics")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


# ── Logging utilities ──────────────────────────────────────────────────────────

def log_exception(e: Exception, context: str = "") -> None:
    """
    Log an exception with full traceback
    
    Args:
        e: The exception to log
        context: Additional context about where the error occurred
    """
    if context:
        logger.error(f"Exception in {context}: {str(e)}")
    else:
        logger.error(f"Exception: {str(e)}")
    logger.debug(traceback.format_exc())


def log_model_loading(model_name: str, status: str = "loading") -> None:
    """
    Log model loading status
    
    Args:
        model_name: Name of the model
        status: Status message (loading, loaded, failed, etc.)
    """
    logger.info(f"Model {model_name}: {status}")


class ProgressTracker:
    """
    Track and log progress of long-running tasks
    """
    
    def __init__(self, total: int, task_name: str = "Processing"):
        self.total = total
        self.task_name = task_name
        self.current = 0
    
    def update(self, amount: int = 1) -> None:
        """Update progress"""
        self.current += amount
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        logger.info(f"{self.task_name}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def log_step(self, step: str) -> None:
        """Log a processing step"""
        logger.info(f"{self.task_name}: {step}")

"""
Logger configuration and utilities
Cấu hình logging cho toàn bộ project - Phiên bản sạch Unicode
"""

import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional


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

    # File handler (log chi tiết hơn)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


# ── Helper methods (không dùng emoji) ────────────────────────────────────────
def section(title: str) -> None:
    """In dòng phân cách rõ ràng"""
    logger.info("\n" + "=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def success(msg: str) -> None:
    """Log thông báo thành công"""
    logger.info(f"[DONE] {msg}")


def warning(msg: str) -> None:
    """Log cảnh báo"""
    logger.warning(f"[WARN] {msg}")


# Gắn các helper vào logger để pipeline có thể gọi logger.section(), logger.success()
logger.section = section
logger.success = success
logger.warning = warning   # type: ignore[attr-defined]


# ── Utilities ────────────────────────────────────────────────────────────────
def log_exception(e: Exception, context: str = "") -> None:
    """Log exception với full traceback"""
    if context:
        logger.error(f"Exception in {context}: {str(e)}")
    else:
        logger.error(f"Exception: {str(e)}")
    logger.debug(traceback.format_exc())


def log_model_loading(model_name: str, status: str = "loading") -> None:
    """Log model loading status"""
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
        self.current += amount
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        logger.info(f"{self.task_name}: {self.current}/{self.total} ({percentage:.1f}%)")

    def log_step(self, step: str) -> None:
        logger.info(f"{self.task_name}: {step}")

    def step(self, msg: str) -> None:
        self.log_step(msg)
        self.update()

    def complete(self, msg: str = "") -> None:
        final = msg or f"{self.task_name} complete"
        logger.info(f"[DONE] {final}")


# Export
__all__ = ["logger", "log_exception", "log_model_loading", "ProgressTracker"]
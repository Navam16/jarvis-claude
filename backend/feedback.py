"""
Feedback / Logging Module for Jarvis HR Agent
Web deployment version - logs to console + file instead of colored terminal output
"""

import logging
import re
import time

logger = logging.getLogger(__name__)


def sanitize_log_message(message: str) -> str:
    """Mask phone-like patterns in log messages."""
    text = str(message)

    def _mask_phone(match):
        value = match.group(0)
        digits_only = re.sub(r"[^\d+]", "", value)
        if len(digits_only) <= 2:
            return "*" * len(value)
        num_mask_chars = len(digits_only) - 2
        masked_core = "*" * num_mask_chars + digits_only[-2:]
        if len(masked_core) < len(value):
            masked_core = masked_core.rjust(len(value), "*")
        return masked_core

    phone_pattern = re.compile(r"\+?\d(?:[\d\s-]{7,})")
    return phone_pattern.sub(_mask_phone, text)


class StatusIndicator:
    """Logs status messages using Python's logging module (web-safe, no terminal color)."""

    @staticmethod
    def listening(message="Listening..."):
        logger.info(f"[LISTENING] {sanitize_log_message(message)}")

    @staticmethod
    def processing(message="Processing..."):
        logger.info(f"[PROCESSING] {sanitize_log_message(message)}")

    @staticmethod
    def done(message="Done.", duration=None):
        if duration is not None:
            message = f"{message} (Completed in {duration:.2f}s)"
        logger.info(f"[DONE] {sanitize_log_message(message)}")

    @staticmethod
    def success(message):
        logger.info(f"[SUCCESS] {sanitize_log_message(message)}")

    @staticmethod
    def error(message):
        logger.error(f"[ERROR] {sanitize_log_message(message)}")

    @staticmethod
    def info(message):
        logger.info(f"[INFO] {sanitize_log_message(message)}")

    @staticmethod
    def warning(message):
        logger.warning(f"[WARNING] {sanitize_log_message(message)}")

    @staticmethod
    def command(message):
        logger.info(f"[COMMAND] {sanitize_log_message(message)}")

    @staticmethod
    def response(message):
        logger.info(f"[RESPONSE] {sanitize_log_message(message)}")


class Timer:
    """Context manager for timing operations."""

    def __init__(self, operation_name=None):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_type is None and self.operation_name:
            StatusIndicator.done(self.operation_name, self.elapsed())
        elif self.operation_name:
            StatusIndicator.error(f"{self.operation_name} failed")
        return False

    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

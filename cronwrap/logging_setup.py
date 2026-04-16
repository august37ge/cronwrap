import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    fmt: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
) -> None:
    """Configure root logger for cronwrap."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout)
    ]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(fmt))
        handlers.append(file_handler)

    logging.basicConfig(
        level=numeric_level,
        format=fmt,
        handlers=handlers,
    )

    logging.getLogger("cronwrap").setLevel(numeric_level)


def log_result(result) -> None:
    """Log a RunResult summary."""
    logger = logging.getLogger("cronwrap.runner")
    status = "SUCCESS" if result.success else "FAILURE"
    logger.info(
        "[%s] command=%r returncode=%d duration=%.2fs attempts=%d",
        status,
        result.command,
        result.returncode,
        result.duration,
        result.attempts,
    )
    if result.stdout.strip():
        logger.debug("stdout:\n%s", result.stdout.strip())
    if result.stderr.strip():
        logger.debug("stderr:\n%s", result.stderr.strip())

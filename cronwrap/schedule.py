"""Schedule validation and next-run calculation for cron expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from croniter import croniter
except ImportError:  # pragma: no cover
    croniter = None  # type: ignore


@dataclass
class ScheduleInfo:
    expression: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_valid: bool = True
    error: Optional[str] = None


def validate_expression(expression: str) -> ScheduleInfo:
    """Return a ScheduleInfo indicating whether *expression* is a valid cron string."""
    if croniter is None:
        return ScheduleInfo(expression=expression, error="croniter not installed")
    try:
        croniter.is_valid(expression)
        if not croniter.is_valid(expression):
            return ScheduleInfo(expression=expression, is_valid=False, error="Invalid cron expression")
        return ScheduleInfo(expression=expression, is_valid=True)
    except Exception as exc:  # noqa: BLE001
        return ScheduleInfo(expression=expression, is_valid=False, error=str(exc))


def next_run_time(expression: str, base: Optional[datetime] = None) -> Optional[datetime]:
    """Return the next scheduled datetime after *base* (defaults to now)."""
    if croniter is None:
        return None
    base = base or datetime.now()
    info = validate_expression(expression)
    if not info.is_valid:
        return None
    return croniter(expression, base).get_next(datetime)


def is_overdue(expression: str, last_run: datetime, threshold_multiplier: float = 1.5) -> bool:
    """Return True when the job appears overdue based on its schedule."""
    expected_next = next_run_time(expression, last_run)
    if expected_next is None:
        return False
    overdue_at = expected_next + (expected_next - last_run) * (threshold_multiplier - 1)
    return datetime.now() > overdue_at

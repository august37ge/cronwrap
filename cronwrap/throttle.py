"""Job throttling: skip execution if the job ran too recently."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwrap.history import get_recent_runs, JobRecord


@dataclass
class ThrottleResult:
    job_name: str
    allowed: bool
    last_run: Optional[datetime]
    min_interval_seconds: int
    seconds_remaining: float

    @property
    def message(self) -> str:
        if self.allowed:
            return f"{self.job_name}: allowed (no recent run within throttle window)"
        remaining = int(self.seconds_remaining)
        return (
            f"{self.job_name}: throttled — {remaining}s remaining "
            f"(min interval {self.min_interval_seconds}s)"
        )


def check_throttle(
    job_name: str,
    min_interval_seconds: int,
    db_path: str,
) -> ThrottleResult:
    """Return a ThrottleResult indicating whether the job may run.

    Args:
        job_name: Unique identifier for the job being checked.
        min_interval_seconds: Minimum number of seconds that must have elapsed
            since the last run before the job is allowed to execute again.
        db_path: Path to the SQLite database used to look up run history.

    Returns:
        A ThrottleResult with ``allowed=True`` if no run exists within the
        throttle window, or ``allowed=False`` along with the seconds remaining
        until the job may next execute.
    """
    records = get_recent_runs(job_name, limit=1, db_path=db_path)
    if not records:
        return ThrottleResult(
            job_name=job_name,
            allowed=True,
            last_run=None,
            min_interval_seconds=min_interval_seconds,
            seconds_remaining=0.0,
        )

    last: JobRecord = records[0]
    last_dt = datetime.fromisoformat(last.started_at).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    elapsed = (now - last_dt).total_seconds()
    remaining = min_interval_seconds - elapsed
    allowed = remaining <= 0

    return ThrottleResult(
        job_name=job_name,
        allowed=allowed,
        last_run=last_dt,
        min_interval_seconds=min_interval_seconds,
        seconds_remaining=max(0.0, remaining),
    )


def render_throttle_result(result: ThrottleResult) -> str:
    return result.message

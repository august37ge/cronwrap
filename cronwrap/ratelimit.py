"""Rate limiting: prevent a job from running more frequently than allowed."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from cronwrap.history import get_recent_runs, _connect


@dataclass
class RateLimitResult:
    job_name: str
    allowed: bool
    last_run: Optional[datetime]
    min_interval_seconds: int
    seconds_remaining: float


def check_rate_limit(db_path: str, job_name: str, min_interval_seconds: int) -> RateLimitResult:
    """Return whether the job is allowed to run given the minimum interval."""
    runs = get_recent_runs(db_path, job_name, limit=1)
    if not runs:
        return RateLimitResult(
            job_name=job_name,
            allowed=True,
            last_run=None,
            min_interval_seconds=min_interval_seconds,
            seconds_remaining=0.0,
        )

    last = runs[0]
    last_dt = datetime.fromisoformat(last.started_at)
    elapsed = (datetime.utcnow() - last_dt).total_seconds()
    remaining = max(0.0, min_interval_seconds - elapsed)
    allowed = remaining == 0.0

    return RateLimitResult(
        job_name=job_name,
        allowed=allowed,
        last_run=last_dt,
        min_interval_seconds=min_interval_seconds,
        seconds_remaining=remaining,
    )


def render_rate_limit_result(result: RateLimitResult) -> str:
    if result.allowed:
        return f"[{result.job_name}] allowed to run (last run: {result.last_run or 'never'})"
    return (
        f"[{result.job_name}] rate limited — "
        f"{result.seconds_remaining:.1f}s remaining "
        f"(min interval: {result.min_interval_seconds}s, last run: {result.last_run})"
    )

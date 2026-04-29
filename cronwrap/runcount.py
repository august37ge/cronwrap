"""Track and query the total number of runs for a job within a time window."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class RunCountResult:
    job_name: str
    window_seconds: int
    count: int
    limit: Optional[int]
    allowed: bool
    message: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def count_runs(
    db_path: str,
    job_name: str,
    window_seconds: int,
    limit: Optional[int] = None,
) -> RunCountResult:
    """Count successful + failed runs for *job_name* within the last *window_seconds*.

    If *limit* is given, the result is marked as blocked when count >= limit.
    """
    cutoff = (_now_utc() - timedelta(seconds=window_seconds)).isoformat()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM runs "
            "WHERE job_name = ? AND started_at >= ?",
            (job_name, cutoff),
        ).fetchone()
    count = row["cnt"] if row else 0

    if limit is None:
        allowed = True
        msg = f"{job_name}: {count} run(s) in the last {window_seconds}s (no limit set)"
    elif count >= limit:
        allowed = False
        msg = (
            f"{job_name}: {count}/{limit} run(s) in the last {window_seconds}s — limit reached"
        )
    else:
        allowed = True
        msg = f"{job_name}: {count}/{limit} run(s) in the last {window_seconds}s — allowed"

    return RunCountResult(
        job_name=job_name,
        window_seconds=window_seconds,
        count=count,
        limit=limit,
        allowed=allowed,
        message=msg,
    )


def render_runcount_result(result: RunCountResult) -> str:
    status = "OK" if result.allowed else "BLOCKED"
    return f"[{status}] {result.message}"

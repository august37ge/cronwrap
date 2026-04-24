"""Job run quota enforcement — limit how many times a job may run per time window."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


@dataclass
class QuotaResult:
    job_name: str
    allowed: bool
    used: int
    limit: int
    window_seconds: int
    message: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_quota_db(db_path: str) -> None:
    """Create the quota tracking table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quota_runs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name  TEXT NOT NULL,
                ran_at    TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_quota_job_ran ON quota_runs (job_name, ran_at)"
        )


def record_quota_run(db_path: str, job_name: str, ran_at: Optional[datetime] = None) -> None:
    """Record a quota run timestamp for *job_name*."""
    ts = (ran_at or datetime.now(timezone.utc)).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO quota_runs (job_name, ran_at) VALUES (?, ?)",
            (job_name, ts),
        )


def check_quota(
    db_path: str,
    job_name: str,
    limit: int,
    window_seconds: int,
) -> QuotaResult:
    """Return a QuotaResult indicating whether the job may run.

    Args:
        db_path: Path to the SQLite database.
        job_name: Identifier of the job.
        limit: Maximum number of runs allowed within *window_seconds*.
        window_seconds: Length of the rolling window in seconds.
    """
    since = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM quota_runs WHERE job_name = ? AND ran_at >= ?",
            (job_name, since),
        ).fetchone()
    used = row["cnt"] if row else 0
    allowed = used < limit
    if allowed:
        msg = f"quota ok: {used}/{limit} runs in the last {window_seconds}s"
    else:
        msg = f"quota exceeded: {used}/{limit} runs in the last {window_seconds}s"
    return QuotaResult(
        job_name=job_name,
        allowed=allowed,
        used=used,
        limit=limit,
        window_seconds=window_seconds,
        message=msg,
    )


def render_quota_result(result: QuotaResult) -> str:
    status = "ALLOWED" if result.allowed else "BLOCKED"
    return (
        f"[quota] {result.job_name}: {status} — {result.message}"
    )

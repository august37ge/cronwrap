"""Debounce: suppress a job run if it was already triggered recently.

This is distinct from throttle/rate-limit in that debounce is designed
for edge-triggered scenarios: only run the job if there has been a quiet
period of at least `min_gap_seconds` since the *last run attempt*.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class DebounceResult:
    job_name: str
    allowed: bool
    last_run_at: Optional[str]  # ISO-8601 or None
    gap_seconds: Optional[float]
    min_gap_seconds: float
    reason: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def check_debounce(
    db_path: str,
    job_name: str,
    min_gap_seconds: float,
) -> DebounceResult:
    """Return a DebounceResult indicating whether the job should run.

    Reads the most recent run timestamp from the history table.
    Does NOT write anything — callers should use record_run() from
    cronwrap.history after a successful dispatch.
    """
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT started_at FROM runs WHERE job_name = ? ORDER BY started_at DESC LIMIT 1",
            (job_name,),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    now = _now_utc()

    if row is None:
        return DebounceResult(
            job_name=job_name,
            allowed=True,
            last_run_at=None,
            gap_seconds=None,
            min_gap_seconds=min_gap_seconds,
            reason="no previous run found",
        )

    last_run_at: str = row["started_at"]
    try:
        last_dt = datetime.fromisoformat(last_run_at)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return DebounceResult(
            job_name=job_name,
            allowed=True,
            last_run_at=last_run_at,
            gap_seconds=None,
            min_gap_seconds=min_gap_seconds,
            reason="could not parse last_run_at timestamp",
        )

    gap = (now - last_dt).total_seconds()
    allowed = gap >= min_gap_seconds
    reason = (
        f"gap {gap:.1f}s >= min {min_gap_seconds}s"
        if allowed
        else f"gap {gap:.1f}s < min {min_gap_seconds}s — debounced"
    )
    return DebounceResult(
        job_name=job_name,
        allowed=allowed,
        last_run_at=last_run_at,
        gap_seconds=gap,
        min_gap_seconds=min_gap_seconds,
        reason=reason,
    )


def render_debounce_result(result: DebounceResult) -> str:
    status = "ALLOWED" if result.allowed else "DEBOUNCED"
    lines = [
        f"[debounce] {result.job_name}: {status}",
        f"  min gap : {result.min_gap_seconds}s",
        f"  last run: {result.last_run_at or 'never'}",
        f"  gap     : {f'{result.gap_seconds:.1f}s' if result.gap_seconds is not None else 'n/a'}",
        f"  reason  : {result.reason}",
    ]
    return "\n".join(lines)

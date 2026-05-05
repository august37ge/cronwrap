"""Heartbeat tracking — record periodic pings and detect missed beats."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class HeartbeatResult:
    job_name: str
    last_beat: Optional[str]   # ISO-8601 UTC or None
    seconds_since: Optional[float]
    max_interval: int          # seconds
    alive: bool
    message: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_heartbeat_db(db_path: str) -> None:
    """Create the heartbeats table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS heartbeats (
                job_name  TEXT NOT NULL,
                beat_at   TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hb_job ON heartbeats (job_name)"
        )


def record_beat(db_path: str, job_name: str) -> str:
    """Insert a heartbeat for *job_name* at the current UTC time.

    Returns the ISO timestamp that was stored.
    """
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO heartbeats (job_name, beat_at) VALUES (?, ?)",
            (job_name, now),
        )
    return now


def check_heartbeat(db_path: str, job_name: str, max_interval: int) -> HeartbeatResult:
    """Return a :class:`HeartbeatResult` for *job_name*.

    *max_interval* is the maximum number of seconds allowed between beats
    before the job is considered dead.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT beat_at FROM heartbeats
            WHERE job_name = ?
            ORDER BY beat_at DESC
            LIMIT 1
            """,
            (job_name,),
        ).fetchone()

    if row is None:
        return HeartbeatResult(
            job_name=job_name,
            last_beat=None,
            seconds_since=None,
            max_interval=max_interval,
            alive=False,
            message=f"{job_name}: no heartbeat recorded",
        )

    last_beat_dt = datetime.fromisoformat(row["beat_at"])
    if last_beat_dt.tzinfo is None:
        last_beat_dt = last_beat_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    seconds_since = (now - last_beat_dt).total_seconds()
    alive = seconds_since <= max_interval

    if alive:
        msg = f"{job_name}: alive (last beat {seconds_since:.0f}s ago)"
    else:
        msg = (
            f"{job_name}: DEAD — last beat {seconds_since:.0f}s ago "
            f"(max {max_interval}s)"
        )

    return HeartbeatResult(
        job_name=job_name,
        last_beat=row["beat_at"],
        seconds_since=seconds_since,
        max_interval=max_interval,
        alive=alive,
        message=msg,
    )


def render_heartbeat_result(result: HeartbeatResult) -> str:
    status = "OK" if result.alive else "DEAD"
    return f"[{status}] {result.message}"

"""Concurrency guard: prevent more than N simultaneous runs of a job."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ConcurrencyResult:
    job_name: str
    allowed: bool
    active_count: int
    max_concurrent: int
    message: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_concurrency_db(db_path: str) -> None:
    """Create the active_runs table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS active_runs (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT    NOT NULL,
                pid      INTEGER NOT NULL,
                started  REAL    NOT NULL
            )
            """
        )


def register_run(db_path: str, job_name: str, pid: int) -> int:
    """Record a new active run; return the row id."""
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO active_runs (job_name, pid, started) VALUES (?, ?, ?)",
            (job_name, pid, time.time()),
        )
        return cur.lastrowid  # type: ignore[return-value]


def unregister_run(db_path: str, run_id: int) -> None:
    """Remove an active run record by id."""
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM active_runs WHERE id = ?", (run_id,))


def active_run_count(db_path: str, job_name: str) -> int:
    """Return the number of currently registered active runs for *job_name*."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM active_runs WHERE job_name = ?",
            (job_name,),
        ).fetchone()
        return int(row["cnt"])


def check_concurrency(
    db_path: str,
    job_name: str,
    max_concurrent: int = 1,
) -> ConcurrencyResult:
    """Return a ConcurrencyResult indicating whether a new run is permitted."""
    count = active_run_count(db_path, job_name)
    allowed = count < max_concurrent
    if allowed:
        msg = f"allowed ({count}/{max_concurrent} active runs)"
    else:
        msg = f"blocked — {count} active run(s) already running (max {max_concurrent})"
    return ConcurrencyResult(
        job_name=job_name,
        allowed=allowed,
        active_count=count,
        max_concurrent=max_concurrent,
        message=msg,
    )


def render_concurrency_result(result: ConcurrencyResult) -> str:
    status = "ALLOWED" if result.allowed else "BLOCKED"
    return f"[concurrency] {result.job_name}: {status} — {result.message}"

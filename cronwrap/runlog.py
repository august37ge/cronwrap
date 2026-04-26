"""runlog.py – per-job structured run log with filtering and summary."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class RunLogEntry:
    job_name: str
    started_at: str
    finished_at: str
    exit_code: int
    duration_s: float
    stdout: str
    stderr: str
    attempt: int = 1


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_runlog_db(db_path: str) -> None:
    """Create the run_log table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name    TEXT    NOT NULL,
                started_at  TEXT    NOT NULL,
                finished_at TEXT    NOT NULL,
                exit_code   INTEGER NOT NULL,
                duration_s  REAL    NOT NULL,
                stdout      TEXT    NOT NULL DEFAULT '',
                stderr      TEXT    NOT NULL DEFAULT '',
                attempt     INTEGER NOT NULL DEFAULT 1
            )
            """
        )


def append_run(db_path: str, entry: RunLogEntry) -> None:
    """Insert a new run log entry."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO run_log
                (job_name, started_at, finished_at, exit_code,
                 duration_s, stdout, stderr, attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.job_name,
                entry.started_at,
                entry.finished_at,
                entry.exit_code,
                entry.duration_s,
                entry.stdout,
                entry.stderr,
                entry.attempt,
            ),
        )


def get_run_log(
    db_path: str,
    job_name: Optional[str] = None,
    limit: int = 50,
    failed_only: bool = False,
) -> List[RunLogEntry]:
    """Retrieve run log entries with optional filters."""
    query = "SELECT * FROM run_log WHERE 1=1"
    params: list = []
    if job_name:
        query += " AND job_name = ?"
        params.append(job_name)
    if failed_only:
        query += " AND exit_code != 0"
    query += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        RunLogEntry(
            job_name=r["job_name"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
            exit_code=r["exit_code"],
            duration_s=r["duration_s"],
            stdout=r["stdout"],
            stderr=r["stderr"],
            attempt=r["attempt"],
        )
        for r in rows
    ]


def summarise_run_log(entries: List[RunLogEntry]) -> dict:
    """Return a simple summary dict for a list of entries."""
    if not entries:
        return {"total": 0, "failures": 0, "success_rate": None, "avg_duration_s": None}
    failures = sum(1 for e in entries if e.exit_code != 0)
    avg_dur = sum(e.duration_s for e in entries) / len(entries)
    return {
        "total": len(entries),
        "failures": failures,
        "success_rate": round((len(entries) - failures) / len(entries) * 100, 1),
        "avg_duration_s": round(avg_dur, 3),
    }

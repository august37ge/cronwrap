"""Snapshot: capture and compare job metric summaries over time."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Snapshot:
    job_name: str
    taken_at: str
    total_runs: int
    success_count: int
    failure_count: int
    avg_duration: float
    max_duration: float


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_snapshot_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                taken_at TEXT NOT NULL,
                total_runs INTEGER NOT NULL,
                success_count INTEGER NOT NULL,
                failure_count INTEGER NOT NULL,
                avg_duration REAL NOT NULL,
                max_duration REAL NOT NULL
            )
            """
        )


def save_snapshot(db_path: str, snapshot: Snapshot) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO snapshots
              (job_name, taken_at, total_runs, success_count, failure_count, avg_duration, max_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.job_name,
                snapshot.taken_at,
                snapshot.total_runs,
                snapshot.success_count,
                snapshot.failure_count,
                snapshot.avg_duration,
                snapshot.max_duration,
            ),
        )


def get_snapshots(db_path: str, job_name: str, limit: int = 10) -> list[Snapshot]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT job_name, taken_at, total_runs, success_count, failure_count,
                   avg_duration, max_duration
            FROM snapshots WHERE job_name = ?
            ORDER BY taken_at DESC LIMIT ?
            """,
            (job_name, limit),
        ).fetchall()
    return [Snapshot(**dict(r)) for r in rows]


def take_snapshot(db_path: str, job_name: str) -> Optional[Snapshot]:
    """Build a snapshot from current metrics and persist it."""
    from cronwrap.metrics import get_job_metrics

    m = get_job_metrics(db_path, job_name)
    if m is None:
        return None
    snap = Snapshot(
        job_name=job_name,
        taken_at=datetime.now(timezone.utc).isoformat(),
        total_runs=m.total_runs,
        success_count=m.success_count,
        failure_count=m.failure_count,
        avg_duration=m.avg_duration,
        max_duration=m.max_duration,
    )
    init_snapshot_db(db_path)
    save_snapshot(db_path, snap)
    return snap

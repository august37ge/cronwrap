"""Lightweight metrics collection for cron job runs."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from cronwrap.history import _connect


@dataclass
class JobMetrics:
    job_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration_seconds: float
    max_duration_seconds: float
    success_rate: float


def init_metrics_view(db_path: str) -> None:
    """Ensure the runs table exists (delegates to history init)."""
    conn = _connect(db_path)
    conn.close()


def get_job_metrics(db_path: str, job_name: str, limit: int = 100) -> Optional[JobMetrics]:
    """Return aggregated metrics for a single job."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN exit_code != 0 THEN 1 ELSE 0 END) AS failures,
                AVG(duration_seconds) AS avg_dur,
                MAX(duration_seconds) AS max_dur
            FROM (
                SELECT exit_code, duration_seconds
                FROM runs
                WHERE job_name = ?
                ORDER BY started_at DESC
                LIMIT ?
            )
            """,
            (job_name, limit),
        ).fetchone()
    finally:
        conn.close()

    if row is None or row[0] == 0:
        return None

    total, successes, failures, avg_dur, max_dur = row
    return JobMetrics(
        job_name=job_name,
        total_runs=total,
        successful_runs=successes or 0,
        failed_runs=failures or 0,
        avg_duration_seconds=round(avg_dur or 0.0, 3),
        max_duration_seconds=round(max_dur or 0.0, 3),
        success_rate=round((successes or 0) / total * 100, 2),
    )


def get_all_job_metrics(db_path: str, limit: int = 100) -> List[JobMetrics]:
    """Return metrics for every distinct job recorded in the database."""
    conn = _connect(db_path)
    try:
        names = [
            r[0] for r in conn.execute("SELECT DISTINCT job_name FROM runs").fetchall()
        ]
    finally:
        conn.close()

    results = []
    for name in names:
        m = get_job_metrics(db_path, name, limit=limit)
        if m:
            results.append(m)
    return results

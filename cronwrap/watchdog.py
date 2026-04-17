"""Watchdog: detect jobs that haven't run recently based on their schedule."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from cronwrap.history import get_recent_runs, _connect, init_db
from cronwrap.schedule import is_overdue, next_run_time


@dataclass
class WatchdogAlert:
    job_name: str
    schedule: str
    last_run: Optional[datetime]
    overdue_by_seconds: float
    message: str


def check_job_watchdog(db_path: str, job_name: str, schedule: str) -> Optional[WatchdogAlert]:
    """Return job is overdue, else None."""
    conn = _connect(db_path)
    init_db(conn)
    runs = get_recent_runs(conn, job_name, limit=1)
    conn.close()

    last_run: Optional[datetime] = None
    if runs:
        last_run = runs[0].started_at

    if not is_overdue(schedule, last_run):
         = datetime.now(timezone.utc)
    nxt = next_run_time(schedule)
    overdue_by = (now - nxt).total_seconds() if nxt and nxt < now else 0.0

    msg = (
        f"Job '{job_name}' is overdue (schedule: {schedule}). "
        f"Last run: {last_run.isoformat() if last_run else 'never'}."
    )
    return WatchdogAlert(
        job_name=job_name,
        schedule=schedule,
        last_run=last_run,
        overdue_by_seconds=overdue_by,
        message=msg,
    )


def check_all_watchdog(db_path: str, jobs: List[dict]) -> List[WatchdogAlert]:
    """Check all jobs from a config list and return overdue alerts."""
    alerts = []
    for job in jobs:
        name = job.get("name", "")
        schedule = job.get("schedule", "")
        if not name or not schedule:
            continue
        alert = check_job_watchdog(db_path, name, schedule)
        if alert:
            alerts.append(alert)
    return alerts


def render_watchdog_report(alerts: List[WatchdogAlert]) -> str:
    if not alerts:
        return "All jobs are running on schedule.\n"
    lines = ["OVERDUE JOBS", "=" * 40]
    for a in alerts:
        lines.append(a.message)
        if a.overdue_by_seconds > 0:
            lines.append(f"  Overdue by: {a.overdue_by_seconds:.0f}s")
    return "\n".join(lines) + "\n"

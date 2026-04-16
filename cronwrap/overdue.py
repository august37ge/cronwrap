"""Check all tracked jobs for overdue runs and emit warnings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from cronwrap.history import get_recent_runs
from cronwrap.schedule import is_overdue

logger = logging.getLogger(__name__)


@dataclass
class OverdueReport:
    job_name: str
    expression: str
    message: str


def check_job(job_name: str, expression: str, db_path: str) -> OverdueReport | None:
    """Return an OverdueReport if *job_name* is overdue, else None."""
    runs = get_recent_runs(job_name, limit=1, db_path=db_path)
    if not runs:
        return None
    last = runs[0]
    if is_overdue(expression, last.started_at):
        msg = f"Job '{job_name}' is overdue (schedule: {expression}, last run: {last.started_at})"
        logger.warning(msg)
        return OverdueReport(job_name=job_name, expression=expression, message=msg)
    return None


def check_all_jobs(jobs: List[dict], db_path: str) -> List[OverdueReport]:
    """Check a list of job dicts with keys 'name' and 'schedule'.

    Returns a list of OverdueReport for any overdue jobs.
    """
    reports: List[OverdueReport] = []
    for job in jobs:
        report = check_job(job["name"], job["schedule"], db_path=db_path)
        if report:
            reports.append(report)
    return reports

"""Retention policy: prune old job history records from the database."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwrap.history import _connect


@dataclass
class PruneResult:
    job_name: Optional[str]
    rows_deleted: int
    cutoff: datetime


def prune_job(
    db_path: str,
    job_name: str,
    keep_days: int = 30,
) -> PruneResult:
    """Delete records older than *keep_days* for a specific job."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    cutoff_iso = cutoff.isoformat()
    con = _connect(db_path)
    cur = con.execute(
        "DELETE FROM job_runs WHERE job_name = ? AND started_at < ?",
        (job_name, cutoff_iso),
    )
    con.commit()
    con.close()
    return PruneResult(job_name=job_name, rows_deleted=cur.rowcount, cutoff=cutoff)


def prune_all(
    db_path: str,
    keep_days: int = 30,
) -> PruneResult:
    """Delete all records older than *keep_days* regardless of job name."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    cutoff_iso = cutoff.isoformat()
    con = _connect(db_path)
    cur = con.execute(
        "DELETE FROM job_runs WHERE started_at < ?",
        (cutoff_iso,),
    )
    con.commit()
    con.close()
    return PruneResult(job_name=None, rows_deleted=cur.rowcount, cutoff=cutoff)


def prune_from_config(
    db_path: str,
    jobs: list[dict],
    default_keep_days: int = 30,
) -> list[PruneResult]:
    """Prune each job using per-job keep_days or the global default."""
    results = []
    for job in jobs:
        name = job.get("name", "")
        keep = job.get("keep_days", default_keep_days)
        if name:
            results.append(prune_job(db_path, name, keep_days=keep))
    return results

"""Healthcheck endpoint support: write a status file after each run."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cronwrap.runner import RunResult


@dataclass
class HealthStatus:
    job_name: str
    last_run: str          # ISO-8601
    success: bool
    exit_code: int
    duration: float
    message: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(job_name: str, result: RunResult, status_dir: str) -> Path:
    """Write a JSON status file for *job_name* into *status_dir*."""
    os.makedirs(status_dir, exist_ok=True)
    status = HealthStatus(
        job_name=job_name,
        last_run=_now_iso(),
        success=result.success,
        exit_code=result.exit_code,
        duration=result.duration,
        message=(result.stdout or result.stderr or "")[:256],
    )
    path = Path(status_dir) / f"{job_name}.json"
    path.write_text(json.dumps(asdict(status), indent=2))
    return path


def read_status(job_name: str, status_dir: str) -> Optional[HealthStatus]:
    """Return the last recorded HealthStatus for *job_name*, or None."""
    path = Path(status_dir) / f"{job_name}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return HealthStatus(**data)


def check_stale(job_name: str, status_dir: str, max_age_seconds: float) -> bool:
    """Return True when the status file is older than *max_age_seconds*."""
    status = read_status(job_name, status_dir)
    if status is None:
        return True
    last = datetime.fromisoformat(status.last_run)
    age = (datetime.now(timezone.utc) - last).total_seconds()
    return age > max_age_seconds

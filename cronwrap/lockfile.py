"""Simple file-based locking to prevent overlapping cron job runs."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LockResult:
    acquired: bool
    lock_path: str
    existing_pid: Optional[int] = None
    message: str = ""


def _lock_path(lock_dir: str, job_name: str) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return Path(lock_dir) / f"{safe}.lock"


def acquire(lock_dir: str, job_name: str) -> LockResult:
    """Try to acquire a lock for job_name. Returns LockResult."""
    path = _lock_path(lock_dir, job_name)
    os.makedirs(lock_dir, exist_ok=True)

    if path.exists():
        try:
            existing_pid = int(path.read_text().strip())
        except ValueError:
            existing_pid = None

        # Check if process is still alive
        if existing_pid is not None:
            try:
                os.kill(existing_pid, 0)
                return LockResult(
                    acquired=False,
                    lock_path=str(path),
                    existing_pid=existing_pid,
                    message=f"Job '{job_name}' already running (pid {existing_pid})",
                )
            except OSError:
                pass  # Process gone, stale lock — overwrite

    path.write_text(str(os.getpid()))
    return LockResult(acquired=True, lock_path=str(path), message="Lock acquired")


def release(lock_dir: str, job_name: str) -> bool:
    """Release the lock for job_name. Returns True if removed."""
    path = _lock_path(lock_dir, job_name)
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def is_locked(lock_dir: str, job_name: str) -> bool:
    path = _lock_path(lock_dir, job_name)
    if not path.exists():
        return False
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False

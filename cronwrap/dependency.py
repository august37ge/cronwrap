"""Job dependency checking — verify upstream jobs succeeded before running."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import get_recent_runs, _connect


@dataclass
class DependencyResult:
    job_name: str
    required_jobs: List[str]
    blocking_jobs: List[str] = field(default_factory=list)
    missing_jobs: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blocking_jobs and not self.missing_jobs


def check_dependency(job_name: str, required_jobs: List[str], db_path: str,
                     lookback: int = 1) -> DependencyResult:
    """Return a DependencyResult indicating whether all required jobs last ran successfully.

    Args:
        job_name:      The job about to run.
        required_jobs: Names of jobs that must have succeeded recently.
        db_path:       Path to the history SQLite database.
        lookback:      How many recent runs to inspect per dependency.
    """
    blocking: List[str] = []
    missing: List[str] = []

    for dep in required_jobs:
        runs = get_recent_runs(dep, limit=lookback, db_path=db_path)
        if not runs:
            missing.append(dep)
        elif runs[0].exit_code != 0:
            blocking.append(dep)

    return DependencyResult(
        job_name=job_name,
        required_jobs=required_jobs,
        blocking_jobs=blocking,
        missing_jobs=missing,
    )


def render_dependency_result(result: DependencyResult) -> str:
    """Return a human-readable summary of the dependency check."""
    lines = [f"Dependency check for '{result.job_name}':"]
    if result.ok:
        lines.append("  All dependencies satisfied.")
        return "\n".join(lines)
    if result.missing_jobs:
        lines.append("  No history found for: " + ", ".join(result.missing_jobs))
    if result.blocking_jobs:
        lines.append("  Last run failed for: " + ", ".join(result.blocking_jobs))
    lines.append("  Status: BLOCKED")
    return "\n".join(lines)

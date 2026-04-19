"""Check for required environment variables before running a job."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EnvCheckResult:
    job_name: str
    required: List[str]
    missing: List[str] = field(default_factory=list)
    present: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def check_env(job_name: str, required_vars: List[str]) -> EnvCheckResult:
    """Check that all required environment variables are set."""
    missing: List[str] = []
    present: List[str] = []
    for var in required_vars:
        if os.environ.get(var):
            present.append(var)
        else:
            missing.append(var)
    return EnvCheckResult(
        job_name=job_name,
        required=list(required_vars),
        missing=missing,
        present=present,
    )


def render_env_check_result(result: EnvCheckResult) -> str:
    lines = [f"Env check for '{result.job_name}':"]
    if result.ok:
        lines.append("  All required variables are set.")
    else:
        lines.append(f"  MISSING ({len(result.missing)}):")
        for var in result.missing:
            lines.append(f"    - {var}")
    if result.present:
        lines.append(f"  Present ({len(result.present)}): {', '.join(result.present)}")
    return "\n".join(lines)


def check_env_from_config(job_name: str, job_config: dict) -> Optional[EnvCheckResult]:
    """Run env check using a job config dict. Returns None if no env_vars key."""
    required = job_config.get("env_vars", [])
    if not required:
        return None
    return check_env(job_name, required)

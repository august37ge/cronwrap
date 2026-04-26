"""Precondition checks for cron jobs.

Allows a job to declare shell-command or Python-callable preconditions
that must pass (exit 0 / return True) before the job is allowed to run.
This is useful for things like "only run if disk space > 10 GB" or
"only run if the upstream service is reachable".
"""

from __future__ import annotations

import subprocess
import shlex
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class PreconditionResult:
    """Outcome of evaluating one or more preconditions."""

    allowed: bool
    """True when every precondition passed."""

    failed: List[str] = field(default_factory=list)
    """Human-readable descriptions of the conditions that failed."""

    passed: List[str] = field(default_factory=list)
    """Human-readable descriptions of the conditions that passed."""


def _run_shell(command: str, timeout: int) -> bool:
    """Return True if *command* exits with code 0."""
    try:
        result = subprocess.run(
            shlex.split(command),
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_preconditions(
    commands: Optional[List[str]] = None,
    callables: Optional[List[Callable[[], bool]]] = None,
    timeout: int = 10,
) -> PreconditionResult:
    """Evaluate all preconditions and return a consolidated result.

    Parameters
    ----------
    commands:
        Shell commands to run.  Each must exit 0 to be considered passing.
    callables:
        Python callables that take no arguments and return a bool.
    timeout:
        Per-command timeout in seconds (applies to shell commands only).

    Returns
    -------
    PreconditionResult
        ``allowed`` is True only when every supplied condition passes.
    """
    passed: List[str] = []
    failed: List[str] = []

    for cmd in commands or []:
        label = f"shell: {cmd}"
        if _run_shell(cmd, timeout):
            passed.append(label)
        else:
            failed.append(label)

    for fn in callables or []:
        label = f"callable: {fn.__name__}"
        try:
            ok = bool(fn())
        except Exception as exc:  # noqa: BLE001
            ok = False
            label = f"callable: {fn.__name__} (raised {exc})"
        if ok:
            passed.append(label)
        else:
            failed.append(label)

    return PreconditionResult(
        allowed=len(failed) == 0,
        failed=failed,
        passed=passed,
    )


def check_preconditions_from_config(
    job_config: dict,
    timeout: int = 10,
) -> PreconditionResult:
    """Convenience wrapper that reads precondition commands from a job config dict.

    The config dict may contain::

        {
            "preconditions": ["test -f /var/run/ready", "ping -c1 db.internal"]
        }

    Parameters
    ----------
    job_config:
        Mapping with an optional ``preconditions`` key holding a list of
        shell command strings.
    timeout:
        Per-command timeout forwarded to :func:`check_preconditions`.
    """
    commands: List[str] = job_config.get("preconditions") or []
    return check_preconditions(commands=commands, timeout=timeout)


def render_precondition_result(result: PreconditionResult) -> str:
    """Return a human-readable summary of a :class:`PreconditionResult`."""
    lines: List[str] = []
    status = "ALLOWED" if result.allowed else "BLOCKED"
    lines.append(f"Preconditions: {status}")
    for label in result.passed:
        lines.append(f"  [PASS] {label}")
    for label in result.failed:
        lines.append(f"  [FAIL] {label}")
    if not result.passed and not result.failed:
        lines.append("  (no preconditions defined)")
    return "\n".join(lines)

"""CLI sub-command for cooldown checks."""

from __future__ import annotations

import argparse
import sys

from cronwrap.cooldown import check_cooldown, render_cooldown_result


def add_cooldown_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *cooldown* sub-command."""
    p = subparsers.add_parser(
        "cooldown",
        help="Check whether a job is still in its post-failure cooldown window.",
    )
    p.add_argument("job_name", help="Name of the job to check.")
    p.add_argument(
        "--db",
        default="cronwrap.db",
        help="Path to the SQLite history database (default: cronwrap.db).",
    )
    p.add_argument(
        "--seconds",
        type=int,
        default=300,
        help="Cooldown window in seconds (default: 300).",
    )


def run_cooldown(ns: argparse.Namespace) -> int:
    """Execute the cooldown check and return an exit code.

    Returns 0 when the job is allowed to run, 1 when it is blocked.
    """
    result = check_cooldown(
        db_path=ns.db,
        job_name=ns.job_name,
        cooldown_seconds=ns.seconds,
    )
    print(render_cooldown_result(result))
    return 0 if result.allowed else 1


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="cronwrap-cooldown")
    subs = parser.add_subparsers(dest="command")
    add_cooldown_subparser(subs)
    args = parser.parse_args()
    sys.exit(run_cooldown(args))

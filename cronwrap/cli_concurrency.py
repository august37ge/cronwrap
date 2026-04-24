"""CLI sub-command: concurrency — check or manage active run slots."""
from __future__ import annotations

import argparse
import os
import sys

from cronwrap.concurrency import (
    check_concurrency,
    init_concurrency_db,
    register_run,
    render_concurrency_result,
    unregister_run,
)

_DEFAULT_DB = "cronwrap.db"


def add_concurrency_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "concurrency",
        help="Check or manage concurrent run slots for a job",
    )
    p.add_argument("job_name", help="Name of the cron job")
    p.add_argument(
        "--max",
        type=int,
        default=1,
        dest="max_concurrent",
        help="Maximum allowed simultaneous runs (default: 1)",
    )
    p.add_argument("--db", default=_DEFAULT_DB, help="Path to SQLite database")

    action = p.add_mutually_exclusive_group()
    action.add_argument(
        "--register",
        action="store_true",
        help="Register current PID as an active run and print the run-id",
    )
    action.add_argument(
        "--unregister",
        type=int,
        metavar="RUN_ID",
        help="Remove an active run record by its id",
    )


def run_concurrency(ns: argparse.Namespace) -> int:
    db_path: str = ns.db
    job_name: str = ns.job_name
    max_concurrent: int = ns.max_concurrent

    init_concurrency_db(db_path)

    if ns.unregister is not None:
        unregister_run(db_path, ns.unregister)
        print(f"[concurrency] unregistered run id {ns.unregister} for '{job_name}'")
        return 0

    result = check_concurrency(db_path, job_name, max_concurrent)
    print(render_concurrency_result(result))

    if ns.register:
        if not result.allowed:
            return 1
        run_id = register_run(db_path, job_name, os.getpid())
        print(f"[concurrency] registered run id {run_id} (pid {os.getpid()})")
        return 0

    return 0 if result.allowed else 1

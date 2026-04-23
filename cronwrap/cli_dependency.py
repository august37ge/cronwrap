"""CLI sub-command: cronwrap dependency — check job dependencies."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronwrap.dependency import check_dependency, render_dependency_result


def add_dependency_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "dependency",
        help="Check whether upstream jobs succeeded before running a job.",
    )
    p.add_argument("job", help="Name of the job about to run.")
    p.add_argument(
        "--requires",
        nargs="+",
        metavar="JOB",
        required=True,
        help="One or more job names that must have succeeded recently.",
    )
    p.add_argument(
        "--db",
        default="cronwrap_history.db",
        help="Path to the history database (default: cronwrap_history.db).",
    )
    p.add_argument(
        "--lookback",
        type=int,
        default=1,
        help="Number of recent runs to inspect per dependency (default: 1).",
    )


def run_dependency(ns: argparse.Namespace) -> int:
    result = check_dependency(
        job_name=ns.job,
        required_jobs=ns.requires,
        db_path=ns.db,
        lookback=ns.lookback,
    )
    print(render_dependency_result(result))
    return 0 if result.ok else 1

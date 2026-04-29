"""CLI subcommand: runcount — query how many times a job ran in a window."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwrap.runcount import count_runs, render_runcount_result

_DEFAULT_DB = "cronwrap.db"


def add_runcount_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "runcount",
        help="Show how many times a job ran within a time window",
    )
    p.add_argument("job_name", help="Name of the job to query")
    p.add_argument(
        "--window",
        type=int,
        default=3600,
        metavar="SECONDS",
        help="Look-back window in seconds (default: 3600)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Optional maximum allowed runs; exit 1 when reached",
    )
    p.add_argument(
        "--db",
        default=_DEFAULT_DB,
        metavar="PATH",
        help="Path to the SQLite database (default: cronwrap.db)",
    )


def run_runcount(ns: argparse.Namespace) -> int:
    result = count_runs(
        db_path=ns.db,
        job_name=ns.job_name,
        window_seconds=ns.window,
        limit=ns.limit,
    )
    print(render_runcount_result(result))
    return 0 if result.allowed else 1

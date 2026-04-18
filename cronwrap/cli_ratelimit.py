"""CLI subcommand: ratelimit — check whether a job is allowed to run."""
from __future__ import annotations

import argparse
import sys

from cronwrap.ratelimit import check_rate_limit, render_rate_limit_result


def add_ratelimit_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("ratelimit", help="Check if a job is rate-limited")
    p.add_argument("--db", required=True, help="Path to history SQLite DB")
    p.add_argument("--job", required=True, help="Job name")
    p.add_argument(
        "--min-interval",
        type=int,
        required=True,
        metavar="SECONDS",
        help="Minimum seconds between runs",
    )


def run_ratelimit(ns: argparse.Namespace) -> int:
    result = check_rate_limit(
        db_path=ns.db,
        job_name=ns.job,
        min_interval_seconds=ns.min_interval,
    )
    print(render_rate_limit_result(result))
    return 0 if result.allowed else 1

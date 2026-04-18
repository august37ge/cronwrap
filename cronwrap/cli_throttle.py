"""CLI subcommand: throttle — check whether a job is allowed to run."""
from __future__ import annotations

import argparse
import sys

from cronwrap.throttle import check_throttle, render_throttle_result


def add_throttle_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "throttle",
        help="Check whether a job is within its minimum run interval",
    )
    p.add_argument("job_name", help="Name of the cron job")
    p.add_argument(
        "--min-interval",
        type=int,
        required=True,
        metavar="SECONDS",
        help="Minimum seconds that must pass between runs",
    )
    p.add_argument("--db", default="cronwrap.db", help="Path to history database")


def run_throttle(ns: argparse.Namespace) -> int:
    result = check_throttle(
        job_name=ns.job_name,
        min_interval_seconds=ns.min_interval,
        db_path=ns.db,
    )
    print(render_throttle_result(result))
    if not result.allowed:
        return 2  # distinct exit code so callers can detect throttle vs error
    return 0

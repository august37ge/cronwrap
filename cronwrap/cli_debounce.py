"""CLI sub-command: cronwrap debounce"""
from __future__ import annotations

import argparse
import sys

from cronwrap.debounce import check_debounce, render_debounce_result


def add_debounce_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "debounce",
        help="Check whether a job is within its debounce quiet period.",
    )
    p.add_argument("job_name", help="Name of the cron job to check.")
    p.add_argument(
        "--db",
        default="cronwrap.db",
        help="Path to the SQLite history database (default: cronwrap.db).",
    )
    p.add_argument(
        "--min-gap",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Minimum quiet-period in seconds (default: 60).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; rely on exit code only.",
    )


def run_debounce(args: argparse.Namespace) -> int:
    result = check_debounce(
        db_path=args.db,
        job_name=args.job_name,
        min_gap_seconds=args.min_gap,
    )
    if not args.quiet:
        print(render_debounce_result(result))
    return 0 if result.allowed else 1


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="cronwrap-debounce")
    subs = parser.add_subparsers(dest="command")
    add_debounce_subparser(subs)
    parsed = parser.parse_args()
    sys.exit(run_debounce(parsed))

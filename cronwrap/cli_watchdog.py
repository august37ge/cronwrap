"""CLI subcommand: watchdog — report overdue jobs."""
from __future__ import annotations

import argparse
import sys

from cronwrap.config import load_config, get_jobs
from cronwrap.watchdog import check_all_watchdog, render_watchdog_report


def add_watchdog_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("watchdog", help="Report jobs that are overdue based on their schedule")
    p.add_argument("--config", required=True, help="Path to cronwrap config file")
    p.add_argument("--db", required=True, help="Path to history database")
    p.add_argument("--fail-on-overdue", action="store_true",
                   help="Exit with code 1 if any jobs are overdue")


def run_watchdog(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except Exception as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 2

    jobs = get_jobs(cfg)
    alerts = check_all_watchdog(args.db, jobs)
    report = render_watchdog_report(alerts)
    print(report, end="")

    if alerts and getattr(args, "fail_on_overdue", False):
        return 1
    return 0

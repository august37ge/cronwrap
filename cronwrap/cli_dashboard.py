"""CLI subcommand: cronwrap dashboard"""
from __future__ import annotations
import argparse

from cronwrap.dashboard import build_dashboard, print_dashboard
from cronwrap.config import load_config, get_jobs


def add_dashboard_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("dashboard", help="Show a summary dashboard of all jobs")
    p.add_argument("--db", default="cronwrap.db", help="Path to history database")
    p.add_argument("--config", default=None, help="Config file for schedule/overdue info")


def run_dashboard(args: argparse.Namespace) -> int:
    jobs: list = []
    if args.config:
        try:
            cfg = load_config(args.config)
            jobs = get_jobs(cfg)
        except Exception as exc:  # pragma: no cover
            print(f"Warning: could not load config: {exc}")

    rows = build_dashboard(args.db, jobs)
    print_dashboard(rows)
    return 0

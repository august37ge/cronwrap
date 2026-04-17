"""CLI helpers for the 'prune' sub-command."""
from __future__ import annotations

import argparse
import sys

from cronwrap.config import load_config, get_jobs
from cronwrap.retention import prune_job, prune_all, prune_from_config
from cronwrap.retention_report import print_prune_report


def add_prune_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("prune", help="Remove old job history records")
    p.add_argument("--db", default="cronwrap.db", help="Path to history database")
    p.add_argument("--job", default=None, help="Prune a single named job")
    p.add_argument(
        "--keep-days",
        type=int,
        default=30,
        dest="keep_days",
        help="Retain records newer than this many days (default: 30)",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Config file; per-job keep_days overrides --keep-days",
    )
    p.set_defaults(func=run_prune)


def run_prune(args: argparse.Namespace) -> int:
    if args.config:
        try:
            cfg = load_config(args.config)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        jobs = get_jobs(cfg)
        results = prune_from_config(args.db, jobs, default_keep_days=args.keep_days)
        print_prune_report(results)
        return 0

    if args.job:
        result = prune_job(args.db, args.job, keep_days=args.keep_days)
        print_prune_report([result])
    else:
        result = prune_all(args.db, keep_days=args.keep_days)
        print_prune_report([result])
    return 0

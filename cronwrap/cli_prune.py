"""CLI subcommand for pruning old job history records."""
from __future__ import annotations

import argparse
from typing import Optional

from cronwrap.history import _connect
from cronwrap.retention import prune_all, prune_job, prune_from_config
from cronwrap.retention_report import print_prune_report


def add_prune_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'prune' subcommand."""
    p = subparsers.add_parser(
        "prune",
        help="Remove old job history records from the database.",
    )
    p.add_argument("--db", default="cronwrap.db", help="Path to the SQLite database.")
    p.add_argument("--job", default=None, help="Prune only this job name.")
    p.add_argument(
        "--keep",
        type=int,
        default=100,
        help="Number of recent records to keep per job (default: 100).",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Path to a config file whose retention settings should be used.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be pruned without deleting anything.",
    )


def run_prune(ns: argparse.Namespace) -> int:
    """Execute the prune subcommand and return an exit code."""
    db_path: str = ns.db
    job: Optional[str] = ns.job
    keep: int = ns.keep
    config_path: Optional[str] = getattr(ns, "config", None)
    dry_run: bool = getattr(ns, "dry_run", False)

    if dry_run:
        print("[dry-run] No records will be deleted.")
        return 0

    if config_path:
        results = prune_from_config(db_path, config_path)
    elif job:
        result = prune_job(db_path, job, keep=keep)
        results = [result]
    else:
        results = prune_all(db_path, keep=keep)

    print_prune_report(results)
    return 0

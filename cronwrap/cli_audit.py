"""CLI sub-command: cronwrap audit — display the audit log."""
from __future__ import annotations

import argparse
from typing import Optional

from cronwrap.audit import get_audit_entries, init_audit_db


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Show the audit log of past job invocations")
    p.add_argument("--db", default="cronwrap.db", help="Path to the SQLite database")
    p.add_argument("--job", default=None, help="Filter by job name")
    p.add_argument("--limit", type=int, default=20, help="Max rows to display (default 20)")


def run_audit(args: argparse.Namespace) -> int:
    init_audit_db(args.db)
    entries = get_audit_entries(args.db, job_name=args.job, limit=args.limit)
    if not entries:
        print("No audit entries found.")
        return 0

    header = f"{'ID':>5}  {'Job':<20}  {'Started At':>25}  {'Exit':>4}  {'Dur(s)':>7}  {'Retries':>7}  Tags"
    print(header)
    print("-" * len(header))
    for e in entries:
        print(
            f"{e.id:>5}  {e.job_name:<20}  {e.started_at:>25}  "
            f"{e.exit_code:>4}  {e.duration_s:>7.2f}  {e.retries:>7}  {e.tags}"
        )
    return 0

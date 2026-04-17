"""CLI subcommand for viewing the audit log."""
from __future__ import annotations

import argparse
from cronwrap.audit import init_audit_db, get_audit_entries


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("audit", help="Show audit log entries")
    p.add_argument("--db", default="cronwrap.db", help="Path to history database")
    p.add_argument("--job", default=None, help="Filter by job name")
    p.add_argument("--action", default=None, help="Filter by action type")
    p.add_argument("--limit", type=int, default=50, help="Max entries to show")
    p.set_defaults(func=run_audit)


def run_audit(args: argparse.Namespace) -> int:
    init_audit_db(args.db)
    entries = get_audit_entries(
        args.db,
        job_name=args.job,
        action=args.action,
        limit=args.limit,
    )
    if not entries:
        print("No audit entries found.")
        return 0
    print(f"{'Timestamp':<26} {'Job':<20} {'Action':<16} {'Detail'}")
    print("-" * 80)
    for e in entries:
        detail = e.detail or ""
        print(f"{e.timestamp:<26} {e.job_name:<20} {e.action:<16} {detail}")
    return 0

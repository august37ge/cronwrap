"""CLI subcommands for job reports and tag reports."""
from __future__ import annotations

import argparse

from cronwrap.history import init_db, _connect
from cronwrap.report import print_report
from cronwrap.tag_report import print_tag_report


def add_report_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'report' subcommand."""
    p = subparsers.add_parser(
        "report",
        help="Print a summary report of recent job history.",
    )
    p.add_argument(
        "--db",
        default="cronwrap.db",
        help="Path to the SQLite history database (default: cronwrap.db).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent runs to consider per job (default: 10).",
    )
    p.add_argument(
        "--tag",
        default=None,
        help="Filter report to jobs with this tag.",
    )
    p.set_defaults(func=run_report)


def run_report(args: argparse.Namespace) -> int:
    """Execute the report subcommand."""
    db_path = args.db
    init_db(db_path)
    conn = _connect(db_path)
    try:
        if args.tag:
            print_tag_report(conn, tag=args.tag, limit=args.limit)
        else:
            print_report(conn, limit=args.limit)
    finally:
        conn.close()
    return 0

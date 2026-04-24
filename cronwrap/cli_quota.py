"""CLI sub-command for quota checking."""

from __future__ import annotations

import argparse
import sys

from cronwrap.quota import (
    check_quota,
    init_quota_db,
    record_quota_run,
    render_quota_result,
)


def add_quota_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("quota", help="Check or record a job run quota")
    p.add_argument("job_name", help="Name of the job")
    p.add_argument("--db", default="cronwrap.db", help="Path to the SQLite database")
    p.add_argument("--limit", type=int, required=True, help="Max runs allowed in the window")
    p.add_argument(
        "--window", type=int, required=True, metavar="SECONDS",
        help="Rolling window size in seconds",
    )
    p.add_argument(
        "--record", action="store_true",
        help="Record a run after a successful quota check",
    )
    p.add_argument(
        "--check-only", action="store_true",
        help="Only check quota; do not record (default behaviour when --record is omitted)",
    )


def run_quota(ns: argparse.Namespace) -> int:
    init_quota_db(ns.db)
    result = check_quota(
        db_path=ns.db,
        job_name=ns.job_name,
        limit=ns.limit,
        window_seconds=ns.window,
    )
    print(render_quota_result(result))
    if result.allowed and getattr(ns, "record", False):
        record_quota_run(ns.db, ns.job_name)
    return 0 if result.allowed else 1

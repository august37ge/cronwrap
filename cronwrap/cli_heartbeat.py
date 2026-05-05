"""CLI sub-commands for heartbeat: *beat* and *check*."""

from __future__ import annotations

import argparse

from cronwrap.heartbeat import (
    init_heartbeat_db,
    record_beat,
    check_heartbeat,
    render_heartbeat_result,
)


def add_heartbeat_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("heartbeat", help="Record or check job heartbeats")
    sub = p.add_subparsers(dest="heartbeat_cmd", required=True)

    # beat
    beat_p = sub.add_parser("beat", help="Record a heartbeat ping for a job")
    beat_p.add_argument("job_name", help="Name of the job")
    beat_p.add_argument("--db", default="cronwrap.db", help="SQLite database path")

    # check
    check_p = sub.add_parser("check", help="Check whether a job is still alive")
    check_p.add_argument("job_name", help="Name of the job")
    check_p.add_argument(
        "--max-interval",
        type=int,
        default=3600,
        metavar="SECONDS",
        help="Maximum seconds between beats before job is considered dead (default 3600)",
    )
    check_p.add_argument("--db", default="cronwrap.db", help="SQLite database path")


def run_heartbeat(ns: argparse.Namespace) -> int:
    init_heartbeat_db(ns.db)

    if ns.heartbeat_cmd == "beat":
        ts = record_beat(ns.db, ns.job_name)
        print(f"Heartbeat recorded for '{ns.job_name}' at {ts}")
        return 0

    if ns.heartbeat_cmd == "check":
        result = check_heartbeat(ns.db, ns.job_name, ns.max_interval)
        print(render_heartbeat_result(result))
        return 0 if result.alive else 1

    return 1  # unknown sub-command

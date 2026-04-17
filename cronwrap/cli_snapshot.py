"""CLI subcommand: snapshot — capture or view metric snapshots."""
from __future__ import annotations

import argparse
import sys

from cronwrap.snapshots import take_snapshot, get_snapshots, init_snapshot_db


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("snapshot", help="Capture or view job metric snapshots")
    p.add_argument("--db", default="cronwrap.db", help="Path to history DB")
    sub = p.add_subparsers(dest="snapshot_cmd")

    take_p = sub.add_parser("take", help="Take a snapshot for a job")
    take_p.add_argument("job_name", help="Job name")

    view_p = sub.add_parser("view", help="View recent snapshots for a job")
    view_p.add_argument("job_name", help="Job name")
    view_p.add_argument("--limit", type=int, default=5, help="Number of snapshots")


def run_snapshot(ns: argparse.Namespace) -> int:
    if ns.snapshot_cmd == "take":
        snap = take_snapshot(ns.db, ns.job_name)
        if snap is None:
            print(f"No metrics found for job '{ns.job_name}'.")
            return 1
        print(
            f"Snapshot taken for '{snap.job_name}' at {snap.taken_at}: "
            f"runs={snap.total_runs} ok={snap.success_count} fail={snap.failure_count} "
            f"avg={snap.avg_duration:.2f}s max={snap.max_duration:.2f}s"
        )
        return 0

    if ns.snapshot_cmd == "view":
        init_snapshot_db(ns.db)
        snaps = get_snapshots(ns.db, ns.job_name, limit=ns.limit)
        if not snaps:
            print(f"No snapshots found for '{ns.job_name}'.")
            return 0
        header = f"{'Taken At':<32} {'Runs':>6} {'OK':>6} {'Fail':>6} {'Avg(s)':>8} {'Max(s)':>8}"
        print(header)
        print("-" * len(header))
        for s in snaps:
            print(
                f"{s.taken_at:<32} {s.total_runs:>6} {s.success_count:>6} "
                f"{s.failure_count:>6} {s.avg_duration:>8.2f} {s.max_duration:>8.2f}"
            )
        return 0

    print("Specify a subcommand: take | view")
    return 1

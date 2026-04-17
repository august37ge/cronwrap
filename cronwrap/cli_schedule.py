"""CLI subcommand for schedule inspection — next run times and overdue checks."""
from __future__ import annotations

import argparse
from cronwrap.config import load_config, get_jobs
from cronwrap.schedule import next_run_time, is_overdue
from cronwrap.history import init_db, get_recent_runs


def add_schedule_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("schedule", help="Show schedule info and overdue jobs")
    p.add_argument("--config", required=True, help="Path to config file")
    p.add_argument("--db", default="cronwrap.db", help="Path to history database")
    p.add_argument("--overdue-only", action="store_true", help="Only show overdue jobs")
    p.set_defaults(func=run_schedule)


def run_schedule(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    jobs = get_jobs(cfg)
    init_db(args.db)

    rows = []
    for job in jobs:
        name = job.get("name", "<unnamed>")
        expr = job.get("schedule", "")
        nxt = next_run_time(expr)
        nxt_str = nxt.strftime("%Y-%m-%d %H:%M:%S") if nxt else "invalid"

        recent = get_recent_runs(args.db, name, limit=1)
        last_ts = recent[0].timestamp if recent else None
        overdue = is_overdue(expr, last_ts) if expr else False

        if args.overdue_only and not overdue:
            continue
        flag = " [OVERDUE]" if overdue else ""
        rows.append((name, expr or "—", nxt_str, flag))

    if not rows:
        print("No jobs to display.")
        return 0

    print(f"{'Job':<24} {'Schedule':<20} {'Next Run':<22} {'Status'}")
    print("-" * 72)
    for name, expr, nxt_str, flag in rows:
        print(f"{name:<24} {expr:<20} {nxt_str:<22}{flag}")
    return 0

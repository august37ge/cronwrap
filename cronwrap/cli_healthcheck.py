"""CLI subcommand: healthcheck — show / check job status files."""
from __future__ import annotations

import argparse
import sys

from cronwrap.healthcheck import read_status, check_stale


def add_healthcheck_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("healthcheck", help="Check job health-status files")
    p.add_argument("job", help="Job name")
    p.add_argument("--status-dir", default="/var/lib/cronwrap/status",
                   help="Directory containing status files")
    p.add_argument("--max-age", type=float, default=0,
                   help="Fail if last run is older than N seconds (0 = disabled)")


def run_healthcheck(ns: argparse.Namespace) -> int:
    status = read_status(ns.job, ns.status_dir)
    if status is None:
        print(f"[healthcheck] No status file found for job '{ns.job}'")
        return 1

    icon = "OK" if status.success else "FAIL"
    print(f"[{icon}] {status.job_name}  last_run={status.last_run}  "
          f"exit={status.exit_code}  duration={status.duration:.2f}s")
    if status.message:
        print(f"       {status.message}")

    if ns.max_age > 0 and check_stale(ns.job, ns.status_dir, ns.max_age):
        print(f"[healthcheck] STALE — last run exceeds {ns.max_age}s threshold")
        return 2

    return 0 if status.success else 1

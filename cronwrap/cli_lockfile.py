"""CLI subcommand for inspecting and clearing job locks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from cronwrap import lockfile


def add_lockfile_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("lock", help="Inspect or clear job locks")
    p.add_argument("--lock-dir", default="/tmp/cronwrap/locks", help="Lock directory")
    sub = p.add_subparsers(dest="lock_cmd")

    ls = sub.add_parser("list", help="List active locks")
    ls.add_argument("--lock-dir", default=None)

    clr = sub.add_parser("clear", help="Clear lock for a job")
    clr.add_argument("job", help="Job name")


def run_lockfile(ns: argparse.Namespace) -> int:
    lock_dir = getattr(ns, "lock_dir", "/tmp/cronwrap/locks")
    cmd = getattr(ns, "lock_cmd", None)

    if cmd == "list" or cmd is None:
        dir_path = Path(lock_dir)
        if not dir_path.exists():
            print("No lock directory found.")
            return 0
        files = list(dir_path.glob("*.lock"))
        if not files:
            print("No active locks.")
            return 0
        for f in sorted(files):
            job = f.stem
            active = lockfile.is_locked(lock_dir, job)
            status = "ACTIVE" if active else "STALE"
            try:
                pid = f.read_text().strip()
            except Exception:
                pid = "?"
            print(f"{job:<30} pid={pid:<8} {status}")
        return 0

    if cmd == "clear":
        removed = lockfile.release(lock_dir, ns.job)
        if removed:
            print(f"Lock cleared for '{ns.job}'.")
        else:
            print(f"No lock found for '{ns.job}'.")
        return 0

    print("Unknown lock subcommand.")
    return 1

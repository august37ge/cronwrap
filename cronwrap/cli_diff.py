"""CLI subcommand: diff two snapshots by label or index."""
from __future__ import annotations
import argparse
from cronwrap.snapshots import get_snapshots
from cronwrap.diff import diff_snapshots, print_diff


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("diff", help="Diff two snapshots")
    p.add_argument("--db", default="cronwrap.db", help="Path to history DB")
    p.add_argument("--old", required=True, help="Label of the older snapshot")
    p.add_argument("--new", required=True, help="Label of the newer snapshot")


def run_diff(ns: argparse.Namespace) -> int:
    snapshots = get_snapshots(ns.db)
    by_label = {s.label: s for s in snapshots}

    if ns.old not in by_label:
        print(f"Snapshot not found: {ns.old}")
        return 1
    if ns.new not in by_label:
        print(f"Snapshot not found: {ns.new}")
        return 1

    diffs = diff_snapshots(by_label[ns.old], by_label[ns.new])
    print_diff(diffs)
    return 0

"""CLI sub-commands for checkpoint management."""

from __future__ import annotations

import argparse
import sys

from cronwrap.checkpoint import (
    delete_checkpoint,
    init_checkpoint_db,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


def add_checkpoint_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("checkpoint", help="Manage job checkpoints")
    p.add_argument("--db", default="cronwrap.db", help="Path to SQLite database")
    sub = p.add_subparsers(dest="checkpoint_cmd", required=True)

    # save
    sv = sub.add_parser("save", help="Save or update a checkpoint")
    sv.add_argument("job", help="Job name")
    sv.add_argument("key", help="Checkpoint key")
    sv.add_argument("value", help="Checkpoint value")

    # load
    ld = sub.add_parser("load", help="Print a checkpoint value")
    ld.add_argument("job", help="Job name")
    ld.add_argument("key", help="Checkpoint key")

    # delete
    dl = sub.add_parser("delete", help="Delete a checkpoint")
    dl.add_argument("job", help="Job name")
    dl.add_argument("key", help="Checkpoint key")

    # list
    ls = sub.add_parser("list", help="List all checkpoints for a job")
    ls.add_argument("job", help="Job name")


def run_checkpoint(ns: argparse.Namespace) -> int:
    init_checkpoint_db(ns.db)

    if ns.checkpoint_cmd == "save":
        save_checkpoint(ns.db, ns.job, ns.key, ns.value)
        print(f"Saved checkpoint {ns.job}/{ns.key} = {ns.value}")
        return 0

    if ns.checkpoint_cmd == "load":
        cp = load_checkpoint(ns.db, ns.job, ns.key)
        if cp is None:
            print(f"No checkpoint found for {ns.job}/{ns.key}", file=sys.stderr)
            return 1
        print(cp.value)
        return 0

    if ns.checkpoint_cmd == "delete":
        removed = delete_checkpoint(ns.db, ns.job, ns.key)
        if removed:
            print(f"Deleted checkpoint {ns.job}/{ns.key}")
            return 0
        print(f"No checkpoint found for {ns.job}/{ns.key}", file=sys.stderr)
        return 1

    if ns.checkpoint_cmd == "list":
        entries = list_checkpoints(ns.db, ns.job)
        if not entries:
            print(f"No checkpoints for job '{ns.job}'")
            return 0
        for cp in entries:
            print(f"{cp.key}={cp.value}  (updated {cp.updated_at})")
        return 0

    return 1

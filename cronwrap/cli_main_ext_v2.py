"""Extended subcommand registry including diff."""
from __future__ import annotations
import argparse
from cronwrap.cli_main_ext import register_all_subcommands as _register_base
from cronwrap.cli_diff import add_diff_subparser, run_diff

_EXTRA = {
    "diff": run_diff,
}


def register_all_subcommands(subparsers: argparse._SubParsersAction) -> dict:
    """Register base + extra subcommands; return dispatch map."""
    dispatch = _register_base(subparsers)
    add_diff_subparser(subparsers)
    dispatch.update(_EXTRA)
    return dispatch


def dispatch(ns: argparse.Namespace, dispatch_map: dict) -> int:
    handler = dispatch_map.get(ns.command)
    if handler is None:
        print(f"Unknown command: {ns.command}")
        return 1
    return handler(ns)

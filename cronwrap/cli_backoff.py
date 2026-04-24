"""CLI subcommand: show backoff schedule for a job retry configuration."""
from __future__ import annotations

import argparse

from cronwrap.backoff import backoff_sequence, render_backoff_result


def add_backoff_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "backoff",
        help="Show exponential backoff schedule for retry attempts.",
    )
    p.add_argument(
        "--attempts",
        type=int,
        default=5,
        help="Number of retry attempts to display (default: 5).",
    )
    p.add_argument(
        "--base",
        type=float,
        default=1.0,
        dest="base_seconds",
        help="Base delay in seconds (default: 1.0).",
    )
    p.add_argument(
        "--multiplier",
        type=float,
        default=2.0,
        help="Exponential multiplier (default: 2.0).",
    )
    p.add_argument(
        "--max",
        type=float,
        default=300.0,
        dest="max_seconds",
        help="Maximum delay cap in seconds (default: 300).",
    )
    p.add_argument(
        "--no-jitter",
        action="store_true",
        help="Disable jitter (show deterministic delays).",
    )


def run_backoff(ns: argparse.Namespace) -> int:
    """Execute the backoff subcommand; returns exit code."""
    results = backoff_sequence(
        max_attempts=ns.attempts,
        base_seconds=ns.base_seconds,
        multiplier=ns.multiplier,
        max_seconds=ns.max_seconds,
        jitter=not ns.no_jitter,
    )
    if not results:
        print("No attempts to display.")
        return 0

    print(f"Backoff schedule ({len(results)} attempt(s)):")
    for r in results:
        print(f"  {render_backoff_result(r)}")
    return 0

"""CLI subcommand: cronwrap signal-demo — demonstrate graceful shutdown handling."""

from __future__ import annotations

import argparse
import time
import sys

from cronwrap.signal_handler import setup_signal_handlers, render_shutdown_report


def add_signal_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "signal-demo",
        help="Run a demo loop that exits cleanly on SIGTERM/SIGINT.",
    )
    p.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of loop iterations before natural exit (default: 5).",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Seconds to sleep between iterations (default: 0.1).",
    )


def run_signal_demo(ns: argparse.Namespace) -> int:
    event = setup_signal_handlers()

    completed = 0
    for i in range(ns.iterations):
        if event.should_stop:
            print(f"Stopping early at iteration {i}.")
            break
        time.sleep(ns.interval)
        completed += 1

    report = render_shutdown_report(event)
    print(report)
    print(f"Completed {completed}/{ns.iterations} iterations.")
    return 0 if not event.triggered else 2

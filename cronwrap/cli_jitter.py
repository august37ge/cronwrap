"""CLI sub-command: ``cronwrap jitter``

Print (or apply) a jitter delay for a named job.

Example usage::

    cronwrap jitter --job backup --max-seconds 60
"""

from __future__ import annotations

import argparse
import sys

from cronwrap.jitter import apply_jitter, render_jitter_result


def add_jitter_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "jitter",
        help="Sleep for a random delay before running a job (thundering-herd mitigation).",
    )
    p.add_argument("--job", required=True, help="Job name (used in log output only).")
    p.add_argument(
        "--max-seconds",
        type=int,
        default=30,
        dest="max_seconds",
        help="Maximum jitter delay in seconds (default: 30). Use 0 to disable.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the computed delay without actually sleeping.",
    )


def run_jitter(args: argparse.Namespace) -> int:
    """Execute the jitter sub-command.  Returns an exit code."""

    if args.dry_run:
        from cronwrap.jitter import compute_jitter

        delay = compute_jitter(args.max_seconds)
        print(
            f"[jitter] {args.job}: would sleep {delay:.2f}s "
            f"(max={args.max_seconds}s) [dry-run]"
        )
        return 0

    result = apply_jitter(args.job, args.max_seconds)
    print(render_jitter_result(result), file=sys.stdout)
    return 0

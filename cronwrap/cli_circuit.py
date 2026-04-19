"""CLI sub-command: circuit — inspect circuit-breaker state for a job."""
from __future__ import annotations

import argparse
import sys

from cronwrap.circuit_breaker import check_circuit, render_circuit_state


def add_circuit_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "circuit",
        help="Show circuit-breaker state for a cron job",
    )
    p.add_argument("job_name", help="Name of the job to inspect")
    p.add_argument("--db", required=True, help="Path to history SQLite database")
    p.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Consecutive failures before circuit opens (default: 3)",
    )
    p.add_argument(
        "--lookback",
        type=int,
        default=10,
        help="Number of recent runs to examine (default: 10)",
    )
    p.add_argument(
        "--fail-if-open",
        action="store_true",
        help="Exit with code 1 when the circuit is open",
    )


def run_circuit(ns: argparse.Namespace) -> int:
    state = check_circuit(
        job_name=ns.job_name,
        db_path=ns.db,
        threshold=ns.threshold,
        lookback=ns.lookback,
    )
    print(render_circuit_state(state))
    if ns.fail_if_open and state.is_open:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_circuit_subparser(subs)
    args = parser.parse_args()
    sys.exit(run_circuit(args))

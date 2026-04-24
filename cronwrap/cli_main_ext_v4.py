"""Extended CLI dispatcher v4 — adds cooldown sub-command."""

from __future__ import annotations

import argparse
import sys

from cronwrap.cli_cooldown import add_cooldown_subparser, run_cooldown
from cronwrap.cli_circuit import add_circuit_subparser, run_circuit
from cronwrap.cli_dependency import add_dependency_subparser, run_dependency
from cronwrap.cli_throttle import add_throttle_subparser, run_throttle
from cronwrap.cli_ratelimit import add_ratelimit_subparser, run_ratelimit

_REGISTRY = {
    "cooldown": run_cooldown,
    "circuit": run_circuit,
    "dependency": run_dependency,
    "throttle": run_throttle,
    "ratelimit": run_ratelimit,
}


def register_all_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach every v4 sub-command to *subparsers*."""
    add_cooldown_subparser(subparsers)
    add_circuit_subparser(subparsers)
    add_dependency_subparser(subparsers)
    add_throttle_subparser(subparsers)
    add_ratelimit_subparser(subparsers)


def dispatch(ns: argparse.Namespace) -> int:
    """Route *ns* to the correct handler and return its exit code."""
    handler = _REGISTRY.get(ns.command)
    if handler is None:
        print(f"Unknown command: {ns.command}", file=sys.stderr)
        return 2
    return handler(ns)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="cronwrap")
    subs = parser.add_subparsers(dest="command")
    register_all_subcommands(subs)
    parsed = parser.parse_args()
    if not parsed.command:
        parser.print_help()
        sys.exit(0)
    sys.exit(dispatch(parsed))

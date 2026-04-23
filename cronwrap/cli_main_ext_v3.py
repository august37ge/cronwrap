"""Extended CLI dispatcher v3 — includes dependency sub-command."""

from __future__ import annotations

import argparse

from cronwrap.cli_report import add_report_subparser, run_report
from cronwrap.cli_prune import add_prune_subparser, run_prune
from cronwrap.cli_audit import add_audit_subparser, run_audit
from cronwrap.cli_schedule import add_schedule_subparser, run_schedule
from cronwrap.cli_dashboard import add_dashboard_subparser, run_dashboard
from cronwrap.cli_snapshot import add_snapshot_subparser, run_snapshot
from cronwrap.cli_diff import add_diff_subparser, run_diff
from cronwrap.cli_watchdog import add_watchdog_subparser, run_watchdog
from cronwrap.cli_healthcheck import add_healthcheck_subparser, run_healthcheck
from cronwrap.cli_ratelimit import add_ratelimit_subparser, run_ratelimit
from cronwrap.cli_throttle import add_throttle_subparser, run_throttle
from cronwrap.cli_circuit import add_circuit_subparser, run_circuit
from cronwrap.cli_dependency import add_dependency_subparser, run_dependency

_REGISTRY = [
    ("report", add_report_subparser, run_report),
    ("prune", add_prune_subparser, run_prune),
    ("audit", add_audit_subparser, run_audit),
    ("schedule", add_schedule_subparser, run_schedule),
    ("dashboard", add_dashboard_subparser, run_dashboard),
    ("snapshot", add_snapshot_subparser, run_snapshot),
    ("diff", add_diff_subparser, run_diff),
    ("watchdog", add_watchdog_subparser, run_watchdog),
    ("healthcheck", add_healthcheck_subparser, run_healthcheck),
    ("ratelimit", add_ratelimit_subparser, run_ratelimit),
    ("throttle", add_throttle_subparser, run_throttle),
    ("circuit", add_circuit_subparser, run_circuit),
    ("dependency", add_dependency_subparser, run_dependency),
]


def register_all_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    for _name, add_fn, _run_fn in _REGISTRY:
        add_fn(subparsers)


def dispatch(ns: argparse.Namespace) -> int:
    for name, _add_fn, run_fn in _REGISTRY:
        if getattr(ns, "cmd", None) == name:
            return run_fn(ns)
    return 0

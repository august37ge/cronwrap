"""Extension helpers to register all subcommands onto a parser."""
from __future__ import annotations
import argparse


def register_all_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Register every known subcommand in one call."""
    from cronwrap.cli_report import add_report_subparser
    from cronwrap.cli_prune import add_prune_subparser
    from cronwrap.cli_audit import add_audit_subparser
    from cronwrap.cli_schedule import add_schedule_subparser
    from cronwrap.cli_dashboard import add_dashboard_subparser

    add_report_subparser(subparsers)
    add_prune_subparser(subparsers)
    add_audit_subparser(subparsers)
    add_schedule_subparser(subparsers)
    add_dashboard_subparser(subparsers)


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch a parsed namespace to the correct run_* handler."""
    from cronwrap.cli_report import run_report
    from cronwrap.cli_prune import run_prune
    from cronwrap.cli_audit import run_audit
    from cronwrap.cli_schedule import run_schedule
    from cronwrap.cli_dashboard import run_dashboard

    handlers = {
        "report": run_report,
        "prune": run_prune,
        "audit": run_audit,
        "schedule": run_schedule,
        "dashboard": run_dashboard,
    }
    command = getattr(args, "command", None)
    handler = handlers.get(command)
    if handler is None:
        return 1
    return handler(args)

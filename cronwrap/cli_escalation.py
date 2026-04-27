"""CLI sub-command: escalation — evaluate escalation policy for a job."""
from __future__ import annotations

import argparse
import sys

from cronwrap.escalation import (
    EscalationLevel,
    check_escalation,
    render_escalation_result,
)


def add_escalation_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "escalation",
        help="Evaluate escalation policy for a job based on consecutive failures.",
    )
    p.add_argument("job", help="Job name to evaluate.")
    p.add_argument(
        "--db",
        default="cronwrap.db",
        help="Path to the history database (default: cronwrap.db).",
    )
    p.add_argument(
        "--level",
        dest="levels",
        action="append",
        metavar="AFTER_FAILURES:CONTACT[,CONTACT]:LABEL",
        help=(
            "Define an escalation level. Format: "
            "after_failures:contact1[,contact2]:label. "
            "May be repeated for multiple tiers."
        ),
    )


def _parse_level(raw: str) -> EscalationLevel:
    """Parse 'after:contacts:label' into an EscalationLevel."""
    parts = raw.split(":", 2)
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(
            f"Invalid level spec {raw!r}. Expected after_failures:contacts[:label]"
        )
    after = int(parts[0])
    contacts = [c.strip() for c in parts[1].split(",") if c.strip()]
    label = parts[2] if len(parts) == 3 else ""
    return EscalationLevel(after_failures=after, notify=contacts, label=label)


def run_escalation(ns: argparse.Namespace) -> int:
    raw_levels = ns.levels or []
    try:
        levels = [_parse_level(r) for r in raw_levels]
    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"Error parsing escalation levels: {exc}", file=sys.stderr)
        return 2

    result = check_escalation(ns.job, levels, db_path=ns.db)
    print(render_escalation_result(result))
    return 0 if not result.triggered else 1

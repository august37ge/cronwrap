"""Extended CLI dispatcher v5 — adds the quota sub-command."""

from __future__ import annotations

import argparse

from cronwrap.cli_main_ext_v4 import register_all_subcommands as _register_v4
from cronwrap.cli_main_ext_v4 import dispatch as _dispatch_v4
from cronwrap.cli_quota import add_quota_subparser, run_quota

_HANDLERS: dict[str, object] = {}


def register_all_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register every known sub-command including quota."""
    _register_v4(subparsers)
    add_quota_subparser(subparsers)
    _HANDLERS["quota"] = run_quota


def dispatch(ns: argparse.Namespace) -> int:
    """Dispatch *ns* to the appropriate handler.

    Falls back to the v4 dispatcher for commands registered there.
    """
    cmd = getattr(ns, "cmd", None)
    if cmd in _HANDLERS:
        handler = _HANDLERS[cmd]
        return handler(ns)  # type: ignore[operator]
    return _dispatch_v4(ns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Cron job wrapper with logging, alerting, and control utilities.",
    )
    subparsers = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    register_all_subcommands(subparsers)
    ns = parser.parse_args(argv)
    if ns.cmd is None:
        parser.print_help()
        return 0
    return dispatch(ns)

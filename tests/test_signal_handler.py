"""Tests for cronwrap.signal_handler."""

from __future__ import annotations

import signal
import argparse

import pytest

from cronwrap.signal_handler import (
    ShutdownEvent,
    setup_signal_handlers,
    get_event,
    render_shutdown_report,
)
from cronwrap.cli_signal import add_signal_subparser, run_signal_demo


# ---------------------------------------------------------------------------
# ShutdownEvent unit tests
# ---------------------------------------------------------------------------

def test_initial_state_not_triggered():
    ev = ShutdownEvent()
    assert not ev.triggered
    assert ev.signal_num is None
    assert not ev.should_stop


def test_trigger_sets_flag():
    ev = ShutdownEvent()
    ev.trigger(signal.SIGTERM)
    assert ev.triggered
    assert ev.signal_num == signal.SIGTERM
    assert ev.should_stop


def test_callbacks_called_on_trigger():
    ev = ShutdownEvent()
    called = []
    ev.register_callback(lambda: called.append(1))
    ev.register_callback(lambda: called.append(2))
    ev.trigger(signal.SIGTERM)
    assert called == [1, 2]


# ---------------------------------------------------------------------------
# render_shutdown_report
# ---------------------------------------------------------------------------

def test_render_no_shutdown():
    ev = ShutdownEvent()
    report = render_shutdown_report(ev)
    assert "No shutdown" in report


def test_render_with_shutdown():
    ev = ShutdownEvent()
    ev.trigger(signal.SIGTERM)
    report = render_shutdown_report(ev)
    assert "SIGTERM" in report


# ---------------------------------------------------------------------------
# setup_signal_handlers / get_event
# ---------------------------------------------------------------------------

def test_setup_returns_event():
    ev = setup_signal_handlers()
    assert isinstance(ev, ShutdownEvent)
    assert get_event() is ev


# ---------------------------------------------------------------------------
# CLI subcommand
# ---------------------------------------------------------------------------

def _make_ns(iterations: int = 3, interval: float = 0.0) -> argparse.Namespace:
    return argparse.Namespace(iterations=iterations, interval=interval)


def test_add_signal_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    add_signal_subparser(subs)
    ns = parser.parse_args(["signal-demo", "--iterations", "2"])
    assert ns.cmd == "signal-demo"
    assert ns.iterations == 2


def test_run_signal_demo_completes_normally():
    ns = _make_ns(iterations=2, interval=0.0)
    rc = run_signal_demo(ns)
    assert rc == 0


def test_run_signal_demo_zero_iterations():
    ns = _make_ns(iterations=0, interval=0.0)
    rc = run_signal_demo(ns)
    assert rc == 0

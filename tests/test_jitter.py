"""Tests for cronwrap.jitter and cronwrap.cli_jitter."""

from __future__ import annotations

import argparse
import types

import pytest

from cronwrap.jitter import (
    JitterResult,
    apply_jitter,
    compute_jitter,
    render_jitter_result,
)


# ---------------------------------------------------------------------------
# compute_jitter
# ---------------------------------------------------------------------------

def test_compute_jitter_zero_max_returns_zero():
    assert compute_jitter(0) == 0.0


def test_compute_jitter_negative_max_returns_zero():
    assert compute_jitter(-5) == 0.0


def test_compute_jitter_within_bounds():
    for _ in range(50):
        val = compute_jitter(10)
        assert 0.0 <= val <= 10.0


def test_compute_jitter_seed_is_deterministic():
    a = compute_jitter(60, seed=42)
    b = compute_jitter(60, seed=42)
    assert a == b


# ---------------------------------------------------------------------------
# apply_jitter
# ---------------------------------------------------------------------------

def test_apply_jitter_skipped_when_max_zero():
    result = apply_jitter("myjob", 0)
    assert result.skipped is True
    assert result.actual_delay_seconds == 0.0


def test_apply_jitter_calls_sleep():
    slept: list[float] = []
    result = apply_jitter("backup", 30, seed=7, _sleep=slept.append)
    assert not result.skipped
    assert len(slept) == 1
    assert slept[0] == result.actual_delay_seconds
    assert 0.0 <= result.actual_delay_seconds <= 30.0


def test_apply_jitter_result_fields():
    result = apply_jitter("sync", 15, seed=99, _sleep=lambda _: None)
    assert result.job_name == "sync"
    assert result.requested_max_seconds == 15


# ---------------------------------------------------------------------------
# render_jitter_result
# ---------------------------------------------------------------------------

def test_render_skipped():
    r = JitterResult(job_name="noop", requested_max_seconds=0, actual_delay_seconds=0.0, skipped=True)
    text = render_jitter_result(r)
    assert "disabled" in text
    assert "noop" in text


def test_render_active():
    r = JitterResult(job_name="cleanup", requested_max_seconds=60, actual_delay_seconds=23.456, skipped=False)
    text = render_jitter_result(r)
    assert "23.46" in text
    assert "cleanup" in text
    assert "60" in text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {"job": "testjob", "max_seconds": 10, "dry_run": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_jitter_subparser_registers_command():
    from cronwrap.cli_jitter import add_jitter_subparser

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_jitter_subparser(sub)
    ns = parser.parse_args(["jitter", "--job", "x", "--max-seconds", "5"])
    assert ns.command == "jitter"
    assert ns.max_seconds == 5


def test_run_jitter_returns_zero(capsys):
    from cronwrap.cli_jitter import run_jitter

    ns = _make_namespace(max_seconds=0)  # skipped immediately
    code = run_jitter(ns)
    assert code == 0


def test_run_jitter_dry_run_prints_would_sleep(capsys):
    from cronwrap.cli_jitter import run_jitter

    ns = _make_namespace(dry_run=True, max_seconds=20)
    code = run_jitter(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "testjob" in out

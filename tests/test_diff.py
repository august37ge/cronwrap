"""Tests for cronwrap.diff."""
import pytest
from cronwrap.diff import MetricDiff, diff_snapshots, render_diff
from cronwrap.snapshots import Snapshot
from datetime import datetime


def _snap(label: str, metrics: list) -> Snapshot:
    return Snapshot(label=label, taken_at=datetime.utcnow(), metrics=metrics)


def test_diff_empty_snapshots():
    old = _snap("v1", [])
    new = _snap("v2", [])
    assert diff_snapshots(old, new) == []


def test_diff_new_job_appears():
    old = _snap("v1", [])
    new = _snap("v2", [{"job_name": "backup", "success_rate": 100.0, "avg_duration": 2.0}])
    diffs = diff_snapshots(old, new)
    assert len(diffs) == 1
    assert diffs[0].job_name == "backup"
    assert diffs[0].old_success_rate is None
    assert diffs[0].new_success_rate == 100.0


def test_diff_job_removed():
    old = _snap("v1", [{"job_name": "sync", "success_rate": 80.0, "avg_duration": 5.0}])
    new = _snap("v2", [])
    diffs = diff_snapshots(old, new)
    assert diffs[0].new_success_rate is None


def test_diff_calculates_deltas():
    old = _snap("v1", [{"job_name": "job", "success_rate": 80.0, "avg_duration": 3.0}])
    new = _snap("v2", [{"job_name": "job", "success_rate": 90.0, "avg_duration": 2.5}])
    diffs = diff_snapshots(old, new)
    d = diffs[0]
    assert d.success_rate_delta == pytest.approx(10.0)
    assert d.avg_duration_delta == pytest.approx(-0.5)


def test_render_diff_no_diffs():
    assert render_diff([]) == "No differences found."


def test_render_diff_contains_job_name():
    d = MetricDiff("myjob", 50.0, 75.0, 1.0, 2.0)
    out = render_diff([d])
    assert "myjob" in out
    assert "+25.0%" in out
    assert "+1.00s" in out


def test_render_diff_na_when_missing():
    d = MetricDiff("newjob", None, 100.0, None, 1.5)
    out = render_diff([d])
    assert "N/A" in out

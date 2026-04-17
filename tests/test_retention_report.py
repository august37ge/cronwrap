"""Tests for cronwrap.retention_report rendering."""
from __future__ import annotations

from datetime import datetime, timezone

from cronwrap.retention import PruneResult
from cronwrap.retention_report import render_prune_result, render_prune_results


def _result(job_name, rows_deleted):
    return PruneResult(
        job_name=job_name,
        rows_deleted=rows_deleted,
        cutoff=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_render_single_result_contains_job_name():
    r = _result("my_job", 5)
    text = render_prune_result(r)
    assert "my_job" in text
    assert "5" in text


def test_render_single_result_all_jobs_label():
    r = _result(None, 12)
    text = render_prune_result(r)
    assert "<all jobs>" in text
    assert "12" in text


def test_render_results_empty():
    text = render_prune_results([])
    assert "No jobs pruned" in text


def test_render_results_total():
    results = [_result("a", 3), _result("b", 7)]
    text = render_prune_results(results)
    assert "Total records deleted: 10" in text
    assert "a" in text
    assert "b" in text


def test_render_results_single_zero():
    results = [_result("noop", 0)]
    text = render_prune_results(results)
    assert "Total records deleted: 0" in text

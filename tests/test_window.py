"""Tests for cronwrap.window execution-window enforcement."""
from datetime import datetime

import pytest

from cronwrap.window import WindowResult, check_window, render_window_result


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 6, 15, hour, minute, 0)


# ---------------------------------------------------------------------------
# Normal (same-day) windows
# ---------------------------------------------------------------------------

def test_allowed_inside_normal_window():
    result = check_window("backup", "08:00", "18:00", now=_dt(12))
    assert result.allowed is True
    assert "ALLOWED" in render_window_result(result) or result.allowed


def test_blocked_before_normal_window():
    result = check_window("backup", "08:00", "18:00", now=_dt(7, 59))
    assert result.allowed is False


def test_blocked_at_window_end_boundary():
    # End is exclusive
    result = check_window("backup", "08:00", "18:00", now=_dt(18, 0))
    assert result.allowed is False


def test_allowed_at_window_start_boundary():
    result = check_window("backup", "08:00", "18:00", now=_dt(8, 0))
    assert result.allowed is True


# ---------------------------------------------------------------------------
# Overnight windows
# ---------------------------------------------------------------------------

def test_allowed_inside_overnight_window_after_start():
    result = check_window("nightly", "22:00", "06:00", now=_dt(23, 30))
    assert result.allowed is True


def test_allowed_inside_overnight_window_before_end():
    result = check_window("nightly", "22:00", "06:00", now=_dt(3, 0))
    assert result.allowed is True


def test_blocked_outside_overnight_window():
    result = check_window("nightly", "22:00", "06:00", now=_dt(10, 0))
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Invalid input
# ---------------------------------------------------------------------------

def test_invalid_start_time_returns_blocked():
    result = check_window("job", "25:00", "18:00", now=_dt(12))
    assert result.allowed is False
    assert "Invalid" in result.reason


def test_invalid_end_time_returns_blocked():
    result = check_window("job", "08:00", "99:99", now=_dt(12))
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def test_render_contains_job_name():
    result = check_window("my-job", "08:00", "18:00", now=_dt(12))
    rendered = render_window_result(result)
    assert "my-job" in rendered


def test_render_shows_blocked():
    result = check_window("my-job", "08:00", "18:00", now=_dt(20))
    rendered = render_window_result(result)
    assert "BLOCKED" in rendered


def test_result_stores_checked_at():
    result = check_window("job", "08:00", "18:00", now=_dt(9))
    assert result.checked_at is not None
    assert "2024-06-15" in result.checked_at

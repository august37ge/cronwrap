"""Tests for cronwrap.schedule."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.schedule import ScheduleInfo, is_overdue, next_run_time, validate_expression


@pytest.fixture(autouse=True)
def _require_croniter():
    """Skip tests if croniter is not installed."""
    pytest.importorskip("croniter")


def test_validate_valid_expression():
    info = validate_expression("*/5 * * * *")
    assert info.is_valid is True
    assert info.error is None


def test_validate_invalid_expression():
    info = validate_expression("not a cron")
    assert info.is_valid is False
    assert info.error is not None


def test_next_run_time_returns_future():
    base = datetime(2024, 1, 1, 12, 0, 0)
    nxt = next_run_time("0 * * * *", base=base)
    assert nxt is not None
    assert nxt > base


def test_next_run_time_invalid_returns_none():
    result = next_run_time("bad expression", base=datetime.now())
    assert result is None


def test_is_overdue_when_past_threshold():
    # Last run was 2 hours ago on an hourly schedule — should be overdue
    last = datetime.now() - timedelta(hours=2)
    assert is_overdue("0 * * * *", last_run=last) is True


def test_is_not_overdue_when_recent():
    # Last run was 10 minutes ago on an hourly schedule — not overdue
    last = datetime.now() - timedelta(minutes=10)
    assert is_overdue("0 * * * *", last_run=last) is False

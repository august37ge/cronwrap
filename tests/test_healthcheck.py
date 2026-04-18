"""Tests for cronwrap.healthcheck."""
import json
import time
from pathlib import Path

import pytest

from cronwrap.runner import RunResult
from cronwrap.healthcheck import write_status, read_status, check_stale, HealthStatus


@pytest.fixture()
def status_dir(tmp_path):
    return str(tmp_path / "status")


def _result(success=True, exit_code=0, duration=1.5, stdout="ok", stderr=""):
    return RunResult(success=success, exit_code=exit_code,
                     stdout=stdout, stderr=stderr, duration=duration)


def test_write_creates_file(status_dir):
    path = write_status("backup", _result(), status_dir)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["job_name"] == "backup"
    assert data["success"] is True


def test_read_returns_none_when_missing(status_dir):
    assert read_status("nonexistent", status_dir) is None


def test_read_returns_status(status_dir):
    write_status("cleanup", _result(success=False, exit_code=1), status_dir)
    s = read_status("cleanup", status_dir)
    assert isinstance(s, HealthStatus)
    assert s.success is False
    assert s.exit_code == 1


def test_message_truncated(status_dir):
    long_msg = "x" * 500
    write_status("job", _result(stdout=long_msg), status_dir)
    s = read_status("job", status_dir)
    assert len(s.message) <= 256


def test_check_stale_no_file(status_dir):
    assert check_stale("missing", status_dir, max_age_seconds=60) is True


def test_check_stale_fresh(status_dir):
    write_status("fresh", _result(), status_dir)
    assert check_stale("fresh", status_dir, max_age_seconds=3600) is False


def test_check_stale_old(status_dir):
    write_status("old", _result(), status_dir)
    # max_age of 0 seconds means it's immediately stale
    assert check_stale("old", status_dir, max_age_seconds=0) is True

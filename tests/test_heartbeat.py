"""Tests for cronwrap.heartbeat."""

from __future__ import annotations

import time
import pytest

from cronwrap.heartbeat import (
    init_heartbeat_db,
    record_beat,
    check_heartbeat,
    render_heartbeat_result,
)


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "hb.db")
    init_heartbeat_db(p)
    return p


# ---------------------------------------------------------------------------
# check_heartbeat — no history
# ---------------------------------------------------------------------------

def test_dead_when_no_beat_recorded(db_path):
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    assert result.alive is False
    assert result.last_beat is None
    assert result.seconds_since is None


def test_message_when_no_beat_recorded(db_path):
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    assert "no heartbeat" in result.message


# ---------------------------------------------------------------------------
# record_beat + check_heartbeat
# ---------------------------------------------------------------------------

def test_alive_immediately_after_beat(db_path):
    record_beat(db_path, "myjob")
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    assert result.alive is True
    assert result.seconds_since is not None
    assert result.seconds_since < 5  # recorded moments ago


def test_dead_when_interval_exceeded(db_path):
    record_beat(db_path, "myjob")
    # max_interval of 0 seconds means any beat is immediately stale
    result = check_heartbeat(db_path, "myjob", max_interval=0)
    assert result.alive is False


def test_multiple_beats_uses_latest(db_path):
    record_beat(db_path, "myjob")
    time.sleep(0.05)
    record_beat(db_path, "myjob")
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    assert result.alive is True
    assert result.seconds_since < 2


def test_beats_isolated_by_job(db_path):
    record_beat(db_path, "job-a")
    result = check_heartbeat(db_path, "job-b", max_interval=60)
    assert result.alive is False


# ---------------------------------------------------------------------------
# render_heartbeat_result
# ---------------------------------------------------------------------------

def test_render_alive(db_path):
    record_beat(db_path, "myjob")
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    rendered = render_heartbeat_result(result)
    assert rendered.startswith("[OK]")


def test_render_dead(db_path):
    result = check_heartbeat(db_path, "myjob", max_interval=60)
    rendered = render_heartbeat_result(result)
    assert rendered.startswith("[DEAD]")

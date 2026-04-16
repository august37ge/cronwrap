import pytest
from cronwrap.runner import run_command, RunResult


def test_successful_command():
    result = run_command(["echo", "hello"])
    assert result.success
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.attempts == 1
    assert result.duration >= 0


def test_failed_command_no_retry():
    result = run_command(["false"])
    assert not result.success
    assert result.returncode != 0
    assert result.attempts == 1


def test_retry_eventually_fails():
    result = run_command(["false"], retries=2, retry_delay=0)
    assert not result.success
    assert result.attempts == 3


def test_retry_succeeds_on_first_try():
    result = run_command(["true"], retries=3, retry_delay=0)
    assert result.success
    assert result.attempts == 1


def test_timeout_returns_failure():
    result = run_command(["sleep", "5"], timeout=0.1)
    assert not result.success
    assert result.returncode == -1
    assert "Timeout" in result.stderr


def test_run_result_command_string():
    result = run_command(["echo", "world"])
    assert result.command == "echo world"

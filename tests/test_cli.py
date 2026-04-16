"""Integration tests for the CLI entry point."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cronwrap.cli import main
from cronwrap.runner import RunResult


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "cli_test.db")


def _success_result():
    return RunResult(exit_code=0, stdout="ok", stderr="", success=True, attempts=1)


def _failure_result():
    return RunResult(exit_code=1, stdout="", stderr="error", success=False, attempts=1)


def test_cli_success(db_path):
    with patch("cronwrap.cli.run_command", return_value=_success_result()):
        rc = main(["myjob", "echo", "hello", "--db", db_path])
    assert rc == 0


def test_cli_failure_returns_nonzero(db_path):
    with patch("cronwrap.cli.run_command", return_value=_failure_result()):
        rc = main(["myjob", "false", "--db", db_path])
    assert rc == 1


def test_cli_records_history(db_path):
    from cronwrap.history import get_recent_runs
    with patch("cronwrap.cli.run_command", return_value=_success_result()):
        main(["myjob", "echo", "hi", "--db", db_path])
    runs = get_recent_runs("myjob", db_path=Path(db_path))
    assert len(runs) == 1
    assert runs[0].success is True


def test_cli_sends_alert_on_failure(db_path):
    with patch("cronwrap.cli.run_command", return_value=_failure_result()), \
         patch("cronwrap.cli.alert_on_failure") as mock_alert:
        main(["myjob", "false", "--alert-email", "ops@example.com", "--db", db_path])
    mock_alert.assert_called_once()


def test_cli_no_command_exits(db_path):
    with pytest.raises(SystemExit):
        main(["myjob"])

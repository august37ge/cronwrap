"""Tests for cronwrap.notify."""

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.notify import NotifyConfig, build_payload, notify, _post_webhook


def test_build_payload_truncates_output():
    long_output = "x" * 5000
    payload = build_payload("myjob", True, 0, long_output)
    assert payload["job"] == "myjob"
    assert payload["success"] is True
    assert payload["exit_code"] == 0
    assert len(payload["output"]) == 2000


def test_build_payload_short_output():
    payload = build_payload("j", False, 1, "err")
    assert payload["output"] == "err"


def test_notify_skips_when_success_and_on_success_false():
    cfg = NotifyConfig(webhook_url="http://example.com", on_success=False, on_failure=True)
    with patch("cronwrap.notify._post_webhook") as mock_post:
        notify(cfg, "job", success=True, exit_code=0, output="ok")
        mock_post.assert_not_called()


def test_notify_sends_on_failure():
    cfg = NotifyConfig(webhook_url="http://example.com", on_failure=True)
    with patch("cronwrap.notify._post_webhook", return_value=True) as mock_post:
        notify(cfg, "job", success=False, exit_code=1, output="fail")
        mock_post.assert_called_once()
        _, payload, _ = mock_post.call_args[0]
        assert payload["success"] is False


def test_notify_sends_on_success_when_enabled():
    cfg = NotifyConfig(webhook_url="http://hook", on_success=True, on_failure=False)
    with patch("cronwrap.notify._post_webhook", return_value=True) as mock_post:
        notify(cfg, "job", success=True, exit_code=0, output="")
        mock_post.assert_called_once()


def test_notify_no_webhook_logs_only(caplog):
    cfg = NotifyConfig(webhook_url=None, on_failure=True)
    import logging
    with caplog.at_level(logging.INFO, logger="cronwrap.notify"):
        notify(cfg, "myjob", success=False, exit_code=2, output="bad")
    assert "myjob" in caplog.text
    assert "FAILURE" in caplog.text


def test_post_webhook_handles_exception():
    with patch("urllib.request.urlopen", side_effect=OSError("conn refused")):
        result = _post_webhook("http://bad", {"k": "v"}, {})
    assert result is False

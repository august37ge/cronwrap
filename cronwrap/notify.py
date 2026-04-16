"""Notification hooks for cronwrap — supports stdout, webhook, and email summary."""

from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class NotifyConfig:
    webhook_url: Optional[str] = None
    webhook_headers: dict = field(default_factory=dict)
    on_success: bool = False
    on_failure: bool = True


def _post_webhook(url: str, payload: dict, headers: dict) -> bool:
    """POST JSON payload to webhook URL. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception as exc:  # noqa: BLE001
        log.warning("Webhook delivery failed: %s", exc)
        return False


def build_payload(job_name: str, success: bool, exit_code: int, output: str) -> dict:
    return {
        "job": job_name,
        "success": success,
        "exit_code": exit_code,
        "output": output[-2000:],  # truncate long output
    }


def notify(
    config: NotifyConfig,
    job_name: str,
    success: bool,
    exit_code: int,
    output: str,
) -> None:
    """Send notifications according to config and run outcome."""
    should_notify = (success and config.on_success) or (not success and config.on_failure)
    if not should_notify:
        return

    if config.webhook_url:
        payload = build_payload(job_name, success, exit_code, output)
        sent = _post_webhook(config.webhook_url, payload, config.webhook_headers)
        if sent:
            log.info("Webhook notification sent for job '%s'", job_name)
        else:
            log.warning("Webhook notification failed for job '%s'", job_name)
    else:
        status = "SUCCESS" if success else "FAILURE"
        log.info("[notify] Job '%s' finished with status %s (exit %d)", job_name, status, exit_code)

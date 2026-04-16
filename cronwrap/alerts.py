"""Alert notifications for cron job failures and recoveries."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert notifications."""
    recipients: List[str]
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = False
    sender: str = "cronwrap@localhost"
    subject_prefix: str = "[cronwrap]"


def _build_email(
    config: AlertConfig,
    subject: str,
    body: str,
) -> MIMEMultipart:
    """Construct a MIME email message."""
    msg = MIMEMultipart()
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.recipients)
    msg["Subject"] = f"{config.subject_prefix} {subject}"
    msg.attach(MIMEText(body, "plain"))
    return msg


def send_alert(
    config: AlertConfig,
    subject: str,
    body: str,
) -> bool:
    """Send an alert email. Returns True on success, False on failure."""
    if not config.recipients:
        logger.warning("No alert recipients configured, skipping alert.")
        return False

    msg = _build_email(config, subject, body)

    try:
        if config.use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)

        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)

        server.sendmail(config.sender, config.recipients, msg.as_string())
        server.quit()
        logger.info("Alert sent to %s: %s", config.recipients, subject)
        return True
    except smtplib.SMTPException as e:
        logger.error("Failed to send alert email: %s", e)
        return False


def alert_on_failure(
    config: Optional[AlertConfig],
    command: str,
    exit_code: int,
    stderr: str,
    attempt: int,
    max_attempts: int,
) -> None:
    """Send a failure alert if alert config is provided."""
    if config is None:
        return

    subject = f"FAILED: {command!r} (exit {exit_code})"
    body = (
        f"Command: {command}\n"
        f"Exit code: {exit_code}\n"
        f"Attempt: {attempt} of {max_attempts}\n\n"
        f"Stderr output:\n{stderr or '(none)'}\n"
    )
    send_alert(config, subject, body)


def alert_on_recovery(
    config: Optional[AlertConfig],
    command: str,
    attempt: int,
) -> None:
    """Send a recovery alert when a previously failing job succeeds."""
    if config is None:
        return

    subject = f"RECOVERED: {command!r}"
    body = (
        f"Command: {command}\n"
        f"Succeeded on attempt {attempt}.\n"
    )
    send_alert(config, subject, body)

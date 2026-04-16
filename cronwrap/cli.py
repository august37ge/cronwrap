"""CLI entry point for cronwrap."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from cronwrap.runner import run_command
from cronwrap.logging_setup import setup_logging, log_result
from cronwrap.alerts import AlertConfig, alert_on_failure, alert_on_recovery
from cronwrap.history import JobRecord, record_run, last_run, DEFAULT_DB_PATH


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Wrap a cron job with logging, alerting, and retries.")
    p.add_argument("job_name", help="Unique name for this job")
    p.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    p.add_argument("--retries", type=int, default=0, help="Number of retry attempts")
    p.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    p.add_argument("--alert-email", default=None, help="Email address for failure alerts")
    p.add_argument("--smtp-host", default="localhost")
    p.add_argument("--smtp-port", type=int, default=25)
    p.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to history database")
    p.add_argument("--log-level", default="INFO")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.error("No command provided.")

    logger = setup_logging(args.log_level)
    db_path = Path(args.db)
    cmd = args.command[0] if len(args.command) == 1 else " ".join(args.command)

    alert_cfg = None
    if args.alert_email:
        alert_cfg = AlertConfig(
            recipient=args.alert_email,
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
        )

    started_at = datetime.now(timezone.utc).isoformat()
    result = run_command(cmd, retries=args.retries, timeout=args.timeout)
    finished_at = datetime.now(timezone.utc).isoformat()

    log_result(logger, args.job_name, result)

    record = JobRecord(
        job_name=args.job_name, command=cmd,
        started_at=started_at, finished_at=finished_at,
        exit_code=result.exit_code, success=result.success,
        stdout=result.stdout, stderr=result.stderr,
        attempt=result.attempts,
    )
    record_run(record, db_path=db_path)

    if alert_cfg:
        previous = last_run(args.job_name, db_path=db_path)
        prev_success = previous.success if previous else True
        if not result.success:
            alert_on_failure(args.job_name, result, alert_cfg)
        elif not prev_success:
            alert_on_recovery(args.job_name, result, alert_cfg)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())

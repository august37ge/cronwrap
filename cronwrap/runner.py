import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration: float
    attempts: int

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_command(
    command: List[str],
    retries: int = 0,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None,
) -> RunResult:
    """Run a shell command with optional retry logic."""
    attempt = 0
    last_result = None

    while attempt <= retries:
        attempt += 1
        logger.info("Running command (attempt %d/%d): %s", attempt, retries + 1, command)
        start = time.monotonic()

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start
            logger.error("Command timed out after %.1fs", duration)
            last_result = RunResult(
                command=" ".join(command),
                returncode=-1,
                stdout="",
                stderr=f"Timeout after {timeout}s",
                duration=duration,
                attempts=attempt,
            )
        else:
            duration = time.monotonic() - start
            last_result = RunResult(
                command=" ".join(command),
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                attempts=attempt,
            )

        if last_result.success:
            logger.info("Command succeeded in %.2fs", last_result.duration)
            return last_result

        if attempt <= retries:
            logger.warning("Command failed (code %d), retrying in %.1fs...", last_result.returncode, retry_delay)
            time.sleep(retry_delay)

    logger.error("Command failed after %d attempt(s)", attempt)
    return last_result

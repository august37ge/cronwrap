# cronwrap

A lightweight wrapper for cron jobs that adds logging, alerting, and retry logic.

## Installation

```bash
pip install cronwrap
```

## Usage

Wrap any cron job command with `cronwrap` to get automatic logging, failure alerts, and retry support.

**Basic example:**

```bash
cronwrap --retries 3 --alert email@example.com "python /scripts/backup.py"
```

**As a Python library:**

```python
from cronwrap import CronJob

job = CronJob(
    command="python /scripts/backup.py",
    retries=3,
    alert="email@example.com",
    log_file="/var/log/cronwrap/backup.log"
)

job.run()
```

**Common options:**

| Option | Description |
|--------|-------------|
| `--retries N` | Retry the job up to N times on failure |
| `--alert EMAIL` | Send an alert email if the job fails |
| `--log-file PATH` | Path to write job logs |
| `--timeout SECS` | Kill the job if it exceeds a timeout |
| `--retry-delay SECS` | Wait between retries (default: 0) |

**Crontab example:**

```
0 2 * * * cronwrap --retries 2 --alert ops@example.com "python /scripts/nightly.py"
```

**Retry with delay example:**

```bash
cronwrap --retries 3 --retry-delay 30 --alert ops@example.com "python /scripts/sync.py"
```

This will retry up to 3 times, waiting 30 seconds between each attempt.

## License

This project is licensed under the [MIT License](LICENSE).
